#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def analyze_elite_player_age_impact():
    """Analyze how elite player age impacts team outlooks and contention cycles"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("ANALYZING ELITE PLAYER AGE IMPACT ON TEAM OUTLOOKS")
    print("="*80)
    
    # First, let's identify elite players and their ages
    print("Step 1: Identifying elite players and their ages...")
    
    elite_players_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE toi_tier = 'Elite'
    ),
    player_stats_2024_25 AS (
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
    elite_player_analysis AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            ps.current_age,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.gf60,
            ps.points_60,
            ps.points,
            ps.goals,
            ps.assists,
            CASE 
                WHEN ps.current_age <= 25 THEN "Young Elite"
                WHEN ps.current_age <= 30 THEN "Prime Elite"
                WHEN ps.current_age <= 35 THEN "Veteran Elite"
                ELSE "Aging Elite"
            END as age_category
        FROM projected_rosters pr
        JOIN player_stats_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    )
    SELECT 
        team_abbr,
        player_name,
        position_type,
        current_age,
        age_category,
        toi_per_game,
        cf_pct_corrected,
        points_60,
        points
    FROM elite_player_analysis
    ORDER BY team_abbr, current_age DESC
    """
    
    elite_results = client.query(elite_players_query).to_dataframe()
    
    print("\nElite Players by Team and Age:")
    print("Team | Player | Position | Age | Category | TOI | CF% | Pts/60 | Points")
    print("-" * 90)
    for _, row in elite_results.iterrows():
        print(f"{row.team_abbr:4} | {row.player_name:20} | {row.position_type:8} | {row.current_age:3} | {row.age_category:11} | {row.toi_per_game:4.1f} | {row.cf_pct_corrected:4.1f} | {row.points_60:6.1f} | {row.points:6}")
    
    # Analyze team elite player age distribution
    print("\nStep 2: Analyzing team elite player age distribution...")
    
    team_elite_age_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE toi_tier = 'Elite'
    ),
    player_stats_2024_25 AS (
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
    elite_player_analysis AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            ps.current_age,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.gf60,
            ps.points_60,
            ps.points,
            ps.goals,
            ps.assists,
            CASE 
                WHEN ps.current_age <= 25 THEN "Young Elite"
                WHEN ps.current_age <= 30 THEN "Prime Elite"
                WHEN ps.current_age <= 35 THEN "Veteran Elite"
                ELSE "Aging Elite"
            END as age_category
        FROM projected_rosters pr
        JOIN player_stats_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    ),
    team_elite_summary AS (
        SELECT 
            team_abbr,
            COUNT(*) as total_elite_players,
            ROUND(AVG(current_age), 1) as avg_elite_age,
            MIN(current_age) as youngest_elite,
            MAX(current_age) as oldest_elite,
            COUNT(CASE WHEN age_category = "Young Elite" THEN 1 END) as young_elite_count,
            COUNT(CASE WHEN age_category = "Prime Elite" THEN 1 END) as prime_elite_count,
            COUNT(CASE WHEN age_category = "Veteran Elite" THEN 1 END) as veteran_elite_count,
            COUNT(CASE WHEN age_category = "Aging Elite" THEN 1 END) as aging_elite_count,
            ROUND(AVG(points_60), 1) as avg_elite_points_60,
            ROUND(SUM(points), 0) as total_elite_points
        FROM elite_player_analysis
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_elite_players,
        avg_elite_age,
        youngest_elite,
        oldest_elite,
        young_elite_count,
        prime_elite_count,
        veteran_elite_count,
        aging_elite_count,
        avg_elite_points_60,
        total_elite_points,
        CASE 
            WHEN avg_elite_age <= 26 AND aging_elite_count = 0 THEN "Elite Young Core"
            WHEN avg_elite_age <= 28 AND aging_elite_count <= 1 THEN "Elite Prime Core"
            WHEN avg_elite_age <= 32 AND aging_elite_count <= 2 THEN "Elite Mixed Core"
            WHEN avg_elite_age > 32 OR aging_elite_count >= 3 THEN "Elite Aging Core"
            ELSE "Elite Transitional Core"
        END as elite_core_type
    FROM team_elite_summary
    ORDER BY avg_elite_age DESC
    """
    
    team_elite_results = client.query(team_elite_age_query).to_dataframe()
    
    print("\nTeam Elite Player Age Analysis:")
    print("Team | Elite | Avg Age | Youngest | Oldest | Young | Prime | Veteran | Aging | Core Type")
    print("-" * 100)
    for _, row in team_elite_results.iterrows():
        print(f"{row.team_abbr:4} | {row.total_elite_players:5} | {row.avg_elite_age:7} | {row.youngest_elite:8} | {row.oldest_elite:6} | {row.young_elite_count:5} | {row.prime_elite_count:5} | {row.veteran_elite_count:7} | {row.aging_elite_count:5} | {row.elite_core_type}")
    
    # Now let's create an age-weighted team strength calculation
    print("\nStep 3: Creating age-weighted team strength calculation...")
    
    age_weighted_strength_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    ),
    player_stats_2024_25 AS (
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
    matched_players AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            pr.toi_tier,
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
                WHEN ps.current_age <= 25 THEN "Young Elite"
                WHEN ps.current_age <= 30 THEN "Prime Elite"
                WHEN ps.current_age <= 35 THEN "Veteran Elite"
                ELSE "Aging Elite"
            END as age_category
        FROM projected_rosters pr
        JOIN player_stats_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    ),
    age_weighted_calculation AS (
        SELECT 
            team_abbr,
            COUNT(*) as total_players,
            COUNT(CASE WHEN toi_per_game >= 18 THEN 1 END) as core_players,
            ROUND(AVG(cf_pct_corrected), 1) as avg_cf_pct,
            ROUND(AVG(gf60), 1) as avg_gf60,
            ROUND(AVG(CASE WHEN toi_per_game >= 18 THEN toi_per_game END), 1) as avg_core_toi,
            ROUND(AVG(points_60), 1) as avg_points_60,
            ROUND(SUM(points), 0) as total_points,
            
            -- Elite player age analysis
            COUNT(CASE WHEN toi_tier = 'Elite' THEN 1 END) as elite_players,
            ROUND(AVG(CASE WHEN toi_tier = 'Elite' THEN current_age END), 1) as avg_elite_age,
            COUNT(CASE WHEN toi_tier = 'Elite' AND current_age <= 25 THEN 1 END) as young_elite,
            COUNT(CASE WHEN toi_tier = 'Elite' AND current_age BETWEEN 26 AND 30 THEN 1 END) as prime_elite,
            COUNT(CASE WHEN toi_tier = 'Elite' AND current_age BETWEEN 31 AND 35 THEN 1 END) as veteran_elite,
            COUNT(CASE WHEN toi_tier = 'Elite' AND current_age > 35 THEN 1 END) as aging_elite,
            
            -- Age-weighted factors
            ROUND(AVG(CASE WHEN toi_tier = 'Elite' THEN current_age END) * 0.3, 1) as age_penalty,
            ROUND(COUNT(CASE WHEN toi_tier = 'Elite' AND current_age <= 30 THEN 1 END) * 2.0, 1) as youth_bonus,
            ROUND(COUNT(CASE WHEN toi_tier = 'Elite' AND current_age > 35 THEN 1 END) * -1.5, 1) as aging_penalty
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
        
        -- Age-weighted team strength
        ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + youth_bonus + aging_penalty, 1) as age_weighted_strength,
        
        -- Age factors
        age_penalty,
        youth_bonus,
        aging_penalty,
        
        -- Contention cycle based on age-weighted strength
        CASE 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + youth_bonus + aging_penalty, 1) >= 40 THEN "Win Now"
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + youth_bonus + aging_penalty, 1) >= 37 THEN "Window Closing" 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + youth_bonus + aging_penalty, 1) >= 34 THEN "Window Soon"
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3) + youth_bonus + aging_penalty, 1) >= 30 THEN "Window Closed"
            ELSE "Rebuilding"
        END as age_weighted_cycle
    FROM age_weighted_calculation
    ORDER BY age_weighted_strength DESC
    """
    
    age_weighted_results = client.query(age_weighted_strength_query).to_dataframe()
    
    print("\nAge-Weighted Team Strength Analysis:")
    print("Team | Elite | Avg Age | Young | Prime | Veteran | Aging | Original | Age-Weighted | Cycle")
    print("-" * 100)
    for _, row in age_weighted_results.head(20).iterrows():
        print(f"{row.team_abbr:4} | {row.elite_players:5} | {row.avg_elite_age:7} | {row.young_elite:5} | {row.prime_elite:5} | {row.veteran_elite:7} | {row.aging_elite:5} | {row.original_strength:8} | {row.age_weighted_strength:12} | {row.age_weighted_cycle}")
    
    # Focus on Pittsburgh specifically
    print(f"\nPittsburgh Penguins Elite Player Analysis:")
    pitt_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type,
            toi_tier
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE team_abbr = 'PIT' AND toi_tier = 'Elite'
    ),
    player_stats_2024_25 AS (
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
        AND t.tri_code = 'PIT'
    )
    SELECT 
        pr.player_name,
        pr.position_type,
        ps.current_age,
        ps.toi_per_game,
        ps.cf_pct_corrected,
        ps.points_60,
        ps.points,
        CASE 
            WHEN ps.current_age <= 25 THEN "Young Elite"
            WHEN ps.current_age <= 30 THEN "Prime Elite"
            WHEN ps.current_age <= 35 THEN "Veteran Elite"
            ELSE "Aging Elite"
        END as age_category
    FROM projected_rosters pr
    JOIN player_stats_2024_25 ps 
        ON pr.player_name = ps.player_name 
        AND pr.team_abbr = ps.team
    ORDER BY ps.current_age DESC
    """
    
    pitt_results = client.query(pitt_query).to_dataframe()
    
    if not pitt_results.empty:
        print("Player | Position | Age | TOI | CF% | Pts/60 | Points | Category")
        print("-" * 70)
        for _, row in pitt_results.iterrows():
            print(f"{row.player_name:15} | {row.position_type:8} | {row.current_age:3} | {row.toi_per_game:4.1f} | {row.cf_pct_corrected:4.1f} | {row.points_60:6.1f} | {row.points:6} | {row.age_category}")
    else:
        print("No elite players found for Pittsburgh in projected rosters")
    
    # Show teams that should be in "Window Closed" due to aging elite players
    print(f"\nTeams with Aging Elite Players (Should Consider Rebuilding):")
    aging_teams = age_weighted_results[age_weighted_results['aging_elite'] > 0]
    for _, row in aging_teams.iterrows():
        print(f"  {row.team_abbr}: {row.aging_elite} aging elite players (avg age: {row.avg_elite_age}) - {row.age_weighted_cycle}")
    
    print(f"\n✅ Elite player age impact analysis complete!")
    print(f"Age-weighted model better reflects team rebuilding needs around elite talent")

if __name__ == "__main__":
    analyze_elite_player_age_impact()
