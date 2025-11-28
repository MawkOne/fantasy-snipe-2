#!/usr/bin/env python3
"""
Create a corrected Foster model using actual 3-year TOI distribution data:
- Apply team-specific TOI distribution (77.1% EV, 12.8% PP, 10.1% PK)
- Account for PP1 vs PP2 splits
- Use realistic TOI allocation per player
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_corrected_foster_model():
    """Create a corrected Foster model using actual TOI distribution data."""
    client = bigquery.Client()
    
    print("Creating corrected Foster model with actual TOI distribution...")
    
    # 1. Create team-specific TOI distribution table
    print("1. Creating team-specific TOI distribution table...")
    toi_distribution_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.team_toi_distribution` AS
    WITH team_toi AS (
        SELECT 
            t.tri_code as team,
            psm.strength_state,
            SUM(CAST(REGEXP_REPLACE(psm.duration, ":", "") AS INT64)) as total_seconds
        FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON psm.team_id = t.id
        WHERE g.season >= 20222023 
            AND psm.strength_state IS NOT NULL
        GROUP BY t.tri_code, psm.strength_state
    ),
    team_totals AS (
        SELECT 
            team, 
            SUM(total_seconds) as team_total_seconds
        FROM team_toi 
        GROUP BY team
    ),
    team_distribution AS (
        SELECT 
            tt.team,
            tt.strength_state,
            ROUND(tt.total_seconds / 60.0, 1) as total_minutes,
            ROUND(tt.total_seconds / ttt.team_total_seconds * 100, 1) as pct_of_total_toi
        FROM team_toi tt
        JOIN team_totals ttt ON tt.team = ttt.team
    ),
    -- Add PP1 vs PP2 splits (estimated based on typical NHL patterns)
    pp_splits AS (
        SELECT 
            team,
            'PP1' as pp_unit,
            ROUND(pct_of_total_toi * 0.7, 1) as pct_of_total_toi  -- PP1 gets 70% of PP time
        FROM team_distribution 
        WHERE strength_state = 'PP'
        
        UNION ALL
        
        SELECT 
            team,
            'PP2' as pp_unit,
            ROUND(pct_of_total_toi * 0.3, 1) as pct_of_total_toi  -- PP2 gets 30% of PP time
        FROM team_distribution 
        WHERE strength_state = 'PP'
    ),
    final_distribution AS (
        SELECT team, strength_state as situation, pct_of_total_toi
        FROM team_distribution
        WHERE strength_state != 'PP'
        
        UNION ALL
        
        SELECT team, pp_unit as situation, pct_of_total_toi
        FROM pp_splits
    )
    SELECT * FROM final_distribution
    ORDER BY team, situation
    """
    
    job = client.query(toi_distribution_query)
    job.result()
    print("✓ Created team-specific TOI distribution table")
    
    # 2. Create corrected player forecasts with realistic TOI allocation
    print("2. Creating corrected player forecasts...")
    player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_corrected` AS
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
            
            -- Power Play projections (5v4) - use historical PP production
            CASE 
                WHEN la.pp_points_3yr_avg > 0 THEN
                    (la.pp_points_3yr_avg / 82.0) * 60.0  -- Convert season total to per-60
                ELSE 0
            END as pp_points_60,
            
            -- Penalty Kill projections (4v5) - minimal offensive contribution
            CASE 
                WHEN la.sh_points_3yr_avg > 0 THEN
                    (la.sh_points_3yr_avg / 82.0) * 60.0  -- Convert season total to per-60
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
            'Foster Model v2.1 (Corrected)' as model_version
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_complete` la
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
    print("✓ Created corrected player forecasts with realistic TOI allocation")
    
    # 3. Create final corrected view with situation breakdown
    print("3. Creating final corrected view...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_corrected` AS
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
        
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_corrected` pf
    ORDER BY total_projected_points DESC
    """
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final corrected view with realistic situation breakdown")
    
    # Run comprehensive QA
    print("\nRunning comprehensive QA on corrected model...")
    
    # Check team TOI distribution
    qa_toi_dist = """
    SELECT 
        team,
        situation,
        pct_of_total_toi
    FROM `fantasy-snipe-ai.nhl_projections.team_toi_distribution`
    WHERE team = 'EDM'
    ORDER BY situation
    """
    
    qa_job = client.query(qa_toi_dist)
    qa_results = qa_job.result()
    
    print("Edmonton TOI Distribution:")
    for row in qa_results:
        print(f"  {row.situation}: {row.pct_of_total_toi}%")
    
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
        ev_toi_pct,
        pp_toi_pct,
        pk_toi_pct
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_corrected`
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
        print(f"    5v5: {row.ev_projected_points} pts ({row.ev_points_pct}%) - {row.ev_toi_pct}% TOI")
        print(f"    PP: {row.pp_projected_points} pts ({row.pp_points_pct}%) - {row.pp_toi_pct}% TOI")
        print(f"    PK: {row.pk_projected_points} pts ({row.pk_points_pct}%) - {row.pk_toi_pct}% TOI")
        print()

if __name__ == "__main__":
    create_corrected_foster_model()
