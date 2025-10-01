import argparse
import requests
import time
from google.cloud import bigquery
from typing import Dict, List, Optional
import json

def ensure_tables(client: bigquery.Client) -> None:
    """Create the player_details table if it doesn't exist."""
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_raw`").result()
    
    client.query("""
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_raw.player_details` (
          player_id INT64,
          full_name STRING,
          first_name STRING,
          last_name STRING,
          position STRING,
          birth_date DATE,
          birth_city STRING,
          birth_state_province STRING,
          birth_country STRING,
          shoots_catches STRING,
          height_inches INT64,
          height_cm INT64,
          weight_pounds INT64,
          weight_kg INT64,
          draft_year INT64,
          draft_team STRING,
          draft_round INT64,
          draft_pick INT64,
          current_team_id INT64,
          current_team_abbrev STRING,
          sweater_number INT64,
          is_active BOOL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """).result()

def get_player_details(player_id: int) -> Optional[Dict]:
    """Fetch player details from NHL API."""
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching player {player_id}: {e}")
        return None

def parse_player_data(data: Dict) -> Dict:
    """Parse NHL API response into our schema."""
    return {
        'player_id': data.get('playerId'),
        'full_name': f"{data.get('firstName', {}).get('default', '')} {data.get('lastName', {}).get('default', '')}".strip(),
        'first_name': data.get('firstName', {}).get('default', ''),
        'last_name': data.get('lastName', {}).get('default', ''),
        'position': data.get('position', ''),
        'birth_date': data.get('birthDate'),
        'birth_city': data.get('birthCity', {}).get('default', ''),
        'birth_state_province': data.get('birthStateProvince', {}).get('default', ''),
        'birth_country': data.get('birthCountry', ''),
        'shoots_catches': data.get('shootsCatches', ''),
        'height_inches': data.get('heightInInches'),
        'height_cm': data.get('heightInCentimeters'),
        'weight_pounds': data.get('weightInPounds'),
        'weight_kg': data.get('weightInKilograms'),
        'draft_year': data.get('draftDetails', {}).get('year'),
        'draft_team': data.get('draftDetails', {}).get('teamAbbrev', ''),
        'draft_round': data.get('draftDetails', {}).get('round'),
        'draft_pick': data.get('draftDetails', {}).get('overallPick'),
        'current_team_id': data.get('currentTeamId'),
        'current_team_abbrev': data.get('currentTeamAbbrev', ''),
        'sweater_number': data.get('sweaterNumber'),
        'is_active': data.get('isActive', False)
    }

def load_player_details(client: bigquery.Client, player_data: Dict) -> None:
    """Load player details into BigQuery using direct insert."""
    
    # Convert to DataFrame for easier handling
    import pandas as pd
    import pandas_gbq
    df = pd.DataFrame([player_data])
    
    # Use pandas_gbq for insertion
    pandas_gbq.to_gbq(
        df,
        destination_table='fantasy-snipe-ai.nhl_raw.player_details',
        project_id='fantasy-snipe-ai',
        if_exists='replace'  # Replace for now, we'll add proper upsert later
    )

def get_all_player_ids(client: bigquery.Client) -> List[int]:
    """Get all unique player IDs from our data."""
    query = """
    SELECT DISTINCT player_id 
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
    ORDER BY player_id
    """
    
    result = client.query(query).result()
    return [row.player_id for row in result]

def main():
    parser = argparse.ArgumentParser(description='Ingest player details from NHL API')
    parser.add_argument('--player-id', type=int, help='Specific player ID to ingest')
    parser.add_argument('--all-players', action='store_true', help='Ingest all players from our data')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between API calls (seconds)')
    args = parser.parse_args()
    
    client = bigquery.Client()
    ensure_tables(client)
    
    if args.player_id:
        # Ingest specific player
        print(f"Ingesting player {args.player_id}...")
        data = get_player_details(args.player_id)
        if data:
            player_data = parse_player_data(data)
            load_player_details(client, player_data)
            print(f"Successfully ingested {player_data['full_name']}")
        else:
            print(f"Failed to fetch data for player {args.player_id}")
    
    elif args.all_players:
        # Ingest all players
        print("Getting list of all player IDs...")
        player_ids = get_all_player_ids(client)
        print(f"Found {len(player_ids)} players to process")
        
        success_count = 0
        error_count = 0
        
        for i, player_id in enumerate(player_ids):
            if i % 100 == 0:
                print(f"Processing player {i+1}/{len(player_ids)} (ID: {player_id})")
            
            data = get_player_details(player_id)
            if data:
                try:
                    player_data = parse_player_data(data)
                    load_player_details(client, player_data)
                    success_count += 1
                except Exception as e:
                    print(f"Error processing player {player_id}: {e}")
                    error_count += 1
            else:
                error_count += 1
            
            # Rate limiting
            time.sleep(args.delay)
        
        print(f"\nIngestion complete!")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
    
    else:
        print("Please specify --player-id or --all-players")

if __name__ == "__main__":
    main()
