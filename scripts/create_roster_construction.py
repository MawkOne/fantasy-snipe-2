#!/usr/bin/env python3
"""
Create Roster Construction System for Foster's forecasting method.
This creates line assignments (1L, 2L, 3L, 4L, 1D, 2D, 3D) and TOI profiles.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_roster_construction():
    """Create roster construction system with line assignments and TOI profiles."""
    client = bigquery.Client()
    
    # Create line assignments table
    print("Creating line assignments...")
    line_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments` AS
    WITH team_rosters AS (
        -- Get current team rosters from player input templates
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
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates` pit
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
            
            -- Forward line assignments based on TOI ranking
            CASE 
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 3 THEN '1L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 6 THEN '2L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 9 THEN '3L'
                WHEN tr.position_group = 'F' AND tr.forward_toi_rank <= 12 THEN '4L'
                WHEN tr.position_group = 'F' THEN 'Depth'
                ELSE NULL
            END as forward_line,
            
            -- Defense pair assignments based on TOI ranking
            CASE 
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 2 THEN '1D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 4 THEN '2D'
                WHEN tr.position_group = 'D' AND tr.defense_toi_rank <= 6 THEN '3D'
                WHEN tr.position_group = 'D' THEN 'Depth'
                ELSE NULL
            END as defense_pair,
            
            -- Special teams assignments (simplified based on performance)
            CASE 
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 2.0 THEN 'PP1'
                WHEN tr.position_group = 'F' AND tr.ev_points_60 >= 1.5 THEN 'PP2'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 1.5 THEN 'PK1'
                WHEN tr.position_group = 'F' AND tr.ev_ca60 <= 2.0 THEN 'PK2'
                ELSE 'None'
            END as special_teams_role,
            
            -- Overall role assignment
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
            
            -- Metadata
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("Line assignments created successfully!")
    
    # Create TOI profiles by role
    print("Creating TOI profiles by role...")
    toi_profiles_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.toi_profiles_by_role` AS
    WITH role_toi_stats AS (
        SELECT 
            la.primary_role,
            la.position_group,
            COUNT(*) as player_count,
            AVG(la.ev_toi_avg_minutes) as avg_toi_minutes,
            MIN(la.ev_toi_avg_minutes) as min_toi_minutes,
            MAX(la.ev_toi_avg_minutes) as max_toi_minutes,
            STDDEV(la.ev_toi_avg_minutes) as toi_stddev,
            AVG(la.ev_points_60) as avg_points_60,
            AVG(la.ev_cf60) as avg_cf60,
            AVG(la.ev_ca60) as avg_ca60,
            AVG(la.ev_gf60) as avg_gf60,
            AVG(la.ev_ga60) as avg_ga60,
            AVG(la.ev_pts_conversion) as avg_pts_conversion
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments` la
        WHERE la.primary_role != 'Depth'
        GROUP BY la.primary_role, la.position_group
    ),
    special_teams_toi AS (
        SELECT 
            la.special_teams_role,
            la.position_group,
            COUNT(*) as player_count,
            AVG(la.ev_toi_avg_minutes) as avg_toi_minutes,
            AVG(la.ev_points_60) as avg_points_60,
            AVG(la.ev_cf60) as avg_cf60,
            AVG(la.ev_ca60) as avg_ca60
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments` la
        WHERE la.special_teams_role != 'None'
        GROUP BY la.special_teams_role, la.position_group
    )
    SELECT 
        'EV' as strength_situation,
        rts.primary_role as role,
        rts.position_group,
        rts.player_count,
        ROUND(rts.avg_toi_minutes, 2) as avg_toi_minutes,
        ROUND(rts.min_toi_minutes, 2) as min_toi_minutes,
        ROUND(rts.max_toi_minutes, 2) as max_toi_minutes,
        ROUND(rts.toi_stddev, 2) as toi_stddev,
        ROUND(rts.avg_points_60, 2) as avg_points_60,
        ROUND(rts.avg_cf60, 2) as avg_cf60,
        ROUND(rts.avg_ca60, 2) as avg_ca60,
        ROUND(rts.avg_gf60, 2) as avg_gf60,
        ROUND(rts.avg_ga60, 2) as avg_ga60,
        ROUND(rts.avg_pts_conversion, 4) as avg_pts_conversion,
        CURRENT_TIMESTAMP() as created_at
    FROM role_toi_stats rts
    
    UNION ALL
    
    SELECT 
        'PP' as strength_situation,
        sts.special_teams_role as role,
        sts.position_group,
        sts.player_count,
        ROUND(sts.avg_toi_minutes, 2) as avg_toi_minutes,
        NULL as min_toi_minutes,
        NULL as max_toi_minutes,
        NULL as toi_stddev,
        ROUND(sts.avg_points_60, 2) as avg_points_60,
        ROUND(sts.avg_cf60, 2) as avg_cf60,
        ROUND(sts.avg_ca60, 2) as avg_ca60,
        NULL as avg_gf60,
        NULL as avg_ga60,
        NULL as avg_pts_conversion,
        CURRENT_TIMESTAMP() as created_at
    FROM special_teams_toi sts
    
    ORDER BY strength_situation, role, position_group
    """
    
    job = client.query(toi_profiles_query)
    job.result()
    print("TOI profiles created successfully!")
    
    # Run QA on both tables
    print("\nRunning QA on roster construction...")
    
    # QA for line assignments
    qa_line_assignments = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(CASE WHEN forward_line IS NOT NULL THEN 1 END) as forwards_assigned,
        COUNT(CASE WHEN defense_pair IS NOT NULL THEN 1 END) as defensemen_assigned,
        COUNT(CASE WHEN special_teams_role != 'None' THEN 1 END) as special_teams_assigned,
        COUNT(DISTINCT team) as teams_covered,
        COUNT(CASE WHEN primary_role = '1L' THEN 1 END) as first_line_players,
        COUNT(CASE WHEN primary_role = '2L' THEN 1 END) as second_line_players,
        COUNT(CASE WHEN primary_role = '3L' THEN 1 END) as third_line_players,
        COUNT(CASE WHEN primary_role = '4L' THEN 1 END) as fourth_line_players,
        COUNT(CASE WHEN primary_role = '1D' THEN 1 END) as first_pair_defensemen,
        COUNT(CASE WHEN primary_role = '2D' THEN 1 END) as second_pair_defensemen,
        COUNT(CASE WHEN primary_role = '3D' THEN 1 END) as third_pair_defensemen
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments`
    """
    
    qa_job = client.query(qa_line_assignments)
    qa_results = qa_job.result()
    
    print("Line Assignments QA:")
    for row in qa_results:
        print(f"  Total players: {row.total_players}")
        print(f"  Forwards assigned: {row.forwards_assigned}")
        print(f"  Defensemen assigned: {row.defensemen_assigned}")
        print(f"  Special teams assigned: {row.special_teams_assigned}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  1L players: {row.first_line_players}")
        print(f"  2L players: {row.second_line_players}")
        print(f"  3L players: {row.third_line_players}")
        print(f"  4L players: {row.fourth_line_players}")
        print(f"  1D players: {row.first_pair_defensemen}")
        print(f"  2D players: {row.second_pair_defensemen}")
        print(f"  3D players: {row.third_pair_defensemen}")
    
    # QA for TOI profiles
    qa_toi_profiles = """
    SELECT 
        COUNT(*) as total_profiles,
        COUNT(DISTINCT role) as unique_roles,
        COUNT(DISTINCT strength_situation) as strength_situations,
        AVG(avg_toi_minutes) as overall_avg_toi,
        MIN(avg_toi_minutes) as min_avg_toi,
        MAX(avg_toi_minutes) as max_avg_toi
    FROM `fantasy-snipe-ai.nhl_projections.toi_profiles_by_role`
    """
    
    qa_job2 = client.query(qa_toi_profiles)
    qa_results2 = qa_job2.result()
    
    print("\nTOI Profiles QA:")
    for row in qa_results2:
        print(f"  Total profiles: {row.total_profiles}")
        print(f"  Unique roles: {row.unique_roles}")
        print(f"  Strength situations: {row.strength_situations}")
        print(f"  Overall avg TOI: {row.overall_avg_toi:.2f} minutes")
        print(f"  Min avg TOI: {row.min_avg_toi:.2f} minutes")
        print(f"  Max avg TOI: {row.max_avg_toi:.2f} minutes")

if __name__ == "__main__":
    create_roster_construction()
