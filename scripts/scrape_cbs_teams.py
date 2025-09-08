#!/usr/bin/env python3
"""
Scrape CBS Sports league teams table for a selected season (e.g., 2024).

- Opens a visible browser, allows manual login, then navigates to /teams
- Selects the desired season via a year selector (common <select> or buttons)
- Parses the teams table and writes rows to Postgres cbs_teams
"""

import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from cbs_sports_authenticated import CBSSportsAuthenticated


def select_season_on_teams(driver, base_url: str, season_year: int) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    # Try direct season URLs first (common patterns)
    for qp in (f"?season={season_year}", f"?year={season_year}"):
        try:
            driver.get(f"{base_url}/teams{qp}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(2)
            return
        except Exception:
            continue

    # Fallback: base teams page
    driver.get(f"{base_url}/teams")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)

    # Try a <select> season dropdown
    try:
        selects = driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            name = (sel.get_attribute("name") or "").lower()
            id_ = (sel.get_attribute("id") or "").lower()
            if any(k in name+id_ for k in ["season", "year"]):
                from selenium.webdriver.support.ui import Select
                try:
                    Select(sel).select_by_value(str(season_year))
                except Exception:
                    Select(sel).select_by_visible_text(str(season_year))
                time.sleep(2)
                return
    except Exception:
        pass

    # Try clickable year buttons/links
    candidates = driver.find_elements(By.XPATH, f"//*[contains(text(), '{season_year}')] | //a[contains(@href, '{season_year}')]")
    for el in candidates:
        try:
            el.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(2)
            return
        except Exception:
            continue


def parse_teams_table(driver, season_year: int, source_url: str) -> List[Dict[str, Any]]:
    from selenium.webdriver.common.by import By
    tables = driver.find_elements(By.TAG_NAME, "table")
    target = None
    max_rows = 0
    for tbl in tables:
        try:
            rows = tbl.find_elements(By.TAG_NAME, "tr")
            if len(rows) > max_rows:
                max_rows = len(rows)
                target = tbl
        except Exception:
            continue
    if not target or max_rows <= 1:
        return []

    rows = target.find_elements(By.TAG_NAME, "tr")
    header_cells = rows[0].find_elements(By.XPATH, "./th|./td") if rows else []
    if header_cells:
        headers = [c.text.strip() or f"col_{i+1}" for i, c in enumerate(header_cells)]
    else:
        longest = 0
        for r in rows:
            longest = max(longest, len(r.find_elements(By.XPATH, "./td|./th")))
        headers = [f"col_{i+1}" for i in range(longest)]

    records: List[Dict[str, Any]] = []
    start_idx = 1 if header_cells else 0
    for r in rows[start_idx:]:
        cells = r.find_elements(By.XPATH, "./td|./th")
        if not cells:
            continue
        values = [c.text.strip() for c in cells]
        row = {headers[i]: (values[i] if i < len(values) else "") for i in range(len(headers))}
        row["season_year"] = season_year
        row["source_url"] = source_url
        records.append(row)
    return records


def upsert_cbs_teams(engine: Engine, league_subdomain: str, sport: str, season_year: int, rows: List[Dict[str, Any]]):
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS cbs_teams (
                id BIGSERIAL PRIMARY KEY,
                league_subdomain TEXT NOT NULL,
                sport TEXT NOT NULL,
                season_year INTEGER NOT NULL,
                team_name TEXT,
                owner_name TEXT,
                raw JSONB NOT NULL,
                row_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        ))

        insert_sql = text(
            """
            INSERT INTO cbs_teams (league_subdomain, sport, season_year, team_name, owner_name, raw, row_hash)
            VALUES (:league_subdomain, :sport, :season_year, :team_name, :owner_name, CAST(:raw AS JSONB), :row_hash)
            ON CONFLICT (row_hash) DO NOTHING
            """
        )

        import hashlib
        to_insert = []
        for r in rows:
            team_name = r.get("TEAM") or r.get("Team") or r.get("Team Name") or ""
            owner = r.get("OWNER") or r.get("Owner") or r.get("Owner Name") or ""
            raw = json.dumps(r, sort_keys=True, ensure_ascii=False)
            h = hashlib.sha256()
            # Use full raw JSON for uniqueness so we don't collapse rows with empty team names
            h.update(league_subdomain.encode("utf-8"))
            h.update(b"|")
            h.update(sport.encode("utf-8"))
            h.update(b"|")
            h.update(str(season_year).encode("utf-8"))
            h.update(b"|")
            h.update(raw.encode("utf-8"))
            row_hash = h.hexdigest()

            to_insert.append({
                "league_subdomain": league_subdomain,
                "sport": sport,
                "season_year": season_year,
                "team_name": team_name,
                "owner_name": owner,
                "raw": raw,
                "row_hash": row_hash,
            })

        if to_insert:
            chunk = 1000
            for i in range(0, len(to_insert), chunk):
                conn.execute(insert_sql, to_insert[i:i+chunk])


def main():
    parser = argparse.ArgumentParser(description="Scrape CBS teams table for a given season")
    parser.add_argument("--league-id", required=True)
    parser.add_argument("--sport", default="hockey")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--login-wait", type=int, default=20)

    args = parser.parse_args()

    client = CBSSportsAuthenticated(args.league_id, args.sport, headless=False)
    driver = client.setup_driver()
    # Open base and wait for manual login
    driver.get(client.base_url)
    print(f"🔓 Please log in within {args.login_wait}s...")
    time.sleep(max(5, args.login_wait))

    # Go to teams and select season
    select_season_on_teams(driver, client.base_url, args.season)
    time.sleep(2)
    source_url = driver.current_url
    rows = parse_teams_table(driver, args.season, source_url)

    print(f"✅ Parsed {len(rows)} team rows for {args.season}")
    engine = create_engine(args.db_url, pool_pre_ping=True)
    upsert_cbs_teams(engine, args.league_id, args.sport, args.season, rows)
    print("📦 Saved to cbs_teams")

    # Keep the window open briefly
    time.sleep(2)

if __name__ == "__main__":
    main()


