import os
import sys
import csv
import io
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor, Json


SHEET_ID = "1cDs2scPDrPP1FtUz_lVN9P_s9LCwoMtGJUp4WqjhqQ4"
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")


def db_url() -> str:
    url = os.environ.get("MARKET_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("NHL_DATABASE_URL")
    if not url:
        print("Set MARKET_DATABASE_URL", file=sys.stderr)
        sys.exit(1)
    return url


def fetch_sheet(sheet_id: str, sheet_name: str) -> list[dict[str, str]]:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        alt = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&sheet={sheet_name}"
        resp = requests.get(alt, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch sheet CSV: HTTP {resp.status_code}")
    content = resp.content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def main():
    rows = fetch_sheet(SHEET_ID, SHEET_NAME)
    conn = psycopg2.connect(db_url(), cursor_factory=RealDictCursor)
    try:
        with conn:
            with conn.cursor() as cur:
                # simple upsert by (source_id, sheet_name, row_index)
                for i, r in enumerate(rows, start=1):
                    cur.execute(
                        """
                        INSERT INTO player_projections (source_id, sheet_name, row_index, data)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (SHEET_ID, SHEET_NAME, i, Json(r)),
                    )
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM player_projections WHERE source_id=%s AND sheet_name=%s", (SHEET_ID, SHEET_NAME))
            n = cur.fetchone()["count"]
            print(f"Ingested rows: {n}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


