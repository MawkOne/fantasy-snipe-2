from fastapi import APIRouter, HTTPException
from typing import Dict, List

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
            INSERT INTO markets (slug, title, description, outcome_type, status, b, player_name, metric, threshold)
            VALUES (%s, %s, %s, 'binary', 'open', %s, %s, %s, %s) RETURNING id, created_at
            """,
            (
                payload.slug,
                payload.title,
                payload.description,
                payload.b,
                payload.player_name,
                payload.metric,
                payload.threshold,
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
        cur.execute("SELECT slug, title, description, outcome_type, status, created_at, player_name, metric, threshold FROM markets WHERE id=%s", (market_id,))
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
        )


@router.get("/markets/{market_id}", response_model=MarketResponse)
def get_market(market_id: str):
    with get_cursor() as cur:
        b, inventory, prices, _ = _get_market_q_and_b(cur, market_id)
        cur.execute("SELECT slug, title, description, outcome_type, status, created_at, player_name, metric, threshold FROM markets WHERE id=%s", (market_id,))
        m = cur.fetchone()
        if not m:
            raise HTTPException(status_code=404, detail="market not found")
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
        )


@router.get("/markets", response_model=List[MarketResponse])
def list_markets():
    results: List[MarketResponse] = []
    with get_cursor() as cur:
        cur.execute("SELECT id, slug, title, description, outcome_type, status, created_at, b, player_name, metric, threshold FROM markets ORDER BY created_at DESC")
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


