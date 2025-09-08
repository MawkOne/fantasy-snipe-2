#!/usr/bin/env python3
import os
import sys
import time
import argparse
import requests
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Game, PlayerGameStats, create_tables


def upsert_stats_for_game(session, game_id: int) -> int:
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
    r = requests.get(url, timeout=20)
    if r.status_code == 404:
        return 0
    r.raise_for_status()
    data = r.json() or {}
    live = data.get('liveData', {})
    box = live.get('boxscore', {})
    teams = box.get('teams', {})
    added = 0

    def handle_side(side: str):
        nonlocal added
        team_obj = teams.get(side) or {}
        team_id = (team_obj.get('team') or {}).get('id')
        skaters = (team_obj.get('players') or {}).values()
        for p in skaters:
            try:
                info = p.get('person') or {}
                pid = info.get('id')
                stats = p.get('stats') or {}
                sk = stats.get('skaterStats') or {}
                if not pid or not sk:
                    continue
                # Build or update row
                row = session.query(PlayerGameStats).filter(
                    PlayerGameStats.player_id == int(pid),
                    PlayerGameStats.game_id == int(game_id),
                ).first()
                if row is None:
                    row = PlayerGameStats(player_id=int(pid), game_id=int(game_id), team_id=team_id)
                    session.add(row)
                    added += 1
                row.team_id = team_id
                row.goals = int(sk.get('goals') or 0)
                row.assists = int(sk.get('assists') or 0)
                row.points = row.goals + row.assists
                row.plus_minus = int(sk.get('plusMinus') or 0)
                row.power_play_goals = int(sk.get('powerPlayGoals') or 0)
                row.power_play_points = int(sk.get('powerPlayPoints') or 0)
                row.shorthanded_goals = int(sk.get('shortHandedGoals') or 0)
                row.shorthanded_points = int(sk.get('shortHandedPoints') or 0)
                row.shots = int(sk.get('shots') or 0)
                row.shifts = int(sk.get('shifts') or 0)
                row.pim = int(sk.get('penaltyMinutes') or 0)
                # TOI format "MM:SS"
                row.toi = sk.get('timeOnIce') or None
            except Exception:
                continue

    handle_side('home')
    handle_side('away')
    return added


def populate_player_game_stats(season_start_year: int, game_type: int = 2, batch_commit: int = 200) -> None:
    season_id = int(f"{season_start_year}{season_start_year+1}")
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")
    try:
        create_tables()
    except Exception:
        pass
    try:
        q = session.query(Game.id).filter(Game.season == season_id)
        if game_type is not None:
            q = q.filter(Game.game_type == int(game_type))
        game_ids = [gid for (gid,) in q.all()]
        print(f"Found {len(game_ids)} games for season {season_id}.")
        processed = 0
        to_commit = 0
        for gid in game_ids:
            try:
                added = upsert_stats_for_game(session, int(gid))
                to_commit += added
                processed += 1
                if to_commit >= batch_commit:
                    session.commit()
                    to_commit = 0
                if processed % 50 == 0:
                    print(f"Processed {processed}/{len(game_ids)} games...")
                time.sleep(0.1)
            except requests.exceptions.RequestException as e:
                print(f"Network error on game {gid}: {e}")
                continue
        if to_commit > 0:
            session.commit()
        print(f"Finished. Processed {processed} games.")
    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate player_game_stats from NHL live feed per game.")
    parser.add_argument("season_start_year", type=int, help="Starting year of the season, e.g., 2021 for 2021-22")
    parser.add_argument("--game-type", type=int, default=2, help="2=Regular, 3=Playoffs")
    args = parser.parse_args()
    populate_player_game_stats(args.season_start_year, game_type=args.game_type)


