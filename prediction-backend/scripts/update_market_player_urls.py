import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


# Players DB (source of landing_url)
PLAYERS_DB = os.environ.get(
    "PLAYERS_DATABASE_URL",
    "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require",
)

# Markets DB (target)
MARKET_DB = os.environ.get(
    "MARKET_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:KhNNBPUlaWjUQKpcwzcqmXXUfarnlZTr@maglev.proxy.rlwy.net:39125/railway",
    ),
)


def fetch_player_url_map() -> dict[str, str]:
    """Return mapping full_name(lower) -> landing_url from players DB."""
    conn = psycopg2.connect(PLAYERS_DB, cursor_factory=RealDictCursor)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.full_name, d.landing_url
            FROM players p
            JOIN player_details d ON d.player_id = p.id
            WHERE d.landing_url IS NOT NULL AND d.landing_url<>''
            """
        )
        rows = cur.fetchall()
        return {str(r["full_name"]).strip().lower(): str(r["landing_url"]).strip() for r in rows}
    finally:
        conn.close()


def update_markets(url_map: dict[str, str]) -> tuple[int, int]:
    """Update markets with landing_url when category is Players and names match.
    Returns (updated, missing).
    """
    conn = psycopg2.connect(MARKET_DB, cursor_factory=RealDictCursor)
    conn.autocommit = False
    updated = 0
    missing = 0
    try:
        cur = conn.cursor()
        # Ensure column exists
        cur.execute("ALTER TABLE markets ADD COLUMN IF NOT EXISTS landing_url TEXT")
        # Fetch candidate markets
        cur.execute(
            """
            SELECT id, player_name FROM markets
            WHERE category='Players' AND (landing_url IS NULL OR landing_url='')
            """
        )
        rows = cur.fetchall()
        for r in rows:
            name = (r["player_name"] or "").strip().lower()
            if not name:
                missing += 1
                continue
            url = url_map.get(name)
            if url:
                cur.execute("UPDATE markets SET landing_url=%s WHERE id=%s", (url, r["id"]))
                updated += 1
            else:
                missing += 1
        conn.commit()
        return updated, missing
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    url_map = fetch_player_url_map()
    updated, missing = update_markets(url_map)
    print(f"Updated markets: {updated}; No match: {missing}")


if __name__ == "__main__":
    if not MARKET_DB:
        print("MARKET_DATABASE_URL not set and default missing.", file=sys.stderr)
        sys.exit(1)
    main()


