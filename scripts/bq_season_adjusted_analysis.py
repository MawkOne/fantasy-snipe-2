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

def get_season_adjusted_metrics(client: bigquery.Client, min_games: int = 20) -> pd.DataFrame:
    """Get season-adjusted metrics for all players with sufficient games."""
    
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
        AVG(pgm.TOI_seconds) as avg_toi_seconds,
        AVG(pgm.shooting_pct) as avg_shooting_pct,
        AVG(pgm.a60) as avg_a60,
        AVG(pgm.s60) as avg_s60
      FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
      WHERE pgm.game_type = 2  -- Regular season only
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
    )
    SELECT 
      player_id,
      season,
      games_played,
      avg_pts60,
      avg_cf_pct,
      avg_gf60,
      avg_sf60,
      avg_toi_seconds,
      avg_shooting_pct,
      avg_a60,
      avg_s60,
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
      END as performance_tier
    FROM adjusted_stats
    ORDER BY season, pts60_percentile DESC
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_games", "INT64", min_games)
        ]
    )
    
    return client.query(query, job_config=job_config).to_dataframe()

def create_season_analysis(df: pd.DataFrame, metric: str, title: str) -> None:
    """Create season-based analysis visualizations for different performance tiers."""
    
    # Create the plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'{title} - Season Analysis by Performance Tier', fontsize=16, fontweight='bold')
    
    # Plot 1: All tiers by season
    ax1 = axes[0, 0]
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = df[df['performance_tier'] == tier]
        if len(tier_data) > 0:
            season_curve = tier_data.groupby('season')[metric].agg(['mean', 'count']).reset_index()
            season_curve = season_curve[season_curve['count'] >= 5]  # Minimum 5 players per season
            
            ax1.plot(season_curve['season'], season_curve['mean'], 
                    marker='o', linewidth=2, label=f'{tier} (n={len(tier_data)})')
    
    ax1.set_xlabel('Season')
    ax1.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax1.set_title('All Performance Tiers by Season')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Elite vs High tier comparison
    ax2 = axes[0, 1]
    for tier in ['Elite', 'High']:
        tier_data = df[df['performance_tier'] == tier]
        if len(tier_data) > 0:
            season_curve = tier_data.groupby('season')[metric].agg(['mean', 'count']).reset_index()
            season_curve = season_curve[season_curve['count'] >= 3]
            
            ax2.plot(season_curve['season'], season_curve['mean'], 
                    marker='o', linewidth=3, label=f'{tier} Tier')
    
    ax2.set_xlabel('Season')
    ax2.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax2.set_title('Elite vs High Tier Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Distribution by tier
    ax3 = axes[1, 0]
    tier_data = df.groupby('performance_tier')[metric].apply(list)
    ax3.boxplot([tier_data[tier] for tier in ['Elite', 'High', 'Middle', 'Lower']], 
                labels=['Elite', 'High', 'Middle', 'Lower'])
    ax3.set_ylabel(f'{metric.replace("_", " ").title()}')
    ax3.set_title('Distribution by Performance Tier')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Sample size by season
    ax4 = axes[1, 1]
    season_counts = df.groupby(['season', 'performance_tier']).size().reset_index(name='count')
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_counts = season_counts[season_counts['performance_tier'] == tier]
        ax4.plot(tier_counts['season'], tier_counts['count'], 
                marker='o', linewidth=2, label=f'{tier} Tier')
    
    ax4.set_xlabel('Season')
    ax4.set_ylabel('Number of Players')
    ax4.set_title('Sample Size by Season and Tier')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def identify_elite_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Identify players showing elite trajectory indicators."""
    
    # Focus on recent seasons (2020-2025) for current analysis
    recent_players = df[df['season'] >= 20202021].copy()
    
    # Calculate indicators
    elite_indicators = recent_players[
        (recent_players['pts60_percentile'] >= 0.90) |  # Top 10% in PTS60
        (recent_players['cf_pct_percentile'] >= 0.90) |  # Top 10% in CF%
        (recent_players['toi_zscore'] >= 1.5)  # High TOI usage
    ].copy()
    
    # Add improvement trend analysis
    elite_indicators['improvement_trend'] = elite_indicators.groupby('player_id')['pts60_zscore'].transform(
        lambda x: x.diff().mean() if len(x) > 1 else 0
    )
    
    return elite_indicators.sort_values(['season', 'pts60_percentile'], ascending=[False, False])

def analyze_performance_tiers(df: pd.DataFrame) -> Dict:
    """Analyze performance characteristics by tier."""
    
    results = {}
    
    for tier in ['Elite', 'High', 'Middle', 'Lower']:
        tier_data = df[df['performance_tier'] == tier]
        
        if len(tier_data) > 0:
            # Calculate average performance metrics
            results[f'{tier}_avg_pts60_zscore'] = tier_data['pts60_zscore'].mean()
            results[f'{tier}_avg_cf_pct_zscore'] = tier_data['cf_pct_zscore'].mean()
            results[f'{tier}_avg_toi_zscore'] = tier_data['toi_zscore'].mean()
            results[f'{tier}_player_count'] = len(tier_data)
            results[f'{tier}_seasons_covered'] = tier_data['season'].nunique()
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze season-adjusted performance tiers')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games played per season')
    parser.add_argument('--save-plots', action='store_true', help='Save plots to files')
    args = parser.parse_args()
    
    print("Loading season-adjusted player data...")
    client = bigquery.Client()
    df = get_season_adjusted_metrics(client, args.min_games)
    
    print(f"Loaded {len(df)} player-season records")
    print(f"Players: {df['player_id'].nunique()}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    
    # Performance tier distribution
    print("\nPerformance Tier Distribution:")
    print(df['performance_tier'].value_counts())
    
    # Create season analysis for key metrics
    metrics_to_analyze = [
        ('pts60_zscore', 'PTS60 (Season-Adjusted Z-Score)'),
        ('cf_pct_zscore', 'CF% (Season-Adjusted Z-Score)'),
        ('toi_zscore', 'TOI (Season-Adjusted Z-Score)'),
        ('gf60_zscore', 'GF60 (Season-Adjusted Z-Score)')
    ]
    
    for metric, title in metrics_to_analyze:
        print(f"\nCreating season analysis for {metric}...")
        create_season_analysis(df, metric, title)
        
        if args.save_plots:
            plt.savefig(f'season_analysis_{metric}.png', dpi=300, bbox_inches='tight')
            print(f"Saved plot: season_analysis_{metric}.png")
    
    # Identify elite indicators
    print("\nIdentifying elite indicators...")
    elite_indicators = identify_elite_indicators(df)
    
    print(f"\nFound {len(elite_indicators)} players with elite indicators:")
    print(elite_indicators[['player_id', 'season', 'pts60_percentile', 'cf_pct_percentile', 'toi_zscore']].head(20))
    
    # Analyze performance tiers
    print("\nAnalyzing performance tiers...")
    tier_analysis = analyze_performance_tiers(df)
    
    print("\nPerformance Tier Analysis:")
    for key, value in tier_analysis.items():
        print(f"{key}: {value:.3f}" if isinstance(value, float) else f"{key}: {value}")
    
    print("\nSeason-adjusted performance analysis complete!")

if __name__ == "__main__":
    main()
