#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def check_duplicates_and_data_quality():
    """Check for duplicates and data quality issues causing too many rebuilding teams"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("CHECKING FOR DUPLICATES AND DATA QUALITY ISSUES")
    print("="*80)
    
    # Check for duplicates in the corrected view
    query = """
    SELECT 
        player_name,
        team_abbr,
        COUNT(*) as count
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected`
    GROUP BY player_name, team_abbr
    HAVING COUNT(*) > 1
    ORDER BY count DESC, player_name
    """
    
    results = client.query(query).to_dataframe()
    
    print('Duplicate players in corrected view:')
    print('=' * 50)
    if not results.empty:
        for _, row in results.iterrows():
            print(f'{row.player_name:25} | {row.team_abbr:4} | {row.count} times')
    else:
        print('No duplicates found')
    
    print(f'\nTotal duplicate entries: {len(results)}')
    
    # Check total player count by team
    query2 = """
    SELECT 
        team_abbr,
        COUNT(*) as player_count
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected`
    GROUP BY team_abbr
    ORDER BY player_count DESC
    """
    
    results2 = client.query(query2).to_dataframe()
    
    print('\nPlayers per team:')
    print('=' * 20)
    for _, row in results2.iterrows():
        print(f'{row.team_abbr:4}: {row.player_count:2} players')
    
    # Check the contention cycle logic more carefully
    print('\nChecking contention cycle logic...')
    print('=' * 40)
    
    # Let's look at a few specific teams to see why they're classified as rebuilding
    query3 = """
    WITH team_analysis AS (
        SELECT 
            team_abbr,
            COUNT(CASE WHEN performance_tier = "Elite" THEN 1 END) as elite_players,
            COUNT(CASE WHEN future_elite_potential = "Future Elite" THEN 1 END) as future_elites,
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age <= 25 THEN 1 END) as young_core,
            ROUND(AVG(CASE WHEN toi_per_game >= 18 AND current_age <= 25 THEN points_60 END), 1) as young_core_pts60,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age <= 25 THEN 1 END) as young_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age BETWEEN 26 AND 30 THEN 1 END) as peak_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age > 35 THEN 1 END) as aging_elite,
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age > 35 THEN 1 END) as aging_core
        FROM (
            SELECT 
                pr.team_abbr,
                pr.player_name,
                ps.current_age,
                ps.toi_per_game,
                ps.points_60,
                CASE 
                    WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0) THEN "Elite"
                    WHEN ps.position = "D" AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0) THEN "Elite"
                    WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p90_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) THEN "Near Elite"
                    WHEN ps.position = "D" AND ps.points_60 >= pos.p90_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) THEN "Near Elite"
                    WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p80_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) THEN "Good"
                    WHEN ps.position = "D" AND ps.points_60 >= pos.p80_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) THEN "Good"
                    WHEN ps.toi_per_game >= 18 THEN "Core"
                    WHEN ps.toi_per_game >= 15 THEN "Middle 6"
                    WHEN ps.toi_per_game >= 12 THEN "Bottom 6"
                    ELSE "Depth"
                END as performance_tier,
                CASE 
                    WHEN ps.current_age <= 22 AND ps.points_60 >= pos.p80_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) 
                    AND NOT (ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0))
                    AND NOT (ps.position = "D" AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0))
                    THEN "Future Elite"
                    ELSE "Not Future Elite"
                END as future_elite_potential
            FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected` pr
            JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals` pst ON pr.player_name = pst.player_name
            JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
            JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id
            LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON pst.player_id = ps.player_id AND pst.season = ps.season
            CROSS JOIN (
                SELECT 
                    position,
                    APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
                    APPROX_QUANTILES(points_60, 100)[OFFSET(90)] as p90_points_60,
                    APPROX_QUANTILES(points_60, 100)[OFFSET(80)] as p80_points_60,
                    APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points,
                    APPROX_QUANTILES(points, 100)[OFFSET(80)] as p80_total_points
                FROM (
                    SELECT 
                        p.position,
                        pst.pts60_weighted as points_60,
                        COALESCE(ps.points, 0) as points
                    FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
                    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
                    LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON pst.player_id = ps.player_id AND pst.season = ps.season
                    WHERE pst.season = 20242025 AND pst.game_type = 2 AND pst.games_played >= 20 AND p.position IN ("C", "L", "R", "D") AND pst.pts60_weighted IS NOT NULL
                )
                WHERE points > 0
                GROUP BY position
            ) pos ON p.position = pos.position
            WHERE pst.season = 20242025 AND pst.game_type = 2 AND pst.games_played >= 20 AND p.position IN ("C", "L", "R", "D") AND pst.pts60_weighted IS NOT NULL
            AND pr.team_abbr = t.tri_code
        )
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        elite_players,
        future_elites,
        young_core,
        young_core_pts60,
        young_elite,
        peak_elite,
        aging_elite,
        aging_core,
        CASE 
            WHEN future_elites > 0 AND elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN "Rebuilding"
            WHEN elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN "Rebuilding"
            WHEN future_elites > 0 AND elite_players > 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN "Window Coming"
            WHEN elite_players > 0 AND (young_elite > 0 OR peak_elite > 0) AND peak_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN "Window Open"
            WHEN elite_players > 0 AND peak_elite > 0 AND peak_core > 0 THEN "Win Now"
            WHEN elite_players > 0 AND aging_elite > 0 AND aging_core > 0 THEN "Window Closing"
            WHEN elite_players > 0 AND aging_elite > 0 AND young_core > 0 THEN "Window Closed"
            WHEN elite_players > 0 THEN "Window Open"
            WHEN future_elites > 0 THEN "Rebuilding"
            ELSE "Rebuilding"
        END as contention_cycle
    FROM team_analysis
    WHERE team_abbr IN ('TOR', 'VGK', 'DAL', 'COL', 'FLA', 'BOS', 'EDM', 'TBL', 'NYR', 'CAR')
    ORDER BY team_abbr
    """
    
    results3 = client.query(query3).to_dataframe()
    
    print('Key teams analysis:')
    print('=' * 80)
    for _, row in results3.iterrows():
        print(f'{row.team_abbr:4} | Elite: {row.elite_players} | Future: {row.future_elites} | Young Core: {row.young_core} | Pts/60: {row.young_core_pts60} | Cycle: {row.contention_cycle}')
    
    # Check if there are issues with the data matching
    print('\nChecking data matching issues...')
    print('=' * 40)
    
    query4 = """
    SELECT 
        pr.team_abbr,
        COUNT(*) as total_roster_players,
        COUNT(ps.player_name) as matched_players,
        ROUND(COUNT(ps.player_name) * 100.0 / COUNT(*), 1) as match_percentage
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected` pr
    LEFT JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals` pst ON pr.player_name = pst.player_name
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON pst.player_id = ps.player_id AND pst.season = ps.season
    WHERE pst.season = 20242025 AND pst.game_type = 2 AND pst.games_played >= 20 AND p.position IN ("C", "L", "R", "D") AND pst.pts60_weighted IS NOT NULL
    AND pr.team_abbr = t.tri_code
    GROUP BY pr.team_abbr
    ORDER BY match_percentage ASC
    """
    
    results4 = client.query(query4).to_dataframe()
    
    print('Data matching by team:')
    print('=' * 50)
    for _, row in results4.iterrows():
        print(f'{row.team_abbr:4} | {row.total_roster_players:2} total | {row.matched_players:2} matched | {row.match_percentage:5.1f}%')

if __name__ == "__main__":
    check_duplicates_and_data_quality()
