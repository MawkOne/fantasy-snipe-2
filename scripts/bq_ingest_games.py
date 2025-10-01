import argparse
import time
from typing import Dict, List, Optional, Set

import requests
from google.cloud import bigquery


TEAM_ABBREVS: List[str] = [
    "ANA", "ARI", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SJS", "SEA", "STL", "TBL", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]


def _fetch_schedule_stats_rest(season: int, game_type: Optional[int]) -> List[Dict]:
    base = "https://api.nhle.com/stats/rest/en/schedule"
    cx = f"seasonId={season}" if game_type is None else f"seasonId={season} and gameTypeId={int(game_type)}"
    url = f"{base}?cayenneExp={requests.utils.quote(cx)}"
    for attempt in range(3):
        r = requests.get(url, timeout=20)
        if r.status_code == 404:
            return []
        if 500 <= r.status_code < 600:
            time.sleep(1 + attempt)
            continue
        r.raise_for_status()
        js = r.json() or {}
        rows = js.get("data") or js.get("rows") or []
        out: List[Dict] = []
        for row in rows:
            out.append({
                "id": row.get("gameId"),
                "season": row.get("seasonId"),
                "game_type": row.get("gameTypeId"),
                "game_date": row.get("gameDate") or row.get("startTimeUTC"),
                "game_state": row.get("gameState"),
                "home_team_id": row.get("homeTeamId"),
                "away_team_id": row.get("awayTeamId"),
                "home_score": row.get("homeGoalCount"),
                "away_score": row.get("awayGoalCount"),
            })
        return out
    return []


def _fetch_schedule_api_web(season: int, game_type: Optional[int]) -> List[Dict]:
    # Aggregate from team schedules: https://api-web.nhle.com/v1/club-schedule-season/{TEAM}/{SEASON}
    seen_ids: Set[int] = set()
    games: List[Dict] = []
    for team in TEAM_ABBREVS:
        url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            js = r.json() or {}
        except Exception:
            continue
        for g in js.get("games", []):
            gid = g.get("id")
            if not gid or gid in seen_ids:
                continue
            seen_ids.add(gid)
            gtype = g.get("gameType")
            if game_type is not None and int(gtype or 0) != int(game_type):
                continue
            games.append({
                "id": gid,
                "season": g.get("season"),
                "game_type": gtype,
                "game_date": g.get("startTimeUTC") or g.get("gameDate"),
                "game_state": g.get("gameState"),
                "home_team_id": (g.get("homeTeam") or {}).get("id"),
                "away_team_id": (g.get("awayTeam") or {}).get("id"),
                "home_score": (g.get("homeTeam") or {}).get("score"),
                "away_score": (g.get("awayTeam") or {}).get("score"),
            })
    return games


def _fetch_schedule(season: int, game_type: Optional[int]) -> List[Dict]:
    # Try stats REST first; if empty, fall back to api-web per-team schedules
    rows = _fetch_schedule_stats_rest(season, game_type)
    if rows:
        return rows
    return _fetch_schedule_api_web(season, game_type)


def _existing_ids(client: bigquery.Client, season: int) -> set:
    q = (
        "SELECT id FROM `fantasy-snipe-ai.nhl_raw.games` "
        "WHERE season=@season"
    )
    job = client.query(q, job_config=bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("season", "INT64", season)]
    ))
    return {int(row[0]) for row in job}


def main(season: int, game_type: Optional[int]) -> None:
    client = bigquery.Client()
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_raw`").result()
    client.query(
        "CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_raw.games` ("
        "id INT64, season INT64, game_type INT64, game_date TIMESTAMP, game_state STRING,"
        "home_team_id INT64, away_team_id INT64, home_score INT64, away_score INT64)"
    ).result()

    existing = _existing_ids(client, season)
    rows = _fetch_schedule(season, game_type)
    to_insert = [r for r in rows if r.get("id") not in existing]
    if not to_insert:
        print("No new games to insert.")
        return
    client.load_table_from_json(
        to_insert,
        "fantasy-snipe-ai.nhl_raw.games",
        job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND),
    ).result()
    print(f"Inserted {len(to_insert)} games for season {season} (game_type={game_type}).")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--game-type", type=int, default=None)
    args = p.parse_args()
    main(args.season, args.game_type)


