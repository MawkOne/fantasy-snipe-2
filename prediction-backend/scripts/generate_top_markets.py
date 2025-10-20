# /Users/markhenderson/Cursor Projects/NHL-API/prediction-backend/scripts/generate_top_markets.py
import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor

DB = os.environ.get("MARKET_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("NHL_DATABASE_URL")
if not DB:
    raise SystemExit("Set MARKET_DATABASE_URL")

B_DEFAULT = float(os.environ.get("MARKET_DEFAULT_B", "50"))
STATUS = os.environ.get("MARKET_STATUS", "open")

KEYS = {
    "player": ["Player", "player", "PLAYER"],
    "pts": ["PTS", " PTS", "Points"],
    "g": ["G", " G", "Goals"],
    "a": ["A", " A", "Assists"],
}

def pick(d: dict, names: list[str]) -> str:
    for n in names:
        if n in d and d[n] not in (None, ""):
            return str(d[n])
    return ""

def to_number(s: str) -> float:
    t = re.sub(r"[^0-9.\-]", "", s or "")
    try:
        return float(t) if t else 0.0
    except Exception:
        return 0.0


def top_n(cur, key_names: list[str], n: int = 12):
    cur.execute("SELECT data FROM player_projections")
    rows = [r["data"] for r in cur.fetchall()]
    items = []
    for d in rows:
        player = pick(d, KEYS["player"]).strip()
        val = to_number(pick(d, key_names))
        if player:
            items.append((player, val, d))
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n]


def ensure_market(cur, slug: str, title: str, description: str, b: float, player_name: str | None, metric: str | None, threshold: float | None):
    cur.execute("SELECT id FROM markets WHERE slug=%s", (slug,))
    r = cur.fetchone()
    if r:
        return r["id"]
    cur.execute(
        """
        INSERT INTO markets (slug, title, description, outcome_type, status, b, player_name, metric, threshold)
        VALUES (%s,%s,%s,'binary',%s,%s,%s,%s,%s)
        ON CONFLICT (slug) DO NOTHING
        RETURNING id
        """,
        (slug, title, description, STATUS, b, player_name, metric, threshold),
    )
    market_id = cur.fetchone()["id"]
    cur.execute("INSERT INTO market_outcomes (market_id, outcome) VALUES (%s,'yes'),(%s,'no')", (market_id, market_id))
    cur.execute("INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s,'yes',0),(%s,'no',0)", (market_id, market_id))
    return market_id


def main():
    conn = psycopg2.connect(DB, cursor_factory=RealDictCursor)
    try:
        with conn:
            with conn.cursor() as cur:
                groups = [
                    ("pts", KEYS["pts"], "Top 12 Points"),
                    ("g", KEYS["g"], "Top 12 Goals"),
                    ("a", KEYS["a"], "Top 12 Assists"),
                ]
                created = []
                for kind, keys, label in groups:
                    top = top_n(cur, keys, 12)
                    for rank, (player, val, d) in enumerate(top, start=1):
                        # threshold: round to nearest .5
                        thr = float(int(val)) + 0.5
                        slug = f"{kind}-r{rank}-{player.lower().replace(' ', '-') }"
                        title = f"{player} — {label} (rank {rank})"
                        description = f"Auto-generated market: {label}. Projection={val}, line={thr}"
                        mid = ensure_market(cur, slug, title, description, B_DEFAULT, player, kind.upper(), thr)
                        created.append((mid, slug))
                print(f"Created/ensured {len(created)} markets")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
