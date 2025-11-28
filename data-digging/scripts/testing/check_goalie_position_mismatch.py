#!/usr/bin/env python3
import os
import sys
import psycopg2
import psycopg2.extras


def find_goalie_ids_from_nhl(nhl_dsn: str) -> set[int]:
    conn = psycopg2.connect(nhl_dsn)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Discover columns that look like position
            cur.execute(
                """
                SELECT column_name
                  FROM information_schema.columns
                 WHERE table_name = 'players'
                   AND (column_name ILIKE '%pos%' OR column_name ILIKE '%position%')
                """
            )
            cols = [r[0] for r in cur.fetchall()]
            # Try common column names in order
            candidates = [
                'position_code', 'positioncode', 'primary_position', 'position', 'pos',
            ]
            pos_col = None
            for c in candidates:
                if c in cols:
                    pos_col = c
                    break
            if not pos_col:
                # Fallback: attempt to read a json blob if present (unlikely)
                raise RuntimeError("Could not find position column in NHL DB players table")

            sql = f"SELECT id FROM players WHERE UPPER({pos_col}) = 'G'"
            cur.execute(sql)
            rows = cur.fetchall()
            return {int(r[0]) for r in rows}
    finally:
        conn.close()


def find_mismatches(app_dsn: str, goalie_ids: set[int]) -> list[dict]:
    if not goalie_ids:
        return []
    conn = psycopg2.connect(app_dsn)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            ids_list = sorted(goalie_ids)
            # Chunk to avoid very large IN lists
            out: list[dict] = []
            for i in range(0, len(ids_list), 1000):
                chunk = ids_list[i:i+1000]
                cur.execute(
                    """
                    SELECT p.cbs_player_id,
                           p.full_name,
                           p.pos_primary,
                           p.nhl_player_id
                      FROM cbs_players p
                     WHERE p.nhl_player_id = ANY(%s)
                       AND (UPPER(COALESCE(p.pos_primary, '')) <> 'G')
                    ORDER BY p.full_name
                    """,
                    (chunk,),
                )
                out.extend([dict(r) for r in cur.fetchall()])
            return out
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
        mismatches = find_mismatches(app_dsn, goalie_ids)
        if not mismatches:
            print("No mismatches. All NHL goalies are 'G' in cbs_players.")
            return 0
        print("NHL goalies not marked as 'G' in cbs_players:")
        for r in mismatches:
            print(f"nhl_player_id={r['nhl_player_id']}, cbs_player_id={r['cbs_player_id']}, name={r['full_name']}, pos_primary={r['pos_primary']}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


