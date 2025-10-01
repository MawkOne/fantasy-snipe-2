import argparse
import json
import math
import time
import sys
from typing import Dict, Iterable, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from google.cloud import bigquery


def _fetch_shifts(session: requests.Session, game_id: int) -> List[Dict]:
    # Reference: https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}
    url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"
    for attempt in range(3):
        try:
            r = session.get(url, timeout=20)
            if r.status_code == 404:
                return []
            if 500 <= r.status_code < 600:
                time.sleep(1 + attempt)
                continue
            r.raise_for_status()
            payload = r.json() or {}
            return payload.get("data") or payload.get("rows") or []
        except requests.exceptions.RequestException:
            time.sleep(1 + attempt)
            continue
    return []


def _normalize_shift(row: Dict, game_id: int) -> Dict:
    return {
        "player_id": row.get("playerId"),
        "game_id": game_id,
        "team_id": row.get("teamId"),
        "shift_number": row.get("shiftNumber"),
        "period": row.get("period"),
        "start_time": row.get("startTime"),
        "end_time": row.get("endTime"),
        "duration": row.get("duration"),
    }


def _list_games(client: bigquery.Client, season: int, game_type: Optional[int]) -> List[int]:
    params = [bigquery.ScalarQueryParameter("season", "INT64", season)]
    where = "WHERE season=@season"
    if game_type is not None:
        where += " AND game_type=@game_type"
        params.append(bigquery.ScalarQueryParameter("game_type", "INT64", game_type))
    q = f"""
        SELECT id FROM `fantasy-snipe-ai.nhl_raw.games`
        {where}
        ORDER BY id
    """
    job = client.query(q, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return [int(row[0]) for row in job]


def _existing_games(client: bigquery.Client, season: int, game_type: Optional[int]) -> List[int]:
    params = [bigquery.ScalarQueryParameter("season", "INT64", season)]
    where = "WHERE g.season=@season"
    if game_type is not None:
        where += " AND g.game_type=@game_type"
        params.append(bigquery.ScalarQueryParameter("game_type", "INT64", game_type))
    q = f"""
        SELECT DISTINCT s.game_id
        FROM `fantasy-snipe-ai.nhl_raw.player_shifts` s
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id=s.game_id
        {where}
    """
    job = client.query(q, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return [int(row[0]) for row in job]


def _load_rows(client: bigquery.Client, table_id: str, rows: Iterable[Dict]) -> None:
    def _sanitize(value):
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, dict):
            return {k: _sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_sanitize(v) for v in value]
        return value
    sanitized_rows = [_sanitize(r) for r in rows]
    job = client.load_table_from_json(
        sanitized_rows,
        table_id,
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            ignore_unknown_values=True,
            max_bad_records=1000,
        ),
    )
    try:
        job.result()
    except Exception as e:
        print(f"BigQuery load failed for {len(sanitized_rows)} rows: {e}", file=sys.stderr)
        raise


def main(season: Optional[int], game_type: Optional[int], only_missing: bool, batch_size: int, game_id: Optional[int]) -> None:
    client = bigquery.Client()
    # Single-game mode
    if game_id is not None:
        print(f"Ingesting shifts for single game_id={game_id}.")
        game_ids = [int(game_id)]
    else:
        if season is None:
            raise SystemExit("--season is required unless --game-id is provided")
        all_games = _list_games(client, season, game_type)
        if only_missing:
            existing = set(_existing_games(client, season, game_type))
            game_ids = [gid for gid in all_games if gid not in existing]
        else:
            game_ids = all_games
        print(f"Found {len(game_ids)} games to ingest shifts for (season={season}, game_type={game_type}).")

    buffer: List[Dict] = []
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    def fetch_game(gid: int) -> Dict:
        t0 = time.time()
        rows = _fetch_shifts(session, gid)
        dt = time.time() - t0
        return {"gid": gid, "rows": rows, "ms": int(dt * 1000)}

    workers = 6
    print(f"Using {workers} workers with pooled HTTP session.")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fetch_game, gid): gid for gid in game_ids}
        for fut in as_completed(futures):
            res = fut.result()
            gid = res["gid"]
            rows = res["rows"]
            ms = res["ms"]
            if not rows:
                print(f"No shifts returned for game_id={gid} ({ms} ms), skipping.")
                continue
            print(f"Fetched {len(rows)} shifts for game_id={gid} in {ms} ms")
            for row in rows:
                buffer.append(_normalize_shift(row, gid))
                if len(buffer) >= batch_size:
                    print(f"Flushing {len(buffer)} shifts to BigQuery...")
                    _load_rows(client, "fantasy-snipe-ai.nhl_raw.player_shifts", buffer)
                    print("Flush complete.")
                    buffer.clear()
    if buffer:
        print(f"Final flush of {len(buffer)} shifts to BigQuery...")
        _load_rows(client, "fantasy-snipe-ai.nhl_raw.player_shifts", buffer)
        buffer.clear()
    print("Completed shifts ingest.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, required=False)
    p.add_argument("--game-type", type=int, default=None)
    p.add_argument("--only-missing", action="store_true")
    p.add_argument("--batch-size", type=int, default=25000)
    p.add_argument("--game-id", type=int, default=None, help="Process a single NHL game id")
    args = p.parse_args()
    main(args.season, args.game_type, args.only_missing, args.batch_size, args.game_id)


