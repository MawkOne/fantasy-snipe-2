#!/usr/bin/env python3
"""
Elite Player Consistency Analysis

This script analyzes the year-to-year consistency of elite forwards to see how often
they have volatile "up and down" seasons vs consistent performance.
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from typing import Dict, List, Tuple

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def get_elite_player_consistency_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get elite player data with year-to-year consistency metrics."""
    
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
        STDDEV(total_pts) as league_total_pts_std
      FROM player_season_stats
      GROUP BY season
    ),
    player_seasons_with_percentiles AS (
      SELECT 
        pss.*,
        pd.birth_date,
        pd.position,
        pd.full_name,
        -- Calculate age
        CAST(SUBSTR(CAST(pss.season AS STRING), 1, 4) AS INT64) - EXTRACT(YEAR FROM pd.birth_date) as age,
        -- Season-adjusted percentiles
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.total_pts) as total_pts_percentile,
        -- Performance tier
        CASE 
          WHEN PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.total_pts) >= 0.95 THEN 'Elite'
          WHEN PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.total_pts) >= 0.85 THEN 'High'
          WHEN PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.total_pts) >= 0.15 THEN 'Middle'
          ELSE 'Lower'
        END as performance_tier
      FROM player_season_stats pss
      JOIN season_baselines sb ON sb.season = pss.season
      LEFT JOIN `fantasy-snipe-ai.nhl_raw.players` pd ON pd.player_id = pss.player_id
      WHERE pd.position IN ('C', 'L', 'R')  -- Forwards only
    ),
    elite_players AS (
      SELECT DISTINCT player_id, full_name
      FROM player_seasons_with_percentiles
      WHERE performance_tier = 'Elite'
    ),
    elite_seasons AS (
      SELECT 
        pss.player_id,
        pss.season,
        pss.age,
        pss.total_pts,
        pss.total_pts_percentile,
        pss.performance_tier,
        pss.games_played,
        pss.avg_pts_per_game,
        pss.avg_toi_seconds,
        pss.position,
        ep.full_name,
        -- Calculate season order for each player
        ROW_NUMBER() OVER (PARTITION BY pss.player_id ORDER BY pss.season) as season_order,
        -- Previous season stats for comparison
        LAG(pss.total_pts) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_total_pts,
        LAG(pss.total_pts_percentile) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_percentile,
        LAG(pss.performance_tier) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_tier
      FROM player_seasons_with_percentiles pss
      JOIN elite_players ep ON ep.player_id = pss.player_id
    )
    SELECT 
      player_id,
      full_name,
      season,
      age,
      total_pts,
      total_pts_percentile,
      performance_tier,
      season_order,
      prev_total_pts,
      prev_percentile,
      prev_tier,
      -- Calculate year-to-year changes
      total_pts - prev_total_pts as pts_change,
      total_pts_percentile - prev_percentile as percentile_change,
      -- Categorize consistency patterns
      CASE 
        WHEN prev_total_pts IS NULL THEN 'First Elite Season'
        WHEN total_pts_percentile >= 0.95 AND prev_percentile >= 0.95 THEN 'Elite to Elite'
        WHEN total_pts_percentile >= 0.95 AND prev_percentile < 0.95 THEN 'Up to Elite'
        WHEN total_pts_percentile < 0.95 AND prev_percentile >= 0.95 THEN 'Down from Elite'
        WHEN total_pts_percentile >= 0.85 AND prev_percentile >= 0.85 THEN 'High to High'
        WHEN total_pts_percentile >= 0.85 AND prev_percentile < 0.85 THEN 'Up to High'
        WHEN total_pts_percentile < 0.85 AND prev_percentile >= 0.85 THEN 'Down from High'
        ELSE 'Other'
      END as transition_type
    FROM elite_seasons
    ORDER BY player_id, season
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def analyze_elite_consistency_patterns(df: pd.DataFrame) -> Dict:
    """Analyze consistency patterns for elite players."""
    
    results = {}
    
    # Overall transition patterns
    transition_counts = df['transition_type'].value_counts()
    results['transition_patterns'] = transition_counts.to_dict()
    
    # Elite-specific transitions (excluding first seasons)
    elite_transitions = df[df['transition_type'] != 'First Elite Season']
    elite_transition_counts = elite_transitions['transition_type'].value_counts()
    results['elite_transition_patterns'] = elite_transition_counts.to_dict()
    
    # Calculate consistency metrics
    elite_to_elite = len(elite_transitions[elite_transitions['transition_type'] == 'Elite to Elite'])
    total_elite_transitions = len(elite_transitions)
    
    if total_elite_transitions > 0:
        results['elite_consistency_rate'] = elite_to_elite / total_elite_transitions
    else:
        results['elite_consistency_rate'] = 0
    
    # Volatility analysis
    elite_players = df[df['performance_tier'] == 'Elite'].groupby('player_id')
    
    volatility_metrics = []
    for player_id, player_data in elite_players:
        if len(player_data) >= 3:  # Need at least 3 seasons for volatility analysis
            pts_values = player_data['total_pts'].values
            percentile_values = player_data['total_pts_percentile'].values
            
            # Calculate coefficient of variation (standard deviation / mean)
            pts_cv = np.std(pts_values) / np.mean(pts_values) if np.mean(pts_values) > 0 else 0
            percentile_cv = np.std(percentile_values) / np.mean(percentile_values) if np.mean(percentile_values) > 0 else 0
            
            volatility_metrics.append({
                'player_id': player_id,
                'player_name': player_data['full_name'].iloc[0],
                'seasons': len(player_data),
                'pts_cv': pts_cv,
                'percentile_cv': percentile_cv,
                'min_pts': pts_values.min(),
                'max_pts': pts_values.max(),
                'pts_range': pts_values.max() - pts_values.min(),
                'min_percentile': percentile_values.min(),
                'max_percentile': percentile_values.max(),
                'percentile_range': percentile_values.max() - percentile_values.min()
            })
    
    results['volatility_metrics'] = pd.DataFrame(volatility_metrics)
    
    return results

def plot_elite_consistency_analysis(df: pd.DataFrame, volatility_df: pd.DataFrame, save_plots: bool = False) -> None:
    """Create visualizations for elite player consistency analysis."""
    
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Elite Forwards Consistency Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Transition patterns
    ax1 = axes[0, 0]
    transition_counts = df['transition_type'].value_counts()
    transition_counts.plot(kind='bar', ax=ax1, color='skyblue')
    ax1.set_title('Elite Player Season Transitions')
    ax1.set_xlabel('Transition Type')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Points volatility distribution
    ax2 = axes[0, 1]
    if len(volatility_df) > 0:
        ax2.hist(volatility_df['pts_cv'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
        ax2.set_title('Points Volatility Distribution (CV)')
        ax2.set_xlabel('Coefficient of Variation')
        ax2.set_ylabel('Number of Players')
        ax2.grid(True, alpha=0.3)
    
    # Plot 3: Percentile volatility distribution
    ax3 = axes[0, 2]
    if len(volatility_df) > 0:
        ax3.hist(volatility_df['percentile_cv'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax3.set_title('Percentile Volatility Distribution (CV)')
        ax3.set_xlabel('Coefficient of Variation')
        ax3.set_ylabel('Number of Players')
        ax3.grid(True, alpha=0.3)
    
    # Plot 4: Points range vs seasons played
    ax4 = axes[1, 0]
    if len(volatility_df) > 0:
        scatter = ax4.scatter(volatility_df['seasons'], volatility_df['pts_range'], 
                            c=volatility_df['pts_cv'], cmap='viridis', alpha=0.7)
        ax4.set_title('Points Range vs Seasons Played')
        ax4.set_xlabel('Seasons Played')
        ax4.set_ylabel('Points Range (Max - Min)')
        ax4.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax4, label='Coefficient of Variation')
    
    # Plot 5: Most volatile players
    ax5 = axes[1, 1]
    if len(volatility_df) > 0:
        top_volatile = volatility_df.nlargest(10, 'pts_cv')
        bars = ax5.barh(range(len(top_volatile)), top_volatile['pts_cv'], color='orange')
        ax5.set_yticks(range(len(top_volatile)))
        ax5.set_yticklabels(top_volatile['player_name'], fontsize=8)
        ax5.set_title('Most Volatile Elite Players (Top 10)')
        ax5.set_xlabel('Coefficient of Variation')
        ax5.grid(True, alpha=0.3)
    
    # Plot 6: Most consistent players
    ax6 = axes[1, 2]
    if len(volatility_df) > 0:
        top_consistent = volatility_df.nsmallest(10, 'pts_cv')
        bars = ax6.barh(range(len(top_consistent)), top_consistent['pts_cv'], color='green')
        ax6.set_yticks(range(len(top_consistent)))
        ax6.set_yticklabels(top_consistent['player_name'], fontsize=8)
        ax6.set_title('Most Consistent Elite Players (Top 10)')
        ax6.set_xlabel('Coefficient of Variation')
        ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('elite_consistency_analysis.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: elite_consistency_analysis.png")
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Analyze elite player consistency patterns.')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played (default: 20)')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Elite Player Consistency data...")
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Get the data
    df = get_elite_player_consistency_data(client, args.min_games)
    
    print(f"Loaded {len(df)} elite player-season records")
    print(f"Unique elite players: {df['player_id'].nunique()}")
    print(f"Seasons analyzed: {sorted(df['season'].unique())}")
    
    # Analyze consistency patterns
    print("\nAnalyzing elite player consistency patterns...")
    results = analyze_elite_consistency_patterns(df)
    
    # Print transition patterns
    print("\nElite Player Season Transitions:")
    for transition, count in results['transition_patterns'].items():
        print(f"  {transition}: {count}")
    
    print(f"\nElite Consistency Rate: {results['elite_consistency_rate']:.1%}")
    print("(Percentage of elite seasons followed by another elite season)")
    
    # Volatility analysis
    volatility_df = results['volatility_metrics']
    if len(volatility_df) > 0:
        print(f"\nVolatility Analysis (Players with 3+ seasons):")
        print(f"Average Points CV: {volatility_df['pts_cv'].mean():.3f}")
        print(f"Average Percentile CV: {volatility_df['percentile_cv'].mean():.3f}")
        
        print(f"\nMost Volatile Elite Players (Top 5):")
        top_volatile = volatility_df.nlargest(5, 'pts_cv')
        for _, player in top_volatile.iterrows():
            print(f"  {player['player_name']}: CV={player['pts_cv']:.3f}, Range={player['pts_range']:.0f} pts")
        
        print(f"\nMost Consistent Elite Players (Top 5):")
        top_consistent = volatility_df.nsmallest(5, 'pts_cv')
        for _, player in top_consistent.iterrows():
            print(f"  {player['player_name']}: CV={player['pts_cv']:.3f}, Range={player['pts_range']:.0f} pts")
    
    # Create visualizations
    print("\nCreating consistency analysis visualizations...")
    plot_elite_consistency_analysis(df, volatility_df, args.save_plots)
    
    print("\nElite player consistency analysis complete!")

if __name__ == "__main__":
    main()
