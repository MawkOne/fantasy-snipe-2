#!/usr/bin/env python3
"""
Elite Player Bounce Back Analysis

This script analyzes how often elite players have "bounce back" seasons after lower performance.
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

def get_elite_player_bounceback_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get elite player data with bounce back analysis."""
    
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
    ),
    elite_seasons_with_lag AS (
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
        -- Previous season stats
        LAG(pss.total_pts) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_total_pts,
        LAG(pss.total_pts_percentile) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_percentile,
        LAG(pss.performance_tier) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as prev_tier,
        -- Next season stats
        LEAD(pss.total_pts) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as next_total_pts,
        LEAD(pss.total_pts_percentile) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as next_percentile,
        LEAD(pss.performance_tier) OVER (PARTITION BY pss.player_id ORDER BY pss.season) as next_tier
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
      prev_total_pts,
      prev_percentile,
      prev_tier,
      next_total_pts,
      next_percentile,
      next_tier,
      -- Calculate changes
      total_pts - prev_total_pts as pts_change_from_prev,
      total_pts_percentile - prev_percentile as percentile_change_from_prev,
      next_total_pts - total_pts as pts_change_to_next,
      next_percentile - total_pts_percentile as percentile_change_to_next,
      -- Categorize bounce back patterns
      CASE 
        WHEN prev_total_pts IS NULL THEN 'First Season'
        WHEN total_pts_percentile >= 0.95 AND prev_percentile < 0.95 THEN 'Bounce Back to Elite'
        WHEN total_pts_percentile >= 0.85 AND prev_percentile < 0.85 THEN 'Bounce Back to High'
        WHEN total_pts_percentile >= 0.95 AND prev_percentile >= 0.95 THEN 'Elite to Elite'
        WHEN total_pts_percentile >= 0.85 AND prev_percentile >= 0.85 THEN 'High to High'
        WHEN total_pts_percentile < 0.85 AND prev_percentile >= 0.95 THEN 'Elite to Lower'
        WHEN total_pts_percentile < 0.85 AND prev_percentile >= 0.85 THEN 'High to Lower'
        ELSE 'Other'
      END as bounce_back_type,
      -- Categorize what happens next
      CASE 
        WHEN next_total_pts IS NULL THEN 'Last Season'
        WHEN next_percentile >= 0.95 AND total_pts_percentile < 0.95 THEN 'Bounces Back to Elite'
        WHEN next_percentile >= 0.85 AND total_pts_percentile < 0.85 THEN 'Bounces Back to High'
        WHEN next_percentile >= 0.95 AND total_pts_percentile >= 0.95 THEN 'Stays Elite'
        WHEN next_percentile >= 0.85 AND total_pts_percentile >= 0.85 THEN 'Stays High'
        WHEN next_percentile < 0.85 AND total_pts_percentile >= 0.95 THEN 'Drops from Elite'
        WHEN next_percentile < 0.85 AND total_pts_percentile >= 0.85 THEN 'Drops from High'
        ELSE 'Other'
      END as next_season_outcome
    FROM elite_seasons_with_lag
    ORDER BY player_id, season
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def analyze_bounceback_patterns(df: pd.DataFrame) -> Dict:
    """Analyze bounce back patterns for elite players."""
    
    results = {}
    
    # Overall bounce back patterns
    bounce_counts = df['bounce_back_type'].value_counts()
    results['bounce_back_patterns'] = bounce_counts.to_dict()
    
    # Next season outcomes
    next_outcome_counts = df['next_season_outcome'].value_counts()
    results['next_season_outcomes'] = next_outcome_counts.to_dict()
    
    # Focus on bounce back scenarios
    bounce_back_seasons = df[df['bounce_back_type'].isin(['Bounce Back to Elite', 'Bounce Back to High'])]
    results['bounce_back_seasons'] = len(bounce_back_seasons)
    
    # Calculate bounce back rates
    total_non_first_seasons = len(df[df['bounce_back_type'] != 'First Season'])
    elite_bounce_backs = len(df[df['bounce_back_type'] == 'Bounce Back to Elite'])
    high_bounce_backs = len(df[df['bounce_back_type'] == 'Bounce Back to High'])
    
    results['elite_bounce_back_rate'] = elite_bounce_backs / total_non_first_seasons if total_non_first_seasons > 0 else 0
    results['high_bounce_back_rate'] = high_bounce_backs / total_non_first_seasons if total_non_first_seasons > 0 else 0
    results['total_bounce_back_rate'] = (elite_bounce_backs + high_bounce_backs) / total_non_first_seasons if total_non_first_seasons > 0 else 0
    
    # Analyze what happens after a down season
    down_seasons = df[df['bounce_back_type'].isin(['Elite to Lower', 'High to Lower'])]
    results['down_seasons'] = len(down_seasons)
    
    if len(down_seasons) > 0:
        down_bounce_backs = len(down_seasons[down_seasons['next_season_outcome'].isin(['Bounces Back to Elite', 'Bounces Back to High'])])
        results['down_to_bounce_back_rate'] = down_bounce_backs / len(down_seasons)
    else:
        results['down_to_bounce_back_rate'] = 0
    
    # Player-specific bounce back analysis
    player_bounce_analysis = []
    
    for player_id, player_data in df.groupby('player_id'):
        if len(player_data) >= 3:  # Need at least 3 seasons
            player_name = player_data['full_name'].iloc[0]
            
            # Count bounce backs
            elite_bounce_backs = len(player_data[player_data['bounce_back_type'] == 'Bounce Back to Elite'])
            high_bounce_backs = len(player_data[player_data['bounce_back_type'] == 'Bounce Back to High'])
            total_bounce_backs = elite_bounce_backs + high_bounce_backs
            
            # Count down seasons
            down_seasons = len(player_data[player_data['bounce_back_type'].isin(['Elite to Lower', 'High to Lower'])])
            
            # Count total seasons
            total_seasons = len(player_data)
            
            player_bounce_analysis.append({
                'player_id': player_id,
                'player_name': player_name,
                'total_seasons': total_seasons,
                'elite_bounce_backs': elite_bounce_backs,
                'high_bounce_backs': high_bounce_backs,
                'total_bounce_backs': total_bounce_backs,
                'down_seasons': down_seasons,
                'bounce_back_rate': total_bounce_backs / (total_seasons - 1) if total_seasons > 1 else 0,
                'down_season_rate': down_seasons / (total_seasons - 1) if total_seasons > 1 else 0
            })
    
    results['player_bounce_analysis'] = pd.DataFrame(player_bounce_analysis)
    
    return results

def create_bounceback_charts(df: pd.DataFrame, results: Dict, save_plots: bool = False) -> None:
    """Create charts showing bounce back patterns."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Elite Player Bounce Back Analysis', fontsize=16, fontweight='bold')
    
    # Chart 1: Bounce Back Patterns
    ax1 = axes[0, 0]
    bounce_counts = df['bounce_back_type'].value_counts()
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6']
    bars = ax1.bar(range(len(bounce_counts)), bounce_counts.values, color=colors[:len(bounce_counts)])
    ax1.set_xticks(range(len(bounce_counts)))
    ax1.set_xticklabels(bounce_counts.index, rotation=45, ha='right')
    ax1.set_title('Bounce Back Patterns')
    ax1.set_ylabel('Number of Seasons')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, bounce_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                str(value), ha='center', va='bottom', fontsize=10)
    
    # Chart 2: Next Season Outcomes
    ax2 = axes[0, 1]
    next_counts = df['next_season_outcome'].value_counts()
    colors2 = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6']
    bars2 = ax2.bar(range(len(next_counts)), next_counts.values, color=colors2[:len(next_counts)])
    ax2.set_xticks(range(len(next_counts)))
    ax2.set_xticklabels(next_counts.index, rotation=45, ha='right')
    ax2.set_title('Next Season Outcomes')
    ax2.set_ylabel('Number of Seasons')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars2, next_counts.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                str(value), ha='center', va='bottom', fontsize=10)
    
    # Chart 3: Bounce Back Rate by Player (Top 10)
    ax3 = axes[1, 0]
    player_analysis = results['player_bounce_analysis']
    top_bounce_back_players = player_analysis.nlargest(10, 'bounce_back_rate')
    
    bars3 = ax3.barh(range(len(top_bounce_back_players)), top_bounce_back_players['bounce_back_rate'], 
                     color='lightcoral')
    ax3.set_yticks(range(len(top_bounce_back_players)))
    ax3.set_yticklabels(top_bounce_back_players['player_name'], fontsize=9)
    ax3.set_title('Top 10 Bounce Back Players')
    ax3.set_xlabel('Bounce Back Rate')
    ax3.grid(True, alpha=0.3)
    
    # Chart 4: Down Season Recovery Rate
    ax4 = axes[1, 1]
    
    # Calculate recovery rates
    down_seasons = df[df['bounce_back_type'].isin(['Elite to Lower', 'High to Lower'])]
    if len(down_seasons) > 0:
        recovery_data = down_seasons['next_season_outcome'].value_counts()
        
        # Calculate recovery rate
        total_down = len(down_seasons)
        recovered = len(down_seasons[down_seasons['next_season_outcome'].isin(['Bounces Back to Elite', 'Bounces Back to High'])])
        recovery_rate = recovered / total_down if total_down > 0 else 0
        
        # Create pie chart
        labels = ['Bounced Back', 'Did Not Bounce Back']
        sizes = [recovered, total_down - recovered]
        colors_pie = ['#99ff99', '#ff9999']
        
        wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        ax4.set_title(f'Down Season Recovery Rate\n({recovery_rate:.1%} bounce back)')
    else:
        ax4.text(0.5, 0.5, 'No down seasons found', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Down Season Recovery Rate')
    
    plt.tight_layout()
    
    if save_plots:
        plt.savefig('elite_bounceback_analysis.png', dpi=300, bbox_inches='tight')
        print(f"Saved plot: elite_bounceback_analysis.png")
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Analyze elite player bounce back patterns.')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played (default: 20)')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Elite Player Bounce Back data...")
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Get the data
    df = get_elite_player_bounceback_data(client, args.min_games)
    
    print(f"Loaded {len(df)} elite player-season records")
    print(f"Unique elite players: {df['player_id'].nunique()}")
    
    # Analyze bounce back patterns
    print("\nAnalyzing bounce back patterns...")
    results = analyze_bounceback_patterns(df)
    
    # Print key statistics
    print(f"\nBounce Back Analysis Results:")
    print(f"Total bounce back seasons: {results['bounce_back_seasons']}")
    print(f"Elite bounce back rate: {results['elite_bounce_back_rate']:.1%}")
    print(f"High bounce back rate: {results['high_bounce_back_rate']:.1%}")
    print(f"Total bounce back rate: {results['total_bounce_back_rate']:.1%}")
    
    print(f"\nDown Season Recovery:")
    print(f"Down seasons: {results['down_seasons']}")
    print(f"Down to bounce back rate: {results['down_to_bounce_back_rate']:.1%}")
    
    # Print bounce back patterns
    print(f"\nBounce Back Patterns:")
    for pattern, count in results['bounce_back_patterns'].items():
        print(f"  {pattern}: {count}")
    
    # Print top bounce back players
    player_analysis = results['player_bounce_analysis']
    if len(player_analysis) > 0:
        print(f"\nTop 10 Bounce Back Players:")
        top_bounce_back = player_analysis.nlargest(10, 'bounce_back_rate')
        for _, player in top_bounce_back.iterrows():
            print(f"  {player['player_name']}: {player['bounce_back_rate']:.1%} bounce back rate ({player['total_bounce_backs']} bounce backs in {player['total_seasons']} seasons)")
    
    # Create visualizations
    print("\nCreating bounce back analysis charts...")
    create_bounceback_charts(df, results, args.save_plots)
    
    print("\nElite player bounce back analysis complete!")

if __name__ == "__main__":
    main()
