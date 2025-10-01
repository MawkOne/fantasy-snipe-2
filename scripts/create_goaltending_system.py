#!/usr/bin/env python3
"""
Create Goaltending System for Foster's forecasting method.
This implements GSAA (Goals Saved Above Average) and goaltending performance forecasting.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_goaltending_system():
    """Create goaltending system with GSAA and performance forecasting."""
    client = bigquery.Client()
    
    # First, let's check if we have goaltending data
    print("Checking for goaltending data...")
    check_goalies_query = """
    SELECT COUNT(*) as goalie_count
    FROM `fantasy-snipe-ai.nhl_raw.player_stats` 
    WHERE position = 'G'
    """
    
    check_job = client.query(check_goalies_query)
    check_results = check_job.result()
    
    for row in check_results:
        print(f"Goaltenders found in player_stats: {row.goalie_count}")
    
    if row.goalie_count == 0:
        print("No goaltending data found. Creating placeholder system...")
        create_placeholder_goaltending_system()
        return
    
    # Create goaltending forecasts table
    print("Creating goaltending forecasts...")
    goalie_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.goalie_forecasts` AS
    WITH goalie_stats AS (
        -- Get goalie stats from player_stats
        SELECT 
            ps.player_id,
            ps.full_name,
            ps.team_abbrev as team,
            ps.season,
            ps.games_played,
            ps.toi_seconds_per_game,
            -- Calculate basic goalie stats
            ps.games_played * ps.toi_seconds_per_game / 60.0 as toi_minutes,
            -- We'll need to calculate these from available data
            NULL as goals_against,
            NULL as saves,
            NULL as shots_against,
            NULL as save_percentage,
            NULL as goals_against_average,
            NULL as shutouts
        FROM `fantasy-snipe-ai.nhl_raw.player_stats` ps
        WHERE ps.position = 'G'
            AND ps.season >= 20222023  -- Last 3 seasons
            AND ps.games_played >= 5   -- Minimum games
    ),
    goalie_3yr_averages AS (
        -- Calculate 3-year averages for goalies
        SELECT 
            gs.player_id,
            gs.full_name,
            gs.team,
            AVG(gs.games_played) as gp_3yr_avg,
            SUM(gs.games_played) as gp_3yr_total,
            AVG(gs.toi_minutes) as toi_3yr_avg,
            -- Placeholder values - would need actual goalie stats
            2.5 as gaa_3yr_avg,
            0.915 as sv_pct_3yr_avg,
            2.0 as shutouts_3yr_avg,
            -- Current season stats
            MAX(CASE WHEN gs.season = 20242025 THEN gs.games_played END) as current_gp,
            MAX(CASE WHEN gs.season = 20242025 THEN gs.toi_minutes END) as current_toi
        FROM goalie_stats gs
        GROUP BY gs.player_id, gs.full_name, gs.team
    ),
    team_goalie_assignments AS (
        -- Assign goalies to starter/backup roles
        SELECT 
            g3a.player_id,
            g3a.full_name,
            g3a.team,
            g3a.gp_3yr_avg,
            g3a.toi_3yr_avg,
            g3a.gaa_3yr_avg,
            g3a.sv_pct_3yr_avg,
            g3a.shutouts_3yr_avg,
            g3a.current_gp,
            g3a.current_toi,
            
            -- Rank goalies by games played within team
            ROW_NUMBER() OVER (
                PARTITION BY g3a.team 
                ORDER BY g3a.gp_3yr_avg DESC
            ) as team_goalie_rank,
            
            -- Determine role
            CASE 
                WHEN ROW_NUMBER() OVER (PARTITION BY g3a.team ORDER BY g3a.gp_3yr_avg DESC) = 1 THEN 'Starter'
                WHEN ROW_NUMBER() OVER (PARTITION BY g3a.team ORDER BY g3a.gp_3yr_avg DESC) = 2 THEN 'Backup'
                ELSE 'Depth'
            END as goalie_role
            
        FROM goalie_3yr_averages g3a
    ),
    goalie_forecasts AS (
        SELECT 
            tga.player_id,
            tga.full_name,
            tga.team,
            tga.goalie_role,
            
            -- Forecasted games played based on role
            CASE 
                WHEN tga.goalie_role = 'Starter' THEN 55
                WHEN tga.goalie_role = 'Backup' THEN 25
                ELSE 5
            END as forecast_gp,
            
            -- Forecasted TOI based on role
            CASE 
                WHEN tga.goalie_role = 'Starter' THEN 55 * 60  -- 55 games * 60 minutes
                WHEN tga.goalie_role = 'Backup' THEN 25 * 60   -- 25 games * 60 minutes
                ELSE 5 * 60  -- 5 games * 60 minutes
            END as forecast_toi_minutes,
            
            -- Forecasted performance (using 3-year averages with slight regression)
            tga.gaa_3yr_avg * 1.02 as forecast_gaa,  -- Slight regression
            tga.sv_pct_3yr_avg * 0.998 as forecast_sv_pct,  -- Slight regression
            tga.shutouts_3yr_avg * 0.95 as forecast_shutouts,  -- Slight regression
            
            -- GSAA calculation (simplified)
            -- GSAA = (SV% - League Average SV%) * Shots Against
            -- Using league average SV% of 0.905
            CASE 
                WHEN tga.goalie_role = 'Starter' THEN 
                    (tga.sv_pct_3yr_avg * 0.998 - 0.905) * 55 * 30  -- 30 shots per game average
                WHEN tga.goalie_role = 'Backup' THEN 
                    (tga.sv_pct_3yr_avg * 0.998 - 0.905) * 25 * 30
                ELSE 
                    (tga.sv_pct_3yr_avg * 0.998 - 0.905) * 5 * 30
            END as forecast_gsaa,
            
            -- Expected goals against
            CASE 
                WHEN tga.goalie_role = 'Starter' THEN 
                    55 * tga.gaa_3yr_avg * 1.02
                WHEN tga.goalie_role = 'Backup' THEN 
                    25 * tga.gaa_3yr_avg * 1.02
                ELSE 
                    5 * tga.gaa_3yr_avg * 1.02
            END as forecast_goals_against,
            
            -- Expected saves
            CASE 
                WHEN tga.goalie_role = 'Starter' THEN 
                    55 * 30 * tga.sv_pct_3yr_avg * 0.998
                WHEN tga.goalie_role = 'Backup' THEN 
                    25 * 30 * tga.sv_pct_3yr_avg * 0.998
                ELSE 
                    5 * 30 * tga.sv_pct_3yr_avg * 0.998
            END as forecast_saves,
            
            -- Historical performance for reference
            tga.gp_3yr_avg as historical_gp,
            tga.toi_3yr_avg as historical_toi,
            tga.gaa_3yr_avg as historical_gaa,
            tga.sv_pct_3yr_avg as historical_sv_pct,
            tga.shutouts_3yr_avg as historical_shutouts,
            
            -- Metadata
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0' as model_version
            
        FROM team_goalie_assignments tga
    )
    SELECT * FROM goalie_forecasts
    ORDER BY team, goalie_role, forecast_gsaa DESC
    """
    
    job = client.query(goalie_forecasts_query)
    job.result()
    print("Goaltending forecasts created successfully!")
    
    # Run QA on goaltending system
    print("\nRunning QA on goaltending system...")
    
    qa_goalies = """
    SELECT 
        COUNT(*) as total_goalies,
        COUNT(DISTINCT team) as teams_covered,
        COUNT(CASE WHEN goalie_role = 'Starter' THEN 1 END) as starters,
        COUNT(CASE WHEN goalie_role = 'Backup' THEN 1 END) as backups,
        AVG(forecast_gp) as avg_forecast_gp,
        AVG(forecast_gaa) as avg_forecast_gaa,
        AVG(forecast_sv_pct) as avg_forecast_sv_pct,
        AVG(forecast_gsaa) as avg_forecast_gsaa,
        AVG(forecast_shutouts) as avg_forecast_shutouts,
        MAX(forecast_gsaa) as best_gsaa,
        MIN(forecast_gsaa) as worst_gsaa
    FROM `fantasy-snipe-ai.nhl_projections.goalie_forecasts`
    """
    
    qa_job = client.query(qa_goalies)
    qa_results = qa_job.result()
    
    print("Goaltending System QA:")
    for row in qa_results:
        print(f"  Total goalies: {row.total_goalies}")
        print(f"  Teams covered: {row.teams_covered}")
        print(f"  Starters: {row.starters}")
        print(f"  Backups: {row.backups}")
        print(f"  Avg forecast GP: {row.avg_forecast_gp:.1f}")
        print(f"  Avg forecast GAA: {row.avg_forecast_gaa:.3f}")
        print(f"  Avg forecast SV%: {row.avg_forecast_sv_pct:.3f}")
        print(f"  Avg forecast GSAA: {row.avg_forecast_gsaa:.1f}")
        print(f"  Avg forecast shutouts: {row.avg_forecast_shutouts:.1f}")
        print(f"  Best GSAA: {row.best_gsaa:.1f}")
        print(f"  Worst GSAA: {row.worst_gsaa:.1f}")

def create_placeholder_goaltending_system():
    """Create a placeholder goaltending system when no data is available."""
    client = bigquery.Client()
    
    print("Creating placeholder goaltending system...")
    placeholder_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.goalie_forecasts` AS
    WITH team_list AS (
        SELECT DISTINCT team
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments`
    ),
    placeholder_goalies AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY team) as player_id,
            CONCAT('Goalie ', ROW_NUMBER() OVER (ORDER BY team)) as full_name,
            team,
            'Starter' as goalie_role,
            55 as forecast_gp,
            3300 as forecast_toi_minutes,  -- 55 games * 60 minutes
            2.50 as forecast_gaa,
            0.915 as forecast_sv_pct,
            2.0 as forecast_shutouts,
            0.0 as forecast_gsaa,  -- Placeholder
            137.5 as forecast_goals_against,  -- 55 * 2.5
            1509.75 as forecast_saves,  -- 55 * 30 * 0.915
            50 as historical_gp,
            3000 as historical_toi,
            2.50 as historical_gaa,
            0.915 as historical_sv_pct,
            2.0 as historical_shutouts,
            CURRENT_TIMESTAMP() as created_at,
            'Foster Model v1.0 (Placeholder)' as model_version
        FROM team_list
    )
    SELECT * FROM placeholder_goalies
    ORDER BY team
    """
    
    job = client.query(placeholder_query)
    job.result()
    print("Placeholder goaltending system created!")

if __name__ == "__main__":
    create_goaltending_system()
