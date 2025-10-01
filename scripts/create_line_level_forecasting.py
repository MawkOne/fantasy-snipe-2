#!/usr/bin/env python3
"""
Create Line-Level Forecasting Engine for Foster's forecasting method.
This implements the core calculation engine for CF, CA, GF, GA by line and points allocation.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_line_level_forecasting():
    """Create line-level forecasting engine with CF, CA, GF, GA calculations."""
    client = bigquery.Client()
    
    # Create line forecasts table
    print("Creating line forecasts...")
    line_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_forecasts` AS
    WITH team_lines AS (
        -- Group players by team and line/pair
        SELECT 
            la.team,
            la.primary_role,
            la.position_group,
            COUNT(*) as players_on_line,
            -- Sum up individual player stats for the line
            SUM(la.ev_cf60) as line_cf60,
            SUM(la.ev_ca60) as line_ca60,
            SUM(la.ev_gf60) as line_gf60,
            SUM(la.ev_ga60) as line_ga60,
            SUM(la.ev_pts_conversion) as line_pts_conversion,
            -- Calculate line averages
            AVG(la.ev_cf60) as avg_cf60,
            AVG(la.ev_ca60) as avg_ca60,
            AVG(la.ev_gf60) as avg_gf60,
            AVG(la.ev_ga60) as avg_ga60,
            AVG(la.ev_pts_conversion) as avg_pts_conversion,
            -- Calculate line chemistry factor (how well players work together)
            STDDEV(la.ev_cf60) as cf60_stddev,
            STDDEV(la.ev_pts_conversion) as pts_conversion_stddev
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments` la
        WHERE la.primary_role IN ('1L', '2L', '3L', '4L', '1D', '2D', '3D')
        GROUP BY la.team, la.primary_role, la.position_group
    ),
    line_forecasts AS (
        SELECT 
            tl.team,
            tl.primary_role as line_role,
            tl.position_group,
            tl.players_on_line,
            
            -- Line-level CF/CA forecasts (Foster's requirement)
            tl.line_cf60 as forecast_cf60,
            tl.line_ca60 as forecast_ca60,
            tl.line_gf60 as forecast_gf60,
            tl.line_ga60 as forecast_ga60,
            
            -- Line chemistry factors
            tl.cf60_stddev,
            tl.pts_conversion_stddev,
            CASE 
                WHEN tl.cf60_stddev < 5.0 THEN 1.05  -- Good chemistry
                WHEN tl.cf60_stddev < 10.0 THEN 1.0  -- Average chemistry
                ELSE 0.95  -- Poor chemistry
            END as chemistry_multiplier,
            
            -- Line GF/CF conversion rate (Foster's requirement)
            CASE 
                WHEN tl.line_cf60 > 0 THEN tl.line_gf60 / tl.line_cf60
                ELSE 0
            END as line_gf_cf_conversion,
            
            -- Line GA/CA conversion rate (Foster's requirement)
            CASE 
                WHEN tl.line_ca60 > 0 THEN tl.line_ga60 / tl.line_ca60
                ELSE 0
            END as line_ga_ca_conversion,
            
            -- Line points conversion (Foster's requirement)
            tl.line_pts_conversion as line_pts_conversion,
            
            -- Expected TOI for the line (based on role)
            CASE 
                WHEN tl.primary_role = '1L' THEN 18.0
                WHEN tl.primary_role = '2L' THEN 16.0
                WHEN tl.primary_role = '3L' THEN 14.0
                WHEN tl.primary_role = '4L' THEN 12.0
                WHEN tl.primary_role = '1D' THEN 22.0
                WHEN tl.primary_role = '2D' THEN 20.0
                WHEN tl.primary_role = '3D' THEN 18.0
                ELSE 15.0
            END as expected_toi_minutes,
            
            -- Metadata
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM team_lines tl
    )
    SELECT * FROM line_forecasts
    ORDER BY team, line_role
    """
    
    job = client.query(line_forecasts_query)
    job.result()
    print("Line forecasts created successfully!")
    
    # Create player forecasts table
    print("Creating player forecasts...")
    player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts` AS
    WITH player_line_forecasts AS (
        SELECT 
            la.player_id,
            la.player_name,
            la.position,
            la.team,
            la.primary_role,
            la.ev_toi_avg_minutes,
            la.ev_cf60,
            la.ev_ca60,
            la.ev_gf60,
            la.ev_ga60,
            la.ev_pts_conversion,
            la.special_teams_role,
            
            -- Get line forecasts for this player's line
            lf.forecast_cf60 as line_cf60,
            lf.forecast_ca60 as line_ca60,
            lf.forecast_gf60 as line_gf60,
            lf.forecast_ga60 as line_ga60,
            lf.line_gf_cf_conversion,
            lf.line_ga_ca_conversion,
            lf.line_pts_conversion as line_pts_conversion,
            lf.chemistry_multiplier,
            lf.expected_toi_minutes as line_expected_toi,
            
            -- Calculate player's share of line TOI
            CASE 
                WHEN lf.expected_toi_minutes > 0 THEN 
                    la.ev_toi_avg_minutes / lf.expected_toi_minutes
                ELSE 0
            END as toi_share_of_line,
            
            -- Calculate player's individual contribution to line
            CASE 
                WHEN lf.forecast_cf60 > 0 THEN 
                    la.ev_cf60 / lf.forecast_cf60
                ELSE 0
            END as cf_contribution_share,
            
            CASE 
                WHEN lf.forecast_gf60 > 0 THEN 
                    la.ev_gf60 / lf.forecast_gf60
                ELSE 0
            END as gf_contribution_share
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments` la
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.line_forecasts` lf 
            ON la.team = lf.team AND la.primary_role = lf.line_role
        WHERE la.primary_role IN ('1L', '2L', '3L', '4L', '1D', '2D', '3D')
    ),
    player_forecasts AS (
        SELECT 
            plf.player_id,
            plf.player_name,
            plf.position,
            plf.team,
            plf.primary_role,
            plf.special_teams_role,
            
            -- Individual player forecasts (Foster's requirement)
            plf.ev_cf60 as forecast_cf60,
            plf.ev_ca60 as forecast_ca60,
            plf.ev_gf60 as forecast_gf60,
            plf.ev_ga60 as forecast_ga60,
            plf.ev_pts_conversion as forecast_pts_conversion,
            
            -- Line-level forecasts
            plf.line_cf60,
            plf.line_ca60,
            plf.line_gf60,
            plf.line_ga60,
            plf.line_gf_cf_conversion,
            plf.line_ga_ca_conversion,
            plf.line_pts_conversion,
            
            -- Points allocation using Foster's formula:
            -- Line GF * (player TOI / total line TOI) * (player pts conversion / line GF/CF conversion)
            CASE 
                WHEN plf.line_gf60 > 0 AND plf.line_gf_cf_conversion > 0 THEN
                    plf.line_gf60 * plf.toi_share_of_line * (plf.ev_pts_conversion / plf.line_gf_cf_conversion)
                ELSE 0
            END as forecast_points_60,
            
            -- Apply chemistry multiplier
            CASE 
                WHEN plf.line_gf60 > 0 AND plf.line_gf_cf_conversion > 0 THEN
                    plf.line_gf60 * plf.toi_share_of_line * (plf.ev_pts_conversion / plf.line_gf_cf_conversion) * plf.chemistry_multiplier
                ELSE 0
            END as forecast_points_60_adjusted,
            
            -- TOI forecasts
            plf.ev_toi_avg_minutes as forecast_toi_minutes,
            plf.toi_share_of_line,
            plf.line_expected_toi,
            
            -- Contribution metrics
            plf.cf_contribution_share,
            plf.gf_contribution_share,
            
            -- Historical G/A split (simplified - would need more data for accuracy)
            CASE 
                WHEN plf.ev_pts_conversion > 0 THEN
                    plf.ev_gf60 / (plf.ev_gf60 + plf.ev_ca60 * 0.7)  -- Rough G/A split
                ELSE 0.4  -- Default 40% goals, 60% assists
            END as goals_share,
            
            CASE 
                WHEN plf.ev_pts_conversion > 0 THEN
                    (plf.ev_ca60 * 0.7) / (plf.ev_gf60 + plf.ev_ca60 * 0.7)  -- Rough G/A split
                ELSE 0.6  -- Default 40% goals, 60% assists
            END as assists_share,
            
            -- Metadata
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM player_line_forecasts plf
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, forecast_points_60_adjusted DESC
    """
    
    job = client.query(player_forecasts_query)
    job.result()
    print("Player forecasts created successfully!")
    
    # Run QA on both tables
    print("\nRunning QA on line-level forecasting...")
    
    # QA for line forecasts
    qa_line_forecasts = """
    SELECT 
        COUNT(*) as total_lines,
        COUNT(DISTINCT team) as teams_covered,
        COUNT(CASE WHEN position_group = 'F' THEN 1 END) as forward_lines,
        COUNT(CASE WHEN position_group = 'D' THEN 1 END) as defense_pairs,
        AVG(forecast_cf60) as avg_cf60,
        AVG(forecast_ca60) as avg_ca60,
        AVG(forecast_gf60) as avg_gf60,
        AVG(forecast_ga60) as avg_ga60,
        AVG(chemistry_multiplier) as avg_chemistry,
        AVG(line_gf_cf_conversion) as avg_gf_cf_conversion
    FROM `fantasy-snipe-ai.nhl_projections.line_forecasts`
    """
    
    qa_job = client.query(qa_line_forecasts)
    qa_results = qa_job.result()
    
    print("Line Forecasts QA:")
    for row in qa_results:
        print(f"  Total lines: {row.total_lines}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  Forward lines: {row.forward_lines}")
        print(f"  Defense pairs: {row.defense_pairs}")
        print(f"  Avg CF/60: {row.avg_cf60:.2f}")
        print(f"  Avg CA/60: {row.avg_ca60:.2f}")
        print(f"  Avg GF/60: {row.avg_gf60:.2f}")
        print(f"  Avg GA/60: {row.avg_ga60:.2f}")
        print(f"  Avg chemistry: {row.avg_chemistry:.3f}")
        print(f"  Avg GF/CF conversion: {row.avg_gf_cf_conversion:.4f}")
    
    # QA for player forecasts
    qa_player_forecasts = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(DISTINCT team) as teams_covered,
        AVG(forecast_points_60) as avg_points_60,
        AVG(forecast_points_60_adjusted) as avg_points_60_adjusted,
        MAX(forecast_points_60_adjusted) as max_points_60,
        AVG(forecast_toi_minutes) as avg_toi_minutes,
        AVG(goals_share) as avg_goals_share,
        AVG(assists_share) as avg_assists_share,
        COUNT(CASE WHEN forecast_points_60_adjusted > 2.0 THEN 1 END) as elite_players,
        COUNT(CASE WHEN forecast_points_60_adjusted > 1.5 THEN 1 END) as high_end_players
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts`
    """
    
    qa_job2 = client.query(qa_player_forecasts)
    qa_results2 = qa_job2.result()
    
    print("\nPlayer Forecasts QA:")
    for row in qa_results2:
        print(f"  Total players: {row.total_players}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  Avg points/60: {row.avg_points_60:.2f}")
        print(f"  Avg points/60 (adjusted): {row.avg_points_60_adjusted:.2f}")
        print(f"  Max points/60: {row.max_points_60:.2f}")
        print(f"  Avg TOI: {row.avg_toi_minutes:.1f} minutes")
        print(f"  Avg goals share: {row.avg_goals_share:.3f}")
        print(f"  Avg assists share: {row.avg_assists_share:.3f}")
        print(f"  Elite players (>2.0 P/60): {row.elite_players}")
        print(f"  High-end players (>1.5 P/60): {row.high_end_players}")

if __name__ == "__main__":
    create_line_level_forecasting()
