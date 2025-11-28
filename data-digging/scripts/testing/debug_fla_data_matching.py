#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def debug_fla_data_matching():
    """Debug why FLA elite players aren't being matched properly"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("DEBUGGING FLA DATA MATCHING ISSUE")
    print("="*80)
    
    # Check FLA data matching issue
    query = """
    SELECT 
        pr.player_name as roster_name,
        pr.team_abbr as roster_team,
        ps.player_name as stats_name,
        ps.team as stats_team,
        ps.current_age,
        ps.points_60,
        ps.points,
        CASE 
            WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= 2.5 AND (ps.points >= 80 OR ps.points = 0) THEN "Elite"
            WHEN ps.position = "D" AND ps.points_60 >= 1.8 AND (ps.points >= 50 OR ps.points = 0) THEN "Elite"
            ELSE "Not Elite"
        END as performance_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated` pr
    LEFT JOIN (
        SELECT 
            t.tri_code as team,
            p.full_name as player_name,
            p.position,
            EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM p.birth_date) as current_age,
            pst.pts60_weighted as points_60,
            COALESCE(ps.points, 0) as points
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
            ON pst.player_id = ps.player_id 
            AND pst.season = ps.season
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position IN ("C", "L", "R", "D")
        AND pst.pts60_weighted IS NOT NULL
        AND t.tri_code = "FLA"
    ) ps ON pr.player_name = ps.player_name AND pr.team_abbr = ps.team
    WHERE pr.team_abbr = "FLA"
    ORDER BY pr.player_name
    """
    
    results = client.query(query).to_dataframe()
    
    print('FLA Data Matching Analysis:')
    print('=' * 80)
    print('Roster Name | Roster Team | Stats Name | Stats Team | Age | Pts/60 | Points | Tier')
    print('-' * 80)

    for _, row in results.iterrows():
        print(f'{row.roster_name:20} | {row.roster_team:4} | {row.stats_name:20} | {row.stats_team:4} | {row.current_age:3} | {row.points_60:6.1f} | {row.points:6} | {row.performance_tier}')

    print(f'\nTotal FLA roster players: {len(results)}')
    print(f'Matched with stats: {len(results[results["stats_name"].notna()])}')
    print(f'Elite players found: {len(results[results["performance_tier"] == "Elite"])}')
    
    # Check what FLA players are in the raw database
    print('\nFLA players in raw database:')
    print('=' * 50)
    
    query2 = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as team,
        p.position,
        pst.pts60_weighted as points_60,
        COALESCE(ps.points, 0) as points
    FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
        ON pst.player_id = ps.player_id 
        AND pst.season = ps.season
    WHERE pst.season = 20242025 
    AND pst.game_type = 2 
    AND pst.games_played >= 20 
    AND p.position IN ("C", "L", "R", "D")
    AND pst.pts60_weighted IS NOT NULL
    AND t.tri_code = "FLA"
    ORDER BY pst.pts60_weighted DESC
    """
    
    results2 = client.query(query2).to_dataframe()
    
    for _, row in results2.iterrows():
        print(f'{row.player_name:25} | {row.team:4} | {row.position:2} | {row.points_60:6.1f} | {row.points:6}')
    
    print(f'\nTotal FLA players in raw database: {len(results2)}')
    
    # Check if the issue is with the team matching
    print('\nChecking team matching issue...')
    print('=' * 40)
    
    # Look for FLA players that might be on different teams in the raw data
    query3 = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as team,
        pst.pts60_weighted as points_60,
        COALESCE(ps.points, 0) as points
    FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
        ON pst.player_id = ps.player_id 
        AND pst.season = ps.season
    WHERE pst.season = 20242025 
    AND pst.game_type = 2 
    AND pst.games_played >= 20 
    AND p.position IN ("C", "L", "R", "D")
    AND pst.pts60_weighted IS NOT NULL
    AND p.full_name IN ("Mackie Samoskevich", "Aaron Ekblad", "Aleksander Barkov")
    ORDER BY p.full_name
    """
    
    results3 = client.query(query3).to_dataframe()
    
    print('Key FLA players in raw database:')
    for _, row in results3.iterrows():
        print(f'{row.player_name:25} | {row.team:4} | {row.points_60:6.1f} | {row.points:6}')

if __name__ == "__main__":
    debug_fla_data_matching()
