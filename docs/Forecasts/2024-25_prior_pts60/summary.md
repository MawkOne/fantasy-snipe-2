### Forecast: 2024/25 (prior-season PTS/60 × 2024/25 TOI)

Method:
- For each skater, carry forward prior-season (2023/24) PTS per 60 and multiply by 2024/25 total TOI hours.
- Regular season only (game_type=2). Missed games captured via TOI.

Overall accuracy:
- MAE 5.60
- RMSE 8.59
- MAPE 40.29%
- Correlation 0.935

Top-N (by actual points rank):
- Top 25: MAE 11.68, RMSE 13.27, MAPE 12.81%
- Top 100: MAE 11.52, RMSE 14.19, MAPE 16.46%
- Top 200: MAE 10.28, RMSE 12.87, MAPE 18.05%
- Top 300: MAE 9.54, RMSE 12.01, MAPE 20.15%
- Top 400: MAE 8.94, RMSE 11.56, MAPE 22.52%
- Top 500: MAE 8.28, RMSE 10.85, MAPE 24.80%

Notes:
- Similar performance to 2023/24; slightly better MAE/RMSE in several Top-N buckets.

