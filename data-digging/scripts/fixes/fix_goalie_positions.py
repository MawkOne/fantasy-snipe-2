#!/usr/bin/env python3
import os
import sys
import psycopg2
import psycopg2.extras


def find_goalie_ids_from_nhl(nhl_dsn: str) -> set[int]:
    conn = psycopg2.connect(nhl_dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Try common position columns
            cur.execute(
                """
                SELECT column_name
                  FROM information_schema.columns
                 WHERE table_name = 'players'
                   AND (column_name ILIKE '%pos%' OR column_name ILIKE '%position%')
                """
            )
            cols = [r[0] for r in cur.fetchall()]
            for col in [
                'position_code', 'positioncode', 'primary_position', 'position', 'pos',
            ]:
                if col in cols:
                    pos_col = col
                    break
            else:
                raise RuntimeError("Could not find position column in NHL DB players table")
            sql = f"SELECT id FROM players WHERE UPPER({pos_col}) = 'G'"
            cur.execute(sql)
            return {int(r[0]) for r in cur.fetchall()}
    finally:
        conn.close()


def update_goalies_in_app(app_dsn: str, goalie_ids: set[int]) -> int:
    if not goalie_ids:
        return 0
    conn = psycopg2.connect(app_dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Update in chunks
            total = 0
            ids = sorted(goalie_ids)
            for i in range(0, len(ids), 1000):
                chunk = ids[i:i+1000]
                cur.execute(
                    """
                    UPDATE cbs_players
                       SET pos_primary = 'G'
                     WHERE nhl_player_id = ANY(%s)
                    """,
                    (chunk,),
                )
                total += cur.rowcount or 0
            return total
    finally:
        conn.close()


def main() -> int:
    app_dsn = os.getenv("DATABASE_URL")
    nhl_dsn = os.getenv("NHL_DATABASE_URL")
    if not app_dsn or not nhl_dsn:
        print("DATABASE_URL and NHL_DATABASE_URL must be set", file=sys.stderr)
        return 2
    try:
        goalie_ids = find_goalie_ids_from_nhl(nhl_dsn)
        updated = update_goalies_in_app(app_dsn, goalie_ids)
        print(f"Updated pos_primary='G' for {updated} rows in cbs_players.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


