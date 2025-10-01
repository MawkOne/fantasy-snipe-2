#!/usr/bin/env python3
"""
David Foster Forecasting Model - Strength Situation Segmentation

This script implements strength situation segmentation for our nhl_processed data
to support David Foster's forecasting method without external data sources.
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

class StrengthSituationSegmentation:
    """Handle strength situation segmentation for Foster model."""
    
    def __init__(self, project_id="fantasy-snipe-ai"):
        self.client = bigquery.Client()
        self.project_id = project_id
        self.dataset_id = f"{project_id}.nhl_projections"
        
        # Define strength situations based on the dropdown
        self.strength_situations = {
            'all_strengths': 'All Strengths',
            'even_strength': 'Even Strength', 
            '5v5': '5v5',
            '5v5_score_venue_adjusted': '5v5 Score & Venue Adjusted',
            'power_play': 'Power Play',
            '5v4_pp': '5 on 4 PP',
            'penalty_kill': 'Penalty Kill',
            '4v5_pk': '4 on 5 PK',
            '3v3': '3 on 3',
            'with_empty_net': 'With Empty Net',
            'against_empty_net': 'Against Empty Net'
        }
    
    def create_strength_situation_tables(self, season):
        """Create tables segmented by strength situations."""
        
        print(f"📊 Creating strength situation segmentation for {season}...")
        
        # Create player shift metrics by strength situation
        self.create_player_shift_metrics_by_strength(season)
        
        # Create player game advanced metrics by strength situation  
        self.create_player_game_metrics_by_strength(season)
        
        # Create team context by strength situation
        self.create_team_context_by_strength(season)
        
        print(f"✅ Strength situation segmentation complete for {season}")
    
    def create_player_shift_metrics_by_strength(self, season):
        """Create player shift metrics segmented by strength situations."""
        
        print("Creating player shift metrics by strength situation...")
        
        query = f"""
        WITH shift_metrics_by_strength AS (
            SELECT 
                psm.player_id,
                psm.game_id,
                psm.team_id,
                g.season,
                g.game_type,
                
                -- Even Strength (5v5)
                SUM(CASE WHEN psm.strength_state = '5v5' THEN CAST(psm.duration AS FLOAT64) ELSE 0 END) as toi_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.attempts_for ELSE 0 END) as cf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.attempts_against ELSE 0 END) as ca_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.goals_for ELSE 0 END) as gf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.goals_against ELSE 0 END) as ga_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.shots_for ELSE 0 END) as sf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.shots_against ELSE 0 END) as sa_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.unblocked_for ELSE 0 END) as ff_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.unblocked_against ELSE 0 END) as fa_5v5,
                
                -- Power Play (5v4)
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.duration ELSE 0 END) as toi_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.cf ELSE 0 END) as cf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ca ELSE 0 END) as ca_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.gf ELSE 0 END) as gf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ga ELSE 0 END) as ga_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sf ELSE 0 END) as sf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sa ELSE 0 END) as sa_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ff ELSE 0 END) as ff_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.fa ELSE 0 END) as fa_5v4,
                
                -- Penalty Kill (4v5)
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.duration ELSE 0 END) as toi_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.cf ELSE 0 END) as cf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ca ELSE 0 END) as ca_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.gf ELSE 0 END) as gf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ga ELSE 0 END) as ga_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sf ELSE 0 END) as sf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sa ELSE 0 END) as sa_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ff ELSE 0 END) as ff_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.fa ELSE 0 END) as fa_4v5,
                
                -- 3v3
                SUM(CASE WHEN psm.strength_state = '3v3' THEN psm.duration ELSE 0 END) as toi_3v3,
                SUM(CASE WHEN psm.strength_state = '3v3' THEN psm.cf ELSE 0 END) as cf_3v3,
                SUM(CASE WHEN psm.strength_state = '3v3' THEN psm.ca ELSE 0 END) as ca_3v3,
                SUM(CASE WHEN psm.strength_state = '3v3' THEN psm.gf ELSE 0 END) as gf_3v3,
                SUM(CASE WHEN psm.strength_state = '3v3' THEN psm.ga ELSE 0 END) as ga_3v3,
                
                -- Empty Net (6v5)
                SUM(CASE WHEN psm.strength_state = '6v5' THEN psm.duration ELSE 0 END) as toi_6v5,
                SUM(CASE WHEN psm.strength_state = '6v5' THEN psm.cf ELSE 0 END) as cf_6v5,
                SUM(CASE WHEN psm.strength_state = '6v5' THEN psm.ca ELSE 0 END) as ca_6v5,
                SUM(CASE WHEN psm.strength_state = '6v5' THEN psm.gf ELSE 0 END) as gf_6v5,
                SUM(CASE WHEN psm.strength_state = '6v5' THEN psm.ga ELSE 0 END) as ga_6v5,
                
                -- Empty Net Against (5v6)
                SUM(CASE WHEN psm.strength_state = '5v6' THEN psm.duration ELSE 0 END) as toi_5v6,
                SUM(CASE WHEN psm.strength_state = '5v6' THEN psm.cf ELSE 0 END) as cf_5v6,
                SUM(CASE WHEN psm.strength_state = '5v6' THEN psm.ca ELSE 0 END) as ca_5v6,
                SUM(CASE WHEN psm.strength_state = '5v6' THEN psm.gf ELSE 0 END) as gf_5v6,
                SUM(CASE WHEN psm.strength_state = '5v6' THEN psm.ga ELSE 0 END) as ga_5v6,
                
                -- Total metrics
                SUM(psm.duration) as toi_total,
                SUM(psm.cf) as cf_total,
                SUM(psm.ca) as ca_total,
                SUM(psm.gf) as gf_total,
                SUM(psm.ga) as ga_total,
                SUM(psm.sf) as sf_total,
                SUM(psm.sa) as sa_total,
                SUM(psm.ff) as ff_total,
                SUM(psm.fa) as fa_total
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.game_id
            WHERE g.season = {season}
            GROUP BY psm.player_id, psm.game_id, psm.team_id, g.season, g.game_type
        ),
        calculated_metrics AS (
            SELECT 
                *,
                -- 5v5 rates
                SAFE_DIVIDE(cf_5v5, toi_5v5) * 3600 as cf60_5v5,
                SAFE_DIVIDE(ca_5v5, toi_5v5) * 3600 as ca60_5v5,
                SAFE_DIVIDE(gf_5v5, toi_5v5) * 3600 as gf60_5v5,
                SAFE_DIVIDE(ga_5v5, toi_5v5) * 3600 as ga60_5v5,
                SAFE_DIVIDE(sf_5v5, toi_5v5) * 3600 as sf60_5v5,
                SAFE_DIVIDE(sa_5v5, toi_5v5) * 3600 as sa60_5v5,
                SAFE_DIVIDE(ff_5v5, toi_5v5) * 3600 as ff60_5v5,
                SAFE_DIVIDE(fa_5v5, toi_5v5) * 3600 as fa60_5v5,
                SAFE_DIVIDE(cf_5v5, cf_5v5 + ca_5v5) * 100 as cf_pct_5v5,
                SAFE_DIVIDE(ff_5v5, ff_5v5 + fa_5v5) * 100 as ff_pct_5v5,
                SAFE_DIVIDE(sf_5v5, sf_5v5 + sa_5v5) * 100 as sf_pct_5v5,
                SAFE_DIVIDE(gf_5v5, gf_5v5 + ga_5v5) * 100 as gf_pct_5v5,
                
                -- Power Play rates
                SAFE_DIVIDE(cf_5v4, toi_5v4) * 3600 as cf60_5v4,
                SAFE_DIVIDE(ca_5v4, toi_5v4) * 3600 as ca60_5v4,
                SAFE_DIVIDE(gf_5v4, toi_5v4) * 3600 as gf60_5v4,
                SAFE_DIVIDE(ga_5v4, toi_5v4) * 3600 as ga60_5v4,
                SAFE_DIVIDE(sf_5v4, toi_5v4) * 3600 as sf60_5v4,
                SAFE_DIVIDE(sa_5v4, toi_5v4) * 3600 as sa60_5v4,
                SAFE_DIVIDE(ff_5v4, toi_5v4) * 3600 as ff60_5v4,
                SAFE_DIVIDE(fa_5v4, toi_5v4) * 3600 as fa60_5v4,
                SAFE_DIVIDE(cf_5v4, cf_5v4 + ca_5v4) * 100 as cf_pct_5v4,
                SAFE_DIVIDE(ff_5v4, ff_5v4 + fa_5v4) * 100 as ff_pct_5v4,
                SAFE_DIVIDE(sf_5v4, sf_5v4 + sa_5v4) * 100 as sf_pct_5v4,
                SAFE_DIVIDE(gf_5v4, gf_5v4 + ga_5v4) * 100 as gf_pct_5v4,
                
                -- Penalty Kill rates
                SAFE_DIVIDE(cf_4v5, toi_4v5) * 3600 as cf60_4v5,
                SAFE_DIVIDE(ca_4v5, toi_4v5) * 3600 as ca60_4v5,
                SAFE_DIVIDE(gf_4v5, toi_4v5) * 3600 as gf60_4v5,
                SAFE_DIVIDE(ga_4v5, toi_4v5) * 3600 as ga60_4v5,
                SAFE_DIVIDE(sf_4v5, toi_4v5) * 3600 as sf60_4v5,
                SAFE_DIVIDE(sa_4v5, toi_4v5) * 3600 as sa60_4v5,
                SAFE_DIVIDE(ff_4v5, toi_4v5) * 3600 as ff60_4v5,
                SAFE_DIVIDE(fa_4v5, toi_4v5) * 3600 as fa60_4v5,
                SAFE_DIVIDE(cf_4v5, cf_4v5 + ca_4v5) * 100 as cf_pct_4v5,
                SAFE_DIVIDE(ff_4v5, ff_4v5 + fa_4v5) * 100 as ff_pct_4v5,
                SAFE_DIVIDE(sf_4v5, sf_4v5 + sa_4v5) * 100 as sf_pct_4v5,
                SAFE_DIVIDE(gf_4v5, gf_4v5 + ga_4v5) * 100 as gf_pct_4v5,
                
                -- Total rates
                SAFE_DIVIDE(cf_total, toi_total) * 3600 as cf60_total,
                SAFE_DIVIDE(ca_total, toi_total) * 3600 as ca60_total,
                SAFE_DIVIDE(gf_total, toi_total) * 3600 as gf60_total,
                SAFE_DIVIDE(ga_total, toi_total) * 3600 as ga60_total,
                SAFE_DIVIDE(sf_total, toi_total) * 3600 as sf60_total,
                SAFE_DIVIDE(sa_total, toi_total) * 3600 as sa60_total,
                SAFE_DIVIDE(ff_total, toi_total) * 3600 as ff60_total,
                SAFE_DIVIDE(fa_total, toi_total) * 3600 as fa60_total,
                SAFE_DIVIDE(cf_total, cf_total + ca_total) * 100 as cf_pct_total,
                SAFE_DIVIDE(ff_total, ff_total + fa_total) * 100 as ff_pct_total,
                SAFE_DIVIDE(sf_total, sf_total + sa_total) * 100 as sf_pct_total,
                SAFE_DIVIDE(gf_total, gf_total + ga_total) * 100 as gf_pct_total
                
            FROM shift_metrics_by_strength
        )
        SELECT 
            *,
            CURRENT_TIMESTAMP() as created_at
        FROM calculated_metrics
        """
        
        # Execute query and load into table
        job_config = bigquery.QueryJobConfig(
            destination=f"{self.dataset_id}.player_shift_metrics_by_strength",
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = self.client.query(query, job_config=job_config)
        job.result()
        
        print("✅ Player shift metrics by strength situation created")
    
    def create_player_game_metrics_by_strength(self, season):
        """Create player game advanced metrics by strength situations."""
        
        print("Creating player game advanced metrics by strength situation...")
        
        query = f"""
        WITH game_metrics_by_strength AS (
            SELECT 
                pgm.player_id,
                pgm.game_id,
                pgm.team_id,
                pgm.season,
                pgm.game_type,
                
                -- Even Strength (5v5) - primary focus for Foster model
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.duration ELSE 0 END) / 60 as toi_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.cf ELSE 0 END) as cf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ca ELSE 0 END) as ca_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.gf ELSE 0 END) as gf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ga ELSE 0 END) as ga_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.sf ELSE 0 END) as sf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.sa ELSE 0 END) as sa_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ff ELSE 0 END) as ff_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.fa ELSE 0 END) as fa_5v5,
                
                -- Power Play (5v4)
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.duration ELSE 0 END) / 60 as toi_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.cf ELSE 0 END) as cf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ca ELSE 0 END) as ca_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.gf ELSE 0 END) as gf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ga ELSE 0 END) as ga_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sf ELSE 0 END) as sf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sa ELSE 0 END) as sa_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ff ELSE 0 END) as ff_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.fa ELSE 0 END) as fa_5v4,
                
                -- Penalty Kill (4v5)
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.duration ELSE 0 END) / 60 as toi_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.cf ELSE 0 END) as cf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ca ELSE 0 END) as ca_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.gf ELSE 0 END) as gf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ga ELSE 0 END) as ga_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sf ELSE 0 END) as sf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sa ELSE 0 END) as sa_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ff ELSE 0 END) as ff_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.fa ELSE 0 END) as fa_4v5,
                
                -- Total metrics
                SUM(psm.duration) / 60 as toi_total,
                SUM(psm.cf) as cf_total,
                SUM(psm.ca) as ca_total,
                SUM(psm.gf) as gf_total,
                SUM(psm.ga) as ga_total,
                SUM(psm.sf) as sf_total,
                SUM(psm.sa) as sa_total,
                SUM(psm.ff) as ff_total,
                SUM(psm.fa) as fa_total
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            WHERE psm.season = {season}
            GROUP BY pgm.player_id, pgm.game_id, pgm.team_id, pgm.season, pgm.game_type
        ),
        calculated_rates AS (
            SELECT 
                *,
                -- 5v5 rates (primary for Foster model)
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
                SAFE_DIVIDE(ff_4v5, ff_4v5 + fa_5v5) * 100 as ff_pct_4v5,
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
                
            FROM game_metrics_by_strength
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
                t.team_id,
                t.team_name,
                {season} as season,
                
                -- Even Strength (5v5) - primary for Foster model
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.cf ELSE 0 END) as cf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ca ELSE 0 END) as ca_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.gf ELSE 0 END) as gf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ga ELSE 0 END) as ga_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.sf ELSE 0 END) as sf_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.sa ELSE 0 END) as sa_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.ff ELSE 0 END) as ff_5v5,
                SUM(CASE WHEN psm.strength_state = '5v5' THEN psm.fa ELSE 0 END) as fa_5v5,
                
                -- Power Play (5v4)
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.cf ELSE 0 END) as cf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ca ELSE 0 END) as ca_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.gf ELSE 0 END) as gf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ga ELSE 0 END) as ga_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sf ELSE 0 END) as sf_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.sa ELSE 0 END) as sa_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.ff ELSE 0 END) as ff_5v4,
                SUM(CASE WHEN psm.strength_state = '5v4' THEN psm.fa ELSE 0 END) as fa_5v4,
                
                -- Penalty Kill (4v5)
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.cf ELSE 0 END) as cf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ca ELSE 0 END) as ca_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.gf ELSE 0 END) as gf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ga ELSE 0 END) as ga_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sf ELSE 0 END) as sf_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.sa ELSE 0 END) as sa_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.ff ELSE 0 END) as ff_4v5,
                SUM(CASE WHEN psm.strength_state = '4v5' THEN psm.fa ELSE 0 END) as fa_4v5,
                
                -- Total metrics
                SUM(psm.cf) as cf_total,
                SUM(psm.ca) as ca_total,
                SUM(psm.gf) as gf_total,
                SUM(psm.ga) as ga_total,
                SUM(psm.sf) as sf_total,
                SUM(psm.sa) as sa_total,
                SUM(psm.ff) as ff_total,
                SUM(psm.fa) as fa_total
                
            FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
            JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON psm.team_id = t.team_id
            JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.game_id
            WHERE g.season = {season}
            GROUP BY t.team_id, t.team_name
        ),
        calculated_percentages AS (
            SELECT 
                *,
                -- 5v5 percentages (primary for Foster model)
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
    """Main function to run strength situation segmentation."""
    
    segmenter = StrengthSituationSegmentation()
    
    # Get current season
    current_year = datetime.now().year
    season = current_year
    
    # Create strength situation segmentation
    segmenter.create_strength_situation_tables(season)
    
    # Get summary
    summary = segmenter.get_strength_situation_summary(season)
    print("\n📊 Strength Situation Summary:")
    print(summary)

if __name__ == "__main__":
    main()
