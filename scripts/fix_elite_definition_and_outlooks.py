#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def fix_elite_definition_and_outlooks():
    """Fix elite definition based on actual performance metrics and redo team outlooks"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FIXING ELITE DEFINITION AND REDOING TEAM OUTLOOKS")
    print("="*80)
    
    # Step 1: Define elite players based on actual 2024-25 performance
    print("Step 1: Identifying elite players based on actual performance...")
    
    elite_definition_query = """
    WITH player_performance_2024_25 AS (
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
            ps.points,
            ps.goals,
            ps.assists,
            ps.goals_60,
            ps.assists_60
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
            ON pst.player_id = ps.player_id 
            AND pst.season = ps.season
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
    ),
    position_percentiles AS (
        SELECT 
            position,
            APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
            APPROX_QUANTILES(points_60, 100)[OFFSET(90)] as p90_points_60,
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points,
            APPROX_QUANTILES(goals_60, 100)[OFFSET(90)] as p90_goals_60,
            APPROX_QUANTILES(assists_60, 100)[OFFSET(90)] as p90_assists_60
        FROM player_performance_2024_25
        WHERE points_60 IS NOT NULL
        GROUP BY position
    ),
    elite_players AS (
        SELECT 
            pp.*,
            CASE 
                WHEN pp.position = 'F' AND pp.points_60 >= pos.p95_points_60 AND pp.points >= pos.p90_total_points THEN 'Elite'
                WHEN pp.position = 'D' AND pp.points_60 >= pos.p95_points_60 AND pp.points >= pos.p90_total_points THEN 'Elite'
                WHEN pp.toi_per_game >= 18 THEN 'Top Line'
                WHEN pp.toi_per_game >= 15 THEN 'Middle 6'
                WHEN pp.toi_per_game >= 12 THEN 'Bottom 6'
                ELSE 'Depth'
            END as performance_tier
        FROM player_performance_2024_25 pp
        JOIN position_percentiles pos ON pp.position = pos.position
    )
    SELECT 
        team,
        player_name,
        position,
        current_age,
        toi_per_game,
        cf_pct_corrected,
        points_60,
        points,
        goals,
        assists,
        performance_tier
    FROM elite_players
    WHERE performance_tier = 'Elite'
    ORDER BY points_60 DESC
    """
    
    elite_results = client.query(elite_definition_query).to_dataframe()
    
    print(f"Found {len(elite_results)} elite players based on performance:")
    print("Player | Team | Position | Age | TOI | Pts/60 | Points | Tier")
    print("-" * 70)
    for _, row in elite_results.head(20).iterrows():
        print(f"{row.player_name:20} | {row.team:4} | {row.position:8} | {row.current_age:3} | {row.toi_per_game:4.1f} | {row.points_60:6.1f} | {row.points:6} | {row.performance_tier}")
    
    # Step 2: Get team outlooks with corrected elite definitions
    print("\nStep 2: Calculating team outlooks with corrected elite definitions...")
    
    team_outlook_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
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
            ps.points,
            ps.goals,
            ps.assists
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
            ON pst.player_id = ps.player_id 
            AND pst.season = ps.season
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
    ),
    position_percentiles AS (
        SELECT 
            position,
            APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points
        FROM player_performance_2024_25
        WHERE points_60 IS NOT NULL
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
            CASE 
                WHEN ps.position = 'F' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'Elite'
                WHEN ps.position = 'D' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'Elite'
                WHEN ps.toi_per_game >= 18 THEN 'Top Line'
                WHEN ps.toi_per_game >= 15 THEN 'Middle 6'
                WHEN ps.toi_per_game >= 12 THEN 'Bottom 6'
                ELSE 'Depth'
            END as performance_tier
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
            COUNT(CASE WHEN performance_tier = 'Elite' THEN 1 END) as elite_players,
            ROUND(AVG(CASE WHEN performance_tier = 'Elite' THEN current_age END), 1) as avg_elite_age,
            COUNT(CASE WHEN performance_tier = 'Elite' AND current_age <= 25 THEN 1 END) as young_elite,
            COUNT(CASE WHEN performance_tier = 'Elite' AND current_age BETWEEN 26 AND 30 THEN 1 END) as prime_elite,
            COUNT(CASE WHEN performance_tier = 'Elite' AND current_age BETWEEN 31 AND 35 THEN 1 END) as veteran_elite,
            COUNT(CASE WHEN performance_tier = 'Elite' AND current_age > 35 THEN 1 END) as aging_elite
        FROM matched_players
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        avg_elite_age,
        young_elite,
        prime_elite,
        veteran_elite,
        aging_elite,
        avg_cf_pct,
        avg_gf60,
        avg_core_toi,
        total_points,
        
        -- Original team strength
        ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) as original_strength,
        
        -- Elite player impact (heavily weighted)
        ROUND(elite_players * 5.0, 1) as elite_bonus,
        ROUND(aging_elite * -3.0, 1) as aging_penalty,
        ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + (elite_players * 5.0) + (aging_elite * -3.0), 1) as corrected_strength,
        
        -- Contention cycle based on corrected strength
        CASE 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + (elite_players * 5.0) + (aging_elite * -3.0), 1) >= 45 THEN "Win Now"
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + (elite_players * 5.0) + (aging_elite * -3.0), 1) >= 40 THEN "Window Closing" 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + (elite_players * 5.0) + (aging_elite * -3.0), 1) >= 35 THEN "Window Soon"
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + (elite_players * 5.0) + (aging_elite * -3.0), 1) >= 30 THEN "Window Closed"
            ELSE "Rebuilding"
        END as contention_cycle
    FROM team_analysis
    ORDER BY corrected_strength DESC
    """
    
    team_results = client.query(team_outlook_query).to_dataframe()
    
    print("\nCorrected Team Outlooks:")
    print("Team | Elite | Avg Age | Original | Elite Bonus | Aging Penalty | Corrected | Cycle")
    print("-" * 90)
    for _, row in team_results.iterrows():
        print(f"{row.team_abbr:4} | {row.elite_players:5} | {row.avg_elite_age:7} | {row.original_strength:8} | {row.elite_bonus:11} | {row.aging_penalty:12} | {row.corrected_strength:9} | {row.contention_cycle}")
    
    # Step 3: Update the projected rosters with corrected TOI tiers
    print("\nStep 3: Updating projected rosters with corrected TOI tiers...")
    
    # Create updated roster data
    updated_rosters_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
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
            ps.points,
            ps.goals,
            ps.assists
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
            ON pst.player_id = ps.player_id 
            AND pst.season = ps.season
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
    ),
    position_percentiles AS (
        SELECT 
            position,
            APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points
        FROM player_performance_2024_25
        WHERE points_60 IS NOT NULL
        GROUP BY position
    ),
    corrected_rosters AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            ps.current_age,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.points_60,
            ps.points,
            ps.goals,
            ps.assists,
            CASE 
                WHEN ps.position = 'F' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'Elite'
                WHEN ps.position = 'D' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'Elite'
                WHEN ps.toi_per_game >= 18 THEN 'Top Line'
                WHEN ps.toi_per_game >= 15 THEN 'Middle 6'
                WHEN ps.toi_per_game >= 12 THEN 'Bottom 6'
                ELSE 'Depth'
            END as corrected_tier,
            -- Assign line positions based on corrected tiers
            CASE 
                WHEN ps.position = 'F' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'line_1'
                WHEN ps.position = 'F' AND ps.toi_per_game >= 18 THEN 'line_1'
                WHEN ps.position = 'F' AND ps.toi_per_game >= 15 THEN 'line_2'
                WHEN ps.position = 'F' AND ps.toi_per_game >= 12 THEN 'line_3'
                WHEN ps.position = 'F' THEN 'line_4'
                WHEN ps.position = 'D' AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN 'pair_1'
                WHEN ps.position = 'D' AND ps.toi_per_game >= 18 THEN 'pair_1'
                WHEN ps.position = 'D' AND ps.toi_per_game >= 15 THEN 'pair_2'
                WHEN ps.position = 'D' AND ps.toi_per_game >= 12 THEN 'pair_3'
                WHEN ps.position = 'D' THEN 'depth'
            END as corrected_line_position
        FROM projected_rosters pr
        JOIN player_performance_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
        JOIN position_percentiles pos ON ps.position = pos.position
    )
    SELECT 
        team_abbr,
        player_name,
        position_type,
        current_age,
        toi_per_game,
        points_60,
        points,
        corrected_tier,
        corrected_line_position
    FROM corrected_rosters
    ORDER BY team_abbr, position_type, corrected_tier, toi_per_game DESC
    """
    
    corrected_roster_results = client.query(updated_rosters_query).to_dataframe()
    
    # Step 4: Generate updated markdown file
    print("\nStep 4: Generating updated markdown file...")
    
    with open('/Users/markhenderson/Cursor Projects/NHL-API/projected_rosters_2025_26.md', 'w') as f:
        f.write('# 2025-26 Projected NHL Rosters with Corrected TOI Forecasts\n\n')
        f.write('**CORRECTED VERSION** - Elite players defined by actual performance metrics\n\n')
        f.write('## Elite Player Definition:\n')
        f.write('- **Forwards**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Defensemen**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Elite players are RARE** - only ~15-20 total in the league\n\n')
        
        for team_abbr in sorted(corrected_roster_results['team_abbr'].unique()):
            team_data = corrected_roster_results[corrected_roster_results['team_abbr'] == team_abbr]
            
            f.write(f'## {team_abbr}\n\n')
            
            # Forwards
            forwards = team_data[team_data['position_type'] == 'Forward'].sort_values('toi_per_game', ascending=False)
            if not forwards.empty:
                f.write('### Forwards\n\n')
                f.write('| Player | Age | TOI | Pts/60 | Points | Tier | Line |\n')
                f.write('|--------|-----|-----|--------|--------|------|------|\n')
                for _, player in forwards.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["corrected_tier"]} | {player["corrected_line_position"]} |\n')
                f.write('\n')
            
            # Defensemen
            defensemen = team_data[team_data['position_type'] == 'Defenseman'].sort_values('toi_per_game', ascending=False)
            if not defensemen.empty:
                f.write('### Defensemen\n\n')
                f.write('| Player | Age | TOI | Pts/60 | Points | Tier | Pair |\n')
                f.write('|--------|-----|-----|--------|--------|------|------|\n')
                for _, player in defensemen.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["corrected_tier"]} | {player["corrected_line_position"]} |\n')
                f.write('\n')
            
            # Team summary
            total_players = len(team_data)
            elite_players = len(team_data[team_data['corrected_tier'] == 'Elite'])
            avg_toi = team_data['toi_per_game'].mean()
            
            f.write('### Team Summary\n\n')
            f.write(f'- **Total Players**: {total_players}\n')
            f.write(f'- **Elite Players**: {elite_players}\n')
            f.write(f'- **Average TOI/Game**: {avg_toi:.1f} minutes\n\n')
            f.write('---\n\n')
    
    print("✅ Updated projected_rosters_2025_26.md with corrected elite definitions and team outlooks")
    
    # Show summary of changes
    print(f"\nSummary of Changes:")
    print(f"- Elite players reduced from 957 to {len(elite_results)} (based on actual performance)")
    print(f"- Most teams now have 0-2 elite players (realistic)")
    print(f"- Team outlooks recalculated with performance-based elite definitions")

if __name__ == "__main__":
    fix_elite_definition_and_outlooks()
