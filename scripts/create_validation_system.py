#!/usr/bin/env python3
"""
Create Validation System for Foster's forecasting method.
This implements quality control, reasonability checks, and manual adjustment tracking.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_validation_system():
    """Create validation system with quality control and manual adjustments."""
    client = bigquery.Client()
    
    # Create validation flags table
    print("Creating validation flags system...")
    validation_flags_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.validation_flags` AS
    WITH player_forecast_validation AS (
        SELECT 
            pf.player_id,
            pf.player_name,
            pf.team,
            pf.primary_role,
            pf.forecast_points_60_adjusted,
            pf.forecast_toi_minutes,
            pf.forecast_cf60,
            pf.forecast_ca60,
            pf.forecast_gf60,
            pf.forecast_ga60,
            
            -- Get historical data for comparison
            pit.ev_points_60 as historical_points_60,
            pit.ev_toi_avg_minutes as historical_toi,
            pit.ev_cf60 as historical_cf60,
            pit.ev_ca60 as historical_ca60,
            pit.ev_gf60 as historical_gf60,
            pit.ev_ga60 as historical_ga60,
            pit.gp_3yr_avg as historical_gp_avg,
            
            -- Calculate variance from historical performance
            ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) as points_variance_pct,
            ABS(pf.forecast_toi_minutes - pit.ev_toi_avg_minutes) / NULLIF(pit.ev_toi_avg_minutes, 0) as toi_variance_pct,
            ABS(pf.forecast_cf60 - pit.ev_cf60) / NULLIF(pit.ev_cf60, 0) as cf_variance_pct,
            ABS(pf.forecast_ca60 - pit.ev_ca60) / NULLIF(pit.ev_ca60, 0) as ca_variance_pct,
            
            -- Flag conditions
            CASE 
                WHEN ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) > 0.5 THEN 'HIGH_POINTS_VARIANCE'
                WHEN ABS(pf.forecast_toi_minutes - pit.ev_toi_avg_minutes) / NULLIF(pit.ev_toi_avg_minutes, 0) > 0.3 THEN 'HIGH_TOI_VARIANCE'
                WHEN pf.forecast_points_60_adjusted > 3.0 AND pit.ev_points_60 < 1.5 THEN 'UNREALISTIC_ELITE_JUMP'
                WHEN pf.forecast_points_60_adjusted < 0.5 AND pit.ev_points_60 > 1.5 THEN 'UNREALISTIC_DECLINE'
                WHEN pf.forecast_cf60 < 0 OR pf.forecast_ca60 < 0 THEN 'NEGATIVE_METRICS'
                WHEN pf.forecast_toi_minutes > 25 THEN 'EXCESSIVE_TOI'
                WHEN pf.forecast_toi_minutes < 5 THEN 'INSUFFICIENT_TOI'
                ELSE NULL
            END as flag_reason,
            
            -- Severity level
            CASE 
                WHEN ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) > 1.0 THEN 'CRITICAL'
                WHEN ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) > 0.5 THEN 'HIGH'
                WHEN ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) > 0.3 THEN 'MEDIUM'
                WHEN ABS(pf.forecast_points_60_adjusted - pit.ev_points_60) / NULLIF(pit.ev_points_60, 0) > 0.2 THEN 'LOW'
                ELSE 'NONE'
            END as severity_level
            
        FROM `fantasy-snipe-ai.nhl_projections.player_forecasts` pf
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.player_input_templates` pit 
            ON pf.player_id = pit.player_id
    ),
    team_balance_validation AS (
        -- Check team-level balance (Foster's requirement: EV GF = GA, PP/SH balance)
        SELECT 
            lf.team,
            SUM(CASE WHEN lf.position_group = 'F' THEN lf.forecast_gf60 ELSE 0 END) as total_forward_gf60,
            SUM(CASE WHEN lf.position_group = 'D' THEN lf.forecast_gf60 ELSE 0 END) as total_defense_gf60,
            SUM(lf.forecast_gf60) as total_team_gf60,
            SUM(lf.forecast_ga60) as total_team_ga60,
            SUM(lf.forecast_cf60) as total_team_cf60,
            SUM(lf.forecast_ca60) as total_team_ca60,
            
            -- Balance checks
            ABS(SUM(lf.forecast_gf60) - SUM(lf.forecast_ga60)) as gf_ga_imbalance,
            CASE 
                WHEN ABS(SUM(lf.forecast_gf60) - SUM(lf.forecast_ga60)) > 50 THEN 'UNBALANCED_GF_GA'
                WHEN SUM(lf.forecast_cf60) < SUM(lf.forecast_ca60) THEN 'NEGATIVE_CF_BALANCE'
                ELSE NULL
            END as team_flag_reason
            
        FROM `fantasy-snipe-ai.nhl_projections.line_forecasts` lf
        GROUP BY lf.team
    ),
    validation_flags AS (
        SELECT 
            pfv.player_id,
            pfv.player_name,
            pfv.team,
            pfv.primary_role,
            pfv.flag_reason,
            pfv.severity_level,
            pfv.forecast_points_60_adjusted,
            pfv.historical_points_60,
            pfv.points_variance_pct,
            pfv.toi_variance_pct,
            pfv.cf_variance_pct,
            pfv.ca_variance_pct,
            'PLAYER' as flag_type,
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM player_forecast_validation pfv
        WHERE pfv.flag_reason IS NOT NULL
        
        UNION ALL
        
        SELECT 
            NULL as player_id,
            tbv.team as player_name,
            tbv.team,
            'TEAM' as primary_role,
            tbv.team_flag_reason as flag_reason,
            CASE 
                WHEN tbv.gf_ga_imbalance > 100 THEN 'CRITICAL'
                WHEN tbv.gf_ga_imbalance > 50 THEN 'HIGH'
                WHEN tbv.gf_ga_imbalance > 25 THEN 'MEDIUM'
                ELSE 'LOW'
            END as severity_level,
            tbv.total_team_gf60 as forecast_points_60_adjusted,
            tbv.total_team_ga60 as historical_points_60,
            tbv.gf_ga_imbalance as points_variance_pct,
            NULL as toi_variance_pct,
            NULL as cf_variance_pct,
            NULL as ca_variance_pct,
            'TEAM' as flag_type,
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM team_balance_validation tbv
        WHERE tbv.team_flag_reason IS NOT NULL
    )
    SELECT * FROM validation_flags
    ORDER BY severity_level DESC, flag_type, team, player_name
    """
    
    job = client.query(validation_flags_query)
    job.result()
    print("Validation flags created successfully!")
    
    # Create manual adjustments table
    print("Creating manual adjustments system...")
    manual_adjustments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.manual_adjustments` (
        adjustment_id INT64,
        player_id INT64,
        player_name STRING,
        team STRING,
        adjustment_type STRING,
        field_name STRING,
        original_value FLOAT64,
        adjusted_value FLOAT64,
        reason STRING,
        adjusted_by STRING,
        adjustment_date TIMESTAMP,
        notes STRING,
        created_at TIMESTAMP,
        model_version STRING
    )
    """
    
    job = client.query(manual_adjustments_query)
    job.result()
    print("Manual adjustments table created successfully!")
    
    # Create current player forecasts view (for easy access)
    print("Creating current player forecasts view...")
    current_forecasts_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts` AS
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
        -- Calculate projected season totals
        ROUND(pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_points,
        ROUND(pf.goals_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_goals,
        ROUND(pf.assists_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_assists,
        -- Add validation flags
        vf.flag_reason,
        vf.severity_level,
        pf.created_at,
        pf.model_version
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts` pf
    LEFT JOIN `fantasy-snipe-ai.nhl_projections.validation_flags` vf 
        ON pf.player_id = vf.player_id
    ORDER BY pf.forecast_points_60_adjusted DESC
    """
    
    job = client.query(current_forecasts_query)
    job.result()
    print("Current player forecasts view created successfully!")
    
    # Run QA on validation system
    print("\nRunning QA on validation system...")
    
    # QA for validation flags
    qa_validation_flags = """
    SELECT 
        COUNT(*) as total_flags,
        COUNT(CASE WHEN flag_type = 'PLAYER' THEN 1 END) as player_flags,
        COUNT(CASE WHEN flag_type = 'TEAM' THEN 1 END) as team_flags,
        COUNT(CASE WHEN severity_level = 'CRITICAL' THEN 1 END) as critical_flags,
        COUNT(CASE WHEN severity_level = 'HIGH' THEN 1 END) as high_flags,
        COUNT(CASE WHEN severity_level = 'MEDIUM' THEN 1 END) as medium_flags,
        COUNT(CASE WHEN severity_level = 'LOW' THEN 1 END) as low_flags,
        COUNT(DISTINCT team) as teams_with_flags,
        AVG(points_variance_pct) as avg_points_variance
    FROM `fantasy-snipe-ai.nhl_projections.validation_flags`
    """
    
    qa_job = client.query(qa_validation_flags)
    qa_results = qa_job.result()
    
    print("Validation Flags QA:")
    for row in qa_results:
        print(f"  Total flags: {row.total_flags}")
        print(f"  Player flags: {row.player_flags}")
        print(f"  Team flags: {row.team_flags}")
        print(f"  Critical flags: {row.critical_flags}")
        print(f"  High flags: {row.high_flags}")
        print(f"  Medium flags: {row.medium_flags}")
        print(f"  Low flags: {row.low_flags}")
        print(f"  Teams with flags: {row.teams_with_flags}")
        print(f"  Avg points variance: {row.avg_points_variance:.3f}")
    
    # QA for current forecasts view
    qa_current_forecasts = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(CASE WHEN flag_reason IS NOT NULL THEN 1 END) as flagged_players,
        AVG(forecast_points_60) as avg_points_60,
        MAX(forecast_points_60) as max_points_60,
        AVG(projected_points) as avg_projected_points,
        MAX(projected_points) as max_projected_points,
        COUNT(CASE WHEN projected_points > 100 THEN 1 END) as high_scorers,
        COUNT(CASE WHEN projected_points > 80 THEN 1 END) as top_scorers
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts`
    """
    
    qa_job2 = client.query(qa_current_forecasts)
    qa_results2 = qa_job2.result()
    
    print("\nCurrent Player Forecasts QA:")
    for row in qa_results2:
        print(f"  Total players: {row.total_players}")
        print(f"  Flagged players: {row.flagged_players}")
        print(f"  Avg points/60: {row.avg_points_60:.2f}")
        print(f"  Max points/60: {row.max_points_60:.2f}")
        print(f"  Avg projected points: {row.avg_projected_points:.1f}")
        print(f"  Max projected points: {row.max_projected_points:.1f}")
        print(f"  High scorers (>100 pts): {row.high_scorers}")
        print(f"  Top scorers (>80 pts): {row.top_scorers}")

if __name__ == "__main__":
    create_validation_system()
