#!/usr/bin/env python3
"""
Forecast 2023/24 player points using prior-season (2022/23) PTS/60 carried forward,
applied to 2023/24 total TOI. Compare to actual 2023/24 points and print accuracy.

This is a simple, leakage-free rate-baseline (no current-season rate info used).
"""

import os
import sys
import math
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.connection import connect_with_connector


def get_engine():
    load_dotenv()
    url = os.getenv("NHL_DATABASE_URL")
    if url:
        return create_engine(url, pool_pre_ping=True)
    return connect_with_connector()


def fetch_season_totals(engine, season: int) -> pd.DataFrame:
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


def backtest_points(engine, prev_season: int, target_season: int):
    prev = fetch_season_totals(engine, prev_season)
    cur = fetch_season_totals(engine, target_season)
    # Position-mean fallback for low sample or missing
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
    # Metrics
    mae = float((cur["error"].abs()).mean())
    rmse = float(math.sqrt((cur["error"]**2).mean()))
    # MAPE excluding zero-actuals
    mask = cur["points"] > 0
    mape = float(((cur.loc[mask, "error"].abs()) / cur.loc[mask, "points"]).mean()) if mask.any() else float("nan")
    # Correlation
    corr = float(cur[["pred_points", "points"]].corr().iloc[0,1]) if len(cur) > 1 else float("nan")

    # Top 10 over/under
    over = cur.sort_values("error", ascending=False).head(10)[["player_id","points","pred_points","error"]]
    under = cur.sort_values("error", ascending=True).head(10)[["player_id","points","pred_points","error"]]

    print(f"Backtest  forecast: prior-season PTS/60 -> {target_season}")
    print(f"MAE: {mae:.2f}  RMSE: {rmse:.2f}  MAPE: {mape:.2%}  Corr: {corr:.3f}")
    print("Top 10 over-predictions (pred - actual):")
    print(over.to_string(index=False))
    print("Top 10 under-predictions (pred - actual):")
    print(under.to_string(index=False))


def main():
    engine = get_engine()
    backtest_points(engine, prev_season=20222023, target_season=20232024)


if __name__ == "__main__":
    main()


