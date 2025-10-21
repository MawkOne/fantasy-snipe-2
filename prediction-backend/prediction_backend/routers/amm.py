from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import requests

from ..db import get_cursor
from ..models import MarketCreate, MarketResponse, QuoteRequest, QuoteResponse, TradeRequest, TradeResponse
from ..pricing.lmsr import prices_lmsr, quote_delta


router = APIRouter(prefix="/api/amm", tags=["amm"])


def _get_market_q_and_b(cur, market_id: str):
    cur.execute("SELECT b FROM markets WHERE id=%s", (market_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="market not found")
    b = float(row["b"]) if isinstance(row, dict) else float(row[0])
    # outcomes order: yes, no
    cur.execute("SELECT outcome, shares FROM amm_inventory WHERE market_id=%s ORDER BY outcome ASC", (market_id,))
    rows = cur.fetchall()
    inventory: Dict[str, float] = {r["outcome"]: float(r["shares"]) for r in rows}
    q = [inventory.get("no", 0.0), inventory.get("yes", 0.0)]  # sorted order: no, yes
    # prices need to map back to outcome labels
    px = prices_lmsr(q, b)
    prices = {"no": px[0], "yes": px[1]}
    return b, inventory, prices, q


@router.post("/markets", response_model=MarketResponse)
def create_market(payload: MarketCreate):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO markets (slug, title, description, outcome_type, status, b, player_name, metric, threshold, category, sub_category, timeframe, team, volume_total)
            VALUES (%s, %s, %s, 'binary', 'open', %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, created_at
            """,
            (
                payload.slug,
                payload.title,
                payload.description,
                payload.b,
                payload.player_name,
                payload.metric,
                payload.threshold,
                payload.category,
                payload.sub_category,
                payload.timeframe,
                payload.team,
                payload.volume_total,
            ),
        )
        row = cur.fetchone()
        market_id = row["id"]
        # create outcomes and inventory
        cur.execute(
            "INSERT INTO market_outcomes (market_id, outcome) VALUES (%s,'yes'),(%s,'no')",
            (market_id, market_id),
        )
        cur.execute(
            "INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s,'yes',0),(%s,'no',0)",
            (market_id, market_id),
        )
        # response
        b, inventory, prices, _ = _get_market_q_and_b(cur, market_id)
        cur.execute("SELECT slug, title, description, outcome_type, status, created_at, player_name, metric, threshold, category, sub_category, timeframe, team, volume_total, landing_url FROM markets WHERE id=%s", (market_id,))
        m = cur.fetchone()
        return MarketResponse(
            id=str(market_id),
            slug=m["slug"],
            title=m["title"],
            description=m.get("description"),
            outcome_type=m["outcome_type"],
            status=m["status"],
            b=b,
            created_at=str(m["created_at"]),
            outcomes=["yes", "no"],
            inventory=inventory,
            prices=prices,
            player_name=m.get("player_name"),
            metric=m.get("metric"),
            threshold=float(m["threshold"]) if m.get("threshold") is not None else None,
            category=m.get("category"),
            sub_category=m.get("sub_category"),
            timeframe=m.get("timeframe"),
            team=m.get("team"),
            volume_total=float(m["volume_total"]) if m.get("volume_total") is not None else None,
            landing_url=m.get("landing_url"),
        )


@router.get("/markets/{market_id}", response_model=MarketResponse)
def get_market(market_id: str):
    with get_cursor() as cur:
        b, inventory, prices, _ = _get_market_q_and_b(cur, market_id)
        cur.execute("SELECT slug, title, description, outcome_type, status, created_at, player_name, metric, threshold, category, sub_category, timeframe, team, volume_total, landing_url FROM markets WHERE id=%s", (market_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail="market not found")
        landing: Optional[dict] = None
        game_log: Optional[list] = None
        if m.get("landing_url"):
            try:
                r = requests.get(m["landing_url"], timeout=6)
                if r.ok:
                    landing = r.json()
            except Exception:
                landing = None
        # NHL game log via player_id if present in landing or markets table later
        try:
            player_id = None
            if landing and isinstance(landing, dict):
                # some landing payloads include playerId under 'playerId' or nested
                player_id = landing.get("playerId") or landing.get("id")
            # fallback: if markets table has player_id column available
            if not player_id:
                cur.execute("SELECT player_id FROM markets WHERE id=%s", (market_id,))
                row_pid = cur.fetchone()
                if row_pid and (row_pid.get("player_id") is not None):
                    player_id = row_pid["player_id"]
            if player_id:
                # determine season id (YYYYYYYY) for current season; default to 20252026 for now
                season_id = "20252026"
                url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/2"
                gr = requests.get(url, timeout=6)
                if gr.ok:
                    gj = gr.json()
                    if isinstance(gj, dict) and isinstance(gj.get("gameLog"), list):
                        game_log = gj["gameLog"]
        except Exception:
            game_log = None

        # best-effort projection record (exact match on player_name)
        player_projection = None
        try:
            if m.get("player_name"):
                cur.execute(
                    "SELECT data FROM player_projections WHERE (data->>'Player')=%s ORDER BY created_at DESC LIMIT 1",
                    (m["player_name"],),
                )
                row = cur.fetchone()
                if row and row.get("data"):
                    player_projection = row["data"]
        except Exception:
            player_projection = None
        return MarketResponse(
            id=str(market_id),
            slug=m["slug"],
            title=m["title"],
            description=m.get("description"),
            outcome_type=m["outcome_type"],
            status=m["status"],
            b=b,
            created_at=str(m["created_at"]),
            outcomes=["yes", "no"],
            inventory=inventory,
            prices=prices,
            player_name=m.get("player_name"),
            metric=m.get("metric"),
            threshold=float(m["threshold"]) if m.get("threshold") is not None else None,
            category=m.get("category"),
            sub_category=m.get("sub_category"),
            timeframe=m.get("timeframe"),
            team=m.get("team"),
            volume_total=float(m["volume_total"]) if m.get("volume_total") is not None else None,
            landing_url=m.get("landing_url"),
            landing=landing,
            player_projection=player_projection,
            game_log=game_log,
        )


@router.get("/markets/slug/{slug}", response_model=MarketResponse)
def get_market_by_slug(slug: str):
    with get_cursor() as cur:
        # resolve id from slug
        cur.execute("SELECT id FROM markets WHERE slug=%s", (slug,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="market not found")
        market_id = str(row["id"]) if isinstance(row, dict) else str(row[0])
        # reuse logic
        return get_market(market_id)


@router.get("/markets", response_model=List[MarketResponse])
def list_markets():
    results: List[MarketResponse] = []
    with get_cursor() as cur:
        cur.execute("SELECT id, slug, title, description, outcome_type, status, created_at, b, player_name, metric, threshold, category, sub_category, timeframe, team, volume_total, landing_url FROM markets ORDER BY created_at DESC")
        markets = cur.fetchall()
        for m in markets:
            market_id = m["id"]
            b, inventory, prices, _ = _get_market_q_and_b(cur, market_id)
            results.append(
                MarketResponse(
                    id=str(market_id),
                    slug=m["slug"],
                    title=m["title"],
                    description=m.get("description"),
                    outcome_type=m["outcome_type"],
                    status=m["status"],
                    b=b,
                    created_at=str(m["created_at"]),
                    outcomes=["yes", "no"],
                    inventory=inventory,
                    prices=prices,
                    player_name=m.get("player_name"),
                    metric=m.get("metric"),
                    threshold=float(m["threshold"]) if m.get("threshold") is not None else None,
                    category=m.get("category"),
                    sub_category=m.get("sub_category"),
                    timeframe=m.get("timeframe"),
                    team=m.get("team"),
                    volume_total=float(m["volume_total"]) if m.get("volume_total") is not None else None,
                    landing_url=m.get("landing_url"),
                )
            )
    return results


@router.post("/markets/{market_id}/quote", response_model=QuoteResponse)
def quote_market(market_id: str, payload: QuoteRequest):
    if payload.outcome not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="invalid outcome")
    with get_cursor() as cur:
        b, inventory, _prices, q = _get_market_q_and_b(cur, market_id)
        idx = 1 if payload.outcome == "yes" else 0
        qd = quote_delta(q, b, idx, payload.delta)
        return QuoteResponse(
            cost=qd["cost"],
            price_after=qd["price_after"],
            prices_after={"no": qd["prices_after"][0], "yes": qd["prices_after"][1]},
        )


@router.post("/markets/{market_id}/trade", response_model=TradeResponse)
def trade_market(market_id: str, payload: TradeRequest):
    if payload.outcome not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="invalid outcome")
    if payload.shares == 0:
        raise HTTPException(status_code=400, detail="shares must be non-zero")
    with get_cursor() as cur:
        b, inventory, _prices, q = _get_market_q_and_b(cur, market_id)
        idx = 1 if payload.outcome == "yes" else 0
        qd = quote_delta(q, b, idx, payload.shares)
        cost = qd["cost"]
        # naive funds check: require cost <= available if buying; allow negative cost for selling
        if cost > 0:
            cur.execute(
                "SELECT available FROM balances WHERE user_id=%s AND asset='VC'",
                (payload.user_id,),
            )
            row = cur.fetchone()
            available = float(row["available"]) if row else 0.0
            if available + 1e-9 < cost:
                raise HTTPException(status_code=400, detail="insufficient VC balance")
        # apply trade
        side = "buy" if payload.shares > 0 else "sell"
        cur.execute(
            "UPDATE amm_inventory SET shares = shares + %s WHERE market_id=%s AND outcome=%s",
            (payload.shares, market_id, payload.outcome),
        )
        cur.execute(
            """
            INSERT INTO trades (market_id, user_id, side, outcome, shares, price, cost)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                market_id,
                payload.user_id,
                side,
                payload.outcome,
                abs(payload.shares),
                float(qd["price_after"]),
                float(cost),
            ),
        )
        # update balances + ledger
        if cost != 0:
            cur.execute(
                "INSERT INTO ledger_entries (user_id, asset, delta, reason, ref_type) VALUES (%s,'VC',%s,%s,%s)",
                (payload.user_id, -cost, "amm_trade", "trade"),
            )
            # upsert balance
            cur.execute(
                """
                INSERT INTO balances (user_id, asset, available, reserved)
                VALUES (%s,'VC',%s,0)
                ON CONFLICT (user_id, asset) DO UPDATE SET available = balances.available + EXCLUDED.available
                """,
                (payload.user_id, -cost),
            )
        # new balance
        cur.execute(
            "SELECT available FROM balances WHERE user_id=%s AND asset='VC'",
            (payload.user_id,),
        )
        row = cur.fetchone()
        new_balance = float(row["available"]) if row else 0.0
        return TradeResponse(
            cost=float(cost),
            price_after=float(qd["price_after"]),
            user_vc_balance=new_balance,
        )


