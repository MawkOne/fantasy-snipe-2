#!/usr/bin/env python3
"""
David Foster Forecasting Model - Core Implementation

This script implements the core forecasting logic based on David Foster's method,
adapted for BigQuery automation.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import json

class FosterForecastingModel:
    """Core implementation of David Foster's forecasting method."""
    
    def __init__(self, project_id="fantasy-snipe-ai"):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = f"{project_id}.nhl_projections"
        
    def create_team_context(self, season):
        """Create team context data for the season using strength situation segmentation."""
        
        print(f"📊 Creating team context for {season} using strength situation data...")
        
        query = f"""
        WITH team_stats AS (
            SELECT 
                t.id as team_id,
                t.full_name as team_name,
                {season} as season,
                -- Use 5v5 data as primary (Foster model focus)
                SUM(tms.cf) as cf_total,
                SUM(tms.ca) as ca_total,
                AVG(tms.cf_pct) as cf_pct,
                SUM(tms.gf) as goals_for,
                SUM(tms.ga) as goals_against,
                AVG(tms.gf_pct) as goal_pct,
                -- Include special teams context (will add PP/PK data separately)
                0.0 as cf_pct_pp,  -- Placeholder
                0.0 as gf_pct_pp,  -- Placeholder
                0.0 as cf_pct_pk,  -- Placeholder
                0.0 as gf_pct_pk,  -- Placeholder
                SUM(tms.gf) - SUM(tms.ga) as gf_ga_differential
            FROM `fantasy-snipe-ai.nhl_processed.team_metrics_by_strength` tms
            JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON tms.team_id = t.id
            WHERE tms.season = {season}
                AND tms.strength_situation = 'EV'  -- Focus on 5v5 for Foster model
            GROUP BY t.id, t.full_name
        )
        SELECT 
            ts.*,
            0.5 as win_pct,  -- Placeholder - will be calculated from game results later
            CURRENT_TIMESTAMP() as created_at,
            CURRENT_TIMESTAMP() as updated_at
        FROM team_stats ts
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.team_context",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print(f"✅ Team context created for {season}")
    
    def create_toi_profiles(self, season):
        """Create TOI profiles by role and position."""
        
        print(f"📊 Creating TOI profiles for {season}...")
        
        query = f"""
        WITH player_roles AS (
            SELECT 
                p.player_id,
                p.position,
                CASE 
                    WHEN p.position IN ('C', 'LW', 'RW') THEN 'Forward'
                    WHEN p.position = 'D' THEN 'Defense'
                    ELSE 'Goalie'
                END as position_group,
                CASE 
                    WHEN pd.birth_date IS NOT NULL 
                    THEN {season} - EXTRACT(YEAR FROM CAST(pd.birth_date AS DATE))
                    ELSE NULL
                END as age,
                CASE 
                    WHEN EXTRACT(YEAR FROM pd.birth_date) IS NOT NULL 
                    THEN 
                        CASE 
                            WHEN {season} - EXTRACT(YEAR FROM pd.birth_date) < 23 THEN 'Young'
                            WHEN {season} - EXTRACT(YEAR FROM pd.birth_date) < 27 THEN 'Prime'
                            WHEN {season} - EXTRACT(YEAR FROM pd.birth_date) < 32 THEN 'Veteran'
                            ELSE 'Old'
                        END
                    ELSE 'Unknown'
                END as age_group,
                AVG(pgm.toi_seconds) / 60 as avg_toi_total,
                AVG(pgm.toi_ev_seconds) / 60 as avg_toi_ev,
                AVG(pgm.toi_pp_seconds) / 60 as avg_toi_pp,
                AVG(pgm.toi_pk_seconds) / 60 as avg_toi_pk,
                COUNT(*) as games_played
            FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
            JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pgm.player_id = p.player_id
            LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_details` pd ON p.player_id = pd.player_id
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON pgm.game_id = g.game_id
            WHERE g.season = {season}
                AND p.position != 'G'
            GROUP BY p.player_id, p.position, position_group, age, age_group
        ),
        role_assignments AS (
            SELECT 
                player_id,
                position,
                position_group,
                age_group,
                avg_toi_total,
                CASE 
                    WHEN avg_toi_total >= 18 THEN '1L'
                    WHEN avg_toi_total >= 15 THEN '2L'
                    WHEN avg_toi_total >= 12 THEN '3L'
                    ELSE '4L'
                END as role,
                games_played
            FROM player_roles
            WHERE position_group = 'Forward'
            
            UNION ALL
            
            SELECT 
                player_id,
                position,
                position_group,
                age_group,
                avg_toi_total,
                CASE 
                    WHEN avg_toi_total >= 20 THEN '1D'
                    WHEN avg_toi_total >= 16 THEN '2D'
                    ELSE '3D'
                END as role,
                games_played
            FROM player_roles
            WHERE position_group = 'Defense'
        ),
        role_profiles AS (
            SELECT 
                role,
                position,
                age_group,
                {season} as season,
                AVG(avg_toi_ev) as avg_toi_ev,
                AVG(avg_toi_pp) as avg_toi_pp,
                AVG(avg_toi_pk) as avg_toi_pk,
                AVG(avg_toi_total) as avg_toi_total,
                COUNT(*) as sample_size
            FROM role_assignments ra
            JOIN player_roles pr ON ra.player_id = pr.player_id
            GROUP BY role, position, age_group
        )
        SELECT 
            role,
            position,
            age_group,
            season,
            avg_toi_ev,
            avg_toi_pp,
            avg_toi_pk,
            avg_toi_total,
            sample_size,
            CURRENT_TIMESTAMP() as created_at
        FROM role_profiles
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.toi_profiles_by_role",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print(f"✅ TOI profiles created for {season}")
    
    def create_player_archetypes(self, season):
        """Create player archetype classifications using strength situation data."""
        
        print(f"📊 Creating player archetypes for {season} using 5v5 data...")
        
        query = f"""
        WITH player_stats AS (
            SELECT 
                p.player_id,
                {season} as season,
                p.position,
                CASE 
                    WHEN pd.birth_date IS NOT NULL 
                    THEN {season} - EXTRACT(YEAR FROM CAST(pd.birth_date AS DATE))
                    ELSE NULL
                END as age,
                -- Use 5v5 data as primary (Foster model focus)
                AVG(pgms.cf_pct) as cf_pct,
                AVG(pgms.gf60) as gf60,
                AVG(pgms.gf60) as pts60,  -- Using GF60 as proxy for points
                AVG(pgms.toi_minutes) as toi_avg,
                SAFE_DIVIDE(SUM(pgms.gf), SUM(pgms.cf)) as pts_conversion,
                -- Include special teams context (will add PP/PK data separately)
                0.0 as cf_pct_pp,  -- Placeholder
                0.0 as gf60_pp,    -- Placeholder
                0.0 as cf_pct_pk,  -- Placeholder
                0.0 as gf60_pk,    -- Placeholder
                COUNT(*) as games_played
            FROM `fantasy-snipe-ai.nhl_processed.player_game_metrics_by_strength` pgms
            JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pgms.player_id = p.player_id
            LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_details` pd ON p.player_id = pd.player_id
            WHERE pgms.season = {season}
                AND pgms.strength_situation = 'EV'  -- Focus on 5v5 for Foster model
                AND p.position != 'G'
            GROUP BY p.player_id, p.position, age
        ),
        archetype_classification AS (
            SELECT 
                player_id,
                season,
                position,
                age,
                cf_pct,
                gf60,
                pts60,
                toi_avg,
                pts_conversion,
                games_played,
                CASE 
                    WHEN cf_pct >= 55.0 AND gf60 >= 25.0 AND toi_avg >= 18.0 THEN 'Elite'
                    WHEN cf_pct >= 50.0 AND gf60 >= 20.0 AND toi_avg >= 15.0 THEN 'High'
                    WHEN cf_pct >= 45.0 AND gf60 >= 15.0 AND toi_avg >= 12.0 THEN 'Middle'
                    ELSE 'Lower'
                END as primary_archetype,
                CASE 
                    WHEN position = 'D' THEN
                        CASE 
                            WHEN gf60 >= 20.0 THEN 'Off Defence'
                            ELSE 'Def Defence'
                        END
                    ELSE
                        CASE 
                            WHEN gf60 >= 25.0 AND pts_conversion >= 0.15 THEN 'Elite'
                            WHEN gf60 >= 20.0 AND pts_conversion >= 0.12 THEN 'Playmaker'
                            WHEN gf60 >= 18.0 AND pts_conversion >= 0.10 THEN 'Sniper'
                            WHEN gf60 >= 15.0 THEN 'Power Forward'
                            ELSE 'Forechecker'
                        END
                END as secondary_archetype,
                (cf_pct + gf60 + pts60) / 3 as archetype_score
            FROM player_stats
        )
        SELECT 
            player_id,
            season,
            primary_archetype,
            secondary_archetype,
            archetype_score,
            age,
            cf_pct,
            gf60,
            pts_conversion,
            toi_avg,
            CURRENT_TIMESTAMP() as created_at
        FROM archetype_classification
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.player_archetypes",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print(f"✅ Player archetypes created for {season}")
    
    def create_age_curve_adjustments(self, season):
        """Create age curve adjustments for player performance."""
        
        print(f"📊 Creating age curve adjustments for {season}...")
        
        query = f"""
        WITH age_performance AS (
            SELECT 
                CASE 
                    WHEN pd.birth_date IS NOT NULL 
                    THEN {season} - EXTRACT(YEAR FROM CAST(pd.birth_date AS DATE))
                    ELSE NULL
                END as age,
                p.position,
                AVG(pgm.cf_pct) as avg_cf_pct,
                AVG(pgm.gf60) as avg_gf60,
                AVG(pgm.pts60) as avg_pts60,
                AVG(pgm.toi_seconds) / 60 as avg_toi,
                COUNT(*) as sample_size
            FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
            JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pgm.player_id = p.player_id
            LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_details` pd ON p.player_id = pd.player_id
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON pgm.game_id = g.game_id
            WHERE g.season = {season}
                AND p.position != 'G'
                AND EXTRACT(YEAR FROM pd.birth_date) IS NOT NULL
            GROUP BY age, p.position
            HAVING sample_size >= 5
        ),
        peak_performance AS (
            SELECT 
                position,
                MAX(avg_cf_pct) as peak_cf_pct,
                MAX(avg_gf60) as peak_gf60,
                MAX(avg_pts60) as peak_pts60,
                MAX(avg_toi) as peak_toi
            FROM age_performance
            GROUP BY position
        ),
        adjustments AS (
            SELECT 
                ap.age,
                ap.position,
                'cf_pct' as metric,
                SAFE_DIVIDE(ap.avg_cf_pct, pp.peak_cf_pct) as adjustment_factor,
                ap.sample_size,
                CASE 
                    WHEN ap.sample_size >= 20 THEN 0.9
                    WHEN ap.sample_size >= 10 THEN 0.7
                    ELSE 0.5
                END as confidence
            FROM age_performance ap
            JOIN peak_performance pp ON ap.position = pp.position
            
            UNION ALL
            
            SELECT 
                ap.age,
                ap.position,
                'gf60' as metric,
                SAFE_DIVIDE(ap.avg_gf60, pp.peak_gf60) as adjustment_factor,
                ap.sample_size,
                CASE 
                    WHEN ap.sample_size >= 20 THEN 0.9
                    WHEN ap.sample_size >= 10 THEN 0.7
                    ELSE 0.5
                END as confidence
            FROM age_performance ap
            JOIN peak_performance pp ON ap.position = pp.position
            
            UNION ALL
            
            SELECT 
                ap.age,
                ap.position,
                'pts60' as metric,
                SAFE_DIVIDE(ap.avg_pts60, pp.peak_pts60) as adjustment_factor,
                ap.sample_size,
                CASE 
                    WHEN ap.sample_size >= 20 THEN 0.9
                    WHEN ap.sample_size >= 10 THEN 0.7
                    ELSE 0.5
                END as confidence
            FROM age_performance ap
            JOIN peak_performance pp ON ap.position = pp.position
            
            UNION ALL
            
            SELECT 
                ap.age,
                ap.position,
                'toi' as metric,
                SAFE_DIVIDE(ap.avg_toi, pp.peak_toi) as adjustment_factor,
                ap.sample_size,
                CASE 
                    WHEN ap.sample_size >= 20 THEN 0.9
                    WHEN ap.sample_size >= 10 THEN 0.7
                    ELSE 0.5
                END as confidence
            FROM age_performance ap
            JOIN peak_performance pp ON ap.position = pp.position
        )
        SELECT 
            age,
            position,
            metric,
            adjustment_factor,
            sample_size,
            confidence,
            CURRENT_TIMESTAMP() as created_at
        FROM adjustments
        WHERE adjustment_factor IS NOT NULL
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.age_curve_adjustments",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print(f"✅ Age curve adjustments created for {season}")
    
    def create_player_input_templates(self, season):
        """Create player input templates for forecasting."""
        
        print(f"📊 Creating player input templates for {season}...")
        
        query = f"""
        WITH player_season_stats AS (
            SELECT 
                p.player_id,
                p.full_name as player_name,
                p.position,
                CASE 
                    WHEN p.position IN ('C', 'LW', 'RW') THEN 'Forward'
                    WHEN p.position = 'D' THEN 'Defense'
                    ELSE 'Goalie'
                END as position_group,
                t.team_id,
                CASE 
                    WHEN pd.birth_date IS NOT NULL 
                    THEN {season} - EXTRACT(YEAR FROM CAST(pd.birth_date AS DATE))
                    ELSE NULL
                END as age,
                AVG(pgm.games_played) as gp_3yr_avg,
                SUM(pgm.games_played) as gp_3yr_total,
                AVG(pgm.toi_ev_seconds) / 60 as toi_ev_avg,
                AVG(pgm.cf60) as ecf60,
                AVG(pgm.ca60) as eca60,
                SAFE_DIVIDE(SUM(pgm.goals + pgm.assists), SUM(pgm.cf)) as pts_conversion,
                AVG(pgm.gf60) as gf60,
                AVG(pgm.ga60) as ga60
            FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
            JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pgm.player_id = p.player_id
            LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_details` pd ON p.player_id = pd.player_id
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON pgm.game_id = g.game_id
            JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pgm.team_id = t.team_id
            WHERE g.season = {season}
                AND p.position != 'G'
            GROUP BY p.player_id, p.full_name, p.position, position_group, t.team_id, age
        )
        SELECT 
            player_id,
            {season} as season,
            player_name,
            position,
            position_group,
            team_id,
            age,
            gp_3yr_avg,
            gp_3yr_total,
            toi_ev_avg,
            ecf60,
            eca60,
            pts_conversion,
            gf60,
            ga60,
            CURRENT_TIMESTAMP() as created_at
        FROM player_season_stats
        WHERE age IS NOT NULL
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.player_input_templates",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print(f"✅ Player input templates created for {season}")
    
    def run_initial_setup(self, season):
        """Run the initial setup for the Foster model."""
        
        print(f"🏒 Setting up David Foster forecasting model for {season}")
        print("=" * 60)
        
        # Create all the foundational tables
        self.create_team_context(season)
        self.create_toi_profiles(season)
        self.create_player_archetypes(season)
        self.create_age_curve_adjustments(season)
        self.create_player_input_templates(season)
        
        print(f"\n✅ Initial setup complete for {season}!")
        print("Next steps:")
        print("1. Create line assignments")
        print("2. Implement line-level forecasting")
        print("3. Build points allocation system")
        print("4. Add validation and quality control")

def main():
    """Main function to run the Foster model setup."""
    
    model = FosterForecastingModel()
    
    # Get current season
    current_year = datetime.now().year
    season = current_year
    
    # Run initial setup
    model.run_initial_setup(season)

if __name__ == "__main__":
    main()
