#!/usr/bin/env python3
"""
Fix special teams assignments to include defensemen.
Cale Makar and Evan Bouchard should be PP1 based on their PP stats.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_special_teams_for_defensemen():
    """Fix special teams assignments to include defensemen."""
    client = bigquery.Client()
    
    print("Fixing special teams assignments to include defensemen...")
    
    # 1. Create corrected line assignments with proper special teams for defensemen
    print("1. Creating corrected line assignments with defensemen special teams...")
    line_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_final` AS
    WITH team_rosters AS (
        SELECT 
            pit.player_id,
            pit.player_name,
            pit.position,
            pit.position_group,
            pit.team,
            pit.age,
            pit.gp_3yr_avg,
            pit.ev_toi_avg_minutes,
            pit.ev_points_60,
            pit.ev_cf60,
            pit.ev_ca60,
            pit.ev_gf60,
            pit.ev_ga60,
            pit.player_archetype,
            pit.ev_pts_conversion,
            pit.pp_goals_3yr_avg,
            pit.pp_points_3yr_avg,
            pit.sh_goals_3yr_avg,
            pit.sh_points_3yr_avg,
            -- Rank players by performance within their team and position (ONE PER PLAYER)
            ROW_NUMBER() OVER (
                PARTITION BY pit.team, pit.position_group 
                ORDER BY pit.ev_points_60 DESC, pit.ev_toi_avg_minutes DESC
            ) as team_position_rank
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated_final` pit
        WHERE pit.team IS NOT NULL
    ),
    line_assignments AS (
        SELECT 
            tr.player_id,
            tr.player_name,
            tr.position,
            tr.position_group,
            tr.team,
            tr.age,
            tr.gp_3yr_avg,
            tr.ev_toi_avg_minutes,
            tr.ev_points_60,
            tr.ev_cf60,
            tr.ev_ca60,
            tr.ev_gf60,
            tr.ev_ga60,
            tr.player_archetype,
            tr.ev_pts_conversion,
            tr.pp_goals_3yr_avg,
            tr.pp_points_3yr_avg,
            tr.sh_goals_3yr_avg,
            tr.sh_points_3yr_avg,
            
            -- Forward line assignments based on ranking (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 3 THEN '1L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 6 THEN '2L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 9 THEN '3L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 12 THEN '4L'
                WHEN tr.position_group = 'F' THEN 'Depth'
                ELSE NULL
            END as forward_line,
            
            -- Defense pair assignments based on ranking (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 2 THEN '1D'
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 4 THEN '2D'
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 6 THEN '3D'
                WHEN tr.position_group = 'D' THEN 'Depth'
                ELSE NULL
            END as defense_pair,
            
            -- Special teams assignments (FIXED to include defensemen)
            CASE 
                -- Forwards PP assignments
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 2.0 AND tr.pp_points_3yr_avg >= 20 THEN 'PP1'
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 1.5 AND tr.pp_points_3yr_avg >= 10 THEN 'PP2'
                -- Defensemen PP assignments (based on PP points, not EV points)
                WHEN tr.position_group = 'D' AND tr.pp_points_3yr_avg >= 30 THEN 'PP1'
                WHEN tr.position_group = 'D' AND tr.pp_points_3yr_avg >= 15 THEN 'PP2'
                -- PK assignments (both forwards and defensemen)
                WHEN tr.ev_ca60 <= 1.5 AND tr.sh_points_3yr_avg >= 2 THEN 'PK1'
                WHEN tr.ev_ca60 <= 2.0 AND tr.sh_points_3yr_avg >= 1 THEN 'PK2'
                ELSE 'None'
            END as special_teams_role,
            
            -- Overall role assignment (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 3 THEN '1L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 6 THEN '2L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 9 THEN '3L'
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 12 THEN '4L'
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 2 THEN '1D'
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 4 THEN '2D'
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 6 THEN '3D'
                ELSE 'Depth'
            END as primary_role,
            
            -- REALISTIC TOI per player (based on historical data with slight adjustments)
            CASE 
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 3 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 18.0)  -- 1st line forwards (min 18 min)
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 6 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 16.0)  -- 2nd line forwards (min 16 min)
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 9 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 14.0)  -- 3rd line forwards (min 14 min)
                WHEN tr.position_group = 'F' AND tr.team_position_rank <= 12 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 12.0)  -- 4th line forwards (min 12 min)
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 2 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 22.0)  -- 1st pair defense (min 22 min)
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 4 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 20.0)  -- 2nd pair defense (min 20 min)
                WHEN tr.position_group = 'D' AND tr.team_position_rank <= 6 THEN 
                    GREATEST(tr.ev_toi_avg_minutes, 18.0)  -- 3rd pair defense (min 18 min)
                ELSE 
                    LEAST(tr.ev_toi_avg_minutes, 12.0)  -- Depth players (max 12 min)
            END as forecast_toi_minutes,
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v2.3 (Defensemen PP Fixed)' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("✓ Created corrected line assignments with defensemen special teams")
    
    # 2. Re-run the role-based TOI allocation with the corrected assignments
    print("2. Re-running role-based TOI allocation...")
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
            'Foster Model v2.3 (Defensemen PP Fixed)' as model_version
            
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
    print("✓ Re-ran role-based TOI allocation")
    
    # 3. Create final view with corrected projections
    print("3. Creating final view with corrected projections...")
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
    print("✓ Created final view with corrected projections")
    
    # Run QA
    print("\nRunning QA on corrected model...")
    
    # Check key players with corrected special teams assignments
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
    
    print("Corrected projections (key players):")
    for row in qa_results:
        print(f"  {row.player_name} ({row.primary_role}, {row.special_teams_role}):")
        print(f"    Total: {row.total_projected_points} pts")
        print(f"    5v5: {row.ev_projected_points} pts ({row.ev_points_pct}%) - {row.ev_toi_minutes} min")
        print(f"    PP: {row.pp_projected_points} pts ({row.pp_points_pct}%) - {row.pp_toi_minutes} min")
        print(f"    PK: {row.pk_projected_points} pts ({row.pk_points_pct}%) - {row.pk_toi_minutes} min")
        print()

if __name__ == "__main__":
    fix_special_teams_for_defensemen()
