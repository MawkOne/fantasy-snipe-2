### Forecast: 2023/24 (prior-season PTS/60 × 2023/24 TOI)

Method:
- For each skater, carry forward prior-season (2022/23) PTS per 60 and multiply by 2023/24 total TOI hours.
- Regular season only (game_type=2). Missed games captured via TOI.

Overall accuracy:
- MAE 5.48
- RMSE 8.48
- MAPE 41.46%
- Correlation 0.939

Top-N (by actual points rank):
- Top 25: MAE 12.52, RMSE 15.38, MAPE 12.74%
- Top 100: MAE 11.53, RMSE 14.17, MAPE 15.71%
- Top 200: MAE 11.01, RMSE 14.04, MAPE 18.90%
- Top 300: MAE 9.79, RMSE 12.73, MAPE 20.01%
- Top 400: MAE 9.00, RMSE 11.77, MAPE 21.86%
- Top 500: MAE 8.39, RMSE 11.08, MAPE 24.87%

Notes:
- Simple rate×usage baseline; good rank correlation, increasing relative error deeper in pool.

