#!/usr/bin/env python3
"""
Forwards Total Points Age Curve Analysis

This script analyzes age curves for forwards using total points instead of per-60 metrics.
This avoids the bias where older players get more ice time and inflate their per-60 numbers.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from typing import Dict

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def get_forwards_total_pts_age_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get total points data with age calculations for forwards only."""
    
    query = """
    WITH player_season_stats AS (
      SELECT 
        pgm.player_id,
        pgm.season,
        pgm.game_type,
        COUNT(*) as games_played,
        SUM(pgs.goals + pgs.assists) as total_pts,
        AVG(pgs.goals + pgs.assists) as avg_pts_per_game,
        AVG(pgm.TOI_seconds) as avg_toi_seconds
      FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
      JOIN `fantasy-snipe-ai.nhl_raw.player_game_stats` pgs 
        ON pgs.player_id = pgm.player_id AND pgs.game_id = pgm.game_id
      JOIN `fantasy-snipe-ai.nhl_raw.games` g 
        ON g.id = pgm.game_id
      WHERE pgm.game_type = 2  -- Regular season only
      AND g.game_type = 2
      AND pgs.goals IS NOT NULL 
      AND pgs.assists IS NOT NULL
      GROUP BY pgm.player_id, pgm.season, pgm.game_type
      HAVING COUNT(*) >= @min_games
    ),
    season_baselines AS (
      SELECT 
        season,
        AVG(total_pts) as league_total_pts,
        STDDEV(total_pts) as league_total_pts_std,
        AVG(avg_toi_seconds) as league_toi,
        STDDEV(avg_toi_seconds) as league_toi_std
      FROM player_season_stats
      GROUP BY season
    ),
    adjusted_stats AS (
      SELECT 
        pss.*,
        pd.birth_date,
        pd.position,
        pd.full_name,
        -- Calculate age (season is stored as 20242025, so extract first 4 digits)
        CAST(SUBSTR(CAST(pss.season AS STRING), 1, 4) AS INT64) - EXTRACT(YEAR FROM pd.birth_date) as age,
        -- Season-adjusted metrics (z-scores)
        (pss.total_pts - sb.league_total_pts) / NULLIF(sb.league_total_pts_std, 0) as total_pts_zscore,
        (pss.avg_toi_seconds - sb.league_toi) / NULLIF(sb.league_toi_std, 0) as toi_zscore,
        -- Percentile rankings within season
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.total_pts) as total_pts_percentile
      FROM player_season_stats pss
      JOIN season_baselines sb ON sb.season = pss.season
      LEFT JOIN `fantasy-snipe-ai.nhl_raw.players` pd ON pd.player_id = pss.player_id
    )
    SELECT 
      player_id,
      full_name,
      position,
      season,
      age,
      games_played,
      total_pts,
      avg_pts_per_game,
      avg_toi_seconds,
      total_pts_zscore,
      toi_zscore,
      total_pts_percentile,
      -- Performance tiers (split out Elite and High)
      CASE 
        WHEN total_pts_percentile >= 0.95 THEN 'Elite'
        WHEN total_pts_percentile >= 0.85 THEN 'High'
        WHEN total_pts_percentile >= 0.15 THEN 'Middle'
        ELSE 'Lower'
      END as performance_tier,
      -- Position groups (Center vs Wing)
      CASE 
        WHEN position = 'C' THEN 'Center'
        WHEN position IN ('L', 'R') THEN 'Wing'
        ELSE 'Other'
      END as position_group
    FROM adjusted_stats
    WHERE position IN ('C', 'L', 'R')  -- Forwards only
    AND age BETWEEN 18 AND 40  -- Reasonable age range
    ORDER BY season, total_pts_percentile DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def create_forwards_total_pts_age_curves(df: pd.DataFrame, save_plots: bool = False) -> None:
    """Create focused total points age curve visualizations for forwards with all tiers."""
    
    # Create the plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Forwards Total Points Age Curves - All Tiers', fontsize=16, fontweight='bold')
    
    # Plot 1: All tiers
    ax1 = axes[0, 0]
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = df[df['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')['total_pts'].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 5]  # Minimum 5 players per age
            
            ax1.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=2, label=f'{tier} (n={len(tier_data)})')
    
    ax1.set_xlabel('Age')
    ax1.set_ylabel('Total Points')
    ax1.set_title('Forwards Total Points by Age - All Tiers')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Center vs Wing comparison
    ax2 = axes[0, 1]
    for position in ['Center', 'Wing']:
        pos_data = df[df['position_group'] == position]
        if len(pos_data) > 0:
            age_curve = pos_data.groupby('age')['total_pts'].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 5]
            
            ax2.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=3, label=f'{position} (n={len(pos_data)})')
    
    ax2.set_xlabel('Age')
    ax2.set_ylabel('Total Points')
    ax2.set_title('Center vs Wing Total Points by Age')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Elite and High by position
    ax3 = axes[1, 0]
    for tier in ['Elite', 'High']:
        tier_data = df[df['performance_tier'] == tier]
        for position in ['Center', 'Wing']:
            pos_data = tier_data[tier_data['position_group'] == position]
            if len(pos_data) > 0:
                age_curve = pos_data.groupby('age')['total_pts'].agg(['mean', 'count']).reset_index()
                age_curve = age_curve[age_curve['count'] >= 3]
                
                ax3.plot(age_curve['age'], age_curve['mean'], 
                        marker='o', linewidth=2, label=f'{tier} {position}')
    
    ax3.set_xlabel('Age')
    ax3.set_ylabel('Total Points')
    ax3.set_title('Elite & High Forwards Total Points by Position')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Sample size by age and tier
    ax4 = axes[1, 1]
    age_counts = df.groupby(['age', 'performance_tier']).size().reset_index(name='count')
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_counts = age_counts[age_counts['performance_tier'] == tier]
        ax4.plot(tier_counts['age'], tier_counts['count'], 
                marker='o', linewidth=2, label=f'{tier}')
    
    ax4.set_xlabel('Age')
    ax4.set_ylabel('Number of Players')
    ax4.set_title('Sample Size by Age and Tier (Forwards)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('forwards_total_pts_age_curves.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: forwards_total_pts_age_curves.png")
    
    plt.show()

def identify_early_elite_forwards(df: pd.DataFrame) -> pd.DataFrame:
    """Identify young forwards (18-25) with elite total points indicators."""
    
    # Filter for young forwards with high total points
    young_elite = df[
        (df['age'] >= 18) & 
        (df['age'] <= 25) & 
        (df['total_pts_percentile'] >= 0.8)  # Top 20% in total points
    ].copy()
    
    # Sort by total points percentile descending
    young_elite = young_elite.sort_values('total_pts_percentile', ascending=False)
    
    return young_elite[['full_name', 'age', 'total_pts', 'avg_pts_per_game', 'total_pts_percentile', 'position_group']]

def analyze_forwards_total_pts_peak_ages(df: pd.DataFrame) -> Dict:
    """Analyze peak total points ages by tier and position for forwards."""
    
    results = {}
    
    # By performance tier
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = df[df['performance_tier'] == tier]
        
        # Calculate average total points by age
        age_performance = tier_data.groupby('age')['total_pts'].agg(['mean', 'count']).reset_index()
        age_performance = age_performance[age_performance['count'] >= 3]  # Minimum 3 players
        
        if len(age_performance) > 0:
            peak_age = age_performance.loc[age_performance['mean'].idxmax(), 'age']
            peak_value = age_performance['mean'].max()
            
            results[f'{tier}_total_pts_peak_age'] = peak_age
            results[f'{tier}_total_pts_peak_value'] = peak_value
    
    # By position (Center vs Wing)
    for position in ['Center', 'Wing']:
        pos_data = df[df['position_group'] == position]
        
        # Calculate average total points by age
        age_performance = pos_data.groupby('age')['total_pts'].agg(['mean', 'count']).reset_index()
        age_performance = age_performance[age_performance['count'] >= 3]
        
        if len(age_performance) > 0:
            peak_age = age_performance.loc[age_performance['mean'].idxmax(), 'age']
            peak_value = age_performance['mean'].max()
            
            results[f'{position}_total_pts_peak_age'] = peak_age
            results[f'{position}_total_pts_peak_value'] = peak_value
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze forwards total points age curves.')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played (default: 20)')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Forwards Total Points age data...")
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Get the data
    df = get_forwards_total_pts_age_data(client, args.min_games)
    
    print(f"Loaded {len(df)} forward player-season records")
    print(f"Players: {df['player_id'].nunique()}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    print(f"Age range: {df['age'].min()}-{df['age'].max()}")
    
    # Performance tier distribution
    print("\nPerformance Tier Distribution (Forwards):")
    print(df['performance_tier'].value_counts())
    
    # Position distribution
    print("\nPosition Distribution (Center vs Wing):")
    print(df['position_group'].value_counts())
    
    # Total points statistics by tier
    print("\nTotal Points Statistics by Tier (Forwards):")
    tier_stats = df.groupby('performance_tier')['total_pts'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
    print(tier_stats)
    
    # Total points statistics by position
    print("\nTotal Points Statistics by Position (Center vs Wing):")
    pos_stats = df.groupby('position_group')['total_pts'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
    print(pos_stats)
    
    # Create visualizations
    print("\nCreating Forwards Total Points age curves...")
    create_forwards_total_pts_age_curves(df, args.save_plots)
    
    # Identify early elite forwards
    print("\nIdentifying early elite forwards...")
    early_elite = identify_early_elite_forwards(df)
    print(f"\nFound {len(early_elite)} young forwards with elite total points indicators:")
    print(early_elite.head(20).to_string(index=False))
    
    # Analyze peak ages
    print("\nAnalyzing peak total points ages for forwards...")
    peak_analysis = analyze_forwards_total_pts_peak_ages(df)
    
    print("\nPeak Total Points Age Analysis (Forwards - All Tiers):")
    for key, value in peak_analysis.items():
        if 'peak_age' in key:
            print(f"{key}: {value} years old")
        else:
            print(f"{key}: {value:.1f} total points")
    
    print("\nForwards Total Points age curve analysis complete!")

if __name__ == "__main__":
    main()
