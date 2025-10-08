"""
Fantasy Sports API with Kinde Authentication
Main FastAPI application for fantasy sports management
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Request
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, create_engine, text

# Import our database and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.fantasy_connection import get_fantasy_session
from src.database.fantasy_connection import fantasy_db
from src.database.fantasy_models_v2 import (
    FantasyUser, FantasyLeague, FantasyTeam, FantasyPlayer,
    FantasyUserLeague, FantasyAPIKey, FantasySeasonRanking,
    FantasyLeagueSettings, FantasyScoringRule, SiteUser
)
# Avoid importing NHL DB connector and models at import time to prevent local env requirements
# We'll import NHL connectors lazily inside endpoints that need them.

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fantasy Sports API",
    description="API for managing fantasy sports leagues with NHL metrics integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Kinde configuration
KINDE_DOMAIN = os.getenv("KINDE_DOMAIN")
KINDE_CLIENT_ID = os.getenv("KINDE_CLIENT_ID")
KINDE_CLIENT_SECRET = os.getenv("KINDE_CLIENT_SECRET")
KINDE_AUDIENCE = os.getenv("KINDE_AUDIENCE", "api://default")

class KindeAuth:
    """Kinde authentication handler"""
    
    def __init__(self):
        self.domain = KINDE_DOMAIN
        self.client_id = KINDE_CLIENT_ID
        self.client_secret = KINDE_CLIENT_SECRET
        self.audience = KINDE_AUDIENCE
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Kinde JWT token"""
        try:
            # Decode token without verification first to get the issuer
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            issuer = unverified_payload.get("iss")
            
            if not issuer or not issuer.startswith(f"https://{self.domain}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token issuer"
                )
            
            # Get the public key from Kinde
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            import requests
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
            
            # Verify the token
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}"
            )
            
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

# Initialize Kinde auth
kinde_auth = KindeAuth()
# Helper: create NHL DB engine with short connect timeout so production doesn't stall
def _get_nhl_engine(timeout_seconds: int = 3):
    try:
        nhl_url = os.getenv("NHL_DATABASE_URL")
        if nhl_url:
            return create_engine(
                nhl_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": int(os.getenv("NHL_DB_CONNECT_TIMEOUT", str(timeout_seconds)))}
            )
        # Fallback to cloud connector (used only in environments that can reach it)
        from src.database.connection import connect_with_connector  # type: ignore
        return connect_with_connector()
    except Exception as e:
        logger.warning(f"NHL DB engine init failed: {e}")
        raise

# ---- Simple email/password auth that returns an API key ----
def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

@app.post("/api/auth/register", response_model=dict)
async def register_site_user(body: Dict[str, Any]) -> Dict[str, Any]:
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or ''
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")
    with get_fantasy_session() as session:
        existing = session.query(SiteUser).filter(SiteUser.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="email already registered")
        salt = secrets.token_hex(16)
        pwd_hash = _hash_password(password, salt)
        api_key = secrets.token_hex(24)
        user = SiteUser(email=email, password_salt=salt, password_hash=pwd_hash, api_key=api_key)
        session.add(user)
        session.flush()
        return {"ok": True, "api_key": api_key}

@app.post("/api/auth/login", response_model=dict)
async def login_site_user(body: Dict[str, Any]) -> Dict[str, Any]:
    email = (body.get('email') or '').strip().lower()
    password = body.get('password') or ''
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")
    with get_fantasy_session() as session:
        user = session.query(SiteUser).filter(SiteUser.email == email, SiteUser.is_active == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="invalid credentials")
        if _hash_password(password, user.password_salt) != user.password_hash:
            raise HTTPException(status_code=401, detail="invalid credentials")
        return {"ok": True, "api_key": user.api_key}
# Archetype mapping cache
ARCHETYPE_MAPS_CACHE: dict[int, dict[int, str]] = {}

# Simple in-process TTL cache for computed fantasy points
FP_CACHE: dict[str, dict] = {}
FP_CACHE_TTL_SECONDS = 600  # 10 minutes

# Simple in-memory WebSocket manager per league slug
class WSConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, slug: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(slug, set()).add(websocket)

    def disconnect(self, slug: str, websocket: WebSocket) -> None:
        try:
            if slug in self._rooms and websocket in self._rooms[slug]:
                self._rooms[slug].remove(websocket)
                if not self._rooms[slug]:
                    del self._rooms[slug]
        except Exception:
            pass

    async def broadcast(self, slug: str, message: dict) -> None:
        import json as _json
        text = _json.dumps(message)
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(slug, set())):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(slug, ws)

ws_manager = WSConnectionManager()

def load_archetype_mapping(season: int) -> dict[int, str]:
    """Load player_id -> archetype label mapping from docs artifacts for a season."""
    if season in ARCHETYPE_MAPS_CACHE:
        return ARCHETYPE_MAPS_CACHE[season]
    import os
    import json
    import csv
    mapping: dict[int, str] = {}
    try:
        # project root: src/api/main.py -> src/api -> src -> project_root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        docs_dir = os.path.join(project_root, 'docs')
        combined_csv = os.path.join(docs_dir, 'cluster_assignments_all_2024-25.csv')
        meta_json = os.path.join(docs_dir, 'cluster_meta_2024-25.json')
        # Load meta labels
        with open(meta_json, 'r') as f:
            meta = json.load(f)
        # Build (position_group, cluster)->label map
        label_map = {}
        for pos_name, entry in meta.items():
            labels = entry.get('labels', {})
            for cid_str, label in labels.items():
                try:
                    cid = int(cid_str)
                except Exception:
                    continue
                label_map[(pos_name, cid)] = label
        # Read combined assignments
        if os.path.exists(combined_csv):
            with open(combined_csv, newline='') as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    try:
                        pid = int(row.get('player_id', '') or 0)
                        pos_group = row.get('position_group', '')
                        cluster_val = row.get('cluster', '')
                        cid = int(cluster_val) if str(cluster_val).strip() != '' else None
                        if pid and cid is not None:
                            label = label_map.get((pos_group, cid))
                            if label:
                                mapping[pid] = label
                    except Exception:
                        continue
        ARCHETYPE_MAPS_CACHE[season] = mapping
        return mapping
    except Exception as e:
        logger.warning(f"Archetype mapping load failed: {e}")
        return {}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> FantasyUser:
    """Get current authenticated user from database"""
    try:
        # Verify Kinde token
        payload = kinde_auth.verify_token(credentials.credentials)
        
        # Extract user info from token
        kinde_user_id = payload.get("sub")
        email = payload.get("email")
        
        if not kinde_user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        with get_fantasy_session() as session:
            user = session.query(FantasyUser).filter(
                FantasyUser.external_auth_id == kinde_user_id
            ).first()
            
            if not user:
                # Create new user if doesn't exist
                user = FantasyUser(
                    external_auth_id=kinde_user_id,
                    email=email,
                    username=email.split('@')[0],  # Use email prefix as username
                    first_name=payload.get("given_name", ""),
                    last_name=payload.get("family_name", ""),
                    display_name=payload.get("name", email),
                    is_active=True,
                    is_verified=True,
                    email_verified=True,
                    created_at=datetime.now()
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            
            return user
            
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/admin/db/init_v2")
async def init_v2_tables():
    try:
        fantasy_db.create_v2_tables()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inseason/cbs/import", response_model=dict)
async def import_cbs_extraction(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    import json as _json
    raw = payload
    if not isinstance(raw, dict) or 'pages' not in raw:
        raise HTTPException(status_code=400, detail="Invalid payload")
    with get_fantasy_session() as session:
        session.execute(sa_text(
            """
            CREATE TABLE IF NOT EXISTS cbs_extractions (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMP DEFAULT NOW(),
              source TEXT,
              raw JSONB
            )
            """
        ))
        session.execute(sa_text("INSERT INTO cbs_extractions(source, raw) VALUES(:src, CAST(:raw AS JSONB))"), {"src": "chrome_extension", "raw": _json.dumps(raw)})

        league_name = None
        scoring_rules: List[Dict[str, Any]] = []
        roster_positions: Dict[str, int] = {}
        try:
            import re
            for page in (raw.get('pages') or []):
                for tbl in (page.get('tables') or []):
                    headers = tbl.get('headers') or []
                    rows = tbl.get('rows') or []
                    if 'description' in [str(h).lower() for h in headers] and 'setting' in [str(h).lower() for h in headers]:
                        for r in rows:
                            if (str(r.get('DESCRIPTION') or '').strip().lower()) == 'league name':
                                league_name = r.get('SETTING')
                    if set(headers) >= { 'STATS', 'NAME', 'SETTINGS' }:
                        for r in rows:
                            settings = str(r.get('SETTINGS') or '').lower()
                            m = re.search(r"(-?\d+(?:\.\d+)?)\s*points?", settings)
                            if m:
                                scoring_rules.append({
                                    'stat_code': r.get('STATS'),
                                    'stat_name': r.get('NAME'),
                                    'points': float(m.group(1)),
                                })
                    if set(str(h).lower() for h in headers) >= {'status','min','max'}:
                        for r in rows:
                            status = str(r.get('STATUS') or '').strip().upper()
                            if status in ('C','W','F','D','G'):
                                try:
                                    roster_positions[status] = int(str(r.get('MIN') or '0').split()[0])
                                except Exception:
                                    pass
        except Exception:
            pass

        # Persist normalized league, settings, scoring
        saved_league_id = None
        if league_name:
            # Create a minimal FantasyLeague if not exists
            try:
                # Resolve owner from API key if provided, else fallback to placeholder
                owner = None
                try:
                    api_key = request.headers.get('x-api-key') or ''
                    # Also allow Authorization: ApiKey <key>
                    auth = request.headers.get('authorization') or ''
                    if not api_key and auth.lower().startswith('apikey '):
                        api_key = auth.split(' ', 1)[1].strip()
                    if api_key:
                        key_obj = (
                            session.query(FantasyAPIKey)
                            .filter(FantasyAPIKey.api_key == api_key, FantasyAPIKey.is_active == True)
                            .first()
                        )
                        if key_obj and key_obj.user:
                            owner = key_obj.user
                except Exception:
                    # Non-fatal; we will fallback to placeholder user
                    pass

                if not owner:
                    owner = session.query(FantasyUser).filter(FantasyUser.email == 'importer@fantasy.local').first()
                    if not owner:
                        owner = FantasyUser(email='importer@fantasy.local', display_name='Importer')
                        session.add(owner)
                        session.flush()
                league = session.query(FantasyLeague).filter(FantasyLeague.name == league_name).first()
                if not league:
                    league = FantasyLeague(
                        league_id='uhhp',
                        sport='hockey',
                        name=league_name,
                        platform='cbs',
                        owner_id=owner.id,
                        is_public=False,
                        is_active=True,
                    )
                    session.add(league)
                    session.flush()
                saved_league_id = league.id
                # Upsert settings
                settings = session.query(FantasyLeagueSettings).filter(FantasyLeagueSettings.league_id == league.id).first()
                if not settings:
                    settings = FantasyLeagueSettings(
                        league_id=league.id,
                        roster_positions=roster_positions or {},
                        raw_settings_json=payload,
                    )
                    session.add(settings)
                else:
                    settings.roster_positions = roster_positions or {}
                    settings.raw_settings_json = payload
                # Replace scoring rules
                if scoring_rules:
                    session.query(FantasyScoringRule).filter(FantasyScoringRule.league_id == league.id).delete()
                    for r in scoring_rules:
                        session.add(FantasyScoringRule(
                            league_id=league.id,
                            stat_name=str(r.get('stat_code') or ''),
                            stat_description=str(r.get('stat_name') or ''),
                            points=float(r.get('points') or 0.0),
                        ))
            except Exception as e:
                logger.warning(f"Import persist failed: {e}")

        return {"ok": True, "league_name": league_name, "league_id": saved_league_id, "roster_positions": roster_positions, "scoring_rules": scoring_rules}

# Rankings endpoint (public)
@app.get("/api/rankings")
async def get_rankings(season: int = 2024, limit: int = 200):
    """Return skater rankings from cached table for fast frontend consumption."""
    try:
        with get_fantasy_session() as session:
            rows = (
                session.query(FantasySeasonRanking)
                .filter(FantasySeasonRanking.season == season)
                .order_by(FantasySeasonRanking.rank.asc())
                .limit(limit)
                .all()
            )
            archetypes = load_archetype_mapping(20242025 if season == 2024 else season)
            results = [
                {
                    "rank": r.rank,
                    "player_id": r.nhl_player_id,
                    "name": r.player_name,
                    "team": r.team,
                    "position": r.position,
                    "gp": r.gp,
                    "goals": r.goals,
                    "assists": r.assists,
                    "points": r.points,
                    "shots": r.shots,
                    "archetype": archetypes.get(r.nhl_player_id)
                }
                for r in rows
            ]
            return {"season": season, "count": len(results), "results": results}
    except Exception as e:
        logger.error(f"Error reading rankings: {e}")
        raise HTTPException(status_code=500, detail="Failed to read rankings")

def _assign_tiers(items, value_key: str, tiers: int = 5, method: str = 'quantile', gap_sigma: float = 0.5):
    try:
        import numpy as np
    except Exception:
        # Fallback: simple equal-size buckets without numpy
        values = [i.get(value_key, 0) or 0 for i in items]
        sorted_vals = sorted(values, reverse=True)
        breaks = [sorted_vals[min(len(sorted_vals)-1, int(len(sorted_vals)*t/tiers))] for t in range(1, tiers)]
        for it in items:
            v = it.get(value_key, 0) or 0
            tier = 1
            for b in breaks:
                if v < b:
                    tier += 1
            it['tier'] = tier
        return items
    values = np.array([i.get(value_key, 0) or 0 for i in items], dtype=float)
    if len(values) == 0:
        return items
    # Higher value = better tier (tier 1 is best)
    if method == 'kmeans':
        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score
            vals = values.reshape(-1, 1)
            if tiers is None or tiers <= 1:
                # auto-select k by silhouette
                k_candidates = [k for k in range(2, min(10, len(values)) + 1)]
                best_k, best_score, best_labels, best_centers = None, -1, None, None
                for k in k_candidates:
                    km = KMeans(n_clusters=k, n_init=10, random_state=42)
                    labels = km.fit_predict(vals)
                    score = silhouette_score(vals, labels) if len(set(labels)) > 1 else -1
                    if score > best_score:
                        best_k, best_score, best_labels, best_centers = k, score, labels, km.cluster_centers_.flatten()
                labels = best_labels
                centers = best_centers
            else:
                k = min(max(2, tiers), len(values))
                km = KMeans(n_clusters=k, n_init=10, random_state=42)
                labels = km.fit_predict(vals)
                centers = km.cluster_centers_.flatten()
            # Map cluster centers to tiers (higher center -> lower tier number)
            order = np.argsort(-centers)  # descending
            cluster_to_tier = {int(c): int(idx)+1 for idx, c in enumerate(order)}
            for it, lab in zip(items, labels):
                it['tier'] = cluster_to_tier[int(lab)]
            return items
        except Exception:
            method = 'quantile'
    if method == 'gaps':
        # Dynamic tiers based on adjacent gaps in descending value order
        if not items:
            return items
        # Sort by value desc; keep original ref
        sorted_items = sorted(items, key=lambda x: (x.get(value_key, 0) or 0), reverse=True)
        vals = [float(it.get(value_key, 0) or 0) for it in sorted_items]
        # Adjacent diffs (positive)
        diffs = [vals[i] - vals[i+1] for i in range(len(vals)-1)]
        if len(diffs) == 0:
            for it in items:
                it['tier'] = 1
            return items
        try:
            import math
            mu = sum(diffs) / len(diffs)
            var = sum((d - mu) ** 2 for d in diffs) / max(1, len(diffs)-1)
            sigma = math.sqrt(var)
        except Exception:
            mu, sigma = (sum(diffs) / len(diffs), 0.0)
        threshold = mu + sigma * gap_sigma
        tier = 1
        # Assign tiers by scanning gaps
        tiers_assigned = [tier]
        for i, d in enumerate(diffs):
            if d >= threshold:
                tier += 1
            tiers_assigned.append(tier)
        # Map back to original items
        for it, t in zip(sorted_items, tiers_assigned):
            it['tier'] = t
        return items
    # quantile method
    q_breaks = []
    for t in range(1, tiers):
        q = 1.0 - (t/tiers)
        q_breaks.append(float(np.quantile(values, q)))
    for it in items:
        v = float(it.get(value_key, 0) or 0)
        tier = 1
        for b in q_breaks:
            if v < b:
                tier += 1
        it['tier'] = tier
    return items


def _compute_gaps(items, value_key: str, gap_sigma: float = 0.5):
    """Return sorted items with gap diagnostics for debugging tiers-by-gaps.
    Each entry contains: rank, value, next_value, gap, tier.
    """
    if not items:
        return {"threshold": 0, "mu": 0, "sigma": 0, "rows": []}
    sorted_items = sorted(items, key=lambda x: (x.get(value_key, 0) or 0), reverse=True)
    vals = [float(it.get(value_key, 0) or 0) for it in sorted_items]
    diffs = [vals[i] - vals[i+1] for i in range(len(vals)-1)]
    if len(diffs) == 0:
        rows = []
        for idx, it in enumerate(sorted_items):
            rows.append({
                "rank": idx + 1,
                "player_id": it.get("player_id"),
                "name": it.get("name"),
                "position": it.get("position"),
                "team": it.get("team"),
                "value": vals[idx],
                "next_value": None,
                "gap": None,
                "tier": 1,
            })
        return {"threshold": 0, "mu": 0, "sigma": 0, "rows": rows}
    mu = sum(diffs) / len(diffs)
    var = sum((d - mu) ** 2 for d in diffs) / max(1, len(diffs)-1)
    import math
    sigma = math.sqrt(var)
    threshold = mu + sigma * gap_sigma
    tier = 1
    rows = []
    for idx, it in enumerate(sorted_items):
        next_val = vals[idx+1] if idx+1 < len(vals) else None
        gap = (vals[idx] - next_val) if next_val is not None else None
        if idx > 0 and (rows[-1]["gap"] is not None) and rows[-1]["gap"] >= threshold:
            tier += 1
        rows.append({
            "rank": idx + 1,
            "player_id": it.get("player_id"),
            "name": it.get("name"),
            "position": it.get("position"),
            "team": it.get("team"),
            "value": vals[idx],
            "next_value": next_val,
            "gap": gap,
            "tier": tier,
        })
    return {"threshold": threshold, "mu": mu, "sigma": sigma, "rows": rows}


@app.get("/api/vorp")
async def get_vorp(
    season: int = 20242025,
    centers_keep: int = 40,
    wings_keep: int = 60,
    defence_keep: int = 40,
    tiers: int = 5,
    method: str = 'quantile',
    value: str = 'vorp',
    gap_sigma: float = 0.3,
    min_gp: int = 11,
):
    """Compute VORP for Points: top N forwards and top M defence.

    VORP = player's points - replacement points at same position group.
    Replacement points are defined as the next player after the kept list (e.g., 101st forward, 41st defenceman).
    """
    try:
        with get_fantasy_session() as session:
            rows = (
                session.query(FantasySeasonRanking)
                .filter(FantasySeasonRanking.season == season)
                .all()
            )
            if not rows:
                return {"season": season, "centers": [], "wings": [], "defence": []}
            # Production-only features path: PTS/60, PTS/GM, PP points, PP minutes
            if value in ('production', 'prod'):
                nhl_url = os.getenv("NHL_DATABASE_URL")
                # Lazy import to avoid env requirements when unused
                if nhl_url:
                    engine = create_engine(nhl_url, pool_pre_ping=True)
                else:
                    from src.database.connection import connect_with_connector  # type: ignore
                    engine = connect_with_connector()
                season_val = int(season)
                prod_sql = text(
                    """
                    WITH pg AS (
                      SELECT pg.player_id, SUM(pg.points) AS points, COUNT(pg.id) AS gp, p.position_code
                      FROM player_game_stats pg
                      JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
                      JOIN players p ON p.id = pg.player_id
                      GROUP BY pg.player_id, p.position_code
                    ), toi AS (
                      SELECT pg.player_id,
                             SUM(
                               CASE WHEN position(':' in pg.toi) > 0 THEN
                                 CAST(split_part(pg.toi, ':', 1) AS INT)*60 + CAST(split_part(pg.toi, ':', 2) AS INT)
                               ELSE 0 END
                             ) AS toi_sec
                      FROM player_game_stats pg
                      JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
                      GROUP BY pg.player_id
                    ), ppp AS (
                      SELECT pg.player_id, SUM(COALESCE(pg.power_play_points,0)) AS pp_points
                      FROM player_game_stats pg
                      JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
                      GROUP BY pg.player_id
                    ), sh AS (
                      SELECT sm.player_id,
                             SUM(CASE WHEN sm.strength_state = 'PP' THEN (
                               CASE WHEN position(':' in sm.duration) > 0 THEN
                                 CAST(split_part(sm.duration, ':', 1) AS INT)*60 + CAST(split_part(sm.duration, ':', 2) AS INT)
                               ELSE 0 END) ELSE 0 END) AS pp_sec
                      FROM player_shift_metrics sm
                      JOIN games g ON g.id = sm.game_id AND g.season = :season AND g.game_type = 2
                      GROUP BY sm.player_id
                    )
                    SELECT pg.player_id, pg.position_code, COALESCE(pg.points,0) AS points, COALESCE(pg.gp,0) AS gp,
                           COALESCE(toi.toi_sec,0) AS toi_sec, COALESCE(ppp.pp_points,0) AS pp_points, COALESCE(sh.pp_sec,0) AS pp_sec
                    FROM pg
                    LEFT JOIN toi ON toi.player_id = pg.player_id
                    LEFT JOIN ppp ON ppp.player_id = pg.player_id
                    LEFT JOIN sh ON sh.player_id = pg.player_id
                    """
                )
                with engine.connect() as conn:
                    res = conn.execute(prod_sql, {"season": season_val})
                    prod_rows = res.fetchall()
                id_to_info = {r.nhl_player_id: r for r in rows}
                def map_prod(r):
                    player_id, pos, points, gp, toi_sec, pp_points, pp_sec = r
                    points = float(points or 0)
                    gp = int(gp or 0)
                    toi_sec = float(toi_sec or 0)
                    pp_points = float(pp_points or 0)
                    pp_sec = float(pp_sec or 0)
                    ppg = (points / gp) if gp else 0.0
                    pts_per_60 = (points * 3600.0 / toi_sec) if toi_sec > 0 else 0.0
                    pp_min_pg = (pp_sec / 60.0) / gp if gp else 0.0
                    pp_points_pg = (pp_points / gp) if gp else 0.0
                    base = {
                        "player_id": int(player_id),
                        "name": None,
                        "team": None,
                        "position": pos or '',
                        "gp": gp,
                        "points": int(points),
                        "ppg": ppg,
                        "pts_per_60": pts_per_60,
                        "pp_points": pp_points_pg,
                        "pp_min_pg": pp_min_pg,
                    }
                    info = id_to_info.get(int(player_id))
                    if info:
                        base["name"] = info.player_name
                        base["team"] = info.team
                        if not base["position"]:
                            base["position"] = info.position
                    return base
                items = [map_prod(r) for r in prod_rows]
                # Filter by minimum games played
                items = [x for x in items if int(x.get('gp') or 0) >= min_gp]
                # Split groups
                centers = [c for c in items if (c.get('position') or '').upper() == 'C']
                wings = [c for c in items if (c.get('position') or '').upper() in ['L','R']]
                defence = [c for c in items if (c.get('position') or '').upper() == 'D']
                import math
                def score_group(arr):
                    if not arr:
                        return arr
                    # Compute means and stds
                    def mean_std(vals):
                        if not vals:
                            return (0.0, 1.0)
                        m = sum(vals)/len(vals)
                        var = sum((v-m)*(v-m) for v in vals)/max(1, len(vals)-1)
                        s = math.sqrt(var) if var > 0 else 1.0
                        return (m, s)
                    p60_vals = [x['pts_per_60'] for x in arr]
                    ppg_vals = [x['ppg'] for x in arr]
                    ppp_vals = [x['pp_points'] for x in arr]
                    ppm_vals = [x['pp_min_pg'] for x in arr]
                    m_p60, s_p60 = mean_std(p60_vals)
                    m_ppg, s_ppg = mean_std(ppg_vals)
                    m_ppp, s_ppp = mean_std(ppp_vals)
                    m_ppm, s_ppm = mean_std(ppm_vals)
                    for x in arr:
                        z_p60 = (x['pts_per_60'] - m_p60)/s_p60
                        z_ppg = (x['ppg'] - m_ppg)/s_ppg
                        z_ppp = (x['pp_points'] - m_ppp)/s_ppp
                        z_ppm = (x['pp_min_pg'] - m_ppm)/s_ppm
                        # Weighted composite per your spec
                        x['score'] = (
                            0.50 * z_ppg +
                            0.25 * z_ppp +
                            0.15 * z_ppm +
                            0.10 * z_p60
                        )
                        x['vorp_pts'] = x['score']
                    return arr
                centers = score_group(centers)
                wings = score_group(wings)
                defence = score_group(defence)
                # Sort by score and keep top K per group
                centers_sorted = sorted(centers, key=lambda x: x['score'], reverse=True)[:centers_keep]
                wings_sorted = sorted(wings, key=lambda x: x['score'], reverse=True)[:wings_keep]
                defence_sorted = sorted(defence, key=lambda x: x['score'], reverse=True)[:defence_keep]
                centers_top = _assign_tiers(centers_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                wings_top = _assign_tiers(wings_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                defence_top = _assign_tiers(defence_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                return {
                    "season": season,
                    "centers": centers_top,
                    "wings": wings_top,
                    "defence": defence_top,
                    "forwards": [dict(x, **{"group": "C"}) for x in centers_top] + [dict(x, **{"group": "W"}) for x in wings_top],
                }
            # Composite score path
            if value == 'composite':
                try:
                    engine = _get_nhl_engine()
                except Exception as _e:
                    logger.warning(f"Auction birthdate enrichment failed early: {_e}")
                    engine = None
                season_val = int(season)
                core_sql = text(
                    """
                    WITH pg AS (
                      SELECT pg.player_id, SUM(pg.goals) AS goals, SUM(pg.shots) AS shots,
                             COUNT(pg.id) AS gp, p.position_code
                      FROM player_game_stats pg
                      JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
                      JOIN players p ON p.id = pg.player_id
                      GROUP BY pg.player_id, p.position_code
                    ), adv AS (
                      SELECT a.player_id, AVG(a."GF60") AS gf60
                      FROM player_game_advanced_metrics_flat a
                      JOIN games g ON g.id = a.game_id AND g.season = :season AND g.game_type = 2
                      GROUP BY a.player_id
                    ), sh AS (
                      SELECT sm.player_id,
                             SUM(CASE WHEN sm.strength_state = 'PP' THEN (
                               CASE WHEN position(':' in sm.duration) > 0 THEN
                                 CAST(split_part(sm.duration, ':', 1) AS INT)*60 + CAST(split_part(sm.duration, ':', 2) AS INT)
                               ELSE 0 END) ELSE 0 END) AS pp_sec,
                             SUM(CASE WHEN sm.strength_state = 'EV' THEN (
                               CASE WHEN position(':' in sm.duration) > 0 THEN
                                 CAST(split_part(sm.duration, ':', 1) AS INT)*60 + CAST(split_part(sm.duration, ':', 2) AS INT)
                               ELSE 0 END) ELSE 0 END) AS ev_sec,
                             SUM(CASE WHEN sm.strength_state = 'SH' THEN (
                               CASE WHEN position(':' in sm.duration) > 0 THEN
                                 CAST(split_part(sm.duration, ':', 1) AS INT)*60 + CAST(split_part(sm.duration, ':', 2) AS INT)
                               ELSE 0 END) ELSE 0 END) AS sh_sec
                      FROM player_shift_metrics sm
                      JOIN games g ON g.id = sm.game_id AND g.season = :season AND g.game_type = 2
                      GROUP BY sm.player_id
                    )
                    SELECT pg.player_id, pg.position_code, pg.goals, pg.shots, pg.gp,
                           COALESCE(adv.gf60, 0) AS gf60,
                           COALESCE(sh.pp_sec, 0) AS pp_sec,
                           COALESCE(sh.ev_sec, 0) AS ev_sec,
                           COALESCE(sh.sh_sec, 0) AS sh_sec
                    FROM pg
                    LEFT JOIN adv ON adv.player_id = pg.player_id
                    LEFT JOIN sh ON sh.player_id = pg.player_id
                    """
                )
                with engine.connect() as conn:
                    res = conn.execute(core_sql, {"season": season_val})
                    core_rows = res.fetchall()
                id_to_info = {r.nhl_player_id: r for r in rows}
                def comp_row(r):
                    player_id, pos, goals, shots, gp, gf60, pp_sec, ev_sec, sh_sec = r
                    goals = goals or 0
                    shots = shots or 0
                    gp = gp or 0
                    gf60 = float(gf60 or 0)
                    pp_min_pg = (float(pp_sec or 0) / 60.0) / gp if gp else 0.0
                    ev_min_pg = (float(ev_sec or 0) / 60.0) / gp if gp else 0.0
                    total_sec = float((pp_sec or 0) + (ev_sec or 0) + (sh_sec or 0))
                    ev_share = (float(ev_sec or 0) / total_sec) if total_sec > 0 else 0.0
                    shots_pg = (float(shots) / gp) if gp else 0.0
                    shots_ev_best = shots_pg * ev_share
                    finishing_index = (float(goals) / float(shots)) if shots else 0.0
                    score = (
                        0.35 * finishing_index +
                        0.20 * gf60 +
                        0.15 * shots_ev_best +
                        0.15 * pp_min_pg +
                        0.05 * ev_min_pg
                    )
                    base = {
                        "player_id": int(player_id),
                        "name": None,
                        "team": None,
                        "position": pos or '',
                        "gp": gp or 0,
                        "points": None,
                        "score": score,
                        "vorp_pts": score,  # for UI compatibility
                    }
                    info = id_to_info.get(int(player_id))
                    if info:
                        base["name"] = info.player_name
                        base["team"] = info.team
                        base["gp"] = info.gp
                        base["points"] = info.points
                        if (pos or '') == '':
                            base["position"] = info.position
                    return base
                comp = [comp_row(r) for r in core_rows]
                # Filter by minimum games played
                comp = [x for x in comp if int(x.get('gp') or 0) >= min_gp]
                centers = [c for c in comp if (c.get('position') or '').upper() == 'C']
                wings = [c for c in comp if (c.get('position') or '').upper() in ['L','R']]
                defence = [c for c in comp if (c.get('position') or '').upper() == 'D']
                centers_sorted = sorted(centers, key=lambda x: x['score'], reverse=True)[:centers_keep]
                wings_sorted = sorted(wings, key=lambda x: x['score'], reverse=True)[:wings_keep]
                defence_sorted = sorted(defence, key=lambda x: x['score'], reverse=True)[:defence_keep]
                centers_top = _assign_tiers(centers_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                wings_top = _assign_tiers(wings_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                defence_top = _assign_tiers(defence_sorted, 'score', tiers=tiers, method=method, gap_sigma=gap_sigma)
                return {
                    "season": season,
                    "centers": centers_top,
                    "wings": wings_top,
                    "defence": defence_top,
                    "forwards": [dict(x, **{"group": "C"}) for x in centers_top] + [dict(x, **{"group": "W"}) for x in wings_top],
                }
            # Partition by position group
            centers = [r for r in rows if (r.position or '').upper() == 'C' and int(r.gp or 0) >= min_gp]
            wings = [r for r in rows if (r.position or '').upper() in ['L','R'] and int(r.gp or 0) >= min_gp]
            defence = [r for r in rows if (r.position or '').upper() == 'D' and int(r.gp or 0) >= min_gp]
            centers_sorted = sorted(centers, key=lambda r: (r.points or 0), reverse=True)
            wings_sorted = sorted(wings, key=lambda r: (r.points or 0), reverse=True)
            defence_sorted = sorted(defence, key=lambda r: (r.points or 0), reverse=True)
            # Determine replacement benchmarks
            # Replacement per-game points
            def _ppg(r):
                pts = r.points or 0
                gp = r.gp or 0
                return float(pts) / float(gp) if gp else 0.0
            c_repl_ppg = _ppg(centers_sorted[centers_keep]) if len(centers_sorted) > centers_keep else (_ppg(centers_sorted[-1]) if centers_sorted else 0.0)
            w_repl_ppg = _ppg(wings_sorted[wings_keep]) if len(wings_sorted) > wings_keep else (_ppg(wings_sorted[-1]) if wings_sorted else 0.0)
            d_repl_ppg = _ppg(defence_sorted[defence_keep]) if len(defence_sorted) > defence_keep else (_ppg(defence_sorted[-1]) if defence_sorted else 0.0)
            # Build outputs
            def map_row(r, repl_ppg):
                return {
                    "player_id": r.nhl_player_id,
                    "name": r.player_name,
                    "team": r.team,
                    "position": r.position,
                    "gp": r.gp,
                    "points": r.points,
                    "ppg": (float(r.points or 0) / float(r.gp or 1)) if (r.gp or 0) else 0.0,
                    "vorp_pts": ((float(r.points or 0) / float(r.gp or 1)) if (r.gp or 0) else 0.0) - repl_ppg,
                }
            centers_top = [map_row(r, c_repl_ppg) for r in centers_sorted[:centers_keep]]
            wings_top = [map_row(r, w_repl_ppg) for r in wings_sorted[:wings_keep]]
            defence_top = [map_row(r, d_repl_ppg) for r in defence_sorted[:defence_keep]]
            # Assign tiers within each group based on VORP points
            # key selection: if value == 'points' we cluster on PPG tiers rather than total points
            key = 'ppg' if value == 'points' else 'vorp_pts'
            centers_top = _assign_tiers(centers_top, key, tiers=tiers, method=method, gap_sigma=gap_sigma)
            wings_top = _assign_tiers(wings_top, key, tiers=tiers, method=method, gap_sigma=gap_sigma)
            defence_top = _assign_tiers(defence_top, key, tiers=tiers, method=method, gap_sigma=gap_sigma)
            return {
                "season": season,
                "replacement": {"centers_ppg": c_repl_ppg, "wings_ppg": w_repl_ppg, "defence_ppg": d_repl_ppg},
                "centers": centers_top,
                "wings": wings_top,
                "defence": defence_top,
                # Backwards-compatible combined forwards (centers + wings)
                "forwards": [dict(x, **{"group": "C"}) for x in centers_top] + [dict(x, **{"group": "W"}) for x in wings_top],
            }
    except Exception as e:
        logger.error(f"Error computing VORP: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute VORP")

@app.get("/api/vorp_gaps")
async def get_vorp_gaps(season: int = 20242025, forwards_keep: int = 100, defence_keep: int = 40, value: str = 'vorp', gap_sigma: float = 0.5):
    """Return gaps and dynamic tiers based on adjacent differences for forwards and defence."""
    try:
        with get_fantasy_session() as session:
            rows = (
                session.query(FantasySeasonRanking)
                .filter(FantasySeasonRanking.season == season)
                .all()
            )
            if not rows:
                return {"season": season, "forwards": {}, "defence": {}}
            forwards = [r for r in rows if (r.position or '').upper() in ['L','R','C']]
            defence = [r for r in rows if (r.position or '').upper() == 'D']
            forwards_sorted = sorted(forwards, key=lambda r: (r.points or 0), reverse=True)
            defence_sorted = sorted(defence, key=lambda r: (r.points or 0), reverse=True)
            f_repl = forwards_sorted[forwards_keep].points if len(forwards_sorted) > forwards_keep else (forwards_sorted[-1].points if forwards_sorted else 0)
            d_repl = defence_sorted[defence_keep].points if len(defence_sorted) > defence_keep else (defence_sorted[-1].points if defence_sorted else 0)
            f_repl = f_repl or 0
            d_repl = d_repl or 0
            def map_row(r, repl):
                base = {
                    "player_id": r.nhl_player_id,
                    "name": r.player_name,
                    "team": r.team,
                    "position": r.position,
                    "gp": r.gp,
                    "points": r.points,
                    "vorp_pts": (r.points or 0) - repl,
                }
                return base
            f_items = [map_row(r, f_repl) for r in forwards_sorted[:forwards_keep]]
            d_items = [map_row(r, d_repl) for r in defence_sorted[:defence_keep]]
            key = 'points' if value == 'points' else 'vorp_pts'
            f_gaps = _compute_gaps(f_items, key, gap_sigma=gap_sigma)
            d_gaps = _compute_gaps(d_items, key, gap_sigma=gap_sigma)
            return {
                "season": season,
                "replacement": {"forwards_pts": f_repl, "defence_pts": d_repl},
                "forwards": f_gaps,
                "defence": d_gaps,
            }
    except Exception as e:
        logger.error(f"Error computing VORP gaps: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute VORP gaps")
# Projections: read from fantasy_player_projections
@app.get("/api/projections", response_model=dict)
async def get_projections(
    season: int = 2025,
    source: str | None = None,
    kind: str | None = None,
    league_id: int | None = None,
    limit: int = 500,
    offset: int = 0,
):
    from sqlalchemy import text as sa_text
    try:
        with get_fantasy_session() as session:
            # Load scoring rules if league provided
            scoring_rules: List[Dict[str, Any]] = []
            if league_id is not None:
                try:
                    srows = session.execute(sa_text(
                        "SELECT stat_code, stat_name, points FROM cbs_scoring_rules WHERE league_id = :lid"
                    ), {"lid": int(league_id)}).fetchall()
                    scoring_rules = [
                        {"code": str(r.stat_code), "name": (str(r.stat_name) if r.stat_name is not None else ""), "w": float(r.points)}
                        for r in srows
                    ]
                except Exception as e:
                    logger.warning(f"Scoring rules load failed for league {league_id}: {e}")
            # For avg mode, restrict to the specified UHHP codes only
            AVG_SOURCES = {"avg", "avg_all", "avg_experts", "average"}
            is_avg = (source or "").lower() in AVG_SOURCES
            VORP_SOURCES = {"vorp_available", "vorp_all", "vorp_cap"}
            is_vorp = (source or "").lower() in VORP_SOURCES
            if is_avg and scoring_rules:
                allowed = {"+/-", "A", "DG", "G", "GA", "PIM", "S", "SHG", "W"}
                scoring_rules = [r for r in scoring_rules if str(r.get("code") or "").upper() in allowed]
            # Normalize pagination early so it's always available
            local_limit = max(1, min(10000, int(limit)))
            local_offset = max(0, int(offset))

            # Support aggregated average across all sources when source is a special avg token
            # is_avg already computed above

            params: dict[str, Any] = {"season": int(season), "limit": local_limit, "offset": local_offset}

            # Scoring helpers must be defined BEFORE any FP computation
            def _norm_key(s: str) -> str:
                return ''.join(ch for ch in (s or '').lower() if ch.isalnum())

            def compute_fp(metrics: Dict[str, Any]) -> float:
                if not scoring_rules:
                    return 0.0
                total = 0.0
                norm_metrics = {_norm_key(k): v for k, v in (metrics or {}).items()}
                for rule in scoring_rules:
                    code = rule.get("code") or ""
                    name = rule.get("name") or ""
                    weight = float(rule.get("w") or 0.0)
                    v = None
                    if code:
                        v = metrics.get(code)
                        if v is None:
                            v = metrics.get(str(code).lower())
                    if v is None and name:
                        v = norm_metrics.get(_norm_key(str(name)))
                    if v is None:
                        alias_map = {
                            # Skaters
                            "G": ["goals", "g"],
                            "A": ["assists", "a"],
                            "SOG": ["shotsongoal", "shots", "sog"],
                            "PIM": ["penaltyminutes", "pim"],
                            "+/-": ["plusminus"],
                            "BLK": ["blockedshots", "blocks", "blk"],
                            "HIT": ["hits"],
                            "PPP": ["pppoints", "powerplaypoints", "ppp", "pp_points"],
                            "GP": ["gamesplayed", "gp", "games"],
                            "TOI": ["timeonicepergame", "toipergame", "avgtoi", "toigp", "toiper_gp"],
                            "SHG": ["shorthandedgoals", "shg"],
                            "DG": ["defensemangoals", "defencemangoals", "defenseman_goals", "dg"],
                            # Goalies
                            "W": ["winsgoalie", "wins"],
                            "SO": ["shutoutsgoalie", "shutouts"],
                            "SV": ["savesgoalie", "saves", "sv"],
                            "S": ["savesgoalie", "saves", "sv"],
                            "GA": ["goalsagainst", "ga", "goals_against"],
                        }
                        aliases = alias_map.get(str(code).upper(), [])
                        for ak in aliases:
                            v = norm_metrics.get(ak)
                            if v is not None:
                                break
                        if v is None:
                            # Friendly labels used by avg metrics
                            for fk in [
                                "hits","goals","points","assists","pp_points",
                                "games_played","blocked_shots","shots_on_goal",
                                "penalty_minutes","time_on_ice_per_game",
                                "wins","shutouts","saves","goals_against",
                            ]:
                                v = norm_metrics.get(fk)
                                if v is not None:
                                    break
                    try:
                        total += (float(v) if v is not None else 0.0) * float(weight)
                    except Exception:
                        continue
                return total
            # Special handling: VORP computed on-the-fly; returns items with
            #  - fantasy_points from AVG aggregation (display)
            #  - vorp: computed against replacement baselines (available/all)
            if is_vorp:
                # 1) Build AVG-like baseline list for all players
                where = ["season = :season"]
                where_sql = " AND ".join(where)
                sql_all = sa_text(
                    f"""
                    SELECT season, source, kind, nhl_player_id, player_name, position, team, metrics
                      FROM fantasy_player_projections
                     WHERE {where_sql}
                    """
                )
                rows_all = session.execute(sql_all, params).fetchall()
                raw_items = [dict(r._mapping) for r in rows_all]

                def _norm_pos_v(p: str | None) -> str:
                    pp = (p or "").strip().upper()
                    if pp in ("LW", "RW"): return "W"
                    if pp in ("D", "DEF", "DEFENSE", "DEFENCE"): return "D"
                    if pp in ("C", "CTR", "CENTER", "CENTRE"): return "C"
                    if pp in ("G", "GK", "GL", "GOALIE", "GOALTENDER"): return "G"
                    if pp in ("FWD", "F"): return "F"
                    return pp

                # Compute per-row FP using UHHP rules (same as AVG compute_fp_avg)
                def compute_fp_avg_local(m: Dict[str, Any], pos_str: str | None) -> float:
                    try:
                        raw = m or {}
                        # Normalize keys to alnum-lower for alias lookup
                        def _n(s: str) -> str:
                            return ''.join(ch for ch in (s or '').lower() if ch.isalnum())
                        nm = {_n(k): v for k, v in raw.items()}

                        def _get(labels: list[str], fallback_keys: list[str] | None = None) -> float:
                            # Try normalized aliases first
                            for lab in labels:
                                v = nm.get(_n(lab))
                                if v is not None:
                                    try:
                                        return float(v)
                                    except Exception:
                                        pass
                            # Then try raw keys exactly as provided
                            if fallback_keys:
                                for k in fallback_keys:
                                    if k in raw and raw[k] is not None:
                                        try:
                                            return float(raw[k])
                                        except Exception:
                                            pass
                            return 0.0

                        # Skater metrics
                        g = _get(["goals", "g"], ["Goals"])  # total DG handled via weight
                        a = _get(["assists", "a"], ["Assists"])  # DA handled via weight
                        pm = _get(["plusminus", "+/-", "pm"], ["Plus_Minus"])  # Plus/Minus
                        shg = _get(["shorthandedgoals", "shg"], ["Short_Handed_Goals"])  # SHG
                        # Goalie metrics
                        wv = _get(["winsgoalie", "wins", "w"], ["Wins"])  # Wins
                        sv = _get(["savesgoalie", "saves", "sv", "s"], ["Saves"])  # Saves
                        ga = _get(["goalsagainst", "ga", "goals_against"], ["Goals_Against"])  # Goals Against

                        is_def = (str(pos_str or "").upper().startswith("D"))
                        # Apply total weights directly so DG totals 5 and DA totals 3 for defensemen
                        goal_weight = 5.0 if is_def else 3.0
                        assist_weight = 3.0 if is_def else 2.0
                        return (
                            0.25 * pm +
                            assist_weight * a +
                            goal_weight * g +
                            2.00 * shg +
                            2.00 * wv +
                            0.20 * sv +
                            (-1.25) * ga
                        )
                    except Exception:
                        return 0.0

                # Group rows by player_id or name, average FP and target metrics
                from collections import defaultdict, Counter
                by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
                # Normalize metrics payloads
                def _ensure_dict(obj: Any) -> Dict[str, Any]:
                    if isinstance(obj, dict):
                        return obj
                    if isinstance(obj, str):
                        try:
                            import json as _json
                            parsed = _json.loads(obj)
                            return parsed if isinstance(parsed, dict) else {}
                        except Exception:
                            return {}
                    return {}

                for it in raw_items:
                    metrics = _ensure_dict(it.get("metrics"))
                    pos = _norm_pos_v(it.get("position"))
                    fp = compute_fp_avg_local(metrics, pos)
                    by_key_key = f"id:{int(it.get('nhl_player_id'))}" if it.get("nhl_player_id") not in (None, "", 0) else f"name:{(str(it.get('player_name') or '').strip().lower())}"
                    by_key.setdefault(by_key_key, []).append({
                        "nhl_player_id": it.get("nhl_player_id"),
                        "player_name": it.get("player_name"),
                        "position": pos,
                        "team": it.get("team"),
                        "fp": fp,
                    })

                base_items: list[dict[str, Any]] = []
                for key_k, group in by_key.items():
                    avg_fp = sum(float(g.get("fp") or 0.0) for g in group) / max(1, len(group))
                    nhl_ids = [g.get("nhl_player_id") for g in group if g.get("nhl_player_id")]
                    nhl_id = nhl_ids[0] if nhl_ids else None
                    names = [str(g.get("player_name") or "") for g in group if (g.get("player_name") or "").strip()]
                    name = names[0] if names else None
                    pos_counts = Counter([str(g.get("position") or "").upper() for g in group if (g.get("position") or "")])
                    pos = (pos_counts.most_common(1)[0][0] if pos_counts else "")
                    teams = [str(g.get("team") or "") for g in group if (g.get("team") or "").strip()]
                    team = teams[0] if teams else None
                    base_items.append({
                        "nhl_player_id": nhl_id,
                        "player_name": name,
                        "position": pos,
                        "team": team,
                        "fantasy_points": float(avg_fp),
                    })

                # 2) Determine available pool if requested
                avail_set: set[int] = set()
                if (source or "").lower() in ("vorp_available", "vorp_cap") and league_id is not None:
                    # rights-held
                    rows_rights = session.execute(sa_text(
                        """
                        SELECT DISTINCT COALESCE(r.nhl_player_id, m.nhl_player_id) AS nhl_player_id
                          FROM cbs_rosters r
                          LEFT JOIN cbs_player_map m ON m.cbs_player_id = r.cbs_player_id
                         WHERE r.league_id = :lid
                           AND r.slot_type IN ('A','I')
                           AND (r.years IS NULL OR r.years NOT IN (1,2,3))
                        """
                    ), {"lid": int(league_id)}).fetchall()
                    for r in rows_rights:
                        pid = getattr(r, 'nhl_player_id', None)
                        try:
                            if pid is not None:
                                avail_set.add(int(pid))
                        except Exception:
                            pass
                    # unrostered
                    rows_unrostered = session.execute(sa_text(
                        """
                        WITH any_in_roster AS (
                          SELECT DISTINCT COALESCE(r.nhl_player_id, m.nhl_player_id) AS nhl_player_id
                            FROM cbs_rosters r
                            LEFT JOIN cbs_player_map m ON m.cbs_player_id = r.cbs_player_id
                           WHERE r.league_id = :lid
                        )
                        SELECT p.nhl_player_id
                          FROM fantasy_player_projections p
                          LEFT JOIN any_in_roster ar ON ar.nhl_player_id = p.nhl_player_id
                         WHERE p.season = :season AND ar.nhl_player_id IS NULL
                        """
                    ), {"lid": int(league_id), "season": int(season)}).fetchall()
                    for r in rows_unrostered:
                        pid = getattr(r, 'nhl_player_id', None)
                        try:
                            if pid is not None:
                                avail_set.add(int(pid))
                        except Exception:
                            pass

                # 3) Compute baselines by position using number of teams
                num_teams = 12
                try:
                    if league_id is not None:
                        trow = session.execute(sa_text("SELECT COUNT(*) AS c FROM cbs_teams WHERE league_id=:lid"), {"lid": int(league_id)}).fetchone()
                        if trow and getattr(trow, 'c', None) is not None:
                            num_teams = max(1, int(trow.c))
                except Exception:
                    pass

                def _sorted_pool(pos_code: str) -> list[dict[str, Any]]:
                    pool = [it for it in base_items if str(it.get("position") or "").upper() == pos_code]
                    if avail_set:
                        pool = [it for it in pool if (it.get("nhl_player_id") is not None and int(it.get("nhl_player_id")) in avail_set)]
                    pool.sort(key=lambda x: float(x.get("fantasy_points") or 0.0), reverse=True)
                    return pool

                pool_C = _sorted_pool("C")
                pool_W = _sorted_pool("W")
                pool_D = _sorted_pool("D")
                pool_G = _sorted_pool("G")

                c_slots = num_teams * 2
                w_slots = num_teams * 3
                d_slots = num_teams * 4
                g_slots = num_teams * 2
                f_slots = num_teams * 4

                def _nth_fp(pool: list[dict[str, Any]], n: int) -> float:
                    if n <= 0 or not pool:
                        return 0.0
                    idx = min(len(pool), n) - 1
                    try:
                        return float(pool[idx].get("fantasy_points") or 0.0)
                    except Exception:
                        return 0.0

                # Flex baseline = forwards leftover after filling C and W starters
                used_ids: set[int] = set()
                for it in pool_C[:c_slots]:
                    try:
                        if it.get("nhl_player_id") is not None:
                            used_ids.add(int(it.get("nhl_player_id")))
                    except Exception:
                        pass
                for it in pool_W[:w_slots]:
                    try:
                        if it.get("nhl_player_id") is not None:
                            used_ids.add(int(it.get("nhl_player_id")))
                    except Exception:
                        pass

                forward_pool = [it for it in base_items if str(it.get("position") or "").upper() in ("C","W","F")]
                if avail_set:
                    forward_pool = [it for it in forward_pool if (it.get("nhl_player_id") is not None and int(it.get("nhl_player_id")) in avail_set)]
                forward_pool.sort(key=lambda x: float(x.get("fantasy_points") or 0.0), reverse=True)
                forward_leftovers = [it for it in forward_pool if (it.get("nhl_player_id") is None or int(it.get("nhl_player_id")) not in used_ids)]

                c_repl = _nth_fp(pool_C, c_slots)
                w_repl = _nth_fp(pool_W, w_slots)
                d_repl = _nth_fp(pool_D, d_slots)
                g_repl = _nth_fp(pool_G, g_slots)
                f_repl = _nth_fp(forward_leftovers, f_slots)

                # 4) Compute vorp per player and sort by vorp desc
                results: list[dict[str, Any]] = []
                for it in base_items:
                    pid = it.get("nhl_player_id")
                    pos = str(it.get("position") or "").upper()
                    fpv = float(it.get("fantasy_points") or 0.0)
                    if pos == "C":
                        repl = min(c_repl, f_repl) if f_repl > 0 else c_repl
                    elif pos == "W":
                        repl = min(w_repl, f_repl) if f_repl > 0 else w_repl
                    elif pos == "D":
                        repl = d_repl
                    elif pos == "G":
                        repl = g_repl
                    else:
                        repl = f_repl if f_repl > 0 else 0.0
                    vorp_val = fpv - float(repl or 0.0)
                    out = {
                        "season": int(season),
                        "source": (source or "").lower(),
                        "kind": kind,
                        "nhl_player_id": pid,
                        "player_name": it.get("player_name"),
                        "position": pos,
                        "team": it.get("team"),
                        "fantasy_points": fpv,
                        "vorp": float(vorp_val),
                    }
                    results.append(out)

                # 5) Market-calibrated VORP salary using available cap and open roster slots
                total_available_cap = 0.0
                total_contracted_counts = 0
                try:
                    if league_id is not None:
                        # Per-team current spend (years 1-3) and cap hits
                        rows_cap = session.execute(sa_text(
                            """
                            SELECT t.id AS team_id,
                                   COALESCE(SUM(CASE WHEN r.years IN (1,2,3) THEN COALESCE(NULLIF(r.salary, ''), '0')::numeric ELSE 0 END), 0) AS spend,
                                   COALESCE(COUNT(CASE WHEN r.years IN (1,2,3) THEN 1 END), 0) AS contracted_count,
                                   COALESCE(h.cap_hits, 0) AS cap_hits
                              FROM cbs_teams t
                              LEFT JOIN cbs_rosters r
                                ON r.league_id = t.league_id AND r.team_id = t.id
                              LEFT JOIN cbs_team_cap_hits h
                                ON h.league_id = t.league_id AND h.team_id = t.id
                             WHERE t.league_id = :lid
                             GROUP BY t.id, h.cap_hits
                            """
                        ), {"lid": int(league_id)}).fetchall()
                        for rr in rows_cap:
                            try:
                                spend_v = float(getattr(rr, 'spend', 0) or 0)
                                caph_v = float(getattr(rr, 'cap_hits', 0) or 0)
                                contracted_v = int(getattr(rr, 'contracted_count', 0) or 0)
                                total_contracted_counts += contracted_v
                                # Use different per-team budget when vorp_cap requested (reflect UI Cap Summary's budget)
                                per_team_budget = 100.0
                                if (source or "").lower() == "vorp_cap":
                                    per_team_budget = 120.0 if False else 100.0
                                avail = per_team_budget - (spend_v + caph_v)
                                if avail > 0:
                                    total_available_cap += avail
                            except Exception:
                                continue
                except Exception:
                    total_available_cap = 0.0

                # Estimate remaining roster slots across league (UHHP default 15 per team)
                roster_size = (2 + 3 + 4 + 2 + 4)  # C,W,D,G,F
                total_slots_remaining = max(0, num_teams * roster_size - total_contracted_counts)
                if total_slots_remaining <= 0:
                    total_slots_remaining = num_teams * 5  # conservative fallback

                # Build the market pool: top remaining candidates by VORP limited to expected open slots
                def _pid_in_avail(pid_val: Any) -> bool:
                    try:
                        return (not avail_set) or (pid_val is not None and int(pid_val) in avail_set)
                    except Exception:
                        return not bool(avail_set)

                market_pool = [r for r in results if _pid_in_avail(r.get("nhl_player_id"))]
                market_pool.sort(key=lambda x: float(x.get("vorp") or 0.0), reverse=True)
                market_pool = market_pool[:max(1, total_slots_remaining)]

                # Base price curve anchored to top VORP ~ 30, then calibrated to available cap
                top_v = float(market_pool[0].get("vorp") or 0.0) if market_pool else 0.0
                def _base_price(v: float) -> float:
                    if top_v <= 0:
                        return 0.0
                    return 30.0 * max(0.0, v) / top_v

                # Sum of positive VORP in market pool for reporting
                sum_vorp_pos = 0.0
                for r in market_pool:
                    try:
                        v = float(r.get("vorp") or 0.0)
                        if v > 0:
                            sum_vorp_pos += v
                    except Exception:
                        continue

                sum_base = sum(_base_price(float(r.get("vorp") or 0.0)) for r in market_pool)
                scale = (total_available_cap / sum_base) if sum_base > 0 else 0.0
                # For vorp_cap, allocate dollars linearly by VORP so totals match available cap
                if (source or "").lower() == "vorp_cap" and sum_vorp_pos > 0:
                    dollars_per_vorp = total_available_cap / sum_vorp_pos
                else:
                    dollars_per_vorp = ((30.0 / top_v) * scale) if top_v > 0 else 0.0

                def _clamp_price(x: float) -> int:
                    if x < 2:
                        return 2
                    if x > 30:
                        return 30
                    try:
                        return int(round(x))
                    except Exception:
                        return 2

                for r in results:
                    v = float(r.get("vorp") or 0.0)
                    if (source or "").lower() == "vorp_cap":
                        raw_price = v * dollars_per_vorp
                    else:
                        raw_price = _base_price(v) * scale
                    r["vorp_salary"] = _clamp_price(raw_price)

                results.sort(key=lambda x: float(x.get("vorp") or 0.0), reverse=True)
                start = local_offset
                end = start + local_limit
                items = results[start:end]

                return {
                    "season": season,
                    "count": len(items),
                    "results": items,
                    "league_id": league_id,
                    "replacement": {
                        "C": c_repl, "W": w_repl, "D": d_repl, "G": g_repl, "F": f_repl,
                        "teams": num_teams,
                        "market": {
                            "total_available_cap": float(total_available_cap),
                            "sum_vorp_positive": float(sum_vorp_pos),
                            "dollars_per_vorp": float(dollars_per_vorp),
                        }
                    },
                }

            if not is_avg:
                where = ["season = :season"]
                if source:
                    where.append("source = :source")
                    params["source"] = source
                if kind:
                    where.append("kind = :kind")
                    params["kind"] = kind
                where_sql = " AND ".join(where)
                sql = sa_text(
                    f"""
                    SELECT season, source, kind, nhl_player_id, player_name, position, team, metrics
                      FROM fantasy_player_projections
                     WHERE {where_sql}
                     ORDER BY player_name NULLS LAST, nhl_player_id
                     LIMIT :limit OFFSET :offset
                    """
                )
                rows = session.execute(sql, params).fetchall()
                items = [dict(r._mapping) for r in rows]
            else:
                # Load all rows for season (optionally filter by kind), compute FP per row, then average by player
                where = ["season = :season"]
                if kind:
                    where.append("kind = :kind")
                    params["kind"] = kind
                where_sql = " AND ".join(where)
                sql_all = sa_text(
                    f"""
                    SELECT season, source, kind, nhl_player_id, player_name, position, team, metrics
                      FROM fantasy_player_projections
                     WHERE {where_sql}
                    """
                )
                rows_all = session.execute(sql_all, params).fetchall()
                raw_items = [dict(r._mapping) for r in rows_all]
                # Compute FP for all, then aggregate
                def _norm_pos(p: str | None) -> str:
                    pp = (p or "").upper()
                    if pp in ("LW", "RW"): return "W"
                    return pp

                fp_per: list[dict[str, Any]] = []
                # Average-able metrics map: label -> aliases (normalized)
                TARGETS: dict[str, list[str]] = {
                    "Hits": ["hits"],
                    "Goals": ["goals", "g"],
                    "Points": ["points", "pts"],
                    "Assists": ["assists", "a"],
                    "PP_Points": ["powerplaypoints", "pppoints", "ppp"],
                    "Games_Played": ["gp", "gamesplayed", "games"],
                    "Blocked_Shots": ["blockedshots", "blocks", "blk"],
                    "Shots_on_Goal": ["shotsongoal", "shots", "sog"],
                    "Penalty_Minutes": ["penaltyminutes", "pim"],
                    "Time_on_Ice_Per_Game": ["toipergame", "avgtoi", "toigp", "toiper_gp"],
                    # Additional metrics needed for UHHP scoring
                    "Plus_Minus": ["plusminus", "pm"],
                    "Short_Handed_Goals": ["shorthandedgoals", "shg"],
                    "Saves": ["savesgoalie", "saves", "sv"],
                    "Wins": ["winsgoalie", "wins"],
                    "Goals_Against": ["goalsagainst", "ga", "goals_against"],
                }
                def _nkey(s: str) -> str:
                    return ''.join(ch for ch in (s or '').lower() if ch.isalnum())
                TARGETS_NORM = {k: [_nkey(a) for a in v] for k, v in TARGETS.items()}

                for it in raw_items:
                    try:
                        metrics = it.get("metrics") or {}
                        if isinstance(metrics, str):
                            import json as _json
                            metrics = _json.loads(metrics)
                    except Exception:
                        metrics = {}
                    # Build normalized metrics map
                    norm_metrics = {_nkey(k): v for k, v in (metrics or {}).items()}
                    # Compute per-row FP using rules
                    try:
                        fp = compute_fp(metrics)
                    except Exception:
                        fp = 0.0
                    row: dict[str, Any] = {
                        "nhl_player_id": it.get("nhl_player_id"),
                        "player_name": it.get("player_name"),
                        "position": _norm_pos(it.get("position")),
                        "team": it.get("team"),
                        "fantasy_points": float(fp),
                        "metrics": {},
                    }
                    # Pull target metrics for this row
                    for label, aliases in TARGETS_NORM.items():
                        val = None
                        for ak in aliases:
                            if ak in norm_metrics and norm_metrics[ak] is not None:
                                val = norm_metrics[ak]
                                break
                        # Derive Points if missing and G+A present
                        if val is None and label == "Points":
                            g = norm_metrics.get("goals") or norm_metrics.get("g")
                            a = norm_metrics.get("assists") or norm_metrics.get("a")
                            try:
                                if g is not None and a is not None:
                                    val = float(g) + float(a)
                            except Exception:
                                val = None
                        if val is not None:
                            try:
                                row["metrics"][label] = float(val)
                            except Exception:
                                pass
                    fp_per.append(row)

                # Group by id, fallback to name when id is null
                from collections import defaultdict, Counter
                by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for it in fp_per:
                    pid = it.get("nhl_player_id")
                    key = f"id:{int(pid)}" if pid not in (None, "", 0) else f"name:{(it.get('player_name') or '').strip().lower()}"
                    by_key[key].append(it)

                # Scoring for AVG using UHHP codes only
                def compute_fp_avg(m: Dict[str, Any], pos_str: str | None) -> float:
                    try:
                        g = float(m.get("Goals", 0) or 0)
                        a = float(m.get("Assists", 0) or 0)
                        pm = float(m.get("Plus_Minus", 0) or 0)
                        shg = float(m.get("Short_Handed_Goals", 0) or 0)
                        w = float(m.get("Wins", 0) or 0)
                        s = float(m.get("Saves", 0) or 0)
                        ga = float(m.get("Goals_Against", 0) or 0)
                        is_def = (str(pos_str or "").upper().startswith("D"))
                        # Apply total weights directly so DG totals 5 and DA totals 3 for defensemen
                        goal_weight = 5.0 if is_def else 3.0
                        assist_weight = 3.0 if is_def else 2.0
                        return (
                            0.25 * pm +
                            assist_weight * a +
                            goal_weight * g +
                            2.00 * shg +
                            2.00 * w +
                            0.20 * s +
                            (-1.25) * ga
                        )
                    except Exception:
                        return 0.0

                items_agg: list[dict[str, Any]] = []
                for key, group in by_key.items():
                    # average fp
                    total_fp = sum(float(x.get("fantasy_points") or 0.0) for x in group)
                    avg_fp = total_fp / max(1, len(group))
                    # choose canonical fields
                    nhl_id_vals = [g.get("nhl_player_id") for g in group if g.get("nhl_player_id")]
                    nhl_id = nhl_id_vals[0] if nhl_id_vals else None
                    name_vals = [str(g.get("player_name") or "") for g in group if (g.get("player_name") or "").strip()]
                    player_name = name_vals[0] if name_vals else None
                    pos_counts = Counter([str(g.get("position") or "").upper() for g in group if (g.get("position") or "")])
                    position = (pos_counts.most_common(1)[0][0] if pos_counts else "")
                    team_vals = [str(g.get("team") or "") for g in group if (g.get("team") or "").strip()]
                    team = team_vals[0] if team_vals else None
                    # Average target metrics across sources, ignoring missing
                    sums: dict[str, float] = {}
                    counts: dict[str, int] = {}
                    for g in group:
                        mm = g.get("metrics") or {}
                        if not isinstance(mm, dict):
                            continue
                        for label, val in mm.items():
                            try:
                                fv = float(val)
                            except Exception:
                                continue
                            sums[label] = sums.get(label, 0.0) + fv
                            counts[label] = counts.get(label, 0) + 1
                    metrics_avg: dict[str, float] = {}
                    for label in TARGETS.keys():
                        if counts.get(label, 0) > 0:
                            metrics_avg[label] = sums[label] / counts[label]
                    items_agg.append({
                        "season": int(season),
                        "source": "avg",
                        "kind": kind,
                        "nhl_player_id": nhl_id,
                        "player_name": player_name,
                        "position": position,
                        "team": team,
                        "metrics": metrics_avg,
                        # Score using UHHP weights against averaged metrics
                        "fantasy_points": float(compute_fp_avg(metrics_avg, position)),
                    })

                # Sort by FP desc, apply offset/limit
                items_agg.sort(key=lambda x: float(x.get("fantasy_points") or 0.0), reverse=True)
                start = local_offset
                end = start + local_limit
                items = items_agg[start:end]

            # Optional: compute fantasy points on the fly
            def _norm_key(s: str) -> str:
                return ''.join(ch for ch in s.lower() if ch.isalnum())

            def compute_fp(metrics: Dict[str, Any]) -> float:
                if not scoring_rules:
                    return 0.0
                total = 0.0
                norm_metrics = {_norm_key(k): v for k, v in (metrics or {}).items()}
                for rule in scoring_rules:
                    code = rule.get("code") or ""
                    name = rule.get("name") or ""
                    weight = float(rule.get("w") or 0.0)
                    v = None
                    if code:
                        v = metrics.get(code)
                        if v is None:
                            v = metrics.get(str(code).lower())
                    if v is None and name:
                        v = norm_metrics.get(_norm_key(str(name)))
                    if v is None:
                        alias_map = {
                            # Skaters
                            "G": ["goals", "g"],
                            "A": ["assists", "a"],
                            "SOG": ["shotsongoal", "shots", "sog"],
                            "PIM": ["penaltyminutes", "pim"],
                            "+/-": ["plusminus"],
                            "BLK": ["blockedshots", "blocks", "blk"],
                            "HIT": ["hits"],
                            "PPP": ["pppoints", "powerplaypoints", "ppp", "pp_points"],
                            "GP": ["gamesplayed", "gp", "games"],
                            "TOI": ["timeonicepergame", "toipergame", "avgtoi", "toigp", "toiper_gp"],
                            "SHG": ["shorthandedgoals", "shg"],
                            "DG": ["defensemangoals", "defencemangoals", "defenseman_goals", "dg"],
                            # Goalies
                            "W": ["winsgoalie", "wins"],
                            "SO": ["shutoutsgoalie", "shutouts"],
                            "SV": ["savesgoalie", "saves", "sv"],
                            "S": ["savesgoalie", "saves", "sv"],
                            "GA": ["goalsagainst", "ga", "goals_against"],
                        }
                        aliases = alias_map.get(str(code).upper(), [])
                        for ak in aliases:
                            v = norm_metrics.get(ak)
                            if v is not None:
                                break
                        # In avg mode, do NOT fall back to broad friendly labels to prevent overcounting
                        if v is None and not is_avg:
                            # Friendly labels from avg metrics
                            friendly = {
                                "hits": "hits",
                                "goals": "goals",
                                "points": "points",
                                "assists": "assists",
                                "pp_points": "pp_points",
                                "games_played": "games_played",
                                "blocked_shots": "blocked_shots",
                                "shots_on_goal": "shots_on_goal",
                                "penalty_minutes": "penalty_minutes",
                                "time_on_ice_per_game": "time_on_ice_per_game",
                            }
                            for fk in friendly.values():
                                v = norm_metrics.get(fk)
                                if v is not None:
                                    break
                    try:
                        total += (float(v) if v is not None else 0.0) * float(weight)
                    except Exception:
                        continue
                return total

            now_ts = datetime.now().timestamp()
            cache_key = None
            if league_id is not None and not is_avg:
                cache_key = f"proj:{season}:{league_id}:{source or '*'}:{kind or '*'}:{local_offset}:{local_limit}"
                entry = FP_CACHE.get(cache_key)
                if entry and (now_ts - entry.get("ts", 0)) <= FP_CACHE_TTL_SECONDS:
                    return entry["data"]

            if not is_avg:
                for it in items:
                    try:
                        metrics = it.get("metrics") or {}
                        if isinstance(metrics, str):
                            import json as _json
                            metrics = _json.loads(metrics)
                        it["fantasy_points"] = compute_fp(metrics)
                    except Exception:
                        it["fantasy_points"] = 0.0

            # Enrich with NHL birthdates when available so projections lists have correct birthdays
            try:
                ids: list[int] = []
                try:
                    ids = [int(it.get("nhl_player_id")) for it in items if it.get("nhl_player_id") is not None]
                except Exception:
                    ids = []
                if ids:
                    nhl_url = os.getenv("NHL_DATABASE_URL")
                    if nhl_url:
                        from sqlalchemy import create_engine as _create_engine  # type: ignore
                        engine = _create_engine(nhl_url, pool_pre_ping=True)
                        ids_csv = ",".join(str(i) for i in sorted(set(ids)))
                        sql_bd = sa_text(
                            f"""
                            SELECT p.id AS player_id, d.birth_date
                              FROM players p
                              LEFT JOIN player_details d ON d.player_id = p.id
                             WHERE p.id = ANY(string_to_array(:ids_csv, ',')::int[])
                            """
                        )
                        with engine.connect() as conn:
                            bd_rows = conn.execute(sql_bd, {"ids_csv": ids_csv}).fetchall()
                        bd_map = {int(r.player_id): (str(r.birth_date) if r.birth_date is not None else None) for r in bd_rows}
                        for it in items:
                            pid = it.get("nhl_player_id")
                            if pid is not None and it.get("birthdate") in (None, ""):
                                bd = bd_map.get(int(pid))
                                if bd:
                                    it["birthdate"] = bd
                        # Removed projections-only override per request
            except Exception as _e:
                logger.warning(f"Projections birthdate enrichment failed: {_e}")

            result = {"season": season, "count": len(items), "results": items, "league_id": league_id}
            if cache_key and not is_avg:
                FP_CACHE[cache_key] = {"ts": now_ts, "data": result}
            return result
    except Exception as e:
        logger.error(f"Read projections failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to read projections")


# User endpoints
@app.get("/api/user/profile")
async def get_user_profile(current_user: FantasyUser = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

@app.get("/api/user/leagues")
async def get_user_leagues(current_user: FantasyUser = Depends(get_current_user)):
    """Get all leagues for current user"""
    with get_fantasy_session() as session:
        memberships = session.query(FantasyUserLeague).filter(
            FantasyUserLeague.user_id == current_user.id
        ).all()
        
        leagues = []
        for membership in memberships:
            league = session.query(FantasyLeague).filter(
                FantasyLeague.id == membership.league_id
            ).first()
            
            if league:
                leagues.append({
                    "league_id": league.id,
                    "league_name": league.name,
                    "league_code": league.league_id,
                    "sport": league.sport,
                    "role": membership.role,
                    "permissions": {
                        "can_view_rosters": membership.can_view_rosters,
                        "can_make_transactions": membership.can_make_transactions,
                        "can_trade": membership.can_trade,
                        "can_manage_league": membership.can_manage_league
                    },
                    "joined_at": membership.joined_at.isoformat()
                })
        
        return {"leagues": leagues}

# League endpoints
@app.get("/api/leagues/{league_id}")
async def get_league_details(
    league_id: int,
    current_user: FantasyUser = Depends(get_current_user)
):
    """Get league details"""
    with get_fantasy_session() as session:
        # Check if user has access to this league
        membership = session.query(FantasyUserLeague).filter(
            FantasyUserLeague.user_id == current_user.id,
            FantasyUserLeague.league_id == league_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this league"
            )
        
        league = session.query(FantasyLeague).filter(
            FantasyLeague.id == league_id
        ).first()
        
        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found"
            )
        
        # Get teams in league
        teams = session.query(FantasyTeam).filter(
            FantasyTeam.league_id == league_id
        ).all()
        
        return {
            "league": {
                "id": league.id,
                "name": league.name,
                "league_id": league.league_id,
                "sport": league.sport,
                "platform": league.platform,
                "scoring_system": league.scoring_system,
                "draft_type": league.draft_type,
                "draft_rounds": league.draft_rounds,
                "trade_deadline": league.trade_deadline.isoformat() if league.trade_deadline else None,
                "created_at": league.created_at.isoformat()
            },
            "teams": [
                {
                    "id": team.id,
                    "team_name": team.team_name,
                    "owner_name": team.owner_name,
                    "current_rank": team.current_rank,
                    "wins": team.wins,
                    "losses": team.losses,
                    "ties": team.ties,
                    "total_points": team.total_points,
                    "is_active": team.is_active
                } for team in teams
            ],
            "user_role": membership.role,
            "permissions": {
                "can_view_rosters": membership.can_view_rosters,
                "can_make_transactions": membership.can_make_transactions,
                "can_trade": membership.can_trade,
                "can_manage_league": membership.can_manage_league
            }
        }

@app.get("/api/leagues/{league_id}/teams")
async def get_league_teams(
    league_id: int,
    current_user: FantasyUser = Depends(get_current_user)
):
    """Get all teams in a league"""
    with get_fantasy_session() as session:
        # Check if user has access to this league
        membership = session.query(FantasyUserLeague).filter(
            FantasyUserLeague.user_id == current_user.id,
            FantasyUserLeague.league_id == league_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this league"
            )
        
        teams = session.query(FantasyTeam).filter(
            FantasyTeam.league_id == league_id
        ).all()
        
        return {
            "teams": [
                {
                    "id": team.id,
                    "team_name": team.team_name,
                    "owner_name": team.owner_name,
                    "current_rank": team.current_rank,
                    "wins": team.wins,
                    "losses": team.losses,
                    "ties": team.ties,
                    "total_points": team.total_points,
                    "logo_url": team.logo_url,
                    "is_active": team.is_active
                } for team in teams
            ]
        }

# Public (unauthenticated) read-only endpoint for league teams
# Useful for development and non-sensitive displays. Consider securing before production use.
@app.get("/api/public/leagues/{league_id}/teams")
async def get_league_teams_public(league_id: int):
    """Get all teams in a league (public)."""
    with get_fantasy_session() as session:
        teams = session.query(FantasyTeam).filter(
            FantasyTeam.league_id == league_id
        ).all()

        return {
            "teams": [
                {
                    "id": team.id,
                    "team_name": team.team_name,
                    "owner_name": team.owner_name,
                    "current_rank": team.current_rank,
                    "wins": team.wins,
                    "losses": team.losses,
                    "ties": team.ties,
                    "total_points": team.total_points,
                    "logo_url": team.logo_url,
                    "is_active": team.is_active
                } for team in teams
            ]
        }

# --- CBS endpoints (public for now) ---

@app.get("/api/public/cbs/leagues", response_model=dict)
async def list_cbs_leagues() -> Dict[str, Any]:
    """List CBS leagues discovered/imported."""
    from sqlalchemy import text as sa_text
    # Use the fantasy session which should point to Railway FANTASY_DATABASE_URL
    with get_fantasy_session() as session:
        try:
            rows = session.execute(sa_text("SELECT id, provider_slug, name, domain, sport, season FROM cbs_leagues ORDER BY id"))
            leagues = [dict(r._mapping) for r in rows]
            return {"leagues": leagues}
        except Exception as e:
            logger.error(f"CBS leagues query failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read CBS leagues")


@app.get("/api/public/cbs/leagues/{league_id}/teams", response_model=dict)
async def list_cbs_league_teams(league_id: int) -> Dict[str, Any]:
    """Teams for a CBS league id (internal surrogate id)."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        try:
            rows = session.execute(sa_text(
                """
                SELECT t.*
                  FROM cbs_teams t
                 WHERE t.league_id = :lid
                 ORDER BY t.team_name
                """
            ), {"lid": league_id})
            teams = [dict(r._mapping) for r in rows]
            return {"league_id": league_id, "teams": teams}
        except Exception as e:
            logger.error(f"CBS teams query failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read CBS teams")


@app.get("/api/public/cbs/league/{slug}/teams", response_model=dict)
async def list_cbs_league_teams_by_slug(slug: str) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        try:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            # Ensure GM creds table exists for safe LEFT JOIN
            try:
                session.execute(sa_text(
                    """
                    CREATE TABLE IF NOT EXISTS cbs_gm_credentials (
                      league_id INT NOT NULL,
                      team_id INT NOT NULL,
                      login TEXT,
                      password_hash TEXT,
                      salt TEXT,
                      is_admin BOOLEAN DEFAULT FALSE,
                      PRIMARY KEY (league_id, team_id)
                    )
                    """
                ))
            except Exception:
                pass
            rows = session.execute(sa_text(
                """
                SELECT t.*,
                       g.login,
                       g.is_admin,
                       mem.user_email AS attached_email,
                       mem.role       AS attached_role
                  FROM cbs_teams t
                  LEFT JOIN cbs_gm_credentials g
                         ON g.league_id = t.league_id
                        AND g.team_id::text = t.team_id::text
                  LEFT JOIN LATERAL (
                       SELECT user_email, role
                         FROM cbs_user_memberships m
                        WHERE m.league_id = t.league_id
                          AND m.team_id::text = t.team_id::text
                        ORDER BY m.created_at DESC
                        LIMIT 1
                  ) mem ON TRUE
                 WHERE t.league_id = :lid
                 ORDER BY t.team_name
                """
            ), {"lid": league_id})
            teams = [dict(r._mapping) for r in rows]
            return {"league_id": league_id, "slug": slug, "teams": teams}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CBS teams by slug failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read CBS teams")


@app.get("/api/public/cbs/league/{slug}/gm_credentials", response_model=dict)
async def get_cbs_gm_credentials(slug: str) -> Dict[str, Any]:
    """Return GM login/admin settings per team for the league."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        try:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            session.execute(sa_text(
                """
                CREATE TABLE IF NOT EXISTS cbs_gm_credentials (
                  league_id INT NOT NULL,
                  team_id INT NOT NULL,
                  login TEXT,
                  password_hash TEXT,
                  salt TEXT,
                  is_admin BOOLEAN DEFAULT FALSE,
                  PRIMARY KEY (league_id, team_id)
                )
                """
            ))
            rows = session.execute(sa_text(
                "SELECT team_id, login, is_admin FROM cbs_gm_credentials WHERE league_id = :lid ORDER BY team_id"
            ), {"lid": league_id}).fetchall()
            return {"league_id": league_id, "slug": slug, "credentials": [dict(r._mapping) for r in rows]}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CBS gm_credentials read failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read GM credentials")


@app.post("/api/public/cbs/league/{slug}/gm_credentials", response_model=dict)
async def set_cbs_gm_credentials(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert GM login/password/admin for teams. If password omitted/blank, existing password remains."""
    from sqlalchemy import text as sa_text
    import os as _os, hashlib as _hash
    with get_fantasy_session() as session:
        try:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            session.execute(sa_text(
                """
                CREATE TABLE IF NOT EXISTS cbs_gm_credentials (
                  league_id INT NOT NULL,
                  team_id INT NOT NULL,
                  login TEXT,
                  password_hash TEXT,
                  salt TEXT,
                  is_admin BOOLEAN DEFAULT FALSE,
                  PRIMARY KEY (league_id, team_id)
                )
                """
            ))
            items = payload.get("creds") or []
            for it in items:
                try:
                    team_id = int(it.get("team_id"))
                except Exception:
                    continue
                login = (it.get("login") or None)
                is_admin = bool(it.get("is_admin") or False)
                password = (it.get("password") or "").strip()
                if password:
                    salt = _os.urandom(16).hex()
                    ph = _hash.sha256((salt + password).encode("utf-8")).hexdigest()
                    session.execute(sa_text(
                        """
                        INSERT INTO cbs_gm_credentials (league_id, team_id, login, password_hash, salt, is_admin)
                        VALUES (:lid, :tid, :login, :ph, :salt, :admin)
                        ON CONFLICT (league_id, team_id)
                        DO UPDATE SET login=EXCLUDED.login, password_hash=EXCLUDED.password_hash, salt=EXCLUDED.salt, is_admin=EXCLUDED.is_admin
                        """
                    ), {"lid": league_id, "tid": team_id, "login": login, "ph": ph, "salt": salt, "admin": is_admin})
                else:
                    session.execute(sa_text(
                        """
                        INSERT INTO cbs_gm_credentials (league_id, team_id, login, is_admin)
                        VALUES (:lid, :tid, :login, :admin)
                        ON CONFLICT (league_id, team_id)
                        DO UPDATE SET login=EXCLUDED.login, is_admin=EXCLUDED.is_admin
                        """
                    ), {"lid": league_id, "tid": team_id, "login": login, "admin": is_admin})
            session.commit()
            return {"ok": True}
        except HTTPException:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"CBS gm_credentials write failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to save GM credentials")
@app.get("/api/public/cbs/league/{slug}/state", response_model=dict)
async def get_cbs_league_state(slug: str) -> Dict[str, Any]:
    """Return league teams, roster limits, scoring rules, and A/I rosters with salary/years/NHL ids."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        try:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            # Teams
            team_rows = session.execute(sa_text(
                "SELECT team_id, team_name, abbrev, long_abbr, short_name, owner_id, logo_url FROM cbs_teams WHERE league_id=:lid ORDER BY team_name"
            ), {"lid": league_id}).fetchall()
            teams = [dict(r._mapping) for r in team_rows]
            # Rules
            rules_row = session.execute(sa_text(
                "SELECT scoring_mode, roster_positions FROM cbs_league_rules WHERE league_id=:lid"
            ), {"lid": league_id}).fetchone()
            rules = dict(rules_row._mapping) if rules_row else {}
            scoring_rows = session.execute(sa_text(
                "SELECT stat_code, stat_name, points, category FROM cbs_scoring_rules WHERE league_id=:lid"
            ), {"lid": league_id}).fetchall()
            scoring = [dict(r._mapping) for r in scoring_rows]
            # Rosters (A/I) with player names
            roster_rows = session.execute(sa_text(
                """
                SELECT r.team_id, r.cbs_player_id, r.nhl_player_id, r.slot_type, r.salary, r.years, r.roster_order,
                       p.full_name, p.pos_primary, p.nhl_team_abbr
                  FROM cbs_rosters r
                  LEFT JOIN cbs_players p ON p.cbs_player_id = r.cbs_player_id
                 WHERE r.league_id = :lid AND r.slot_type IN ('A','I')
                 ORDER BY r.team_id, r.slot_type DESC, r.roster_order
                """
            ), {"lid": league_id}).fetchall()
            rosters = [dict(r._mapping) for r in roster_rows]
            return {"league_id": league_id, "slug": slug, "teams": teams, "rules": rules, "scoring": scoring, "rosters": rosters}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CBS league state failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read CBS league state")


@app.get("/api/public/cbs/league/{slug}/draft_state", response_model=dict)
async def get_cbs_league_draft_state(slug: str, season: int = 2025) -> Dict[str, Any]:
    """Consolidated draft state for a CBS league slug.
    Returns: { league_id, slug, season, teams[], scoring_rules[], rosters[] with fantasy_points and RFA/UFA status }
    """
    from sqlalchemy import text as sa_text
    from datetime import date
    with get_fantasy_session() as session:
        try:
            lid_row = session.execute(sa_text("SELECT id, season FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            season_infer = int(getattr(lid_row, 'season', season) or season)

            team_rows = session.execute(sa_text(
                """
                SELECT t.team_id, t.team_name, t.abbrev, t.long_abbr, t.short_name, t.owner_id, t.logo_url, t.is_active,
                       COALESCE(s.total_salary, 0) AS total_salary,
                       COALESCE(s.total_players, 0) AS total_players
                  FROM cbs_teams t
                  LEFT JOIN (
                    SELECT team_id,
                           SUM(CASE WHEN slot_type='A' THEN COALESCE(salary,0) ELSE 0 END) AS total_salary,
                           COUNT(*) FILTER (WHERE slot_type IN ('A','I')) AS total_players
                      FROM cbs_rosters
                     WHERE league_id = :lid
                     GROUP BY team_id
                  ) s ON s.team_id = t.team_id
                 WHERE t.league_id = :lid
                 ORDER BY t.team_name
                """
            ), {"lid": league_id}).fetchall()
            teams = [dict(r._mapping) for r in team_rows]

            scoring_rows = session.execute(sa_text(
                "SELECT stat_code, stat_name, points FROM cbs_scoring_rules WHERE league_id = :lid"
            ), {"lid": league_id}).fetchall()
            scoring_rules = [
                {"code": str(r.stat_code), "name": (str(r.stat_name) if r.stat_name is not None else ""), "w": float(r.points)}
                for r in scoring_rows
            ]

            roster_rows = session.execute(sa_text(
                """
                SELECT r.team_id,
                       r.cbs_player_id,
                       r.nhl_player_id,
                       r.slot_type,
                       r.salary,
                       r.years,
                       r.rookie,
                       r.roster_order,
                       COALESCE(p.full_name, CAST(r.cbs_player_id AS TEXT), CAST(r.nhl_player_id AS TEXT)) AS player_name,
                       COALESCE(p.pos_primary, 'F') AS position,
                       p.birthdate AS birthdate,
                       p.nhl_team_abbr AS nhl_team_abbr
                  FROM cbs_rosters r
                  LEFT JOIN cbs_players p ON p.cbs_player_id = r.cbs_player_id
                 WHERE r.league_id = :lid AND r.slot_type IN ('A','I')
                 ORDER BY r.team_id, r.slot_type DESC, r.roster_order
                """
            ), {"lid": league_id}).fetchall()
            roster_items = [dict(r._mapping) for r in roster_rows]

            # Backfill birthdates from NHL DB when missing
            try:
                missing_ids = [int(r["nhl_player_id"]) for r in roster_items if r.get("nhl_player_id") is not None and not r.get("birthdate")]
                if missing_ids:
                    nhl_url = os.getenv("NHL_DATABASE_URL")
                    if nhl_url:
                        engine = create_engine(nhl_url, pool_pre_ping=True)
                    else:
                        from src.database.connection import connect_with_connector  # type: ignore
                        engine = connect_with_connector()
                    ids_csv = ",".join(str(i) for i in sorted(set(missing_ids)))
                    sql_bd = sa_text(
                        f"""
                        SELECT p.id AS player_id, d.birth_date
                          FROM players p
                          LEFT JOIN player_details d ON d.player_id = p.id
                         WHERE p.id = ANY(string_to_array(:ids_csv, ',')::int[])
                        """
                    )
                    with engine.connect() as conn:
                        bd_rows = conn.execute(sql_bd, {"ids_csv": ids_csv}).fetchall()
                    bd_map = {int(r.player_id): (str(r.birth_date) if r.birth_date is not None else None) for r in bd_rows}
                    for it in roster_items:
                        pid = it.get("nhl_player_id")
                        if pid is not None and not it.get("birthdate"):
                            bd = bd_map.get(int(pid))
                            if bd:
                                it["birthdate"] = bd
                        # Now that we know birthdate, compute status: UFA if age >=27 on July 1 of season; else RFA
                        try:
                            bstr = it.get("birthdate") or bd
                            if bstr:
                                parts = [int(x) for x in str(bstr).split('-')[:3]]
                                from datetime import date as _d
                                b_date = _d(parts[0], parts[1], parts[2]) if len(parts) == 3 else None
                                if b_date:
                                    from datetime import date as _date
                                    cutoff = _date(int(season), 7, 1)
                                    age = cutoff.year - b_date.year - (1 if (cutoff.month, cutoff.day) < (b_date.month, b_date.day) else 0)
                                    it["status"] = "UFA" if age >= 27 else "RFA"
                        except Exception:
                            pass
            except Exception as _e:
                logger.warning(f"Available birthdate enrichment failed: {_e}")

            # Ensure status is computed for ALL roster items from age rule (override any legacy CBS value)
            try:
                from datetime import date as _date
                cutoff = _date(int(season_infer), 7, 1)
                for it in roster_items:
                    bd = it.get("birthdate")
                    try:
                        # Rookie special-case: always RFA regardless of contract years
                        if bool(it.get("rookie")):
                            it["status"] = "RFA"
                            continue
                        if bd:
                            y, m, d = [int(x) for x in str(bd).split('-')[:3]]
                            bdate = _date(y, m, d)
                            age = cutoff.year - bdate.year - (1 if (cutoff.month, cutoff.day) < (bdate.month, bdate.day) else 0)
                            it["status"] = "UFA" if age >= 27 else "RFA"
                        else:
                            # Default to RFA when birthdate unknown
                            it.setdefault("status", "RFA")
                    except Exception:
                        it.setdefault("status", "RFA")
            except Exception:
                pass

            # Compute fantasy points per roster row using scoring_rules and projections
            nhl_ids = [int(r["nhl_player_id"]) for r in roster_items if r.get("nhl_player_id") is not None]
            proj_by_id: dict[int, Dict[str, Any]] = {}
            if nhl_ids:
                ids_csv = ",".join(str(i) for i in sorted(set(nhl_ids)))
                sql_proj = sa_text(
                    f"""
                    SELECT nhl_player_id, source, kind, metrics
                      FROM fantasy_player_projections
                     WHERE season = :season
                       AND nhl_player_id = ANY(string_to_array(:ids_csv, ',')::int[])
                    """
                )
                proj_rows = session.execute(sql_proj, {"season": int(season_infer), "ids_csv": ids_csv}).fetchall()
                for pr in proj_rows:
                    pid = int(pr.nhl_player_id)
                    src = (pr.source or "").lower()
                    existing = proj_by_id.get(pid)
                    if existing is None or ("cullen" in src and "cullen" not in (existing.get("source") or "").lower()):
                        proj_by_id[pid] = {"source": pr.source, "kind": pr.kind, "metrics": pr.metrics}

            def _norm_key(s: str) -> str:
                return ''.join(ch for ch in s.lower() if ch.isalnum())

            def compute_fp(metrics: Dict[str, Any]) -> float:
                if not scoring_rules:
                    return 0.0
                try:
                    if isinstance(metrics, str):
                        import json as _json
                        metrics = _json.loads(metrics)
                except Exception:
                    metrics = {}
                norm_metrics = {_norm_key(k): v for k, v in (metrics or {}).items()}
                total = 0.0
                for rule in scoring_rules:
                    code = rule.get("code") or ""
                    name = rule.get("name") or ""
                    weight = float(rule.get("w") or 0.0)
                    v = None
                    if code:
                        v = metrics.get(code)
                        if v is None:
                            v = metrics.get(str(code).lower())
                    if v is None and name:
                        v = norm_metrics.get(_norm_key(str(name)))
                    if v is None:
                        alias_map = {
                            # Skaters
                            "G": ["goals", "g"],
                            "A": ["assists", "a"],
                            "SOG": ["shotsongoal", "shots", "sog"],
                            "PIM": ["penaltyminutes", "pim"],
                            "+/-": ["plusminus"],
                            "BLK": ["blockedshots", "blocks", "blk"],
                            "HIT": ["hits"],
                            "PPP": ["pppoints", "powerplaypoints", "ppp", "pp_points"],
                            "GP": ["gamesplayed", "gp", "games"],
                            "TOI": ["timeonicepergame", "toipergame", "avgtoi", "toigp", "toiper_gp"],
                            # Goalies
                            "W": ["winsgoalie", "wins"],
                            "SO": ["shutoutsgoalie", "shutouts"],
                            "SV": ["savesgoalie", "saves", "sv"],
                            "GA": ["goalsagainst", "ga", "goals_against"],
                        }
                        aliases = alias_map.get(str(code).upper(), [])
                        for ak in aliases:
                            v = norm_metrics.get(ak)
                            if v is not None:
                                break
                        if v is None:
                            # Friendly labels from avg metrics
                            friendly = {
                                "hits": "hits",
                                "goals": "goals",
                                "points": "points",
                                "assists": "assists",
                                "pp_points": "pp_points",
                                "games_played": "games_played",
                                "blocked_shots": "blocked_shots",
                                "shots_on_goal": "shots_on_goal",
                                "penalty_minutes": "penalty_minutes",
                                "time_on_ice_per_game": "time_on_ice_per_game",
                            }
                            for fk in friendly.values():
                                v = norm_metrics.get(fk)
                                if v is not None:
                                    break
                    try:
                        total += (float(v) if v is not None else 0.0) * float(weight)
                    except Exception:
                        continue
                return total

            cutoff = date(season_infer, 7, 1)
            for r in roster_items:
                pid = r.get("nhl_player_id")
                fp = 0.0
                if isinstance(pid, (int,)):
                    proj = proj_by_id.get(int(pid))
                    if proj is not None:
                        fp = compute_fp(proj.get("metrics") or {})
                r["fantasy_points"] = fp
                # Do not overwrite status here; it has been set by rookie/age rule above

            # Projection sources for selector (distinct by season)
            try:
                ps_rows = session.execute(sa_text(
                    "SELECT DISTINCT source FROM fantasy_player_projections WHERE season = :season AND source IS NOT NULL ORDER BY source"
                ), {"season": int(season_infer)}).fetchall()
                def _label(s: str) -> str:
                    x = (s or "").replace("_", " ").strip()
                    return x[:1].upper() + x[1:] if x else s
                projection_sources = [{"slug": str(r.source), "display_name": _label(str(r.source)), "season_year": int(season_infer)} for r in ps_rows]
            except Exception:
                projection_sources = []

            return {"league_id": league_id, "slug": slug, "season": season_infer, "teams": teams, "scoring_rules": scoring_rules, "rosters": roster_items, "projection_sources": projection_sources}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CBS draft state failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read CBS draft state")
@app.get("/api/public/cbs/teams/{team_id}/roster", response_model=dict)
async def get_cbs_team_roster(team_id: str, draft_year: int | None = None) -> Dict[str, Any]:
    """Return a single team's roster with player names, slot type, salary, years, NHL id, and RFA/UFA status.

    RFA rule per UHH: If player's birthdate is after July 1 of draft_year, status = RFA, else UFA.
    If draft_year is not provided, infer from league season when available; otherwise default to 2025.
    """
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        try:
            row_team = session.execute(sa_text(
                "SELECT league_id, team_name FROM cbs_teams WHERE team_id = :tid LIMIT 1"
            ), {"tid": team_id}).fetchone()
            if not row_team:
                raise HTTPException(status_code=404, detail="Team not found")
            league_id = int(row_team.league_id)
            # Determine draft year cutoff
            inferred_year = None
            try:
                row_season = session.execute(sa_text(
                    "SELECT season FROM cbs_leagues WHERE id = :lid LIMIT 1"
                ), {"lid": league_id}).fetchone()
                if row_season and getattr(row_season, 'season', None):
                    inferred_year = int(row_season.season)
            except Exception:
                inferred_year = None
            use_year = int(draft_year) if draft_year is not None else (inferred_year if inferred_year else 2025)
            roster_rows = session.execute(sa_text(
                """
                SELECT r.team_id,
                       r.cbs_player_id,
                       r.nhl_player_id,
                       r.slot_type,
                       r.salary,
                       r.years,
                       r.roster_order,
                       COALESCE(p.full_name, CAST(r.cbs_player_id AS TEXT), CAST(r.nhl_player_id AS TEXT)) AS player_name,
                       COALESCE(p.pos_primary, 'F') AS position,
                       p.birthdate AS birthdate
                  FROM cbs_rosters r
                  LEFT JOIN cbs_players p ON p.cbs_player_id = r.cbs_player_id
                 WHERE r.league_id = :lid AND r.team_id = :tid AND r.slot_type IN ('A','I')
                 ORDER BY r.slot_type DESC, r.roster_order
                """
            ), {"lid": league_id, "tid": team_id}).fetchall()
            roster = []
            from datetime import date
            cutoff = date(use_year, 7, 1)
            for r in roster_rows:
                item = dict(r._mapping)
                b = item.get("birthdate")
                status = None
                try:
                    if b is not None:
                        # b may already be a date; if string, attempt parse YYYY-MM-DD
                        if isinstance(b, str):
                            parts = [int(x) for x in b.split("-")[:3]]
                            b_date = date(parts[0], parts[1], parts[2]) if len(parts) == 3 else None
                        else:
                            b_date = b
                        if b_date:
                            status = "RFA" if b_date > cutoff else "UFA"
                except Exception:
                    status = None
                item["status"] = status
                roster.append(item)

            return {"league_id": league_id, "team_id": team_id, "draft_year": use_year, "roster": roster}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CBS team roster failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to read team roster")


@app.post("/api/cbs/league/{slug}/attach", response_model=dict)
async def attach_user_to_league_team(slug: str, payload: Dict[str, Any], credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Attach current authenticated user to a CBS league/team.
    Body: { team_id: string }
    """
    from sqlalchemy import text as sa_text
    try:
        # Auth user
        auth_payload = kinde_auth.verify_token(credentials.credentials)
        user_subject = auth_payload.get("sub")
        user_email = auth_payload.get("email")
        if not user_subject:
            raise HTTPException(status_code=401, detail="Invalid auth user")
        team_id = str(payload.get("team_id") or '').strip()
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id is required")
        with get_fantasy_session() as session:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            # Validate team exists in league
            trow = session.execute(sa_text("SELECT 1 FROM cbs_teams WHERE league_id=:lid AND team_id=:tid"), {"lid": league_id, "tid": team_id}).fetchone()
            if not trow:
                raise HTTPException(status_code=404, detail="Team not found in league")
            # Upsert membership
            session.execute(sa_text(
                """
                INSERT INTO cbs_user_memberships(league_id, team_id, user_subject, user_email, role)
                VALUES (:lid, :tid, :sub, :email, 'member')
                ON CONFLICT (league_id, user_subject) DO UPDATE SET team_id=EXCLUDED.team_id, user_email=EXCLUDED.user_email
                """
            ), {"lid": league_id, "tid": team_id, "sub": user_subject, "email": user_email})
            return {"ok": True, "league_id": league_id, "team_id": team_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attach membership failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to attach membership")


@app.get("/api/cbs/league/{slug}/me", response_model=dict)
async def get_my_membership(slug: str, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Return current user's membership for this league."""
    from sqlalchemy import text as sa_text
    try:
        auth_payload = kinde_auth.verify_token(credentials.credentials)
        user_subject = auth_payload.get("sub")
        if not user_subject:
            raise HTTPException(status_code=401, detail="Invalid auth user")
        with get_fantasy_session() as session:
            lid_row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
            if not lid_row:
                raise HTTPException(status_code=404, detail="League not found")
            league_id = int(lid_row.id)
            row = session.execute(sa_text(
                "SELECT league_id, team_id, role FROM cbs_user_memberships WHERE league_id=:lid AND user_subject=:sub"
            ), {"lid": league_id, "sub": user_subject}).fetchone()
            if not row:
                return {"league_id": league_id, "team_id": None, "role": None}
            return dict(row._mapping)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read membership failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to read membership")
########## Auction Draft Endpoints ##########

def _get_league_id_by_slug(session, slug: str) -> int:
    from sqlalchemy import text as sa_text
    row = session.execute(sa_text("SELECT id FROM cbs_leagues WHERE provider_slug = :s LIMIT 1"), {"s": slug}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="League not found")
    return int(row.id)

@app.websocket("/ws/cbs/league/{slug}")
async def ws_league(slug: str, websocket: WebSocket):
    try:
        await ws_manager.connect(slug, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(slug, websocket)
    except Exception:
        ws_manager.disconnect(slug, websocket)

@app.get("/api/public/cbs/league/{slug}/auction/state", response_model=dict)
async def get_auction_state(slug: str) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        # Open auctions with top bid
        auctions = session.execute(sa_text(
            """
            SELECT a.id, a.league_id, a.nhl_player_id, a.cbs_player_id, a.nominated_by_team_id, a.status, a.started_at,
                   b.team_id AS top_team_id, b.amount AS top_amount
              FROM cbs_auctions a
              LEFT JOIN LATERAL (
                   SELECT team_id, amount
                     FROM cbs_auction_bids b
                    WHERE b.auction_id = a.id
                    ORDER BY amount DESC, created_at DESC
                    LIMIT 1
              ) b ON TRUE
             WHERE a.league_id = :lid AND a.status = 'open'
             ORDER BY a.started_at DESC
            """
        ), {"lid": lid}).fetchall()
        auctions_list = [dict(r._mapping) for r in auctions]

        # Enrich with player birthdates (always attach) using NHL DB
        try:
            nhl_ids = [int(a.get("nhl_player_id")) for a in auctions_list if a.get("nhl_player_id") is not None]
            if nhl_ids:
                try:
                    engine = _get_nhl_engine()
                except Exception as _e:
                    logger.warning(f"Available birthdate enrichment failed early: {_e}")
                    engine = None
                ids_csv = ",".join(str(i) for i in sorted(set(nhl_ids)))
                sql_bd = sa_text(
                    f"""
                    SELECT p.id AS player_id, d.birth_date
                      FROM players p
                      LEFT JOIN player_details d ON d.player_id = p.id
                     WHERE p.id = ANY(string_to_array(:ids_csv, ',')::int[])
                    """
                )
                bd_rows = []
                if engine is not None:
                    with engine.connect() as conn:
                        bd_rows = conn.execute(sql_bd, {"ids_csv": ids_csv}).fetchall()
                bd_map = {int(r.player_id): (str(r.birth_date) if r.birth_date is not None else None) for r in bd_rows}
                for a in auctions_list:
                    pid = a.get("nhl_player_id")
                    if pid is not None and not a.get("birthdate"):
                        bd = bd_map.get(int(pid))
                        if bd:
                            a["birthdate"] = bd
        except Exception as _e:
            logger.warning(f"Auction birthdate enrichment failed: {_e}")
        # Nomination order (persisted if available)
        try:
            session.execute(sa_text(
                """
                CREATE TABLE IF NOT EXISTS cbs_auction_order (
                  league_id INT NOT NULL,
                  pos INT NOT NULL,
                  team_id TEXT NOT NULL,
                  PRIMARY KEY (league_id, pos)
                )
                """
            ))
        except Exception:
            pass
        rows = session.execute(sa_text(
            "SELECT o.pos, o.team_id, t.team_name FROM cbs_auction_order o LEFT JOIN cbs_teams t ON t.team_id=o.team_id AND t.league_id=o.league_id WHERE o.league_id=:lid ORDER BY o.pos"
        ), {"lid": lid}).fetchall()
        if rows:
            order = [dict(r._mapping) for r in rows]
        else:
            teams = session.execute(sa_text(
                "SELECT team_id, team_name FROM cbs_teams WHERE league_id=:lid ORDER BY team_name"
            ), {"lid": lid}).fetchall()
            order = [dict(r._mapping) for r in teams]
        return {"league_id": lid, "open_auctions": auctions_list, "order": order}

@app.get("/api/public/cbs/league/{slug}/auction/history", response_model=dict)
async def get_auction_history(slug: str, limit: int = 50) -> Dict[str, Any]:
    """Recent closed auctions with winner team and amount."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        # Ensure optional winner columns exist on cbs_auctions
        try:
            session.execute(sa_text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winner_team_id'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winner_team_id TEXT;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winning_amount'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winning_amount NUMERIC;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='pick_num'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN pick_num INT;
                  END IF;
                END$$;
                """
            ))
        except Exception:
            pass
        rows = session.execute(sa_text(
            """
            SELECT a.id AS auction_id,
                   a.nhl_player_id,
                   a.cbs_player_id,
                   a.closed_at,
                   COALESCE(cp.full_name, fp.player_name) AS player_name,
                   COALESCE(cp.pos_primary, fp.position) AS position,
                   COALESCE(a.winner_team_id, w.team_id) AS winner_team_id,
                   t.team_name AS winner_team_name,
                   COALESCE(a.winning_amount, w.amount) AS winning_amount,
                   COALESCE(a.pick_num, w.pick_num) AS pick_num
              FROM cbs_auctions a
              LEFT JOIN LATERAL (
                   SELECT team_id, amount, pick_num
                     FROM cbs_auction_bids b
                    WHERE b.auction_id = a.id
                    ORDER BY amount DESC, created_at DESC
                    LIMIT 1
              ) w ON TRUE
              LEFT JOIN cbs_players cp ON cp.cbs_player_id = a.cbs_player_id
              LEFT JOIN fantasy_player_projections fp
                     ON fp.nhl_player_id = a.nhl_player_id AND fp.source = 'avg' AND fp.season = 2025
              LEFT JOIN cbs_teams t ON t.league_id = :lid AND t.team_id = COALESCE(a.winner_team_id, w.team_id)
             WHERE a.league_id = :lid AND a.status = 'closed'
             ORDER BY COALESCE(a.pick_num, w.pick_num) ASC NULLS LAST, a.closed_at ASC NULLS LAST, a.id ASC
             LIMIT :lim
            """
        ), {"lid": lid, "lim": max(1, min(200, int(limit)))}).fetchall()
        results = []
        # Attach full bid ledgers
        for r in rows:
            d = dict(r._mapping)
            aid = int(d.get("auction_id"))
            bids = session.execute(sa_text(
                """
                SELECT team_id, amount, kind, pick_num, created_at
                  FROM cbs_auction_bids
                 WHERE auction_id = :aid
                 ORDER BY created_at ASC
                """
            ), {"aid": aid}).fetchall()
            d["bids"] = [dict(b._mapping) for b in bids]
            results.append(d)
        return {"league_id": lid, "results": results}

@app.get("/api/public/cbs/league/{slug}/auction/order", response_model=dict)
async def get_auction_order(slug: str) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        try:
            session.execute(sa_text(
                """
                CREATE TABLE IF NOT EXISTS cbs_auction_order (
                  league_id INT NOT NULL,
                  pos INT NOT NULL,
                  team_id TEXT NOT NULL,
                  PRIMARY KEY (league_id, pos)
                )
                """
            ))
        except Exception:
            pass
        rows = session.execute(sa_text(
            "SELECT pos, team_id FROM cbs_auction_order WHERE league_id=:lid ORDER BY pos"
        ), {"lid": lid}).fetchall()
        return {"league_id": lid, "order": [dict(r._mapping) for r in rows]}

@app.post("/api/public/cbs/league/{slug}/auction/order", response_model=dict)
async def set_auction_order(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Persist pick order. Body: { order: [team_id1, team_id2, ...] }"""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        order_list = payload.get("order") or []
        if not isinstance(order_list, list) or not order_list:
            return {"ok": False, "error": "order array required"}
        # Ensure table exists
        session.execute(sa_text(
            """
            CREATE TABLE IF NOT EXISTS cbs_auction_order (
              league_id INT NOT NULL,
              pos INT NOT NULL,
              team_id TEXT NOT NULL,
              PRIMARY KEY (league_id, pos)
            )
            """
        ))
        # Replace existing order
        session.execute(sa_text("DELETE FROM cbs_auction_order WHERE league_id=:lid"), {"lid": lid})
        for idx, team_id in enumerate(order_list, start=1):
            session.execute(sa_text(
                "INSERT INTO cbs_auction_order(league_id, pos, team_id) VALUES(:lid, :pos, :tid)"
            ), {"lid": lid, "pos": idx, "tid": str(team_id)})
        try:
            await ws_manager.broadcast(slug, {"event": "order_updated"})
        except Exception:
            pass
        return {"ok": True, "count": len(order_list)}

# --- Cap hits persistence ---
@app.get("/api/public/cbs/league/{slug}/cap_hits", response_model=dict)
async def get_cap_hits(slug: str) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        # Ensure table exists
        session.execute(sa_text(
            """
            CREATE TABLE IF NOT EXISTS cbs_team_cap_hits (
              league_id INT NOT NULL,
              team_id TEXT NOT NULL,
              cap_hits NUMERIC NOT NULL DEFAULT 0,
              PRIMARY KEY (league_id, team_id)
            )
            """
        ))
        rows = session.execute(sa_text(
            "SELECT team_id, cap_hits FROM cbs_team_cap_hits WHERE league_id=:lid"
        ), {"lid": lid}).fetchall()
        return {"league_id": lid, "cap_hits": [dict(r._mapping) for r in rows]}

@app.post("/api/public/cbs/league/{slug}/cap_hits", response_model=dict)
async def set_cap_hits(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        team_id = str(payload.get("team_id") or '')
        cap_hits = float(payload.get("cap_hits") or 0)
        if not team_id:
            return {"ok": False, "error": "team_id required"}
        session.execute(sa_text(
            """
            CREATE TABLE IF NOT EXISTS cbs_team_cap_hits (
              league_id INT NOT NULL,
              team_id TEXT NOT NULL,
              cap_hits NUMERIC NOT NULL DEFAULT 0,
              PRIMARY KEY (league_id, team_id)
            )
            """
        ))
        session.execute(sa_text(
            "INSERT INTO cbs_team_cap_hits(league_id, team_id, cap_hits) VALUES(:lid, :tid, :ch)\n             ON CONFLICT (league_id, team_id) DO UPDATE SET cap_hits=EXCLUDED.cap_hits"
        ), {"lid": lid, "tid": team_id, "ch": cap_hits})
        return {"ok": True}

@app.get("/api/public/cbs/league/{slug}/auction/available", response_model=dict)
async def get_auction_available(slug: str, season: int = 2025, limit: int = 200) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    from datetime import date
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        # Determine cutoff for RFA/UFA
        cutoff = date(int(season), 7, 1)
        # Players available: anyone in league rosters that does NOT have contract years in (1,2,3)
        # We also include players not on any roster in this league (unowned) from projections as UFAs/RFAs by age
        # Part 1: roster-held rights (years NULL or NOT IN 1,2,3)
        rows_rights = session.execute(sa_text(
            """
            SELECT r.team_id,
                   COALESCE(r.nhl_player_id, m.nhl_player_id) AS nhl_player_id,
                   r.cbs_player_id,
                   r.years,
                   COALESCE(p.full_name, CAST(r.cbs_player_id AS TEXT), CAST(r.nhl_player_id AS TEXT)) AS player_name,
                   COALESCE(p.pos_primary, 'F') AS position,
                   p.birthdate
              FROM cbs_rosters r
              LEFT JOIN cbs_players p ON p.cbs_player_id = r.cbs_player_id
              LEFT JOIN cbs_player_map m ON m.cbs_player_id = r.cbs_player_id
             WHERE r.league_id = :lid
               AND r.slot_type IN ('A','I')
               AND (r.years IS NULL OR r.years NOT IN (1,2,3))
             ORDER BY r.team_id, r.roster_order
             LIMIT :limit
            """
        ), {"lid": lid, "limit": max(1, min(1000, int(limit)))}).fetchall()

        rights_items = []
        for r in rows_rights:
            it = dict(r._mapping)
            it["controlling_team_id"] = str(getattr(r, 'team_id', '')) if getattr(r, 'team_id', None) is not None else None
            rights_items.append(it)

        # Compute age-based status for rights-held players: UFA if age >=27 on July 1 of season; else RFA
        try:
            need_bd = [int(it.get("nhl_player_id")) for it in rights_items if it.get("nhl_player_id") is not None and not it.get("birthdate")]
            if need_bd:
                try:
                    engine = _get_nhl_engine()
                except Exception as _e:
                    logger.warning(f"Projections birthdate enrichment failed early: {_e}")
                    engine = None
                ids_csv = ",".join(str(i) for i in sorted(set(need_bd)))
                sql_bd = sa_text(
                    f"""
                    SELECT p.id AS player_id, d.birth_date
                      FROM players p
                      LEFT JOIN player_details d ON d.player_id = p.id
                     WHERE p.id = ANY(string_to_array(:ids_csv, ',')::int[])
                    """
                )
                bd_rows = []
                if engine is not None:
                    with engine.connect() as conn:
                        bd_rows = conn.execute(sql_bd, {"ids_csv": ids_csv}).fetchall()
                bd_map = {int(r.player_id): (str(r.birth_date) if r.birth_date is not None else None) for r in bd_rows}
                for it in rights_items:
                    if it.get("nhl_player_id") is not None and not it.get("birthdate"):
                        bd = bd_map.get(int(it.get("nhl_player_id")))
                        if bd:
                            it["birthdate"] = bd
            from datetime import date as _date
            cutoff = _date(int(season), 7, 1)
            for it in rights_items:
                try:
                    bd = it.get("birthdate")
                    if bd:
                        y, m, d = [int(x) for x in str(bd).split('-')[:3]]
                        bdate = _date(y, m, d)
                        age = cutoff.year - bdate.year - (1 if (cutoff.month, cutoff.day) < (bdate.month, bdate.day) else 0)
                        it["status"] = "UFA" if age >= 27 else "RFA"
                    else:
                        it.setdefault("status", "RFA")
                except Exception:
                    it.setdefault("status", "RFA")
        except Exception as _e:
            logger.warning(f"Rights birthdate/status computation failed: {_e}")

        # Part 2: completely unrostered players from projections (season) minus any player who appears in league rosters at all
        rows_unrostered = session.execute(sa_text(
            """
            WITH any_in_roster AS (
              SELECT DISTINCT COALESCE(r.nhl_player_id, m.nhl_player_id) AS nhl_player_id
                FROM cbs_rosters r
                LEFT JOIN cbs_player_map m ON m.cbs_player_id = r.cbs_player_id
               WHERE r.league_id = :lid
            )
            SELECT p.nhl_player_id, p.player_name, p.position, p.team
              FROM fantasy_player_projections p
              LEFT JOIN any_in_roster ar ON ar.nhl_player_id = p.nhl_player_id
             WHERE p.season = :season AND ar.nhl_player_id IS NULL
             ORDER BY p.player_name NULLS LAST
             LIMIT :limit
            """
        ), {"lid": lid, "season": int(season), "limit": max(1, min(1000, int(limit)))}).fetchall()

        unrostered_items = []
        for r in rows_unrostered:
            it = dict(r._mapping)
            # Not on any roster → UFA by default
            it["status"] = "UFA"
            it["controlling_team_id"] = None
            it["birthdate"] = None
            unrostered_items.append(it)

        # Enrich unrostered players with birthdates from NHL DB so every player has birthdate
        try:
            nhl_ids = [int(it.get("nhl_player_id")) for it in unrostered_items if it.get("nhl_player_id") is not None]
            if nhl_ids:
                nhl_url = os.getenv("NHL_DATABASE_URL")
                if nhl_url:
                    engine = create_engine(nhl_url, pool_pre_ping=True)
                else:
                    from src.database.connection import connect_with_connector  # type: ignore
                    engine = connect_with_connector()
                ids_csv = ",".join(str(i) for i in sorted(set(nhl_ids)))
                sql_bd = sa_text(
                    f"""
                    SELECT p.id AS player_id, d.birth_date
                      FROM players p
                      LEFT JOIN player_details d ON d.player_id = p.id
                     WHERE p.id = ANY(string_to_array(:ids_csv, ',')::int[])
                    """
                )
                bd_rows = []
                if engine is not None:
                    with engine.connect() as conn:
                        bd_rows = conn.execute(sql_bd, {"ids_csv": ids_csv}).fetchall()
                bd_map = {int(r.player_id): (str(r.birth_date) if r.birth_date is not None else None) for r in bd_rows}
                for it in unrostered_items:
                    pid = it.get("nhl_player_id")
                    if pid is not None and not it.get("birthdate"):
                        bd = bd_map.get(int(pid))
                        if bd:
                            it["birthdate"] = bd
                        # Now that we know birthdate, compute status: UFA if age >=27 on July 1 of season; else RFA
                        try:
                            if bd:
                                parts = [int(x) for x in str(bd).split('-')[:3]]
                                from datetime import date as _d
                                b_date = _d(parts[0], parts[1], parts[2]) if len(parts) == 3 else None
                                if b_date:
                                    from datetime import date as _date
                                    cutoff = _date(int(season), 7, 1)
                                    age = cutoff.year - b_date.year - (1 if (cutoff.month, cutoff.day) < (b_date.month, b_date.day) else 0)
                                    it["status"] = "UFA" if age >= 27 else "RFA"
                        except Exception:
                            pass
        except Exception as _e:
            logger.warning(f"Available birthdate enrichment failed: {_e}")

        # Final pass: enforce age-based status for ALL unrostered items
        try:
            from datetime import date as _date
            cutoff = _date(int(season), 7, 1)
            for it in unrostered_items:
                try:
                    bd = it.get("birthdate")
                    if bd:
                        y, m, d = [int(x) for x in str(bd).split('-')[:3]]
                        bdate = _date(y, m, d)
                        age = cutoff.year - bdate.year - (1 if (cutoff.month, cutoff.day) < (bdate.month, bdate.day) else 0)
                        it["status"] = "UFA" if age >= 27 else "RFA"
                    else:
                        it["status"] = "RFA"
                except Exception:
                    it["status"] = "RFA"
        except Exception:
            pass

        items = rights_items + unrostered_items
        return {"league_id": lid, "season": season, "available": items}

@app.post("/api/public/cbs/league/{slug}/auction/nominate", response_model=dict)
async def post_auction_nominate(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        nhl_player_id = int(payload.get("nhl_player_id"))
        cbs_player_id = (payload.get("cbs_player_id") or None)
        team_id = str(payload.get("team_id") or '')
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id required")
        # Ensure not already rostered
        already = session.execute(sa_text(
            "SELECT 1 FROM cbs_rosters WHERE league_id=:lid AND (nhl_player_id=:pid OR cbs_player_id=:cid) LIMIT 1"
        ), {"lid": lid, "pid": nhl_player_id, "cid": cbs_player_id}).fetchone()
        if already:
            raise HTTPException(status_code=409, detail="Player already rostered")
        # Upsert auction
        row = session.execute(sa_text(
            """
            INSERT INTO cbs_auctions(league_id, nhl_player_id, cbs_player_id, nominated_by_team_id, status)
            VALUES(:lid, :pid, :cid, :tid, 'open')
            ON CONFLICT (league_id, nhl_player_id) DO UPDATE SET cbs_player_id = COALESCE(cbs_auctions.cbs_player_id, EXCLUDED.cbs_player_id), nominated_by_team_id = EXCLUDED.nominated_by_team_id, status='open', started_at=NOW()
            RETURNING id
            """
        ), {"lid": lid, "pid": nhl_player_id, "cid": cbs_player_id, "tid": team_id}).fetchone()
        try:
            await ws_manager.broadcast(slug, {"event": "auction_nominated", "auction_id": int(row.id), "nhl_player_id": nhl_player_id, "team_id": team_id})
        except Exception:
            pass
        return {"ok": True, "auction_id": int(row.id)}

@app.post("/api/public/cbs/league/{slug}/auction/bid", response_model=dict)
async def post_auction_bid(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        team_id = str(payload.get("team_id") or '')
        amount = float(payload.get("amount"))
        is_rebid = bool(payload.get("rebid") or payload.get("tiebreak"))
        # Validate auction open
        st = session.execute(sa_text("SELECT status FROM cbs_auctions WHERE id=:id AND league_id=:lid"), {"id": auction_id, "lid": lid}).fetchone()
        if not st or st.status != 'open':
            raise HTTPException(status_code=400, detail="Auction not open")
        # Allow multiple bids from the same team; mark kind accordingly
        # Ensure optional columns exist for kind and pick number
        try:
            session.execute(sa_text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auction_bids' AND column_name='kind'
                  ) THEN
                    ALTER TABLE cbs_auction_bids ADD COLUMN kind TEXT;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auction_bids' AND column_name='pick_num'
                  ) THEN
                    ALTER TABLE cbs_auction_bids ADD COLUMN pick_num INT;
                  END IF;
                END$$;
                """
            ))
        except Exception:
            pass
        # Compute pick number as (closed auctions count + 1) within league
        pick_row = session.execute(sa_text(
            "SELECT COUNT(*) AS c FROM cbs_auctions WHERE league_id=:lid AND status='closed'"
        ), {"lid": lid}).fetchone()
        pick_num = int(getattr(pick_row, 'c', 0) or 0) + 1
        session.execute(sa_text(
            "INSERT INTO cbs_auction_bids(auction_id, team_id, amount, kind, pick_num) VALUES(:aid, :tid, :amt, :kind, :p)"
        ), {"aid": auction_id, "tid": team_id, "amt": amount, "kind": ('tiebreak' if is_rebid else 'initial'), "p": pick_num})
        # Return top bid
        top = session.execute(sa_text(
            "SELECT team_id, amount FROM cbs_auction_bids WHERE auction_id=:aid ORDER BY amount DESC, created_at DESC LIMIT 1"
        ), {"aid": auction_id}).fetchone()
        try:
            await ws_manager.broadcast(slug, {"event": "bid_placed", "auction_id": auction_id, "top_bid": dict(top._mapping) if top else None})
        except Exception:
            pass
        return {"ok": True, "top_bid": dict(top._mapping) if top else None}

@app.post("/api/public/cbs/league/{slug}/auction/finalize", response_model=dict)
async def post_auction_finalize(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        # Top bid
        top = session.execute(sa_text(
            "SELECT b.team_id, b.amount, a.nhl_player_id, a.cbs_player_id FROM cbs_auction_bids b JOIN cbs_auctions a ON a.id=b.auction_id WHERE b.auction_id=:aid ORDER BY b.amount DESC, b.created_at DESC LIMIT 1"
        ), {"aid": auction_id}).fetchone()
        if not top:
            # Close without winner
            session.execute(sa_text("UPDATE cbs_auctions SET status='closed', closed_at=NOW() WHERE id=:id AND league_id=:lid"), {"id": auction_id, "lid": lid})
            return {"ok": True, "winner": None}
        team_id = str(top.team_id)
        amount = float(top.amount)
        nhl_pid = int(top.nhl_player_id)
        cbs_pid = (top.cbs_player_id or None)
        # Assign sequential pick number based on already closed auctions
        pick_row = session.execute(sa_text(
            "SELECT COALESCE(MAX(pick_num), 0) AS max_pick FROM cbs_auctions WHERE league_id=:lid AND status='closed'"
        ), {"lid": lid}).fetchone()
        winner_pick = int(getattr(pick_row, 'max_pick', 0) or 0) + 1
        # Ensure columns exist on cbs_auctions to record outcome
        try:
            session.execute(sa_text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winner_team_id'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winner_team_id TEXT;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winning_amount'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winning_amount NUMERIC;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='pick_num'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN pick_num INT;
                  END IF;
                END$$;
                """
            ))
        except Exception:
            pass
        # Close auction
        session.execute(sa_text(
            "UPDATE cbs_auctions SET status='closed', closed_at=NOW(), winner_team_id=:tid, winning_amount=:amt, pick_num=:p WHERE id=:id AND league_id=:lid"
        ), {"id": auction_id, "lid": lid, "tid": team_id, "amt": amount, "p": winner_pick})
        # Insert roster entry (3-year contract per rules). cbs_player_id is required by schema.
        # If we lack CBS id, create a placeholder CBS player row so FK is satisfied.
        if cbs_pid is None:
            # Try to derive a CBS player id for the NHL id, otherwise synthesize
            row = session.execute(sa_text(
                "SELECT cbs_player_id FROM cbs_player_map WHERE nhl_player_id=:pid LIMIT 1"), {"pid": nhl_pid}
            ).fetchone()
            if row and getattr(row, 'cbs_player_id', None):
                cbs_pid = str(row.cbs_player_id)
            else:
                cbs_pid = f"nhl-{nhl_pid}"
                try:
                    # Ensure placeholder exists in cbs_players
                    session.execute(sa_text(
                        """
                        INSERT INTO cbs_players(cbs_player_id, full_name, pos_primary)
                        VALUES(:cid, 'Unknown', 'F')
                        ON CONFLICT (cbs_player_id) DO NOTHING
                        """
                    ), {"cid": cbs_pid})
                except Exception:
                    pass
        session.execute(sa_text(
            """
            INSERT INTO cbs_rosters(league_id, team_id, season, cbs_player_id, nhl_player_id, slot_type, status, salary, years, effective_from)
            VALUES(:lid, :tid, NULL, :cid, :pid, 'A', 'signed', :sal, 3, NOW())
            """
        ), {"lid": lid, "tid": team_id, "cid": cbs_pid, "pid": nhl_pid, "sal": amount})
        # Persist pick number on all bids for this auction for consistency
        try:
            session.execute(sa_text(
                "UPDATE cbs_auction_bids SET pick_num=:p WHERE auction_id=:aid"
            ), {"p": winner_pick, "aid": auction_id})
        except Exception:
            pass
        # Enrich winner response with player name/position and full bid ledger
        info = session.execute(sa_text(
            """
            SELECT COALESCE(cp.full_name, fp.player_name) AS player_name,
                   COALESCE(cp.pos_primary, fp.position) AS position
              FROM cbs_auctions a
              LEFT JOIN cbs_players cp ON cp.cbs_player_id = a.cbs_player_id
              LEFT JOIN fantasy_player_projections fp
                     ON fp.nhl_player_id = a.nhl_player_id AND fp.source='avg' AND fp.season=2025
             WHERE a.id = :aid
            """
        ), {"aid": auction_id}).fetchone()
        bids = session.execute(sa_text(
            "SELECT team_id, amount, kind, pick_num, created_at FROM cbs_auction_bids WHERE auction_id=:aid ORDER BY created_at ASC"
        ), {"aid": auction_id}).fetchall()
        try:
            await ws_manager.broadcast(slug, {"event": "auction_finalized", "auction_id": auction_id, "team_id": team_id, "amount": amount, "nhl_player_id": nhl_pid})
        except Exception:
            pass
        return {
            "ok": True,
            "winner": {
                "team_id": team_id,
                "amount": amount,
                "nhl_player_id": nhl_pid,
                "pick_num": winner_pick,
                "player_name": (getattr(info, 'player_name', None) if info else None),
                "position": (getattr(info, 'position', None) if info else None),
            },
            "bids": [dict(b._mapping) for b in bids],
        }

@app.post("/api/public/cbs/league/{slug}/auction/match", response_model=dict)
async def post_auction_match(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """RFA match: assign the player to the controlling team at the top bid amount.
    Body: { auction_id, team_id }
    - Validates auction is open and that the controlling team has rights (years IS NULL or NOT IN (1,2,3))
    - Closes the auction and updates (or inserts) a signed roster row for the controlling team
    """
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        team_id = str(payload.get("team_id") or '')
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id required")
        # Validate auction open and get top bid + player ids
        st = session.execute(sa_text(
            "SELECT status FROM cbs_auctions WHERE id=:id AND league_id=:lid"), {"id": auction_id, "lid": lid}
        ).fetchone()
        if not st or st.status != 'open':
            raise HTTPException(status_code=400, detail="Auction not open")
        top = session.execute(sa_text(
            """
            SELECT b.team_id, b.amount, a.nhl_player_id, a.cbs_player_id
              FROM cbs_auction_bids b
              JOIN cbs_auctions a ON a.id=b.auction_id
             WHERE b.auction_id=:aid
             ORDER BY b.amount DESC, b.created_at DESC
             LIMIT 1
            """
        ), {"aid": auction_id}).fetchone()
        if not top:
            raise HTTPException(status_code=400, detail="No bids to match")
        amount = float(top.amount)
        nhl_pid = int(top.nhl_player_id) if top.nhl_player_id is not None else None
        cbs_pid = (top.cbs_player_id or None)
        # Validate controlling rights (years IS NULL OR NOT IN 1,2,3)
        rights = session.execute(sa_text(
            """
            SELECT 1
              FROM cbs_rosters r
             WHERE r.league_id=:lid AND r.team_id=:tid
               AND (r.nhl_player_id = :pid OR (r.cbs_player_id = :cid))
               AND r.slot_type IN ('A','I')
               AND (r.years IS NULL OR r.years NOT IN (1,2,3))
             LIMIT 1
            """
        ), {"lid": lid, "tid": team_id, "pid": nhl_pid, "cid": cbs_pid}).fetchone()
        if not rights:
            raise HTTPException(status_code=403, detail="Match not allowed: no RFA rights for team")
        # Assign sequential pick number based on already closed auctions
        pick_row = session.execute(sa_text(
            "SELECT COALESCE(MAX(pick_num), 0) AS max_pick FROM cbs_auctions WHERE league_id=:lid AND status='closed'"
        ), {"lid": lid}).fetchone()
        winner_pick = int(getattr(pick_row, 'max_pick', 0) or 0) + 1
        # Ensure columns exist on cbs_auctions to record outcome
        try:
            session.execute(sa_text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winner_team_id'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winner_team_id TEXT;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='winning_amount'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN winning_amount NUMERIC;
                  END IF;
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='cbs_auctions' AND column_name='pick_num'
                  ) THEN
                    ALTER TABLE cbs_auctions ADD COLUMN pick_num INT;
                  END IF;
                END$$;
                """
            ))
        except Exception:
            pass
        # Close auction and record outcome
        session.execute(sa_text(
            "UPDATE cbs_auctions SET status='closed', closed_at=NOW(), winner_team_id=:tid, winning_amount=:amt, pick_num=:p WHERE id=:id AND league_id=:lid"
        ), {"id": auction_id, "lid": lid, "tid": team_id, "amt": amount, "p": winner_pick})
        # Try to update existing rights row into a signed contract
        updated = session.execute(sa_text(
            """
            UPDATE cbs_rosters
               SET status='signed', salary=:sal, years=3, effective_from=NOW(), slot_type='A'
             WHERE league_id=:lid AND team_id=:tid
               AND (nhl_player_id=:pid OR (cbs_player_id=:cid))
               AND slot_type IN ('A','I')
               AND (years IS NULL OR years NOT IN (1,2,3))
            """
        ), {"lid": lid, "tid": team_id, "pid": nhl_pid, "cid": cbs_pid, "sal": amount}).rowcount
        if updated == 0:
            # Insert if no placeholder rights row existed
            session.execute(sa_text(
                """
                INSERT INTO cbs_rosters(league_id, team_id, season, cbs_player_id, nhl_player_id, slot_type, status, salary, years, effective_from)
                VALUES(:lid, :tid, NULL, :cid, :pid, 'A', 'signed', :sal, 3, NOW())
                """
            ), {"lid": lid, "tid": team_id, "cid": cbs_pid, "pid": nhl_pid, "sal": amount})
        # Persist pick number on all bids for this auction for consistency
        try:
            session.execute(sa_text(
                "UPDATE cbs_auction_bids SET pick_num=:p WHERE auction_id=:aid"
            ), {"p": winner_pick, "aid": auction_id})
        except Exception:
            pass
        # Enrich response
        info = session.execute(sa_text(
            """
            SELECT COALESCE(cp.full_name, fp.player_name) AS player_name,
                   COALESCE(cp.pos_primary, fp.position) AS position
              FROM cbs_auctions a
              LEFT JOIN cbs_players cp ON cp.cbs_player_id = a.cbs_player_id
              LEFT JOIN fantasy_player_projections fp
                     ON fp.nhl_player_id = a.nhl_player_id AND fp.source='avg' AND fp.season=2025
             WHERE a.id = :aid
            """
        ), {"aid": auction_id}).fetchone()
        bids = session.execute(sa_text(
            "SELECT team_id, amount, kind, pick_num, created_at FROM cbs_auction_bids WHERE auction_id=:aid ORDER BY created_at ASC"
        ), {"aid": auction_id}).fetchall()
        return {
            "ok": True,
            "winner": {
                "team_id": team_id,
                "amount": amount,
                "nhl_player_id": nhl_pid,
                "pick_num": winner_pick,
                "player_name": (getattr(info, 'player_name', None) if info else None),
                "position": (getattr(info, 'position', None) if info else None),
            },
            "bids": [dict(b._mapping) for b in bids],
        }

@app.post("/api/public/cbs/league/{slug}/auction/admin/update_salary", response_model=dict)
async def post_admin_update_salary(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admin: update finalized roster salary for a closed auction's winner."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        amount = float(payload.get("amount"))
        # Find winner roster entry by auction
        top = session.execute(sa_text(
            """
            SELECT b.team_id, a.nhl_player_id, a.cbs_player_id
              FROM cbs_auction_bids b
              JOIN cbs_auctions a ON a.id=b.auction_id
             WHERE a.id=:aid AND a.league_id=:lid
             ORDER BY b.amount DESC, b.created_at DESC
             LIMIT 1
            """
        ), {"aid": auction_id, "lid": lid}).fetchone()
        if not top:
            raise HTTPException(status_code=404, detail="Winner not found for auction")
        team_id = str(top.team_id)
        nhl_pid = int(top.nhl_player_id)
        # Update roster salary where signed from this auction
        session.execute(sa_text(
            """
            UPDATE cbs_rosters
               SET salary = :sal
             WHERE league_id=:lid AND team_id=:tid AND nhl_player_id=:pid AND slot_type='A' AND status='signed'
            """
        ), {"lid": lid, "tid": team_id, "pid": nhl_pid, "sal": amount})
        return {"ok": True}

@app.post("/api/public/cbs/league/{slug}/auction/admin/reset", response_model=dict)
async def post_admin_reset_auction(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admin: reset a closed auction back to nomination state and remove roster move."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        # Identify winner
        top = session.execute(sa_text(
            """
            SELECT b.team_id, b.amount, a.nhl_player_id, a.cbs_player_id
              FROM cbs_auction_bids b
              JOIN cbs_auctions a ON a.id=b.auction_id
             WHERE a.id=:aid AND a.league_id=:lid
             ORDER BY b.amount DESC, b.created_at DESC
             LIMIT 1
            """
        ), {"aid": auction_id, "lid": lid}).fetchone()
        # Reopen the auction and delete roster assignment if there was a winner
        session.execute(sa_text("UPDATE cbs_auctions SET status='open', closed_at=NULL WHERE id=:id AND league_id=:lid"), {"id": auction_id, "lid": lid})
        if top:
            team_id = str(top.team_id)
            nhl_pid = int(top.nhl_player_id)
            session.execute(sa_text(
                """
                DELETE FROM cbs_rosters
                 WHERE league_id=:lid AND team_id=:tid AND nhl_player_id=:pid AND slot_type='A' AND status='signed'
                """
            ), {"lid": lid, "tid": team_id, "pid": nhl_pid})
        return {"ok": True}

@app.post("/api/public/cbs/league/{slug}/admin/attach", response_model=dict)
async def admin_attach_membership(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admin helper: attach a user (by email/subject) to a team in this league.
    Body: { email: string, subject?: string, team_id?: string, team_name?: string, role?: string }
    """
    from sqlalchemy import text as sa_text
    email = (payload.get("email") or "").strip()
    subject = (payload.get("subject") or email).strip()
    team_id = (payload.get("team_id") or "").strip()
    team_name = (payload.get("team_name") or "").strip()
    role = (payload.get("role") or "member").strip() or "member"
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        # Resolve team_id by name if not provided
        if not team_id and team_name:
            row = session.execute(sa_text(
                "SELECT team_id FROM cbs_teams WHERE league_id=:lid AND team_name ILIKE :name LIMIT 1"
            ), {"lid": lid, "name": team_name}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="team not found")
            team_id = str(row.team_id)
        if not team_id:
            raise HTTPException(status_code=400, detail="team_id or team_name required")
        # Upsert membership
        session.execute(sa_text(
            """
            INSERT INTO cbs_user_memberships(league_id, team_id, user_subject, user_email, role)
            VALUES (:lid, :tid, :sub, :email, :role)
            ON CONFLICT (league_id, user_subject)
            DO UPDATE SET team_id = EXCLUDED.team_id, user_email = EXCLUDED.user_email, role = EXCLUDED.role
            """
        ), {"lid": lid, "tid": team_id, "sub": subject, "email": email, "role": role})
        return {"ok": True, "league_id": lid, "team_id": team_id, "email": email, "subject": subject}

@app.post("/api/public/cbs/league/{slug}/auction/admin/change_nomination", response_model=dict)
async def post_admin_change_nomination(slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admin: change the nominated player for an open auction.
    Body: { auction_id, nhl_player_id, cbs_player_id? }
    """
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        lid = _get_league_id_by_slug(session, slug)
        auction_id = int(payload.get("auction_id"))
        nhl_pid = int(payload.get("nhl_player_id"))
        cbs_pid = payload.get("cbs_player_id")
        st = session.execute(sa_text("SELECT status FROM cbs_auctions WHERE id=:id AND league_id=:lid"), {"id": auction_id, "lid": lid}).fetchone()
        if not st or st.status != 'open':
            raise HTTPException(status_code=400, detail="Auction not open")
        # Update nomination
        session.execute(sa_text(
            """
            UPDATE cbs_auctions
               SET nhl_player_id = :pid,
                   cbs_player_id = :cid,
                   started_at = NOW()
             WHERE id=:id AND league_id=:lid
            """
        ), {"pid": nhl_pid, "cid": cbs_pid, "id": auction_id, "lid": lid})
        try:
            await ws_manager.broadcast(slug, {"event": "nomination_changed", "auction_id": auction_id, "nhl_player_id": nhl_pid})
        except Exception:
            pass
        return {"ok": True}

@app.get("/api/public/cbs/league/{slug}/admin/users", response_model=dict)
async def admin_list_known_users(slug: str) -> Dict[str, Any]:
    """Return a tolerant list of known users for Assign dropdown.
    Sources (any missing tables are skipped gracefully):
      - cbs_user_memberships (user_email/user_subject)
      - cbs_gm_credentials (login as email)
      - fantasy_users (optional; if present)
    """
    from sqlalchemy import text as sa_text
    try:
        with get_fantasy_session() as session:
            lid = _get_league_id_by_slug(session, slug)
            out: List[Dict[str, Any]] = []

        def _table_exists(name: str) -> bool:
            try:
                row = session.execute(sa_text("SELECT to_regclass(:n) AS t"), {"n": f"public.{name}"}).fetchone()
                return bool(getattr(row, 't', None))
            except Exception:
                return False

        # Collect from memberships
        if _table_exists('cbs_user_memberships'):
            rows_m = session.execute(sa_text(
                """
                SELECT DISTINCT COALESCE(user_email,'') AS email,
                                COALESCE(user_subject,'') AS subject,
                                '' AS display_name
                  FROM cbs_user_memberships
                 WHERE league_id = :lid
                """
            ), {"lid": lid}).fetchall()
            for r in rows_m:
                em = (getattr(r, 'email', '') or '').strip()
                sub = (getattr(r, 'subject', '') or '').strip()
                if em or sub:
                    out.append({"email": em, "subject": sub, "display_name": ""})

        # Collect from GM credentials (login)
        if _table_exists('cbs_gm_credentials'):
            rows_g = session.execute(sa_text(
                """
                SELECT DISTINCT COALESCE(login,'') AS email
                  FROM cbs_gm_credentials
                 WHERE league_id = :lid
                """
            ), {"lid": lid}).fetchall()
            for r in rows_g:
                em = (getattr(r, 'email', '') or '').strip()
                if em:
                    out.append({"email": em, "subject": "", "display_name": ""})

            # Optional fantasy_users
            if _table_exists('fantasy_users'):
                rows_f = session.execute(sa_text(
                    """
                    SELECT DISTINCT COALESCE(email,'') AS email,
                                    COALESCE(external_auth_id,'') AS subject,
                                    COALESCE(display_name,'') AS display_name
                      FROM fantasy_users
                    """
                )).fetchall()
                for r in rows_f:
                    em = (getattr(r, 'email', '') or '').strip()
                    sub = (getattr(r, 'subject', '') or '').strip()
                    if em or sub:
                        out.append({"email": em, "subject": sub, "display_name": (getattr(r, 'display_name', '') or '')})

            # Deduplicate by (email, subject)
            dedup: Dict[tuple, Dict[str, Any]] = {}
            for u in out:
                key = (u.get('email') or '', u.get('subject') or '')
                if key not in dedup:
                    dedup[key] = u
            users = sorted(dedup.values(), key=lambda x: (x.get('email') or '', x.get('subject') or ''))
            return {"league_id": lid, "users": users}
    except Exception as e:
        logger.error(f"/admin/users failed: {e}")
        return {"league_id": None, "users": []}
@app.get("/api/pools/{pool_id}/state", response_model=dict)
async def get_pool_state(pool_id: str) -> Dict[str, Any]:
    """Minimal UHHP draft state for frontend draft room. Pulls CBS order and teams if available."""
    from sqlalchemy import text as sa_text
    with get_fantasy_session() as session:
        # Try to find UHHP league by slug or name
        league_row = session.execute(sa_text(
            """
            SELECT id, provider_slug, name
              FROM cbs_leagues
             WHERE provider_slug ILIKE 'uhhp' OR name ILIKE '%UHHP%'
             ORDER BY id DESC
             LIMIT 1
            """
        )).fetchone()
        league_id = league_row.id if league_row else None
        teams: List[Dict[str, Any]] = []
        order: List[str] = []
        if league_id:
            team_rows = session.execute(sa_text(
                """
                SELECT team_name
                  FROM cbs_teams
                 WHERE league_id = :lid AND COALESCE(is_active, true) = true
                 ORDER BY team_name
                """
            ), {"lid": league_id}).fetchall()
            teams = [{"name": r.team_name} for r in team_rows]
            order = [t["name"] for t in teams]
        picks: List[Dict[str, Any]] = []
        return {"teams": teams, "order": order, "picks": picks}

# API key endpoints
@app.get("/api/user/api-keys")
async def get_user_api_keys(current_user: FantasyUser = Depends(get_current_user)):
    """Get user's API keys"""
    with get_fantasy_session() as session:
        api_keys = session.query(FantasyAPIKey).filter(
            FantasyAPIKey.user_id == current_user.id,
            FantasyAPIKey.is_active == True
        ).all()
        
        return {
            "api_keys": [
                {
                    "id": key.id,
                    "key_name": key.key_name,
                    "api_key": key.api_key,
                    "permissions": key.permissions,
                    "last_used": key.last_used.isoformat() if key.last_used else None,
                    "usage_count": key.usage_count,
                    "is_active": key.is_active,
                    "created_at": key.created_at.isoformat()
                } for key in api_keys
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 