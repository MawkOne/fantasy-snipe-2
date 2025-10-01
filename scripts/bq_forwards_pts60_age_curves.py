import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def get_forwards_pts60_age_data(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get PTS/60 data with age calculations for forwards only."""
    
    query = """
    WITH player_season_stats AS (
      SELECT 
        pgm.player_id,
        pgm.season,
        pgm.game_type,
        COUNT(*) as games_played,
        AVG(pgm.pts60) as avg_pts60,
        AVG(pgm.TOI_seconds) as avg_toi_seconds
      FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
      WHERE pgm.game_type = 2  -- Regular season only
      AND pgm.pts60 IS NOT NULL
      AND pgm.pts60 > 0
      GROUP BY pgm.player_id, pgm.season, pgm.game_type
      HAVING COUNT(*) >= @min_games
    ),
    season_baselines AS (
      SELECT 
        season,
        AVG(avg_pts60) as league_pts60,
        STDDEV(avg_pts60) as league_pts60_std,
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
        (pss.avg_pts60 - sb.league_pts60) / NULLIF(sb.league_pts60_std, 0) as pts60_zscore,
        (pss.avg_toi_seconds - sb.league_toi) / NULLIF(sb.league_toi_std, 0) as toi_zscore,
        -- Percentile rankings within season
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_pts60) as pts60_percentile
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
      avg_pts60,
      avg_toi_seconds,
      pts60_zscore,
      toi_zscore,
      pts60_percentile,
      -- Performance tiers based on season percentiles
      CASE 
        WHEN pts60_percentile >= 0.95 THEN 'Elite'
        WHEN pts60_percentile >= 0.85 THEN 'High'
        WHEN pts60_percentile >= 0.15 THEN 'Middle'
        ELSE 'Lower'
      END as performance_tier,
      -- Position groups (forwards only)
      CASE 
        WHEN position = 'C' THEN 'Center'
        WHEN position = 'L' THEN 'Left Wing'
        WHEN position = 'R' THEN 'Right Wing'
        ELSE 'Other'
      END as position_group
    FROM adjusted_stats
    WHERE age BETWEEN 18 AND 40  -- Reasonable age range
    AND position IN ('C', 'L', 'R')  -- Forwards only
    ORDER BY season, pts60_percentile DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def create_forwards_pts60_age_curves(df: pd.DataFrame) -> None:
    """Create focused PTS/60 age curve visualizations for forwards only."""
    
    # Create the plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Forwards PTS/60 Age Curves by Performance Tier', fontsize=16, fontweight='bold')
    
    # Plot 1: All tiers together
    ax1 = axes[0, 0]
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = df[df['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')['avg_pts60'].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 5]  # Minimum 5 players per age
            
            ax1.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=2, label=f'{tier} (n={len(tier_data)})')
    
    ax1.set_xlabel('Age')
    ax1.set_ylabel('PTS/60')
    ax1.set_title('Forwards PTS/60 by Age - All Performance Tiers')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Elite vs High tier comparison
    ax2 = axes[0, 1]
    for tier in ['Elite', 'High']:
        tier_data = df[df['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')['avg_pts60'].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 3]
            
            ax2.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=3, label=f'{tier} Tier')
    
    ax2.set_xlabel('Age')
    ax2.set_ylabel('PTS/60')
    ax2.set_title('Elite vs High Tier Forwards PTS/60')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Position-specific (Center vs Wing)
    ax3 = axes[1, 0]
    for position in ['Center', 'Left Wing', 'Right Wing']:
        pos_data = df[df['position_group'] == position]
        if len(pos_data) > 0:
            age_curve = pos_data.groupby('age')['avg_pts60'].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 3]
            
            ax3.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=2, label=f'{position}')
    
    ax3.set_xlabel('Age')
    ax3.set_ylabel('PTS/60')
    ax3.set_title('Forwards PTS/60 by Position')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Sample size by age
    ax4 = axes[1, 1]
    age_counts = df.groupby(['age', 'performance_tier']).size().reset_index(name='count')
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_counts = age_counts[age_counts['performance_tier'] == tier]
        ax4.plot(tier_counts['age'], tier_counts['count'], 
                marker='o', linewidth=2, label=f'{tier} Tier')
    
    ax4.set_xlabel('Age')
    ax4.set_ylabel('Number of Players')
    ax4.set_title('Sample Size by Age and Tier (Forwards)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def identify_early_elite_forwards(df: pd.DataFrame) -> pd.DataFrame:
    """Identify young forwards showing elite PTS/60 trajectory indicators."""
    
    # Focus on players aged 18-25
    young_players = df[df['age'].between(18, 25)].copy()
    
    # Calculate indicators
    early_elite = young_players[
        (young_players['pts60_percentile'] >= 0.90) |  # Top 10% in PTS60
        (young_players['avg_pts60'] >= 2.0)  # High absolute PTS/60
    ].copy()
    
    # Add career trajectory analysis
    early_elite['improvement_trend'] = early_elite.groupby('player_id')['pts60_zscore'].transform(
        lambda x: x.diff().mean() if len(x) > 1 else 0
    )
    
    return early_elite.sort_values(['age', 'pts60_percentile'], ascending=[True, False])

def analyze_forwards_pts60_peak_ages(df: pd.DataFrame) -> Dict:
    """Analyze peak PTS/60 ages by tier and position for forwards."""
    
    results = {}
    
    # By performance tier
    for tier in ['Elite', 'High', 'Middle']:
        tier_data = df[df['performance_tier'] == tier]
        
        # Calculate average PTS/60 by age
        age_performance = tier_data.groupby('age')['avg_pts60'].agg(['mean', 'count']).reset_index()
        age_performance = age_performance[age_performance['count'] >= 3]  # Minimum 3 players
        
        if len(age_performance) > 0:
            peak_age = age_performance.loc[age_performance['mean'].idxmax(), 'age']
            peak_value = age_performance['mean'].max()
            
            results[f'{tier}_pts60_peak_age'] = peak_age
            results[f'{tier}_pts60_peak_value'] = peak_value
    
    # By position
    for position in ['Center', 'Left Wing', 'Right Wing']:
        pos_data = df[df['position_group'] == position]
        
        # Calculate average PTS/60 by age
        age_performance = pos_data.groupby('age')['avg_pts60'].agg(['mean', 'count']).reset_index()
        age_performance = age_performance[age_performance['count'] >= 3]  # Minimum 3 players
        
        if len(age_performance) > 0:
            peak_age = age_performance.loc[age_performance['mean'].idxmax(), 'age']
            peak_value = age_performance['mean'].max()
            
            results[f'{position}_pts60_peak_age'] = peak_age
            results[f'{position}_pts60_peak_value'] = peak_value
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze Forwards PTS/60 age curves')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played per season')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading Forwards PTS/60 age data...")
    client = bigquery.Client()
    df = get_forwards_pts60_age_data(client, args.min_games)
    
    print(f"Loaded {len(df)} forward player-season records")
    print(f"Players: {df['player_id'].nunique()}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    print(f"Age range: {df['age'].min()}-{df['age'].max()}")
    
    # Performance tier distribution
    print("\nPerformance Tier Distribution (Forwards):")
    print(df['performance_tier'].value_counts())
    
    # Position distribution
    print("\nPosition Distribution (Forwards):")
    print(df['position_group'].value_counts())
    
    # PTS/60 statistics by tier
    print("\nPTS/60 Statistics by Tier (Forwards):")
    tier_stats = df.groupby('performance_tier')['avg_pts60'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
    print(tier_stats)
    
    # PTS/60 statistics by position
    print("\nPTS/60 Statistics by Position (Forwards):")
    pos_stats = df.groupby('position_group')['avg_pts60'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
    print(pos_stats)
    
    # Create PTS/60 age curves
    print("\nCreating Forwards PTS/60 age curves...")
    create_forwards_pts60_age_curves(df)
    
    if args.save_plots:
        plt.savefig('forwards_pts60_age_curves.png', dpi=300, bbox_inches='tight')
        print("Saved plot: forwards_pts60_age_curves.png")
    
    # Identify early elite indicators
    print("\nIdentifying early elite forwards...")
    early_elite = identify_early_elite_forwards(df)
    
    print(f"\nFound {len(early_elite)} young forwards with elite PTS/60 indicators:")
    print(early_elite[['full_name', 'age', 'season', 'avg_pts60', 'pts60_percentile', 'position_group']].head(20))
    
    # Analyze peak ages
    print("\nAnalyzing peak PTS/60 ages for forwards...")
    peak_analysis = analyze_forwards_pts60_peak_ages(df)
    
    print("\nPeak PTS/60 Age Analysis (Forwards):")
    for key, value in peak_analysis.items():
        if 'peak_age' in key:
            print(f"{key}: {value} years old")
        else:
            print(f"{key}: {value:.2f} PTS/60")
    
    print("\nForwards PTS/60 age curve analysis complete!")

if __name__ == "__main__":
    main()
