#!/usr/bin/env python3
"""
Compute Top-N accuracy metrics (25/100/200/300/400/500) for 2023/24 points forecasts
using prior-season (2022/23) PTS/60 carried forward and 2023/24 TOI.
Print MAE, RMSE, MAPE per Top-N bucket.
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
               SUM(pg.points) AS points,
               COUNT(pg.id) AS gp,
               SUM(
                 CASE WHEN position(':' in pg.toi) > 0 THEN
                   CAST(split_part(pg.toi, ':', 1) AS INT)*60 + CAST(split_part(pg.toi, ':', 2) AS INT)
                 ELSE 0 END
               ) AS toi_sec,
               p.position_code
        FROM player_game_stats pg
        JOIN games g ON g.id = pg.game_id AND g.season = :season AND g.game_type = 2
        JOIN players p ON p.id = pg.player_id
        GROUP BY pg.player_id, p.position_code
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(q, conn, params={"season": int(season)})
    df["points"] = df["points"].fillna(0).astype(float)
    df["toi_sec"] = df["toi_sec"].fillna(0).astype(float)
    df["position_code"] = (df["position_code"].fillna("").str.upper())
    df["pts_per_60"] = df.apply(lambda r: (r["points"] * 3600.0 / r["toi_sec"]) if r["toi_sec"] > 0 else 0.0, axis=1)
    return df


def build_predictions(engine) -> pd.DataFrame:
    prev = fetch_totals(engine, 20222023)
    cur = fetch_totals(engine, 20232024)
    pos_means = prev.groupby("position_code")["pts_per_60"].mean().to_dict()
    prev_map = prev.set_index("player_id")["pts_per_60"].to_dict()
    pos_map = prev.set_index("player_id")["position_code"].to_dict()

    def prior_rate(pid: int) -> float:
        r = prev_map.get(pid)
        if r is not None and r > 0:
            return float(r)
        pos = (pos_map.get(pid) or "")
        return float(pos_means.get(pos, prev["pts_per_60"].mean() if len(prev) else 0.0))

    cur = cur.copy()
    cur["pred_points"] = cur.apply(lambda r: prior_rate(int(r["player_id"])) * (r["toi_sec"]/3600.0), axis=1)
    cur["error"] = cur["pred_points"] - cur["points"]
    return cur


def metrics_for(df: pd.DataFrame) -> tuple[float, float, float]:
    mae = float((df["error"].abs()).mean())
    rmse = float(math.sqrt((df["error"]**2).mean()))
    mask = df["points"] > 0
    mape = float(((df.loc[mask, "error"].abs()) / df.loc[mask, "points"]).mean()) if mask.any() else float("nan")
    return mae, rmse, mape


def main():
    engine = get_engine()
    df = build_predictions(engine)
    df = df.sort_values("points", ascending=False).reset_index(drop=True)
    buckets = [25, 100, 200, 300, 400, 500]
    print("Top-N accuracy (2023/24):")
    for n in buckets:
        sub = df.head(n)
        mae, rmse, mape = metrics_for(sub)
        print(f"Top {n}: MAE {mae:.2f} | RMSE {rmse:.2f} | MAPE {mape:.2%}")


if __name__ == "__main__":
    main()


