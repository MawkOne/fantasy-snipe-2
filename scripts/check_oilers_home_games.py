#!/usr/bin/env python3
"""
Check Oilers home games to see which side they start on
"""

import pandas as pd
from google.cloud import bigquery

def check_oilers_home_games():
    """
    Check Oilers home games and see what side they start on
    """
    client = bigquery.Client()
    
    # Check game data for Oilers home games
    print("Checking Oilers home games...")
    games_query = """
    SELECT 
        g.id as game_id,
        g.season,
        g.game_date,
        g.game_type,
        g.home_team_id,
        g.away_team_id,
        g.home_score,
        g.away_score,
        ht.tri_code as home_team,
        at.tri_code as away_team,
        CASE WHEN ht.tri_code = 'EDM' THEN 'HOME' ELSE 'AWAY' END as oilers_status
    FROM `fantasy-snipe-ai.nhl_raw.games` g
    JOIN `fantasy-snipe-ai.nhl_raw.teams` ht ON g.home_team_id = ht.id
    JOIN `fantasy-snipe-ai.nhl_raw.teams` at ON g.away_team_id = at.id
    WHERE g.season = 20242025
    AND (ht.tri_code = 'EDM' OR at.tri_code = 'EDM')
    ORDER BY g.game_date
    """
    
    games_df = client.query(games_query).to_dataframe()
    print(f"Found {len(games_df)} Oilers games in 2024-25")
    
    # Show first few games
    print("\nFirst 10 Oilers games:")
    print(games_df.head(10)[['game_id', 'game_date', 'home_team', 'away_team', 'oilers_status']].to_string(index=False))
    
    # Check home vs away split
    home_games = games_df[games_df['oilers_status'] == 'HOME']
    away_games = games_df[games_df['oilers_status'] == 'AWAY']
    
    print(f"\nOilers Home Games: {len(home_games)}")
    print(f"Oilers Away Games: {len(away_games)}")
    
    # Now let's check if there's any indication of which side teams start on
    print("\nChecking for side information in game data...")
    
    # Check if there are any fields that indicate starting side
    schema_query = """
    SELECT column_name, data_type, is_nullable
    FROM `fantasy-snipe-ai.nhl_raw.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'games'
    ORDER BY ordinal_position
    """
    
    schema_df = client.query(schema_query).to_dataframe()
    print("Games table schema:")
    print(schema_df.to_string(index=False))
    
    # Check if there's any side information in player_game_stats
    print("\nChecking player_game_stats for side information...")
    pgs_schema_query = """
    SELECT column_name, data_type, is_nullable
    FROM `fantasy-snipe-ai.nhl_raw.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'player_game_stats'
    ORDER BY ordinal_position
    """
    
    pgs_schema_df = client.query(pgs_schema_query).to_dataframe()
    print("Player_game_stats table schema:")
    print(pgs_schema_df.to_string(index=False))
    
    # Check if there's any side information in game_events
    print("\nChecking game_events for side information...")
    ge_schema_query = """
    SELECT column_name, data_type, is_nullable
    FROM `fantasy-snipe-ai.nhl_raw.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'game_events'
    ORDER BY ordinal_position
    """
    
    ge_schema_df = client.query(ge_schema_query).to_dataframe()
    print("Game_events table schema:")
    print(ge_schema_df.to_string(index=False))
    
    # Let's look at some actual game events to see if there's any side indication
    print("\nChecking sample game events for side information...")
    events_query = """
    SELECT 
        ge.id,
        ge.game_id,
        ge.period,
        ge.event_type,
        ge.coordinates_x,
        ge.coordinates_y,
        ge.team_id,
        t.tri_code as team,
        g.home_team_id,
        g.away_team_id,
        ht.tri_code as home_team,
        at.tri_code as away_team
    FROM `fantasy-snipe-ai.nhl_raw.game_events` ge
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON ge.team_id = t.id
    JOIN `fantasy-snipe-ai.nhl_raw.games` g ON ge.game_id = g.id
    JOIN `fantasy-snipe-ai.nhl_raw.teams` ht ON g.home_team_id = ht.id
    JOIN `fantasy-snipe-ai.nhl_raw.teams` at ON g.away_team_id = at.id
    WHERE g.season = 20242025
    AND (ht.tri_code = 'EDM' OR at.tri_code = 'EDM')
    AND ge.event_type = 'goal'
    AND ge.coordinates_x IS NOT NULL
    ORDER BY g.game_date, ge.period, ge.period_time
    LIMIT 20
    """
    
    events_df = client.query(events_query).to_dataframe()
    print("Sample goal events with team and coordinate info:")
    print(events_df[['game_id', 'period', 'event_type', 'coordinates_x', 'coordinates_y', 'team', 'home_team', 'away_team']].to_string(index=False))
    
    # Check if there's a pattern in coordinates by period for home vs away
    print("\nAnalyzing coordinate patterns by period for Oilers...")
    pattern_query = """
    WITH oilers_goals AS (
        SELECT 
            ge.game_id,
            ge.period,
            ge.coordinates_x,
            ge.coordinates_y,
            ge.team_id,
            t.tri_code as team,
            g.home_team_id,
            g.away_team_id,
            ht.tri_code as home_team,
            at.tri_code as away_team,
            CASE WHEN ht.tri_code = 'EDM' THEN 'HOME' ELSE 'AWAY' END as oilers_status
        FROM `fantasy-snipe-ai.nhl_raw.game_events` ge
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON ge.team_id = t.id
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON ge.game_id = g.id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` ht ON g.home_team_id = ht.id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` at ON g.away_team_id = at.id
        WHERE g.season = 20242025
        AND t.tri_code = 'EDM'
        AND ge.event_type = 'goal'
        AND ge.coordinates_x IS NOT NULL
    )
    SELECT 
        oilers_status,
        period,
        COUNT(*) as goal_count,
        AVG(coordinates_x) as avg_x,
        AVG(coordinates_y) as avg_y,
        MIN(coordinates_x) as min_x,
        MAX(coordinates_x) as max_x
    FROM oilers_goals
    GROUP BY oilers_status, period
    ORDER BY oilers_status, period
    """
    
    pattern_df = client.query(pattern_query).to_dataframe()
    print("Oilers goal coordinate patterns by period and home/away status:")
    print(pattern_df.to_string(index=False))

if __name__ == "__main__":
    check_oilers_home_games()
