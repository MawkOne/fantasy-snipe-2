#!/usr/bin/env python3
"""
Fix TOI allocation to respect special teams roles:
- Only PP1/PP2 players get PP time
- Only PK1/PK2 players get PK time
- All players get 5v5 time
- Distribute TOI based on actual roles, not team averages
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_toi_allocation_by_role():
    """Fix TOI allocation to respect special teams roles."""
    client = bigquery.Client()
    
    print("Fixing TOI allocation to respect special teams roles...")
    
    # 1. Create proper TOI allocation by role
    print("1. Creating proper TOI allocation by role...")
    toi_allocation_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_role_based` AS
    WITH player_forecasts AS (
        SELECT 
            la.player_id,
            la.player_name,
            la.position,
            la.team,
            la.primary_role,
            la.special_teams_role,
            la.forecast_toi_minutes as total_toi_minutes,
            la.ev_cf60,
            la.ev_ca60,
            la.ev_gf60,
            la.ev_ga60,
            la.ev_pts_conversion,
            la.pp_goals_3yr_avg,
            la.pp_points_3yr_avg,
            la.sh_goals_3yr_avg,
            la.sh_points_3yr_avg,
            
            -- Get team-specific TOI distribution
            COALESCE(ev_dist.pct_of_total_toi, 77.1) as ev_toi_pct,
            COALESCE(pp1_dist.pct_of_total_toi, 0) as pp1_toi_pct,
            COALESCE(pp2_dist.pct_of_total_toi, 0) as pp2_toi_pct,
            COALESCE(pk_dist.pct_of_total_toi, 10.1) as pk_toi_pct,
            
            -- 5v5 (Even Strength) projections - ALL players get this
            la.ev_pts_conversion * 60.0 as ev_points_60,
            
            -- Power Play projections - ONLY for PP1/PP2 players
            CASE 
                WHEN la.special_teams_role = 'PP1' AND la.pp_points_3yr_avg > 0 THEN
                    (la.pp_points_3yr_avg / 82.0) / 3.5 * 60.0  -- 3.5 min PP TOI per game for PP1
                WHEN la.special_teams_role = 'PP2' AND la.pp_points_3yr_avg > 0 THEN
                    (la.pp_points_3yr_avg / 82.0) / 1.5 * 60.0  -- 1.5 min PP TOI per game for PP2
                ELSE 0
            END as pp_points_60,
            
            -- Penalty Kill projections - ONLY for PK1/PK2 players
            CASE 
                WHEN la.special_teams_role IN ('PK1', 'PK2') AND la.sh_points_3yr_avg > 0 THEN
                    (la.sh_points_3yr_avg / 82.0) / 2.5 * 60.0  -- 2.5 min PK TOI per game
                ELSE 0
            END as sh_points_60,
            
            -- TOI allocation based on ACTUAL roles
            -- 5v5 TOI: All players get their full TOI at 5v5
            la.forecast_toi_minutes as ev_toi_minutes,
            
            -- PP TOI: Only for PP1/PP2 players
            CASE 
                WHEN la.special_teams_role = 'PP1' THEN 3.5  -- 3.5 min per game
                WHEN la.special_teams_role = 'PP2' THEN 1.5  -- 1.5 min per game
                ELSE 0
            END as pp_toi_minutes,
            
            -- PK TOI: Only for PK1/PK2 players
            CASE 
                WHEN la.special_teams_role IN ('PK1', 'PK2') THEN 2.5  -- 2.5 min per game
                ELSE 0
            END as pk_toi_minutes,
            
            -- G/A splits for each situation
            CASE 
                WHEN la.ev_pts_conversion > 0 THEN
                    la.ev_gf60 / (la.ev_gf60 + la.ev_ca60 * 0.7)
                ELSE 0.4
            END as ev_goals_share,
            
            CASE 
                WHEN la.ev_pts_conversion > 0 THEN
                    (la.ev_ca60 * 0.7) / (la.ev_gf60 + la.ev_ca60 * 0.7)
                ELSE 0.6
            END as ev_assists_share,
            
            -- PP G/A splits (typically more assists on PP)
            CASE 
                WHEN la.pp_points_3yr_avg > 0 THEN
                    la.pp_goals_3yr_avg / la.pp_points_3yr_avg
                ELSE 0.3
            END as pp_goals_share,
            
            CASE 
                WHEN la.pp_points_3yr_avg > 0 THEN
                    (la.pp_points_3yr_avg - la.pp_goals_3yr_avg) / la.pp_points_3yr_avg
                ELSE 0.7
            END as pp_assists_share,
            
            -- SH G/A splits (typically more goals on PK)
            CASE 
                WHEN la.sh_points_3yr_avg > 0 THEN
                    la.sh_goals_3yr_avg / la.sh_points_3yr_avg
                ELSE 0.6
            END as sh_goals_share,
            
            CASE 
                WHEN la.sh_points_3yr_avg > 0 THEN
                    (la.sh_points_3yr_avg - la.sh_goals_3yr_avg) / la.sh_points_3yr_avg
                ELSE 0.4
            END as sh_assists_share,
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v2.3 (Role-Based)' as model_version
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_final` la
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.team_toi_distribution` ev_dist 
            ON la.team = ev_dist.team AND ev_dist.situation = 'EV'
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.team_toi_distribution` pp1_dist 
            ON la.team = pp1_dist.team AND pp1_dist.situation = 'PP1'
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.team_toi_distribution` pp2_dist 
            ON la.team = pp2_dist.team AND pp2_dist.situation = 'PP2'
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.team_toi_distribution` pk_dist 
            ON la.team = pk_dist.team AND pk_dist.situation = 'SH'
        WHERE la.primary_role IN ('1L', '2L', '3L', '4L', '1D', '2D', '3D')
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, (ev_points_60 + pp_points_60 + sh_points_60) DESC
    """
    
    job = client.query(toi_allocation_query)
    job.result()
    print("✓ Created role-based TOI allocation")
    
    # 2. Create final view with proper role-based projections
    print("2. Creating final view with role-based projections...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_role_based` AS
    SELECT 
        pf.player_id,
        pf.player_name,
        pf.position,
        pf.team,
        pf.primary_role,
        pf.special_teams_role,
        pf.total_toi_minutes,
        
        -- 5v5 projections
        ROUND(pf.ev_points_60, 2) as ev_points_60,
        ROUND(pf.ev_toi_minutes, 1) as ev_toi_minutes,
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_points,
        ROUND(pf.ev_goals_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_goals,
        ROUND(pf.ev_assists_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_assists,
        
        -- Power Play projections (ONLY for PP1/PP2 players)
        ROUND(pf.pp_points_60, 2) as pp_points_60,
        ROUND(pf.pp_toi_minutes, 1) as pp_toi_minutes,
        ROUND(pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_points,
        ROUND(pf.pp_goals_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_goals,
        ROUND(pf.pp_assists_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_assists,
        
        -- Penalty Kill projections (ONLY for PK1/PK2 players)
        ROUND(pf.sh_points_60, 2) as sh_points_60,
        ROUND(pf.pk_toi_minutes, 1) as pk_toi_minutes,
        ROUND(pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_points,
        ROUND(pf.sh_goals_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_goals,
        ROUND(pf.sh_assists_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_assists,
        
        -- Total projections
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_points,
        ROUND(pf.ev_goals_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_goals_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_goals_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_goals,
        ROUND(pf.ev_assists_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_assists_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_assists_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_assists,
        
        -- Situation breakdown percentages
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as ev_points_pct,
        ROUND(pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as pp_points_pct,
        ROUND(pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as pk_points_pct,
        
        pf.created_at,
        pf.model_version
        
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_role_based` pf
    ORDER BY total_projected_points DESC
    """
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final view with role-based projections")
    
    # Run QA
    print("\nRunning QA on role-based model...")
    
    # Check top projections with proper role-based allocation
    qa_projections = """
    SELECT 
        player_name,
        team,
        primary_role,
        special_teams_role,
        total_projected_points,
        ev_projected_points,
        pp_projected_points,
        pk_projected_points,
        ev_points_pct,
        pp_points_pct,
        pk_points_pct,
        ev_toi_minutes,
        pp_toi_minutes,
        pk_toi_minutes
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_role_based`
    WHERE player_name IN ('Connor McDavid', 'Evan Bouchard', 'Cale Makar', 'Leon Draisaitl')
    ORDER BY total_projected_points DESC
    """
    
    qa_job = client.query(qa_projections)
    qa_results = qa_job.result()
    
    print("Role-based projections (key players):")
    for row in qa_results:
        print(f"  {row.player_name} ({row.primary_role}, {row.special_teams_role}):")
        print(f"    Total: {row.total_projected_points} pts")
        print(f"    5v5: {row.ev_projected_points} pts ({row.ev_points_pct}%) - {row.ev_toi_minutes} min")
        print(f"    PP: {row.pp_projected_points} pts ({row.pp_points_pct}%) - {row.pp_toi_minutes} min")
        print(f"    PK: {row.pk_projected_points} pts ({row.pk_points_pct}%) - {row.pk_toi_minutes} min")
        print()

if __name__ == "__main__":
    fix_toi_allocation_by_role()
