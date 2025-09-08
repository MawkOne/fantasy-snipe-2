#!/usr/bin/env python3
"""
Analyze importance of factors across strengths (EV/PP/SH) for Goals, Assists, Points.

Features:
- Shots on goal (estimated per strength via TOI share; exact shot strength mapping requires event-strength alignment)
- Time on ice per strength (from player_shift_metrics)
- Who they play with (teammate diversity and concentration from teammates_on_ice_ids)
- Shot location (overall avg distance/angle from game_events coordinates)
- Player age at game date (from player_details.birth_date)
- Advanced metrics (overall per-game from player_game_advanced_metrics_flat)

Models:
- LassoCV for sparse combos
- RandomForestRegressor for non-linear importance
- Optionally computes simple composite formulas and evaluates their predictive power

Usage:
  python scripts/analyze_strength_predictors.py --season 20242025 --limit 50000

Env:
  NHL_DATABASE_URL=postgresql://USER:PASS@HOST:PORT/postgres?sslmode=require
"""

import os
import sys
import math
import json
import logging
from typing import Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from sklearn.model_selection import cross_val_score, GroupKFold
from sklearn.linear_model import LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if not url:
        raise RuntimeError("NHL_DATABASE_URL not set in environment")
    return create_engine(url, pool_pre_ping=True)


def parse_toi_str(toi: str) -> float:
    if not toi or pd.isna(toi):
        return 0.0
    try:
        m, s = str(toi).split(":")
        return int(m) + int(s) / 60.0
    except Exception:
        return 0.0


def fetch_core(engine, season: int, limit: int) -> pd.DataFrame:
    # Core per-game skater stats and advanced
    q = f"""
    SELECT pgs.player_id, pgs.game_id, g.season, g.game_type,
           pgs.goals, pgs.assists, pgs.points, pgs.shots, pgs.plus_minus, pgs.toi,
           adv."CF", adv."FF", adv."SF", adv."GF", adv."CA", adv."FA", adv."SA", adv."GA",
           adv."CF60", adv."FF60", adv."SF60", adv."GF60", adv."PDO", adv."TOI_seconds"
    FROM player_game_stats pgs
    JOIN games g ON g.id = pgs.game_id
    LEFT JOIN player_game_advanced_metrics_flat adv
      ON adv.player_id = pgs.player_id AND adv.game_id = pgs.game_id
    WHERE g.season = {season} AND g.game_type = 2
    LIMIT {limit}
    """
    return pd.read_sql_query(q, engine)


def fetch_shifts(engine, season: int, player_game_keys: List[tuple]) -> pd.DataFrame:
    # Pull strength-state TOI and teammate info from shift metrics for the passed keys
    # Build temp table of keys to reduce scanning
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS tmp_player_games")
        conn.exec_driver_sql("CREATE TEMP TABLE tmp_player_games(player_id INT, game_id INT)")
        # Bulk insert keys
        if player_game_keys:
            values = ",".join([f"({pid},{gid})" for pid, gid in player_game_keys])
            conn.exec_driver_sql(f"INSERT INTO tmp_player_games VALUES {values}")
        q = text("""
            SELECT sm.player_id, sm.game_id, sm.strength_state,
                   COUNT(*) AS shift_rows,
                   SUM(
                     CASE WHEN position(':' in sm.duration) > 0 THEN
                       CAST(split_part(sm.duration, ':', 1) AS INT) * 60 + CAST(split_part(sm.duration, ':', 2) AS INT)
                     ELSE 0 END
                   ) AS duration_seconds,
                   AVG(COALESCE(sm.teammates_on_ice, 5)) AS teammates_on_ice_avg,
                   -- approximate unique teammates via count of distinct teammate arrays string
                   COUNT(DISTINCT COALESCE(sm.teammates_on_ice_ids::text,'')) AS teammate_line_variants
            FROM player_shift_metrics sm
            JOIN tmp_player_games t ON t.player_id = sm.player_id AND t.game_id = sm.game_id
            GROUP BY sm.player_id, sm.game_id, sm.strength_state
        """)
        df = pd.read_sql_query(q, conn)
    return df


def fetch_shot_locations(engine, season: int, player_game_keys: List[tuple]) -> pd.DataFrame:
    # Approx overall shot location features from game_events
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS tmp_player_games2")
        conn.exec_driver_sql("CREATE TEMP TABLE tmp_player_games2(player_id INT, game_id INT)")
        if player_game_keys:
            values = ",".join([f"({pid},{gid})" for pid, gid in player_game_keys])
            conn.exec_driver_sql(f"INSERT INTO tmp_player_games2 VALUES {values}")
        q = text("""
            SELECT e.primary_player_id AS player_id, e.game_id,
                   AVG(ABS(COALESCE(e.coordinates_x,0))) AS avg_abs_x,
                   AVG(SQRT(POWER(COALESCE(e.coordinates_x,0),2) + POWER(COALESCE(e.coordinates_y,0),2))) AS avg_dist,
                   COUNT(*) FILTER (WHERE e.event_type IN ('SHOT','GOAL')) AS shot_events
            FROM game_events e
            JOIN tmp_player_games2 t ON t.player_id = e.primary_player_id AND t.game_id = e.game_id
            WHERE e.event_type IN ('SHOT','GOAL')
            GROUP BY e.primary_player_id, e.game_id
        """)
        df = pd.read_sql_query(q, conn)
    return df


def fetch_shot_strength_features(engine, season: int, player_game_keys: List[tuple]) -> pd.DataFrame:
    # Join events to shifts by period and time window to infer strength at shot time
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS tmp_player_games3")
        conn.exec_driver_sql("CREATE TEMP TABLE tmp_player_games3(player_id INT, game_id INT)")
        if player_game_keys:
            values = ",".join([f"({pid},{gid})" for pid, gid in player_game_keys])
            conn.exec_driver_sql(f"INSERT INTO tmp_player_games3 VALUES {values}")
        q = text("""
            WITH ev AS (
              SELECT e.primary_player_id AS player_id,
                     e.game_id,
                     e.period,
                     CASE WHEN position(':' in e.period_time) > 0 THEN
                       CAST(split_part(e.period_time, ':', 1) AS INT) * 60 + CAST(split_part(e.period_time, ':', 2) AS INT)
                     ELSE 0 END AS evt_sec,
                     e.event_type,
                     COALESCE(e.coordinates_x,0) AS x,
                     COALESCE(e.coordinates_y,0) AS y
              FROM game_events e
              JOIN tmp_player_games3 t ON t.player_id = e.primary_player_id AND t.game_id = e.game_id
              WHERE e.event_type IN ('SHOT','GOAL')
            )
            SELECT ev.player_id, ev.game_id, sm.strength_state,
                   COUNT(*) FILTER (WHERE ev.event_type='SHOT') AS shots_true,
                   COUNT(*) FILTER (WHERE ev.event_type='GOAL') AS goals_true,
                   AVG(SQRT(POWER(ev.x,2) + POWER(ev.y,2))) AS avg_dist,
                   AVG(ABS(ev.x)) AS avg_abs_x,
                   AVG(1.0 / (1.0 + EXP((SQRT(POWER(ev.x,2) + POWER(ev.y,2)) - 25.0)/5.0))) AS xg_proxy
            FROM ev
            JOIN player_shift_metrics sm
              ON sm.player_id = ev.player_id
             AND sm.game_id = ev.game_id
             AND sm.period = ev.period
             AND (
               CASE WHEN position(':' in sm.start_time) > 0 THEN
                 CAST(split_part(sm.start_time, ':', 1) AS INT) * 60 + CAST(split_part(sm.start_time, ':', 2) AS INT)
               ELSE 0 END
             ) <= ev.evt_sec
             AND ev.evt_sec <= (
               CASE WHEN position(':' in sm.end_time) > 0 THEN
                 CAST(split_part(sm.end_time, ':', 1) AS INT) * 60 + CAST(split_part(sm.end_time, ':', 2) AS INT)
               ELSE 0 END
             )
            GROUP BY ev.player_id, ev.game_id, sm.strength_state
        """)
        df = pd.read_sql_query(q, conn)
    return df


def fetch_player_age(engine, player_ids: List[int], game_dates: Dict[int, pd.Timestamp]) -> pd.DataFrame:
    # Compute age per player-game using player_details.birth_date and games.game_date
    ids_csv = ",".join(str(i) for i in sorted(set(player_ids)) or [0])
    q = f"""
    SELECT pd.player_id, pd.birth_date
    FROM player_details pd
    WHERE pd.player_id IN ({ids_csv})
    """
    df = pd.read_sql_query(q, engine)
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    return df


def build_dataset(engine, season: int, limit: int) -> pd.DataFrame:
    core = fetch_core(engine, season, limit)
    if core.empty:
        return core
    # Parse TOI
    core['toi_minutes'] = core['toi'].apply(parse_toi_str)

    # Prepare keys
    keys = list(zip(core['player_id'].astype(int), core['game_id'].astype(int)))

    # Shifts / strengths
    shifts = fetch_shifts(engine, season, keys)
    # Pivot strengths into columns
    pivot = shifts.pivot_table(index=['player_id','game_id'], columns='strength_state', values='duration_seconds', aggfunc='sum').fillna(0)
    pivot.columns = [f"toi_{c}_sec" for c in pivot.columns]
    features = core.merge(pivot.reset_index(), on=['player_id','game_id'], how='left')

    # Add teammate features
    teammates = shifts.groupby(['player_id','game_id']).agg(
        teammate_variants=('teammate_line_variants','sum'),
        teammates_on_ice_avg=('teammates_on_ice_avg','mean')
    ).reset_index()
    features = features.merge(teammates, on=['player_id','game_id'], how='left')

    # Shot location features
    shots_loc = fetch_shot_locations(engine, season, keys)
    features = features.merge(shots_loc, on=['player_id','game_id'], how='left')

    # True shot/goal counts and distances by strength
    shot_strength = fetch_shot_strength_features(engine, season, keys)
    shot_pivot_ct = shot_strength.pivot_table(index=['player_id','game_id'], columns='strength_state', values=['shots_true','goals_true'], aggfunc='sum').fillna(0)
    # Flatten columns
    shot_pivot_ct.columns = [f"{a}_{b}" for a, b in shot_pivot_ct.columns]
    features = features.merge(shot_pivot_ct.reset_index(), on=['player_id','game_id'], how='left')
    # Strength-specific distances
    shot_pivot_dist = shot_strength.pivot_table(index=['player_id','game_id'], columns='strength_state', values=['avg_dist','avg_abs_x','xg_proxy'], aggfunc='mean')
    shot_pivot_dist.columns = [f"{a}_{b}" for a, b in shot_pivot_dist.columns]
    features = features.merge(shot_pivot_dist.reset_index(), on=['player_id','game_id'], how='left')

    # Age features
    # Map game dates
    game_dates = {int(row['game_id']): pd.NaT for _, row in core[['game_id']].drop_duplicates().iterrows()}
    # Fetch game_date
    gdf = pd.read_sql_query(f"SELECT id, game_date FROM games WHERE season={season} AND game_type=2", engine)
    gdf['game_date'] = pd.to_datetime(gdf['game_date'], errors='coerce')
    game_date_map = dict(zip(gdf['id'].astype(int), gdf['game_date']))
    features['game_date'] = features['game_id'].map(game_date_map)
    # Ensure datetime
    features['game_date'] = pd.to_datetime(features['game_date'], errors='coerce')

    # Player birthdays
    ages = fetch_player_age(engine, features['player_id'].tolist(), game_date_map)
    birth_map = dict(zip(ages['player_id'], ages['birth_date']))
    features['birth_date'] = pd.to_datetime(features['player_id'].map(birth_map), errors='coerce')
    # Age in years (safe)
    age_days = (features['game_date'] - features['birth_date']).dt.days
    features['age_years'] = age_days.div(365.25).fillna(0)

    # Fill NaNs
    for c in features.columns:
        if features[c].dtype.kind in 'biufc':
            features[c] = features[c].fillna(0)

    # Derive strength TOI minutes
    for st in ['EV','PP','SH']:
        col = f"toi_{st}_sec"
        if col in features.columns:
            features[f"toi_{st}_min"] = features[col] / 60.0
        else:
            features[f"toi_{st}_min"] = 0.0

    # Prefer true shot counts by strength; fallback to TOI-share estimate if missing
    total_toi_sec = features[[c for c in features.columns if c.startswith('toi_') and c.endswith('_sec')]].sum(axis=1)
    total_toi_sec = total_toi_sec.replace(0, np.nan)
    for st in ['EV','PP','SH']:
        est_share = features.get(f"toi_{st}_sec", 0) / total_toi_sec
        est = (features['shots'] * est_share.fillna(0)).fillna(0)
        col = f"shots_true_{st}"
        true_ct = features[col] if col in features.columns else None
        if true_ct is None:
            features[f"shots_{st}_best"] = est
        else:
            best = true_ct.where(true_ct.notna(), est)
            features[f"shots_{st}_best"] = best.fillna(0)

    # Composite formulas candidates
    features['possession_index'] = (features.get('CF60',0) + features.get('FF60',0) + features.get('SF60',0)) / 3.0
    features['finishing_index'] = np.where(features['shots']>0, features['goals']/features['shots'], 0)
    features['pp_exposure'] = features['toi_PP_min']
    features['ev_burden'] = features['toi_EV_min']

    return features


def run_models(df: pd.DataFrame, target: str) -> Dict:
    # Select predictors (exclude direct target leakage)
    predictors = [
        # Strength-specific
        'toi_EV_min','toi_PP_min','toi_SH_min',
        'shots_EV_best','shots_PP_best','shots_SH_best',
        'goals_true_EV','goals_true_PP','goals_true_SH',
        'avg_dist_EV','avg_dist_PP','avg_dist_SH',
        # Teammates / on-ice context
        'teammates_on_ice_avg','teammate_variants',
        # Location
        'avg_abs_x','avg_dist',
        # Age
        'age_years',
        # Advanced totals
        'CF','FF','SF','GF','CA','FA','SA','GA','CF60','FF60','SF60','GF60','PDO','TOI_seconds',
        # Composite
        'possession_index','finishing_index','pp_exposure','ev_burden',
    ]
    predictors = [p for p in predictors if p in df.columns]
    X = df[predictors].fillna(0)
    y = df[target].fillna(0)

    lasso = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LassoCV(cv=5, random_state=42, max_iter=20000))
    ])
    gkf = GroupKFold(n_splits=5)
    lasso_scores = cross_val_score(lasso, X, y, cv=gkf, scoring='r2', groups=df['player_id'])
    lasso.fit(X, y)
    lasso_coefs = dict(zip(predictors, lasso.named_steps['model'].coef_))
    lasso_top = sorted(lasso_coefs.items(), key=lambda x: abs(x[1]), reverse=True)[:15]

    rf = RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1)
    rf_scores = cross_val_score(rf, X, y, cv=gkf, scoring='r2', groups=df['player_id'])
    rf.fit(X, y)
    rf_importance = dict(zip(predictors, rf.feature_importances_))
    rf_top = sorted(rf_importance.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        'lasso_r2_mean': float(np.mean(lasso_scores)),
        'lasso_r2_std': float(np.std(lasso_scores)),
        'lasso_top': lasso_top,
        'rf_r2_mean': float(np.mean(rf_scores)),
        'rf_r2_std': float(np.std(rf_scores)),
        'rf_top': rf_top,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Strength-specific predictor importance')
    parser.add_argument('--season', type=int, default=20242025)
    parser.add_argument('--limit', type=int, default=50000)
    args = parser.parse_args()

    engine = get_engine()
    logger.info(f"Building dataset for season {args.season}...")
    df = build_dataset(engine, args.season, args.limit)
    if df.empty:
        print("No data found.")
        return

    for target in ['goals','assists','points']:
        logger.info(f"\n=== Target: {target.upper()} ===")
        res = run_models(df, target)
        print(f"Target: {target.upper()}")
        print(f"  Lasso R^2: {res['lasso_r2_mean']:.3f} ± {res['lasso_r2_std']:.3f}")
        print("  Lasso top features:")
        for k, v in res['lasso_top'][:10]:
            print(f"    - {k:25s} {v:+.3f}")
        print(f"  RF R^2: {res['rf_r2_mean']:.3f} ± {res['rf_r2_std']:.3f}")
        print("  RF top features:")
        for k, v in res['rf_top'][:10]:
            print(f"    - {k:25s} {v:.4f}")


if __name__ == "__main__":
    main()
