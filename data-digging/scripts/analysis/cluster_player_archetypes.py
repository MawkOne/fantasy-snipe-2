#!/usr/bin/env python3
"""
Cluster NHL player archetypes by position (Centers, Wings, Defence) for a season.

Features (per player-season):
- Rates per 60: goals, assists, points, shots
- Advanced rates: CF60, FF60, SF60, GF60, PDO
- Usage: average TOI (seconds per game), games played
- Efficiency: finishing_index (goals/shots)

Position groups:
- Centers: players.position_code = 'C'
- Wings: players.position_code IN ('L','R')
- Defence: players.position_code = 'D'

Model:
- Standardize features, try KMeans for k in [3..8]; select by silhouette score
- Save assignments per position to CSV in docs/

Usage:
  python scripts/cluster_player_archetypes.py --season 20242025 --min_gp 20

Env:
  NHL_DATABASE_URL=postgresql://USER:PASS@HOST:PORT/postgres?sslmode=require
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if not url:
        raise RuntimeError("NHL_DATABASE_URL not set")
    return create_engine(url, pool_pre_ping=True)


def fetch_player_season(engine, season: int) -> pd.DataFrame:
    # Aggregate per player-season across games
    q = f"""
    WITH per_game AS (
      SELECT p.id AS player_id, p.full_name, p.position_code,
             pg.player_id AS pg_player_id, pg.game_id,
             COALESCE(pg.goals,0) AS goals,
             COALESCE(pg.assists,0) AS assists,
             COALESCE(pg.points,0) AS points,
             COALESCE(pg.shots,0) AS shots,
             COALESCE(adv."CF60",0) AS CF60,
             COALESCE(adv."FF60",0) AS FF60,
             COALESCE(adv."SF60",0) AS SF60,
             COALESCE(adv."GF60",0) AS GF60,
             COALESCE(adv."PDO",0) AS PDO,
             COALESCE(adv."TOI_seconds",0) AS TOI_seconds
      FROM players p
      JOIN player_game_stats pg ON pg.player_id = p.id
      JOIN games g ON g.id = pg.game_id AND g.season = {season} AND g.game_type = 2
      LEFT JOIN player_game_advanced_metrics_flat adv ON adv.player_id = pg.player_id AND adv.game_id = pg.game_id
    )
    SELECT player_id, full_name, position_code,
           COUNT(*) AS gp,
           SUM(goals) AS goals,
           SUM(assists) AS assists,
           SUM(points) AS points,
           SUM(shots) AS shots,
           AVG(CF60) AS CF60,
           AVG(FF60) AS FF60,
           AVG(SF60) AS SF60,
           AVG(GF60) AS GF60,
           AVG(PDO) AS PDO,
           AVG(TOI_seconds) AS avg_toi_seconds
    FROM per_game
    GROUP BY player_id, full_name, position_code
    """
    return pd.read_sql_query(q, engine)


def fetch_birthdates(engine) -> pd.DataFrame:
    q = "SELECT player_id, birth_date FROM player_details"
    df = pd.read_sql_query(q, engine)
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    return df


def season_midpoint(season_code: int) -> pd.Timestamp:
    # e.g., 20242025 -> midpoint ~ 2025-01-15
    s = str(season_code)
    second = int(s[4:]) if len(s) == 8 else (int(s) + 1)
    return pd.Timestamp(year=second, month=1, day=15)


def build_features(df: pd.DataFrame, engine, season: int) -> pd.DataFrame:
    d = df.copy()
    # Rates per 60 based on average TOI seconds per game; safeguard zeros
    toi_min = (d['avg_toi_seconds'].replace(0, np.nan) / 60.0)
    d['goals_per60'] = (d['goals'] / d['gp']) / toi_min * 60.0
    d['assists_per60'] = (d['assists'] / d['gp']) / toi_min * 60.0
    d['points_per60'] = (d['points'] / d['gp']) / toi_min * 60.0
    d['shots_per60'] = (d['shots'] / d['gp']) / toi_min * 60.0
    d[['goals_per60','assists_per60','points_per60','shots_per60']] = d[['goals_per60','assists_per60','points_per60','shots_per60']].fillna(0)
    d['finishing_index'] = np.where(d['shots'] > 0, d['goals'] / d['shots'], 0)

    # Age at season midpoint
    bd = fetch_birthdates(engine)
    d = d.merge(bd, left_on='player_id', right_on='player_id', how='left')
    mid = season_midpoint(season)
    age_days = (mid - pd.to_datetime(d['birth_date'], errors='coerce')).dt.days
    d['age_years'] = age_days.div(365.25).fillna(0)

    # Points relative to position (z-score within position)
    def zscore(x):
        s = x.std(ddof=0)
        return (x - x.mean()) / s if s and s > 1e-9 else 0.0
    d['points_pos_z'] = d.groupby('position_code')['points_per60'].transform(zscore)
    return d


def cluster_position(df: pd.DataFrame, position_mask: pd.Series, position_name: str, out_dir: str, min_gp: int = 20) -> Tuple[pd.DataFrame, dict]:
    pos_df = df.loc[position_mask].copy()
    pos_df = pos_df[pos_df['gp'] >= min_gp]
    if pos_df.empty:
        logger.warning(f"No players found for {position_name} with gp >= {min_gp}")
        return pos_df, {}

    feature_cols_all = [
        'goals_per60','assists_per60','points_per60','shots_per60',
        'CF60','FF60','SF60','GF60','PDO','avg_toi_seconds','finishing_index',
        'points_pos_z','age_years'
    ]
    feature_cols = [c for c in feature_cols_all if c in pos_df.columns]
    if len(feature_cols) < 5:
        logger.warning(f"{position_name}: limited features available ({len(feature_cols)}) -> {feature_cols}")
    else:
        logger.info(f"{position_name}: using features {feature_cols}")
    X = pos_df[feature_cols].fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    best_k, best_score, best_labels = None, -1, None
    for k in range(3, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = km.fit_predict(Xs)
        score = silhouette_score(Xs, labels)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels

    pos_df['cluster'] = best_labels
    pos_df['position_group'] = position_name
    pos_df['silhouette'] = best_score

    # Save CSV
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"cluster_assignments_{position_name.replace(' ','_').lower()}_2024-25.csv")
    pos_df[['player_id','full_name','position_code','gp','cluster','silhouette'] + feature_cols].to_csv(out_path, index=False)
    logger.info(f"Saved {position_name} clusters (k={best_k}, silhouette={best_score:.3f}) -> {out_path}")

    # Cluster centroids for interpretation
    centroids = (
        pos_df.groupby('cluster')[feature_cols]
        .mean()
        .reset_index()
        .sort_values('cluster')
    )
    def _label_centroids(centroids_df: pd.DataFrame) -> dict:
        # Keep raw for heuristic overrides
        raw = centroids_df.copy()
        # Normalized copy for scoring
        cd = centroids_df.copy()
        cols = [c for c in cd.columns if c != 'cluster']
        for c in cols:
            col = cd[c]
            if col.max() > col.min():
                cd[c] = (col - col.mean()) / (col.std(ddof=0) + 1e-9)
            else:
                cd[c] = 0.0
        # Base scoring to generate ranked candidates
        def scores(row):
            d = row.to_dict()
            s_goals = d.get('goals_per60', 0)
            s_assists = d.get('assists_per60', 0)
            s_points = d.get('points_per60', 0)
            s_shots = d.get('shots_per60', 0)
            s_toi = d.get('avg_toi_seconds', 0)
            s_fin = d.get('finishing_index', 0)
            s_ppz = d.get('points_pos_z', 0)
            s_age = d.get('age_years', 0)
            return {
                'Sniper': 1.4*s_goals + 1.1*s_fin + 0.4*s_shots + 0.3*s_ppz,
                'Playmaker': 1.5*s_assists + 0.6*s_points + 0.3*s_ppz,
                'Volume Shooter': 1.5*s_shots + 0.3*s_goals - 0.2*s_fin,
                'Offensive Driver': 1.0*s_points + 0.6*s_shots + 0.3*s_assists + 0.4*s_ppz,
                'Two-Way Workhorse': 1.0*(s_toi/60.0) + 0.3*s_points + 0.2*s_ppz,
                'Power-Play Specialist': 0.7*s_points + 0.6*s_assists + 0.2*s_fin + 0.3*s_ppz,
                'Transition Driver': 0.7*s_shots + 0.5*s_points + 0.3*s_assists + 0.2*s_ppz,
                'Defensive Anchor': 0.9*(s_toi/60.0) + 0.1*s_age - 0.3*s_points,
                'Depth/Role Player': -0.4*s_points + -0.2*s_shots,
            }
        cluster_to_ranked_labels = {}
        for _, r in cd.iterrows():
            cid = int(r['cluster'])
            sc = scores(r.drop(labels=['cluster']))
            ranked = sorted(sc.items(), key=lambda x: x[1], reverse=True)
            cluster_to_ranked_labels[cid] = [name for name, _ in ranked]
        # Heuristic overrides using raw centroids
        rp = raw.copy()
        # Ensure top scoring cluster by points_pos_z isn't Depth
        if 'points_pos_z' in rp.columns:
            top_ppz_cid = int(rp.loc[rp['points_pos_z'].idxmax(), 'cluster'])
            # If goals >= assists -> Sniper else Playmaker or Offensive Driver
            g = rp.loc[rp['points_pos_z'].idxmax(), 'goals_per60'] if 'goals_per60' in rp.columns else 0
            a = rp.loc[rp['points_pos_z'].idxmax(), 'assists_per60'] if 'assists_per60' in rp.columns else 0
            forced = 'Sniper' if g >= a else 'Playmaker'
            cluster_to_ranked_labels[top_ppz_cid] = [forced] + [l for l in cluster_to_ranked_labels[top_ppz_cid] if l != forced]
        # Avoid assigning Depth to more than one cluster; prefer Depth only for lowest points cluster
        if 'points_per60' in rp.columns:
            low_points_cid = int(rp.loc[rp['points_per60'].idxmin(), 'cluster'])
        else:
            low_points_cid = None
        assigned = {}
        used = set()
        for cid in sorted(cluster_to_ranked_labels.keys()):
            for cand in cluster_to_ranked_labels[cid]:
                if cand == 'Depth/Role Player' and low_points_cid is not None and cid != low_points_cid:
                    continue
                if cand not in used:
                    assigned[cid] = cand
                    used.add(cand)
                    break
        for cid in sorted(cluster_to_ranked_labels.keys()):
            if cid not in assigned:
                for cand in cluster_to_ranked_labels[cid]:
                    assigned[cid] = cand
                    break
        return assigned

    labels_map = _label_centroids(centroids)
    meta = {
        'k': best_k,
        'silhouette': best_score,
        'centroids': centroids.to_dict(orient='list'),
        'labels': labels_map,
    }
    return pos_df, meta


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Cluster NHL player archetypes by position')
    parser.add_argument('--season', type=int, default=20242025)
    parser.add_argument('--min_gp', type=int, default=20)
    parser.add_argument('--out_dir', type=str, default='docs')
    args = parser.parse_args()

    engine = get_engine()
    df = fetch_player_season(engine, args.season)
    df = build_features(df, engine, args.season)

    centers_mask = df['position_code'] == 'C'
    wings_mask = df['position_code'].isin(['L','R'])
    defence_mask = df['position_code'] == 'D'

    all_assignments = []
    meta_all = {}
    for name, mask in [
        ('Centers', centers_mask),
        ('Wings', wings_mask),
        ('Defence', defence_mask),
    ]:
        assign, meta = cluster_position(df, mask, name, args.out_dir, min_gp=args.min_gp)
        if not assign.empty:
            all_assignments.append(assign)
            meta_all[name] = meta

    if all_assignments:
        combined = pd.concat(all_assignments, ignore_index=True)
        combined_path = os.path.join(args.out_dir, 'cluster_assignments_all_2024-25.csv')
        combined[['player_id','full_name','position_group','position_code','gp','cluster']].to_csv(combined_path, index=False)
        logger.info(f"Saved combined clusters -> {combined_path}")

    # Dump brief meta summary
    meta_path = os.path.join(args.out_dir, 'cluster_meta_2024-25.json')
    import json
    with open(meta_path, 'w') as f:
        json.dump(meta_all, f, indent=2)
    logger.info(f"Saved cluster meta -> {meta_path}")


if __name__ == '__main__':
    main()


