#!/usr/bin/env python3
"""
Fix the line forecast calculation to properly average player stats instead of summing them.
This implements Foster's correct method: sum individual stats, then divide by number of players on line.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_line_forecast_calculation():
    """Fix the line forecast calculation to properly average player stats."""
    client = bigquery.Client()
    
    print("Fixing line forecast calculation...")
    
    # Fix line forecasts with proper averaging
    fix_line_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_forecasts_fixed` AS
    WITH team_lines AS (
        -- Group players by team and line/pair with proper counting
        SELECT 
            la.team,
            la.primary_role,
            la.position_group,
            COUNT(*) as players_on_line,
            -- Sum up individual player stats for the line
            SUM(la.ev_cf60) as line_cf60_sum,
            SUM(la.ev_ca60) as line_ca60_sum,
            SUM(la.ev_gf60) as line_gf60_sum,
            SUM(la.ev_ga60) as line_ga60_sum,
            SUM(la.ev_pts_conversion) as line_pts_conversion_sum,
            -- Calculate line averages (Foster's method: sum ÷ number of players)
            SUM(la.ev_cf60) / COUNT(*) as line_cf60_avg,
            SUM(la.ev_ca60) / COUNT(*) as line_ca60_avg,
            SUM(la.ev_gf60) / COUNT(*) as line_gf60_avg,
            SUM(la.ev_ga60) / COUNT(*) as line_ga60_avg,
            SUM(la.ev_pts_conversion) / COUNT(*) as line_pts_conversion_avg,
            -- Calculate line chemistry factor
            STDDEV(la.ev_cf60) as cf60_stddev,
            STDDEV(la.ev_pts_conversion) as pts_conversion_stddev
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_clean` la
        WHERE la.primary_role IN ('1L', '2L', '3L', '4L', '1D', '2D', '3D')
        GROUP BY la.team, la.primary_role, la.position_group
    ),
    line_forecasts AS (
        SELECT 
            tl.team,
            tl.primary_role as line_role,
            tl.position_group,
            tl.players_on_line,
            
            -- Use AVERAGED values (Foster's method)
            tl.line_cf60_avg as forecast_cf60,
            tl.line_ca60_avg as forecast_ca60,
            tl.line_gf60_avg as forecast_gf60,
            tl.line_ga60_avg as forecast_ga60,
            
            -- Line chemistry factors
            tl.cf60_stddev,
            tl.pts_conversion_stddev,
            CASE 
                WHEN tl.cf60_stddev < 5.0 THEN 1.05  -- Good chemistry
                WHEN tl.cf60_stddev < 10.0 THEN 1.0  -- Average chemistry
                ELSE 0.95  -- Poor chemistry
            END as chemistry_multiplier,
            
            -- Line GF/CF conversion rate (using averaged values)
            CASE 
                WHEN tl.line_cf60_avg > 0 THEN tl.line_gf60_avg / tl.line_cf60_avg
                ELSE 0
            END as line_gf_cf_conversion,
            
            -- Line GA/CA conversion rate (using averaged values)
            CASE 
                WHEN tl.line_ca60_avg > 0 THEN tl.line_ga60_avg / tl.line_ca60_avg
                ELSE 0
            END as line_ga_ca_conversion,
            
            -- Line points conversion (using averaged values)
            tl.line_pts_conversion_avg as line_pts_conversion,
            
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
            'Foster Model v1.1 (Fixed)' as model_version
            
        FROM team_lines tl
    )
    SELECT * FROM line_forecasts
    ORDER BY team, line_role
    """
    
    job = client.query(fix_line_forecasts_query)
    job.result()
    print("✓ Fixed line forecasts calculation")
    
    # Fix player forecasts with corrected line values
    print("Fixing player forecasts with corrected line values...")
    fix_player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_fixed` AS
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
            
            -- Get corrected line forecasts
            lf.forecast_cf60 as line_cf60,
            lf.forecast_ca60 as line_ca60,
            lf.forecast_gf60 as line_gf60,
            lf.forecast_ga60 as line_ga60,
            lf.line_gf_cf_conversion,
            lf.line_ga_ca_conversion,
            lf.line_pts_conversion,
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
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_clean` la
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.line_forecasts_fixed` lf 
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
            
            -- Individual player forecasts
            plf.ev_cf60 as forecast_cf60,
            plf.ev_ca60 as forecast_ca60,
            plf.ev_gf60 as forecast_gf60,
            plf.ev_ga60 as forecast_ga60,
            plf.ev_pts_conversion as forecast_pts_conversion,
            
            -- Line-level forecasts (corrected)
            plf.line_cf60,
            plf.line_ca60,
            plf.line_gf60,
            plf.line_ga60,
            plf.line_gf_cf_conversion,
            plf.line_ga_ca_conversion,
            plf.line_pts_conversion,
            
            -- Points allocation using Foster's formula (corrected):
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
            
            -- Historical G/A split (simplified)
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
            'Foster Model v1.1 (Fixed)' as model_version
            
        FROM player_line_forecasts plf
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, forecast_points_60_adjusted DESC
    """
    
    job = client.query(fix_player_forecasts_query)
    job.result()
    print("✓ Fixed player forecasts with corrected line values")
    
    # Create final clean view with corrected calculations
    print("Creating final clean view with corrected calculations...")
    create_final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_corrected` AS
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
        -- Calculate projected season totals (82 games) - REALISTIC VALUES
        ROUND(pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_points,
        ROUND(pf.goals_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_goals,
        ROUND(pf.assists_share * pf.forecast_points_60_adjusted * pf.forecast_toi_minutes / 60.0 * 82, 1) as projected_assists,
        pf.created_at,
        pf.model_version
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_fixed` pf
    ORDER BY pf.forecast_points_60_adjusted DESC
    """
    
    job = client.query(create_final_view_query)
    job.result()
    print("✓ Created final corrected view")
    
    # Run QA on corrected calculations
    print("\nRunning QA on corrected calculations...")
    
    # QA for line forecasts
    qa_line_forecasts = """
    SELECT 
        team,
        line_role,
        players_on_line,
        ROUND(forecast_gf60, 2) as forecast_gf60,
        ROUND(line_gf_cf_conversion, 4) as line_gf_cf_conversion,
        ROUND(chemistry_multiplier, 3) as chemistry_multiplier
    FROM `fantasy-snipe-ai.nhl_projections.line_forecasts_fixed`
    WHERE team = 'EDM'
    ORDER BY line_role
    """
    
    qa_job = client.query(qa_line_forecasts)
    qa_results = qa_job.result()
    
    print("Corrected Line Forecasts (Edmonton):")
    for row in qa_results:
        print(f"  {row.line_role}: {row.players_on_line} players, {row.forecast_gf60} GF/60, {row.line_gf_cf_conversion} conversion, {row.chemistry_multiplier} chemistry")
    
    # QA for player forecasts
    qa_player_forecasts = """
    SELECT 
        player_name,
        team,
        primary_role,
        ROUND(forecast_points_60, 2) as forecast_points_60,
        ROUND(projected_points, 1) as projected_points,
        ROUND(projected_goals, 1) as projected_goals,
        ROUND(projected_assists, 1) as projected_assists
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_corrected`
    WHERE team = 'EDM'
    ORDER BY projected_points DESC
    LIMIT 5
    """
    
    qa_job2 = client.query(qa_player_forecasts)
    qa_results2 = qa_job2.result()
    
    print("\nCorrected Player Forecasts (Edmonton):")
    for row in qa_results2:
        print(f"  {row.player_name} ({row.primary_role}): {row.forecast_points_60} P/60 → {row.projected_points} pts ({row.projected_goals}G, {row.projected_assists}A)")

if __name__ == "__main__":
    fix_line_forecast_calculation()
