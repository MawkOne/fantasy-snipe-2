#!/usr/bin/env python3
"""
Scrape CBS Sports league transactions across a year range using an authenticated session.

- Reuses CBSSportsAuthenticated (Selenium + requests session) to handle login
- Fetches transactions HTML for each year via:
  /transactions/all/all_but_lineup/{year}?print_rows=9999
- Parses the transactions table(s) into normalized JSON/CSV

Usage examples:
  python scripts/scrape_cbs_transactions.py \
    --league-id uhhp --sport hockey \
    --start-year 2015 --end-year 2024 \
    --output-json cbs_transactions_2015_2024.json \
    --output-csv cbs_transactions_2015_2024.csv \
    --use-saved-creds

  python scripts/scrape_cbs_transactions.py \
    --league-id uhhp --sport hockey \
    --start-year 2020 --end-year 2024 \
    --username you@example.com --password yourPassword
"""

import os
import sys
import csv
import json
import time
import argparse
from typing import List, Dict, Any, Optional

# Add project root to Python path for script imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import requests
from bs4 import BeautifulSoup
import hashlib

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

try:
    from cbs_sports_authenticated import CBSSportsAuthenticated
except Exception as e:
    print(f"❌ Unable to import CBSSportsAuthenticated: {e}")
    sys.exit(1)

# Credentials are optional; we prefer non-interactive flows
try:
    from cbs_credentials import CBSCredentials
except Exception:
    CBSCredentials = None  # Best-effort: script can still run with explicit creds


class CBSTransactionsScraper:
    """Scrape CBS transactions table(s) for a league across years."""

    def __init__(
        self,
        league_id: str,
        sport: str = "hockey",
        headless: bool = True,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_saved_creds: bool = False,
        manual_wait: bool = False,
        manual_wait_seconds: int = 600,
        manual_wait_fixed_seconds: Optional[int] = None,
    ) -> None:
        self.league_id = league_id
        self.sport = sport
        self.base_url = f"https://{league_id}.{sport}.cbssports.com"
        self.username = username
        self.password = password
        self.use_saved_creds = use_saved_creds
        self.manual_wait = manual_wait
        self.manual_wait_seconds = manual_wait_seconds
        self.manual_wait_fixed_seconds = manual_wait_fixed_seconds
        self.client = CBSSportsAuthenticated(league_id, sport, headless=headless)
        self.driver = None

    def login(self) -> bool:
        """Perform a non-interactive login if possible.

        Priority:
          1) Explicit username/password args
          2) Saved credentials (if available and requested)
          3) Return False (no interactive prompts in this script)
        """
        # Manual visible browser flow that detects login completion without terminal input
        if self.manual_wait:
            # Ensure visible browser
            if self.client.headless:
                # Recreate client with headless disabled
                self.client = CBSSportsAuthenticated(self.league_id, self.sport, headless=False)
            driver = self.client.setup_driver()
            self.driver = driver
            driver.get(self.base_url)
            print("\n🔓 A browser window opened. Please log in to CBS Sports.")
            # Simple fixed-wait mode (no detection). After the wait we proceed regardless.
            if self.manual_wait_fixed_seconds is not None:
                wait_s = max(5, int(self.manual_wait_fixed_seconds))
                print(f"⏳ Waiting {wait_s}s for manual login...")
                time.sleep(wait_s)
                # After wait, navigate to a protected league page to bind cookies to subdomain
                try:
                    driver.get(f"{self.base_url}/standings")
                    time.sleep(3)
                except Exception:
                    pass
                # Transfer cookies to requests session
                try:
                    for cookie in driver.get_cookies():
                        self.client.session.cookies.set(cookie['name'], cookie.get('value', ''))
                except Exception:
                    pass
                print("➡️ Proceeding with scraping.")
                return True

            print("We'll auto-detect when you're logged in.")
            start = time.time()
            timeout = max(60, int(self.manual_wait_seconds))  # seconds
            last_status = ""
            while time.time() - start < timeout:
                try:
                    current_url = driver.current_url.lower()
                    page_source = driver.page_source or ""

                    # Transfer cookies to requests session too (for optional requests fallback)
                    for cookie in driver.get_cookies():
                        self.client.session.cookies.set(cookie['name'], cookie.get('value', ''))

                    url_not_login = ('login' not in current_url and 'signin' not in current_url)
                    not_login_html = not self._looks_like_login_page(page_source)

                    # Separate probe using requests to a protected endpoint (won't disrupt your typing)
                    auth_ok = False
                    try:
                        probe = self.client.session.get(f"{self.base_url}/standings", timeout=10)
                        if probe.status_code == 200 and not self._looks_like_login_page(probe.text) and 'login' not in probe.url.lower():
                            auth_ok = True
                    except Exception:
                        auth_ok = False

                    if (url_not_login and not_login_html) or auth_ok:
                        print("✅ Login detected. Proceeding with scraping.")
                        return True
                    # Update status every few seconds
                    if int(time.time() - start) % 15 == 0 and last_status != str(int(time.time() - start)):
                        print(f"⏳ Waiting for login... {int(time.time() - start)}s / {timeout}s")
                        last_status = str(int(time.time() - start))
                    time.sleep(2)
                except Exception:
                    time.sleep(2)
            print(f"❌ Timed out waiting for manual login ({timeout} seconds).")
            return False

        # 1) Explicit credentials (non-interactive)
        if self.username and self.password:
            return self.client.login(self.username, self.password)

        # 2) Saved credentials if requested
        if self.use_saved_creds and CBSCredentials is not None:
            try:
                creds_mgr = CBSCredentials()
                saved_user, saved_pass = creds_mgr.load_credentials()
                if saved_user and saved_pass:
                    return self.client.login(saved_user, saved_pass)
            except Exception:
                pass

        # 3) No interactive fallback in this script
        return False

    def fetch_transactions_html(self, year: int) -> Optional[str]:
        """Fetch the transactions page HTML for a given year using the authenticated requests session."""
        url = f"{self.base_url}/transactions/all/all_but_lineup/{year}?print_rows=9999"
        # If we have a live driver (manual flow), prefer it to retain login state reliably
        if self.driver is not None:
            try:
                self.driver.get(url)
                time.sleep(3)
                html = self.driver.page_source or ""
                if html and not self._looks_like_login_page(html):
                    return html
            except Exception:
                return None
        # Fallback to requests session
        try:
            resp = self.client.session.get(url, timeout=20)
            if resp.status_code == 200 and not self._looks_like_login_page(resp.text):
                return resp.text
            return None
        except Exception:
            return None

    def parse_transactions_from_driver(self, year: int, source_url: str) -> List[Dict[str, Any]]:
        """Parse transactions directly from the live Selenium driver DOM for higher reliability."""
        if self.driver is None:
            return []
        try:
            # Import only when needed
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import NoSuchElementException
        except Exception:
            return []

        records: List[Dict[str, Any]] = []
        try:
            # Try to find the main transactions table: pick the table with the most rows
            tables = self.driver.find_elements(By.TAG_NAME, "table")
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
            # Header
            header_cells = rows[0].find_elements(By.XPATH, "./th|./td") if rows else []
            if header_cells:
                headers = [c.text.strip() or f"col_{i+1}" for i, c in enumerate(header_cells)]
            else:
                # Synthesize headers from the longest data row
                longest = 0
                for r in rows:
                    longest = max(longest, len(r.find_elements(By.XPATH, "./td|./th")))
                headers = [f"col_{i+1}" for i in range(longest)]

            start_idx = 1 if header_cells else 0
            for r in rows[start_idx:]:
                cells = r.find_elements(By.XPATH, "./td|./th")
                if not cells:
                    continue
                values: List[str] = [c.text.strip() for c in cells]

                # Align
                row_obj: Dict[str, Any] = {}
                for i, header in enumerate(headers):
                    row_obj[header] = values[i] if i < len(values) else ""
                row_obj["year"] = year
                row_obj["source_url"] = source_url
                records.append(row_obj)
        except Exception:
            return []
        return records

    @staticmethod
    def _looks_like_login_page(html: str) -> bool:
        # Heuristic to detect login form content
        lowered = html.lower()
        return (
            ("log in" in lowered or "login" in lowered or "sign in" in lowered) and
            ("password" in lowered or "continue with" in lowered)
        )

    def parse_transactions_html(self, html: str, year: int, source_url: str) -> List[Dict[str, Any]]:
        """Parse transactions tables from HTML into a list of records.

        Strategy:
          - Find all tables; choose the one with the most data rows
          - Use <th> as headers if present; else synthesize headers
          - Extract text and any links present per cell
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            return []

        # Choose the largest table by number of rows (excluding header)
        def table_data_rows_count(tbl) -> int:
            rows = tbl.find_all('tr')
            return max(0, len(rows) - 1)

        target_table = max(tables, key=table_data_rows_count)
        rows = target_table.find_all('tr')
        if not rows:
            return []

        # Header extraction
        headers: List[str] = []
        header_cells = rows[0].find_all(['th', 'td'])
        if header_cells and any(h.get_text(strip=True) for h in header_cells):
            headers = [h.get_text(strip=True) or f"col_{i+1}" for i, h in enumerate(header_cells)]
        else:
            # No headers; synthesize based on max cell count observed
            max_cols = 0
            for r in rows:
                max_cols = max(max_cols, len(r.find_all(['td', 'th'])))
            headers = [f"col_{i+1}" for i in range(max_cols)]

        records: List[Dict[str, Any]] = []
        # Start from 1 if first row is header with <th>
        start_idx = 1 if header_cells and rows[0].find_all('th') else 0

        for r in rows[start_idx:]:
            cells = r.find_all(['td', 'th'])
            if not cells:
                continue

            values: List[str] = []
            links: List[Dict[str, str]] = []

            for c in cells:
                # Cell text
                text = c.get_text(" ", strip=True)
                values.append(text)

                # Capture any links in this cell
                for a in c.find_all('a', href=True):
                    href = a['href']
                    label = a.get_text(strip=True) or href
                    links.append({"label": label, "href": href})

            # Align values -> headers
            row_obj: Dict[str, Any] = {}
            for i, header in enumerate(headers):
                row_obj[header] = values[i] if i < len(values) else ""

            if links:
                row_obj["_links"] = links

            row_obj["year"] = year
            row_obj["source_url"] = source_url
            records.append(row_obj)

        return records

    def scrape_years(self, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """Scrape transactions for each year in [start_year, end_year]."""
        all_records: List[Dict[str, Any]] = []
        for year in range(start_year, end_year + 1):
            url = f"{self.base_url}/transactions/all/all_but_lineup/{year}?print_rows=9999"
            html = self.fetch_transactions_html(year)
            if not html:
                # Skip if not accessible (likely not logged in)
                continue
            year_records = self.parse_transactions_html(html, year, url)
            all_records.extend(year_records)
            # Be polite
            time.sleep(0.5)
        return all_records


def write_json(path: str, data: Any) -> None:
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(path: str, records: List[Dict[str, Any]]) -> None:
    if not records:
        # Create an empty file with no rows
        with open(path, 'w', newline='') as f:
            pass
        return

    # Collect union of all keys to ensure wide CSV
    fieldnames: List[str] = []
    seen = set()
    for rec in records:
        for k in rec.keys():
            if k not in seen and k != "_links":
                seen.add(k)
                fieldnames.append(k)
    # Make _links the last column if present
    has_links = any("_links" in r for r in records)
    if has_links:
        fieldnames.append("_links")

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = {k: v for k, v in rec.items() if k in fieldnames}
            # Serialize links to a compact string
            if "_links" in rec:
                row["_links"] = "; ".join([f"{l.get('label','')}|{l.get('href','')}" for l in rec["_links"]])
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Scrape CBS Sports league transactions across years")
    parser.add_argument("--league-id", required=True, help="CBS Sports league subdomain (e.g., uhhp)")
    parser.add_argument("--sport", default="hockey", help="Sport subdomain (default: hockey)")
    parser.add_argument("--start-year", type=int, required=True, help="Start year (inclusive)")
    parser.add_argument("--end-year", type=int, required=True, help="End year (inclusive)")
    parser.add_argument("--only-year", type=int, help="Scrape a single year; overrides start/end")
    parser.add_argument("--output-json", help="Path to output JSON file")
    parser.add_argument("--output-csv", help="Path to output CSV file")
    parser.add_argument("--db-url", help="PostgreSQL URL to write into (e.g., postgresql://...)")
    parser.add_argument("--db-table", default="transactions", help="Target table name (default: transactions)")
    parser.add_argument("--username", help="CBS Sports username/email")
    parser.add_argument("--password", help="CBS Sports password")
    parser.add_argument("--use-saved-creds", action="store_true", help="Use saved credentials if available (non-interactive)")
    parser.add_argument("--manual-wait", action="store_true", help="Open a visible browser and wait up to 3 minutes for manual login")
    parser.add_argument("--no-headless", action="store_true", help="Run Selenium with a visible browser window")
    parser.add_argument("--manual-wait-seconds", type=int, default=600, help="Seconds to wait for manual login (default: 600)")
    parser.add_argument("--manual-wait-fixed-seconds", type=int, help="Fixed seconds to wait for manual login before scraping")

    args = parser.parse_args()

    # Normalize year range
    if args.only_year:
        args.start_year = args.only_year
        args.end_year = args.only_year

    scraper = CBSTransactionsScraper(
        league_id=args.league_id,
        sport=args.sport,
        headless=not (args.no_headless or args.manual_wait),
        username=args.username,
        password=args.password,
        use_saved_creds=args.use_saved_creds,
        manual_wait=args.manual_wait,
        manual_wait_seconds=args.manual_wait_seconds,
        manual_wait_fixed_seconds=args.manual_wait_fixed_seconds,
    )

    # Non-interactive login only
    logged_in = scraper.login()
    if not logged_in:
        print("❌ Login failed or no credentials provided. Provide --username/--password or --use-saved-creds.")
        sys.exit(2)

    # If we have a live browser, prefer DOM parsing for reliability
    records: List[Dict[str, Any]] = []
    if scraper.driver is not None and args.start_year == args.end_year:
        y = args.start_year
        url = f"{scraper.base_url}/transactions/all/all_but_lineup/{y}?print_rows=9999"
        try:
            scraper.driver.get(url)
            time.sleep(3)
        except Exception:
            pass
        # Parse via DOM
        records = scraper.parse_transactions_from_driver(y, url)
        # Fallback to HTML fetch if empty
        if not records:
            html = scraper.fetch_transactions_html(y)
            if html:
                records = scraper.parse_transactions_html(html, y, url)
    else:
        records = scraper.scrape_years(args.start_year, args.end_year)
    summary = {
        "league_id": args.league_id,
        "sport": args.sport,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "record_count": len(records),
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Optional: write to Postgres
    if args.db_url and records:
        engine: Engine = create_engine(args.db_url, pool_pre_ping=True)
        with engine.begin() as conn:
            # Support two table shapes:
            # 1) Generic staging (league_id, sport, year, source_url, row, row_hash)
            # 2) cbs_transactions (league_subdomain, sport, season_year, source_url, row, row_hash)

            is_cbs_transactions = args.db_table.strip().lower() == "cbs_transactions"

            if not is_cbs_transactions:
                # Create generic staging if not present
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {args.db_table} (
                        id BIGSERIAL PRIMARY KEY,
                        league_id TEXT NOT NULL,
                        sport TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        source_url TEXT NOT NULL,
                        row JSONB NOT NULL,
                        row_hash TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                """))

            if is_cbs_transactions:
                insert_sql = text(f"""
                    INSERT INTO {args.db_table} (league_subdomain, sport, season_year, source_url, row, row_hash)
                    VALUES (:league_subdomain, :sport, :season_year, :source_url, CAST(:row AS JSONB), :row_hash)
                    ON CONFLICT (row_hash) DO NOTHING
                """)
            else:
                insert_sql = text(f"""
                    INSERT INTO {args.db_table} (league_id, sport, year, source_url, row, row_hash)
                    VALUES (:league_id, :sport, :year, :source_url, CAST(:row AS JSONB), :row_hash)
                    ON CONFLICT (row_hash) DO NOTHING
                """)

            # Prepare and insert rows
            batch = []
            for rec in records:
                row_obj = {
                    k: v for k, v in rec.items()
                    if k not in ("year", "source_url")
                }
                row_json = json.dumps(row_obj, sort_keys=True, ensure_ascii=False)
                h = hashlib.sha256()
                h.update(args.league_id.encode("utf-8"))
                h.update(b"|")
                h.update(args.sport.encode("utf-8"))
                h.update(b"|")
                h.update(str(rec.get("year")).encode("utf-8"))
                h.update(b"|")
                h.update(row_json.encode("utf-8"))
                row_hash = h.hexdigest()

                if is_cbs_transactions:
                    batch.append({
                        "league_subdomain": args.league_id,
                        "sport": args.sport,
                        "season_year": rec.get("year"),
                        "source_url": rec.get("source_url"),
                        "row": row_json,
                        "row_hash": row_hash,
                    })
                else:
                    batch.append({
                        "league_id": args.league_id,
                        "sport": args.sport,
                        "year": rec.get("year"),
                        "source_url": rec.get("source_url"),
                        "row": row_json,
                        "row_hash": row_hash,
                    })

            chunk_size = 1000
            for i in range(0, len(batch), chunk_size):
                conn.execute(insert_sql, batch[i:i+chunk_size])

        print(f"📦 Loaded {len(records)} records into {args.db_table}")

    if args.output_json:
        write_json(args.output_json, {"summary": summary, "records": records})
        print(f"📄 Wrote JSON: {args.output_json} ({len(records)} records)")

    if args.output_csv:
        write_csv(args.output_csv, records)
        print(f"📄 Wrote CSV:  {args.output_csv} ({len(records)} records)")

    if not args.output_json and not args.output_csv:
        # Print to stdout if no output paths provided
        print(json.dumps({"summary": summary, "records": records}, indent=2))


if __name__ == "__main__":
    main()


