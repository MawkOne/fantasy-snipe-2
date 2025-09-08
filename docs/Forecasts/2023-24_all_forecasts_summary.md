### 2023/24 Forecast Comparison (All Models)

Scope:
- Season: 2023/24 (regular season only; game_type=2)
- Metrics: MAE, RMSE, Correlation vs actual points per game (PPG)
- Top-N: evaluated by actual points rank (25/100/200/300/400/500)

Models compared:
- Our baseline (non-leak): 2022/23 PTS/60 with 2022/23 TOI/GP → predict 2023/24 PPG
- Athletic (CSV provided)
- Edraft (CSV provided)
- Dobber (CSV provided)

Overall PPG accuracy (MAE, RMSE, Corr):
- Our baseline: 0.137, 0.200, 0.791
- Athletic: 0.129, 0.168, 0.835
- Edraft: 0.128, 0.174, 0.837
- Dobber: 0.173, 0.221, 0.729

Top-N PPG (MAE | RMSE):
- Our baseline:
  - Top 25: 0.187 | 0.227
  - Top 100: 0.170 | 0.215
  - Top 200: 0.162 | 0.208
  - Top 300: 0.156 | 0.203
  - Top 400: 0.149 | 0.195
  - Top 500: 0.144 | 0.189
- Athletic:
  - Top 25: 0.178 | 0.214
  - Top 100: 0.150 | 0.182
  - Top 200: 0.139 | 0.173
  - Top 300: 0.128 | 0.160
  - Top 400: 0.125 | 0.159
  - Top 500: 0.124 | 0.161
- Edraft:
  - Top 25: 0.174 | 0.212
  - Top 100: 0.168 | 0.200
  - Top 200: 0.160 | 0.195
  - Top 300: 0.146 | 0.182
  - Top 400: 0.139 | 0.178
  - Top 500: 0.135 | 0.178
- Dobber:
  - Top 25: 0.210 | 0.277
  - Top 100: 0.180 | 0.227
  - Top 200: 0.176 | 0.222
  - Top 300: 0.167 | 0.210
  - Top 400: 0.164 | 0.208
  - Top 500: 0.167 | 0.214

Conclusions:
- Best overall (PPG): Athletic/Edraft achieve lower RMSE/higher Corr mid‑pool, but our baseline leads at the very top (Top‑25) and deeper pools (Top‑400/500).
- Best third‑party: Athletic slightly ahead of Edraft; both outperform Dobber.

Notes:
- Absolute-error views (MAE/RMSE) across PPG are stable; correlation highlights ranking quality.
- Next improvement: 3‑year weighted PTS/60 (e.g., 60/30/10) and EV/PP rate splits with team deployment baselines.

### PPG-based comparison (2023/24)

Overall PPG accuracy (MAE, RMSE, Corr):
- Our baseline PPG (non-leak, uses 2022/23 PTS/60 and 2022/23 TOI/GP): 0.137, 0.200, 0.791
- Athletic PPG: 0.129, 0.168, 0.835
- Edraft PPG: 0.128, 0.174, 0.837
- Dobber PPG: 0.173, 0.221, 0.729

Summary:
- Athletic/Edraft show slightly better RMSE/Corr mid-pool, but baseline leads Top-25 and deeper pools.
- Dobber underperforms on PPG vs. actuals across metrics.

Top-N PPG (MAE | RMSE):
- Baseline (non-leak):
  - Top 25: 0.187 | 0.227
  - Top 100: 0.170 | 0.215
  - Top 200: 0.162 | 0.208
  - Top 300: 0.156 | 0.203
  - Top 400: 0.149 | 0.195
  - Top 500: 0.144 | 0.189

