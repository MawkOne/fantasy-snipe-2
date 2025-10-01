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

def get_season_adjusted_metrics_with_age(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get season-adjusted metrics with age calculations."""
    
    query = """
    WITH player_season_stats AS (
      SELECT 
        pgm.player_id,
        pgm.season,
        pgm.game_type,
        COUNT(*) as games_played,
        AVG(pgm.pts60) as avg_pts60,
        AVG(pgm.cf_pct) as avg_cf_pct,
        AVG(pgm.gf60) as avg_gf60,
        AVG(pgm.sf60) as avg_sf60,
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
        AVG(avg_cf_pct) as league_cf_pct,
        STDDEV(avg_cf_pct) as league_cf_pct_std,
        AVG(avg_gf60) as league_gf60,
        STDDEV(avg_gf60) as league_gf60_std,
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
        (pss.avg_cf_pct - sb.league_cf_pct) / NULLIF(sb.league_cf_pct_std, 0) as cf_pct_zscore,
        (pss.avg_gf60 - sb.league_gf60) / NULLIF(sb.league_gf60_std, 0) as gf60_zscore,
        (pss.avg_toi_seconds - sb.league_toi) / NULLIF(sb.league_toi_std, 0) as toi_zscore,
        -- Percentile rankings within season
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_pts60) as pts60_percentile,
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_cf_pct) as cf_pct_percentile,
        PERCENT_RANK() OVER (PARTITION BY pss.season ORDER BY pss.avg_gf60) as gf60_percentile
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
      avg_cf_pct,
      avg_gf60,
      avg_sf60,
      avg_toi_seconds,
      pts60_zscore,
      cf_pct_zscore,
      gf60_zscore,
      toi_zscore,
      pts60_percentile,
      cf_pct_percentile,
      gf60_percentile,
      -- Performance tiers based on season percentiles
      CASE 
        WHEN pts60_percentile >= 0.95 THEN 'Elite'
        WHEN pts60_percentile >= 0.85 THEN 'High'
        WHEN pts60_percentile >= 0.15 THEN 'Middle'
        ELSE 'Lower'
      END as performance_tier,
      -- Position groups
      CASE 
        WHEN position IN ('C', 'L', 'R') THEN 'Forward'
        WHEN position = 'D' THEN 'Defence'
        WHEN position = 'G' THEN 'Goalie'
        ELSE 'Other'
      END as position_group
    FROM adjusted_stats
    WHERE age BETWEEN 18 AND 40  -- Reasonable age range
    ORDER BY season, pts60_percentile DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def create_age_curves(df: pd.DataFrame, metric: str, title: str) -> None:
    """Create age curve visualizations for different performance tiers."""
    
    # Filter out goalies for most metrics
    if metric != 'toi_zscore':
        plot_df = df[df['position_group'] != 'Goalie'].copy()
    else:
        plot_df = df.copy()
    
    # Create the plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'{title} - Age Curves by Performance Tier', fontsize=16, fontweight='bold')
    
    # Plot 1: All tiers together
    ax1 = axes[0, 0]
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = plot_df[plot_df['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')[metric].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 5]  # Minimum 5 players per age
            
            ax1.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=2, label=f'{tier} (n={len(tier_data)})')
    
    ax1.set_xlabel('Age')
    ax1.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax1.set_title('All Performance Tiers')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Elite vs High tier comparison
    ax2 = axes[0, 1]
    for tier in ['Elite', 'High']:
        tier_data = plot_df[plot_df['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')[metric].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 3]
            
            ax2.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=3, label=f'{tier} Tier')
    
    ax2.set_xlabel('Age')
    ax2.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax2.set_title('Elite vs High Tier Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Position-specific (Forwards only)
    ax3 = axes[1, 0]
    forward_data = plot_df[plot_df['position_group'] == 'Forward']
    for tier in ['Elite', 'High', 'Middle']:
        tier_data = forward_data[forward_data['performance_tier'] == tier]
        if len(tier_data) > 0:
            age_curve = tier_data.groupby('age')[metric].agg(['mean', 'count']).reset_index()
            age_curve = age_curve[age_curve['count'] >= 3]
            
            ax3.plot(age_curve['age'], age_curve['mean'], 
                    marker='o', linewidth=2, label=f'{tier} Forwards')
    
    ax3.set_xlabel('Age')
    ax3.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax3.set_title('Forwards Only')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Sample size by age
    ax4 = axes[1, 1]
    age_counts = plot_df.groupby(['age', 'performance_tier']).size().reset_index(name='count')
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_counts = age_counts[age_counts['performance_tier'] == tier]
        ax4.plot(tier_counts['age'], tier_counts['count'], 
                marker='o', linewidth=2, label=f'{tier} Tier')
    
    ax4.set_xlabel('Age')
    ax4.set_ylabel('Number of Players')
    ax4.set_title('Sample Size by Age and Tier')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def identify_early_elite_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Identify young players showing elite trajectory indicators."""
    
    # Focus on players aged 18-25
    young_players = df[df['age'].between(18, 25)].copy()
    
    # Calculate indicators
    early_elite = young_players[
        (young_players['pts60_percentile'] >= 0.90) |  # Top 10% in PTS60
        (young_players['cf_pct_percentile'] >= 0.90) |  # Top 10% in CF%
        (young_players['toi_zscore'] >= 1.5)  # High TOI usage
    ].copy()
    
    # Add career trajectory analysis
    early_elite['improvement_trend'] = early_elite.groupby('player_id')['pts60_zscore'].transform(
        lambda x: x.diff().mean() if len(x) > 1 else 0
    )
    
    return early_elite.sort_values(['age', 'pts60_percentile'], ascending=[True, False])

def analyze_peak_ages(df: pd.DataFrame) -> Dict:
    """Analyze peak performance ages by tier and position."""
    
    results = {}
    
    for tier in ['Elite', 'High', 'Middle']:
        tier_data = df[df['performance_tier'] == tier]
        
        # Calculate average performance by age
        age_performance = tier_data.groupby('age').agg({
            'pts60_zscore': 'mean',
            'cf_pct_zscore': 'mean',
            'toi_zscore': 'mean'
        }).reset_index()
        
        # Find peak ages
        for metric in ['pts60_zscore', 'cf_pct_zscore', 'toi_zscore']:
            peak_age = age_performance.loc[age_performance[metric].idxmax(), 'age']
            peak_value = age_performance[metric].max()
            
            results[f'{tier}_{metric}_peak_age'] = peak_age
            results[f'{tier}_{metric}_peak_value'] = peak_value
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze age curves with season-adjusted metrics')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played per season')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading season-adjusted player data with age calculations...")
    client = bigquery.Client()
    df = get_season_adjusted_metrics_with_age(client, args.min_games)
    
    print(f"Loaded {len(df)} player-season records")
    print(f"Players: {df['player_id'].nunique()}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    print(f"Age range: {df['age'].min()}-{df['age'].max()}")
    
    # Performance tier distribution
    print("\nPerformance Tier Distribution:")
    print(df['performance_tier'].value_counts())
    
    # Create age curves for key metrics
    metrics_to_analyze = [
        ('pts60_zscore', 'PTS60 (Season-Adjusted Z-Score)'),
        ('cf_pct_zscore', 'CF% (Season-Adjusted Z-Score)'),
        ('toi_zscore', 'TOI (Season-Adjusted Z-Score)'),
        ('gf60_zscore', 'GF60 (Season-Adjusted Z-Score)')
    ]
    
    for metric, title in metrics_to_analyze:
        print(f"\nCreating age curves for {metric}...")
        create_age_curves(df, metric, title)
        
        if args.save_plots:
            plt.savefig(f'age_curves_{metric}.png', dpi=300, bbox_inches='tight')
            print(f"Saved plot: age_curves_{metric}.png")
    
    # Identify early elite indicators
    print("\nIdentifying early elite indicators...")
    early_elite = identify_early_elite_indicators(df)
    
    print(f"\nFound {len(early_elite)} young players with elite indicators:")
    print(early_elite[['full_name', 'age', 'season', 'pts60_percentile', 'cf_pct_percentile', 'toi_zscore']].head(20))
    
    # Analyze peak ages
    print("\nAnalyzing peak performance ages...")
    peak_analysis = analyze_peak_ages(df)
    
    print("\nPeak Age Analysis:")
    for key, value in peak_analysis.items():
        if 'peak_age' in key:
            print(f"{key}: {value}")
    
    print("\nAge curve analysis complete!")

if __name__ == "__main__":
    main()
