#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def verify_team_assignments():
    """Verify team assignments between raw database and projected rosters"""
    
    client = bigquery.Client()
    
    # Check for Mitchell Marner specifically
    query = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as current_team,
        p.position
    FROM `fantasy-snipe-ai.nhl_raw.players` p
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON p.current_team_id = t.id
    WHERE p.full_name LIKE "%Marner%" OR p.full_name LIKE "%Mitchell%"
    ORDER BY p.full_name
    """
    
    results = client.query(query).to_dataframe()
    
    print('Searching for Mitchell Marner:')
    print('=' * 40)
    if not results.empty:
        for _, row in results.iterrows():
            print(f'{row.player_name:25} | {row.current_team:4} | {row.position:2}')
    else:
        print('No players found matching Marner or Mitchell')
    
    # Also check what teams DAL and VGK are
    query2 = """
    SELECT 
        tri_code,
        name,
        id
    FROM `fantasy-snipe-ai.nhl_raw.teams`
    WHERE tri_code IN ("DAL", "VGK", "TOR")
    ORDER BY tri_code
    """
    
    results2 = client.query(query2).to_dataframe()
    
    print('\nTeam codes:')
    print('=' * 20)
    for _, row in results2.iterrows():
        print(f'{row.tri_code:4} | {row.name:20} | ID: {row.id}')
    
    # Now let's compare our projected rosters with the raw database
    print('\nComparing projected rosters with raw database:')
    print('=' * 50)
    
    # Check key players in our projected rosters
    query3 = """
    WITH projected_players AS (
        SELECT 
            team_abbr,
            player_name,
            position_type
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE player_name IN ("Mikko Rantanen", "Jakob Chychrun", "Sam Bennett", "Ivan Provorov")
    ),
    raw_players AS (
        SELECT 
            p.full_name as player_name,
            t.tri_code as current_team,
            p.position
        FROM `fantasy-snipe-ai.nhl_raw.players` p
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON p.current_team_id = t.id
        WHERE p.full_name IN ("Mikko Rantanen", "Jakob Chychrun", "Sam Bennett", "Ivan Provorov")
    )
    SELECT 
        pp.player_name,
        pp.team_abbr as projected_team,
        rp.current_team as raw_team,
        CASE 
            WHEN pp.team_abbr = rp.current_team THEN 'MATCH'
            ELSE 'MISMATCH'
        END as status
    FROM projected_players pp
    FULL OUTER JOIN raw_players rp ON pp.player_name = rp.player_name
    ORDER BY pp.player_name
    """
    
    results3 = client.query(query3).to_dataframe()
    
    for _, row in results3.iterrows():
        print(f'{row.player_name:20} | Projected: {row.projected_team:4} | Raw: {row.raw_team:4} | {row.status}')

if __name__ == "__main__":
    verify_team_assignments()
