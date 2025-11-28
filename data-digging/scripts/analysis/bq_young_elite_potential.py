#!/usr/bin/env python3
"""
Young Elite Potential Analysis

This script identifies players under 24 today who are showing promise of being elite players
based on their current performance and trajectory.
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from typing import Dict, List, Tuple
from datetime import datetime

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def get_young_elite_potential_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get data for young players showing elite potential."""
    
    query = """
    WITH player_season_stats AS (
      SELECT 
        pgm.player_id,
        pgm.season,
        pgm.game_type,
        COUNT(*) as games_played,
        SUM(pgs.goals + pgs.assists) as total_pts,
        AVG(pgs.goals + pgs.assists) as avg_pts_per_game,
        AVG(pgm.TOI_seconds) as avg_toi_seconds,
        AVG(pgm.CF_pct) as avg_cf_pct,
        AVG(pgm.GF60) as avg_gf60,
        AVG(pgm.SF60) as avg_sf60
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
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_cf_pct) as cf_pct_percentile,
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_gf60) as gf60_percentile,
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
    current_season AS (
      SELECT MAX(season) as max_season FROM player_season_stats
    ),
    young_players AS (
      SELECT DISTINCT 
        pss.player_id,
        pss.full_name,
        pss.position,
        pss.birth_date,
        -- Calculate current age (assuming 2024-25 season)
        CAST(SUBSTR(CAST(cs.max_season AS STRING), 1, 4) AS INT64) - EXTRACT(YEAR FROM pss.birth_date) as current_age
      FROM player_seasons_with_percentiles pss
      CROSS JOIN current_season cs
      WHERE CAST(SUBSTR(CAST(cs.max_season AS STRING), 1, 4) AS INT64) - EXTRACT(YEAR FROM pss.birth_date) < 24
    )
    SELECT 
      pss.player_id,
      pss.full_name,
      pss.position,
      pss.season,
      pss.age,
      pss.total_pts,
      pss.avg_pts_per_game,
      pss.avg_toi_seconds,
      pss.avg_cf_pct,
      pss.avg_gf60,
      pss.avg_sf60,
      pss.total_pts_percentile,
      pss.cf_pct_percentile,
      pss.gf60_percentile,
      pss.performance_tier,
      yp.current_age
    FROM player_seasons_with_percentiles pss
    JOIN young_players yp ON yp.player_id = pss.player_id
    ORDER BY pss.player_id, pss.season
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def analyze_young_elite_potential(df: pd.DataFrame) -> Dict:
    """Analyze young players for elite potential."""
    
    results = {}
    
    # Get current season data (most recent season)
    current_season = df['season'].max()
    current_data = df[df['season'] == current_season].copy()
    
    # Calculate elite potential metrics
    current_data['elite_potential_score'] = (
        current_data['total_pts_percentile'] * 0.4 +  # 40% weight on points
        current_data['cf_pct_percentile'] * 0.2 +     # 20% weight on possession
        current_data['gf60_percentile'] * 0.2 +       # 20% weight on goal generation
        (current_data['avg_toi_seconds'] / 1200) * 0.2  # 20% weight on ice time (normalized)
    )
    
    # Categorize potential
    current_data['potential_tier'] = pd.cut(
        current_data['elite_potential_score'],
        bins=[0, 0.6, 0.8, 0.9, 1.0],
        labels=['Low', 'Medium', 'High', 'Elite'],
        include_lowest=True
    )
    
    # Get players with high/elite potential
    high_potential = current_data[
        current_data['potential_tier'].isin(['High', 'Elite'])
    ].sort_values('elite_potential_score', ascending=False)
    
    # Analyze trajectory for players with multiple seasons
    trajectory_analysis = []
    
    for player_id, player_data in df.groupby('player_id'):
        if len(player_data) >= 2:  # Need at least 2 seasons for trajectory
            player_name = player_data['full_name'].iloc[0]
            position = player_data['position'].iloc[0]
            current_age = player_data['current_age'].iloc[0]
            
            # Calculate trajectory metrics
            seasons = sorted(player_data['season'].unique())
            pts_trajectory = []
            percentile_trajectory = []
            
            for season in seasons:
                season_data = player_data[player_data['season'] == season]
                if len(season_data) > 0:
                    pts_trajectory.append(season_data['total_pts'].iloc[0])
                    percentile_trajectory.append(season_data['total_pts_percentile'].iloc[0])
            
            if len(pts_trajectory) >= 2:
                # Calculate trend
                pts_trend = np.polyfit(range(len(pts_trajectory)), pts_trajectory, 1)[0]
                percentile_trend = np.polyfit(range(len(percentile_trajectory)), percentile_trajectory, 1)[0]
                
                # Calculate improvement rate
                pts_improvement = (pts_trajectory[-1] - pts_trajectory[0]) / len(pts_trajectory)
                percentile_improvement = (percentile_trajectory[-1] - percentile_trajectory[0]) / len(percentile_trajectory)
                
                trajectory_analysis.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': position,
                    'current_age': current_age,
                    'seasons': len(seasons),
                    'current_pts': pts_trajectory[-1],
                    'current_percentile': percentile_trajectory[-1],
                    'pts_trend': pts_trend,
                    'percentile_trend': percentile_trend,
                    'pts_improvement': pts_improvement,
                    'percentile_improvement': percentile_improvement,
                    'trajectory_score': (pts_trend * 0.5 + percentile_trend * 0.5)
                })
    
    results['current_season'] = current_season
    results['high_potential_players'] = high_potential
    results['trajectory_analysis'] = pd.DataFrame(trajectory_analysis)
    results['current_data'] = current_data
    
    return results

def create_young_elite_charts(df: pd.DataFrame, results: Dict, save_plots: bool = False) -> None:
    """Create charts showing young elite potential."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Young Elite Potential Analysis (Under 24)', fontsize=16, fontweight='bold')
    
    current_data = results['current_data']
    high_potential = results['high_potential_players']
    
    # Chart 1: Elite Potential Score by Age
    ax1 = axes[0, 0]
    scatter = ax1.scatter(current_data['age'], current_data['elite_potential_score'], 
                         c=current_data['total_pts'], cmap='viridis', alpha=0.7, s=60)
    ax1.set_xlabel('Age')
    ax1.set_ylabel('Elite Potential Score')
    ax1.set_title('Elite Potential Score by Age')
    ax1.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Total Points')
    
    # Highlight high potential players
    high_pot = current_data[current_data['potential_tier'].isin(['High', 'Elite'])]
    ax1.scatter(high_pot['age'], high_pot['elite_potential_score'], 
               c='red', s=100, alpha=0.8, marker='*', label='High/Elite Potential')
    ax1.legend()
    
    # Chart 2: Points vs Possession (CF%)
    ax2 = axes[0, 1]
    scatter2 = ax2.scatter(current_data['avg_cf_pct'], current_data['total_pts'], 
                          c=current_data['elite_potential_score'], cmap='plasma', alpha=0.7, s=60)
    ax2.set_xlabel('Corsi For %')
    ax2.set_ylabel('Total Points')
    ax2.set_title('Points vs Possession')
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar2 = plt.colorbar(scatter2, ax=ax2)
    cbar2.set_label('Elite Potential Score')
    
    # Highlight high potential players
    ax2.scatter(high_pot['avg_cf_pct'], high_pot['total_pts'], 
               c='red', s=100, alpha=0.8, marker='*', label='High/Elite Potential')
    ax2.legend()
    
    # Chart 3: Top 15 Elite Potential Players
    ax3 = axes[1, 0]
    top_15 = high_potential.head(15)
    bars = ax3.barh(range(len(top_15)), top_15['elite_potential_score'], 
                    color='lightcoral', alpha=0.8)
    ax3.set_yticks(range(len(top_15)))
    ax3.set_yticklabels([f"{row['full_name']} ({row['age']})" for _, row in top_15.iterrows()], fontsize=9)
    ax3.set_xlabel('Elite Potential Score')
    ax3.set_title('Top 15 Elite Potential Players')
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, top_15['elite_potential_score'])):
        ax3.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                f'{value:.3f}', ha='left', va='center', fontsize=8)
    
    # Chart 4: Trajectory Analysis
    ax4 = axes[1, 1]
    trajectory_df = results['trajectory_analysis']
    if len(trajectory_df) > 0:
        # Plot trajectory scores
        scatter3 = ax4.scatter(trajectory_df['current_age'], trajectory_df['trajectory_score'], 
                              c=trajectory_df['current_pts'], cmap='coolwarm', alpha=0.7, s=60)
        ax4.set_xlabel('Current Age')
        ax4.set_ylabel('Trajectory Score (Improvement Rate)')
        ax4.set_title('Player Development Trajectory')
        ax4.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar3 = plt.colorbar(scatter3, ax=ax4)
        cbar3.set_label('Current Points')
        
        # Highlight positive trajectories
        positive_traj = trajectory_df[trajectory_df['trajectory_score'] > 0]
        if len(positive_traj) > 0:
            ax4.scatter(positive_traj['current_age'], positive_traj['trajectory_score'], 
                       c='green', s=100, alpha=0.8, marker='^', label='Positive Trajectory')
            ax4.legend()
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('young_elite_potential_analysis.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: young_elite_potential_analysis.png")
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Analyze young elite potential players.')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played (default: 20)')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Young Elite Potential data...")
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Get the data
    df = get_young_elite_potential_data(client, args.min_games)
    
    print(f"Loaded {len(df)} young player-season records")
    print(f"Unique young players: {df['player_id'].nunique()}")
    print(f"Seasons analyzed: {sorted(df['season'].unique())}")
    
    # Analyze young elite potential
    print("\nAnalyzing young elite potential...")
    results = analyze_young_elite_potential(df)
    
    current_season = results['current_season']
    high_potential = results['high_potential_players']
    trajectory_df = results['trajectory_analysis']
    
    print(f"\nCurrent Season: {current_season}")
    print(f"Players under 24 analyzed: {len(df['player_id'].unique())}")
    
    # Print high potential players
    print(f"\nTop 20 Elite Potential Players (Under 24):")
    print("=" * 80)
    for i, (_, player) in enumerate(high_potential.head(20).iterrows(), 1):
        print(f"{i:2d}. {player['full_name']:20s} | Age: {player['age']:2d} | "
              f"Pts: {player['total_pts']:3.0f} | Percentile: {player['total_pts_percentile']:5.1%} | "
              f"Potential: {player['elite_potential_score']:.3f} | Tier: {player['potential_tier']}")
    
    # Print trajectory analysis
    if len(trajectory_df) > 0:
        print(f"\nTop 15 Rising Young Players (Positive Trajectory):")
        print("=" * 80)
        rising_players = trajectory_df[trajectory_df['trajectory_score'] > 0].nlargest(15, 'trajectory_score')
        for i, (_, player) in enumerate(rising_players.iterrows(), 1):
            print(f"{i:2d}. {player['player_name']:20s} | Age: {player['current_age']:2d} | "
                  f"Current Pts: {player['current_pts']:3.0f} | Trend: {player['trajectory_score']:+.3f} | "
                  f"Seasons: {player['seasons']}")
    
    # Position breakdown
    print(f"\nHigh Potential Players by Position:")
    position_breakdown = high_potential['position'].value_counts()
    for pos, count in position_breakdown.items():
        print(f"  {pos}: {count} players")
    
    # Age breakdown
    print(f"\nHigh Potential Players by Age:")
    age_breakdown = high_potential['age'].value_counts().sort_index()
    for age, count in age_breakdown.items():
        print(f"  Age {age}: {count} players")
    
    # Create visualizations
    print("\nCreating young elite potential charts...")
    create_young_elite_charts(df, results, args.save_plots)
    
    print("\nYoung elite potential analysis complete!")

if __name__ == "__main__":
    main()
