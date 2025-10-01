#!/usr/bin/env python3
"""
Ingest individual player stats from NHL Stats API into BigQuery.
This provides individual scoring data (goals, assists, points) that we're missing.
"""

import os
import sys
import requests
import time
from typing import Dict, List, Optional
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_seasons() -> List[int]:
    """Get list of seasons to process (2013-14 through 2024-25)."""
    seasons = []
    for year in range(2013, 2025):
        season_id = int(f"{year}{year+1}")
        seasons.append(season_id)
    return seasons

def fetch_player_stats(season_id: int, limit: int = 1000, offset: int = 0) -> List[Dict]:
    """Fetch player stats for a specific season from NHL Stats API."""
    url = "https://api.nhle.com/stats/rest/en/skater/summary"
    params = {
        "limit": limit,
        "start": offset,
        "cayenneExp": f"seasonId={season_id}"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching player stats for season {season_id}: {e}")
        return []

def process_player_stats(stats_data: List[Dict]) -> pd.DataFrame:
    """Process raw player stats data into a clean DataFrame."""
    if not stats_data:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(stats_data)
    
    # Rename columns to match our schema
    column_mapping = {
        "playerId": "player_id",
        "skaterFullName": "full_name",
        "lastName": "last_name",
        "teamAbbrevs": "team_abbrev",
        "seasonId": "season",
        "gamesPlayed": "games_played",
        "goals": "goals",
        "assists": "assists", 
        "points": "points",
        "pointsPerGame": "points_per_game",
        "evGoals": "ev_goals",
        "evPoints": "ev_points",
        "ppGoals": "pp_goals",
        "ppPoints": "pp_points",
        "shGoals": "sh_goals",
        "shPoints": "sh_points",
        "timeOnIcePerGame": "toi_seconds_per_game",
        "shots": "shots",
        "shootingPct": "shooting_pct",
        "faceoffWinPct": "faceoff_win_pct",
        "penaltyMinutes": "pim",
        "plusMinus": "plus_minus",
        "gameWinningGoals": "game_winning_goals",
        "otGoals": "ot_goals",
        "positionCode": "position",
        "shootsCatches": "shoots_catches"
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Calculate per-60 rates
    df["goals_60"] = (df["goals"] * 3600) / df["toi_seconds_per_game"]
    df["assists_60"] = (df["assists"] * 3600) / df["toi_seconds_per_game"]
    df["points_60"] = (df["points"] * 3600) / df["toi_seconds_per_game"]
    df["shots_60"] = (df["shots"] * 3600) / df["toi_seconds_per_game"]
    
    # Convert TOI to minutes
    df["toi_minutes_per_game"] = df["toi_seconds_per_game"] / 60.0
    
    # Handle NaN values
    df = df.fillna(0)
    
    return df

def load_to_bigquery(df: pd.DataFrame, table_id: str) -> None:
    """Load DataFrame to BigQuery table."""
    if df.empty:
        print("No data to load")
        return
    
    client = bigquery.Client()
    
    # Configure load job
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace all data
        create_disposition="CREATE_IF_NEEDED"
    )
    
    try:
        # Load data
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for job to complete
        
        print(f"Loaded {len(df)} records to {table_id}")
        
    except Exception as e:
        print(f"Error loading data to BigQuery: {e}")
        raise

def create_table_schema() -> None:
    """Create the player_stats table schema in BigQuery."""
    client = bigquery.Client()
    
    schema = [
        bigquery.SchemaField("player_id", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("full_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("team_abbrev", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("season", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("games_played", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("assists", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("points", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("points_per_game", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("ev_goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ev_points", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("pp_goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("pp_points", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("sh_goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("sh_points", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("toi_seconds_per_game", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("toi_minutes_per_game", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("shots", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("shooting_pct", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("faceoff_win_pct", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("pim", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("plus_minus", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("game_winning_goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ot_goals", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("position", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("shoots_catches", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("goals_60", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("assists_60", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("points_60", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("shots_60", "FLOAT64", mode="REQUIRED"),
    ]
    
    table_id = "fantasy-snipe-ai.nhl_raw.player_stats"
    
    try:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        print(f"Created table {table_id}")
    except Exception as e:
        if "already exists" in str(e) or "Already Exists" in str(e):
            print(f"Table {table_id} already exists")
        else:
            print(f"Error creating table: {e}")
            raise

def main():
    """Main function to ingest player stats for all seasons."""
    print("Starting player stats ingestion...")
    
    # Create table schema
    create_table_schema()
    
    # Get seasons to process
    seasons = get_seasons()
    print(f"Processing {len(seasons)} seasons: {seasons}")
    
    all_data = []
    
    for season in seasons:
        print(f"\nProcessing season {season}...")
        
        # First, get the total count to know how many records to fetch
        print(f"  Getting total record count...")
        url = "https://api.nhle.com/stats/rest/en/skater/summary"
        params = {"limit": 1, "start": 0, "cayenneExp": f"seasonId={season}"}
        response = requests.get(url, params=params)
        total_records = response.json().get("total", 0)
        print(f"  Total records for season {season}: {total_records}")
        
        if total_records == 0:
            print(f"  No data found for season {season}")
            continue
        
        # Fetch all data for this season (handle pagination)
        offset = 0
        limit = 100  # Use smaller limit to ensure we get all data
        season_data = []
        
        while offset < total_records:
            print(f"  Fetching offset {offset}...")
            data = fetch_player_stats(season, limit, offset)
            
            if not data:
                print(f"  No more data at offset {offset}")
                break
                
            season_data.extend(data)
            offset += limit
            
            # Rate limiting
            time.sleep(0.1)
            
            # Safety check to avoid infinite loops
            if offset > total_records + 1000:  # Safety buffer
                print(f"  Reached safety limit for season {season}")
                break
        
        print(f"  Fetched {len(season_data)} records for season {season}")
        
        if season_data:
            # Process the data
            df = process_player_stats(season_data)
            if not df.empty:
                all_data.append(df)
        
        # Rate limiting between seasons
        time.sleep(1)
    
    # Combine all data and load to BigQuery
    if all_data:
        print(f"\nCombining {len(all_data)} seasons of data...")
        combined_df = pd.concat(all_data, ignore_index=True)
        
        print(f"Total records: {len(combined_df)}")
        print(f"Seasons covered: {sorted(combined_df['season'].unique())}")
        
        # Load to BigQuery
        table_id = "fantasy-snipe-ai.nhl_raw.player_stats"
        load_to_bigquery(combined_df, table_id)
        
        print("Player stats ingestion completed!")
    else:
        print("No data to process")

if __name__ == "__main__":
    main()
