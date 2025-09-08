#!/usr/bin/env python3
"""
Analyze Points Predictors in NHL Database

This script queries the Google Cloud NHL database to find the best predictors
for Points (excluding goals and assists) using the available metrics.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_points_predictors():
    """Analyze what predicts Points in NHL data"""
    
    try:
        # Import database connection and models
        from database.connection import get_session
        from database.models import Player, PlayerGameStats, Game, Team, PlayerGameAdvancedMetricsFlat
        
        logger.info("🔗 Connecting to NHL database...")
        session = get_session()
        
        # Query player game stats with advanced metrics
        logger.info("📊 Querying player game data...")
        
        # Get a sample of recent games with advanced metrics
        query = session.query(
            PlayerGameStats.player_id,
            PlayerGameStats.game_id,
            PlayerGameStats.goals,
            PlayerGameStats.assists,
            PlayerGameStats.points,
            PlayerGameStats.plus_minus,
            PlayerGameStats.shots,
            PlayerGameStats.pim,
            PlayerGameStats.power_play_goals,
            PlayerGameStats.power_play_points,
            PlayerGameStats.game_winning_goals,
            PlayerGameStats.ot_goals,
            PlayerGameStats.shorthanded_goals,
            PlayerGameStats.shorthanded_points,
            PlayerGameStats.shifts,
            PlayerGameStats.toi,
            PlayerGameAdvancedMetricsFlat.CF,
            PlayerGameAdvancedMetricsFlat.CA,
            PlayerGameAdvancedMetricsFlat.CF_pct,
            PlayerGameAdvancedMetricsFlat.FF,
            PlayerGameAdvancedMetricsFlat.FA,
            PlayerGameAdvancedMetricsFlat.FF_pct,
            PlayerGameAdvancedMetricsFlat.SF,
            PlayerGameAdvancedMetricsFlat.SA,
            PlayerGameAdvancedMetricsFlat.SF_pct,
            PlayerGameAdvancedMetricsFlat.GF,
            PlayerGameAdvancedMetricsFlat.GA,
            PlayerGameAdvancedMetricsFlat.GF_pct,
            PlayerGameAdvancedMetricsFlat.CF60,
            PlayerGameAdvancedMetricsFlat.FF60,
            PlayerGameAdvancedMetricsFlat.SF60,
            PlayerGameAdvancedMetricsFlat.GF60,
            PlayerGameAdvancedMetricsFlat.PDO,
            PlayerGameAdvancedMetricsFlat.TOI_seconds,
            PlayerGameAdvancedMetricsFlat.shifts
        ).join(
            PlayerGameAdvancedMetricsFlat,
            (PlayerGameStats.player_id == PlayerGameAdvancedMetricsFlat.player_id) &
            (PlayerGameStats.game_id == PlayerGameAdvancedMetricsFlat.game_id)
        ).limit(10000)  # Limit to 10k records for analysis
        
        logger.info("📈 Executing query...")
        results = query.all()
        
        if not results:
            logger.error("❌ No data found in database")
            return
        
        logger.info(f"✅ Retrieved {len(results)} game records")
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=[
            'player_id', 'game_id', 'goals', 'assists', 'points', 'plus_minus',
            'shots', 'pim', 'power_play_goals', 'power_play_points', 'game_winning_goals',
            'ot_goals', 'shorthanded_goals', 'shorthanded_points', 'shifts', 'toi',
            'CF', 'CA', 'CF_pct', 'FF', 'FA', 'FF_pct', 'SF', 'SA', 'SF_pct',
            'GF', 'GA', 'GF_pct', 'CF60', 'FF60', 'SF60', 'GF60', 'PDO',
            'TOI_seconds', 'shifts_adv'
        ])
        
        # Clean and prepare data
        logger.info("🧹 Cleaning and preparing data...")
        
        # Parse time on ice to minutes
        df['toi_minutes'] = df['toi'].apply(parse_toi)
        
        # Calculate additional metrics
        df['shot_attempts'] = df['CF']  # Corsi For = shot attempts
        df['unblocked_attempts'] = df['FF']  # Fenwick For = unblocked attempts
        df['shot_attempt_percentage'] = df['CF_pct']
        df['unblocked_attempt_percentage'] = df['FF_pct']
        df['shot_percentage'] = df['SF_pct']
        df['goal_percentage'] = df['GF_pct']
        
        # Calculate rates per 60 minutes
        df['shot_attempts_per_60'] = df['CF60']
        df['unblocked_attempts_per_60'] = df['FF60']
        df['shots_per_60'] = df['SF60']
        df['goals_per_60'] = df['GF60']
        
        # Calculate efficiency metrics
        df['shooting_percentage'] = np.where(df['shots'] > 0, df['goals'] / df['shots'], 0)
        df['shot_attempt_efficiency'] = np.where(df['shot_attempts'] > 0, df['shots'] / df['shot_attempts'], 0)
        
        # Remove rows with missing data
        df = df.dropna(subset=['points', 'CF', 'FF', 'SF'])
        
        logger.info(f"✅ Cleaned data: {len(df)} records remaining")
        
        # Define potential predictors (excluding goals and assists)
        predictors = [
            # Basic stats
            'plus_minus', 'shots', 'pim', 'power_play_goals', 'power_play_points',
            'game_winning_goals', 'ot_goals', 'shorthanded_goals', 'shorthanded_points',
            'shifts', 'toi_minutes',
            
            # Advanced metrics
            'CF', 'CA', 'CF_pct', 'FF', 'FA', 'FF_pct', 'SF', 'SA', 'SF_pct',
            'GF', 'GA', 'GF_pct', 'PDO', 'TOI_seconds',
            
            # Calculated metrics
            'shot_attempts', 'unblocked_attempts', 'shot_attempt_percentage',
            'unblocked_attempt_percentage', 'shot_percentage', 'goal_percentage',
            'shot_attempts_per_60', 'unblocked_attempts_per_60', 'shots_per_60',
            'goals_per_60', 'shooting_percentage', 'shot_attempt_efficiency'
        ]
        
        # Filter to only include columns that exist in the data
        available_predictors = [p for p in predictors if p in df.columns]
        
        logger.info(f"📊 Analyzing {len(available_predictors)} potential predictors...")
        
        # Calculate correlations with points
        correlations = {}
        for predictor in available_predictors:
            if predictor in df.columns:
                corr = df[predictor].corr(df['points'])
                correlations[predictor] = corr
        
        # Sort by absolute correlation
        sorted_correlations = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Display results
        print("\n🏒 NHL Points Predictors Analysis")
        print("=" * 60)
        print(f"📊 Data: {len(df)} game records")
        print(f"🎯 Target: Points (excluding goals and assists)")
        print(f"📈 Predictors analyzed: {len(available_predictors)}")
        print()
        
        print("🏆 TOP 10 PREDICTORS FOR POINTS:")
        print("-" * 40)
        for i, (predictor, corr) in enumerate(sorted_correlations[:10]):
            direction = "positive" if corr > 0 else "negative"
            print(f"{i+1:2d}. {predictor:30s} | {corr:6.3f} ({direction})")
        
        print("\n📊 CORRELATION BREAKDOWN BY CATEGORY:")
        print("-" * 40)
        
        # Group by category
        categories = {
            'Basic Stats': ['plus_minus', 'shots', 'pim', 'power_play_goals', 'power_play_points', 
                          'game_winning_goals', 'ot_goals', 'shorthanded_goals', 'shorthanded_points'],
            'Time Metrics': ['shifts', 'toi_minutes', 'TOI_seconds'],
            'Possession (Corsi)': ['CF', 'CA', 'CF_pct', 'shot_attempts', 'shot_attempt_percentage', 'shot_attempts_per_60'],
            'Unblocked (Fenwick)': ['FF', 'FA', 'FF_pct', 'unblocked_attempts', 'unblocked_attempt_percentage', 'unblocked_attempts_per_60'],
            'Shots': ['SF', 'SA', 'SF_pct', 'shot_percentage', 'shots_per_60'],
            'Goals': ['GF', 'GA', 'GF_pct', 'goal_percentage', 'goals_per_60'],
            'Efficiency': ['PDO', 'shooting_percentage', 'shot_attempt_efficiency']
        }
        
        for category, metrics in categories.items():
            category_corrs = [(m, correlations.get(m, 0)) for m in metrics if m in correlations]
            if category_corrs:
                print(f"\n{category}:")
                for metric, corr in sorted(category_corrs, key=lambda x: abs(x[1]), reverse=True):
                    direction = "positive" if corr > 0 else "negative"
                    print(f"  • {metric:25s} | {corr:6.3f} ({direction})")
        
        # Statistical significance analysis
        print("\n🔬 STATISTICAL SIGNIFICANCE:")
        print("-" * 40)
        
        # Calculate p-values for top correlations
        from scipy import stats
        
        significant_predictors = []
        for predictor, corr in sorted_correlations[:10]:
            if predictor in df.columns:
                # Calculate correlation and p-value
                corr_coef, p_value = stats.pearsonr(df[predictor].dropna(), df['points'].dropna())
                significant_predictors.append((predictor, corr_coef, p_value))
        
        print("Top predictors with p-values:")
        for predictor, corr, p_value in significant_predictors:
            significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
            print(f"  • {predictor:25s} | {corr:6.3f} | p={p_value:.4f} {significance}")
        
        # Feature importance using linear regression
        print("\n⚖️ FEATURE IMPORTANCE (Linear Regression):")
        print("-" * 40)
        
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        
        # Prepare data for regression
        X = df[available_predictors].fillna(0)
        y = df['points']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Fit linear regression
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Get feature importance (coefficients)
        feature_importance = dict(zip(available_predictors, model.coef_))
        sorted_importance = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
        
        print("Top 10 most important features:")
        for i, (feature, importance) in enumerate(sorted_importance[:10]):
            direction = "positive" if importance > 0 else "negative"
            print(f"{i+1:2d}. {feature:30s} | {importance:6.3f} ({direction})")
        
        # Model performance
        y_pred = model.predict(X_scaled)
        r2 = model.score(X_scaled, y)
        
        print(f"\n📈 MODEL PERFORMANCE:")
        print(f"  R² Score: {r2:.3f}")
        print(f"  Explained Variance: {r2*100:.1f}%")
        
        # Summary insights
        print("\n💡 KEY INSIGHTS:")
        print("-" * 40)
        
        top_predictor = sorted_correlations[0]
        print(f"• Best predictor: {top_predictor[0]} (correlation: {top_predictor[1]:.3f})")
        
        # Find strongest positive and negative correlations
        positive_corrs = [(p, c) for p, c in sorted_correlations if c > 0]
        negative_corrs = [(p, c) for p, c in sorted_correlations if c < 0]
        
        if positive_corrs:
            best_positive = positive_corrs[0]
            print(f"• Strongest positive: {best_positive[0]} (correlation: {best_positive[1]:.3f})")
        
        if negative_corrs:
            best_negative = negative_corrs[0]
            print(f"• Strongest negative: {best_negative[0]} (correlation: {best_negative[1]:.3f})")
        
        # Category insights
        possession_corrs = [c for p, c in sorted_correlations if 'CF' in p or 'FF' in p or 'possession' in p.lower()]
        if possession_corrs:
            avg_possession = np.mean([abs(c) for c in possession_corrs])
            print(f"• Possession metrics average correlation: {avg_possession:.3f}")
        
        time_corrs = [c for p, c in sorted_correlations if 'toi' in p.lower() or 'time' in p.lower()]
        if time_corrs:
            avg_time = np.mean([abs(c) for c in time_corrs])
            print(f"• Time metrics average correlation: {avg_time:.3f}")
        
        session.close()
        logger.info("✅ Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def parse_toi(toi_str):
    """Parse time on ice string to minutes"""
    if not toi_str or pd.isna(toi_str):
        return 0.0
    try:
        parts = toi_str.split(':')
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes + seconds / 60.0
    except:
        return 0.0

if __name__ == "__main__":
    analyze_points_predictors() 