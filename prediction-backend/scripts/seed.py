import os
import sys
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_url() -> str:
    db_url = os.environ.get("NHL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("Set DATABASE_URL or NHL_DATABASE_URL in env.", file=sys.stderr)
        sys.exit(1)
    return db_url


def seed():
    conn = psycopg2.connect(get_db_url(), cursor_factory=RealDictCursor)
    conn.autocommit = False
    try:
        cur = conn.cursor()

        # Ensure pgcrypto exists (for UUID default usage in SQL if needed)
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

        # Create or fetch a demo user balance
        user_id = str(uuid.uuid4())
        vc = 10000.0
        cur.execute(
            """
            INSERT INTO balances (user_id, asset, available, reserved)
            VALUES (%s,'VC',%s,0)
            ON CONFLICT (user_id, asset) DO UPDATE SET available = EXCLUDED.available
            RETURNING user_id
            """,
            (user_id, vc),
        )

        # Create or fetch a demo market
        slug = "demo_nhl_mvp_binary"
        title = "Will Player X win the NHL MVP?"
        b = 50.0
        cur.execute("SELECT id FROM markets WHERE slug=%s", (slug,))
        row = cur.fetchone()
        if row:
            market_id = row["id"]
        else:
            cur.execute(
                """
                INSERT INTO markets (slug, title, description, outcome_type, status, b)
                VALUES (%s, %s, %s, 'binary', 'open', %s)
                RETURNING id
                """,
                (slug, title, "Demo seeded market", b),
            )
            market_id = cur.fetchone()["id"]

        # Outcomes and inventory (idempotent)
        cur.execute(
            "INSERT INTO market_outcomes (market_id, outcome) VALUES (%s,'yes') ON CONFLICT DO NOTHING",
            (market_id,),
        )
        cur.execute(
            "INSERT INTO market_outcomes (market_id, outcome) VALUES (%s,'no') ON CONFLICT DO NOTHING",
            (market_id,),
        )
        cur.execute(
            "INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s,'yes',0) ON CONFLICT DO NOTHING",
            (market_id,),
        )
        cur.execute(
            "INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s,'no',0) ON CONFLICT DO NOTHING",
            (market_id,),
        )

        conn.commit()
        print("Seed complete.")
        print(f"user_id={user_id}")
        print(f"market_id={market_id}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()


