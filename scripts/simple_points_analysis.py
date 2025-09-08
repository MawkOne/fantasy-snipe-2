#!/usr/bin/env python3
"""
Simple Points Predictors Analysis

This script analyzes what predicts Points in NHL data using a direct database connection.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_points_predictors():
    """Analyze what predicts Points in NHL data"""
    
    try:
        # Try to connect to database using environment variables
        logger.info("🔗 Attempting database connection...")
        
        # Check if we have database credentials
        db_host = os.environ.get('DB_HOST')
        db_name = os.environ.get('DB_NAME')
        db_user = os.environ.get('DB_USER')
        db_pass = os.environ.get('DB_PASS')
        
        if not all([db_host, db_name, db_user, db_pass]):
            logger.warning("⚠️ Database credentials not found in environment variables")
            logger.info("📊 Using mock data for demonstration...")
            return analyze_mock_data()
        
        # Try to connect using psycopg2
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_pass
            )
            
            logger.info("✅ Connected to database successfully")
            
            # Query the data
            query = """
            SELECT 
                pgs.player_id,
                pgs.game_id,
                pgs.goals,
                pgs.assists,
                pgs.points,
                pgs.plus_minus,
                pgs.shots,
                pgs.pim,
                pgs.power_play_goals,
                pgs.power_play_points,
                pgs.game_winning_goals,
                pgs.ot_goals,
                pgs.shorthanded_goals,
                pgs.shorthanded_points,
                pgs.shifts,
                pgs.toi,
                pgamf.CF,
                pgamf.CA,
                pgamf.CF_pct,
                pgamf.FF,
                pgamf.FA,
                pgamf.FF_pct,
                pgamf.SF,
                pgamf.SA,
                pgamf.SF_pct,
                pgamf.GF,
                pgamf.GA,
                pgamf.GF_pct,
                pgamf.CF60,
                pgamf.FF60,
                pgamf.SF60,
                pgamf.GF60,
                pgamf.PDO,
                pgamf.TOI_seconds,
                pgamf.shifts as shifts_adv
            FROM player_game_stats pgs
            LEFT JOIN player_game_advanced_metrics_flat pgamf 
                ON pgs.player_id = pgamf.player_id 
                AND pgs.game_id = pgamf.game_id
            WHERE pgs.points IS NOT NULL
            LIMIT 10000
            """
            
            logger.info("📊 Executing query...")
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"✅ Retrieved {len(df)} records from database")
            
        except ImportError:
            logger.warning("⚠️ psycopg2 not available, using mock data")
            return analyze_mock_data()
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            logger.info("📊 Using mock data for demonstration...")
            return analyze_mock_data()
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        logger.info("📊 Using mock data for demonstration...")
        return analyze_mock_data()
    
    # Analyze the data
    return analyze_data(df)

def analyze_mock_data():
    """Analyze mock data for demonstration"""
    logger.info("📊 Generating mock NHL data...")
    
    # Generate realistic mock data
    np.random.seed(42)
    n_records = 5000
    
    # Generate mock data with realistic correlations
    data = {
        'player_id': np.random.randint(1, 100, n_records),
        'game_id': np.random.randint(1, 1000, n_records),
        'goals': np.random.poisson(0.3, n_records),
        'assists': np.random.poisson(0.4, n_records),
        'points': np.random.poisson(0.7, n_records),
        'plus_minus': np.random.normal(0, 1.5, n_records).round().astype(int),
        'shots': np.random.poisson(2.5, n_records),
        'pim': np.random.poisson(0.5, n_records),
        'power_play_goals': np.random.poisson(0.1, n_records),
        'power_play_points': np.random.poisson(0.2, n_records),
        'game_winning_goals': np.random.poisson(0.05, n_records),
        'ot_goals': np.random.poisson(0.02, n_records),
        'shorthanded_goals': np.random.poisson(0.01, n_records),
        'shorthanded_points': np.random.poisson(0.02, n_records),
        'shifts': np.random.randint(15, 35, n_records),
        'toi': [f"{np.random.randint(8, 25):02d}:{np.random.randint(0, 60):02d}" for _ in range(n_records)],
        'CF': np.random.poisson(15, n_records),
        'CA': np.random.poisson(15, n_records),
        'CF_pct': np.random.uniform(0.3, 0.7, n_records),
        'FF': np.random.poisson(12, n_records),
        'FA': np.random.poisson(12, n_records),
        'FF_pct': np.random.uniform(0.3, 0.7, n_records),
        'SF': np.random.poisson(8, n_records),
        'SA': np.random.poisson(8, n_records),
        'SF_pct': np.random.uniform(0.3, 0.7, n_records),
        'GF': np.random.poisson(2, n_records),
        'GA': np.random.poisson(2, n_records),
        'GF_pct': np.random.uniform(0.3, 0.7, n_records),
        'CF60': np.random.uniform(40, 80, n_records),
        'FF60': np.random.uniform(30, 60, n_records),
        'SF60': np.random.uniform(20, 40, n_records),
        'GF60': np.random.uniform(1, 4, n_records),
        'PDO': np.random.uniform(0.95, 1.05, n_records),
        'TOI_seconds': np.random.randint(300, 1500, n_records),
        'shifts_adv': np.random.randint(15, 35, n_records)
    }
    
    df = pd.DataFrame(data)
    
    # Create realistic correlations
    # Points should correlate with shots, possession metrics, etc.
    df['points'] = (
        df['goals'] + df['assists'] + 
        df['shots'] * 0.1 + 
        df['CF_pct'] * 0.5 + 
        df['FF_pct'] * 0.3 +
        np.random.normal(0, 0.5, n_records)
    ).round().clip(lower=0)
    
    logger.info(f"✅ Generated {len(df)} mock records")
    return analyze_data(df)

def analyze_data(df):
    """Analyze the data to find points predictors"""
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
    
    # Feature importance using linear regression
    print("\n⚖️ FEATURE IMPORTANCE (Linear Regression):")
    print("-" * 40)
    
    try:
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
        
    except ImportError:
        print("⚠️ scikit-learn not available, skipping regression analysis")
    
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
    
    logger.info("✅ Analysis completed successfully")

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