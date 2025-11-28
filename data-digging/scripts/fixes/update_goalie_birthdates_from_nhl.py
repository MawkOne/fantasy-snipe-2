#!/usr/bin/env python3
import os
import sys
import psycopg2
import psycopg2.extras


def fetch_goalies_with_ids(app_dsn: str) -> list[dict]:
    conn = psycopg2.connect(app_dsn)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT cbs_player_id, nhl_player_id, full_name, birthdate
                  FROM cbs_players
                 WHERE nhl_player_id IS NOT NULL
                   AND UPPER(COALESCE(pos_primary, '')) = 'G'
                """
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def fetch_birthdates_from_nhl(nhl_dsn: str, ids: list[int]) -> dict[int, str | None]:
    if not ids:
        return {}
    conn = psycopg2.connect(nhl_dsn)
    conn.autocommit = True
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT p.id AS player_id, d.birth_date
                  FROM players p
                  LEFT JOIN player_details d ON d.player_id = p.id
                 WHERE p.id = ANY(%s)
                """,
                (ids,),
            )
            return {int(r[0]): (str(r[1]) if r[1] is not None else None) for r in cur.fetchall()}
    finally:
        conn.close()


def update_birthdates(app_dsn: str, mapping: dict[int, str | None]) -> int:
    if not mapping:
        return 0
    conn = psycopg2.connect(app_dsn)
    conn.autocommit = True
    try:
        updated = 0
        with conn.cursor() as cur:
            for pid, bd in mapping.items():
                if not bd:
                    continue
                cur.execute(
                    """
                    UPDATE cbs_players
                       SET birthdate = %s
                     WHERE nhl_player_id = %s
                       AND (birthdate IS NULL OR birthdate::text <> %s)
                    """,
                    (bd, pid, bd),
                )
                updated += cur.rowcount or 0
        return updated
    finally:
        conn.close()


def main() -> int:
    app_dsn = os.getenv("DATABASE_URL")
    nhl_dsn = os.getenv("NHL_DATABASE_URL")
    if not app_dsn or not nhl_dsn:
        print("DATABASE_URL and NHL_DATABASE_URL must be set", file=sys.stderr)
        return 2
    goalies = fetch_goalies_with_ids(app_dsn)
    ids = [int(g["nhl_player_id"]) for g in goalies if g.get("nhl_player_id") is not None]
    bd_map = fetch_birthdates_from_nhl(nhl_dsn, ids)
    updated = update_birthdates(app_dsn, bd_map)
    print(f"Updated {updated} goalie birthdates in cbs_players.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


