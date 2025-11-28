#!/usr/bin/env python3
import os
import re
import sys
from typing import Set

import psycopg2


def db_connect(db_url: str):
    return psycopg2.connect(db_url, sslmode='require') if 'rlwy.net' in db_url or 'railway' in db_url else psycopg2.connect(db_url)


def extract_rookie_cbs_ids(rosters_path: str) -> Set[str]:
    # Extract CBS IDs that have rookie:"1" in the docs/CBS/rosters blob
    text: str
    with open(rosters_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    ids: Set[str] = set()
    # Find any block that contains an id:"<digits>" and a rookie:"1" near it
    for m in re.finditer(r'"id"\s*:\s*"(?P<id>\d+)"[\s\S]*?"rookie"\s*:\s*"1"', text, flags=re.IGNORECASE | re.DOTALL):
        ids.add(m.group('id'))
    return ids


def main():
    db_url = os.getenv('DATABASE_URL') or os.getenv('FANTASY_DATABASE_URL')
    if not db_url:
        print('DATABASE_URL not set', file=sys.stderr)
        sys.exit(1)
    rosters_path = '/Users/markhenderson/Cursor Projects/NHL-API/docs/CBS/rosters'
    if not os.path.exists(rosters_path):
        print(f'File not found: {rosters_path}', file=sys.stderr)
        sys.exit(1)

    rookie_ids = extract_rookie_cbs_ids(rosters_path)
    print(f"Found {len(rookie_ids)} rookie-flagged CBS IDs")

    if not rookie_ids:
        return

    conn = db_connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # Ensure column exists
        cur.execute("ALTER TABLE cbs_rosters ADD COLUMN IF NOT EXISTS rookie BOOLEAN")
        # League id for UHHP
        cur.execute("SELECT id FROM cbs_leagues WHERE provider_slug ILIKE 'uhhp' ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            print('UHHP league not found; updating all leagues')
            lid = None
        else:
            lid = int(row[0])

        # Batch update
        # Set rookie TRUE where cbs_player_id in list (scoped to league if available)
        ids_tuple = tuple(rookie_ids)
        if lid is None:
            cur.execute("UPDATE cbs_rosters SET rookie=TRUE WHERE cbs_player_id = ANY(%s)", (list(rookie_ids),))
        else:
            cur.execute("UPDATE cbs_rosters SET rookie=TRUE WHERE league_id=%s AND cbs_player_id = ANY(%s)", (lid, list(rookie_ids)))
        print(f"Updated rookie=TRUE for {cur.rowcount} rows in cbs_rosters")
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()


