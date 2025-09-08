import os
import sys
import requests
import time
import argparse
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Player, Game, create_tables

def parse_date(date_string):
    """Parses a date string 'YYYY-MM-DD' into a datetime object."""
    return datetime.strptime(date_string, '%Y-%m-%d')

def populate_all_games_from_logs(season_start_year, batch_size=100):
    """
    Ensures the 'games' table is complete by finding all unique game IDs from 
    player logs for a given season and backfilling any missing games.
    """
    season_id = f"{season_start_year}{season_start_year + 1}"
    
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
        players = session.query(Player.id).all()
        if not players:
            print("No players found in database. Please run populate_players.py first.")
            return

        print(f"Found {len(players)} players. Scanning all game logs for unique game IDs for season {season_id}...")
        
        all_game_ids = set()
        for i, player_tuple in enumerate(players):
            player_id = player_tuple[0]
            for game_type in [2, 3]:
                url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/{game_type}"
                try:
                    response = requests.get(url)
                    if response.status_code == 404: continue
                    response.raise_for_status()
                    game_logs = response.json().get('gameLog', [])
                    for log in game_logs:
                        all_game_ids.add(log['gameId'])
                except requests.exceptions.RequestException:
                    continue
            print(f"Scanned player {i+1}/{len(players)}", end='\r')
        
        print(f"\nFound a total of {len(all_game_ids)} unique games played in season {season_id}.")

        existing_game_ids = {res[0] for res in session.query(Game.id).filter(Game.id.in_(all_game_ids)).all()}
        missing_game_ids = list(all_game_ids - existing_game_ids)

        if not missing_game_ids:
            print("All games for this season are already in the database.")
            return

        print(f"Found {len(missing_game_ids)} new games to add. Fetching details in batches...")

        total_added = 0
        for i in range(0, len(missing_game_ids), batch_size):
            batch = missing_game_ids[i:i + batch_size]
            for game_id in batch:
                url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    game_data = response.json()

                    new_game = Game(
                        id=game_data.get('id'), season=game_data.get('season'),
                        game_type=game_data.get('gameType'), game_date=parse_date(game_data['gameDate']),
                        game_state=game_data.get('gameState'),
                        home_team_id=game_data.get('homeTeam', {}).get('id'),
                        away_team_id=game_data.get('awayTeam', {}).get('id'),
                        home_score=game_data.get('homeTeam', {}).get('score'),
                        away_score=game_data.get('awayTeam', {}).get('score'),
                    )
                    session.add(new_game)
                    total_added += 1
                    time.sleep(0.1)
                except requests.exceptions.RequestException as e:
                    print(f"\nError fetching details for game {game_id}: {e}")
            
            session.commit()
            print(f"Committed batch. Total games added so far: {total_added}")

        print(f"\nSuccessfully stored a total of {total_added} new games.")

    except Exception as e:
        print(f"\nA critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate the database with all games from a season by scanning player logs.")
    parser.add_argument("season_start_year", type=int, help="Starting year of the season (e.g., 2023 for 2023-2024).")
    args = parser.parse_args()
    
    populate_all_games_from_logs(season_start_year=args.season_start_year)
