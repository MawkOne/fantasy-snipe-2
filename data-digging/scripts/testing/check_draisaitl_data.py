#!/usr/bin/env python3
"""
Check what data is available for Leon Draisaitl
"""

import pandas as pd
from google.cloud import bigquery

def check_draisaitl_data():
    """
    Check what data is available for Leon Draisaitl
    """
    client = bigquery.Client()
    
    # Check players table
    print("Checking players table...")
    players_query = """
    SELECT player_id, full_name, position
    FROM `fantasy-snipe-ai.nhl_raw.players`
    WHERE full_name LIKE '%Draisaitl%' OR full_name LIKE '%Leon%'
    """
    players_df = client.query(players_query).to_dataframe()
    print(f"Found {len(players_df)} players matching Draisaitl:")
    print(players_df)
    
    if not players_df.empty:
        player_id = players_df.iloc[0]['player_id']
        print(f"\\nUsing player_id: {player_id}")
        
        # Check game_events for this player
        print("\\nChecking game_events...")
        events_query = f"""
        SELECT 
            event_type,
            COUNT(*) as count
        FROM `fantasy-snipe-ai.nhl_raw.game_events`
        WHERE primary_player_id = {player_id}
        GROUP BY event_type
        ORDER BY count DESC
        """
        events_df = client.query(events_query).to_dataframe()
        print("Event types for this player:")
        print(events_df)
        
        # Check shot events specifically
        print("\\nChecking shot events...")
        shots_query = f"""
        SELECT 
            event_type,
            secondary_type,
            COUNT(*) as count
        FROM `fantasy-snipe-ai.nhl_raw.game_events`
        WHERE primary_player_id = {player_id}
        AND event_type IN ('SHOT', 'GOAL', 'MISSED_SHOT', 'BLOCKED_SHOT')
        GROUP BY event_type, secondary_type
        ORDER BY count DESC
        """
        shots_df = client.query(shots_query).to_dataframe()
        print("Shot events for this player:")
        print(shots_df)
        
        # Check if coordinates are available
        print("\\nChecking coordinate data...")
        coords_query = f"""
        SELECT 
            COUNT(*) as total_events,
            COUNT(coordinates_x) as events_with_x,
            COUNT(coordinates_y) as events_with_y,
            COUNT(CASE WHEN coordinates_x IS NOT NULL AND coordinates_y IS NOT NULL THEN 1 END) as events_with_both_coords
        FROM `fantasy-snipe-ai.nhl_raw.game_events`
        WHERE primary_player_id = {player_id}
        AND event_type IN ('SHOT', 'GOAL', 'MISSED_SHOT', 'BLOCKED_SHOT')
        """
        coords_df = client.query(coords_query).to_dataframe()
        print("Coordinate availability:")
        print(coords_df)
        
        # Check recent games
        print("\\nChecking recent games...")
        games_query = f"""
        SELECT 
            g.season,
            COUNT(DISTINCT ge.game_id) as games_with_events,
            COUNT(*) as total_events
        FROM `fantasy-snipe-ai.nhl_raw.game_events` ge
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON ge.game_id = g.id
        WHERE ge.primary_player_id = {player_id}
        GROUP BY g.season
        ORDER BY g.season DESC
        """
        games_df = client.query(games_query).to_dataframe()
        print("Games by season:")
        print(games_df)

if __name__ == "__main__":
    check_draisaitl_data()
