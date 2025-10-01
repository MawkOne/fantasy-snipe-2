import argparse
import json
import math
import sys
import time
from typing import Dict, Iterable, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from google.cloud import bigquery


def _mmss_to_seconds(mmss: Optional[str]) -> Optional[int]:
    if not mmss or ":" not in str(mmss):
        return None
    try:
        m, s = str(mmss).split(":")
        return int(m) * 60 + int(s)
    except Exception:
        return None


def _fetch_primary(session: requests.Session, game_id: int) -> List[Dict]:
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            r = session.get(url, timeout=20)
            if r.status_code == 404:
                return []
            if 500 <= r.status_code < 600:
                last_exc = Exception(f"{r.status_code} from api-web")
                time.sleep(1 + attempt)
                continue
            r.raise_for_status()
            pl = r.json() or {}
            return pl.get("plays") or pl.get("events") or pl.get("gameEvents") or []
        except requests.exceptions.RequestException as e:
            last_exc = e
            time.sleep(1 + attempt)
            continue
    print(f"Primary PBP failed for game {game_id}: {last_exc}")
    return []


def _fetch_secondary(session: requests.Session, game_id: int) -> List[Dict]:
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
    r = session.get(url, timeout=20)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    pl = r.json() or {}
    return (((pl.get("liveData") or {}).get("plays") or {}).get("allPlays")) or []


def _normalize_event(ev: Dict, game_id: int) -> Dict:
    event_idx = ev.get("eventId") or ev.get("eventIdx") or (ev.get("about") or {}).get("eventIdx")
    period = (
        ev.get("period")
        or (ev.get("about") or {}).get("period")
        or ((ev.get("periodDescriptor") or {}).get("number"))
        or ((ev.get("periodDescriptor") or {}).get("period"))
    )
    try:
        if period is not None:
            period = int(period)
    except Exception:
        pass
    period_time = (
        ev.get("timeInPeriod")
        or (ev.get("about") or {}).get("periodTime")
        or (ev.get("details") or {}).get("timeInPeriod")
        or ev.get("periodTime")
    )
    period_time_remaining = (
        (ev.get("about") or {}).get("periodTimeRemaining")
        or (ev.get("details") or {}).get("timeRemaining")
        or ev.get("timeRemaining")
    )
    if not period_time and period_time_remaining:
        try:
            pnum = int(period) if period is not None else None
        except Exception:
            pnum = None
        rem_s = _mmss_to_seconds(period_time_remaining)
        if rem_s is not None:
            period_len = 1200 if (pnum is None or pnum <= 3) else 300
            elapsed_s = max(0, period_len - rem_s)
            period_time = f"{elapsed_s // 60:02d}:{elapsed_s % 60:02d}"
    event_type = (ev.get("typeDescKey") or (ev.get("result") or {}).get("event") or ev.get("eventTypeId"))
    if isinstance(event_type, str):
        etu = event_type.upper().replace("_", " ")
        if etu == "MISSED SHOT":
            event_type = "MISSED_SHOT"
        elif etu == "BLOCKED SHOT":
            event_type = "BLOCKED_SHOT"
        elif etu == "SHOT":
            event_type = "SHOT_ON_GOAL"
    description = ((ev.get("details") or {}).get("description") or (ev.get("result") or {}).get("description"))
    team_id = (((ev.get("details") or {}) or {}).get("eventOwnerTeamId") or (ev.get("team") or {}).get("id"))
    secondary_type = ((ev.get("result") or {}).get("secondaryType") or (ev.get("details") or {}).get("shotType"))
    coords = ev.get("coordinates") or (ev.get("details") or {}).get("coordinates") or {}
    x = coords.get("x") if isinstance(coords, dict) else None
    y = coords.get("y") if isinstance(coords, dict) else None
    if (x is None or y is None) and isinstance(ev.get("details"), dict):
        x = (ev.get("details") or {}).get("xCoord", x)
        y = (ev.get("details") or {}).get("yCoord", y)
    if period is None and isinstance(ev.get("about"), dict):
        period = (ev.get("about") or {}).get("period")
    if period_time is None and isinstance(ev.get("about"), dict):
        period_time = (ev.get("about") or {}).get("periodTime")
    if event_idx is None and isinstance(ev.get("about"), dict):
        event_idx = (ev.get("about") or {}).get("eventIdx")
    if team_id is None and isinstance(ev.get("team"), dict):
        team_id = (ev.get("team") or {}).get("id")
    if (x is None or y is None) and isinstance(ev.get("coordinates"), dict):
        x = (ev.get("coordinates") or {}).get("x")
        y = (ev.get("coordinates") or {}).get("y")

    return {
        "game_id": game_id,
        "event_idx": event_idx,
        "period": period,
        "period_time": period_time,
        "period_time_remaining": period_time_remaining,
        "event_type": event_type,
        "description": description,
        "team_id": team_id,
        "secondary_type": secondary_type,
        "coordinates_x": x,
        "coordinates_y": y,
        "raw": json.dumps(ev, ensure_ascii=False),
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


def _existing_games(client: bigquery.Client, season: int, game_type: Optional[int]) -> Set[int]:
    params = [bigquery.ScalarQueryParameter("season", "INT64", season)]
    where = "WHERE g.season=@season"
    if game_type is not None:
        where += " AND g.game_type=@game_type"
        params.append(bigquery.ScalarQueryParameter("game_type", "INT64", game_type))
    q = f"""
        SELECT DISTINCT e.game_id
        FROM `fantasy-snipe-ai.nhl_raw.game_events` e
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id=e.game_id
        {where}
    """
    job = client.query(q, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return {int(row[0]) for row in job}


def _load_rows(client: bigquery.Client, table_id: str, rows: Iterable[Dict]) -> None:
    # Load JSON rows directly to BigQuery to avoid local file parser issues
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


def main(season: int, game_type: Optional[int], only_missing: bool, batch_size: int, rows_per_load: int, max_games: int) -> None:
    client = bigquery.Client()
    all_games = _list_games(client, season, game_type)
    if only_missing:
        existing = _existing_games(client, season, game_type)
        game_ids = [gid for gid in all_games if gid not in existing]
    else:
        game_ids = all_games
    print(f"Found {len(game_ids)} games to ingest events for (season={season}, game_type={game_type}).")

    buffer: List[Dict] = []
    processed_games = 0

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    def fetch_game(gid: int) -> Dict:
        t0 = time.time()
        evs = _fetch_primary(session, gid)
        if not evs:
            try:
                evs = _fetch_secondary(session, gid)
            except Exception:
                evs = []
        dt = time.time() - t0
        return {"gid": gid, "events": evs, "ms": int(dt * 1000)}

    workers = 6
    print(f"Using {workers} workers with pooled HTTP session.")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {}
        submit_count = 0
        for gid in game_ids:
            futures[ex.submit(fetch_game, gid)] = gid
            submit_count += 1
            if max_games and submit_count >= max_games:
                break
        for fut in as_completed(futures):
            res = fut.result()
            gid = res["gid"]
            evs = res["events"]
            ms = res["ms"]
            if processed_games % 50 == 0:
                print(f"Progress: processed_games={processed_games}/{len(game_ids)} buffer_size={len(buffer)}")
            print(f"Fetched game_id={gid} events={len(evs)} in {ms} ms")
            if not evs:
                processed_games += 1
                continue
            for ev in evs:
                if isinstance(ev, dict):
                    buffer.append(_normalize_event(ev, gid))
                if len(buffer) >= rows_per_load:
                    print(f"Flushing {len(buffer)} events to BigQuery...")
                    _load_rows(client, "fantasy-snipe-ai.nhl_raw.game_events", buffer)
                    print("Flush complete.")
                    buffer.clear()
            processed_games += 1
    if buffer:
        print(f"Final flush of {len(buffer)} events to BigQuery...")
        _load_rows(client, "fantasy-snipe-ai.nhl_raw.game_events", buffer)
        buffer.clear()
    print(f"Completed events ingest for {processed_games} games.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--game-type", type=int, default=None)
    p.add_argument("--only-missing", action="store_true")
    p.add_argument("--batch-size", type=int, default=25000)
    p.add_argument("--rows-per-load", type=int, default=5000)
    p.add_argument("--max-games", type=int, default=0)
    args = p.parse_args()
    main(args.season, args.game_type, args.only_missing, args.batch_size, args.rows_per_load, args.max_games)


