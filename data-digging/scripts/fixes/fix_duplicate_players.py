#!/usr/bin/env python3
"""
Fix duplicate players in the Foster forecasting model.
This script identifies and removes duplicate records, keeping only the most recent/complete record for each player.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_duplicate_players():
    """Fix duplicate players by keeping only the best record for each player."""
    client = bigquery.Client()
    
    print("Fixing duplicate players in player_input_templates...")
    
    # Fix player_input_templates - keep the record with highest GP and most recent data
    fix_templates_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates_fixed` AS
    WITH ranked_players AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, team 
                ORDER BY gp_3yr_avg DESC, ev_toi_avg_minutes DESC, created_at DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates`
    )
    SELECT 
        player_id,
        player_name,
        position,
        position_group,
        team,
        age,
        gp_3yr_avg,
        gp_3yr_total,
        ev_toi_avg_minutes,
        player_archetype,
        player_archetype_2,
        line_role,
        style,
        ev_cf60,
        ev_ca60,
        ev_ff60,
        ev_fa60,
        ev_sf60,
        ev_sa60,
        ev_gf60,
        ev_ga60,
        ev_pts_conversion,
        ev_goals_60,
        ev_assists_60,
        ev_points_60,
        ev_shots_60,
        shooting_pct,
        faceoff_win_pct,
        pim_avg,
        plus_minus_avg,
        current_gp,
        current_goals,
        current_assists,
        current_points,
        current_toi_per_game_minutes,
        ev_cf_pct,
        ev_ff_pct,
        ev_sf_pct,
        ev_gf_pct,
        ev_pdo,
        pp_goals_avg,
        pp_points_avg,
        sh_goals_avg,
        sh_points_avg,
        created_at,
        model_version
    FROM ranked_players
    WHERE rn = 1
    ORDER BY team, ev_points_60 DESC
    """
    
    job = client.query(fix_templates_query)
    job.result()
    print("Fixed player_input_templates!")
    
    # Fix line_assignments
    print("Fixing duplicate players in line_assignments...")
    fix_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_fixed` AS
    WITH ranked_assignments AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, team 
                ORDER BY ev_toi_avg_minutes DESC, created_at DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments`
    )
    SELECT 
        player_id,
        player_name,
        position,
        position_group,
        team,
        age,
        gp_3yr_avg,
        ev_toi_avg_minutes,
        ev_points_60,
        ev_cf60,
        ev_ca60,
        ev_gf60,
        ev_ga60,
        player_archetype,
        ev_pts_conversion,
        forward_line,
        defense_pair,
        special_teams_role,
        primary_role,
        created_at,
        model_version
    FROM ranked_assignments
    WHERE rn = 1
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(fix_assignments_query)
    job.result()
    print("Fixed line_assignments!")
    
    # Fix player_forecasts
    print("Fixing duplicate players in player_forecasts...")
    fix_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_fixed` AS
    WITH ranked_forecasts AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, team 
                ORDER BY forecast_points_60_adjusted DESC, created_at DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.player_forecasts`
    )
    SELECT 
        player_id,
        player_name,
        position,
        team,
        primary_role,
        special_teams_role,
        forecast_cf60,
        forecast_ca60,
        forecast_gf60,
        forecast_ga60,
        forecast_pts_conversion,
        line_cf60,
        line_ca60,
        line_gf60,
        line_ga60,
        line_gf_cf_conversion,
        line_ga_ca_conversion,
        line_pts_conversion,
        forecast_points_60,
        forecast_points_60_adjusted,
        forecast_toi_minutes,
        toi_share_of_line,
        line_expected_toi,
        cf_contribution_share,
        gf_contribution_share,
        goals_share,
        assists_share,
        created_at,
        model_version
    FROM ranked_forecasts
    WHERE rn = 1
    ORDER BY team, primary_role, forecast_points_60_adjusted DESC
    """
    
    job = client.query(fix_forecasts_query)
    job.result()
    print("Fixed player_forecasts!")
    
    # Create fixed current_player_forecasts view
    print("Creating fixed current_player_forecasts view...")
    fix_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_fixed` AS
    SELECT 
        pf.player_id,
        pf.player_name,
        pf.position,
        pf.team,
        pf.primary_role,
        pf.special_teams_role,
        pf.forecast_points_60_adjusted as forecast_points_60,
        pf.forecast_toi_minutes,
        pf.forecast_cf60,
        pf.forecast_ca60,
        pf.forecast_gf60,
        pf.forecast_ga60,
        pf.goals_share,
        pf.assists_share,
        -- Calculate projected season totals (82 games)
        ROUND(pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_points,
        ROUND(pf.goals_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_goals,
        ROUND(pf.assists_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_assists,
        -- Add validation flags
        vf.flag_reason,
        vf.severity_level,
        pf.created_at,
        pf.model_version
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_fixed` pf
    LEFT JOIN `fantasy-snipe-ai.nhl_projections.validation_flags` vf 
        ON pf.player_id = vf.player_id
    ORDER BY pf.forecast_points_60_adjusted DESC
    """
    
    job = client.query(fix_view_query)
    job.result()
    print("Created fixed current_player_forecasts view!")
    
    # Run QA on fixed tables
    print("\nRunning QA on fixed tables...")
    
    # QA for player_input_templates_fixed
    qa_templates = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(DISTINCT team) as teams_covered,
        AVG(gp_3yr_avg) as avg_gp_3yr,
        AVG(ev_points_60) as avg_ev_points_60
    FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_fixed`
    """
    
    qa_job = client.query(qa_templates)
    qa_results = qa_job.result()
    
    print("Fixed Player Input Templates QA:")
    for row in qa_results:
        print(f"  Total players: {row.total_players}")
        print(f"  Unique players: {row.unique_players}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  Avg 3-year GP: {row.avg_gp_3yr:.1f}")
        print(f"  Avg EV Points/60: {row.avg_ev_points_60:.2f}")
    
    # QA for current_player_forecasts_fixed
    qa_forecasts = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(DISTINCT team) as teams_covered,
        AVG(forecast_points_60) as avg_points_60,
        MAX(forecast_points_60) as max_points_60,
        AVG(projected_points) as avg_projected_points,
        MAX(projected_points) as max_projected_points
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_fixed`
    """
    
    qa_job2 = client.query(qa_forecasts)
    qa_results2 = qa_job2.result()
    
    print("\nFixed Current Player Forecasts QA:")
    for row in qa_results2:
        print(f"  Total players: {row.total_players}")
        print(f"  Unique players: {row.unique_players}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  Avg points/60: {row.avg_points_60:.2f}")
        print(f"  Max points/60: {row.max_points_60:.2f}")
        print(f"  Avg projected points: {row.avg_projected_points:.1f}")
        print(f"  Max projected points: {row.max_projected_points:.1f}")

if __name__ == "__main__":
    fix_duplicate_players()
