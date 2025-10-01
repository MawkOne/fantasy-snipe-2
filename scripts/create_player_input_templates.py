#!/usr/bin/env python3
"""
Create Player Input Templates for Foster's forecasting method.
This creates the foundation data structure with player, position, team, age, 
3-year GP averages, EV TOI, archetypes, and EV stats.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_player_input_templates():
    """Create player input templates with all required fields."""
    client = bigquery.Client()
    
    # Create the player input templates table
    query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates` AS
    WITH player_3yr_stats AS (
        -- Get 3-year averages for each player
        SELECT 
            ps.player_id,
            ps.full_name,
            ps.position,
            ps.team_abbrev,
            ps.season,
            ps.games_played,
            ps.goals,
            ps.assists,
            ps.points,
            ps.toi_seconds_per_game,
            ps.goals_60,
            ps.assists_60,
            ps.points_60,
            ps.shots_60,
            ps.shooting_pct,
            ps.faceoff_win_pct,
            ps.pim,
            ps.plus_minus,
            ps.game_winning_goals,
            ps.ot_goals,
            ps.pp_goals,
            ps.pp_points,
            ps.sh_goals,
            ps.sh_points,
            -- Calculate age from season (approximate)
            EXTRACT(YEAR FROM CURRENT_DATE()) - CAST(SUBSTR(CAST(ps.season AS STRING), 1, 4) AS INT64) + 25 as age,
            -- Get current season for filtering
            EXTRACT(YEAR FROM CURRENT_DATE()) as current_year
        FROM `fantasy-snipe-ai.nhl_raw.player_stats` ps
        WHERE ps.season >= 20222023  -- Last 3 seasons
            AND ps.games_played >= 10  -- Minimum games played
    ),
    player_ev_stats AS (
        -- Get EV (5v5) stats from our processed data
        SELECT 
            psm.player_id,
            psm.season,
            psm.games_played as ev_games_played,
            psm.toi_seconds_total as ev_toi_seconds,
            psm.cf_total as ev_cf,
            psm.ca_total as ev_ca,
            psm.ff_total as ev_ff,
            psm.fa_total as ev_fa,
            psm.sf_total as ev_sf,
            psm.sa_total as ev_sa,
            psm.gf_total as ev_gf,
            psm.ga_total as ev_ga,
            psm.cf60 as ev_cf60,
            psm.ca60 as ev_ca60,
            psm.ff60 as ev_ff60,
            psm.fa60 as ev_fa60,
            psm.sf60 as ev_sf60,
            psm.sa60 as ev_sa60,
            psm.gf60 as ev_gf60,
            psm.ga60 as ev_ga60,
            psm.cf_pct_weighted as ev_cf_pct,
            psm.ff_pct_weighted as ev_ff_pct,
            psm.sf_pct_weighted as ev_sf_pct,
            psm.gf_pct_weighted as ev_gf_pct,
            psm.pdo_weighted as ev_pdo
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` psm
        WHERE psm.season >= 20222023  -- Last 3 seasons
            AND psm.games_played >= 10  -- Minimum games played
    ),
    player_3yr_averages AS (
        -- Calculate 3-year averages
        SELECT 
            p3s.player_id,
            p3s.full_name,
            p3s.position,
            p3s.team_abbrev,
            p3s.age,
            -- 3-year GP averages
            AVG(p3s.games_played) as gp_3yr_avg,
            SUM(p3s.games_played) as gp_3yr_total,
            -- 3-year individual stats
            AVG(p3s.goals) as goals_3yr_avg,
            AVG(p3s.assists) as assists_3yr_avg,
            AVG(p3s.points) as points_3yr_avg,
            AVG(p3s.toi_seconds_per_game) as toi_seconds_per_game_3yr_avg,
            AVG(p3s.goals_60) as goals_60_3yr_avg,
            AVG(p3s.assists_60) as assists_60_3yr_avg,
            AVG(p3s.points_60) as points_60_3yr_avg,
            AVG(p3s.shots_60) as shots_60_3yr_avg,
            AVG(p3s.shooting_pct) as shooting_pct_3yr_avg,
            AVG(p3s.faceoff_win_pct) as faceoff_win_pct_3yr_avg,
            AVG(p3s.pim) as pim_3yr_avg,
            AVG(p3s.plus_minus) as plus_minus_3yr_avg,
            AVG(p3s.game_winning_goals) as game_winning_goals_3yr_avg,
            AVG(p3s.ot_goals) as ot_goals_3yr_avg,
            AVG(p3s.pp_goals) as pp_goals_3yr_avg,
            AVG(p3s.pp_points) as pp_points_3yr_avg,
            AVG(p3s.sh_goals) as sh_goals_3yr_avg,
            AVG(p3s.sh_points) as sh_points_3yr_avg,
            -- Current season stats (most recent)
            MAX(CASE WHEN p3s.season = 20242025 THEN p3s.games_played END) as current_gp,
            MAX(CASE WHEN p3s.season = 20242025 THEN p3s.goals END) as current_goals,
            MAX(CASE WHEN p3s.season = 20242025 THEN p3s.assists END) as current_assists,
            MAX(CASE WHEN p3s.season = 20242025 THEN p3s.points END) as current_points,
            MAX(CASE WHEN p3s.season = 20242025 THEN p3s.toi_seconds_per_game END) as current_toi_per_game
        FROM player_3yr_stats p3s
        GROUP BY p3s.player_id, p3s.full_name, p3s.position, p3s.team_abbrev, p3s.age
    ),
    player_ev_3yr_averages AS (
        -- Calculate 3-year EV averages
        SELECT 
            pev.player_id,
            AVG(pev.ev_games_played) as ev_gp_3yr_avg,
            SUM(pev.ev_games_played) as ev_gp_3yr_total,
            AVG(pev.ev_toi_seconds) as ev_toi_seconds_3yr_avg,
            AVG(pev.ev_cf) as ev_cf_3yr_avg,
            AVG(pev.ev_ca) as ev_ca_3yr_avg,
            AVG(pev.ev_ff) as ev_ff_3yr_avg,
            AVG(pev.ev_fa) as ev_fa_3yr_avg,
            AVG(pev.ev_sf) as ev_sf_3yr_avg,
            AVG(pev.ev_sa) as ev_sa_3yr_avg,
            AVG(pev.ev_gf) as ev_gf_3yr_avg,
            AVG(pev.ev_ga) as ev_ga_3yr_avg,
            AVG(pev.ev_cf60) as ev_cf60_3yr_avg,
            AVG(pev.ev_ca60) as ev_ca60_3yr_avg,
            AVG(pev.ev_ff60) as ev_ff60_3yr_avg,
            AVG(pev.ev_fa60) as ev_fa60_3yr_avg,
            AVG(pev.ev_sf60) as ev_sf60_3yr_avg,
            AVG(pev.ev_sa60) as ev_sa60_3yr_avg,
            AVG(pev.ev_gf60) as ev_gf60_3yr_avg,
            AVG(pev.ev_ga60) as ev_ga60_3yr_avg,
            AVG(pev.ev_cf_pct) as ev_cf_pct_3yr_avg,
            AVG(pev.ev_ff_pct) as ev_ff_pct_3yr_avg,
            AVG(pev.ev_sf_pct) as ev_sf_pct_3yr_avg,
            AVG(pev.ev_gf_pct) as ev_gf_pct_3yr_avg,
            AVG(pev.ev_pdo) as ev_pdo_3yr_avg
        FROM player_ev_stats pev
        GROUP BY pev.player_id
    ),
    player_archetypes_latest AS (
        -- Get latest player archetypes
        SELECT 
            pa.player_id,
            pa.primary_archetype,
            pa.secondary_archetype,
            'Unknown' as line_role,  -- Not available in current schema
            'Unknown' as style,      -- Not available in current schema
            'Unknown' as position_group  -- Not available in current schema
        FROM `fantasy-snipe-ai.nhl_projections.player_archetypes` pa
        WHERE pa.season = 20242025  -- Most recent season
    )
    SELECT 
        p3a.player_id,
        p3a.full_name as player_name,
        p3a.position,
        CASE 
            WHEN p3a.position IN ('C', 'L', 'R') THEN 'F'
            WHEN p3a.position = 'D' THEN 'D'
            ELSE 'Unknown'
        END as position_group,
        p3a.team_abbrev as team,
        p3a.age,
        
        -- 3-year GP averages (Foster's requirement)
        ROUND(p3a.gp_3yr_avg, 1) as gp_3yr_avg,
        p3a.gp_3yr_total,
        
        -- EV TOI average (Foster's requirement)
        ROUND(p3a.toi_seconds_per_game_3yr_avg / 60.0, 2) as ev_toi_avg_minutes,
        
        -- Player Archetype (Foster's requirement)
        COALESCE(pa.primary_archetype, 'Unknown') as player_archetype,
        COALESCE(pa.secondary_archetype, 'Unknown') as player_archetype_2,
        COALESCE(pa.line_role, 'Unknown') as line_role,
        COALESCE(pa.style, 'Unknown') as style,
        
        -- EV stats (Foster's requirement: eCF/60, eCA/60, epts conversion, GF/60, GA/60)
        ROUND(pev.ev_cf60_3yr_avg, 2) as ev_cf60,
        ROUND(pev.ev_ca60_3yr_avg, 2) as ev_ca60,
        ROUND(pev.ev_ff60_3yr_avg, 2) as ev_ff60,
        ROUND(pev.ev_fa60_3yr_avg, 2) as ev_fa60,
        ROUND(pev.ev_sf60_3yr_avg, 2) as ev_sf60,
        ROUND(pev.ev_sa60_3yr_avg, 2) as ev_sa60,
        ROUND(pev.ev_gf60_3yr_avg, 2) as ev_gf60,
        ROUND(pev.ev_ga60_3yr_avg, 2) as ev_ga60,
        
        -- Points conversion (Foster's requirement)
        ROUND(p3a.points_60_3yr_avg / NULLIF(pev.ev_cf60_3yr_avg, 0), 4) as ev_pts_conversion,
        
        -- Additional useful stats
        ROUND(p3a.goals_60_3yr_avg, 2) as ev_goals_60,
        ROUND(p3a.assists_60_3yr_avg, 2) as ev_assists_60,
        ROUND(p3a.points_60_3yr_avg, 2) as ev_points_60,
        ROUND(p3a.shots_60_3yr_avg, 2) as ev_shots_60,
        ROUND(p3a.shooting_pct_3yr_avg, 3) as shooting_pct,
        ROUND(p3a.faceoff_win_pct_3yr_avg, 3) as faceoff_win_pct,
        ROUND(p3a.pim_3yr_avg, 1) as pim_avg,
        ROUND(p3a.plus_minus_3yr_avg, 1) as plus_minus_avg,
        
        -- Current season stats for reference
        p3a.current_gp,
        p3a.current_goals,
        p3a.current_assists,
        p3a.current_points,
        ROUND(p3a.current_toi_per_game / 60.0, 2) as current_toi_per_game_minutes,
        
        -- EV percentages
        ROUND(pev.ev_cf_pct_3yr_avg, 2) as ev_cf_pct,
        ROUND(pev.ev_ff_pct_3yr_avg, 2) as ev_ff_pct,
        ROUND(pev.ev_sf_pct_3yr_avg, 2) as ev_sf_pct,
        ROUND(pev.ev_gf_pct_3yr_avg, 2) as ev_gf_pct,
        ROUND(pev.ev_pdo_3yr_avg, 3) as ev_pdo,
        
        -- Special teams stats
        ROUND(p3a.pp_goals_3yr_avg, 1) as pp_goals_avg,
        ROUND(p3a.pp_points_3yr_avg, 1) as pp_points_avg,
        ROUND(p3a.sh_goals_3yr_avg, 1) as sh_goals_avg,
        ROUND(p3a.sh_points_3yr_avg, 1) as sh_points_avg,
        
        -- Metadata
        CURRENT_TIMESTAMP() as created_at,
        'Foster Model v1.0' as model_version
        
    FROM player_3yr_averages p3a
    LEFT JOIN player_ev_3yr_averages pev ON p3a.player_id = pev.player_id
    LEFT JOIN player_archetypes_latest pa ON p3a.player_id = pa.player_id
    WHERE p3a.gp_3yr_avg >= 20  -- Minimum 20 games per season average
    ORDER BY p3a.points_60_3yr_avg DESC
    """
    
    print("Creating player input templates...")
    job = client.query(query)
    job.result()  # Wait for completion
    
    print("Player input templates created successfully!")
    
    # Run QA
    qa_query = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(CASE WHEN age >= 26 THEN 1 END) as players_26_plus,
        COUNT(CASE WHEN player_archetype != 'Unknown' THEN 1 END) as players_with_archetype,
        COUNT(CASE WHEN ev_cf60 > 0 THEN 1 END) as players_with_ev_stats,
        AVG(gp_3yr_avg) as avg_gp_3yr,
        AVG(ev_toi_avg_minutes) as avg_ev_toi,
        AVG(ev_points_60) as avg_ev_points_60,
        MIN(age) as min_age,
        MAX(age) as max_age
    FROM `fantasy-snipe-ai.nhl_projections.player_input_templates`
    """
    
    print("\nRunning QA on player input templates...")
    qa_job = client.query(qa_query)
    qa_results = qa_job.result()
    
    for row in qa_results:
        print(f"Total players: {row.total_players}")
        print(f"Players 26+: {row.players_26_plus}")
        print(f"Players with archetype: {row.players_with_archetype}")
        print(f"Players with EV stats: {row.players_with_ev_stats}")
        print(f"Avg 3-year GP: {row.avg_gp_3yr:.1f}")
        print(f"Avg EV TOI: {row.avg_ev_toi:.1f} minutes")
        print(f"Avg EV Points/60: {row.avg_ev_points_60:.2f}")
        print(f"Age range: {row.min_age} - {row.max_age}")

if __name__ == "__main__":
    create_player_input_templates()
