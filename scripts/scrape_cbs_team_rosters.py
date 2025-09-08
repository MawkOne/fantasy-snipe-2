#!/usr/bin/env python3
"""
Scrape CBS Sports team rosters for a selected season (e.g., 2024) with detailed columns:
- Team header: "<Team Name> - <Owner Name>"
- Table columns: Player, Salary, Years, Rookie, Own %, Start %, Status, Pos

Writes to Postgres table cbs_team_rosters.
"""

import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple, Set

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from cbs_sports_authenticated import CBSSportsAuthenticated


def navigate_to_season_teams(driver, base_url: str, season_year: int) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    # Try explicit season query params first
    tried = [f"{base_url}/teams?season={season_year}", f"{base_url}/teams?year={season_year}", f"{base_url}/teams"]
    for url in tried:
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            return
        except Exception:
            continue


def collect_team_links(driver) -> List[Tuple[str, str, str]]:
    from selenium.webdriver.common.by import By
    links = driver.find_elements(By.XPATH, "//a[contains(@href, '/teams/') and not(contains(@href, '/teams/all'))]")
    results: List[Tuple[str, str, str]] = []
    seen: Set[str] = set()
    for a in links:
        try:
            href = a.get_attribute("href") or ""
            if not href or href in seen:
                continue
            text = a.text.strip()
            # Heuristic: team links usually have some visible text, but we accept blank and rely on the page title later
            seen.add(href)
            results.append((text, "", href))
        except Exception:
            continue
    return results


def parse_team_header(driver) -> Tuple[str, str]:
    # Expecting header like: "3sheets Sports Entertainment - Michael Wong"
    try:
        title = driver.title or ""
    except Exception:
        title = ""
    header_candidates: List[str] = []
    try:
        from selenium.webdriver.common.by import By
        headers = driver.find_elements(By.XPATH, "//h1|//h2|//h3")
        for h in headers:
            t = h.text.strip()
            if t:
                header_candidates.append(t)
    except Exception:
        pass
    texts = header_candidates + [title]
    for t in texts:
        if " - " in t:
            team, owner = t.split(" - ", 1)
            return team.strip(), owner.strip()
    # Fallback
    return (texts[0] if texts else "", "")


def parse_roster_table(driver, season_year: int, source_url: str, team_name: str, owner_name: str) -> List[Dict[str, Any]]:
    from selenium.webdriver.common.by import By
    tables = driver.find_elements(By.TAG_NAME, "table")
    target = None
    max_cols = 0
    # Choose table whose header contains 'Player' and 'Salary'
    for tbl in tables:
        try:
            rows = tbl.find_elements(By.TAG_NAME, "tr")
            if not rows:
                continue
            header_cells = rows[0].find_elements(By.XPATH, "./th|./td")
            header_texts = [c.text.strip().lower() for c in header_cells]
            if ("player" in " ".join(header_texts)) and ("salary" in " ".join(header_texts)):
                target = tbl
                break
            # Fallback: pick widest table
            if len(header_cells) > max_cols:
                target = tbl
                max_cols = len(header_cells)
        except Exception:
            continue
    if target is None:
        return []

    rows = target.find_elements(By.TAG_NAME, "tr")
    header_cells = rows[0].find_elements(By.XPATH, "./th|./td") if rows else []
    headers = [c.text.strip() or f"col_{i+1}" for i, c in enumerate(header_cells)] if header_cells else []
    # Normalize expected headers
    # We will map by index if names are slightly different
    indices = {
        'player': None, 'salary': None, 'years': None, 'rookie': None,
        'own': None, 'start': None, 'status': None, 'pos': None,
    }
    for i, h in enumerate(headers):
        hl = h.lower()
        if 'player' in hl: indices['player'] = i
        elif 'salary' in hl: indices['salary'] = i
        elif 'years' in hl: indices['years'] = i
        elif 'rookie' in hl: indices['rookie'] = i
        elif 'own' in hl: indices['own'] = i
        elif 'start' in hl: indices['start'] = i
        elif 'status' in hl: indices['status'] = i
        elif hl in ('pos', 'position'): indices['pos'] = i

    records: List[Dict[str, Any]] = []
    for r in rows[1:]:
        cells = r.find_elements(By.XPATH, "./td|./th")
        if not cells:
            continue
        # Stop at totals rows (start with TOTALS)
        row_text = " ".join([c.text for c in cells]).strip()
        if row_text.upper().startswith("TOTALS"):
            break
        def get(idx):
            if idx is None: return ""
            return cells[idx].text.strip() if idx < len(cells) else ""

        rec = {
            'league_subdomain': team_name,  # placeholder; we'll set properly below
            'sport': '',
            'season_year': season_year,
            'team_name': team_name,
            'owner_name': owner_name,
            'player_name': get(indices['player']),
            'salary': get(indices['salary']),
            'years': get(indices['years']),
            'rookie': get(indices['rookie']),
            'own_pct': get(indices['own']),
            'start_pct': get(indices['start']),
            'status': get(indices['status']),
            'position': get(indices['pos']),
            'source_url': source_url,
            'raw': {},
        }
        # Attach raw by header mapping for fidelity
        raw = {}
        for i, c in enumerate(cells):
            key = headers[i] if i < len(headers) else f"col_{i+1}"
            raw[key] = c.text.strip()
        rec['raw'] = raw
        records.append(rec)
    return records


def upsert_cbs_team_rosters(engine: Engine, league_subdomain: str, sport: str, season_year: int, rows: List[Dict[str, Any]]):
    from sqlalchemy import text
    import hashlib
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS cbs_team_rosters (
                id BIGSERIAL PRIMARY KEY,
                league_subdomain TEXT NOT NULL,
                sport TEXT NOT NULL,
                season_year INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                owner_name TEXT,
                player_name TEXT,
                salary TEXT,
                years TEXT,
                rookie TEXT,
                own_pct TEXT,
                start_pct TEXT,
                status TEXT,
                position TEXT,
                source_url TEXT NOT NULL,
                raw JSONB NOT NULL,
                row_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        ))

        insert_sql = text(
            """
            INSERT INTO cbs_team_rosters (
                league_subdomain, sport, season_year, team_name, owner_name, player_name,
                salary, years, rookie, own_pct, start_pct, status, position, source_url, raw, row_hash
            ) VALUES (
                :league_subdomain, :sport, :season_year, :team_name, :owner_name, :player_name,
                :salary, :years, :rookie, :own_pct, :start_pct, :status, :position, :source_url, CAST(:raw AS JSONB), :row_hash
            ) ON CONFLICT (row_hash) DO NOTHING
            """
        )

        batch = []
        for r in rows:
            raw_json = json.dumps(r['raw'], sort_keys=True, ensure_ascii=False)
            h = hashlib.sha256()
            h.update(league_subdomain.encode('utf-8'))
            h.update(b'|')
            h.update(sport.encode('utf-8'))
            h.update(b'|')
            h.update(str(season_year).encode('utf-8'))
            h.update(b'|')
            h.update(r.get('team_name','').encode('utf-8'))
            h.update(b'|')
            h.update(r.get('player_name','').encode('utf-8'))
            h.update(b'|')
            h.update(raw_json.encode('utf-8'))
            row_hash = h.hexdigest()

            batch.append({
                'league_subdomain': league_subdomain,
                'sport': sport,
                'season_year': season_year,
                'team_name': r.get('team_name',''),
                'owner_name': r.get('owner_name',''),
                'player_name': r.get('player_name',''),
                'salary': r.get('salary',''),
                'years': r.get('years',''),
                'rookie': r.get('rookie',''),
                'own_pct': r.get('own_pct',''),
                'start_pct': r.get('start_pct',''),
                'status': r.get('status',''),
                'position': r.get('position',''),
                'source_url': r.get('source_url',''),
                'raw': raw_json,
                'row_hash': row_hash,
            })

        if batch:
            chunk = 500
            for i in range(0, len(batch), chunk):
                conn.execute(insert_sql, batch[i:i+chunk])


def main():
    parser = argparse.ArgumentParser(description='Scrape CBS team rosters for a given season')
    parser.add_argument('--league-id', required=True)
    parser.add_argument('--sport', default='hockey')
    parser.add_argument('--season', type=int, required=True)
    parser.add_argument('--db-url', required=True)
    parser.add_argument('--login-wait', type=int, default=20)

    args = parser.parse_args()

    client = CBSSportsAuthenticated(args.league_id, args.sport, headless=False)
    driver = client.setup_driver()

    # Open base and wait for login
    driver.get(client.base_url)
    print(f"🔓 Please log in within {args.login_wait}s...")
    time.sleep(max(5, args.login_wait))

    # Navigate to teams page for the season
    navigate_to_season_teams(driver, client.base_url, args.season)
    team_links = collect_team_links(driver)
    print(f"Found {len(team_links)} candidate team links")

    all_rows: List[Dict[str, Any]] = []
    visited = 0
    for _, _, href in team_links:
        try:
            driver.get(href)
            time.sleep(2)
            team_name, owner_name = parse_team_header(driver)
            rows = parse_roster_table(driver, args.season, href, team_name, owner_name)
            # Annotate league/sport
            for r in rows:
                r['league_subdomain'] = args.league_id
                r['sport'] = args.sport
            all_rows.extend(rows)
            visited += 1
        except Exception:
            continue

    print(f"✅ Parsed {len(all_rows)} roster rows across {visited} team pages for {args.season}")
    engine = create_engine(args.db_url, pool_pre_ping=True)
    upsert_cbs_team_rosters(engine, args.league_id, args.sport, args.season, all_rows)
    print("📦 Saved to cbs_team_rosters")

    time.sleep(2)

if __name__ == '__main__':
    main()


