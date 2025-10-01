#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def show_fla_team_report():
    """Show detailed FLA team report to understand why they're classified as rebuilding"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FLA (FLORIDA PANTHERS) DETAILED TEAM REPORT")
    print("="*80)
    
    # Get detailed FLA team report
    query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated`
        WHERE team_abbr = "FLA"
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
        AND t.tri_code = "FLA"
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
            -- Performance tiers
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
            -- Future elite potential
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
    )
    SELECT 
        player_name,
        current_age,
        age_category,
        toi_per_game,
        points_60,
        points,
        goals,
        assists,
        performance_tier,
        future_elite_potential
    FROM matched_players
    ORDER BY 
        CASE performance_tier 
            WHEN "Elite" THEN 1
            WHEN "Future Elite" THEN 2
            WHEN "Near Elite" THEN 3
            WHEN "Good" THEN 4
            WHEN "Core" THEN 5
            WHEN "Middle 6" THEN 6
            WHEN "Bottom 6" THEN 7
            ELSE 8
        END,
        points_60 DESC
    """
    
    results = client.query(query).to_dataframe()
    
    print('FLA (Florida Panthers) Detailed Team Report:')
    print('=' * 80)
    print('Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists | Performance Tier | Future Elite')
    print('-' * 100)

    for _, row in results.iterrows():
        print(f'{row.player_name:20} | {row.current_age:3} | {row.age_category:7} | {row.toi_per_game:4.1f} | {row.points_60:6.1f} | {row.points:6} | {row.goals:6} | {row.assists:7} | {row.performance_tier:15} | {row.future_elite_potential}')

    print(f'\nTotal FLA players analyzed: {len(results)}')
    print(f'Elite players: {len(results[results["performance_tier"] == "Elite"])}')
    print(f'Near Elite players: {len(results[results["performance_tier"] == "Near Elite"])}')
    print(f'Good players: {len(results[results["performance_tier"] == "Good"])}')
    print(f'Core players: {len(results[results["performance_tier"] == "Core"])}')
    print(f'Future Elite players: {len(results[results["future_elite_potential"] == "Future Elite"])}')
    
    # Check why they're classified as rebuilding
    print('\nContention Cycle Logic Analysis:')
    print('=' * 40)
    
    elite_players = len(results[results["performance_tier"] == "Elite"])
    future_elites = len(results[results["future_elite_potential"] == "Future Elite"])
    young_core = len(results[(results["toi_per_game"] >= 18) & (results["current_age"] <= 25)])
    
    print(f'Elite players: {elite_players}')
    print(f'Future Elite players: {future_elites}')
    print(f'Young Core players (18+ TOI, ≤25 age): {young_core}')
    
    if elite_players == 0:
        print('\n❌ PROBLEM: FLA has 0 elite players!')
        print('This is why they\'re classified as "Rebuilding"')
        print('But they just won the Stanley Cup - they should have elite players!')
        
        # Check if we're missing key FLA players
        print('\nChecking if we\'re missing key FLA players...')
        
        # Look for FLA players in the raw database
        query2 = """
        SELECT 
            p.full_name as player_name,
            t.tri_code as team,
            p.position,
            pst.toi_minutes / pst.games_played as toi_per_game,
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
        LIMIT 10
        """
        
        results2 = client.query(query2).to_dataframe()
        
        print('\nTop 10 FLA players by Pts/60 from raw database:')
        print('=' * 60)
        for _, row in results2.iterrows():
            print(f'{row.player_name:25} | {row.toi_per_game:4.1f} | {row.points_60:6.1f} | {row.points:6}')

if __name__ == "__main__":
    show_fla_team_report()
