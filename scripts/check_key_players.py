#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def check_key_players():
    """Check key players that should be in rosters"""
    
    client = bigquery.Client()
    
    # Check for key missing players
    key_players = ['Mitchell Marner', 'Mikko Rantanen', 'Jakob Chychrun', 'Sam Bennett', 'Ivan Provorov']
    
    print('Checking key players that should be in rosters:')
    print('=' * 50)
    
    for player in key_players:
        query = f"""
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE player_name = '{player}'
        """
        
        results = client.query(query).to_dataframe()
        
        if not results.empty:
            row = results.iloc[0]
            print(f'{player:20} | {row.team_abbr:4} | {row.position_type:8} | {row.toi_tier}')
        else:
            print(f'{player:20} | NOT FOUND')
    
    # Also check some players that might be on wrong teams
    print('\nChecking players that might be on wrong teams:')
    print('=' * 50)
    
    # Check Mikko Rantanen - should be on COL, not DAL
    query = """
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    WHERE player_name = 'Mikko Rantanen'
    """
    
    results = client.query(query).to_dataframe()
    if not results.empty:
        row = results.iloc[0]
        print(f'Mikko Rantanen: {row.team_abbr} (should be COL)')
    
    # Check Mitchell Marner - should be on TOR
    query = """
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    WHERE player_name = 'Mitchell Marner'
    """
    
    results = client.query(query).to_dataframe()
    if not results.empty:
        row = results.iloc[0]
        print(f'Mitchell Marner: {row.team_abbr} (should be TOR)')
    else:
        print('Mitchell Marner: NOT FOUND (should be TOR)')

if __name__ == "__main__":
    check_key_players()
