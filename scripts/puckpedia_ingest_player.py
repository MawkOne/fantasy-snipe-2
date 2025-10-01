import argparse
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery

try:
    import cloudscraper  # type: ignore
except Exception:  # pragma: no cover
    cloudscraper = None  # lazy optional import

try:
    from playwright.sync_api import sync_playwright  # type: ignore
    try:
        from playwright_stealth import stealth_sync  # type: ignore
    except Exception:
        stealth_sync = None  # type: ignore
except Exception:  # pragma: no cover
    sync_playwright = None  # type: ignore
    stealth_sync = None  # type: ignore


PUCKPEDIA_BASE = "https://puckpedia.com"


@dataclass
class PuckPediaPlayer:
    url: str
    player_name: Optional[str]
    shoots: Optional[str]
    height: Optional[str]
    weight_lb: Optional[int]
    birthdate: Optional[str]
    birthplace: Optional[str]
    position: Optional[str]


@dataclass
class PuckPediaSeasonStat:
    url: str
    season: Optional[str]
    team: Optional[str]
    league: Optional[str]
    gp: Optional[int]
    g: Optional[int]
    a: Optional[int]
    pts: Optional[int]
    pim: Optional[int]
    age: Optional[int]
    aav_usd: Optional[int]
    cap_hit_usd: Optional[int]
    toi_seconds: Optional[int]
    is_playoffs: Optional[bool]
    notes: Optional[str]
    extras: Optional[str]


@dataclass
class PuckPediaContract:
    url: str
    signing_date: Optional[str]
    term_years: Optional[int]
    aav_usd: Optional[int]
    total_value_usd: Optional[int]
    clauses: Optional[str]
    details: Optional[str]


def _to_int(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    s = s.strip().replace(",", "")
    m = re.match(r"^-?\d+", s)
    return int(m.group(0)) if m else None


def _clean_text(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def ensure_bq_tables(client: bigquery.Client) -> None:
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_external`").result()

    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_external.puckpedia_players` (
          url STRING,
          player_name STRING,
          shoots STRING,
          height STRING,
          weight_lb INT64,
          birthdate STRING,
          birthplace STRING,
          position STRING
        )
        """
    ).result()

    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_external.puckpedia_player_season_stats` (
          url STRING,
          season STRING,
          team STRING,
          league STRING,
          gp INT64,
          g INT64,
          a INT64,
          pts INT64,
          pim INT64,
          age INT64,
          aav_usd INT64,
          cap_hit_usd INT64,
          toi_seconds INT64,
          is_playoffs BOOL,
          notes STRING,
          extras STRING
        )
        """
    ).result()

    # Add missing columns if table already exists
    for col, typ in [
        ("age", "INT64"),
        ("aav_usd", "INT64"),
        ("cap_hit_usd", "INT64"),
        ("toi_seconds", "INT64"),
        ("is_playoffs", "BOOL"),
        ("notes", "STRING"),
        ("extras", "STRING"),
    ]:
        try:
            client.query(f"ALTER TABLE `fantasy-snipe-ai.nhl_external.puckpedia_player_season_stats` ADD COLUMN IF NOT EXISTS {col} {typ}").result()
        except Exception:
            pass

    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_external.puckpedia_contracts` (
          url STRING,
          signing_date STRING,
          term_years INT64,
          aav_usd INT64,
          total_value_usd INT64,
          clauses STRING,
          details STRING
        )
        """
    ).result()


def fetch_html(session: requests.Session, url: str) -> BeautifulSoup:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": PUCKPEDIA_BASE + "/",
    }
    resp = session.get(url, headers=headers, timeout=30)
    if resp.status_code == 403 and cloudscraper is not None:
        scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "linux", "mobile": False})
        resp = scraper.get(url, headers=headers, timeout=30)
    if resp.status_code == 403 and sync_playwright is not None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=headers["User-Agent"],
                locale="en-US",
                viewport={"width": 1366, "height": 768},
            )
            page = context.new_page()
            if stealth_sync is not None:
                try:
                    stealth_sync(page)
                except Exception:
                    pass
            page.goto(url, wait_until="networkidle")
            html = page.content()
            browser.close()
        return BeautifulSoup(html, "html.parser")
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_profile(soup: BeautifulSoup, url: str) -> PuckPediaPlayer:
    # Player name
    name_tag = soup.select_one("h1")
    player_name = _clean_text(name_tag.get_text()) if name_tag else None

    position: Optional[str] = None
    shoots: Optional[str] = None
    height: Optional[str] = None
    weight_lb: Optional[int] = None
    birthdate: Optional[str] = None
    birthplace: Optional[str] = None

    # 1) Try JSON-LD blocks for structured person data
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text())
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") in ("Person", ["Person"]):
            height = height or _clean_text(data.get("height"))
            weight_lb = weight_lb or _to_int(str(data.get("weight") or "").replace("lb", ""))
            birthdate = birthdate or _clean_text(data.get("birthDate"))
            bp = data.get("birthPlace")
            if isinstance(bp, dict):
                birthplace = birthplace or _clean_text(bp.get("name"))
            elif isinstance(bp, str):
                birthplace = birthplace or _clean_text(bp)
            position = position or _clean_text(data.get("jobTitle"))

    # 2) Heuristic extraction from page text
    page_text = soup.get_text(" ", strip=True)
    m = re.search(r"Shoots:?\s*(Left|Right)", page_text, re.I)
    if m:
        shoots = shoots or m.group(1).title()
    m = re.search(r"Position:?\s*([A-Za-z/\-\s]+)", page_text, re.I)
    if m:
        position = position or _clean_text(m.group(1))
    m = re.search(r"Height:?\s*([0-9]'\s*\d{1,2}\"?)", page_text, re.I)
    if m:
        height = height or m.group(1).replace(" ", "")
    m = re.search(r"Weight:?\s*(\d+)\s*lbs?", page_text, re.I)
    if m:
        weight_lb = weight_lb or _to_int(m.group(1))
    m = re.search(r"Born:?\s*([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})", page_text)
    if m:
        birthdate = birthdate or _clean_text(m.group(1))
    m = re.search(r"Birth(?:place)?\s*:?\s*([A-Za-z.\-\s']+,\s*[A-Za-z.\-\s']+)", page_text)
    if m:
        birthplace = birthplace or _clean_text(m.group(1))

    return PuckPediaPlayer(
        url=url,
        player_name=player_name,
        shoots=shoots,
        height=height,
        weight_lb=weight_lb,
        birthdate=birthdate,
        birthplace=birthplace,
        position=position,
    )


def parse_season_stats(soup: BeautifulSoup, url: str) -> List[PuckPediaSeasonStat]:
    rows: List[PuckPediaSeasonStat] = []
    # Look for stats tables; PuckPedia markup varies. Collect plausible tables.
    for table in soup.select("table"):
        headers = [h.get_text(" ", strip=True).upper() for h in table.select("thead th")]
        if not headers:
            # Try first row as header if no thead
            headers = [h.get_text(" ", strip=True).upper() for h in table.select("tr:first-child th, tr:first-child td")]
        if not headers:
            continue
        # Require basic stat columns
        must = {"SEASON", "TEAM", "LEAGUE"}
        stat_like = any(col in headers for col in ("GP", "G", "A", "PTS"))
        if not (must.issubset(set(headers)) and stat_like):
            continue
        for tr in table.select("tbody tr"):
            cols = [c.get_text(" ", strip=True) for c in tr.select("td")]
            if not cols or len(cols) < len(headers):
                continue
            data = dict(zip(headers, cols))

            season = _clean_text(data.get("SEASON"))
            team = _clean_text(data.get("TEAM"))
            league = _clean_text(data.get("LEAGUE"))
            gp = _to_int(data.get("GP"))
            g = _to_int(data.get("G"))
            a = _to_int(data.get("A"))
            pts = _to_int(data.get("PTS"))
            pim = _to_int(data.get("PIM"))
            age = _to_int(data.get("AGE"))
            aav_usd = _to_int(re.sub(r"[^0-9]", "", (data.get("AAV") or data.get("AAV (USD)") or "")))
            cap_hit_usd = _to_int(re.sub(r"[^0-9]", "", (data.get("CAP HIT") or data.get("CAP HIT (USD)") or "")))
            # TOI could be minutes; convert to seconds if it looks like an integer minutes value
            toi_seconds = None
            toi_raw = data.get("TOI") or data.get("TOI (MIN)") or data.get("TOI MIN")
            if toi_raw:
                val = _to_int(toi_raw)
                if val is not None:
                    toi_seconds = val * 60

            is_playoffs = None
            notes = None
            # Flag playoffs if any cell contains 'Playoffs'
            if any("PLAYOFF" in c.upper() for c in cols):
                notes = "; ".join(cols)

            # extras: store unmapped columns
            known = {"SEASON","TEAM","LEAGUE","GP","G","A","PTS","PIM","AGE","AAV","AAV (USD)","CAP HIT","CAP HIT (USD)","TOI","TOI (MIN)","TOI MIN"}
            extras_map = {k: v for k, v in data.items() if k not in known and _clean_text(v)}
            extras = json.dumps(extras_map) if extras_map else None

            rows.append(
                PuckPediaSeasonStat(
                    url=url,
                    season=season,
                    team=team,
                    league=league,
                    gp=gp,
                    g=g,
                    a=a,
                    pts=pts,
                    pim=pim,
                    age=age,
                    aav_usd=aav_usd,
                    cap_hit_usd=cap_hit_usd,
                    toi_seconds=toi_seconds,
                    is_playoffs=is_playoffs,
                    notes=notes,
                    extras=extras,
                )
            )
    return rows


def parse_contracts(soup: BeautifulSoup, url: str) -> List[PuckPediaContract]:
    out: List[PuckPediaContract] = []
    # Contracts often in tables with AAV / Total / Term
    for table in soup.select("table"):
        headers = [h.get_text(" ", strip=True).upper().replace("-", " ") for h in table.select("thead th")]
        if not headers:
            headers = [h.get_text(" ", strip=True).upper().replace("-", " ") for h in table.select("tr:first-child th, tr:first-child td")]
        if not headers:
            continue
        if not ((any("AAV" in h or "CAP HIT" in h for h in headers)) and any("TERM" in h or "LENGTH" in h for h in headers)):
            continue
        for tr in table.select("tbody tr"):
            cols = [c.get_text(" ", strip=True) for c in tr.select("td")]
            if not cols:
                continue
            data = dict(zip(headers, cols))
            # Try to map flexible header names
            signing_date = _clean_text(data.get("DATE") or data.get("SIGNING DATE") or data.get("SIGNED") or data.get("CONTRACT DATE"))
            term_years = _to_int((data.get("TERM") or data.get("LENGTH") or data.get("YEARS") or "").split()[0])
            aav_raw = data.get("AAV") or data.get("AAV (USD)") or data.get("CAP HIT") or data.get("CAP HIT (USD)")
            aav_usd = _to_int(re.sub(r"[^0-9]", "", aav_raw or ""))
            total_raw = data.get("TOTAL") or data.get("TOTAL VALUE") or data.get("TOTAL (USD)")
            total_value_usd = _to_int(re.sub(r"[^0-9]", "", total_raw or ""))
            clauses = _clean_text(
                data.get("CLAUSES")
                or data.get("NO TRADE / NO MOVE")
                or data.get("NO TRADE")
                or data.get("NO MOVE")
                or data.get("CLAUSE")
            )
            details = _clean_text(" ".join(cols))
            out.append(
                PuckPediaContract(
                    url=url,
                    signing_date=signing_date,
                    term_years=term_years,
                    aav_usd=aav_usd,
                    total_value_usd=total_value_usd,
                    clauses=clauses,
                    details=details,
                )
            )
    return out


def load_bq(client: bigquery.Client, table: str, rows: List[dict]) -> None:
    if not rows:
        return
    job = client.load_table_from_json(rows, table, job_config=bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ignore_unknown_values=True,
    ))
    job.result()


def ingest(url: str) -> None:
    client = bigquery.Client()
    ensure_bq_tables(client)

    with requests.Session() as session:
        soup = fetch_html(session, url)
        prof = parse_profile(soup, url)
        stats = parse_season_stats(soup, url)
        contracts = parse_contracts(soup, url)

    # Upsert player profile by deleting existing url first
    client.query(f"DELETE FROM `fantasy-snipe-ai.nhl_external.puckpedia_players` WHERE url=@url",
                 job_config=bigquery.QueryJobConfig(
                     query_parameters=[bigquery.ScalarQueryParameter("url", "STRING", url)]
                 )).result()
    load_bq(client, "fantasy-snipe-ai.nhl_external.puckpedia_players", [asdict(prof)])

    # Replace season stats for this url
    client.query(f"DELETE FROM `fantasy-snipe-ai.nhl_external.puckpedia_player_season_stats` WHERE url=@url",
                 job_config=bigquery.QueryJobConfig(
                     query_parameters=[bigquery.ScalarQueryParameter("url", "STRING", url)]
                 )).result()
    load_bq(client, "fantasy-snipe-ai.nhl_external.puckpedia_player_season_stats", [asdict(s) for s in stats])

    # Replace contracts for this url
    client.query(f"DELETE FROM `fantasy-snipe-ai.nhl_external.puckpedia_contracts` WHERE url=@url",
                 job_config=bigquery.QueryJobConfig(
                     query_parameters=[bigquery.ScalarQueryParameter("url", "STRING", url)]
                 )).result()
    load_bq(client, "fantasy-snipe-ai.nhl_external.puckpedia_contracts", [asdict(c) for c in contracts])

    print(json.dumps({
        "player": asdict(prof),
        "season_rows": len(stats),
        "contracts": len(contracts),
    }))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    args = ap.parse_args()
    ingest(args.url)


if __name__ == "__main__":
    main()


