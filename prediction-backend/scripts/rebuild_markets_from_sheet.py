import os
import sys
import csv
import io
import re
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

SHEET_ID = "1cDs2scPDrPP1FtUz_lVN9P_s9LCwoMtGJUp4WqjhqQ4"
TABS = [
    ("Pts", "Z", "PTS"),
    ("Goals", "AA", "G"),
    ("Assists", "AB", "A"),
]


def db_url() -> str:
    url = os.environ.get("MARKET_DATABASE_URL") or os.environ.get("DATABASE_URL")
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


def parse_number(s: str) -> float:
    t = re.sub(r"[^0-9.\-]", "", s or "")
    try:
        return float(t) if t else 0.0
    except Exception:
        return 0.0


def col_letter_to_index(letter: str) -> int:
    # Convert Excel-style column letters to 0-based index (A=0, Z=25, AA=26, AB=27, ...)
    letter = (letter or "").strip().upper()
    total = 0
    for ch in letter:
        if not ('A' <= ch <= 'Z'):
            return -1
        total = total * 26 + (ord(ch) - ord('A') + 1)
    return total - 1  # zero-based


def rebuild():
    conn = psycopg2.connect(db_url(), cursor_factory=RealDictCursor)
    try:
        with conn:
            with conn.cursor() as cur:
                # wipe existing markets and cascading outcomes/inventory/trades
                cur.execute("DELETE FROM markets")
                created = 0
                for tab_name, value_col, metric in TABS:
                    rows = fetch_sheet(SHEET_ID, tab_name)
                    # prepare header order for index lookup
                    headers = []
                    if rows:
                        headers = list(rows[0].keys())
                    idx = col_letter_to_index(value_col)
                    # prefer named columns if present
                    metric_name_candidates = {
                        "PTS": ["PTS", "Pts", "Points", " PTS"],
                        "G": ["G", "Goals", " G"],
                        "A": ["A", "Assists", " A"],
                    }.get(metric, [metric])
                    named_key = None
                    for cand in metric_name_candidates:
                        if cand in headers:
                            named_key = cand
                            break
                    # Expect columns: Player, Team, and Z/AA/AB value columns
                    # Sort by requested value column desc, pick top 12
                    ranked = []
                    for r in rows:
                        player = (r.get("Player") or "").strip()
                        if not player:
                            continue
                        # Prefer named metric column
                        if named_key is not None:
                            val = parse_number(r.get(named_key))
                        # Else by letter index if available
                        elif 0 <= idx < len(headers):
                            key = headers[idx]
                            val = parse_number(r.get(key))
                        else:
                            # fallback: try by exact letter name (unlikely) or metric key
                            val = parse_number(r.get(value_col) or r.get(metric) or r.get(metric.upper()))
                        ranked.append((player, val, r))
                    ranked.sort(key=lambda x: x[1], reverse=True)
                    top = ranked[:20]
                    for rank, (player, val, r) in enumerate(top, start=1):
                        thr = float(int(val)) + 0.5
                        slug = f"{metric.lower()}-r{rank}-{player.lower().replace(' ', '-') }"
                        title = f"{player} — Top 12 {tab_name} (rank {rank})"
                        title = title.replace("Top 12", "Top 20")
                        description = f"Auto-generated from {tab_name} tab. Projection={val}, line={thr}"
                        # create market
                        team = (r.get("Team") or r.get("TEAM") or "").strip()
                        cur.execute(
                            """
                            INSERT INTO markets (slug, title, description, outcome_type, status, b, player_name, metric, threshold, category, sub_category, timeframe, team, volume_total)
                            VALUES (%s,%s,%s,'binary','open',%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            RETURNING id
                            """,
                            (slug, title, description, 50, player, metric, thr, 'Players', tab_name, 'Season', team, 0),
                        )
                        mid = cur.fetchone()["id"]
                        cur.execute("INSERT INTO market_outcomes (market_id, outcome) VALUES (%s,'yes'),(%s,'no')", (mid, mid))
                        cur.execute("INSERT INTO amm_inventory (market_id, outcome, shares) VALUES (%s,'yes',0),(%s,'no',0)", (mid, mid))
                        created += 1
                print(f"Rebuilt markets: {created}")
    finally:
        conn.close()


if __name__ == "__main__":
    rebuild()


