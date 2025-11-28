#!/usr/bin/env python3
"""
Forecast NHL 2021/22 season points using our current baseline (prior-season PTS/60 × target-season TOI)
and compare against an external forecast file (Athletic 2021/22), plus actuals.

Outputs in docs/Forecasts/:
  - nhl_2021_22_model_forecast.csv
  - nhl_2021_22_comparison.csv (name, pos, actual, model_pred, athletic_pred)
  - nhl_2021_22_summary.md (overall and Top-N metrics per forecast)
"""

import os
import math
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if url:
        return create_engine(url, pool_pre_ping=True)
    from src.database.connection import connect_with_connector
    return connect_with_connector()


def fetch_totals(engine, season: int) -> pd.DataFrame:
    q = text(
        """
        SELECT pg.player_id,
               p.full_name AS name,
               p.position_code AS pos,
               SUM(pg.points) AS points,
               COUNT(pg.id) AS gp,
               SUM(
                 CASE WHEN position(':' in pg.toi) > 0 THEN
                   CAST(split_part(pg.toi, ':', 1) AS INT)*60 + CAST(split_part(pg.toi, ':', 2) AS INT)
                 ELSE 0 END
               ) AS toi_sec
        FROM player_game_stats pg
        JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
        JOIN players p ON p.id = pg.player_id
        GROUP BY pg.player_id, p.full_name, p.position_code
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(q, conn, params={"season": int(season)})
    df["points"] = df["points"].fillna(0).astype(float)
    df["toi_sec"] = df["toi_sec"].fillna(0).astype(float)
    df["pos"] = (df["pos"].fillna("").str.upper())
    df["name_key"] = df["name"].str.strip().str.upper()
    df["pts_per_60"] = df.apply(lambda r: (r["points"] * 3600.0 / r["toi_sec"]) if r["toi_sec"] > 0 else 0.0, axis=1)
    return df


def build_model_forecast(engine, prev_season: int, target_season: int) -> pd.DataFrame:
    prev = fetch_totals(engine, prev_season)
    cur = fetch_totals(engine, target_season)
    pos_means = prev.groupby("pos")["pts_per_60"].mean().to_dict()
    prev_rates_s = prev.set_index("player_id")["pts_per_60"]
    # Vectorized: map player prior rate; fallback to position mean; final fallback to overall mean
    model = cur.copy()
    rates = model["player_id"].map(prev_rates_s)
    fallback_pos = model["pos"].map(pos_means)
    overall = prev["pts_per_60"].mean() if len(prev) else 0.0
    rate_used = rates.fillna(fallback_pos).fillna(overall)
    model["model_pred_points"] = rate_used * (model["toi_sec"] / 3600.0)
    # Also build naive prior-season total points baseline for comparison
    prev_points_s = prev.set_index("player_id")["points"]
    model["naive_prev_points"] = model["player_id"].map(prev_points_s).fillna(0.0)
    return model[["player_id","name","name_key","pos","model_pred_points","naive_prev_points","points"]].rename(columns={"points":"actual_points"})


def read_athletic_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expected columns: NAME, POS, GP, G, A, PTS
    # Normalize name key
    df["name_key"] = df["NAME"].astype(str).str.strip().str.upper()
    df["athletic_pts"] = df.get("PTS").astype(float)
    df["athletic_pos"] = df.get("POS").astype(str)
    return df[["name_key","NAME","athletic_pos","athletic_pts"]]


def metrics(df: pd.DataFrame, pred_col: str) -> tuple[float,float,float]:
    err = df[pred_col] - df["actual_points"]
    mae = float(err.abs().mean())
    rmse = float(math.sqrt((err**2).mean()))
    mask = df["actual_points"] > 0
    mape = float((err[mask].abs() / df.loc[mask, "actual_points"]).mean()) if mask.any() else float("nan")
    return mae, rmse, mape


def metrics_topn(df: pd.DataFrame, pred_col: str):
    out = []
    ranks = [25, 100, 200, 300, 400, 500]
    ranked = df.sort_values("actual_points", ascending=False).reset_index(drop=True)
    for n in ranks:
        sub = ranked.head(n)
        mae, rmse, mape = metrics(sub, pred_col)
        out.append((n, mae, rmse, mape))
    return out


def main():
    engine = get_engine()
    prev_season = 20202021
    target_season = 20212022
    athletic_path = os.path.join("docs","Forecasts","NHL 21_22 Forecasts - Athletic 2021_22.csv")
    out_dir = os.path.join("docs","Forecasts")
    os.makedirs(out_dir, exist_ok=True)

    model = build_model_forecast(engine, prev_season, target_season)
    athletic = read_athletic_csv(athletic_path)

    # Join by name_key to actual/model
    merged = model.merge(athletic, on="name_key", how="left")
    merged_out = merged[["player_id","name","pos","actual_points","model_pred_points","naive_prev_points","athletic_pts"]].copy()
    merged_out.to_csv(os.path.join(out_dir, "nhl_2021_22_comparison.csv"), index=False)
    model_out = merged[["player_id","name","pos","model_pred_points","naive_prev_points"]].copy()
    model_out.to_csv(os.path.join(out_dir, "nhl_2021_22_model_forecast.csv"), index=False)

    # Compute metrics
    overall_model = metrics(merged, "model_pred_points")
    overall_naive = metrics(merged, "naive_prev_points")
    overall_ath = metrics(merged.dropna(subset=["athletic_pts"]), "athletic_pts")
    topn_model = metrics_topn(merged, "model_pred_points")
    topn_naive = metrics_topn(merged, "naive_prev_points")
    topn_ath = metrics_topn(merged.dropna(subset=["athletic_pts"]).copy(), "athletic_pts")

    # Write summary
    md = os.path.join(out_dir, "nhl_2021_22_summary.md")
    with open(md, "w") as f:
        f.write("# 2021/22 Forecast Comparison\n\n")
        f.write("Our model: prior-season PTS/60 × 2021/22 TOI\n\n")
        f.write("## Overall\n")
        f.write("- Model MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n".format(*overall_model))
        f.write("- Naive Prev-Year Points MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n".format(*overall_naive))
        f.write("- Athletic MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n\n".format(*overall_ath))
        f.write("## Top-N (by actual points rank)\n")
        f.write("Model:\n")
        for n, mae, rmse, mape in topn_model:
            f.write("- Top {}: MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n".format(n, mae, rmse, mape))
        f.write("\nNaive Prev-Year Points:\n")
        for n, mae, rmse, mape in topn_naive:
            f.write("- Top {}: MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n".format(n, mae, rmse, mape))
        f.write("\nAthletic:\n")
        for n, mae, rmse, mape in topn_ath:
            f.write("- Top {}: MAE {:.2f}, RMSE {:.2f}, MAPE {:.2%}\n".format(n, mae, rmse, mape))
    print(f"Wrote comparison CSVs and summary to {out_dir}")


if __name__ == "__main__":
    main()


