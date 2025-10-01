import argparse
import requests
import time
from typing import Dict, List, Optional
from google.cloud import bigquery
import pandas as pd
import pandas_gbq
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_player_details(player_id: int) -> Optional[Dict]:
    """Fetch detailed player information from NHL API."""
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch player {player_id}: {e}")
        return None

def transform_player_data(player_raw_data: Dict) -> Dict:
    """Transform raw player data into our schema."""
    
    # Extract nested data safely
    def safe_get(data, key, default=None):
        if isinstance(data, dict):
            return data.get(key, default)
        return default
    
    def safe_get_nested(data, keys, default=None):
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    return {
        'player_id': player_raw_data.get('playerId'),
        'is_active': player_raw_data.get('isActive', False),
        'current_team_id': player_raw_data.get('currentTeamId'),
        'current_team_abbrev': player_raw_data.get('currentTeamAbbrev'),
        'full_team_name': safe_get_nested(player_raw_data, ['fullTeamName', 'default']),
        'team_common_name': safe_get_nested(player_raw_data, ['teamCommonName', 'default']),
        'team_place_name': safe_get_nested(player_raw_data, ['teamPlaceNameWithPreposition', 'default']),
        'first_name': safe_get_nested(player_raw_data, ['firstName', 'default']),
        'last_name': safe_get_nested(player_raw_data, ['lastName', 'default']),
        'sweater_number': player_raw_data.get('sweaterNumber'),
        'position': player_raw_data.get('position'),
        'height_inches': player_raw_data.get('heightInInches'),
        'height_cm': player_raw_data.get('heightInCentimeters'),
        'weight_pounds': player_raw_data.get('weightInPounds'),
        'weight_kg': player_raw_data.get('weightInKilograms'),
        'birth_date': player_raw_data.get('birthDate'),
        'birth_city': safe_get_nested(player_raw_data, ['birthCity', 'default']),
        'birth_state_province': safe_get_nested(player_raw_data, ['birthStateProvince', 'default']),
        'birth_country': player_raw_data.get('birthCountry'),
        'shoots_catches': player_raw_data.get('shootsCatches'),
        'draft_year': safe_get_nested(player_raw_data, ['draftDetails', 'year']),
        'draft_team_abbrev': safe_get_nested(player_raw_data, ['draftDetails', 'teamAbbrev']),
        'draft_round': safe_get_nested(player_raw_data, ['draftDetails', 'round']),
        'draft_pick_in_round': safe_get_nested(player_raw_data, ['draftDetails', 'pickInRound']),
        'draft_overall_pick': safe_get_nested(player_raw_data, ['draftDetails', 'overallPick']),
        'headshot_url': player_raw_data.get('headshot'),
        'hero_image_url': player_raw_data.get('heroImage'),
        'team_logo_url': player_raw_data.get('teamLogo'),
        'full_name': f"{safe_get_nested(player_raw_data, ['firstName', 'default'], '')} {safe_get_nested(player_raw_data, ['lastName', 'default'], '')}".strip()
    }

def ensure_players_table(client: bigquery.Client) -> None:
    """Create or update the players table with comprehensive schema."""
    
    # Drop and recreate the table with the new comprehensive schema
    client.query("DROP TABLE IF EXISTS `fantasy-snipe-ai.nhl_raw.players`").result()
    
    create_query = """
    CREATE TABLE `fantasy-snipe-ai.nhl_raw.players` (
      player_id INT64,
      is_active BOOL,
      current_team_id INT64,
      current_team_abbrev STRING,
      full_team_name STRING,
      team_common_name STRING,
      team_place_name STRING,
      first_name STRING,
      last_name STRING,
      sweater_number INT64,
      position STRING,
      height_inches INT64,
      height_cm INT64,
      weight_pounds INT64,
      weight_kg INT64,
      birth_date DATE,
      birth_city STRING,
      birth_state_province STRING,
      birth_country STRING,
      shoots_catches STRING,
      draft_year INT64,
      draft_team_abbrev STRING,
      draft_round INT64,
      draft_pick_in_round INT64,
      draft_overall_pick INT64,
      headshot_url STRING,
      hero_image_url STRING,
      team_logo_url STRING,
      full_name STRING
    )
    """
    
    client.query(create_query).result()
    logger.info("Created comprehensive players table")

def load_player_details(client: bigquery.Client, player_data: Dict) -> None:
    """Load player details into BigQuery using direct insert."""
    
    # Convert to DataFrame for easier handling
    df = pd.DataFrame([player_data])
    
    # Use pandas_gbq for insertion
    pandas_gbq.to_gbq(
        df,
        destination_table='fantasy-snipe-ai.nhl_raw.players',
        project_id='fantasy-snipe-ai',
        if_exists='append'
    )

def get_all_player_ids_from_seasons(client: bigquery.Client, start_season: int, end_season: int) -> List[int]:
    """Get all unique player IDs from specified seasons in reverse order."""
    
    # Get seasons in reverse order (2025 to 2013)
    seasons = []
    for year in range(end_season, start_season - 1, -1):
        season_id = int(f"{year}{year+1}")
        seasons.append(season_id)
    
    logger.info(f"Processing seasons in reverse order: {seasons}")
    
    # Get unique player IDs from all specified seasons
    season_conditions = " OR ".join([f"g.season = {season}" for season in seasons])
    
    query = f"""
    SELECT DISTINCT player_id
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
    JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = pgm.game_id
    WHERE {season_conditions}
    ORDER BY player_id
    """
    
    job_config = bigquery.QueryJobConfig(use_query_cache=True)
    result = client.query(query, job_config=job_config).result()
    
    player_ids = [row.player_id for row in result]
    logger.info(f"Found {len(player_ids)} unique player IDs across seasons {start_season}-{end_season}")
    
    return player_ids

def process_player_batch(client: bigquery.Client, player_ids: List[int], delay: float = 0.1) -> None:
    """Process a batch of players with concurrency."""
    
    def process_single_player(player_id: int) -> bool:
        try:
            player_raw_data = fetch_player_details(player_id)
            if player_raw_data:
                player_details = transform_player_data(player_raw_data)
                load_player_details(client, player_details)
                logger.info(f"Successfully processed player {player_id}: {player_details['full_name']}")
                return True
            else:
                logger.warning(f"Failed to fetch data for player {player_id}")
                return False
        except Exception as e:
            logger.error(f"Error processing player {player_id}: {e}")
            return False
    
    # Process with ThreadPoolExecutor for concurrency
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(process_single_player, player_id): player_id for player_id in player_ids}
        
        successful = 0
        failed = 0
        
        for future in as_completed(futures):
            player_id = futures[future]
            try:
                if future.result():
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Future failed for player {player_id}: {e}")
                failed += 1
            
            # Add delay between requests
            time.sleep(delay)
    
    logger.info(f"Batch complete: {successful} successful, {failed} failed")

def main():
    parser = argparse.ArgumentParser(description='Ingest comprehensive NHL player details from API to BigQuery.')
    parser.add_argument('--player-id', type=int, help='Specific player ID to ingest (e.g., 8478402 for McDavid)')
    parser.add_argument('--all-players', action='store_true', help='Ingest details for all unique players')
    parser.add_argument('--start-season', type=int, default=2013, help='Start season (e.g., 2013 for 2013-14)')
    parser.add_argument('--end-season', type=int, default=2025, help='End season (e.g., 2025 for 2025-26)')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between API requests in seconds')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of players to process in each batch')
    args = parser.parse_args()
    
    client = bigquery.Client()
    
    # Ensure the table exists with the new schema
    ensure_players_table(client)
    
    if args.player_id:
        logger.info(f"Ingesting player {args.player_id}...")
        player_raw_data = fetch_player_details(args.player_id)
        if player_raw_data:
            player_details = transform_player_data(player_raw_data)
            load_player_details(client, player_details)
            logger.info(f"Successfully ingested {player_details['full_name']}")
        else:
            logger.error(f"Failed to fetch details for player {args.player_id}")
    else:
        logger.info(f"Ingesting details for all unique players from seasons {args.start_season}-{args.end_season}...")
        player_ids = get_all_player_ids_from_seasons(client, args.start_season, args.end_season)
        
        # Process in batches
        total_players = len(player_ids)
        logger.info(f"Processing {total_players} players in batches of {args.batch_size}")
        
        for i in range(0, total_players, args.batch_size):
            batch = player_ids[i:i + args.batch_size]
            batch_num = (i // args.batch_size) + 1
            total_batches = (total_players + args.batch_size - 1) // args.batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} players)")
            process_player_batch(client, batch, args.delay)
            
            # Progress update
            processed = min(i + args.batch_size, total_players)
            logger.info(f"Progress: {processed}/{total_players} players processed")
        
        logger.info("Completed ingestion of all player details.")

if __name__ == "__main__":
    main()
