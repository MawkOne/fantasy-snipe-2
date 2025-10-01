#!/usr/bin/env python3
"""
Create a complete Foster model that includes all strength situations:
- 5v5 (Even Strength)
- 5v4 (Power Play) 
- 4v5 (Penalty Kill)
- Total points with situation breakdown
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_complete_foster_model():
    """Create a complete Foster model with all strength situations."""
    client = bigquery.Client()
    
    print("Creating complete Foster model with all strength situations...")
    
    # 1. Create enhanced player input templates with special teams data
    print("1. Creating enhanced player input templates...")
    enhanced_templates_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates_complete` AS
    WITH player_3yr_stats AS (
        -- Get 3-year averages for each player using CORRECTED individual stats
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
            ps.shots,
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
            -- Calculate CORRECT per-60 rates: (stat / TOI in minutes) * 60
            (ps.goals / (ps.toi_seconds_per_game * ps.games_played / 60.0)) * 60.0 as goals_60_corrected,
            (ps.assists / (ps.toi_seconds_per_game * ps.games_played / 60.0)) * 60.0 as assists_60_corrected,
            (ps.points / (ps.toi_seconds_per_game * ps.games_played / 60.0)) * 60.0 as points_60_corrected,
            (ps.shots / (ps.toi_seconds_per_game * ps.games_played / 60.0)) * 60.0 as shots_60_corrected,
            -- Calculate age from season (approximate)
            EXTRACT(YEAR FROM CURRENT_DATE()) - CAST(SUBSTR(CAST(ps.season AS STRING), 1, 4) AS INT64) + 25 as age
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
            -- 3-year individual stats (CORRECTED)
            AVG(p3s.goals) as goals_3yr_avg,
            AVG(p3s.assists) as assists_3yr_avg,
            AVG(p3s.points) as points_3yr_avg,
            AVG(p3s.toi_seconds_per_game) as toi_seconds_per_game_3yr_avg,
            -- Use CORRECTED per-60 rates
            AVG(p3s.goals_60_corrected) as goals_60_3yr_avg,
            AVG(p3s.assists_60_corrected) as assists_60_3yr_avg,
            AVG(p3s.points_60_corrected) as points_60_3yr_avg,
            AVG(p3s.shots_60_corrected) as shots_60_3yr_avg,
            AVG(p3s.shooting_pct) as shooting_pct_3yr_avg,
            AVG(p3s.faceoff_win_pct) as faceoff_win_pct_3yr_avg,
            AVG(p3s.pim) as pim_3yr_avg,
            AVG(p3s.plus_minus) as plus_minus_3yr_avg,
            AVG(p3s.game_winning_goals) as game_winning_goals_3yr_avg,
            AVG(p3s.ot_goals) as ot_goals_3yr_avg,
            -- Special teams stats (3-year averages)
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
            'Unknown' as line_role,
            'Unknown' as style,
            'Unknown' as position_group
        FROM `fantasy-snipe-ai.nhl_projections.player_archetypes` pa
        WHERE pa.season = 20242025
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
        
        -- 3-year GP averages
        ROUND(p3a.gp_3yr_avg, 1) as gp_3yr_avg,
        p3a.gp_3yr_total,
        
        -- EV TOI average
        ROUND(p3a.toi_seconds_per_game_3yr_avg / 60.0, 2) as ev_toi_avg_minutes,
        
        -- Player Archetype
        COALESCE(pa.primary_archetype, 'Unknown') as player_archetype,
        COALESCE(pa.secondary_archetype, 'Unknown') as player_archetype_2,
        COALESCE(pa.line_role, 'Unknown') as line_role,
        COALESCE(pa.style, 'Unknown') as style,
        
        -- EV stats (on-ice metrics)
        ROUND(pev.ev_cf60_3yr_avg, 2) as ev_cf60,
        ROUND(pev.ev_ca60_3yr_avg, 2) as ev_ca60,
        ROUND(pev.ev_ff60_3yr_avg, 2) as ev_ff60,
        ROUND(pev.ev_fa60_3yr_avg, 2) as ev_fa60,
        ROUND(pev.ev_sf60_3yr_avg, 2) as ev_sf60,
        ROUND(pev.ev_sa60_3yr_avg, 2) as ev_sa60,
        ROUND(pev.ev_gf60_3yr_avg, 2) as ev_gf60,
        ROUND(pev.ev_ga60_3yr_avg, 2) as ev_ga60,
        
        -- Points conversion (CORRECTED - using corrected points/60)
        ROUND(p3a.points_60_3yr_avg / NULLIF(pev.ev_cf60_3yr_avg, 0), 4) as ev_pts_conversion,
        
        -- Individual scoring stats (CORRECTED)
        ROUND(p3a.goals_60_3yr_avg, 2) as ev_goals_60,
        ROUND(p3a.assists_60_3yr_avg, 2) as ev_assists_60,
        ROUND(p3a.points_60_3yr_avg, 2) as ev_points_60,
        ROUND(p3a.shots_60_3yr_avg, 2) as ev_shots_60,
        ROUND(p3a.shooting_pct_3yr_avg, 3) as shooting_pct,
        ROUND(p3a.faceoff_win_pct_3yr_avg, 3) as faceoff_win_pct,
        ROUND(p3a.pim_3yr_avg, 1) as pim_avg,
        ROUND(p3a.plus_minus_3yr_avg, 1) as plus_minus_avg,
        
        -- Special teams stats (3-year averages)
        ROUND(p3a.pp_goals_3yr_avg, 1) as pp_goals_3yr_avg,
        ROUND(p3a.pp_points_3yr_avg, 1) as pp_points_3yr_avg,
        ROUND(p3a.sh_goals_3yr_avg, 1) as sh_goals_3yr_avg,
        ROUND(p3a.sh_points_3yr_avg, 1) as sh_points_3yr_avg,
        
        -- Current season stats
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
        
        -- Metadata
        CURRENT_TIMESTAMP() as created_at,
        'Foster Model v2.0 (Complete)' as model_version
        
    FROM player_3yr_averages p3a
    LEFT JOIN player_ev_3yr_averages pev ON p3a.player_id = pev.player_id
    LEFT JOIN player_archetypes_latest pa ON p3a.player_id = pa.player_id
    WHERE p3a.gp_3yr_avg >= 20
    ORDER BY p3a.points_60_3yr_avg DESC
    """
    
    job = client.query(enhanced_templates_query)
    job.result()
    print("✓ Created enhanced player input templates with special teams data")
    
    # 2. Create complete line assignments
    print("2. Creating complete line assignments...")
    line_assignments_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.line_assignments_complete` AS
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
            -- Rank players by performance within their team and position
            ROW_NUMBER() OVER (
                PARTITION BY pit.team, pit.position_group 
                ORDER BY pit.ev_points_60 DESC, pit.ev_toi_avg_minutes DESC
            ) as team_position_rank
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_complete` pit
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
            'Foster Model v2.0 (Complete)' as model_version
            
        FROM team_rosters tr
    )
    SELECT * FROM line_assignments
    ORDER BY team, position_group, ev_toi_avg_minutes DESC
    """
    
    job = client.query(line_assignments_query)
    job.result()
    print("✓ Created complete line assignments with special teams roles")
    
    # 3. Create complete player forecasts with all strength situations
    print("3. Creating complete player forecasts with all strength situations...")
    player_forecasts_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_forecasts_complete` AS
    WITH player_forecasts AS (
        SELECT 
            la.player_id,
            la.player_name,
            la.position,
            la.team,
            la.primary_role,
            la.special_teams_role,
            la.forecast_toi_minutes,
            la.ev_cf60,
            la.ev_ca60,
            la.ev_gf60,
            la.ev_ga60,
            la.ev_pts_conversion,
            la.pp_goals_3yr_avg,
            la.pp_points_3yr_avg,
            la.sh_goals_3yr_avg,
            la.sh_points_3yr_avg,
            
            -- 5v5 (Even Strength) projections
            la.ev_pts_conversion * 60.0 as ev_points_60,
            la.ev_pts_conversion * 60.0 * 1.0 as ev_points_60_adjusted,  -- No chemistry multiplier for individual stats
            
            -- Power Play projections (5v4)
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
            
            -- TOI breakdown by situation (estimated)
            la.forecast_toi_minutes * 0.75 as ev_toi_minutes,  -- 75% of TOI is 5v5
            la.forecast_toi_minutes * 0.15 as pp_toi_minutes,  -- 15% of TOI is PP
            la.forecast_toi_minutes * 0.10 as sh_toi_minutes,  -- 10% of TOI is PK
            
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
            'Foster Model v2.0 (Complete)' as model_version
            
        FROM `fantasy-snipe-ai.nhl_projections.line_assignments_complete` la
        WHERE la.primary_role IN ('1L', '2L', '3L', '4L', '1D', '2D', '3D')
    )
    SELECT * FROM player_forecasts
    ORDER BY team, primary_role, (ev_points_60 + pp_points_60 + sh_points_60) DESC
    """
    
    job = client.query(player_forecasts_query)
    job.result()
    print("✓ Created complete player forecasts with all strength situations")
    
    # 4. Create final complete view with situation breakdown
    print("4. Creating final complete view with situation breakdown...")
    final_view_query = """
    CREATE OR REPLACE VIEW `fantasy-snipe-ai.nhl_projections.current_player_forecasts_complete` AS
    SELECT 
        pf.player_id,
        pf.player_name,
        pf.position,
        pf.team,
        pf.primary_role,
        pf.special_teams_role,
        pf.forecast_toi_minutes as total_toi_minutes,
        
        -- 5v5 projections
        ROUND(pf.ev_points_60, 2) as ev_points_60,
        ROUND(pf.ev_toi_minutes, 1) as ev_toi_minutes,
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_points,
        ROUND(pf.ev_goals_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_goals,
        ROUND(pf.ev_assists_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82, 1) as ev_projected_assists,
        
        -- Power Play projections
        ROUND(pf.pp_points_60, 2) as pp_points_60,
        ROUND(pf.pp_toi_minutes, 1) as pp_toi_minutes,
        ROUND(pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_points,
        ROUND(pf.pp_goals_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_goals,
        ROUND(pf.pp_assists_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82, 1) as pp_projected_assists,
        
        -- Penalty Kill projections
        ROUND(pf.sh_points_60, 2) as sh_points_60,
        ROUND(pf.sh_toi_minutes, 1) as sh_toi_minutes,
        ROUND(pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as sh_projected_points,
        ROUND(pf.sh_goals_share * pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as sh_projected_goals,
        ROUND(pf.sh_assists_share * pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as sh_projected_assists,
        
        -- Total projections
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as total_projected_points,
        ROUND(pf.ev_goals_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_goals_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_goals_share * pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as total_projected_goals,
        ROUND(pf.ev_assists_share * pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
              pf.pp_assists_share * pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
              pf.sh_assists_share * pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 1) as total_projected_assists,
        
        -- Situation breakdown percentages
        ROUND(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 0) * 100, 1) as ev_points_pct,
        ROUND(pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 0) * 100, 1) as pp_points_pct,
        ROUND(pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82 / 
              NULLIF(pf.ev_points_60 * pf.ev_toi_minutes / 60.0 * 82 + 
                     pf.pp_points_60 * pf.pp_toi_minutes / 60.0 * 82 + 
                     pf.sh_points_60 * pf.sh_toi_minutes / 60.0 * 82, 0) * 100, 1) as sh_points_pct,
        
        pf.created_at,
        pf.model_version
        
    FROM `fantasy-snipe-ai.nhl_projections.player_forecasts_complete` pf
    ORDER BY total_projected_points DESC
    """
    
    job = client.query(final_view_query)
    job.result()
    print("✓ Created final complete view with situation breakdown")
    
    # Run comprehensive QA
    print("\nRunning comprehensive QA on complete model...")
    
    # Check for duplicates
    qa_duplicates = """
    SELECT 
        player_name, 
        team, 
        COUNT(*) as entry_count
    FROM `fantasy-snipe-ai.nhl_projections.line_assignments_complete`
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
    
    # Check top projections with situation breakdown
    qa_projections = """
    SELECT 
        player_name,
        team,
        primary_role,
        special_teams_role,
        total_projected_points,
        ev_projected_points,
        pp_projected_points,
        sh_projected_points,
        ev_points_pct,
        pp_points_pct,
        sh_points_pct
    FROM `fantasy-snipe-ai.nhl_projections.current_player_forecasts_complete`
    WHERE team = 'EDM'
    ORDER BY total_projected_points DESC
    LIMIT 5
    """
    
    qa_job2 = client.query(qa_projections)
    qa_results2 = qa_job2.result()
    
    print("\nTop projections with situation breakdown (Edmonton):")
    for row in qa_results2:
        print(f"  {row.player_name} ({row.primary_role}, {row.special_teams_role}):")
        print(f"    Total: {row.total_projected_points} pts")
        print(f"    5v5: {row.ev_projected_points} pts ({row.ev_points_pct}%)")
        print(f"    PP: {row.pp_projected_points} pts ({row.pp_points_pct}%)")
        print(f"    PK: {row.sh_projected_points} pts ({row.sh_points_pct}%)")
        print()

if __name__ == "__main__":
    create_complete_foster_model()
