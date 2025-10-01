#!/usr/bin/env python3
"""
Fix the Foster model using the deduplicated player input templates.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_foster_model_with_deduplicated():
    """Fix the Foster model using deduplicated player input templates."""
    client = bigquery.Client()
    
    print("Fixing Foster model with deduplicated player templates...")
    
    # 1. Create final line assignments using deduplicated data
    print("1. Creating final line assignments...")
    line_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_clean` AS
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
            -- Rank players by performance within their team and position (NO DUPLICATES)
            ROW_NUMBER() OVER (
                PARTITION BY pit.team, pit.position_group 
                ORDER BY pit.ev_points_60 DESC, pit.ev_toi_avg_minutes DESC
            ) as team_position_rank
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated` pit
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
            'Foster Model v1.7 (Clean)' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("✓ Created clean line assignments (one per player, realistic TOI)")
    
    # 2. Create clean line forecasts
    print("2. Creating clean line forecasts...")
    line_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_forecasts_clean` AS
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
            
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.7 (Clean)' as model_version
            
        FROM team_lines tl
    )
    SELECT * FROM line_forecasts
    ORDER BY team, line_role
    """
    
    job = client.query(line_forecasts_query)
    job.result()
    print("✓ Created clean line forecasts")
    
    # 3. Create clean player forecasts
    print("3. Creating clean player forecasts...")
    player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_clean` AS
    WITH player_line_forecasts AS (
        SELECT 
            la.player_id,
            la.player_name,
            la.position,
            la.team,
            la.primary_role,
            la.forecast_toi_minutes,
            la.ev_cf60,
            la.ev_ca60,
            la.ev_gf60,
            la.ev_ga60,
            la.ev_pts_conversion,
            la.special_teams_role,
            
            -- Get line forecasts
            lf.forecast_cf60 as line_cf60,
            lf.forecast_ca60 as line_ca60,
            lf.forecast_gf60 as line_gf60,
            lf.forecast_ga60 as line_ga60,
            lf.line_gf_cf_conversion,
            lf.line_ga_ca_conversion,
            lf.line_pts_conversion,
            lf.chemistry_multiplier,
            lf.players_on_line,
            
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
        LEFT JOIN `fantasy-snipe-ai.nhl_projections.line_forecasts_clean` lf 
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
            
            -- Points allocation using Foster's formula (SIMPLIFIED):
            -- Use individual player's points/60 directly (more realistic)
            plf.ev_pts_conversion * 60.0 as forecast_points_60,
            
            -- Apply chemistry multiplier
            plf.ev_pts_conversion * 60.0 * plf.chemistry_multiplier as forecast_points_60_adjusted,
            
            -- TOI forecasts (realistic per player)
            plf.forecast_toi_minutes,
            
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
            'Foster Model v1.7 (Clean)' as model_version
            
        FROM player_line_forecasts plf
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, forecast_points_60_adjusted DESC
    """
    
    job = client.query(player_forecasts_query)
    job.result()
    print("✓ Created clean player forecasts")
    
    # 4. Create final clean view
    print("4. Creating final clean view...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean` AS
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
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_clean` pf
    ORDER BY pf.forecast_points_60_adjusted DESC
    """
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final clean view")
    
    # Run comprehensive QA
    print("\nRunning comprehensive QA on clean model...")
    
    # Check for duplicates
    qa_duplicates = """
    SELECT 
        player_name, 
        team, 
        COUNT(*) as entry_count,
        STRING_AGG(primary_role, ", ") as roles
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_clean`
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
    
    # Check TOI distribution for Edmonton
    qa_toi = """
    SELECT 
        primary_role,
        COUNT(*) as player_count,
        ROUND(AVG(forecast_toi_minutes), 1) as avg_toi_per_player,
        ROUND(MIN(forecast_toi_minutes), 1) as min_toi,
        ROUND(MAX(forecast_toi_minutes), 1) as max_toi,
        ROUND(SUM(forecast_toi_minutes), 1) as total_toi
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_clean`
    WHERE team = 'EDM'
    GROUP BY primary_role
    ORDER BY avg_toi_per_player DESC
    """
    
    qa_job2 = client.query(qa_toi)
    qa_results2 = qa_job2.result()
    
    print("\nTOI distribution (Edmonton):")
    total_toi = 0
    for row in qa_results2:
        print(f"  {row.primary_role}: {row.player_count} players, {row.avg_toi_per_player} min avg ({row.min_toi}-{row.max_toi}), {row.total_toi} min total")
        total_toi += row.total_toi
    
    print(f"\nTotal TOI per game: {total_toi} minutes (should be ~60-65 minutes)")
    
    # Check top projections
    qa_projections = """
    SELECT 
        player_name,
        team,
        primary_role,
        ROUND(forecast_points_60, 2) as forecast_points_60,
        ROUND(projected_points, 1) as projected_points,
        ROUND(forecast_toi_minutes, 1) as forecast_toi_minutes
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_clean`
    WHERE team = 'EDM'
    ORDER BY projected_points DESC
    LIMIT 10
    """
    
    qa_job3 = client.query(qa_projections)
    qa_results3 = qa_job3.result()
    
    print("\nTop projections (Edmonton):")
    for row in qa_results3:
        print(f"  {row.player_name} ({row.primary_role}): {row.forecast_points_60} P/60 → {row.projected_points} pts ({row.forecast_toi_minutes} min)")

if __name__ == "__main__":
    fix_foster_model_with_deduplicated()
