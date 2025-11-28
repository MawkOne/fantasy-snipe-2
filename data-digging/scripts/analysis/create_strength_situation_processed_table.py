#!/usr/bin/env python3
"""
Create strength situation breakdown in nhl_processed dataset

This script creates a new table in nhl_processed that aggregates
player_shift_metrics by strength situation, avoiding data duplication.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

class StrengthSituationProcessedTable:
    """Create strength situation table in nhl_processed dataset."""
    
    def __init__(self, project_id="fantasy-snipe-ai"):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.processed_dataset = f"{project_id}.nhl_processed"
    
    def create_player_game_metrics_by_strength(self, season):
        """Create player game metrics by strength situation in nhl_processed dataset."""
        
        print(f"📊 Creating player game metrics by strength situation for {season}...")
        
        query = f"""
        WITH player_metrics_by_strength AS (
            SELECT 
                psm.player_id,
                psm.game_id,
                psm.team_id,
                g.season,
                g.game_type,
                psm.strength_state as strength_situation,
                
                -- Convert duration to minutes
                CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64) as duration_seconds,
                
                -- Raw metrics
                psm.attempts_for as cf,
                psm.attempts_against as ca,
                psm.goals_for as gf,
                psm.goals_against as ga,
                psm.shots_for as sf,
                psm.shots_against as sa,
                psm.unblocked_for as ff,
                psm.unblocked_against as fa,
                psm.hits_for,
                psm.hits_against,
                psm.takeaways_for,
                psm.takeaways_against,
                psm.giveaways_for,
                psm.giveaways_against,
                psm.blocks_for,
                psm.blocks_against
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
            WHERE g.season = {season}
                AND psm.strength_state IS NOT NULL
        ),
        aggregated_metrics AS (
            SELECT 
                player_id,
                game_id,
                team_id,
                season,
                game_type,
                strength_situation,
                
                -- Sum raw metrics
                SUM(duration_seconds) as total_duration_seconds,
                SUM(cf) as cf,
                SUM(ca) as ca,
                SUM(gf) as gf,
                SUM(ga) as ga,
                SUM(sf) as sf,
                SUM(sa) as sa,
                SUM(ff) as ff,
                SUM(fa) as fa,
                SUM(hits_for) as hits_for,
                SUM(hits_against) as hits_against,
                SUM(takeaways_for) as takeaways_for,
                SUM(takeaways_against) as takeaways_against,
                SUM(giveaways_for) as giveaways_for,
                SUM(giveaways_against) as giveaways_against,
                SUM(blocks_for) as blocks_for,
                SUM(blocks_against) as blocks_against
                
            FROM player_metrics_by_strength
            GROUP BY player_id, game_id, team_id, season, game_type, strength_situation
        ),
        calculated_metrics AS (
            SELECT 
                *,
                -- Convert to minutes
                total_duration_seconds / 60 as toi_minutes,
                
                -- Calculate rates per 60 minutes
                SAFE_DIVIDE(cf, total_duration_seconds) * 3600 as cf60,
                SAFE_DIVIDE(ca, total_duration_seconds) * 3600 as ca60,
                SAFE_DIVIDE(gf, total_duration_seconds) * 3600 as gf60,
                SAFE_DIVIDE(ga, total_duration_seconds) * 3600 as ga60,
                SAFE_DIVIDE(sf, total_duration_seconds) * 3600 as sf60,
                SAFE_DIVIDE(sa, total_duration_seconds) * 3600 as sa60,
                SAFE_DIVIDE(ff, total_duration_seconds) * 3600 as ff60,
                SAFE_DIVIDE(fa, total_duration_seconds) * 3600 as fa60,
                SAFE_DIVIDE(hits_for, total_duration_seconds) * 3600 as hits60,
                SAFE_DIVIDE(hits_against, total_duration_seconds) * 3600 as hits_against60,
                SAFE_DIVIDE(takeaways_for, total_duration_seconds) * 3600 as takeaways60,
                SAFE_DIVIDE(takeaways_against, total_duration_seconds) * 3600 as takeaways_against60,
                SAFE_DIVIDE(giveaways_for, total_duration_seconds) * 3600 as giveaways60,
                SAFE_DIVIDE(giveaways_against, total_duration_seconds) * 3600 as giveaways_against60,
                SAFE_DIVIDE(blocks_for, total_duration_seconds) * 3600 as blocks60,
                SAFE_DIVIDE(blocks_against, total_duration_seconds) * 3600 as blocks_against60,
                
                -- Calculate percentages
                SAFE_DIVIDE(cf, cf + ca) * 100 as cf_pct,
                SAFE_DIVIDE(ff, ff + fa) * 100 as ff_pct,
                SAFE_DIVIDE(sf, sf + sa) * 100 as sf_pct,
                SAFE_DIVIDE(gf, gf + ga) * 100 as gf_pct
                
            FROM aggregated_metrics
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at
        FROM calculated_metrics
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.processed_dataset}.player_game_metrics_by_strength",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Player game metrics by strength situation created in nhl_processed")
    
    def create_team_metrics_by_strength(self, season):
        """Create team metrics by strength situation in nhl_processed dataset."""
        
        print(f"📊 Creating team metrics by strength situation for {season}...")
        
        query = f"""
        WITH team_metrics_by_strength AS (
            SELECT 
                psm.team_id,
                g.season,
                psm.strength_state as strength_situation,
                
                -- Sum raw metrics
                SUM(CAST(SPLIT(psm.duration, ':')[0] AS INT64) * 60 + CAST(SPLIT(psm.duration, ':')[1] AS INT64)) as total_duration_seconds,
                SUM(psm.attempts_for) as cf,
                SUM(psm.attempts_against) as ca,
                SUM(psm.goals_for) as gf,
                SUM(psm.goals_against) as ga,
                SUM(psm.shots_for) as sf,
                SUM(psm.shots_against) as sa,
                SUM(psm.unblocked_for) as ff,
                SUM(psm.unblocked_against) as fa
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
            WHERE g.season = {season}
                AND psm.strength_state IS NOT NULL
            GROUP BY psm.team_id, g.season, psm.strength_state
        ),
        calculated_metrics AS (
            SELECT 
                *,
                -- Convert to minutes
                total_duration_seconds / 60 as toi_minutes,
                
                -- Calculate rates per 60 minutes
                SAFE_DIVIDE(cf, total_duration_seconds) * 3600 as cf60,
                SAFE_DIVIDE(ca, total_duration_seconds) * 3600 as ca60,
                SAFE_DIVIDE(gf, total_duration_seconds) * 3600 as gf60,
                SAFE_DIVIDE(ga, total_duration_seconds) * 3600 as ga60,
                SAFE_DIVIDE(sf, total_duration_seconds) * 3600 as sf60,
                SAFE_DIVIDE(sa, total_duration_seconds) * 3600 as sa60,
                SAFE_DIVIDE(ff, total_duration_seconds) * 3600 as ff60,
                SAFE_DIVIDE(fa, total_duration_seconds) * 3600 as fa60,
                
                -- Calculate percentages
                SAFE_DIVIDE(cf, cf + ca) * 100 as cf_pct,
                SAFE_DIVIDE(ff, ff + fa) * 100 as ff_pct,
                SAFE_DIVIDE(sf, sf + sa) * 100 as sf_pct,
                SAFE_DIVIDE(gf, gf + ga) * 100 as gf_pct
                
            FROM team_metrics_by_strength
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at
        FROM calculated_metrics
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.processed_dataset}.team_metrics_by_strength",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Team metrics by strength situation created in nhl_processed")
    
    def get_strength_summary(self, season):
        """Get summary of strength situation data."""
        
        query = f"""
        SELECT 
            strength_situation,
            COUNT(DISTINCT player_id) as players,
            COUNT(DISTINCT team_id) as teams,
            AVG(toi_minutes) as avg_toi,
            AVG(cf_pct) as avg_cf_pct,
            AVG(gf60) as avg_gf60
        FROM `{self.processed_dataset}.player_game_metrics_by_strength`
        WHERE season = {season}
        GROUP BY strength_situation
        ORDER BY strength_situation
        """
        
        result = self.client.query(query).to_dataframe()
        return result

def main():
    """Main function to create strength situation tables in nhl_processed."""
    
    table_creator = StrengthSituationProcessedTable()
    
    # Get current season
    season = 20242025
    
    # Create strength situation tables in nhl_processed
    table_creator.create_player_game_metrics_by_strength(season)
    table_creator.create_team_metrics_by_strength(season)
    
    # Get summary
    summary = table_creator.get_strength_summary(season)
    print("\n📊 Strength Situation Summary:")
    print(summary)

if __name__ == "__main__":
    main()
