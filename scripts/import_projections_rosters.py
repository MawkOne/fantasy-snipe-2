#!/usr/bin/env python3
import os
import re
import csv
import json
import argparse
from typing import Dict, Optional, Tuple, List

import psycopg2
from psycopg2.extras import execute_batch


def db_connect(db_url: str):
    return psycopg2.connect(db_url, sslmode='require') if 'rlwy.net' in db_url or 'railway' in db_url else psycopg2.connect(db_url)


def read_text(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def normalize_name(name: str) -> str:
    n = (name or '').strip()
    n = re.sub(r"\s+", ' ', n)
    return n.lower()


def build_cbs_name_to_id_map(skaters_path: str, goalies_path: Optional[str] = None) -> Dict[str, str]:
    """Parse CBS skaters/goalies HTML to map display name -> cbs_player_id."""
    m: Dict[str, str] = {}
    def parse(html: str):
        # Prefer aria-label name when present
        for a_m in re.finditer(r"aria-label='\s*([^']+?)\s*'\s+href='/players/playerpage/(\d+)'", html):
            label = a_m.group(1)
            pid = a_m.group(2)
            # label often like "Connor McDavid C EDM" → strip trailing pos/team
            label_name = re.sub(r"\s+[A-Z](?:\s+[A-Z]{2,3})?$", '', label).strip()
            m.setdefault(normalize_name(label_name), pid)
        # Fallback: anchor text
        for a_m in re.finditer(r"class='playerLink'[^>]*href='/players/playerpage/(\d+)'[^>]*>([^<]+)<", html):
            pid = a_m.group(1)
            anchor_name = a_m.group(2).strip()
            m.setdefault(normalize_name(anchor_name), pid)
    sk_html = read_text(skaters_path)
    parse(sk_html)
    if goalies_path and os.path.exists(goalies_path):
        parse(read_text(goalies_path))
    return m


def load_yahoo_name_to_nhl_id(path: str) -> Dict[str, int]:
    try:
        with open(path, 'r') as f:
            arr = json.load(f)
        out: Dict[str, int] = {}
        for it in arr:
            name = it.get('nhl_player_name') or it.get('yahoo_player_name')
            nhl_id = it.get('nhl_player_id')
            if not name or not nhl_id:
                continue
            try:
                out[normalize_name(name)] = int(nhl_id)
            except Exception:
                continue
        return out
    except Exception:
        return {}


def parse_player_display(s: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Given 'Connor McDavid C | EDM' → ('Connor McDavid','C','EDM')."""
    s = (s or '').strip()
    if '|' in s:
        left, right = s.split('|', 1)
        team = right.strip().split()[0] if right.strip() else None
        left = left.strip()
        # left may end with position code
        m = re.match(r"^(.*)\s+([A-Z])$", left)
        if m:
            name = m.group(1).strip()
            pos = m.group(2)
        else:
            name = left
            pos = None
        return (name, pos, team)
    # No team pipe; try trailing pos
    m = re.match(r"^(.*)\s+([A-Z])$", s)
    if m:
        return (m.group(1).strip(), m.group(2), None)
    return (s, None, None)


def upsert_player_map(cur, rows: List[Tuple[str, int, float, str]]):
    if not rows:
        return 0
    execute_batch(
        cur,
        """
        INSERT INTO cbs_player_map(cbs_player_id, nhl_player_id, confidence, match_method)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (cbs_player_id) DO UPDATE SET
          nhl_player_id=EXCLUDED.nhl_player_id,
          confidence=EXCLUDED.confidence,
          match_method=EXCLUDED.match_method,
          mapped_at=NOW()
        """,
        rows,
        page_size=1000,
    )
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description='Import projections CSV to map players and populate CBS rosters')
    ap.add_argument('--db-url', default=os.getenv('DATABASE_URL') or os.getenv('FANTASY_DATABASE_URL') or 'postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway')
    ap.add_argument('--csv', default='/Users/markhenderson/Cursor Projects/NHL-API/docs/projections.csv')
    ap.add_argument('--skaters', default='/Users/markhenderson/Cursor Projects/NHL-API/docs/CBS/skaters')
    ap.add_argument('--goalies', default='/Users/markhenderson/Cursor Projects/NHL-API/docs/CBS/goalies')
    ap.add_argument('--yahoo-json', default='/Users/markhenderson/Cursor Projects/NHL-API/Player_sources/yahoo_NHL_players_map')
    args = ap.parse_args()

    name_to_cbs = build_cbs_name_to_id_map(args.skaters, args.goalies)
    name_to_nhl = load_yahoo_name_to_nhl_id(args.yahoo_json)

    # Read CSV rows
    rows: List[Tuple[str, str]] = []  # (team_name, player_display)
    with open(args.csv, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header_seen = False
        for r in reader:
            if not r:
                continue
            # Find header row containing 'Player'
            if not header_seen:
                if any(col.strip() == 'Player' for col in r):
                    header = [c.strip() for c in r]
                    try:
                        team_idx = header.index('Avail')
                        player_idx = header.index('Player')
                    except ValueError:
                        continue
                    header_seen = True
                continue
            # After header
            try:
                team_name = (r[team_idx] or '').strip()
                player_disp = (r[player_idx] or '').strip()
            except Exception:
                continue
            if not player_disp:
                continue
            rows.append((team_name, player_disp))

    conn = db_connect(args.db_url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # Locate UHHP league
        cur.execute("SELECT id FROM cbs_leagues WHERE provider_slug ILIKE 'uhhp' ORDER BY id LIMIT 1")
        lid_row = cur.fetchone()
        if not lid_row:
            print('No CBS league with provider_slug uhhp found')
            return
        league_id = int(lid_row[0])
        # Map team_name -> team_id
        cur.execute("SELECT team_id, team_name FROM cbs_teams WHERE league_id=%s", (league_id,))
        tn_to_id: Dict[str, str] = {}
        for tid, tname in cur.fetchall():
            tn_to_id[(tname or '').strip().lower()] = str(tid)

        # Build map rows and roster rows
        map_rows: List[Tuple[str, int, float, str]] = []
        roster_rows: List[Tuple[int, str, Optional[int], str, Optional[str], Optional[str], Optional[float], Optional[int], Optional[str], Optional[str], Optional[str], Optional[str], int]] = []
        # roster_rows columns align with insert below (excluding league_id because we pass it separately)
        order_idx: Dict[str, int] = {}

        for team_name, disp in rows:
            name, pos, _abbr = parse_player_display(disp)
            key = normalize_name(name)
            cbs_id = name_to_cbs.get(key)
            if not cbs_id:
                continue
            nhl_id = name_to_nhl.get(key)
            if nhl_id:
                map_rows.append((cbs_id, nhl_id, 0.92, 'projections_yahoo'))
            tkey = (team_name or '').strip().lower()
            team_id = tn_to_id.get(tkey)
            if not team_id:
                continue
            idx = order_idx.get(team_id, 0)
            order_idx[team_id] = idx + 1
            roster_rows.append((
                # team_id, season, cbs_player_id, slot_type, status, acquired_via, salary, years,
                # effective_from, effective_to, source_url, future_fa, roster_order
                int(team_id), None, cbs_id, 'projection', None, 'projections', None, None,
                None, None, None, None, idx
            ))

        if map_rows:
            upsert_player_map(cur, map_rows)
        if roster_rows:
            # Clear previous projection rows for this league
            cur.execute("DELETE FROM cbs_rosters WHERE league_id=%s AND slot_type='projection'", (league_id,))
            execute_batch(
                cur,
                """
                INSERT INTO cbs_rosters(
                    league_id, team_id, season, cbs_player_id, slot_type, status, acquired_via, salary, years,
                    effective_from, effective_to, source_url, future_fa, roster_order
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    (league_id,)+rr for rr in roster_rows
                ],
                page_size=1000,
            )
        print(f"Upserted maps={len(map_rows)} projection_roster_rows={len(roster_rows)}")
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()


