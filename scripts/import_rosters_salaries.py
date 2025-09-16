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


def parse_player_display(s: str) -> Tuple[str, Optional[str], Optional[str]]:
    s = (s or '').strip()
    if '|' in s:
        left, right = s.split('|', 1)
        team = right.strip().split()[0] if right.strip() else None
        left = left.strip()
        m = re.match(r"^(.*)\s+([A-Z])$", left)
        if m:
            return (m.group(1).strip(), m.group(2), team)
        return (left, None, team)
    m = re.match(r"^(.*)\s+([A-Z])$", s)
    if m:
        return (m.group(1).strip(), m.group(2), None)
    return (s, None, None)


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


def build_cbs_name_to_id_map(cur) -> Dict[str, str]:
    cur.execute("SELECT cbs_player_id, full_name FROM cbs_players")
    m: Dict[str, str] = {}
    for pid, name in cur.fetchall():
        m.setdefault(normalize_name(name or ''), pid)
    return m


def main():
    ap = argparse.ArgumentParser(description='Import CSV rosters with salaries into cbs_rosters (A/I) and map nhl ids')
    ap.add_argument('--db-url', default=os.getenv('DATABASE_URL') or os.getenv('FANTASY_DATABASE_URL') or 'postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway')
    ap.add_argument('--csv', default='/Users/markhenderson/Cursor Projects/NHL-API/docs/rosters_salares.csv')
    ap.add_argument('--yahoo-json', default='/Users/markhenderson/Cursor Projects/NHL-API/Player_sources/yahoo_NHL_players_map')
    args = ap.parse_args()

    conn = db_connect(args.db_url)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # League id for UHHP
        cur.execute("SELECT id FROM cbs_leagues WHERE provider_slug ILIKE 'uhhp' ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            print('No UHHP league found')
            return
        league_id = int(row[0])
        # Team name -> team_id
        cur.execute("SELECT team_id, team_name FROM cbs_teams WHERE league_id=%s", (league_id,))
        team_name_to_id: Dict[str, str] = {}
        for tid, tname in cur.fetchall():
            team_name_to_id[(tname or '').strip().lower()] = str(tid)

        cbs_name_to_id = build_cbs_name_to_id_map(cur)
        name_to_nhl = load_yahoo_name_to_nhl_id(args.yahoo_json)

        roster_rows: List[Tuple[int, str, Optional[int], str, Optional[str], Optional[str], Optional[float], Optional[int], Optional[str], Optional[str], Optional[str], Optional[str], int, Optional[int]]] = []
        # columns: team_id, season, cbs_player_id, slot_type, status, acquired_via, salary, years, effective_from, effective_to, source_url, future_fa, roster_order, nhl_player_id

        current_section = None  # 'Skaters' or 'Goaltenders'
        current_team = None
        order_idx: Dict[str, int] = {}

        with open(args.csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header: List[str] = []
            for r in reader:
                if not r:
                    continue
                if len(r) == 1:
                    val = (r[0] or '').strip()
                    if val in ('Skaters', 'Goaltenders'):
                        current_section = val
                        header = []
                        continue
                    # Team header
                    if val and val.upper() != 'TOTALS':
                        current_team = val.strip()
                        continue
                # headers
                if r and 'Player' in r and ('Status' in r or current_section == 'Goaltenders'):
                    header = r
                    continue
                if not header:
                    continue
                # Data rows; extract team_name, player, status/pos/salary/years
                team_name = (r[0] or '').strip()
                player_disp = (r[1] or '').strip()
                if not player_disp or (player_disp.upper().startswith('TOTALS')):
                    continue
                # For goaltenders block, columns are Avail,Player,FPTS
                status = None
                pos = None
                salary = None
                years = None
                if current_section == 'Skaters':
                    status = (r[2] or '').strip().upper() or None
                    pos = (r[3] or '').strip().upper() or None
                    try:
                        salary = float((r[4] or '').strip() or 0)
                    except Exception:
                        salary = None
                    try:
                        years = int((r[5] or '').strip() or 0)
                    except Exception:
                        years = None
                else:
                    status = 'A'
                    pos = 'G'

                # Map team
                tid = team_name_to_id.get((team_name or current_team or '').strip().lower())
                if not tid:
                    continue
                # Map player
                pname, ppos, _abbr = parse_player_display(player_disp)
                cbs_id = cbs_name_to_id.get(normalize_name(pname))
                nhl_id = name_to_nhl.get(normalize_name(pname))
                if not cbs_id:
                    continue
                idx = order_idx.get(tid, 0)
                order_idx[tid] = idx + 1
                # Normalize slot_type: A for Active; everything else as I (inactive/RS)
                slot_type = 'A' if (status or '').upper() == 'A' else 'I'
                roster_rows.append((
                    int(tid), None, cbs_id, slot_type, None, 'csv_import', salary, years,
                    None, None, None, None, idx, nhl_id
                ))

        if roster_rows:
            # Replace all CSV-imported rows (slot_type A/I) to avoid duplicates
            cur.execute("DELETE FROM cbs_rosters WHERE league_id=%s AND slot_type IN ('A','I')", (league_id,))
            execute_batch(
                cur,
                """
                INSERT INTO cbs_rosters(
                    league_id, team_id, season, cbs_player_id, slot_type, status, acquired_via, salary, years,
                    effective_from, effective_to, source_url, future_fa, roster_order, nhl_player_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [ (league_id,)+rr for rr in roster_rows ],
                page_size=1000,
            )
        print(f"Upserted roster rows={len(roster_rows)}")
    finally:
        cur.close(); conn.close()


if __name__ == '__main__':
    main()


