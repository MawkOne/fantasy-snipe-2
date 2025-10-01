#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def final_corrected_roster_analysis():
    """Final corrected roster analysis with proper category hierarchy"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FINAL CORRECTED ROSTER ANALYSIS - NO DUPLICATE CATEGORIES")
    print("="*80)
    
    # Get comprehensive player analysis with proper hierarchy
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
            -- Performance tiers with proper hierarchy (Elite > Near Elite > Good > Core)
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
    deduplicated_players AS (
        SELECT 
            team_abbr,
            player_name,
            current_age,
            toi_per_game,
            cf_pct_corrected,
            gf60,
            points_60,
            games_played,
            points,
            goals,
            assists,
            age_category,
            performance_tier,
            future_elite_potential,
            ROW_NUMBER() OVER (PARTITION BY team_abbr, player_name ORDER BY points_60 DESC, points DESC) as rn
        FROM matched_players
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
            COUNT(CASE WHEN future_elite_potential = "Future Elite" AND current_age <= 22 THEN 1 END) as young_future_elites,
            
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
        FROM deduplicated_players
        WHERE rn = 1
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        future_elites,
        young_future_elites,
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
    
    team_results = client.query(comprehensive_query).to_dataframe()
    
    # Get detailed player breakdown by team with age-based categories
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
            -- Performance tiers with proper hierarchy (Elite > Near Elite > Good > Core)
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
    deduplicated_players AS (
        SELECT 
            team_abbr,
            player_name,
            current_age,
            toi_per_game,
            cf_pct_corrected,
            gf60,
            points_60,
            games_played,
            points,
            goals,
            assists,
            age_category,
            performance_tier,
            future_elite_potential,
            ROW_NUMBER() OVER (PARTITION BY team_abbr, player_name ORDER BY points_60 DESC, points DESC) as rn
        FROM matched_players
    )
    SELECT 
        team_abbr,
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
    FROM deduplicated_players
    WHERE rn = 1
    ORDER BY team_abbr, 
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
    
    player_results = client.query(player_breakdown_query).to_dataframe()
    
    # Check for any players in multiple categories
    print("Checking for players in multiple categories:")
    elite_players = player_results[player_results['performance_tier'] == 'Elite']
    future_elite_players = player_results[player_results['future_elite_potential'] == 'Future Elite']
    
    # Check for overlaps
    elite_names = set(elite_players['player_name'].tolist())
    future_elite_names = set(future_elite_players['player_name'].tolist())
    overlap = elite_names.intersection(future_elite_names)
    
    if overlap:
        print(f"❌ Found {len(overlap)} players in multiple categories:")
        for player in overlap:
            print(f"  - {player}")
    else:
        print("✅ No players in multiple categories")
    
    # Check Future Elite age distribution
    future_elite_ages = future_elite_players['current_age'].tolist()
    over_22 = [age for age in future_elite_ages if age > 22]
    if over_22:
        print(f"❌ Found {len(over_22)} Future Elites over 22: {over_22}")
    else:
        print("✅ All Future Elites are 22 and younger")
    
    # Create comprehensive markdown file
    with open('/Users/markhenderson/Cursor Projects/NHL-API/projected_rosters_2025_26.md', 'w') as f:
        f.write('# 2025-26 Projected NHL Rosters - Final Analysis (No Duplicate Categories)\n\n')
        f.write('**FINAL VERSION** - Proper category hierarchy, no duplicate categories\n\n')
        f.write('## Category Hierarchy (Players can only be in ONE category):\n')
        f.write('1. **Elite**: Top 5% Pts/60 + (Top 10% total points OR missing points data)\n')
        f.write('2. **Future Elite**: Age ≤22 + Top 20% Pts/60 + (Top 20% total points OR missing points data) - ONLY if not already Elite\n')
        f.write('3. **Near Elite**: Top 10% Pts/60 + (Top 20% total points OR missing points data) - Can be any age\n')
        f.write('4. **Good**: Top 20% Pts/60 + (Top 20% total points OR missing points data)\n')
        f.write('5. **Core Player**: 18+ minutes TOI per game\n\n')
        
        f.write('## Team Outlook Summary:\n\n')
        f.write('| Team | Elite | Future Elite | Near Elite | Good | Core | Cycle |\n')
        f.write('|------|-------|--------------|------------|------|------|-------|\n')
        
        for _, team in team_results.iterrows():
            f.write(f'| {team["team_abbr"]} | {team["elite_players"]} | {team["future_elites"]} | {team["near_elite_players"]} | {team["good_players"]} | {team["core_players"]} | {team["contention_cycle"]} |\n')
        
        f.write('\n---\n\n')
        
        for team_abbr in sorted(team_results['team_abbr'].unique()):
            team_data = team_results[team_results['team_abbr'] == team_abbr].iloc[0]
            team_players = player_results[player_results['team_abbr'] == team_abbr]
            
            f.write(f'## {team_abbr} - {team_data["contention_cycle"]}\n\n')
            f.write(f'**Team Strength**: {team_data["original_strength"]}\n')
            f.write(f'**Elite Players**: {team_data["elite_players"]} (Age: {team_data["avg_elite_age"]})\n')
            f.write(f'**Future Elites**: {team_data["future_elites"]} | **Near Elite**: {team_data["near_elite_players"]} | **Good**: {team_data["good_players"]}\n')
            f.write(f'**Core Players**: {team_data["core_players"]} (18+ TOI)\n')
            f.write(f'**Young Core**: {team_data["young_core"]} | **Peak Core**: {team_data["peak_core"]} | **Veteran Core**: {team_data["veteran_core"]} | **Aging Core**: {team_data["aging_core"]}\n')
            f.write(f'**Total Points**: {team_data["total_points"]}\n\n')
            
            # Elite players
            elite_players = team_players[team_players['performance_tier'] == 'Elite']
            if not elite_players.empty:
                f.write('### Elite Players:\n\n')
                f.write('| Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|-----|----------|-----|--------|--------|-------|----------|\n')
                for _, player in elite_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["age_category"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Future Elite players
            future_elite_players = team_players[team_players['future_elite_potential'] == 'Future Elite']
            if not future_elite_players.empty:
                f.write('### Future Elite Players:\n\n')
                f.write('| Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|-----|----------|-----|--------|--------|-------|----------|\n')
                for _, player in future_elite_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["age_category"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Near Elite players
            near_elite_players = team_players[team_players['performance_tier'] == 'Near Elite']
            if not near_elite_players.empty:
                f.write('### Near Elite Players:\n\n')
                f.write('| Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|-----|----------|-----|--------|--------|-------|----------|\n')
                for _, player in near_elite_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["age_category"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Good players
            good_players = team_players[team_players['performance_tier'] == 'Good']
            if not good_players.empty:
                f.write('### Good Players:\n\n')
                f.write('| Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|-----|----------|-----|--------|--------|-------|----------|\n')
                for _, player in good_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["age_category"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            # Core players (excluding elite/near elite/good)
            core_players = team_players[team_players['performance_tier'] == 'Core']
            if not core_players.empty:
                f.write('### Core Players (18+ TOI):\n\n')
                f.write('| Player | Age | Category | TOI | Pts/60 | Points | Goals | Assists |\n')
                f.write('|--------|-----|----------|-----|--------|--------|-------|----------|\n')
                for _, player in core_players.iterrows():
                    f.write(f'| {player["player_name"]} | {player["current_age"]} | {player["age_category"]} | {player["toi_per_game"]:.1f} | {player["points_60"]:.1f} | {player["points"]} | {player["goals"]} | {player["assists"]} |\n')
                f.write('\n')
            
            f.write('---\n\n')
    
    print("✅ Final corrected roster analysis complete!")
    print(f"Total teams analyzed: {len(team_results)}")
    print(f"Total elite players: {team_results['elite_players'].sum()}")
    print(f"Total future elite players: {team_results['future_elites'].sum()}")
    print(f"Total near elite players: {team_results['near_elite_players'].sum()}")
    print(f"Total good players: {team_results['good_players'].sum()}")
    print(f"Total core players: {team_results['core_players'].sum()}")
    
    # Show contention cycle distribution
    print("\nContention Cycle Distribution:")
    cycle_counts = team_results['contention_cycle'].value_counts()
    for cycle, count in cycle_counts.items():
        print(f"  {cycle}: {count} teams")

if __name__ == "__main__":
    final_corrected_roster_analysis()
