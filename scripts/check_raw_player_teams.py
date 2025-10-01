#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def check_raw_player_teams():
    """Check current team assignments from raw database"""
    
    client = bigquery.Client()
    
    # Check the raw players table for current team assignments
    query = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as current_team,
        p.position,
        p.birth_date
    FROM `fantasy-snipe-ai.nhl_raw.players` p
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON p.current_team_id = t.id
    WHERE p.full_name IN ("Mikko Rantanen", "Mitchell Marner", "Jakob Chychrun", "Sam Bennett", "Ivan Provorov")
    ORDER BY p.full_name
    """
    
    results = client.query(query).to_dataframe()
    
    print('Current team assignments from raw database:')
    print('=' * 50)
    for _, row in results.iterrows():
        print(f'{row.player_name:20} | {row.current_team:4} | {row.position:2} | {row.birth_date}')
    
    print(f'\nTotal players found: {len(results)}')
    
    # Also check a few more key players
    query2 = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as current_team,
        p.position
    FROM `fantasy-snipe-ai.nhl_raw.players` p
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON p.current_team_id = t.id
    WHERE p.full_name IN ("Nikolaj Ehlers", "Brock Boeser", "Brad Marchand", "Trent Frederic", "Brock Nelson")
    ORDER BY p.full_name
    """
    
    results2 = client.query(query2).to_dataframe()
    
    print('\nAdditional key players:')
    print('=' * 30)
    for _, row in results2.iterrows():
        print(f'{row.player_name:20} | {row.current_team:4} | {row.position:2}')

if __name__ == "__main__":
    check_raw_player_teams()
