#!/usr/bin/env python3
"""
David Foster Forecasting Model - Simple Strength Situation Segmentation

This script creates a simplified version of strength situation segmentation
for our nhl_processed data to support David Foster's forecasting method.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

class SimpleStrengthSegmentation:
    """Handle simplified strength situation segmentation for Foster model."""
    
    def __init__(self, project_id="fantasy-snipe-ai"):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = f"{project_id}.nhl_projections"
    
    def create_simple_strength_tables(self, season):
        """Create simplified strength situation tables."""
        
        print(f"📊 Creating simplified strength situation segmentation for {season}...")
        
        # Create player game metrics by strength situation
        self.create_player_game_metrics_by_strength(season)
        
        # Create team context by strength situation
        self.create_team_context_by_strength(season)
        
        print(f"✅ Simplified strength situation segmentation complete for {season}")
    
    def create_player_game_metrics_by_strength(self, season):
        """Create player game metrics segmented by strength situations."""
        
        print("Creating player game metrics by strength situation...")
        
        query = f"""
        WITH player_game_metrics AS (
            SELECT 
                psm.player_id,
                psm.game_id,
                psm.team_id,
                g.season,
                g.game_type,
                
                -- Even Strength (EV) - Primary for Foster model
                SUM(CASE WHEN psm.strength_state = 'EV' THEN 
                    CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64) 
                    ELSE 0 END) / 60 as toi_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.attempts_for ELSE 0 END) as cf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.attempts_against ELSE 0 END) as ca_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.goals_for ELSE 0 END) as gf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.goals_against ELSE 0 END) as ga_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.shots_for ELSE 0 END) as sf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.shots_against ELSE 0 END) as sa_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.unblocked_for ELSE 0 END) as ff_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.unblocked_against ELSE 0 END) as fa_5v5,
                
                -- Power Play (PP)
                SUM(CASE WHEN psm.strength_state = 'PP' THEN 
                    CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64) 
                    ELSE 0 END) / 60 as toi_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.attempts_for ELSE 0 END) as cf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.attempts_against ELSE 0 END) as ca_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.goals_for ELSE 0 END) as gf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.goals_against ELSE 0 END) as ga_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.shots_for ELSE 0 END) as sf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.shots_against ELSE 0 END) as sa_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.unblocked_for ELSE 0 END) as ff_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.unblocked_against ELSE 0 END) as fa_5v4,
                
                -- Penalty Kill (SH)
                SUM(CASE WHEN psm.strength_state = 'SH' THEN 
                    CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64) 
                    ELSE 0 END) / 60 as toi_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.attempts_for ELSE 0 END) as cf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.attempts_against ELSE 0 END) as ca_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.goals_for ELSE 0 END) as gf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.goals_against ELSE 0 END) as ga_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.shots_for ELSE 0 END) as sf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.shots_against ELSE 0 END) as sa_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.unblocked_for ELSE 0 END) as ff_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.unblocked_against ELSE 0 END) as fa_4v5,
                
                -- Total metrics
                SUM(CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64)) / 60 as toi_total,
                SUM(psm.attempts_for) as cf_total,
                SUM(psm.attempts_against) as ca_total,
                SUM(psm.goals_for) as gf_total,
                SUM(psm.goals_against) as ga_total,
                SUM(psm.shots_for) as sf_total,
                SUM(psm.shots_against) as sa_total,
                SUM(psm.unblocked_for) as ff_total,
                SUM(psm.unblocked_against) as fa_total
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
            WHERE g.season = {season}
            GROUP BY psm.player_id, psm.game_id, psm.team_id, g.season, g.game_type
        ),
        calculated_rates AS (
            SELECT 
                *,
                -- 5v5 rates (Primary for Foster model)
                SAFE_DIVIDE(cf_5v5, toi_5v5) * 60 as cf60_5v5,
                SAFE_DIVIDE(ca_5v5, toi_5v5) * 60 as ca60_5v5,
                SAFE_DIVIDE(gf_5v5, toi_5v5) * 60 as gf60_5v5,
                SAFE_DIVIDE(ga_5v5, toi_5v5) * 60 as ga60_5v5,
                SAFE_DIVIDE(sf_5v5, toi_5v5) * 60 as sf60_5v5,
                SAFE_DIVIDE(sa_5v5, toi_5v5) * 60 as sa60_5v5,
                SAFE_DIVIDE(ff_5v5, toi_5v5) * 60 as ff60_5v5,
                SAFE_DIVIDE(fa_5v5, toi_5v5) * 60 as fa60_5v5,
                SAFE_DIVIDE(cf_5v5, cf_5v5 + ca_5v5) * 100 as cf_pct_5v5,
                SAFE_DIVIDE(ff_5v5, ff_5v5 + fa_5v5) * 100 as ff_pct_5v5,
                SAFE_DIVIDE(sf_5v5, sf_5v5 + sa_5v5) * 100 as sf_pct_5v5,
                SAFE_DIVIDE(gf_5v5, gf_5v5 + ga_5v5) * 100 as gf_pct_5v5,
                
                -- Power Play rates
                SAFE_DIVIDE(cf_5v4, toi_5v4) * 60 as cf60_5v4,
                SAFE_DIVIDE(ca_5v4, toi_5v4) * 60 as ca60_5v4,
                SAFE_DIVIDE(gf_5v4, toi_5v4) * 60 as gf60_5v4,
                SAFE_DIVIDE(ga_5v4, toi_5v4) * 60 as ga60_5v4,
                SAFE_DIVIDE(sf_5v4, toi_5v4) * 60 as sf60_5v4,
                SAFE_DIVIDE(sa_5v4, toi_5v4) * 60 as sa60_5v4,
                SAFE_DIVIDE(ff_5v4, toi_5v4) * 60 as ff60_5v4,
                SAFE_DIVIDE(fa_5v4, toi_5v4) * 60 as fa60_5v4,
                SAFE_DIVIDE(cf_5v4, cf_5v4 + ca_5v4) * 100 as cf_pct_5v4,
                SAFE_DIVIDE(ff_5v4, ff_5v4 + fa_5v4) * 100 as ff_pct_5v4,
                SAFE_DIVIDE(sf_5v4, sf_5v4 + sa_5v4) * 100 as sf_pct_5v4,
                SAFE_DIVIDE(gf_5v4, gf_5v4 + ga_5v4) * 100 as gf_pct_5v4,
                
                -- Penalty Kill rates
                SAFE_DIVIDE(cf_4v5, toi_4v5) * 60 as cf60_4v5,
                SAFE_DIVIDE(ca_4v5, toi_4v5) * 60 as ca60_4v5,
                SAFE_DIVIDE(gf_4v5, toi_4v5) * 60 as gf60_4v5,
                SAFE_DIVIDE(ga_4v5, toi_4v5) * 60 as ga60_4v5,
                SAFE_DIVIDE(sf_4v5, toi_4v5) * 60 as sf60_4v5,
                SAFE_DIVIDE(sa_4v5, toi_4v5) * 60 as sa60_4v5,
                SAFE_DIVIDE(ff_4v5, toi_4v5) * 60 as ff60_4v5,
                SAFE_DIVIDE(fa_4v5, toi_4v5) * 60 as fa60_4v5,
                SAFE_DIVIDE(cf_4v5, cf_4v5 + ca_4v5) * 100 as cf_pct_4v5,
                SAFE_DIVIDE(ff_4v5, ff_4v5 + fa_4v5) * 100 as ff_pct_4v5,
                SAFE_DIVIDE(sf_4v5, sf_4v5 + sa_4v5) * 100 as sf_pct_4v5,
                SAFE_DIVIDE(gf_4v5, gf_4v5 + ga_4v5) * 100 as gf_pct_4v5,
                
                -- Total rates
                SAFE_DIVIDE(cf_total, toi_total) * 60 as cf60_total,
                SAFE_DIVIDE(ca_total, toi_total) * 60 as ca60_total,
                SAFE_DIVIDE(gf_total, toi_total) * 60 as gf60_total,
                SAFE_DIVIDE(ga_total, toi_total) * 60 as ga60_total,
                SAFE_DIVIDE(sf_total, toi_total) * 60 as sf60_total,
                SAFE_DIVIDE(sa_total, toi_total) * 60 as sa60_total,
                SAFE_DIVIDE(ff_total, toi_total) * 60 as ff60_total,
                SAFE_DIVIDE(fa_total, toi_total) * 60 as fa60_total,
                SAFE_DIVIDE(cf_total, cf_total + ca_total) * 100 as cf_pct_total,
                SAFE_DIVIDE(ff_total, ff_total + fa_total) * 100 as ff_pct_total,
                SAFE_DIVIDE(sf_total, sf_total + sa_total) * 100 as sf_pct_total,
                SAFE_DIVIDE(gf_total, gf_total + ga_total) * 100 as gf_pct_total
                
            FROM player_game_metrics
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at
        FROM calculated_rates
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.player_game_metrics_by_strength",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Player game metrics by strength situation created")
    
    def create_team_context_by_strength(self, season):
        """Create team context data segmented by strength situations."""
        
        print("Creating team context by strength situation...")
        
        query = f"""
        WITH team_stats_by_strength AS (
            SELECT 
                t.id as team_id,
                t.full_name as team_name,
                {season} as season,
                
                -- Even Strength (EV) - Primary for Foster model
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.attempts_for ELSE 0 END) as cf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.attempts_against ELSE 0 END) as ca_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.goals_for ELSE 0 END) as gf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.goals_against ELSE 0 END) as ga_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.shots_for ELSE 0 END) as sf_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.shots_against ELSE 0 END) as sa_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.unblocked_for ELSE 0 END) as ff_5v5,
                SUM(CASE WHEN psm.strength_state = 'EV' THEN psm.unblocked_against ELSE 0 END) as fa_5v5,
                
                -- Power Play (PP)
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.attempts_for ELSE 0 END) as cf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.attempts_against ELSE 0 END) as ca_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.goals_for ELSE 0 END) as gf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.goals_against ELSE 0 END) as ga_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.shots_for ELSE 0 END) as sf_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.shots_against ELSE 0 END) as sa_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.unblocked_for ELSE 0 END) as ff_5v4,
                SUM(CASE WHEN psm.strength_state = 'PP' THEN psm.unblocked_against ELSE 0 END) as fa_5v4,
                
                -- Penalty Kill (SH)
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.attempts_for ELSE 0 END) as cf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.attempts_against ELSE 0 END) as ca_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.goals_for ELSE 0 END) as gf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.goals_against ELSE 0 END) as ga_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.shots_for ELSE 0 END) as sf_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.shots_against ELSE 0 END) as sa_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.unblocked_for ELSE 0 END) as ff_4v5,
                SUM(CASE WHEN psm.strength_state = 'SH' THEN psm.unblocked_against ELSE 0 END) as fa_4v5,
                
                -- Total metrics
                SUM(psm.attempts_for) as cf_total,
                SUM(psm.attempts_against) as ca_total,
                SUM(psm.goals_for) as gf_total,
                SUM(psm.goals_against) as ga_total,
                SUM(psm.shots_for) as sf_total,
                SUM(psm.shots_against) as sa_total,
                SUM(psm.unblocked_for) as ff_total,
                SUM(psm.unblocked_against) as fa_total
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON psm.team_id = t.id
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
            WHERE g.season = {season}
            GROUP BY t.id, t.full_name
        ),
        calculated_percentages AS (
            SELECT 
                *,
                -- 5v5 percentages (Primary for Foster model)
                SAFE_DIVIDE(cf_5v5, cf_5v5 + ca_5v5) * 100 as cf_pct_5v5,
                SAFE_DIVIDE(ff_5v5, ff_5v5 + fa_5v5) * 100 as ff_pct_5v5,
                SAFE_DIVIDE(sf_5v5, sf_5v5 + sa_5v5) * 100 as sf_pct_5v5,
                SAFE_DIVIDE(gf_5v5, gf_5v5 + ga_5v5) * 100 as gf_pct_5v5,
                
                -- Power Play percentages
                SAFE_DIVIDE(cf_5v4, cf_5v4 + ca_5v4) * 100 as cf_pct_5v4,
                SAFE_DIVIDE(ff_5v4, ff_5v4 + fa_5v4) * 100 as ff_pct_5v4,
                SAFE_DIVIDE(sf_5v4, sf_5v4 + sa_5v4) * 100 as sf_pct_5v4,
                SAFE_DIVIDE(gf_5v4, gf_5v4 + ga_5v4) * 100 as gf_pct_5v4,
                
                -- Penalty Kill percentages
                SAFE_DIVIDE(cf_4v5, cf_4v5 + ca_4v5) * 100 as cf_pct_4v5,
                SAFE_DIVIDE(ff_4v5, ff_4v5 + fa_4v5) * 100 as ff_pct_4v5,
                SAFE_DIVIDE(sf_4v5, sf_4v5 + sa_4v5) * 100 as sf_pct_4v5,
                SAFE_DIVIDE(gf_4v5, gf_4v5 + ga_4v5) * 100 as gf_pct_4v5,
                
                -- Total percentages
                SAFE_DIVIDE(cf_total, cf_total + ca_total) * 100 as cf_pct_total,
                SAFE_DIVIDE(ff_total, ff_total + fa_total) * 100 as ff_pct_total,
                SAFE_DIVIDE(sf_total, sf_total + sa_total) * 100 as sf_pct_total,
                SAFE_DIVIDE(gf_total, gf_total + ga_total) * 100 as gf_pct_total
                
            FROM team_stats_by_strength
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at,
            CURRENT_TIMESTAMP() as updated_at
        FROM calculated_percentages
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.team_context_by_strength",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Team context by strength situation created")
    
    def get_strength_situation_summary(self, season):
        """Get summary of strength situation data."""
        
        query = f"""
        SELECT 
            '5v5' as strength_situation,
            COUNT(DISTINCT player_id) as players,
            COUNT(DISTINCT team_id) as teams,
            AVG(toi_5v5) as avg_toi,
            AVG(cf_pct_5v5) as avg_cf_pct,
            AVG(gf60_5v5) as avg_gf60
        FROM `{self.dataset_id}.player_game_metrics_by_strength`
        WHERE season = {season}
        
        UNION ALL
        
        SELECT 
            '5v4' as strength_situation,
            COUNT(DISTINCT player_id) as players,
            COUNT(DISTINCT team_id) as teams,
            AVG(toi_5v4) as avg_toi,
            AVG(cf_pct_5v4) as avg_cf_pct,
            AVG(gf60_5v4) as avg_gf60
        FROM `{self.dataset_id}.player_game_metrics_by_strength`
        WHERE season = {season}
        
        UNION ALL
        
        SELECT 
            '4v5' as strength_situation,
            COUNT(DISTINCT player_id) as players,
            COUNT(DISTINCT team_id) as teams,
            AVG(toi_4v5) as avg_toi,
            AVG(cf_pct_4v5) as avg_cf_pct,
            AVG(gf60_4v5) as avg_gf60
        FROM `{self.dataset_id}.player_game_metrics_by_strength`
        WHERE season = {season}
        
        ORDER BY strength_situation
        """
        
        result = self.client.query(query).to_dataframe()
        return result

def main():
    """Main function to run simplified strength situation segmentation."""
    
    segmenter = SimpleStrengthSegmentation()
    
    # Get current season
    current_year = datetime.now().year
    season = current_year
    
    # Create strength situation segmentation
    segmenter.create_simple_strength_tables(season)
    
    # Get summary
    summary = segmenter.get_strength_situation_summary(season)
    print("\n📊 Strength Situation Summary:")
    print(summary)

if __name__ == "__main__":
    main()
