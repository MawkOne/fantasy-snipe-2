#!/usr/bin/env python3
import os
import sys
import argparse
import requests
from datetime import date
from sqlalchemy.orm import sessionmaker

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Game


def populate_schedule_statsapi(season_start_year: int, game_type: int = 2, batch_commit: int = 250) -> None:
    season_id = int(f"{season_start_year}{season_start_year+1}")
    # Broad date window for the season
    start = date(season_start_year, 9, 15)  # mid-Sept preseason start (wider)
    end = date(season_start_year + 1, 7, 15)  # mid-July

    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")
    # Use existing schema; do not attempt to create tables here

    try:
        url = f"https://statsapi.web.nhl.com/api/v1/schedule?startDate={start.isoformat()}&endDate={end.isoformat()}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        payload = r.json() or {}
        dates = payload.get('dates') or []
        print(f"Fetched schedule with {len(dates)} dates.")

        existing = {gid for (gid,) in session.query(Game.id).all()}
        to_add = []
        added = 0
        for d in dates:
            for g in d.get('games') or []:
                try:
                    if int(g.get('season')) != season_id:
                        continue
                    # Filter by game type: R=Regular (2), P=Playoffs (3)
                    gt_str = (g.get('gameType') or '').upper()
                    gt = 2 if gt_str == 'R' else (3 if gt_str == 'P' else None)
                    if game_type is not None and gt != int(game_type):
                        continue
                    game_pk = int(g.get('gamePk'))
                    if game_pk in existing:
                        continue
                    teams = g.get('teams') or {}
                    home = (teams.get('home') or {}).get('team') or {}
                    away = (teams.get('away') or {}).get('team') or {}
                    to_add.append(
                        Game(
                            id=game_pk,
                            season=season_id,
                            game_type=gt,
                            game_date=date.fromisoformat(g.get('gameDate').split('T')[0]),
                            game_state=g.get('status', {}).get('detailedState'),
                            home_team_id=home.get('id'),
                            away_team_id=away.get('id'),
                            home_score=((g.get('teams') or {}).get('home') or {}).get('score'),
                            away_score=((g.get('teams') or {}).get('away') or {}).get('score'),
                        )
                    )
                    added += 1
                    if len(to_add) >= batch_commit:
                        session.add_all(to_add)
                        session.commit()
                        to_add.clear()
                except Exception:
                    continue
        if to_add:
            session.add_all(to_add)
            session.commit()
        print(f"Stored {added} new games for season {season_id}.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch schedule: {e}")
    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate games using statsapi schedule endpoint.")
    parser.add_argument("season_start_year", type=int)
    parser.add_argument("--game-type", type=int, default=2)
    args = parser.parse_args()
    populate_schedule_statsapi(args.season_start_year, game_type=args.game_type)


