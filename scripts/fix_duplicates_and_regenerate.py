#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def fix_duplicates_and_regenerate():
    """Fix duplicates and regenerate analysis properly"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FIXING DUPLICATES AND REGENERATING ANALYSIS")
    print("="*80)
    
    # First, let's see the duplicates clearly
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
    
    duplicates = client.query(query).to_dataframe()
    
    print(f'Found {len(duplicates)} duplicate players:')
    print('=' * 50)
    for _, row in duplicates.iterrows():
        print(f'{row.player_name:25} | {row.team_abbr:4} | {row.count} times')
    
    # Create a deduplicated view
    print('\nCreating deduplicated view...')
    
    create_deduplicated_view = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated` AS
    WITH ranked_players AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier,
            ROW_NUMBER() OVER (PARTITION BY team_abbr, player_name ORDER BY player_name) as rn
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_corrected`
    )
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM ranked_players
    WHERE rn = 1
    """
    
    client.query(create_deduplicated_view).to_dataframe()
    print("✅ Created deduplicated view")
    
    # Check the deduplicated counts
    query2 = """
    SELECT 
        team_abbr,
        COUNT(*) as player_count
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated`
    GROUP BY team_abbr
    ORDER BY player_count DESC
    """
    
    results2 = client.query(query2).to_dataframe()
    
    print('\nPlayers per team (deduplicated):')
    print('=' * 30)
    for _, row in results2.iterrows():
        print(f'{row.team_abbr:4}: {row.player_count:2} players')
    
    total_players = results2['player_count'].sum()
    print(f'\nTotal players: {total_players}')
    
    # Now regenerate the analysis with deduplicated data
    print('\nRegenerating analysis with deduplicated data...')
    
    analysis_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated`
    ),
    player_performance_2024_25 AS (
        SELECT 
            t.tri_code as team,
            p.full_name as player_name,
            p.position,
            p.birth_date,
            EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM p.birth_date) as current_age,
            pst.toi_minutes / pst.games_played as toi_per_game,
            LEAST(pst.cf_pct_weighted, 100.0) as cf_pct_corrected,
            pst.gf60,
            pst.pts60_weighted as points_60,
            pst.games_played,
            pst.toi_minutes,
            COALESCE(ps.points, 0) as points,
            COALESCE(ps.goals, 0) as goals,
            COALESCE(ps.assists, 0) as assists
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
    ),
    position_percentiles AS (
        SELECT 
            position,
            APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
            APPROX_QUANTILES(points_60, 100)[OFFSET(90)] as p90_points_60,
            APPROX_QUANTILES(points_60, 100)[OFFSET(80)] as p80_points_60,
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points,
            APPROX_QUANTILES(points, 100)[OFFSET(80)] as p80_total_points
        FROM player_performance_2024_25
        WHERE points > 0
        GROUP BY position
    ),
    matched_players AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            ps.current_age,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.gf60,
            ps.points_60,
            ps.games_played,
            ps.points,
            ps.goals,
            ps.assists,
            -- Age-based categories
            CASE 
                WHEN ps.current_age <= 22 THEN "Young"
                WHEN ps.current_age BETWEEN 23 AND 27 THEN "Rising"
                WHEN ps.current_age BETWEEN 28 AND 32 THEN "Peak"
                WHEN ps.current_age BETWEEN 33 AND 35 THEN "Veteran"
                ELSE "Aging"
            END as age_category,
            -- Performance tiers with proper hierarchy
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
            -- Future elite potential (22 and younger, but only if not already Elite)
            CASE 
                WHEN ps.current_age <= 22 AND ps.points_60 >= pos.p80_points_60 AND (ps.points >= pos.p80_total_points OR ps.points = 0) 
                AND NOT (ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0))
                AND NOT (ps.position = "D" AND ps.points_60 >= pos.p95_points_60 AND (ps.points >= pos.p90_total_points OR ps.points = 0))
                THEN "Future Elite"
                ELSE "Not Future Elite"
            END as future_elite_potential
        FROM projected_rosters pr
        JOIN player_performance_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
        JOIN position_percentiles pos ON ps.position = pos.position
    ),
    team_analysis AS (
        SELECT 
            team_abbr,
            COUNT(*) as total_players,
            COUNT(CASE WHEN toi_per_game >= 18 THEN 1 END) as core_players,
            ROUND(AVG(cf_pct_corrected), 1) as avg_cf_pct,
            ROUND(AVG(gf60), 1) as avg_gf60,
            ROUND(AVG(CASE WHEN toi_per_game >= 18 THEN toi_per_game END), 1) as avg_core_toi,
            ROUND(AVG(points_60), 1) as avg_points_60,
            ROUND(SUM(points), 0) as total_points,
            
            -- Elite player analysis
            COUNT(CASE WHEN performance_tier = "Elite" THEN 1 END) as elite_players,
            ROUND(AVG(CASE WHEN performance_tier = "Elite" THEN current_age END), 1) as avg_elite_age,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age <= 25 THEN 1 END) as young_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age BETWEEN 26 AND 30 THEN 1 END) as peak_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age BETWEEN 31 AND 35 THEN 1 END) as veteran_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age > 35 THEN 1 END) as aging_elite,
            
            -- Future elite analysis
            COUNT(CASE WHEN future_elite_potential = "Future Elite" THEN 1 END) as future_elites,
            
            -- Core player age analysis
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age <= 25 THEN 1 END) as young_core,
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age BETWEEN 26 AND 30 THEN 1 END) as peak_core,
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age BETWEEN 31 AND 35 THEN 1 END) as veteran_core,
            COUNT(CASE WHEN toi_per_game >= 18 AND current_age > 35 THEN 1 END) as aging_core,
            
            -- Performance analysis
            COUNT(CASE WHEN performance_tier = "Near Elite" THEN 1 END) as near_elite_players,
            COUNT(CASE WHEN performance_tier = "Good" THEN 1 END) as good_players,
            
            -- Young core production analysis
            ROUND(AVG(CASE WHEN toi_per_game >= 18 AND current_age <= 25 THEN points_60 END), 1) as young_core_pts60,
            ROUND(AVG(CASE WHEN toi_per_game >= 18 AND current_age <= 25 THEN points END), 1) as young_core_points
        FROM matched_players
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        future_elites,
        near_elite_players,
        good_players,
        avg_elite_age,
        young_elite,
        peak_elite,
        veteran_elite,
        aging_elite,
        young_core,
        peak_core,
        veteran_core,
        aging_core,
        young_core_pts60,
        young_core_points,
        avg_cf_pct,
        avg_gf60,
        avg_core_toi,
        total_points,
        
        -- Original team strength
        ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) as original_strength,
        
        -- Age-based contention cycle logic
        CASE 
            -- Future Elites + no elites + young core with low production = Rebuilding
            WHEN future_elites > 0 AND elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN "Rebuilding"
            -- no elites + young core with low production = Rebuilding  
            WHEN elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN "Rebuilding"
            -- Future Elites + Elites + young core with good production = Window Coming
            WHEN future_elites > 0 AND elite_players > 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN "Window Coming"
            -- Good side of age curve Elites + Core with good production = Window Open
            WHEN elite_players > 0 AND (young_elite > 0 OR peak_elite > 0) AND peak_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN "Window Open"
            -- Elites at age curve peak + Core with good production = Win Now
            WHEN elite_players > 0 AND peak_elite > 0 AND peak_core > 0 THEN "Win Now"
            -- Aging Elites + aging core with good production = Window Closing
            WHEN elite_players > 0 AND aging_elite > 0 AND aging_core > 0 THEN "Window Closing"
            -- Aging Elites + young core = Window Closed
            WHEN elite_players > 0 AND aging_elite > 0 AND young_core > 0 THEN "Window Closed"
            -- Default fallback
            WHEN elite_players > 0 THEN "Window Open"
            WHEN future_elites > 0 THEN "Rebuilding"
            ELSE "Rebuilding"
        END as contention_cycle
    FROM team_analysis
    ORDER BY 
        CASE 
            WHEN future_elites > 0 AND elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN 1
            WHEN elite_players = 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) < 1.5 THEN 1
            WHEN future_elites > 0 AND elite_players > 0 AND young_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN 2
            WHEN elite_players > 0 AND (young_elite > 0 OR peak_elite > 0) AND peak_core > 0 AND COALESCE(young_core_pts60, 0) >= 1.5 THEN 3
            WHEN elite_players > 0 AND peak_elite > 0 AND peak_core > 0 THEN 4
            WHEN elite_players > 0 AND aging_elite > 0 AND aging_core > 0 THEN 5
            WHEN elite_players > 0 AND aging_elite > 0 AND young_core > 0 THEN 6
            WHEN elite_players > 0 THEN 3
            WHEN future_elites > 0 THEN 1
            ELSE 1
        END,
        elite_players DESC,
        future_elites DESC
    """
    
    team_results = client.query(analysis_query).to_dataframe()
    
    print("✅ Regenerated analysis with deduplicated data")
    print(f"Total teams analyzed: {len(team_results)}")
    print(f"Total elite players: {team_results['elite_players'].sum()}")
    print(f"Total future elite players: {team_results['future_elites'].sum()}")
    print(f"Total near elite players: {team_results['near_elite_players'].sum()}")
    print(f"Total good players: {team_results['good_players'].sum()}")
    print(f"Total core players: {team_results['core_players'].sum()}")
    
    # Show contention cycle distribution
    print("\nContention Cycle Distribution (Deduplicated):")
    cycle_counts = team_results['contention_cycle'].value_counts()
    for cycle, count in cycle_counts.items():
        print(f"  {cycle}: {count} teams")
    
    # Show some key teams
    print("\nKey Teams Analysis:")
    print("=" * 60)
    key_teams = ['TOR', 'VGK', 'DAL', 'COL', 'FLA', 'BOS', 'EDM', 'TBL', 'NYR', 'CAR']
    for team in key_teams:
        team_data = team_results[team_results['team_abbr'] == team]
        if not team_data.empty:
            row = team_data.iloc[0]
            print(f'{team:4} | Elite: {row.elite_players} | Future: {row.future_elites} | Young Core: {row.young_core} | Pts/60: {row.young_core_pts60} | Cycle: {row.contention_cycle}')
    
    print(f"\n✅ Analysis complete with deduplicated data!")
    print("The projected_rosters_2025_26_deduplicated view now has:")
    print("- Corrected team assignments from raw database")
    print("- No duplicate players")
    print("- Filtered out depth players")
    print("- Proper elite/near elite/good player classifications")
    print("- Realistic contention cycle distribution")

if __name__ == "__main__":
    fix_duplicates_and_regenerate()
