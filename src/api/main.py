"""
Fantasy Sports API with Kinde Authentication
Main FastAPI application for fantasy sports management
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, create_engine, text

# Import our database and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.fantasy_connection import get_fantasy_session
from src.database.fantasy_models_v2 import (
    FantasyUser, FantasyLeague, FantasyTeam, FantasyPlayer,
    FantasyUserLeague, FantasyAPIKey, FantasySeasonRanking
)
from src.database.connection import connect_with_connector
from src.database.models import (
    Player as NHLPlayer,
    Team as NHLTeam,
    Game as NHLGame,
    PlayerGameStats as NHLPlayerGameStats,
)

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
# Archetype mapping cache
ARCHETYPE_MAPS_CACHE: dict[int, dict[int, str]] = {}

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

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
                engine = create_engine(nhl_url, pool_pre_ping=True) if nhl_url else connect_with_connector()
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
                nhl_url = os.getenv("NHL_DATABASE_URL")
                engine = create_engine(nhl_url, pool_pre_ping=True) if nhl_url else connect_with_connector()
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