### Session Insights (Forecasting, VORP, Ice-Time Deployment, Clustering)

Date: 2025-08-30

#### Data/Infra
- Database: connected to Cloud SQL Postgres (public IP 34.47.23.137) successfully.
- Seasons present (regular season only, game_type=2): 20222023, 20232024, 20242025.
- NHL APIs status during session: `api.nhle.com` and `api-web.nhle.com` returned HTTP 503; `statsapi.web.nhl.com` DNS unresolved (temporary outage). Ingestion of 2021/22 deferred until endpoints recover.

#### Ice-Time Deployment (EV/PP/SH)
- Computed league-wide pair/trio overlaps for 2022–2025 and summarized per team.
- EV top-5 pairs per team (league-wide across seasons):
  - Unit types: FF ≈ 40%, DD ≈ 31.5%, mixed ≈ 28.5%.
  - Forward-forward combos: C–W ≈ 70%, C–C ≈ 23%, W–W ≈ 7%.
  - Seconds distribution (per pair): median ≈ 51,082s, p90 ≈ 64,588s.
- Team deployment baselines derived (EV line shares; PP1/PP2; PK pairs shares) per team for forecasting.

#### Forecasting (Points) — Totals (prior PTS/60 × target TOI)
- 2023/24 baseline: MAE 5.48, RMSE 8.48, MAPE 41.46%, Corr 0.939.
- 2024/25 baseline: MAE 5.60, RMSE 8.59, MAPE 40.29%, Corr 0.935.
- Top-N (2024/25):
  - MAE: Top25 11.68, Top100 11.52, Top200 10.28, Top300 9.54, Top400 8.94, Top500 8.28.

#### Forecasting (Points per Game, PPG) — Non-leak baselines and third-party
- Baseline PPG (non-leak; 2023/24 using 2022/23 PTS/60 & 2022/23 TOI/GP): MAE 0.137, RMSE 0.200, Corr 0.791.
  - Top-N MAE|RMSE: 25: 0.187|0.227; 100: 0.170|0.215; 200: 0.162|0.208; 300: 0.156|0.203; 400: 0.149|0.195; 500: 0.144|0.189.
- Athletic PPG (2023/24): MAE 0.129, RMSE 0.168, Corr 0.835.
- Edraft PPG (2023/24): MAE 0.128, RMSE 0.174, Corr 0.837.
- Dobber PPG (2023/24): MAE 0.173, RMSE 0.221, Corr 0.729.
- Takeaways:
  - Athletic/Edraft lead on RMSE/Corr mid-pool; non-leak baseline leads Top-25 and deep (Top-400/500).
  - Dobber underperforms across metrics.

#### VORP Tiers and Frontend
- Implemented VORP endpoint with production/composite value modes; grouping by `centers`, `wings`, `defence`. Frontend updated to display 15 tiers with quantile method and min GP filter.

#### EV Heavy TOI Driver Clusters (Forwards only)
- Pooled 2022–2025, restricted to forwards; heavy = EV TOI/GP ≥ 75th percentile.
- k=2 clusters (silhouette ≈ 0.573):
  - Cluster 0: High-usage, low-to-mid EV rates (CF60≈22, SF60≈12, GF60≈1.9). Examples: Connor McDavid, Jack Hughes, Mathew Barzal, Zach Hyman, Clayton Keller.
  - Cluster 1: High-usage, high EV rates (CF60≈68, SF60≈36, GF60≈6.1). Examples: Nathan MacKinnon, Kirill Kaprizov, Mikko Rantanen, Leon Draisaitl, Mark Scheifele.

#### Common Traits in EV Top Pairs
- Among teams’ top-5 EV pairs:
  - At least one high-usage (TOI) driver in ≈ 89% of pairs; both TOI-high in ≈ 53%.
  - Both players simultaneously high in CF60/SF60/GF60 in ≈ 19–22% of pairs.
  - Average percentiles within pairs: CF60≈0.58–0.59; SF60≈0.57–0.58; GF60≈0.54; TOI_seconds≈0.69–0.71; PDO≈~0.50.

#### Notes & Next Steps
- Avoid leakage: use prior-season TOI/GP with prior PTS/60 for PPG baselines.
- Improve model fidelity:
  - 3-year weighted PTS/60 (e.g., 60/30/10) and EV/PP split rates.
  - Projected TOI via team deployment baselines (EV lines, PP units, PK pairs) + expected GP (injury model).
  - Ingest 2021/22 once NHL APIs recover to expand backtesting.


