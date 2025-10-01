#!/usr/bin/env python3
"""
Simple check for Oilers home games
"""

import pandas as pd
from google.cloud import bigquery

def check_oilers_games():
    """
    Simple check for Oilers games
    """
    client = bigquery.Client()
    
    # Simple query to check Oilers games
    query = """
    SELECT 
        g.id as game_id,
        g.season,
        g.game_date,
        g.home_team_id,
        g.away_team_id,
        g.home_score,
        g.away_score
    FROM `fantasy-snipe-ai.nhl_raw.games` g
    WHERE g.season = 20242025
    AND (g.home_team_id = 22 OR g.away_team_id = 22)
    ORDER BY g.game_date
    LIMIT 10
    """
    
    try:
        games_df = client.query(query).to_dataframe()
        print(f"Found {len(games_df)} Oilers games")
        print(games_df)
    except Exception as e:
        print(f"Error: {e}")
        
        # Try to find Oilers team ID first
        print("\nTrying to find Oilers team ID...")
        team_query = """
        SELECT id, tri_code, name
        FROM `fantasy-snipe-ai.nhl_raw.teams`
        WHERE tri_code = 'EDM'
        """
        
        try:
            team_df = client.query(team_query).to_dataframe()
            print("Oilers team info:")
            print(team_df)
        except Exception as e2:
            print(f"Team query error: {e2}")

if __name__ == "__main__":
    check_oilers_games()
