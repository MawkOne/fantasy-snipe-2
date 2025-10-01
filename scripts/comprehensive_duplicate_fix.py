#!/usr/bin/env python3
"""
Comprehensive fix for all duplicate entries in Foster model tables.
This script creates completely clean tables with proper deduplication logic.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def comprehensive_duplicate_fix():
    """Fix all duplicate entries across all Foster model tables."""
    client = bigquery.Client()
    
    print("Starting comprehensive duplicate fix...")
    
    # 1. Fix player_input_templates with proper deduplication
    print("1. Fixing player_input_templates...")
    fix_templates_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates_clean` AS
    WITH ranked_players AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id 
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
    print("✓ Fixed player_input_templates")
    
    # 2. Fix line_assignments with proper deduplication
    print("2. Fixing line_assignments...")
    fix_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_clean` AS
    WITH ranked_assignments AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id 
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
    print("✓ Fixed line_assignments")
    
    # 3. Fix player_forecasts with proper deduplication
    print("3. Fixing player_forecasts...")
    fix_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_clean` AS
    WITH ranked_forecasts AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id 
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
    print("✓ Fixed player_forecasts")
    
    # 4. Fix validation_flags with proper deduplication
    print("4. Fixing validation_flags...")
    fix_flags_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.validation_flags_clean` AS
    WITH ranked_flags AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, flag_reason 
                ORDER BY created_at DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.validation_flags`
    )
    SELECT 
        player_id,
        player_name,
        team,
        primary_role,
        flag_reason,
        severity_level,
        forecast_points_60_adjusted,
        historical_points_60,
        points_variance_pct,
        toi_variance_pct,
        cf_variance_pct,
        ca_variance_pct,
        flag_type,
        created_at,
        model_version
    FROM ranked_flags
    WHERE rn = 1
    ORDER BY severity_level DESC, flag_type, team, player_name
    """
    
    job = client.query(fix_flags_query)
    job.result()
    print("✓ Fixed validation_flags")
    
    # 5. Create final clean current_player_forecasts view
    print("5. Creating final clean view...")
    create_final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean_final` AS
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
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_clean` pf
    LEFT JOIN `fantasy-snipe-ai.nhl_projections.validation_flags_clean` vf 
        ON pf.player_id = vf.player_id
    ORDER BY pf.forecast_points_60_adjusted DESC
    """
    
    job = client.query(create_final_view_query)
    job.result()
    print("✓ Created final clean view")
    
    # Run comprehensive QA
    print("\nRunning comprehensive QA...")
    
    # QA for all tables
    qa_query = """
    SELECT 
        'player_input_templates_clean' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(*) - COUNT(DISTINCT player_id) as duplicates
    FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_clean`
    
    UNION ALL
    
    SELECT 
        'line_assignments_clean' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(*) - COUNT(DISTINCT player_id) as duplicates
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_clean`
    
    UNION ALL
    
    SELECT 
        'player_forecasts_clean' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(*) - COUNT(DISTINCT player_id) as duplicates
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_clean`
    
    UNION ALL
    
    SELECT 
        'validation_flags_clean' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(*) - COUNT(DISTINCT player_id) as duplicates
    FROM `fantasy-snipe-ai.nhl_projections.validation_flags_clean`
    
    UNION ALL
    
    SELECT 
        'current_player_forecasts_clean_final' as table_name,
        COUNT(*) as total_records,
        COUNT(DISTINCT player_id) as unique_players,
        COUNT(*) - COUNT(DISTINCT player_id) as duplicates
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean_final`
    
    ORDER BY table_name
    """
    
    qa_job = client.query(qa_query)
    qa_results = qa_job.result()
    
    print("\n=== COMPREHENSIVE QA RESULTS ===")
    for row in qa_results:
        status = "✅ CLEAN" if row.duplicates == 0 else f"❌ {row.duplicates} DUPLICATES"
        print(f"{row.table_name}: {row.total_records} records, {row.unique_players} unique players - {status}")
    
    # Show sample data from clean view
    print("\n=== SAMPLE DATA (Edmonton Oilers) ===")
    sample_query = """
    SELECT 
        player_name, 
        team, 
        primary_role, 
        ROUND(forecast_points_60, 2) as forecast_points_60,
        projected_points,
        projected_goals,
        projected_assists
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean_final`
    WHERE team = 'EDM'
    ORDER BY projected_points DESC
    LIMIT 5
    """
    
    sample_job = client.query(sample_query)
    sample_results = sample_job.result()
    
    for row in sample_results:
        print(f"{row.player_name} ({row.primary_role}): {row.forecast_points_60} P/60 → {row.projected_points} pts ({row.projected_goals}G, {row.projected_assists}A)")

if __name__ == "__main__":
    comprehensive_duplicate_fix()
