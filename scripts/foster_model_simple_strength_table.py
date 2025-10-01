#!/usr/bin/env python3
"""
David Foster Forecasting Model - Simple Strength Situation Table

This script creates a single table with a strength_situation column
instead of separate tables for each strength situation.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

class SimpleStrengthTable:
    """Create a single table with strength_situation column."""
    
    def __init__(self, project_id="fantasy-snipe-ai"):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = f"{project_id}.nhl_projections"
    
    def create_simple_strength_table(self, season):
        """Create a single table with strength_situation column."""
        
        print(f"📊 Creating simple strength situation table for {season}...")
        
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
                psm.unblocked_against as fa
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
            WHERE g.season = {season}
                AND psm.strength_state IS NOT NULL
        ),
        calculated_metrics AS (
            SELECT 
                *,
                -- Convert to minutes
                duration_seconds / 60 as toi_minutes,
                
                -- Calculate rates per 60 minutes
                SAFE_DIVIDE(cf, duration_seconds) * 3600 as cf60,
                SAFE_DIVIDE(ca, duration_seconds) * 3600 as ca60,
                SAFE_DIVIDE(gf, duration_seconds) * 3600 as gf60,
                SAFE_DIVIDE(ga, duration_seconds) * 3600 as ga60,
                SAFE_DIVIDE(sf, duration_seconds) * 3600 as sf60,
                SAFE_DIVIDE(sa, duration_seconds) * 3600 as sa60,
                SAFE_DIVIDE(ff, duration_seconds) * 3600 as ff60,
                SAFE_DIVIDE(fa, duration_seconds) * 3600 as fa60,
                
                -- Calculate percentages
                SAFE_DIVIDE(cf, cf + ca) * 100 as cf_pct,
                SAFE_DIVIDE(ff, ff + fa) * 100 as ff_pct,
                SAFE_DIVIDE(sf, sf + sa) * 100 as sf_pct,
                SAFE_DIVIDE(gf, gf + ga) * 100 as gf_pct
                
            FROM player_metrics_by_strength
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at
        FROM calculated_metrics
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.player_game_metrics_by_strength_simple",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Simple strength situation table created")
    
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
        FROM `{self.dataset_id}.player_game_metrics_by_strength_simple`
        WHERE season = {season}
        GROUP BY strength_situation
        ORDER BY strength_situation
        """
        
        result = self.client.query(query).to_dataframe()
        return result

def main():
    """Main function to create simple strength table."""
    
    table_creator = SimpleStrengthTable()
    
    # Get current season
    current_year = datetime.now().year
    season = 20242025
    
    # Create simple strength table
    table_creator.create_simple_strength_table(season)
    
    # Get summary
    summary = table_creator.get_strength_summary(season)
    print("\n📊 Strength Situation Summary:")
    print(summary)

if __name__ == "__main__":
    main()
