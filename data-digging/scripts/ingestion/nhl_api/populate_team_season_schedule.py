import os
import sys
import time
import argparse
import requests
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Team, Game, create_tables


def parse_date(date_string: str) -> datetime:
    return datetime.strptime(date_string, "%Y-%m-%d")


def get_season_id(season_start_year: int) -> str:
    return f"{season_start_year}{season_start_year + 1}"


def populate_team_season_schedule(season_start_year: int, batch_commit: int = 250) -> None:
    season_id = get_season_id(season_start_year)

    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    # Ensure required tables exist
    try:
        create_tables()
    except Exception:
        pass

    try:
        teams = session.query(Team).all()
        if not teams:
            print("No teams found. Populate teams first.")
            return

        # Process each team’s season schedule
        to_add = []
        seen_game_ids = {gid for (gid,) in session.query(Game.id).all()}

        for i, team in enumerate(teams):
            if not team.tri_code:
                continue

            # Reference: Get Team Season Schedule — api-web.nhle.com
            # GET https://api-web.nhle.com/v1/club-schedule/{triCode}/{seasonId}
            # e.g., /v1/club-schedule/MTL/20242025
            url = f"https://api-web.nhle.com/v1/club-schedule/{team.tri_code}/{season_id}"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                data = resp.json() or {}
                games = data.get('games') or []

                for g in games:
                    game_id = g.get('id') or g.get('gameId')
                    if not game_id or game_id in seen_game_ids:
                        continue

                    # Normalize fields
                    game_date = g.get('gameDate') or g.get('date')
                    game_type = g.get('gameType')
                    home = g.get('homeTeam', {})
                    away = g.get('awayTeam', {})
                    home_id = home.get('id')
                    away_id = away.get('id')
                    home_score = home.get('score')
                    away_score = away.get('score')
                    state = g.get('gameState') or g.get('status')

                    try:
                        dt = parse_date(game_date.split('T')[0]) if game_date else None
                    except Exception:
                        dt = None

                    if not (home_id and away_id and dt):
                        continue

                    to_add.append(
                        Game(
                            id=game_id,
                            season=int(season_id),
                            game_type=int(game_type) if game_type is not None else None,
                            game_date=dt,
                            game_state=state,
                            home_team_id=home_id,
                            away_team_id=away_id,
                            home_score=home_score,
                            away_score=away_score,
                        )
                    )
                    seen_game_ids.add(game_id)

                    if len(to_add) >= batch_commit:
                        session.add_all(to_add)
                        session.commit()
                        to_add.clear()

            except requests.exceptions.RequestException:
                continue

            time.sleep(0.1)

        if to_add:
            session.add_all(to_add)
            session.commit()

        print("Finished storing team season schedules.")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate team season schedules into games table.")
    parser.add_argument("season_start_year", type=int, help="Starting year of the season (e.g., 2024 for 2024-2025)")
    args = parser.parse_args()
    populate_team_season_schedule(args.season_start_year)

