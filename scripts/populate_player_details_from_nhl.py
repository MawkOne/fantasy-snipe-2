#!/usr/bin/env python3
"""
Populate the NHL player_details table from the NHL public landing API.

Source example:
  https://api-web.nhle.com/v1/player/8478402/landing

Behavior:
  - Ensures the table has a landing_url column for traceability.
  - Iterates over player ids from the players table (or a provided subset).
  - Fetches the landing JSON and upserts into player_details.

Env:
  NHL_DATABASE_URL=postgresql://...  (required)

Usage:
  python3 scripts/populate_player_details_from_nhl.py --limit 200 --since-id 0
  python3 scripts/populate_player_details_from_nhl.py --ids 8478402,8478403
"""
import argparse
import os
import sys
import time
from typing import List, Optional, Dict, Any
import requests
from sqlalchemy import create_engine, text as sa_text
from psycopg2.extras import execute_batch  # type: ignore


def get_engine():
    db_url = os.getenv("NHL_DATABASE_URL")
    if not db_url:
        print("NHL_DATABASE_URL is required")
        sys.exit(1)
    return create_engine(db_url, pool_pre_ping=True)


def ensure_schema(engine):
    with engine.begin() as conn:
        conn.execute(sa_text(
            """
            CREATE TABLE IF NOT EXISTS player_details (
              id SERIAL PRIMARY KEY,
              player_id INT UNIQUE NOT NULL,
              birth_date TEXT,
              height_in_inches INT,
              weight_in_pounds INT,
              shoots_catches TEXT,
              nationality TEXT,
              birth_city TEXT,
              birth_state_province TEXT,
              birth_country TEXT,
              rookie BOOLEAN,
              current_team_id INT,
              current_team_tricode TEXT,
              landing_url TEXT
            );
            ALTER TABLE player_details ADD COLUMN IF NOT EXISTS landing_url TEXT;
            """
        ))


def pick_int(v) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def fetch_player(engine_session: requests.Session, player_id: int) -> Optional[Dict[str, Any]]:
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
    try:
        r = engine_session.get(url, timeout=20)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    birth_date = (data.get("birthDate") or None)
    height_in_inches = pick_int(data.get("heightInInches"))
    weight_in_pounds = pick_int(data.get("weightInPounds"))
    shoots_catches = (data.get("shootsCatches") or None)
    birth_city = ((data.get("birthCity") or {}).get("default") if isinstance(data.get("birthCity"), dict) else data.get("birthCity")) or None
    birth_state_province = ((data.get("birthStateProvince") or {}).get("default") if isinstance(data.get("birthStateProvince"), dict) else data.get("birthStateProvince")) or None
    birth_country = (data.get("birthCountry") or None)
    cur_team_id = pick_int(data.get("currentTeamId"))
    cur_team_abbr = (data.get("currentTeamAbbrev") or None)

    return {
        "player_id": int(player_id),
        "birth_date": birth_date,
        "height_in_inches": height_in_inches,
        "weight_in_pounds": weight_in_pounds,
        "shoots_catches": shoots_catches,
        "nationality": None,
        "birth_city": birth_city,
        "birth_state_province": birth_state_province,
        "birth_country": birth_country,
        "current_team_id": cur_team_id,
        "current_team_tricode": cur_team_abbr,
        "landing_url": url,
    }


def main():
    ap = argparse.ArgumentParser(description="Populate player_details from NHL landing API")
    ap.add_argument("--ids", type=str, default="", help="Comma-separated player ids to refresh")
    ap.add_argument("--limit", type=int, default=500, help="Max players when scanning players table")
    ap.add_argument("--since-id", type=int, default=0, help="Only player ids > since-id when scanning")
    args = ap.parse_args()

    engine = get_engine()
    ensure_schema(engine)

    ids: List[int] = []
    if args.ids:
        ids = [int(x) for x in args.ids.split(",") if x.strip()]
    else:
        # derive from players table
        with engine.connect() as conn:
            res = conn.execute(sa_text(
                "SELECT id FROM players WHERE id > :since ORDER BY id ASC LIMIT :lim"
            ), {"since": int(args.since_id), "lim": int(args.limit)})
            ids = [int(r.id) for r in res.fetchall()]

    # Preload existing details to avoid redundant calls
    existing: set[int] = set()
    with engine.connect() as conn:
        rows = conn.execute(sa_text("SELECT player_id FROM player_details"))
        existing = {int(r.player_id) for r in rows}

    sess = requests.Session()
    payload_rows: List[tuple] = []
    ok, fail = 0, 0
    for idx, pid in enumerate(ids):
        if pid in existing:
            continue
        rec = fetch_player(sess, pid)
        if rec is None:
            fail += 1
        else:
            ok += 1
            payload_rows.append((
                rec["player_id"], rec["birth_date"], rec["height_in_inches"], rec["weight_in_pounds"],
                rec["shoots_catches"], rec["nationality"], rec["birth_city"], rec["birth_state_province"],
                rec["birth_country"], None, rec["current_team_id"], rec["current_team_tricode"], rec["landing_url"]
            ))
        # Batch flush every 500
        if len(payload_rows) >= 500 or (idx + 1) == len(ids):
            if payload_rows:
                raw = engine.raw_connection()
                try:
                    cur = raw.cursor()
                    sql = (
                        "INSERT INTO player_details (player_id, birth_date, height_in_inches, weight_in_pounds, "
                        "shoots_catches, nationality, birth_city, birth_state_province, birth_country, rookie, "
                        "current_team_id, current_team_tricode, landing_url) VALUES (" 
                        "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (player_id) DO UPDATE SET "
                        "birth_date=EXCLUDED.birth_date, height_in_inches=EXCLUDED.height_in_inches, "
                        "weight_in_pounds=EXCLUDED.weight_in_pounds, shoots_catches=EXCLUDED.shoots_catches, "
                        "nationality=EXCLUDED.nationality, birth_city=EXCLUDED.birth_city, "
                        "birth_state_province=EXCLUDED.birth_state_province, birth_country=EXCLUDED.birth_country, "
                        "current_team_id=EXCLUDED.current_team_id, current_team_tricode=EXCLUDED.current_team_tricode, "
                        "landing_url=EXCLUDED.landing_url"
                    )
                    execute_batch(cur, sql, payload_rows, page_size=500)
                    raw.commit()
                finally:
                    try:
                        raw.close()
                    except Exception:
                        pass
                payload_rows = []
        time.sleep(0.02)

    print(f"Completed. upserts={ok}, failed={fail}")


if __name__ == "__main__":
    main()


