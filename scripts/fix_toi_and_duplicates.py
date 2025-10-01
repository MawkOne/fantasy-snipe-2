#!/usr/bin/env python3
"""
Fix TOI assignments and duplicate player entries in the Foster model.
- Use realistic TOI per player (not per line)
- Ensure each player appears only once
- Use proper line assignment logic
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_toi_and_duplicates():
    """Fix TOI assignments and duplicate player entries."""
    client = bigquery.Client()
    
    print("Fixing TOI assignments and duplicate player entries...")
    
    # 1. Create corrected line assignments (one per player)
    print("1. Creating corrected line assignments (one per player)...")
    line_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_fixed` AS
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
            -- Rank players by performance within their team and position
            ROW_NUMBER() OVER (
                PARTITION BY pit.team, pit.position_group 
                ORDER BY pit.ev_points_60 DESC, pit.ev_toi_avg_minutes DESC
            ) as team_position_rank,
            -- Rank forwards by TOI for line assignment
            CASE 
                WHEN pit.position_group = 'F' THEN
                    ROW_NUMBER() OVER (
                        PARTITION BY pit.team, pit.position_group
                        ORDER BY pit.ev_toi_avg_minutes DESC
                    )
                ELSE NULL
            END as forward_toi_rank,
            -- Rank defensemen by TOI for pair assignment
            CASE 
                WHEN pit.position_group = 'D' THEN
                    ROW_NUMBER() OVER (
                        PARTITION BY pit.team, pit.position_group
                        ORDER BY pit.ev_toi_avg_minutes DESC
                    )
                ELSE NULL
            END as defense_toi_rank
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_final` pit
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
            
            -- Forward line assignments based on TOI ranking (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 3 THEN '1L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 6 THEN '2L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 9 THEN '3L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 12 THEN '4L'
                WHEN tr.position_group = 'F' THEN 'Depth'
                ELSE NULL
            END as forward_line,
            
            -- Defense pair assignments based on TOI ranking (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 2 THEN '1D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 4 THEN '2D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 6 THEN '3D'
                WHEN tr.position_group = 'D' THEN 'Depth'
                ELSE NULL
            END as defense_pair,
            
            -- Special teams assignments
            CASE 
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 2.0 THEN 'PP1'
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 1.5 THEN 'PP2'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 1.5 THEN 'PK1'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 2.0 THEN 'PK2'
                ELSE 'None'
            END as special_teams_role,
            
            -- Overall role assignment (ONE PER PLAYER)
            CASE 
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 3 THEN '1L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 6 THEN '2L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 9 THEN '3L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 12 THEN '4L'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 2 THEN '1D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 4 THEN '2D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 6 THEN '3D'
                ELSE 'Depth'
            END as primary_role,
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.4 (Fixed)' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("✓ Created corrected line assignments (one per player)")
    
    # 2. Create corrected line forecasts with realistic TOI
    print("2. Creating corrected line forecasts with realistic TOI...")
    line_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_forecasts_fixed` AS
    WITH team_lines AS (
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
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_fixed` la
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
            
            -- Line GF/CF conversion rate
            CASE 
                WHEN tl.line_cf60_avg > 0 THEN tl.line_gf60_avg / tl.line_cf60_avg
                ELSE 0
            END as line_gf_cf_conversion,
            
            -- Line GA/CA conversion rate
            CASE 
                WHEN tl.line_ca60_avg > 0 THEN tl.line_ga60_avg / tl.line_ca60_avg
                ELSE 0
            END as line_ga_ca_conversion,
            
            -- Line points conversion
            tl.line_pts_conversion_avg as line_pts_conversion,
            
            -- REALISTIC TOI per line (total team TOI allocation)
            CASE 
                WHEN tl.primary_role = '1L' THEN 18.0  -- 18 minutes total for 1st line
                WHEN tl.primary_role = '2L' THEN 16.0  -- 16 minutes total for 2nd line
                WHEN tl.primary_role = '3L' THEN 14.0  -- 14 minutes total for 3rd line
                WHEN tl.primary_role = '4L' THEN 12.0  -- 12 minutes total for 4th line
                WHEN tl.primary_role = '1D' THEN 25.0  -- 25 minutes total for 1st pair
                WHEN tl.primary_role = '2D' THEN 20.0  -- 20 minutes total for 2nd pair
                WHEN tl.primary_role = '3D' THEN 15.0  -- 15 minutes total for 3rd pair
                ELSE 10.0
            END as line_total_toi_minutes,
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.4 (Fixed)' as model_version
            
        FROM team_lines tl
    )
    SELECT * FROM line_forecasts
    ORDER BY team, line_role
    """
    
    job = client.query(line_forecasts_query)
    job.result()
    print("✓ Created corrected line forecasts with realistic TOI")
    
    # 3. Create corrected player forecasts with proper TOI allocation
    print("3. Creating corrected player forecasts with proper TOI allocation...")
    player_forecasts_query = """
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
            lf.line_total_toi_minutes as line_total_toi,
            lf.players_on_line,
            
            -- Calculate player's share of line TOI (realistic)
            CASE 
                WHEN lf.players_on_line > 0 THEN 
                    la.ev_toi_avg_minutes / (lf.line_total_toi_minutes / lf.players_on_line)
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
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_fixed` la
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
            
            -- Line-level forecasts
            plf.line_cf60,
            plf.line_ca60,
            plf.line_gf60,
            plf.line_ga60,
            plf.line_gf_cf_conversion,
            plf.line_ga_ca_conversion,
            plf.line_pts_conversion,
            
            -- Points allocation using Foster's formula (CORRECTED):
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
            
            -- REALISTIC TOI forecasts (per player, not per line)
            plf.ev_toi_avg_minutes as forecast_toi_minutes,
            plf.toi_share_of_line,
            plf.line_total_toi,
            
            -- Contribution metrics
            plf.cf_contribution_share,
            plf.gf_contribution_share,
            
            -- Historical G/A split
            CASE 
                WHEN plf.ev_pts_conversion > 0 THEN
                    plf.ev_gf60 / (plf.ev_gf60 + plf.ev_ca60 * 0.7)
                ELSE 0.4
            END as goals_share,
            
            CASE 
                WHEN plf.ev_pts_conversion > 0 THEN
                    (plf.ev_ca60 * 0.7) / (plf.ev_gf60 + plf.ev_ca60 * 0.7)
                ELSE 0.6
            END as assists_share,
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.4 (Fixed)' as model_version
            
        FROM player_line_forecasts plf
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, forecast_points_60_adjusted DESC
    """
    
    job = client.query(player_forecasts_query)
    job.result()
    print("✓ Created corrected player forecasts with proper TOI allocation")
    
    # 4. Create final corrected view
    print("4. Creating final corrected view...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_final_fixed` AS
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
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final corrected view")
    
    # Run QA
    print("\nRunning QA on fixed model...")
    
    # Check for duplicates
    qa_duplicates = """
    SELECT 
        player_name, 
        team, 
        COUNT(*) as entry_count,
        STRING_AGG(primary_role, ", ") as roles
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_fixed`
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
            print(f"  {row.player_name} ({row.team}): {row.entry_count} entries - {row.roles}")
    
    # Check TOI assignments
    qa_toi = """
    SELECT 
        line_role,
        line_total_toi_minutes,
        players_on_line,
        ROUND(line_total_toi_minutes / players_on_line, 1) as toi_per_player
    FROM `fantasy-snipe-ai.nhl_projections.line_forecasts_fixed`
    WHERE team = 'EDM'
    ORDER BY line_total_toi_minutes DESC
    """
    
    qa_job2 = client.query(qa_toi)
    qa_results2 = qa_job2.result()
    
    print("\nTOI assignments (Edmonton):")
    for row in qa_results2:
        print(f"  {row.line_role}: {row.line_total_toi_minutes} min total, {row.players_on_line} players, {row.toi_per_player} min/player")
    
    # Check top projections
    qa_projections = """
    SELECT 
        player_name,
        team,
        primary_role,
        ROUND(forecast_points_60, 2) as forecast_points_60,
        ROUND(projected_points, 1) as projected_points,
        ROUND(forecast_toi_minutes, 1) as forecast_toi_minutes
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_final_fixed`
    WHERE team = 'EDM'
    ORDER BY projected_points DESC
    LIMIT 5
    """
    
    qa_job3 = client.query(qa_projections)
    qa_results3 = qa_job3.result()
    
    print("\nTop projections (Edmonton):")
    for row in qa_results3:
        print(f"  {row.player_name} ({row.primary_role}): {row.forecast_points_60} P/60 → {row.projected_points} pts ({row.forecast_toi_minutes} min)")

if __name__ == "__main__":
    fix_toi_and_duplicates()
