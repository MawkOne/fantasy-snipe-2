#!/usr/bin/env python3
"""
Fix duplicates and correct PP/SH rates calculation.
The issue is that PP/SH points per 60 should be based on actual PP/SH TOI, not total TOI.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_duplicates_and_pp_rates():
    """Fix duplicates and correct PP/SH rates calculation."""
    client = bigquery.Client()
    
    print("Fixing duplicates and correcting PP/SH rates...")
    
    # 1. First, create a deduplicated version of the complete templates
    print("1. Creating deduplicated player input templates...")
    dedupe_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated_final` AS
    WITH ranked_players AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, team 
                ORDER BY gp_3yr_avg DESC, ev_points_60 DESC, ev_toi_avg_minutes DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_complete`
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
        pp_goals_3yr_avg,
        pp_points_3yr_avg,
        sh_goals_3yr_avg,
        sh_points_3yr_avg,
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
        created_at,
        model_version
    FROM ranked_players
    WHERE rn = 1
    ORDER BY team, position_group, ev_points_60 DESC
    """
    
    job = client.query(dedupe_query)
    job.result()
    print("✓ Created deduplicated player input templates")
    
    # 2. Create corrected line assignments (one per player)
    print("2. Creating corrected line assignments...")
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
            
            -- Special teams assignments (enhanced)
            CASE 
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 2.0 AND tr.pp_points_3yr_avg >= 20 THEN 'PP1'
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 1.5 AND tr.pp_points_3yr_avg >= 10 THEN 'PP2'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 1.5 AND tr.sh_points_3yr_avg >= 2 THEN 'PK1'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 2.0 AND tr.sh_points_3yr_avg >= 1 THEN 'PK2'
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
            'Foster Model v2.2 (Final)' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("✓ Created corrected line assignments (one per player)")
    
    # 3. Create corrected player forecasts with proper PP/SH rates
    print("3. Creating corrected player forecasts with proper PP/SH rates...")
    player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_final` AS
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
            
            -- Calculate actual TOI per situation based on team distribution
            la.forecast_toi_minutes * COALESCE(ev_dist.pct_of_total_toi, 77.1) / 100.0 as ev_toi_minutes,
            la.forecast_toi_minutes * COALESCE(pp1_dist.pct_of_total_toi, 0) / 100.0 as pp1_toi_minutes,
            la.forecast_toi_minutes * COALESCE(pp2_dist.pct_of_total_toi, 0) / 100.0 as pp2_toi_minutes,
            la.forecast_toi_minutes * COALESCE(pk_dist.pct_of_total_toi, 10.1) / 100.0 as pk_toi_minutes,
            
            -- 5v5 (Even Strength) projections
            la.ev_pts_conversion * 60.0 as ev_points_60,
            
            -- Power Play projections (5v4) - CORRECTED calculation
            -- Use realistic PP TOI estimates: ~3-4 minutes per game for PP1, ~1-2 minutes for PP2
            CASE 
                WHEN la.pp_points_3yr_avg > 0 AND la.special_teams_role = 'PP1' THEN
                    (la.pp_points_3yr_avg / 82.0) / 3.5 * 60.0  -- 3.5 min PP TOI per game
                WHEN la.pp_points_3yr_avg > 0 AND la.special_teams_role = 'PP2' THEN
                    (la.pp_points_3yr_avg / 82.0) / 1.5 * 60.0  -- 1.5 min PP TOI per game
                WHEN la.pp_points_3yr_avg > 0 THEN
                    (la.pp_points_3yr_avg / 82.0) / 2.0 * 60.0  -- 2.0 min PP TOI per game (average)
                ELSE 0
            END as pp_points_60,
            
            -- Penalty Kill projections (4v5) - CORRECTED calculation
            -- Use realistic PK TOI estimates: ~2-3 minutes per game
            CASE 
                WHEN la.sh_points_3yr_avg > 0 THEN
                    (la.sh_points_3yr_avg / 82.0) / 2.5 * 60.0  -- 2.5 min PK TOI per game
                ELSE 0
            END as sh_points_60,
            
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
            'Foster Model v2.2 (Final)' as model_version
            
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
    
    job = client.query(player_forecasts_query)
    job.result()
    print("✓ Created corrected player forecasts with proper PP/SH rates")
    
    # 4. Create final corrected view
    print("4. Creating final corrected view...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_final` AS
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
        
        -- Power Play projections (PP1 + PP2)
        ROUND(pf.pp_points_60, 2) as pp_points_60,
        ROUND(pf.pp1_toi_minutes + pf.pp2_toi_minutes, 1) as pp_toi_minutes,
        ROUND(pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82, 1) as pp_projected_points,
        ROUND(pf.pp_goals_share * pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82, 1) as pp_projected_goals,
        ROUND(pf.pp_assists_share * pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82, 1) as pp_projected_assists,
        
        -- Penalty Kill projections
        ROUND(pf.sh_points_60, 2) as sh_points_60,
        ROUND(pf.pk_toi_minutes, 1) as pk_toi_minutes,
        ROUND(pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_points,
        ROUND(pf.sh_goals_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_goals,
        ROUND(pf.sh_assists_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as pk_projected_assists,
        
        -- Total projections
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
              pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_points,
        ROUND(pf.ev_goals_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_goals_share * pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
              pf.sh_goals_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_goals,
        ROUND(pf.ev_assists_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_assists_share * pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
              pf.sh_assists_share * pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 1) as total_projected_assists,
        
        -- Situation breakdown percentages
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as ev_points_pct,
        ROUND(pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as pp_points_pct,
        ROUND(pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * (pf.pp1_toi_minutes + pf.pp2_toi_minutes) / 60.0 * 82 + 
                     pf.sh_points_60 * pf.pk_toi_minutes / 60.0 * 82, 0) * 100, 1) as pk_points_pct,
        
        -- TOI distribution percentages
        ROUND(pf.ev_toi_pct, 1) as ev_toi_pct,
        ROUND(pf.pp1_toi_pct + pf.pp2_toi_pct, 1) as pp_toi_pct,
        ROUND(pf.pk_toi_pct, 1) as pk_toi_pct,
        
        pf.created_at,
        pf.model_version
        
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_final` pf
    ORDER BY total_projected_points DESC
    """
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final corrected view")
    
    # Run comprehensive QA
    print("\nRunning comprehensive QA on final corrected model...")
    
    # Check for duplicates
    qa_duplicates = """
    SELECT 
        player_name, 
        team, 
        COUNT(*) as entry_count
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_final`
    GROUP BY player_name, team
    HAVING COUNT(*) > 1
    LIMIT 5
    """
    
    qa_job = client.query(qa_duplicates)
    qa_results = qa_job.result()
    
    print("Duplicate entries check:")
    if qa_results.total_rows == 0:
        print("✓ No duplicate entries found")
    else:
        print("❌ Found duplicate entries:")
        for row in qa_results:
            print(f"  {row.player_name} ({row.team}): {row.entry_count} entries")
    
    # Check top projections with corrected percentages
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
        pp_points_60,
        sh_points_60
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_final`
    WHERE team = 'EDM'
    ORDER BY total_projected_points DESC
    LIMIT 5
    """
    
    qa_job2 = client.query(qa_projections)
    qa_results2 = qa_job2.result()
    
    print("\nTop projections with corrected percentages (Edmonton):")
    for row in qa_results2:
        print(f"  {row.player_name} ({row.primary_role}, {row.special_teams_role}):")
        print(f"    Total: {row.total_projected_points} pts")
        print(f"    5v5: {row.ev_projected_points} pts ({row.ev_points_pct}%)")
        print(f"    PP: {row.pp_projected_points} pts ({row.pp_points_pct}%) - {row.pp_points_60} P/60")
        print(f"    PK: {row.pk_projected_points} pts ({row.pk_points_pct}%) - {row.sh_points_60} P/60")
        print()

if __name__ == "__main__":
    fix_duplicates_and_pp_rates()
