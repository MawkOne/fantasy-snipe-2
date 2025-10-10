#!/usr/bin/env python3
import os
import time
import json
import re
from typing import Any, Dict, List, Optional

import psycopg
import requests
from bs4 import BeautifulSoup

DSN = os.getenv("FANTASY_DATABASE_URL")
POLL_SEC = int(os.getenv("SYNC_POLL_SECONDS", "30"))
BATCH = int(os.getenv("SYNC_BATCH", "5"))
BACKEND_IMPORT_URL = os.getenv("BACKEND_IMPORT_URL")  # e.g. https://fastapi.../api/inseason/cbs/import
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")

TARGET_URLS = [
    "https://uhhp.hockey.cbssports.com/rules",
    "https://uhhp.hockey.cbssports.com/details/teams-managers",
    "https://uhhp.hockey.cbssports.com/teams/all",
    "https://uhhp.hockey.cbssports.com/stats/stats-main/all:C:W:F:D/restofseason:p/standard/projections?print_rows=9999",
]

def _headers() -> Dict[str, str]:
    return {"User-Agent": "Mozilla/5.0 (compatible; ProviderSync/1.0)"}

def _parse_tables(html: str) -> List[Dict[str, Any]]:
    tables_out: List[Dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for tbl in soup.find_all("table"):
        headers: List[str] = []
        # header detection
        thead = tbl.find("thead")
        if thead and thead.find_all("th"):
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]
        else:
            first_tr = tbl.find("tr")
            if first_tr:
                headers = [td.get_text(strip=True) for td in first_tr.find_all(["th", "td"])]
        rows_data: List[Dict[str, Any]] = []
        for tr in tbl.find_all("tr"):
            cells = tr.find_all(["td", "th"]) if headers else tr.find_all("td")
            if not cells:
                continue
            vals = [c.get_text(strip=True) for c in cells]
            if headers and len(vals) == len(headers):
                row = {headers[i]: vals[i] for i in range(len(headers))}
            else:
                # fallback positional
                row = {f"col_{i}": v for i, v in enumerate(vals)}
            # try to extract cbs_player_id from any anchor
            pid: Optional[str] = None
            a = tr.find("a", href=True)
            if a and a["href"]:
                m = re.search(r"pid=(\d+)", a["href"]) or re.search(r"/player/(\d+)", a["href"])  # heuristic
                if m:
                    pid = m.group(1)
            if pid:
                row["cbs_player_id"] = pid
                # also record name if present
                if "Player" not in row and a:
                    row["Player"] = a.get_text(strip=True)
            rows_data.append(row)
        if headers or rows_data:
            tables_out.append({"headers": headers, "rows": rows_data})
    return tables_out

def _build_session_from_secret(secret_ref: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(_headers())
    # secret_ref expected as JSON: {"cookies": {"name": "value", ...}} or raw Cookie header string
    try:
        obj = json.loads(secret_ref)
        cookies = obj.get("cookies") if isinstance(obj, dict) else None
        if isinstance(cookies, dict):
            for k, v in cookies.items():
                s.cookies.set(k, str(v))
    except Exception:
        # treat as raw cookie header string
        if secret_ref and "=" in secret_ref:
            s.headers["Cookie"] = secret_ref
    return s

def _post_import(payload: Dict[str, Any]) -> None:
    if not BACKEND_IMPORT_URL:
        print("BACKEND_IMPORT_URL not set; skipping import POST")
        return
    headers = {"Content-Type": "application/json"}
    if BACKEND_API_KEY:
        headers["x-api-key"] = BACKEND_API_KEY
    try:
        resp = requests.post(BACKEND_IMPORT_URL, headers=headers, data=json.dumps(payload), timeout=60)
        if not resp.ok:
            print(f"import POST failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"import POST error: {e}")

def process_run(conn, run_id: int) -> None:
    # Implement CBS sync: fetch pages using stored cookies, parse tables, post to backend import
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, provider_id FROM provider_sync_runs WHERE id=%s FOR UPDATE",
            (run_id,),
        )
        row = cur.fetchone()
        if not row:
            return
        user_id, provider_id = row
        # find provider slug
        cur.execute("SELECT slug FROM providers WHERE id=%s", (provider_id,))
        p = cur.fetchone()
        slug = (p[0] if p else None) or ""
        if slug.lower() != "cbs":
            cur.execute(
                "UPDATE provider_sync_runs SET status='completed', completed_at=now(), meta = COALESCE(meta,'{}'::jsonb) || '{""note"": ""provider not supported""}'::jsonb WHERE id=%s",
                (run_id,),
            )
            return
        cur.execute(
            "SELECT login, secret_ref FROM provider_accounts WHERE user_id=%s AND provider_id=%s ORDER BY last_verified_at DESC NULLS LAST, id DESC LIMIT 1",
            (user_id, provider_id),
        )
        acct = cur.fetchone()
        if not acct:
            cur.execute(
                "UPDATE provider_sync_runs SET status='failed', completed_at=now(), meta = COALESCE(meta,'{}'::jsonb) || '{""error"": ""no account""}'::jsonb WHERE id=%s",
                (run_id,),
            )
            return
        login, secret_ref = acct
        sess = _build_session_from_secret(secret_ref or "")
        pages: List[Dict[str, Any]] = []
        for url in TARGET_URLS:
            try:
                r = sess.get(url, timeout=30)
                if r.status_code != 200:
                    continue
                tables = _parse_tables(r.text)
                if tables:
                    pages.append({"ok": True, "url": url, "title": "", "tables": tables})
            except Exception as e:
                print(f"fetch error {url}: {e}")
        if pages:
            payload = {"exportedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pages": pages}
            _post_import(payload)
        cur.execute(
            "UPDATE provider_sync_runs SET status='completed', completed_at=now(), meta = COALESCE(meta,'{}'::jsonb) || '{""note"": ""cbs sync done""}'::jsonb WHERE id=%s",
            (run_id,),
        )


def main() -> None:
    if not DSN:
        print("FANTASY_DATABASE_URL not set")
        raise SystemExit(1)
    while True:
        try:
            with psycopg.connect(DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id FROM provider_sync_runs
                         WHERE status IS NULL OR status = 'queued'
                         ORDER BY started_at ASC
                         LIMIT %s
                        """,
                        (BATCH,),
                    )
                    rows = cur.fetchall()
                for (run_id,) in rows:
                    with conn.transaction():
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE provider_sync_runs SET status='running' WHERE id=%s AND (status IS NULL OR status='queued')",
                                (run_id,),
                            )
                        process_run(conn, int(run_id))
        except Exception as e:
            print(f"sync loop error: {e}")
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()
