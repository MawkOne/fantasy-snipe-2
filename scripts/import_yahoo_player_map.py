#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import List, Dict, Any

import psycopg2
from psycopg2.extras import execute_batch


def db_connect(db_url: str):
    return psycopg2.connect(db_url, sslmode='require') if 'rlwy.net' in db_url or 'railway.app' in db_url else psycopg2.connect(db_url)


def ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS yahoo_player_map (
          yahoo_player_id TEXT PRIMARY KEY,
          nhl_player_id BIGINT NOT NULL,
          nhl_player_name TEXT,
          yahoo_player_name TEXT,
          nhl_team_abbreviation TEXT,
          mapped_position TEXT,
          mapped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )


def upsert_rows(cur, rows: List[Dict[str, Any]]):
    if not rows:
        return 0
    params = []
    for r in rows:
        yahoo_id = str(r.get('yahoo_player_id') or '').strip()
        nhl_id_raw = r.get('nhl_player_id')
        nhl_id = int(nhl_id_raw) if isinstance(nhl_id_raw, (int,)) or (isinstance(nhl_id_raw, str) and nhl_id_raw.isdigit()) else None
        if not yahoo_id or nhl_id is None:
            continue
        params.append(
            (
                yahoo_id,
                nhl_id,
                (r.get('nhl_player_name') or None),
                (r.get('yahoo_player_name') or None),
                (r.get('nhl_team_abbreviation') or None),
                (r.get('mapped_position') or None),
            )
        )
    if not params:
        return 0
    execute_batch(
        cur,
        """
        INSERT INTO yahoo_player_map(
          yahoo_player_id, nhl_player_id, nhl_player_name, yahoo_player_name,
          nhl_team_abbreviation, mapped_position
        ) VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (yahoo_player_id) DO UPDATE SET
          nhl_player_id = EXCLUDED.nhl_player_id,
          nhl_player_name = EXCLUDED.nhl_player_name,
          yahoo_player_name = EXCLUDED.yahoo_player_name,
          nhl_team_abbreviation = EXCLUDED.nhl_team_abbreviation,
          mapped_position = EXCLUDED.mapped_position,
          mapped_at = NOW()
        """,
        params,
        page_size=1000,
    )
    return len(params)


def main():
    ap = argparse.ArgumentParser(description='Import Yahoo->NHL player mapping JSON into Postgres')
    ap.add_argument('--db-url', default=os.getenv('CBS_DB_URL') or os.getenv('FANTASY_DATABASE_URL') or 'postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway')
    ap.add_argument('--json', required=True, help='Path to yahoo_NHL_players_map JSON file')
    args = ap.parse_args()

    path = args.json
    if not os.path.exists(path):
        print(f"JSON file not found: {path}")
        sys.exit(1)

    with open(path, 'r') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print('Failed to parse JSON:', e)
            sys.exit(1)

    if not isinstance(data, list):
        print('Expected a JSON array of mapping objects')
        sys.exit(1)

    conn = db_connect(args.db_url)
    cur = conn.cursor()
    try:
        cur.execute('BEGIN')
        ensure_table(cur)
        count = upsert_rows(cur, data)
        conn.commit()
        print(f"Upserted {count} Yahoo→NHL mappings into yahoo_player_map")
    except Exception as e:
        conn.rollback()
        print('Import error:', e)
        sys.exit(1)
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()


