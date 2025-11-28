import os
import sys
import argparse
import requests
from typing import Optional
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Player, Team, PlayerShift, Game


def _fetch_and_store_for_game(session, game_id: int, batch_commit: int = 500) -> None:
    # Build lookups for ids
    player_ids = {pid for (pid,) in session.query(Player.id).all()}
    team_ids = {tid for (tid,) in session.query(Team.id).all()}

    # Prefetch existing shift keys to avoid duplicates on re-runs
    existing_keys = set(
        (pid, gid, sn)
        for (pid, gid, sn) in session.query(
            PlayerShift.player_id, PlayerShift.game_id, PlayerShift.shift_number
        ).filter(PlayerShift.game_id == game_id).all()
    )

    # Reference: Get Shift Charts
    # GET https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}
    url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"

    resp = requests.get(url, timeout=20)
    if resp.status_code == 404:
        print(f"No shift charts available for game {game_id}.")
        return
    resp.raise_for_status()
    payload = resp.json() or {}
    rows = payload.get('data') or payload.get('rows') or []

    to_add = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = row.get('playerId')
        tid = row.get('teamId')
        sn = row.get('shiftNumber')
        if pid not in player_ids or tid not in team_ids:
            # Skip rows for players/teams we don't have locally
            continue
        # Skip if we already have this exact shift
        if (pid, game_id, sn) in existing_keys:
            continue

        shift = PlayerShift(
            player_id=pid,
            game_id=game_id,
            team_id=tid,
            shift_number=sn,
            period=row.get('period'),
            start_time=row.get('startTime'),
            end_time=row.get('endTime'),
            duration=row.get('duration'),
        )
        to_add.append(shift)

        if len(to_add) >= batch_commit:
            session.add_all(to_add)
            session.commit()
            to_add.clear()

    if to_add:
        session.add_all(to_add)
        session.commit()

    print(f"Stored shift charts for game {game_id}.")


def populate_shift_charts(game_id: int, batch_commit: int = 500) -> None:
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    # Do not create tables here; expect existing schema

    try:
        _fetch_and_store_for_game(session, game_id, batch_commit=batch_commit)

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch shift charts for game {game_id}: {e}")
    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


def populate_shift_charts_all(season: Optional[int] = None, game_type: Optional[int] = None, batch_commit: int = 500) -> None:
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    # Do not create tables here; expect existing schema

    try:
        # Games already having shifts
        existing_games = {gid for (gid,) in session.query(PlayerShift.game_id).distinct().all()}

        q = session.query(Game.id)
        if season is not None:
            q = q.filter(Game.season == int(season))
        if game_type is not None:
            q = q.filter(Game.game_type == int(game_type))

        game_ids = [gid for (gid,) in q.all()]
        print(f"Found {len(game_ids)} games matching filter; skipping {len(existing_games)} with existing shifts.")

        processed = 0
        for gid in game_ids:
            if gid in existing_games:
                continue
            _fetch_and_store_for_game(session, gid, batch_commit=batch_commit)
            processed += 1

        print(f"Finished storing shift charts for {processed} games.")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate shift charts.")
    parser.add_argument("game_id", nargs="?", type=int, help="Optional NHL game ID, e.g., 2021020001. If omitted and --all is set, processes all.")
    parser.add_argument("--all", action="store_true", help="Process all games in the local database (optionally filter by --season and/or --game-type).")
    parser.add_argument("--season", type=int, default=None, help="Season ID like 20242025 to filter games when using --all.")
    parser.add_argument("--game-type", type=int, default=None, help="Game type (2=Regular, 3=Playoffs) to filter when using --all.")
    args = parser.parse_args()

    if args.all:
        populate_shift_charts_all(season=args.season, game_type=args.game_type)
    elif args.game_id:
        populate_shift_charts(args.game_id)
    else:
        print("Provide a game_id or use --all (optionally with --season and/or --game-type).")

