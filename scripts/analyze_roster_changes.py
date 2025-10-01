#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def analyze_roster_changes():
    """Analyze projected rosters by applying 2024-25 stats to new rosters"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("ANALYZING ROSTER CHANGES: 2024-25 STATS → 2025-26 PROJECTED ROSTERS")
    print("="*80)
    
    # First, let's see what players we have in our projected rosters vs 2024-25 data
    print("Step 1: Matching projected roster players with 2024-25 stats...")
    
    roster_match_query = """
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
    roster_matches AS (
        SELECT 
            pr.team_abbr,
            pr.player_name as projected_name,
            pr.position_type,
            pr.toi_tier,
            ps.player_name as stats_name,
            ps.team as stats_team,
            ps.position as stats_position,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.gf60,
            ps.points_60,
            ps.games_played,
            ps.points,
            ps.goals,
            ps.assists,
            CASE 
                WHEN pr.player_name = ps.player_name THEN "Exact Match"
                WHEN UPPER(pr.player_name) = UPPER(ps.player_name) THEN "Case Match"
                WHEN SOUNDEX(pr.player_name) = SOUNDEX(ps.player_name) THEN "Soundex Match"
                ELSE "No Match"
            END as match_type
        FROM projected_rosters pr
        LEFT JOIN player_stats_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    )
    SELECT 
        team_abbr,
        COUNT(*) as total_roster_players,
        COUNT(CASE WHEN match_type != "No Match" THEN 1 END) as matched_players,
        COUNT(CASE WHEN match_type = "Exact Match" THEN 1 END) as exact_matches,
        ROUND(COUNT(CASE WHEN match_type != "No Match" THEN 1 END) * 100.0 / COUNT(*), 1) as match_percentage
    FROM roster_matches
    GROUP BY team_abbr
    ORDER BY match_percentage DESC
    """
    
    match_results = client.query(roster_match_query).to_dataframe()
    
    print("\nRoster Matching Results:")
    print("Team | Total | Matched | Exact | Match %")
    print("-" * 50)
    for _, row in match_results.head(15).iterrows():
        print(f"{row.team_abbr:4} | {row.total_roster_players:5} | {row.matched_players:7} | {row.exact_matches:5} | {row.match_percentage:7}%")
    
    # Now let's calculate team strength using the matched players
    print("\nStep 2: Calculating team strength with matched players...")
    
    team_strength_query = """
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
    matched_players AS (
        SELECT 
            pr.team_abbr,
            pr.player_name,
            pr.position_type,
            pr.toi_tier,
            ps.toi_per_game,
            ps.cf_pct_corrected,
            ps.gf60,
            ps.points_60,
            ps.games_played,
            ps.points,
            ps.goals,
            ps.assists
        FROM projected_rosters pr
        JOIN player_stats_2024_25 ps 
            ON pr.player_name = ps.player_name 
            AND pr.team_abbr = ps.team
    ),
    team_strength_calc AS (
        SELECT 
            team_abbr,
            COUNT(*) as total_players,
            COUNT(CASE WHEN toi_per_game >= 18 THEN 1 END) as core_players,
            ROUND(AVG(cf_pct_corrected), 1) as avg_cf_pct,
            ROUND(AVG(gf60), 1) as avg_gf60,
            ROUND(AVG(CASE WHEN toi_per_game >= 18 THEN toi_per_game END), 1) as avg_core_toi,
            ROUND(AVG(points_60), 1) as avg_points_60,
            ROUND(SUM(points), 0) as total_points,
            ROUND(AVG(points), 1) as avg_points_per_player
        FROM matched_players
        GROUP BY team_abbr
    )
    SELECT 
        team_abbr,
        total_players,
        core_players,
        avg_cf_pct,
        avg_gf60,
        avg_core_toi,
        avg_points_60,
        total_points,
        avg_points_per_player,
        ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) as team_strength,
        CASE 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) >= 40 THEN "Win Now"
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) >= 37 THEN "Window Closing" 
            WHEN ROUND((avg_cf_pct * 0.3 + avg_gf60 * 0.4 + avg_core_toi * 0.3), 1) >= 34 THEN "Window Soon"
            ELSE "Rebuilding"
        END as cycle_stage
    FROM team_strength_calc
    ORDER BY team_strength DESC
    """
    
    team_strength_results = client.query(team_strength_query).to_dataframe()
    
    print("\nTeam Strength Analysis (2025-26 Projected Rosters):")
    print("Team | Players | Core | CF% | GF/60 | Core TOI | Pts/60 | Total Pts | Strength | Stage")
    print("-" * 100)
    for _, row in team_strength_results.head(20).iterrows():
        print(f"{row.team_abbr:4} | {row.total_players:7} | {row.core_players:4} | {row.avg_cf_pct:4} | {row.avg_gf60:5} | {row.avg_core_toi:8} | {row.avg_points_60:6} | {row.total_points:9} | {row.team_strength:8} | {row.cycle_stage}")
    
    # Compare with original 2024-25 team strength
    print("\nStep 3: Comparing with original 2024-25 team strength...")
    
    original_strength_query = """
    WITH team_performance_2024_25 AS (
        SELECT 
            t.tri_code as team,
            ROUND((AVG(LEAST(pst.cf_pct_weighted, 100.0)) * 0.3 + AVG(pst.gf60) * 0.4 + AVG(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN pst.toi_minutes / pst.games_played END) * 0.3), 1) as team_strength,
            AVG(LEAST(pst.cf_pct_weighted, 100.0)) as avg_cf_pct,
            AVG(pst.gf60) as avg_gf60,
            AVG(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN pst.toi_minutes / pst.games_played END) as avg_core_toi
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
        GROUP BY t.tri_code
    )
    SELECT 
        team,
        team_strength as original_strength,
        avg_cf_pct as original_cf_pct,
        avg_gf60 as original_gf60,
        avg_core_toi as original_core_toi
    FROM team_performance_2024_25
    WHERE team IN (SELECT team_abbr FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`)
    ORDER BY team
    """
    
    original_results = client.query(original_strength_query).to_dataframe()
    
    # Merge the results for comparison
    comparison_df = team_strength_results.merge(
        original_results, 
        left_on='team_abbr', 
        right_on='team', 
        how='left'
    )
    
    comparison_df['strength_change'] = comparison_df['team_strength'] - comparison_df['original_strength']
    comparison_df['cf_pct_change'] = comparison_df['avg_cf_pct'] - comparison_df['original_cf_pct']
    
    print("\nTeam Strength Comparison (2024-25 vs 2025-26 Projected):")
    print("Team | 2024-25 | 2025-26 | Change | CF% Chg | 2024-25 Stage | 2025-26 Stage")
    print("-" * 80)
    for _, row in comparison_df.head(15).iterrows():
        change_str = f"+{row.strength_change:.1f}" if row.strength_change > 0 else f"{row.strength_change:.1f}"
        cf_change_str = f"+{row.cf_pct_change:.1f}" if row.cf_pct_change > 0 else f"{row.cf_pct_change:.1f}"
        
        # Determine 2024-25 stage
        if row.original_strength >= 40:
            stage_2024 = "Win Now"
        elif row.original_strength >= 37:
            stage_2024 = "Window Closing"
        elif row.original_strength >= 34:
            stage_2024 = "Window Soon"
        else:
            stage_2024 = "Rebuilding"
        
        print(f"{row.team_abbr:4} | {row.original_strength:7} | {row.team_strength:7} | {change_str:6} | {cf_change_str:7} | {stage_2024:12} | {row.cycle_stage}")
    
    # Show biggest changes
    print(f"\nBiggest Improvements:")
    biggest_improvements = comparison_df.nlargest(5, 'strength_change')[['team_abbr', 'original_strength', 'team_strength', 'strength_change']]
    for _, row in biggest_improvements.iterrows():
        print(f"  {row.team_abbr}: {row.original_strength:.1f} → {row.team_strength:.1f} (+{row.strength_change:.1f})")
    
    print(f"\nBiggest Declines:")
    biggest_declines = comparison_df.nsmallest(5, 'strength_change')[['team_abbr', 'original_strength', 'team_strength', 'strength_change']]
    for _, row in biggest_declines.iterrows():
        print(f"  {row.team_abbr}: {row.original_strength:.1f} → {row.team_strength:.1f} ({row.strength_change:.1f})")
    
    # Contention cycle distribution
    print(f"\nContention Cycle Distribution (2025-26 Projected):")
    cycle_dist = team_strength_results['cycle_stage'].value_counts()
    for stage, count in cycle_dist.items():
        print(f"  {stage}: {count} teams")
    
    print(f"\n✅ Roster change analysis complete!")
    print(f"Data shows how team outlooks change with projected 2025-26 rosters")

if __name__ == "__main__":
    analyze_roster_changes()
