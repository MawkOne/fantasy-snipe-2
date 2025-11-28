#!/usr/bin/env python3
"""
Elite Player Volatility Charts

This script creates focused charts showing the most volatile and most consistent elite players.
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

def get_elite_player_season_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get elite player season data for volatility analysis."""
    
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
      JOIN `fantasy-snipe-ai.nhl_raw.players` pd ON pd.player_id = pss.player_id
      WHERE pd.position IN ('C', 'L', 'R')  -- Forwards only
    ),
    elite_players AS (
      SELECT DISTINCT player_id, full_name
      FROM player_seasons_with_percentiles
      WHERE performance_tier = 'Elite'
    )
    SELECT 
      pss.player_id,
      pss.full_name,
      pss.season,
      pss.age,
      pss.total_pts,
      pss.total_pts_percentile,
      pss.performance_tier,
      pss.games_played,
      pss.avg_pts_per_game
    FROM player_seasons_with_percentiles pss
    JOIN elite_players ep ON ep.player_id = pss.player_id
    ORDER BY pss.player_id, pss.season
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def calculate_volatility_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate volatility metrics for each elite player."""
    
    volatility_metrics = []
    
    for player_id, player_data in df.groupby('player_id'):
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
                'percentile_range': percentile_values.max() - percentile_values.min(),
                'avg_pts': np.mean(pts_values),
                'std_pts': np.std(pts_values)
            })
    
    return pd.DataFrame(volatility_metrics)

def create_volatility_charts(df: pd.DataFrame, volatility_df: pd.DataFrame, save_plots: bool = False) -> None:
    """Create focused charts for most volatile and most consistent elite players."""
    
    # Get top 10 most volatile and most consistent players
    top_volatile = volatility_df.nlargest(10, 'pts_cv')
    top_consistent = volatility_df.nsmallest(10, 'pts_cv')
    
    # Create the plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    fig.suptitle('Elite Forwards: Volatility vs Consistency', fontsize=16, fontweight='bold')
    
    # Chart 1: Most Volatile Elite Players
    ax1.set_title('Most Volatile Elite Players (Top 10)', fontsize=14, fontweight='bold')
    
    # Plot each volatile player's season progression
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top_volatile)))
    
    for i, (_, player) in enumerate(top_volatile.iterrows()):
        player_data = df[df['player_id'] == player['player_id']].sort_values('season')
        
        # Plot the line
        ax1.plot(player_data['season'], player_data['total_pts'], 
                marker='o', linewidth=2, markersize=6, 
                color=colors[i], alpha=0.8, 
                label=f"{player['player_name']} (CV: {player['pts_cv']:.3f})")
        
        # Add player name annotation
        ax1.annotate(player['player_name'], 
                    xy=(player_data['season'].iloc[-1], player_data['total_pts'].iloc[-1]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.8)
    
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Total Points')
    ax1.grid(True, alpha=0.3)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # Chart 2: Most Consistent Elite Players
    ax2.set_title('Most Consistent Elite Players (Top 10)', fontsize=14, fontweight='bold')
    
    # Plot each consistent player's season progression
    colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(top_consistent)))
    
    for i, (_, player) in enumerate(top_consistent.iterrows()):
        player_data = df[df['player_id'] == player['player_id']].sort_values('season')
        
        # Plot the line
        ax2.plot(player_data['season'], player_data['total_pts'], 
                marker='o', linewidth=2, markersize=6, 
                color=colors[i], alpha=0.8, 
                label=f"{player['player_name']} (CV: {player['pts_cv']:.3f})")
        
        # Add player name annotation
        ax2.annotate(player['player_name'], 
                    xy=(player_data['season'].iloc[-1], player_data['total_pts'].iloc[-1]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.8)
    
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Total Points')
    ax2.grid(True, alpha=0.3)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('elite_volatility_vs_consistency.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: elite_volatility_vs_consistency.png")
    
    plt.show()

def create_volatility_comparison_chart(volatility_df: pd.DataFrame, save_plots: bool = False) -> None:
    """Create a comparison chart showing volatility distribution."""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Elite Player Volatility Analysis', fontsize=16, fontweight='bold')
    
    # Chart 1: Volatility Distribution
    ax1.hist(volatility_df['pts_cv'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(volatility_df['pts_cv'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'Mean CV: {volatility_df["pts_cv"].mean():.3f}')
    ax1.axvline(volatility_df['pts_cv'].median(), color='orange', linestyle='--', linewidth=2, 
                label=f'Median CV: {volatility_df["pts_cv"].median():.3f}')
    ax1.set_title('Distribution of Volatility (Coefficient of Variation)')
    ax1.set_xlabel('Coefficient of Variation')
    ax1.set_ylabel('Number of Players')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Chart 2: Volatility vs Average Points
    scatter = ax2.scatter(volatility_df['avg_pts'], volatility_df['pts_cv'], 
                         c=volatility_df['seasons'], cmap='viridis', alpha=0.7, s=60)
    ax2.set_title('Volatility vs Average Points')
    ax2.set_xlabel('Average Points per Season')
    ax2.set_ylabel('Coefficient of Variation')
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Number of Seasons')
    
    # Add trend line
    z = np.polyfit(volatility_df['avg_pts'], volatility_df['pts_cv'], 1)
    p = np.poly1d(z)
    ax2.plot(volatility_df['avg_pts'], p(volatility_df['avg_pts']), 
             "r--", alpha=0.8, linewidth=2, label='Trend Line')
    ax2.legend()
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('elite_volatility_distribution.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: elite_volatility_distribution.png")
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Create elite player volatility charts.')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played (default: 20)')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Elite Player data...")
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Get the data
    df = get_elite_player_season_data(client, args.min_games)
    
    print(f"Loaded {len(df)} elite player-season records")
    print(f"Unique elite players: {df['player_id'].nunique()}")
    
    # Calculate volatility metrics
    print("Calculating volatility metrics...")
    volatility_df = calculate_volatility_metrics(df)
    
    print(f"Analyzed {len(volatility_df)} elite players with 3+ seasons")
    print(f"Average volatility (CV): {volatility_df['pts_cv'].mean():.3f}")
    print(f"Median volatility (CV): {volatility_df['pts_cv'].median():.3f}")
    
    # Print top volatile and consistent players
    print("\nMost Volatile Elite Players (Top 5):")
    top_volatile = volatility_df.nlargest(5, 'pts_cv')
    for _, player in top_volatile.iterrows():
        print(f"  {player['player_name']}: CV={player['pts_cv']:.3f}, Range={player['pts_range']:.0f} pts, Avg={player['avg_pts']:.1f}")
    
    print("\nMost Consistent Elite Players (Top 5):")
    top_consistent = volatility_df.nsmallest(5, 'pts_cv')
    for _, player in top_consistent.iterrows():
        print(f"  {player['player_name']}: CV={player['pts_cv']:.3f}, Range={player['pts_range']:.0f} pts, Avg={player['avg_pts']:.1f}")
    
    # Create charts
    print("\nCreating volatility vs consistency charts...")
    create_volatility_charts(df, volatility_df, args.save_plots)
    
    print("\nCreating volatility distribution charts...")
    create_volatility_comparison_chart(volatility_df, args.save_plots)
    
    print("\nElite player volatility analysis complete!")

if __name__ == "__main__":
    main()
