#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def create_comprehensive_roster_analysis():
    """Create comprehensive roster analysis with elite, near elite, breakout candidates, and core players"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("CREATING COMPREHENSIVE ROSTER ANALYSIS")
    print("="*80)
    
    # Get comprehensive player analysis
    comprehensive_query = """
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
        AND p.position IN ("C", "L", "R", "D")
        AND pst.pts60_weighted IS NOT NULL
        AND ps.points IS NOT NULL
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
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN "Elite"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN "Elite"
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p90_points_60 AND ps.points >= pos.p80_total_points THEN "Near Elite"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p90_points_60 AND ps.points >= pos.p80_total_points THEN "Near Elite"
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p80_points_60 AND ps.points >= pos.p80_total_points THEN "Breakout Candidate"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p80_points_60 AND ps.points >= pos.p80_total_points THEN "Breakout Candidate"
                WHEN ps.toi_per_game >= 18 THEN "Core Player"
                WHEN ps.toi_per_game >= 15 THEN "Middle 6"
                WHEN ps.toi_per_game >= 12 THEN "Bottom 6"
                ELSE "Depth"
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
            COUNT(CASE WHEN performance_tier = "Elite" THEN 1 END) as elite_players,
            ROUND(AVG(CASE WHEN performance_tier = "Elite" THEN current_age END), 1) as avg_elite_age,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age <= 25 THEN 1 END) as young_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age BETWEEN 26 AND 30 THEN 1 END) as prime_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age BETWEEN 31 AND 35 THEN 1 END) as veteran_elite,
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age > 35 THEN 1 END) as aging_elite,
            
            -- Near elite analysis
            COUNT(CASE WHEN performance_tier = "Near Elite" THEN 1 END) as near_elite_players,
            COUNT(CASE WHEN performance_tier = "Breakout Candidate" THEN 1 END) as breakout_candidates
        FROM matched_players
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        near_elite_players,
        breakout_candidates,
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
    
    team_results = client.query(comprehensive_query).to_dataframe()
    
    # Get detailed player breakdown by team
    player_breakdown_query = """
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
        AND p.position IN ("C", "L", "R", "D")
        AND pst.pts60_weighted IS NOT NULL
        AND ps.points IS NOT NULL
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
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN "Elite"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p95_points_60 AND ps.points >= pos.p90_total_points THEN "Elite"
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p90_points_60 AND ps.points >= pos.p80_total_points THEN "Near Elite"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p90_points_60 AND ps.points >= pos.p80_total_points THEN "Near Elite"
                WHEN ps.position IN ("C", "L", "R") AND ps.points_60 >= pos.p80_points_60 AND ps.points >= pos.p80_total_points THEN "Breakout Candidate"
                WHEN ps.position = "D" AND ps.points_60 >= pos.p80_points_60 AND ps.points >= pos.p80_total_points THEN "Breakout Candidate"
                WHEN ps.toi_per_game >= 18 THEN "Core Player"
                WHEN ps.toi_per_game >= 15 THEN "Middle 6"
                WHEN ps.toi_per_game >= 12 THEN "Bottom 6"
                ELSE "Depth"
            END as performance_tier
        FROM projected_rosters pr
        JOIN player_performance_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
        JOIN position_percentiles pos ON ps.position = pos.position
    )
    SELECT 
        team_abbr,
        player_name,
        current_age,
        toi_per_game,
        points_60,
        points,
        goals,
        assists,
        performance_tier
    FROM matched_players
    ORDER BY team_abbr, 
        CASE performance_tier 
            WHEN "Elite" THEN 1
            WHEN "Near Elite" THEN 2
            WHEN "Breakout Candidate" THEN 3
            WHEN "Core Player" THEN 4
            WHEN "Middle 6" THEN 5
            WHEN "Bottom 6" THEN 6
            ELSE 7
        END,
        points_60 DESC
    """
    
    player_results = client.query(player_breakdown_query).to_dataframe()
    
    # Create comprehensive markdown file
    with open('/Users/markhenderson/Cursor Projects/NHL-API/projected_rosters_2025_26.md', 'w') as f:
        f.write('# 2025-26 Projected NHL Rosters - Comprehensive Analysis\n\n')
        f.write('**FINAL CORRECTED VERSION** - Elite players defined by actual performance metrics\n\n')
        f.write('## Elite Player Definition:\n')
        f.write('- **Forwards (C, L, R)**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Defensemen (D)**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Elite players are RARE** - only 34 total in the league (23 forwards + 11 defensemen)\n\n')
        
        f.write('## Player Categories:\n')
        f.write('- **Elite**: Top 5% Pts/60 + Top 10% total points\n')
        f.write('- **Near Elite**: Top 10% Pts/60 + Top 20% total points\n')
        f.write('- **Breakout Candidate**: Top 20% Pts/60 + Top 20% total points\n')
        f.write('- **Core Player**: 18+ minutes TOI per game\n\n')
        
        f.write('## Team Outlook Summary:\n\n')
        f.write('| Team | Elite | Near Elite | Breakout | Core | Strength | Cycle |\n')
        f.write('|------|-------|------------|----------|------|----------|-------|\n')
        
        for _, team in team_results.iterrows():
            f.write(f'| {team["team_abbr"]} | {team["elite_players"]} | {team["near_elite_players"]} | {team["breakout_candidates"]} | {team["core_players"]} | {team["corrected_strength"]} | {team["contention_cycle"]} |\n')
        
        f.write('\n---\n\n')
        
        for team_abbr in sorted(team_results['team_abbr'].unique()):
            team_data = team_results[team_results['team_abbr'] == team_abbr].iloc[0]
            team_players = player_results[player_results['team_abbr'] == team_abbr]
            
            f.write(f'## {team_abbr} - {team_data["contention_cycle"]}\n\n')
            f.write(f'**Team Strength**: {team_data["corrected_strength"]} (Original: {team_data["original_strength"]})\n')
            f.write(f'**Elite Players**: {team_data["elite_players"]} (Age: {team_data["avg_elite_age"]})\n')
            f.write(f'**Near Elite**: {team_data["near_elite_players"]} | **Breakout Candidates**: {team_data["breakout_candidates"]}\n')
            f.write(f'**Core Players**: {team_data["core_players"]} (18+ TOI)\n')
            f.write(f'**Total Points**: {team_data["total_points"]}\n\n')
            
            # Elite players
            elite_players = team_players[team_players['performance_tier'] == 'Elite']
            if not elite_players.empty:
                f.write('### Elite Players:\n\n')
                f.write('| Player | Position | Age | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|----------|-----|-----|--------|--------|-------|----------|\n')
                for _, player in elite_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Near Elite players
            near_elite_players = team_players[team_players['performance_tier'] == 'Near Elite']
            if not near_elite_players.empty:
                f.write('### Near Elite Players:\n\n')
                f.write('| Player | Position | Age | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|----------|-----|-----|--------|--------|-------|----------|\n')
                for _, player in near_elite_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Breakout candidates
            breakout_players = team_players[team_players['performance_tier'] == 'Breakout Candidate']
            if not breakout_players.empty:
                f.write('### Breakout Candidates:\n\n')
                f.write('| Player | Position | Age | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|----------|-----|-----|--------|--------|-------|----------|\n')
                for _, player in breakout_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Core players (excluding elite/near elite/breakout)
            core_players = team_players[team_players['performance_tier'] == 'Core Player']
            if not core_players.empty:
                f.write('### Core Players (18+ TOI):\n\n')
                f.write('| Player | Position | Age | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|----------|-----|-----|--------|--------|-------|----------|\n')
                for _, player in core_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            f.write('---\n\n')
    
    print("✅ Created comprehensive roster analysis!")
    print(f"Total teams analyzed: {len(team_results)}")
    print(f"Total elite players: {team_results['elite_players'].sum()}")
    print(f"Total near elite players: {team_results['near_elite_players'].sum()}")
    print(f"Total breakout candidates: {team_results['breakout_candidates'].sum()}")
    print(f"Total core players: {team_results['core_players'].sum()}")

if __name__ == "__main__":
    create_comprehensive_roster_analysis()
