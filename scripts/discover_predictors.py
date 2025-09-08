#!/usr/bin/env python3
"""
Discover multi-metric predictors for NHL Goals, Assists, and Points (excluding target metrics).

- Pulls per-game skater data joined with advanced metrics for a given NHL season code (e.g., 20242025)
- Excludes target columns (goals, assists, points) from predictors appropriately
- Trains multiple models (LassoCV for sparse combos; RandomForest for non-linear importance)
- Reports strongest feature combinations and cross-validated R^2

Usage:
  python scripts/discover_predictors.py --season 20242025 --limit 50000

Env:
  NHL_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB?sslmode=require
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if not url:
        raise RuntimeError("NHL_DATABASE_URL not set. Please add it to .env")
    return create_engine(url, pool_pre_ping=True)


def fetch_dataset(engine, season: int, limit: int) -> pd.DataFrame:
    # Per-game skater metrics (regular season only)
    query = f"""
    SELECT
      pgs.player_id,
      pgs.game_id,
      g.season,
      g.game_type,
      -- targets
      pgs.goals,
      pgs.assists,
      pgs.points,
      -- basic
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
      -- advanced flat
      adv."CF", adv."CA",
      adv."FF", adv."FA",
      adv."SF", adv."SA",
      adv."GF", adv."GA",
      adv."CF_pct", adv."FF_pct", adv."SF_pct", adv."GF_pct",
      adv."CF60", adv."FF60", adv."SF60", adv."GF60",
      adv."PDO",
      adv."TOI_seconds",
      adv.shifts as shifts_adv
    FROM player_game_stats pgs
    JOIN games g ON g.id = pgs.game_id
    JOIN player_game_advanced_metrics_flat adv
      ON adv.player_id = pgs.player_id AND adv.game_id = pgs.game_id
    WHERE g.season = {season} AND g.game_type = 2
    LIMIT {limit}
    """
    df = pd.read_sql_query(query, engine)
    return df


def parse_toi(toi_str: str) -> float:
    if not toi_str or pd.isna(toi_str):
        return 0.0
    try:
        parts = str(toi_str).split(":")
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
        return minutes + seconds / 60.0
    except Exception:
        return 0.0


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    # Derived metrics
    df = df.copy()
    df['toi_minutes'] = df['toi'].apply(parse_toi)
    df['shot_attempts'] = df['CF']
    df['unblocked_attempts'] = df['FF']
    # Percentages not available in flat table; derive approximations where possible
    df['shot_attempt_percentage'] = np.where((df['CF'] + df['CA']) > 0, df['CF'] / (df['CF'] + df['CA']), np.nan)
    df['unblocked_attempt_percentage'] = np.where((df['FF'] + df['FA']) > 0, df['FF'] / (df['FF'] + df['FA']), np.nan)
    df['shot_percentage'] = np.where((df['SF'] + df['SA']) > 0, df['SF'] / (df['SF'] + df['SA']), np.nan)
    df['goal_percentage'] = np.where((df['GF'] + df['GA']) > 0, df['GF'] / (df['GF'] + df['GA']), np.nan)
    df['shot_attempts_per_60'] = df['CF60']
    df['unblocked_attempts_per_60'] = df['FF60']
    df['shots_per_60'] = df['SF60']
    df['goals_per_60'] = df['GF60']
    df['shooting_efficiency'] = np.where(df['shots'] > 0, df['goals'] / df['shots'], 0)
    df['shot_attempt_efficiency'] = np.where(df['shot_attempts'] > 0, df['shots'] / df['shot_attempts'], 0)
    return df


def build_predictor_list(df: pd.DataFrame, target: str) -> List[str]:
    base = [
        'plus_minus', 'shots', 'pim', 'power_play_goals', 'power_play_points',
        'game_winning_goals', 'ot_goals', 'shorthanded_goals', 'shorthanded_points',
        'shifts', 'toi_minutes', 'TOI_seconds',
        'CF','CA','CF_pct','FF','FA','FF_pct','SF','SA','SF_pct','GF','GA','GF_pct',
        'CF60','FF60','SF60','GF60','PDO',
        'shot_attempts','unblocked_attempts','shot_attempt_percentage','unblocked_attempt_percentage',
        'shot_percentage','goal_percentage','shot_attempts_per_60','unblocked_attempts_per_60','shots_per_60',
        'goals_per_60','shooting_efficiency','shot_attempt_efficiency'
    ]
    # Exclude target columns directly
    exclude = set()
    if target == 'goals':
        exclude.update(['goals'])
    elif target == 'assists':
        exclude.update(['assists'])
    elif target == 'points':
        exclude.update(['points','goals','assists'])
    predictors = [c for c in base if c in df.columns and c not in exclude]
    return predictors


def fit_models(df: pd.DataFrame, predictors: List[str], target: str) -> Tuple[dict, dict]:
    X = df[predictors].fillna(0)
    y = df[target].fillna(0)

    # Lasso for sparse combos
    lasso = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LassoCV(cv=5, random_state=42, n_jobs=None, max_iter=10000))
    ])

    lasso.fit(X, y)
    lasso_cv_scores = cross_val_score(lasso, X, y, cv=5, scoring='r2')
    # Extract non-zero features
    coefs = lasso.named_steps['model'].coef_ if hasattr(lasso.named_steps['model'], 'coef_') else np.array([])
    non_zero = [(feat, coef) for feat, coef in zip(predictors, coefs) if abs(coef) > 1e-6]
    non_zero_sorted = sorted(non_zero, key=lambda x: abs(x[1]), reverse=True)

    lasso_result = {
        'cv_r2_mean': float(np.mean(lasso_cv_scores)),
        'cv_r2_std': float(np.std(lasso_cv_scores)),
        'selected_features': non_zero_sorted[:15]
    }

    # Random Forest for non-linear importance
    rf = RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1, max_depth=None)
    rf_scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
    rf.fit(X, y)
    importances = list(zip(predictors, rf.feature_importances_))
    importances_sorted = sorted(importances, key=lambda x: x[1], reverse=True)

    rf_result = {
        'cv_r2_mean': float(np.mean(rf_scores)),
        'cv_r2_std': float(np.std(rf_scores)),
        'top_features': importances_sorted[:15]
    }

    return lasso_result, rf_result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Discover multi-metric predictors for NHL targets')
    parser.add_argument('--season', type=int, default=20242025)
    parser.add_argument('--limit', type=int, default=50000)
    args = parser.parse_args()

    engine = get_engine()
    logger.info(f"Loading data for season {args.season} (limit {args.limit})...")
    df = fetch_dataset(engine, args.season, args.limit)
    if df.empty:
        print("No data returned from DB.")
        return

    df = prepare_features(df)
    # Drop rows with missing targets
    df = df.dropna(subset=['goals','assists','points'])

    for target in ['goals','assists','points']:
        logger.info(f"\n=== Target: {target.upper()} (excluding target metrics) ===")
        predictors = build_predictor_list(df, target)
        if not predictors:
            print(f"No predictors available for {target}")
            continue
        lasso_res, rf_res = fit_models(df, predictors, target)

        print(f"\nTarget: {target.upper()}")
        print(f"LassoCV R^2 (mean±std): {lasso_res['cv_r2_mean']:.3f} ± {lasso_res['cv_r2_std']:.3f}")
        print("Selected combo (Lasso, top 10):")
        for feat, coef in lasso_res['selected_features'][:10]:
            print(f"  - {feat:30s} coef={coef:+.3f}")

        print(f"\nRandomForest R^2 (mean±std): {rf_res['cv_r2_mean']:.3f} ± {rf_res['cv_r2_std']:.3f}")
        print("Top features (RF, top 10):")
        for feat, imp in rf_res['top_features'][:10]:
            print(f"  - {feat:30s} importance={imp:.4f}")


if __name__ == "__main__":
    main()


