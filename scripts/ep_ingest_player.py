import argparse
import re
import time
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery


BASE = "https://www.eliteprospects.com"


def _get(url: str) -> str:
    for attempt in range(3):
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; NHL-API/1.0)"
        })
        if r.status_code == 404:
            return ""
        if 500 <= r.status_code < 600:
            time.sleep(1 + attempt)
            continue
        r.raise_for_status()
        return r.text
    return ""


def _find_player_profile(search_name: str) -> Optional[str]:
    q = requests.utils.quote(search_name)
    url = f"{BASE}/search/player?q={q}"
    html = _get(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("a[href^='/player/']")
    if not link:
        return None
    href = link.get("href")
    if not href:
        return None
    return requests.compat.urljoin(BASE, href)


def _parse_profile(url: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    html = _get(url)
    if not html:
        return {}, [], []
    soup = BeautifulSoup(html, "html.parser")

    # Basic header
    name = (soup.select_one("h1.player-name") or soup.select_one("h1"))
    full_name = name.get_text(strip=True) if name else None
    # Extract DOB if present
    dob = None
    for el in soup.select(".player-bio li"):
        txt = el.get_text(" ", strip=True)
        if "born" in txt.lower():
            m = re.search(r"(\d{4}-\d{2}-\d{2})", txt)
            if m:
                dob = m.group(1)
                break

    # Robust table parsing: detect headers and pull indices by name
    def extract_rows_from_table(table, scope_hint: Optional[str]) -> Tuple[str, List[Dict]]:
        rows_out: List[Dict] = []
        scope = scope_hint or "regular"
        # Try to infer scope from nearby caption/heading
        caption = table.find("caption")
        if caption:
            cap = caption.get_text(" ", strip=True).lower()
            if "playoff" in cap:
                scope = "playoffs"
            elif "regular" in cap:
                scope = "regular"
        # Header mapping
        header_cells = [th.get_text(" ", strip=True).lower() for th in table.select("thead th")]
        if not header_cells:
            thead = table.find("thead")
            if thead:
                header_cells = [th.get_text(" ", strip=True).lower() for th in thead.find_all("th")]
        def col_idx(names: List[str]) -> Optional[int]:
            for name in names:
                if name in header_cells:
                    return header_cells.index(name)
            return None
        idx_season = col_idx(["season"]) or 0
        idx_team = col_idx(["team"]) or 1
        idx_league = col_idx(["league"]) or 2
        idx_gp = col_idx(["gp", "games", "games played"]) or 3
        idx_g = col_idx(["g", "goals"]) or 4
        idx_a = col_idx(["a", "assists"]) or 5
        idx_pts = col_idx(["pts", "tp", "points"]) or 6
        idx_pim = col_idx(["pim"]) or None

        for tr in table.select("tbody tr"):
            tds = tr.find_all("td")
            if not tds or len(tds) < 4:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]
            try:
                season = cells[idx_season] if idx_season is not None and idx_season < len(cells) else None
                team = cells[idx_team] if idx_team is not None and idx_team < len(cells) else None
                league = cells[idx_league] if idx_league is not None and idx_league < len(cells) else None
                gp = cells[idx_gp] if idx_gp is not None and idx_gp < len(cells) else None
                g = cells[idx_g] if idx_g is not None and idx_g < len(cells) else None
                a = cells[idx_a] if idx_a is not None and idx_a < len(cells) else None
                pts = cells[idx_pts] if idx_pts is not None and idx_pts < len(cells) else None
                pim = cells[idx_pim] if (idx_pim is not None and idx_pim < len(cells)) else None
            except Exception:
                continue
            # Basic guards to avoid header/subtotal rows
            if not season or season.lower() in {"season", "total", "career"}:
                continue
            rows_out.append({
                "season": season,
                "team": team,
                "league": league,
                "gp": _as_int(gp),
                "g": _as_int(g),
                "a": _as_int(a),
                "pts": _as_int(pts),
                "pim": _as_int(pim),
                "scope": scope,
            })
        return scope, rows_out

    # Collect candidate tables (regular + playoffs often share structure)
    candidate_tables = []
    candidate_tables += soup.select("table#player-stats-regular, table#player-stats-playoffs")
    candidate_tables += soup.select("table.table-player-career-regular, table.table-player-career-playoffs")
    if not candidate_tables:
        candidate_tables += soup.select("table")

    regular_rows: List[Dict] = []
    playoff_rows: List[Dict] = []
    for tbl in candidate_tables:
        scope, rows = extract_rows_from_table(tbl, None)
        if not rows:
            continue
        if scope == "playoffs":
            playoff_rows.extend({k: v for k, v in row.items() if k != "scope"} for row in rows)
        else:
            regular_rows.extend({k: v for k, v in row.items() if k != "scope"} for row in rows)

    meta = {
        "full_name": full_name,
        "dob": dob,
        "profile_url": url,
    }
    return meta, regular_rows, playoff_rows


def _as_int(x: Optional[str]) -> Optional[int]:
    try:
        return int(str(x).replace(" ", "")) if x not in (None, "", "-") else None
    except Exception:
        return None


def _load_bq(player_meta: Dict, reg: List[Dict], po: List[Dict], client: bigquery.Client) -> None:
    dataset = "fantasy-snipe-ai.nhl_external"
    client.query(f"CREATE SCHEMA IF NOT EXISTS `{dataset}`").result()

    # Upsert player
    players_tbl = f"{dataset}.ep_players"
    client.query(
        f"CREATE TABLE IF NOT EXISTS `{players_tbl}` (full_name STRING, dob DATE, profile_url STRING)"
    ).result()
    client.load_table_from_json([
        {"full_name": player_meta.get("full_name"), "dob": player_meta.get("dob"), "profile_url": player_meta.get("profile_url")}
    ], players_tbl, job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)).result()

    # Season stats
    stats_tbl = f"{dataset}.ep_player_season_stats"
    client.query(
        f"CREATE TABLE IF NOT EXISTS `{stats_tbl}` (full_name STRING, dob DATE, profile_url STRING, season STRING, league STRING, team STRING, gp INT64, g INT64, a INT64, pts INT64, pim INT64, scope STRING)"
    ).result()

    payload: List[Dict] = []
    for row in reg:
        payload.append({**player_meta, **row, "scope": "regular"})
    for row in po:
        payload.append({**player_meta, **row, "scope": "playoffs"})

    if payload:
        client.load_table_from_json(
            payload,
            stats_tbl,
            job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND),
        ).result()


def main(player_name: str, profile_url: Optional[str]) -> None:
    if not profile_url:
        profile_url = _find_player_profile(player_name)
        if not profile_url:
            print("Profile not found")
            return
    meta, reg, po = _parse_profile(profile_url)
    if not meta:
        print("Failed to parse profile")
        return
    client = bigquery.Client()
    _load_bq(meta, reg, po, client)
    print(f"Loaded EP stats for {meta.get('full_name')} with {len(reg)} regular and {len(po)} playoff rows.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Player full name, e.g., Connor McDavid")
    p.add_argument("--profile-url", default=None, help="Optional direct EP profile URL")
    args = p.parse_args()
    main(args.name, args.profile_url)


