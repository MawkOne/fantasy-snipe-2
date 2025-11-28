import os
import sys
import requests
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path to allow importing from `src`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Team, create_tables

def populate_teams():
    """
    Fetches team data from the NHL API and stores it in the database.
    Checks for existing teams to prevent duplicates.
    """
    # Step 1: Fetch data from the NHL API
    print("Fetching team data from the NHL API...")
    teams_data = []
    # Primary endpoint
    try:
        url = "https://api.nhle.com/stats/rest/en/team"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        teams_data = response.json().get('data', []) or []
    except requests.exceptions.RequestException:
        teams_data = []
    # Fallback endpoint (more reliable): statsapi teams
    if not teams_data:
        try:
            url2 = "https://statsapi.web.nhl.com/api/v1/teams"
            r2 = requests.get(url2, timeout=20)
            r2.raise_for_status()
            payload = r2.json() or {}
            for t in payload.get('teams', []) or []:
                teams_data.append({
                    'id': t.get('id'),
                    'franchiseId': (t.get('franchise') or {}).get('franchiseId'),
                    'fullName': t.get('name'),
                    'leagueId': None,
                    'rawTricode': t.get('abbreviation'),
                    'triCode': t.get('abbreviation'),
                })
        except requests.exceptions.RequestException as e:
            print(f"Error fetching teams from fallback API: {e}")
            teams_data = []
    if not teams_data:
        print("No team data was returned from any API.")
        return
    print(f"Successfully fetched {len(teams_data)} teams.")

    # Step 2: Connect to the database and create a session
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

    # Step 3: Iterate through teams, check for existence, and add if new
    print("Processing and storing team data...")
    new_teams_count = 0
    try:
        for team_data in teams_data:
            # Check if a team with the same ID already exists
            exists = session.query(Team.id).filter_by(id=team_data['id']).first() is not None
            if exists:
                continue  # Skip if team already in the database
            
            # Create a new Team object and add it to the session
            new_team = Team(
                id=team_data.get('id'),
                franchise_id=team_data.get('franchiseId'),
                full_name=team_data.get('fullName'),
                league_id=team_data.get('leagueId'),
                raw_tricode=team_data.get('rawTricode'),
                tri_code=team_data.get('triCode')
            )
            session.add(new_team)
            new_teams_count += 1
        
        if new_teams_count > 0:
            session.commit()
            print(f"Successfully stored {new_teams_count} new teams in the database.")
        else:
            print("No new teams to add to the database.")

    except Exception as e:
        print(f"An error occurred during database operation: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")

if __name__ == "__main__":
    populate_teams()
