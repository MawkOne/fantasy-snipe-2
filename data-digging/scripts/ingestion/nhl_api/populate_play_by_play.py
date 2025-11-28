import os
import sys
import argparse
import requests
import time
from sqlalchemy.orm import sessionmaker
from typing import Optional

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import GameEvent, Game, Team


def mmss_to_seconds(mmss: Optional[str]) -> Optional[int]:
    if not mmss or ":" not in str(mmss):
        return None
    try:
        m, s = str(mmss).split(":")
        return int(m) * 60 + int(s)
    except Exception:
        return None


def seconds_to_mmss(seconds: Optional[int]) -> Optional[str]:
    if seconds is None or seconds < 0:
        return None
    try:
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"
    except Exception:
        return None


def _fetch_and_store_for_game(session, game_id: int, batch_commit: int = 500, refresh: bool = False) -> None:
    # Ensure referenced game exists locally; do not create schema/rows here
    if not session.query(Game.id).filter(Game.id == game_id).first():
        print(f"Game {game_id} not found in local DB. Insert the game first (e.g., via team schedule or games script).")
        return

    # Optionally refresh: clear prior events for this game
    if refresh:
        session.query(GameEvent).filter(GameEvent.game_id == game_id).delete()
        session.commit()

    # Prefetch existing event keys to de-duplicate on re-runs
    existing = set(
        (eid,)
        for (eid,) in session.query(GameEvent.event_idx).filter(GameEvent.game_id == game_id).all()
    )

    def fetch_primary(game_id: int):
        url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
        last_exc = None
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=20)
                if r.status_code == 404:
                    return []
                if 500 <= r.status_code < 600:
                    last_exc = Exception(f"{r.status_code} from api-web")
                    time.sleep(1 + attempt)
                    continue
                r.raise_for_status()
                pl = r.json() or {}
                return pl.get('plays') or pl.get('events') or pl.get('gameEvents') or []
            except requests.exceptions.RequestException as e:
                last_exc = e
                time.sleep(1 + attempt)
                continue
        # If we exhausted retries, surface no events to trigger fallback
        print(f"Primary PBP failed for game {game_id}: {last_exc}")
        return []

    def fetch_secondary(game_id: int):
        # Legacy endpoint that includes coordinates reliably
        url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
        r = requests.get(url, timeout=20)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        pl = r.json() or {}
        return (((pl.get('liveData') or {}).get('plays') or {}).get('allPlays')) or []

    raw_events = fetch_primary(game_id)
    # Fallback if primary returned nothing OR returned but empty due to upstream issues
    if not raw_events:
        try:
            raw_events = fetch_secondary(game_id)
        except Exception:
            raw_events = []

    to_add = []
    for ev in raw_events:
        if not isinstance(ev, dict):
            continue

        # Try multiple schemas
        event_idx = ev.get('eventId') or ev.get('eventIdx') or (ev.get('about') or {}).get('eventIdx')
        if event_idx is not None and (event_idx,) in existing:
            continue

        # Normalize period and times (try multiple schemas)
        period = (
            ev.get('period')
            or (ev.get('about') or {}).get('period')
            or ((ev.get('periodDescriptor') or {}).get('number'))
            or ((ev.get('periodDescriptor') or {}).get('period'))
        )
        # Some feeds provide strings; coerce to int where possible
        try:
            if period is not None:
                period = int(period)
        except Exception:
            pass
        period_time = (ev.get('timeInPeriod') or (ev.get('about') or {}).get('periodTime') or (ev.get('details') or {}).get('timeInPeriod') or ev.get('periodTime'))
        period_time_remaining = ((ev.get('about') or {}).get('periodTimeRemaining') or (ev.get('details') or {}).get('timeRemaining') or ev.get('timeRemaining'))
        # Fallback via clock object
        if not period_time:
            clock_val = ev.get('clock')
            if isinstance(clock_val, dict):
                period_time = clock_val.get('timeInPeriod') or clock_val.get('time')
                if not period_time_remaining:
                    period_time_remaining = clock_val.get('timeRemaining')
            elif isinstance(clock_val, str):
                period_time = clock_val
        # Derive elapsed from remaining if needed
        if not period_time and period_time_remaining:
            try:
                pnum = int(period) if period is not None else None
            except Exception:
                pnum = None
            rem_s = mmss_to_seconds(period_time_remaining)
            if rem_s is not None:
                period_len = 1200 if (pnum is None or pnum <= 3) else 300
                elapsed_s = max(0, period_len - rem_s)
                period_time = seconds_to_mmss(elapsed_s)
        event_type = (ev.get('typeDescKey') or (ev.get('result') or {}).get('event') or ev.get('eventTypeId'))
        # Normalize known variations
        if isinstance(event_type, str):
            etu = event_type.upper().replace("_", " ")
            if etu == "MISSED SHOT":
                event_type = "MISSED_SHOT"
            elif etu == "BLOCKED SHOT":
                event_type = "BLOCKED_SHOT"
            elif etu == "SHOT":
                event_type = "SHOT_ON_GOAL"
        description = ((ev.get('details') or {}).get('description') or (ev.get('result') or {}).get('description')) or ''
        team_id = (((ev.get('details') or {}) or {}).get('eventOwnerTeamId') or (ev.get('team') or {}).get('id'))
        secondary_type = ((ev.get('result') or {}).get('secondaryType') or (ev.get('details') or {}).get('shotType'))
        coords = ev.get('coordinates') or (ev.get('details') or {}).get('coordinates') or {}
        x = coords.get('x') if isinstance(coords, dict) else None
        y = coords.get('y') if isinstance(coords, dict) else None
        # Try details.xCoord/yCoord if present
        if (x is None or y is None) and isinstance(ev.get('details'), dict):
            x = (ev.get('details') or {}).get('xCoord', x)
            y = (ev.get('details') or {}).get('yCoord', y)
        # Secondary schema fallbacks
        if period is None and isinstance(ev.get('about'), dict):
            period = (ev.get('about') or {}).get('period')
        if period_time is None and isinstance(ev.get('about'), dict):
            period_time = (ev.get('about') or {}).get('periodTime')
        if period_time_remaining is None and isinstance(ev.get('about'), dict):
            period_time_remaining = (ev.get('about') or {}).get('periodTimeRemaining')
        if event_idx is None and isinstance(ev.get('about'), dict):
            event_idx = (ev.get('about') or {}).get('eventIdx')
        if team_id is None and isinstance(ev.get('team'), dict):
            team_id = (ev.get('team') or {}).get('id')
        if (x is None or y is None) and isinstance(ev.get('coordinates'), dict):
            x = (ev.get('coordinates') or {}).get('x')
            y = (ev.get('coordinates') or {}).get('y')

        to_add.append(
            GameEvent(
                game_id=game_id,
                event_idx=event_idx,
                period=period,
                period_time=period_time,
                period_time_remaining=period_time_remaining,
                event_type=event_type,
                description=description,
                team_id=team_id,
                secondary_type=secondary_type,
                coordinates_x=x,
                coordinates_y=y,
                raw=ev,
            )
        )

        if len(to_add) >= batch_commit:
            session.add_all(to_add)
            session.commit()
            to_add.clear()

    if to_add:
        session.add_all(to_add)
        session.commit()

    print(f"Stored play-by-play events for game {game_id}.")


def populate_play_by_play(game_id: int, batch_commit: int = 500, refresh: bool = False) -> None:
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    # Do not create tables here; expect existing schema

    try:
        _fetch_and_store_for_game(session, game_id, batch_commit=batch_commit, refresh=refresh)

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch play-by-play for game {game_id}: {e}")
    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


def populate_play_by_play_all(season: Optional[int] = None, game_type: Optional[int] = None, batch_commit: int = 500) -> None:
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    # Do not create tables here; expect existing schema

    try:
        # Games already having events
        existing_games = {gid for (gid,) in session.query(GameEvent.game_id).distinct().all()}

        q = session.query(Game.id)
        if season is not None:
            q = q.filter(Game.season == int(season))
        if game_type is not None:
            q = q.filter(Game.game_type == int(game_type))

        game_ids = [gid for (gid,) in q.all()]
        print(f"Found {len(game_ids)} games matching filter; skipping {len(existing_games)} with existing events.")

        processed = 0
        for gid in game_ids:
            if gid in existing_games:
                continue
            try:
                _fetch_and_store_for_game(session, gid, batch_commit=batch_commit)
                processed += 1
            except Exception as game_error:
                print(f"Error processing game {gid}: {game_error}")
                import traceback
                traceback.print_exc()
                continue

        print(f"Finished storing play-by-play for {processed} games.")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate play-by-play events.")
    parser.add_argument("game_id", nargs="?", type=int, help="Optional NHL game ID, e.g., 2021020001. If omitted and --all is set, processes all.")
    parser.add_argument("--all", action="store_true", help="Process all games in the local database (optionally filter by --season and/or --game-type).")
    parser.add_argument("--season", type=int, default=None, help="Season ID like 20242025 to filter games when using --all.")
    parser.add_argument("--game-type", type=int, default=None, help="Game type (2=Regular, 3=Playoffs) to filter when using --all.")
    parser.add_argument("--refresh", action="store_true", help="With a specific game_id, delete existing events and re-ingest.")
    args = parser.parse_args()

    if args.all:
        populate_play_by_play_all(season=args.season, game_type=args.game_type)
    elif args.game_id:
        populate_play_by_play(args.game_id, refresh=args.refresh)
    else:
        print("Provide a game_id or use --all (optionally with --season and/or --game-type).")

