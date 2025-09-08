#!/usr/bin/env python3
"""
Analyze team ice-time deployments:
- Compute co-ice overlap for pairs and trios by team and strength (EV/PP/SH)
- Summarize concentration metrics: share of top N pairs/trios, HHI, Gini
- Output CSVs per team and a league-wide summary for 2024-25 by default

Usage:
  NHL_DATABASE_URL=postgresql://... python scripts/analyze_ice_time_deployments.py --season 20242025 --min_shift_sec 10
"""

import os
import sys
import math
import argparse
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure project imports work if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def mmss_to_seconds(mmss: str) -> int:
    if not mmss or ":" not in str(mmss):
        return 0
    try:
        m, s = str(mmss).split(":")
        return int(m) * 60 + int(s)
    except Exception:
        return 0


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if url:
        return create_engine(url, pool_pre_ping=True)
    # Fallback to default connector (e.g., Cloud SQL connector or local settings)
    try:
        from src.database.connection import connect_with_connector
        return connect_with_connector()
    except Exception:
        raise RuntimeError("NHL_DATABASE_URL not set and connector fallback failed")


def fetch_shifts(engine, season: int) -> pd.DataFrame:
    q = text(
        """
        SELECT sm.game_id, sm.team_id, sm.period,
               sm.player_id, sm.start_time, sm.end_time, sm.duration,
               COALESCE(sm.strength_state, 'EV') AS strength_state
        FROM player_shift_metrics sm
        JOIN games g ON g.id = sm.game_id AND g.season = :season AND g.game_type = 2
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(q, conn, params={"season": int(season)})
    # Normalize times
    df["start_s"] = df["start_time"].map(mmss_to_seconds)
    df["end_s"] = df["end_time"].map(mmss_to_seconds)
    df["dur_s"] = df["duration"].map(mmss_to_seconds)
    # Filter invalid
    df = df[(df["start_s"] >= 0) & (df["end_s"] > df["start_s"])]
    # Keep only known strengths
    df["strength_state"] = df["strength_state"].str.upper().map(lambda s: s if s in ("EV","PP","SH") else "EV")
    return df


def compute_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def aggregate_pairs_trios(shifts: pd.DataFrame, min_shift_sec: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Work per game, team, period, strength to keep scope small
    pairs: Dict[Tuple[int,int,int,str,Tuple[int,int]], int] = defaultdict(int)
    trios: Dict[Tuple[int,int,int,str,Tuple[int,int,int]], int] = defaultdict(int)

    for (game_id, team_id, period, strength), grp in shifts.groupby(["game_id","team_id","period","strength_state"]):
        rows = grp.sort_values(["start_s","end_s"]).to_dict("records")
        # Build active timeline discrete at shift boundaries to reduce comparisons
        # Collect boundary seconds
        bounds = sorted(set([r["start_s"] for r in rows] + [r["end_s"] for r in rows]))
        # Iterate adjacent boundary windows
        for s0, s1 in zip(bounds, bounds[1:]):
            if s1 <= s0:
                continue
            window_len = s1 - s0
            # Active players in window
            active = [r["player_id"] for r in rows if r["start_s"] <= s0 and r["end_s"] >= s1]
            if len(active) < 2:
                continue
            # Pairs
            for i in range(len(active)):
                for j in range(i+1, len(active)):
                    key = (game_id, team_id, period, strength, tuple(sorted((active[i], active[j]))))
                    pairs[key] += window_len
            # Trios
            if len(active) >= 3:
                for i in range(len(active)):
                    for j in range(i+1, len(active)):
                        for k in range(j+1, len(active)):
                            key = (game_id, team_id, period, strength, tuple(sorted((active[i], active[j], active[k]))))
                            trios[key] += window_len

    # Convert to DataFrame and aggregate across periods/games
    def pairs_df() -> pd.DataFrame:
        recs = []
        for (game_id, team_id, period, strength, pid_pair), sec in pairs.items():
            if sec >= min_shift_sec:
                a, b = pid_pair
                recs.append({
                    "team_id": team_id,
                    "strength": strength,
                    "player_a": a,
                    "player_b": b,
                    "seconds": sec,
                })
        dfp = pd.DataFrame(recs)
        if dfp.empty:
            return dfp
        return dfp.groupby(["team_id","strength","player_a","player_b"], as_index=False)["seconds"].sum()

    def trios_df() -> pd.DataFrame:
        recs = []
        for (game_id, team_id, period, strength, pid_trio), sec in trios.items():
            if sec >= min_shift_sec:
                a, b, c = pid_trio
                recs.append({
                    "team_id": team_id,
                    "strength": strength,
                    "player_a": a,
                    "player_b": b,
                    "player_c": c,
                    "seconds": sec,
                })
        dft = pd.DataFrame(recs)
        if dft.empty:
            return dft
        return dft.groupby(["team_id","strength","player_a","player_b","player_c"], as_index=False)["seconds"].sum()

    return pairs_df(), trios_df()


def concentration_metrics(seconds_list: List[float], top_n: List[int] = [1,3,5,10]) -> Dict[str, float]:
    if not seconds_list:
        return {f"share_top_{n}": 0.0 for n in top_n} | {"hhi": 0.0, "gini": 0.0}
    total = float(sum(seconds_list))
    if total <= 0:
        return {f"share_top_{n}": 0.0 for n in top_n} | {"hhi": 0.0, "gini": 0.0}
    secs_sorted = sorted(seconds_list, reverse=True)
    shares = [s/total for s in secs_sorted]
    out = {}
    for n in top_n:
        out[f"share_top_{n}"] = float(sum(secs_sorted[:n]) / total) if len(secs_sorted) >= n else float(sum(secs_sorted) / total)
    # HHI
    out["hhi"] = float(sum(p*p for p in shares))
    # Gini (discrete approximation)
    cum = 0.0
    for idx, s in enumerate(secs_sorted, start=1):
        cum += (2*idx - len(secs_sorted) - 1) * s
    out["gini"] = float(cum / (len(secs_sorted) * total))
    return out


def annotate_unit_types(engine, pairs: pd.DataFrame, trios: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if (pairs is None or pairs.empty) and (trios is None or trios.empty):
        return pairs, trios
    pos = pd.read_sql_query("SELECT id AS player_id, position_code FROM players", engine)
    pos_map = dict(zip(pos["player_id"].astype(int), (pos["position_code"].fillna("").str.upper())))

    def is_forward(p: Optional[str]) -> bool:
        return (p or "").upper() in ("L","R","C")

    if pairs is not None and not pairs.empty:
        pairs = pairs.copy()
        pairs["pos_a"] = pairs["player_a"].map(lambda x: pos_map.get(int(x), ""))
        pairs["pos_b"] = pairs["player_b"].map(lambda x: pos_map.get(int(x), ""))
        def pair_type(row):
            a, b = (row.get("pos_a") or "").upper(), (row.get("pos_b") or "").upper()
            if a == "D" and b == "D":
                return "DD"
            if is_forward(a) and is_forward(b):
                return "FF"
            return "mixed"
        pairs["unit_type"] = pairs.apply(pair_type, axis=1)

    if trios is not None and not trios.empty:
        trios = trios.copy()
        trios["pos_a"] = trios["player_a"].map(lambda x: pos_map.get(int(x), ""))
        trios["pos_b"] = trios["player_b"].map(lambda x: pos_map.get(int(x), ""))
        trios["pos_c"] = trios["player_c"].map(lambda x: pos_map.get(int(x), ""))
        def trio_type(row):
            a, b, c = (row.get("pos_a") or "").upper(), (row.get("pos_b") or "").upper(), (row.get("pos_c") or "").upper()
            fwds = sum([a in ("L","R","C"), b in ("L","R","C"), c in ("L","R","C")])
            defs = sum([a == "D", b == "D", c == "D"])
            if fwds == 3:
                return "FWD_line"
            if defs == 2 and fwds == 1:
                return "2D+1F"
            if defs == 1 and fwds == 2:
                return "1D+2F"
            return "mixed"
        trios["unit_type"] = trios.apply(trio_type, axis=1)
    return pairs, trios


def summarize(engine, pairs: pd.DataFrame, trios: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for strength in ["EV","PP","SH"]:
        if not pairs.empty:
            sub = pairs[pairs["strength"] == strength]
            grp = sub.groupby(["team_id"], as_index=False)["seconds"].apply(list)
            grp["kind"] = f"pairs_{strength}"
            frames.append(grp.rename(columns={"seconds": "seconds_list"}))
            # Unit-type shares for pairs
            if "unit_type" in sub.columns:
                tot = sub.groupby(["team_id"], as_index=False)["seconds"].sum().rename(columns={"seconds":"total_sec"})
                dd = sub[sub["unit_type"]=="DD"].groupby(["team_id"], as_index=False)["seconds"].sum().rename(columns={"seconds":"dd_sec"})
                ff = sub[sub["unit_type"]=="FF"].groupby(["team_id"], as_index=False)["seconds"].sum().rename(columns={"seconds":"ff_sec"})
                unit = tot.merge(dd, on="team_id", how="left").merge(ff, on="team_id", how="left").fillna(0)
                unit["pair_dd_share"] = unit.apply(lambda r: (r["dd_sec"]/r["total_sec"]) if r["total_sec"]>0 else 0.0, axis=1)
                unit["pair_ff_share"] = unit.apply(lambda r: (r["ff_sec"]/r["total_sec"]) if r["total_sec"]>0 else 0.0, axis=1)
                unit["bucket"] = f"pairs_{strength}"
                unit_pairs = unit[["team_id","bucket","pair_dd_share","pair_ff_share"]]
                frames.append(unit_pairs)
        if not trios.empty:
            sub3 = trios[trios["strength"] == strength]
            grp3 = sub3.groupby(["team_id"], as_index=False)["seconds"].apply(list)
            grp3["kind"] = f"trios_{strength}"
            frames.append(grp3.rename(columns={"seconds": "seconds_list"}))
            # Unit-type shares for trios
            if "unit_type" in sub3.columns:
                tot3 = sub3.groupby(["team_id"], as_index=False)["seconds"].sum().rename(columns={"seconds":"total_sec"})
                fwd_only = sub3[sub3["unit_type"]=="FWD_line"].groupby(["team_id"], as_index=False)["seconds"].sum().rename(columns={"seconds":"fwd_sec"})
                unit3 = tot3.merge(fwd_only, on="team_id", how="left").fillna(0)
                unit3["trio_fwd_share"] = unit3.apply(lambda r: (r["fwd_sec"]/r["total_sec"]) if r["total_sec"]>0 else 0.0, axis=1)
                unit3["bucket"] = f"trios_{strength}"
                frames.append(unit3[["team_id","bucket","trio_fwd_share"]])
    if not frames:
        return pd.DataFrame()
    cat = pd.concat(frames, ignore_index=True)
    # Compute metrics per row (only for rows having seconds_list)
    metrics = []
    for _, row in cat.iterrows():
        if "seconds_list" in row and isinstance(row["seconds_list"], list):
            secs = row["seconds_list"] or []
            m = concentration_metrics([float(s) for s in secs])
            m.update({
                "team_id": int(row["team_id"]),
                "bucket": str(row["kind"]),
                "total_seconds": float(sum(secs) if secs else 0.0),
                "num_units": int(len(secs) if secs else 0),
            })
            metrics.append(m)
    base = pd.DataFrame(metrics)
    # Merge in unit-type share rows if present
    unit_frames = [f for f in frames if isinstance(f, pd.DataFrame) and "bucket" in f.columns and "seconds_list" not in f.columns]
    if unit_frames:
        unit_df = pd.concat(unit_frames, ignore_index=True)
        out = base.merge(unit_df, on=["team_id","bucket"], how="left")
    else:
        out = base
    return out


def cluster_teams(summary: pd.DataFrame) -> pd.DataFrame:
    if summary is None or summary.empty:
        return pd.DataFrame()
    # Pivot features: for each bucket, include concentration metrics and unit shares
    feat_cols = [
        "share_top_1","share_top_3","share_top_5","hhi","gini",
        "pair_dd_share","pair_ff_share","trio_fwd_share",
    ]
    # Not all columns exist for all buckets; fill later
    piv = summary.pivot_table(index="team_id", columns="bucket", values=feat_cols, aggfunc="mean")
    piv.columns = [f"{c2}__{c1}" for c1, c2 in piv.columns]  # flatten
    piv = piv.fillna(0.0).reset_index()
    # Scale and cluster
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        X = piv.drop(columns=["team_id"]).values
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        best_k, best_score, best_labels = None, -1, None
        for k in range(2, min(8, len(piv))):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(Xs)
            score = silhouette_score(Xs, labels) if len(set(labels)) > 1 else -1
            if score > best_score:
                best_k, best_score, best_labels = k, score, labels
        piv["deployment_cluster"] = best_labels if best_labels is not None else 0
    except Exception:
        piv["deployment_cluster"] = 0
    return piv


def attach_team_meta(engine, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    teams = pd.read_sql_query("SELECT id AS team_id, full_name, tri_code FROM teams", engine)
    return df.merge(teams, on="team_id", how="left")


def save_outputs(out_dir: str, pairs: pd.DataFrame, trios: pd.DataFrame, summary: pd.DataFrame) -> None:
    os.makedirs(out_dir, exist_ok=True)
    pairs.to_csv(os.path.join(out_dir, "pairs_seconds.csv"), index=False)
    trios.to_csv(os.path.join(out_dir, "trios_seconds.csv"), index=False)
    summary.to_csv(os.path.join(out_dir, "team_concentration_summary.csv"), index=False)


def main():
    parser = argparse.ArgumentParser(description="Analyze ice-time deployments: pairs vs lines by strength")
    parser.add_argument("--season", type=int, default=20242025)
    parser.add_argument("--min-shift-sec", type=int, default=10, help="Minimum overlap seconds to count a unit in a window")
    parser.add_argument("--out-dir", type=str, default="docs/ice_time")
    args = parser.parse_args()

    engine = get_engine()
    print(f"Loading shifts for season {args.season}...")
    shifts = fetch_shifts(engine, args.season)
    if shifts.empty:
        print("No shift metrics available.")
        return
    print(f"Shifts rows: {len(shifts)}. Computing overlap pairs and trios...")
    pairs, trios = aggregate_pairs_trios(shifts, min_shift_sec=args.min_shift_sec)
    pairs, trios = annotate_unit_types(engine, pairs, trios)
    print(f"Pairs rows: {len(pairs)} | Trios rows: {len(trios)}. Summarizing...")
    summary = summarize(engine, pairs, trios)
    summary = attach_team_meta(engine, summary)
    save_outputs(args.out_dir, pairs, trios, summary)
    # Clusters
    clusters = cluster_teams(summary)
    clusters = attach_team_meta(engine, clusters)
    clusters.to_csv(os.path.join(args.out_dir, "team_deployment_clusters.csv"), index=False)
    print(f"Saved outputs to {args.out_dir}")


if __name__ == "__main__":
    main()


