import os
import sys
import requests
import time
from datetime import datetime
import argparse
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Team, Player, create_tables

def populate_players_for_season(session, team, season_id):
    """Fetches and stores players for a single team and season."""
    if not team.tri_code:
        print(f"Skipping team {team.full_name} due to missing tri_code.")
        return 0
    
    url = f"https://api-web.nhle.com/v1/roster/{team.tri_code}/{season_id}"
    new_players_count = 0
    
    try:
        response = requests.get(url)
        # Some old seasons might not have rosters, so we'll just skip them
        if response.status_code == 404:
            return 0
        response.raise_for_status()
        roster = response.json()
        
        all_players_data = roster.get('forwards', []) + roster.get('defensemen', []) + roster.get('goalies', [])
        
        if not all_players_data:
            return 0

        for player_data in all_players_data:
            player_id = player_data.get('id')
            if not player_id:
                continue
                
            exists = session.query(Player.id).filter_by(id=player_id).first() is not None
            if exists:
                continue

            first_name = player_data.get('firstName', {}).get('default', '')
            last_name = player_data.get('lastName', {}).get('default', '')

            new_player = Player(
                id=player_id,
                full_name=f"{first_name} {last_name}".strip(),
                first_name=first_name,
                last_name=last_name,
                sweater_number=player_data.get('sweaterNumber'),
                position_code=player_data.get('positionCode'),
                headshot_url=player_data.get('headshot'),
                team_id=team.id,
                is_active=True # We assume players from recent rosters are active
            )
            session.add(new_player)
            new_players_count += 1
            
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch roster for team {team.tri_code} for season {season_id}. Error: {e}")
    except Exception as e:
        print(f"An error occurred while processing team {team.tri_code} for season {season_id}: {e}")
    
    return new_players_count

def populate_players(years_back=3, start_year=2024):
    """
    Fetches player roster data for each team for the last N seasons.
    """
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
            print("No teams found in the database. Please populate teams first.")
            return

        total_new_players = 0
        # Go back from provided start year (e.g., 2025 for 2025-2026)
        current_season_start_year = int(start_year)
        
        for i in range(years_back):
            season_start_year = current_season_start_year - i
            season_id = f"{season_start_year}{season_start_year + 1}"
            print(f"\n--- Fetching players for {season_start_year}-{season_start_year+1} season (ID: {season_id}) ---")
            
            season_new_players = 0
            for team in teams:
                season_new_players += populate_players_for_season(session, team, season_id)
                time.sleep(0.1) # Be respectful to the API
            
            if season_new_players > 0:
                print(f"Found {season_new_players} new players for season {season_id}.")
                session.commit()
            else:
                print(f"No new players found for season {season_id}.")

            total_new_players += season_new_players

        print(f"\nFinished processing. Stored a total of {total_new_players} new players.")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Populate NHL players by team rosters for given seasons")
    ap.add_argument("--start-year", type=int, default=2024, help="Season start year (e.g., 2025 for 2025-26)")
    ap.add_argument("--years-back", type=int, default=3, help="How many seasons to include starting from start-year")
    args = ap.parse_args()
    populate_players(years_back=args.years_back, start_year=args.start_year)
