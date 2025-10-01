#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def fix_elite_thresholds_simple():
    """Fix elite player thresholds with a simpler approach"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FIXING ELITE THRESHOLDS - SIMPLE APPROACH")
    print("="*80)
    
    # Create corrected view with better thresholds (using fixed values instead of percentiles)
    print("Step 1: Creating corrected view with better elite thresholds...")
    
    create_corrected_view = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected` AS
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
            -- CORRECTED Performance tiers with realistic thresholds
            CASE 
                -- Elite: Top performers by position
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= 2.5 AND ps.points >= 80 THEN "Elite"
                WHEN ps.position = "D" AND ps.points_60 >= 1.2 AND ps.points >= 40 THEN "Elite"
                -- Near Elite: Very good performers
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= 2.0 AND ps.points >= 60 THEN "Near Elite"
                WHEN ps.position = "D" AND ps.points_60 >= 1.0 AND ps.points >= 30 THEN "Near Elite"
                -- Good: Solid performers
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= 1.5 AND ps.points >= 40 THEN "Good"
                WHEN ps.position = "D" AND ps.points_60 >= 0.8 AND ps.points >= 20 THEN "Good"
                -- Core: 18+ TOI
                WHEN ps.toi_per_game >= 18 THEN "Core"
                WHEN ps.toi_per_game >= 15 THEN "Middle 6"
                WHEN ps.toi_per_game >= 12 THEN "Bottom 6"
                ELSE "Depth"
            END as performance_tier,
            -- Future elite potential (22 and younger, but only if not already Elite)
            CASE 
                WHEN ps.current_age <= 22 AND ps.points_60 >= 1.5 AND ps.points >= 40 
                AND NOT (ps.position IN ("C", "L", "R") AND ps.points_60 >= 2.5 AND ps.points >= 80)
                AND NOT (ps.position = "D" AND ps.points_60 >= 1.2 AND ps.points >= 40)
                THEN "Future Elite"
                ELSE "Not Future Elite"
            END as future_elite_potential
        FROM projected_rosters pr
        JOIN player_performance_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
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
        
        -- CORRECTED Age-based contention cycle logic
        CASE 
            -- Teams with 3+ elite players = Win Now
            WHEN elite_players >= 3 THEN "Win Now"
            -- Teams with 2+ elite players = Win Now (unless aging)
            WHEN elite_players >= 2 AND (aging_elite = 0 OR aging_elite < elite_players) THEN "Win Now"
            -- Teams with 1 elite player + good supporting cast = Window Open
            WHEN elite_players = 1 AND (near_elite_players >= 2 OR good_players >= 3) THEN "Window Open"
            -- Teams with 1 elite player but aging = Window Closing
            WHEN elite_players = 1 AND aging_elite > 0 AND peak_elite = 0 THEN "Window Closing"
            -- Teams with future elites + some elite talent = Window Coming
            WHEN future_elites > 0 AND elite_players > 0 THEN "Window Coming"
            -- Teams with future elites but no current elite = Rebuilding
            WHEN future_elites > 0 AND elite_players = 0 THEN "Rebuilding"
            -- Teams with no elite players but good depth = Window Soon
            WHEN elite_players = 0 AND (near_elite_players >= 3 OR good_players >= 5) THEN "Window Soon"
            -- Default fallback
            ELSE "Rebuilding"
        END as contention_cycle
    FROM team_analysis
    ORDER BY 
        CASE 
            WHEN elite_players >= 3 THEN 1
            WHEN elite_players >= 2 AND (aging_elite = 0 OR aging_elite < elite_players) THEN 1
            WHEN elite_players = 1 AND (near_elite_players >= 2 OR good_players >= 3) THEN 2
            WHEN elite_players = 1 AND aging_elite > 0 AND peak_elite = 0 THEN 3
            WHEN future_elites > 0 AND elite_players > 0 THEN 4
            WHEN future_elites > 0 AND elite_players = 0 THEN 5
            WHEN elite_players = 0 AND (near_elite_players >= 3 OR good_players >= 5) THEN 6
            ELSE 7
        END,
        elite_players DESC,
        future_elites DESC
    """
    
    client.query(create_corrected_view).to_dataframe()
    print("✅ Created corrected view with realistic elite thresholds")
    
    # Now QA all teams
    print("\nStep 2: QA All Teams...")
    
    qa_query = """
    SELECT 
        team_abbr,
        elite_players,
        near_elite_players,
        good_players,
        future_elites,
        young_elite,
        peak_elite,
        aging_elite,
        contention_cycle
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected`
    ORDER BY elite_players DESC, near_elite_players DESC
    """
    
    results = client.query(qa_query).to_dataframe()
    
    print("All Teams QA Results:")
    print("=" * 80)
    print("Team | Elite | Near Elite | Good | Future | Young | Peak | Aging | Cycle")
    print('-' * 80)
    
    for _, row in results.iterrows():
        print(f'{row.team_abbr:4} | {row.elite_players:5} | {row.near_elite_players:10} | {row.good_players:4} | {row.future_elites:6} | {row.young_elite:5} | {row.peak_elite:4} | {row.aging_elite:6} | {row.contention_cycle}')
    
    # Show overall distribution
    print("\nContention Cycle Distribution:")
    print("=" * 40)
    cycle_counts = results['contention_cycle'].value_counts()
    for cycle, count in cycle_counts.items():
        print(f'{cycle:15}: {count:2} teams')
    
    # Show elite player summary
    print(f"\nElite Player Summary:")
    print("=" * 30)
    print(f'Total Elite Players: {results["elite_players"].sum()}')
    print(f'Total Near Elite Players: {results["near_elite_players"].sum()}')
    print(f'Total Good Players: {results["good_players"].sum()}')
    print(f'Total Future Elite Players: {results["future_elites"].sum()}')
    
    # Check specific teams that should be good
    print(f"\nKey Teams Check:")
    print("=" * 30)
    key_teams = ['FLA', 'TOR', 'VGK', 'DAL', 'COL', 'BOS', 'EDM', 'TBL', 'NYR', 'CAR']
    for team in key_teams:
        team_data = results[results['team_abbr'] == team]
        if not team_data.empty:
            row = team_data.iloc[0]
            print(f'{team:4}: {row.elite_players} elite, {row.near_elite_players} near elite → {row.contention_cycle}')
    
    # Show some specific elite players to verify
    print(f"\nSample Elite Players by Team:")
    print("=" * 50)
    
    elite_players_query = """
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
    ),
    matched_players AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            ps.position,
            ps.points_60,
            ps.points,
            CASE 
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= 2.5 AND ps.points >= 80 THEN "Elite"
                WHEN ps.position = "D" AND ps.points_60 >= 1.2 AND ps.points >= 40 THEN "Elite"
                ELSE "Not Elite"
            END as performance_tier
        FROM projected_rosters pr
        JOIN player_performance_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    )
    SELECT 
        team_abbr,
        player_name,
        position,
        points_60,
        points,
        performance_tier
    FROM matched_players
    WHERE performance_tier = "Elite"
    ORDER BY team_abbr, points_60 DESC
    """
    
    elite_results = client.query(elite_players_query).to_dataframe()
    
    for team in ['FLA', 'TOR', 'VGK', 'DAL', 'COL', 'BOS', 'EDM', 'TBL', 'NYR']:
        team_elite = elite_results[elite_results['team_abbr'] == team]
        if not team_elite.empty:
            print(f'\n{team} Elite Players:')
            for _, player in team_elite.iterrows():
                print(f'  {player.player_name:20} | {player.position:2} | {player.points_60:5.1f} | {player.points:3}')
    
    print(f"\n✅ QA Complete!")
    print("All teams have been analyzed with corrected elite thresholds")

if __name__ == "__main__":
    fix_elite_thresholds_simple()
