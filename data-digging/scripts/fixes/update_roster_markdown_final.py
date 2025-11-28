#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def update_roster_markdown_final():
    """Update the roster markdown with corrected elite definitions and team outlooks"""
    
    client = bigquery.Client()
    
    print("Updating roster markdown with corrected elite definitions...")
    
    # Get the corrected team outlooks
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
        AND p.position IN ("C", "L", "R", "D")
        AND pst.pts60_weighted IS NOT NULL
        AND ps.points IS NOT NULL
    ),
    position_percentiles AS (
        SELECT 
            position,
            APPROX_QUANTILES(points_60, 100)[OFFSET(95)] as p95_points_60,
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points
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
                WHEN ps.toi_per_game >= 18 THEN "Top Line"
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
            COUNT(CASE WHEN performance_tier = "Elite" AND current_age > 35 THEN 1 END) as aging_elite
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
    
    # Get elite players by team
    elite_players_query = """
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
            APPROX_QUANTILES(points, 100)[OFFSET(90)] as p90_total_points
        FROM player_performance_2024_25
        GROUP BY position
    ),
    elite_players AS (
        SELECT 
            pp.*,
            CASE 
                WHEN pp.position IN ("C", "L", "R") AND pp.points_60 >= pos.p95_points_60 AND pp.points >= pos.p90_total_points THEN "Elite"
                WHEN pp.position = "D" AND pp.points_60 >= pos.p95_points_60 AND pp.points >= pos.p90_total_points THEN "Elite"
                ELSE "Not Elite"
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
        points_60,
        points,
        goals,
        assists,
        performance_tier
    FROM elite_players
    WHERE performance_tier = "Elite"
    ORDER BY team, points_60 DESC
    """
    
    elite_results = client.query(elite_players_query).to_dataframe()
    
    # Create updated markdown file
    with open('/Users/markhenderson/Cursor Projects/NHL-API/projected_rosters_2025_26.md', 'w') as f:
        f.write('# 2025-26 Projected NHL Rosters with Corrected Elite Definitions\n\n')
        f.write('**FINAL CORRECTED VERSION** - Elite players defined by actual performance metrics\n\n')
        f.write('## Elite Player Definition:\n')
        f.write('- **Forwards (C, L, R)**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Defensemen (D)**: Top 5% in Pts/60 AND Top 10% in total points\n')
        f.write('- **Elite players are RARE** - only 34 total in the league (23 forwards + 11 defensemen)\n\n')
        
        f.write('## Team Outlook Summary:\n\n')
        f.write('| Team | Elite Players | Strength | Cycle | Key Elite Players |\n')
        f.write('|------|---------------|----------|-------|-------------------|\n')
        
        for _, team in team_results.iterrows():
            team_elite = elite_results[elite_results['team'] == team['team_abbr']]
            elite_names = ', '.join(team_elite['player_name'].tolist()) if not team_elite.empty else 'None'
            f.write(f'| {team["team_abbr"]} | {team["elite_players"]} | {team["corrected_strength"]} | {team["contention_cycle"]} | {elite_names} |\n')
        
        f.write('\n---\n\n')
        
        for team_abbr in sorted(team_results['team_abbr'].unique()):
            team_data = team_results[team_results['team_abbr'] == team_abbr].iloc[0]
            team_elite = elite_results[elite_results['team'] == team_abbr]
            
            f.write(f'## {team_abbr} - {team_data["contention_cycle"]}\n\n')
            f.write(f'**Team Strength**: {team_data["corrected_strength"]} (Original: {team_data["original_strength"]})\n')
            f.write(f'**Elite Players**: {team_data["elite_players"]} (Age: {team_data["avg_elite_age"]})\n')
            f.write(f'**Core Players**: {team_data["core_players"]} (18+ TOI)\n')
            f.write(f'**Total Points**: {team_data["total_points"]}\n\n')
            
            if not team_elite.empty:
                f.write('### Elite Players:\n\n')
                f.write('| Player | Position | Age | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|----------|-----|-----|--------|--------|-------|----------|\n')
                for _, player in team_elite.iterrows():
                    f.write(f'| {player["player_name"]} | {player["position"]} | {player["current_age"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            else:
                f.write('### Elite Players: None\n\n')
            
            f.write('---\n\n')
    
    print("✅ Updated projected_rosters_2025_26.md with corrected elite definitions and team outlooks")
    
    # Show summary
    print(f"\nSummary of Corrected Analysis:")
    print(f"- Total elite players: {len(elite_results)} (realistic)")
    print(f"- Elite forwards: {len(elite_results[elite_results['position'].isin(['C', 'L', 'R'])])}")
    print(f"- Elite defensemen: {len(elite_results[elite_results['position'] == 'D'])}")
    
    win_now_teams = team_results[team_results['contention_cycle'] == 'Win Now']
    print(f"- Win Now teams: {len(win_now_teams)}")
    for _, team in win_now_teams.iterrows():
        print(f"  - {team['team_abbr']}: {team['elite_players']} elite players, {team['corrected_strength']} strength")

if __name__ == "__main__":
    update_roster_markdown_final()
