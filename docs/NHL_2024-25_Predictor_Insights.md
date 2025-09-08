### NHL 2024–25 Strength-Specific Predictor Insights

Date: 2025-08-27

#### Scope
- Season: 2024–25 (NHL season code 20242025)
- Targets: Goals, Assists, Points (per game)
- Exclusions: When predicting a target, directly corresponding target metrics are excluded (e.g., predicting Points excludes Goals and Assists as predictors).

#### Data Sources
- `player_game_stats` (core boxscore)
- `player_game_advanced_metrics_flat` (CF/FF/SF/GF, rates, PDO, TOI_seconds)
- `player_shift_metrics` (strength state per shift; teammates on ice)
- `game_events` (SHOT/GOAL with coordinates)
- `games` (dates, season, game_type)
- `player_details` (birth_date)

#### Pipeline Improvements (Strength + Location)
- True shots/goals by strength (EV/PP/SH): mapped events to shifts using period + timestamps
  - For each shot/goal event, infer the player’s on-ice `strength_state` via `player_shift_metrics` time window.
  - Aggregates per player-game: `shots_true_{EV,PP,SH}`, `goals_true_{EV,PP,SH}`.
- Shot location by strength: average Euclidean distance and |x| per strength (`avg_dist_{EV,PP,SH}`, `avg_abs_x_{EV,PP,SH}`).
- Fallback estimates for strength shot counts: if true counts missing, use TOI-share to allocate total shots.
- Context features: teammate variety (distinct line variants), average teammates on ice.
- Age at game date (years) from `player_details.birth_date` and `games.game_date`.
 - New (enhanced run): xG proxy per strength from shot distance (logistic transform), and grouped CV by player (GroupKFold) for out-of-player validation.

#### Composite / Derived Features
- `finishing_index = goals / shots` (per game; 0 when shots = 0)
- `possession_index = mean(CF60, FF60, SF60)`
- `pp_exposure = toi_PP_min`, `ev_burden = toi_EV_min`

#### Modeling
- LassoCV (standardized; 5-fold CV) for sparse linear combos
- RandomForestRegressor (n=400; 5-fold CV) for non-linear importance

#### Results (high-level)
- Goals
  - R²: Lasso ≈ 0.766 ± 0.008; RF ≈ 0.988 ± 0.005
  - Top drivers:
    - `finishing_index` (dominant)
    - `shots_EV_best` (true EV shots; fallback to EV TOI-share)
    - `shots_PP_best` (smaller but consistent)
    - Small contributions: `GF`, `PDO` (negative), `SF60` (negative), `shots_SH_best`, EV TOI

- Assists
  - R²: Lasso ≈ 0.127 ± 0.009; RF ≈ 0.148 ± 0.006 (harder signal)
  - Top drivers:
    - Rate/production/usage proxies: `GF60`, `shots_EV_best`, `shots_PP_best`, EV TOI
    - On-ice mixing: `teammate_variants` (line variety)
    - Some possession value from `CF`

- Points
  - R²: Lasso ≈ 0.435 ± 0.008; RF ≈ 0.490 ± 0.006
  - Top drivers:
    - `finishing_index` (strong)
    - `GF60`, `shots_EV_best`, `shots_PP_best`
    - On-ice mixing and time: `teammate_variants`, `toi_EV_min`
    - Modest roles: `PDO` (negative), `TOI_seconds`

##### Enhanced run deltas (with xG proxy + grouped CV)
- Assists: RF R² increased slightly to ≈ 0.152 (from ≈ 0.148); top drivers remain `GF60`, EV/PP shots, `teammate_variants`, EV TOI.
- Goals/Points: metrics and importances consistent; xG proxy did not materially shift top features in this pass.
- Takeaway: EV/PP shot volume, finishing_index, GF60, and on-ice mixing remain the strongest signals.

#### Suggested Simple Formulas (for scoring proxies)
- Goals predictor (per game):
  - `0.65·finishing_index + 0.25·shots_EV_best + 0.10·shots_PP_best`
- Assists predictor:
  - `0.35·pp_exposure + 0.20·teammate_variants + 0.15·CF + 0.15·toi_EV_min + 0.15·shots_EV_best`
- Points predictor:
  - `0.35·finishing_index + 0.20·GF60 + 0.15·shots_EV_best + 0.15·pp_exposure + 0.10·teammate_variants + 0.05·toi_EV_min`

Notes:
- These are interpretable baselines informed by model attributions; coefficients can be refit via ridge/lasso on holdout.

#### Key Takeaways
- Shots on goal: EV shots matter most; PP shots further boost Points.
- Ice time: EV TOI consistently helps (esp. Points); PP TOI aids Points; SH TOI minimal.
- Who they play with: teammate variety and avg teammates on ice add meaningful signal for Assists/Points.
- Where they shoot from: current location proxies were weak; a richer distance/angle-by-strength model may increase impact.
- Age: low short-horizon predictive value at game level in-season.
- Advanced metrics: `finishing_index` dominates Goals; `GF60` and possession contribute to Points/Assists.

#### Repro Steps
- Strength+location analysis:
  - `python scripts/analyze_strength_predictors.py --season 20242025 --limit 30000`
- Multi-metric discovery (baseline):
  - `python scripts/discover_predictors.py --season 20242025 --limit 40000`

#### Next Steps
- Enrich shot location: compute true shot distance/angle by strength (done) and consider expected goal models (xG via shot context).
- Add true strength splits for assists (event parsing for primary/secondary assists with strength at event time).
- Out-of-sample validation: player-level rolling windows and season-level generalization.
- Persist per-player season summaries with attributions; track drift weekly.

### Player Archetype Clusters (2024–25)

- Method: per-position KMeans on standardized per-60 and usage features (goals/assists/points/shots per 60, avg TOI, finishing index). k chosen by silhouette (k∈[3..8]).
- Outputs: `docs/cluster_assignments_{centers|wings|defence}_2024-25.csv`, `docs/cluster_meta_2024-25.json`.

Summary (updated with position-relative scoring and age):
- Centers (k=3, silhouette≈0.579)
  - 0: Depth/Role Player
  - 1: Sniper
  - 2: Playmaker

- Wings (k=3, silhouette≈0.602)
  - 0: Depth/Role Player
  - 1: Sniper
  - 2: Playmaker

- Defence (k=3, silhouette≈0.514)
  - 0: Playmaker
  - 1: Depth/Role Player
  - 2: Defensive Anchor

Notes:
- Labels are heuristic from cluster centroids and now consider position-relative scoring and age; can refine with domain thresholds (e.g., “Offensive Driver”, “Shutdown D”) after adding DZ/OZ starts, on-ice GA, blocks/hits context.


Target: GOALS
  Lasso R^2: 0.764 ± 0.007
  Lasso top features:
    - finishing_index           +0.314
    - shots_EV_best             +0.079
    - GF                        +0.077
    - shots_PP_best             +0.041
    - PDO                       -0.030
    - SF60                      -0.027
    - shots_SH_best             +0.018
    - SF                        -0.014
    - GA                        -0.013
    - teammate_variants         -0.009
  RF R^2: 0.988 ± 0.002
  RF top features:
    - finishing_index           0.9309
    - shots_EV_best             0.0567
    - shots_PP_best             0.0043
    - shots_SH_best             0.0028
    - ev_burden                 0.0006
    - toi_EV_min                0.0006
    - teammates_on_ice_avg      0.0004
    - GF                        0.0004
    - teammate_variants         0.0004
    - PDO                       0.0003
Target: ASSISTS
  Lasso R^2: 0.127 ± 0.012
  Lasso top features:
    - GF                        +0.244
    - TOI_seconds               -0.181
    - CF                        +0.113
    - CF60                      -0.070
    - teammate_variants         +0.062
    - finishing_index           -0.057
    - teammates_on_ice_avg      -0.042
    - CA                        -0.030
    - SF60                      -0.029
    - shots_EV_best             +0.026
  RF R^2: 0.152 ± 0.021
  RF top features:
    - GF60                      0.1098
    - shots_EV_best             0.0626
    - teammate_variants         0.0594
    - shots_PP_best             0.0589
    - TOI_seconds               0.0539
    - ev_burden                 0.0517
    - toi_EV_min                0.0515
    - toi_SH_min                0.0494
    - teammates_on_ice_avg      0.0485
    - toi_PP_min                0.0374
Target: POINTS
  Lasso R^2: 0.433 ± 0.010
  Lasso top features:
    - GF                        +0.317
    - finishing_index           +0.256
    - TOI_seconds               -0.183
    - shots_EV_best             +0.105
    - CF                        +0.070
    - SF60                      -0.065
    - shots_PP_best             +0.061
    - PDO                       -0.055
    - teammate_variants         +0.054
    - CF60                      -0.039
  RF R^2: 0.488 ± 0.012
  RF top features:
    - finishing_index           0.3963
    - GF60                      0.0648
    - shots_EV_best             0.0457
    - GF                        0.0430
    - shots_PP_best             0.0379
    - teammate_variants         0.0358
    - TOI_seconds               0.0319
    - ev_burden                 0.0308
    - toi_EV_min                0.0307
    - teammates_on_ice_avg      0.0289
### 2023–24 Points Forecast Backtest (Top-N accuracy)

- Method: Prior-season PTS/60 carried forward × 2023–24 TOI (no injury model; actual TOI captures missed games)
- Overall: MAE 5.48, RMSE 8.48, MAPE 41.46%, Corr 0.939
- Top-N (by actual points rank):
  - Top 25: MAE 12.52, RMSE 15.38, MAPE 12.74%
  - Top 100: MAE 11.53, RMSE 14.17, MAPE 15.71%
  - Top 200: MAE 11.01, RMSE 14.04, MAPE 18.90%
  - Top 300: MAE 9.79, RMSE 12.73, MAPE 20.01%
  - Top 400: MAE 9.00, RMSE 11.77, MAPE 21.86%
  - Top 500: MAE 8.39, RMSE 11.08, MAPE 24.87%

Notes:
- Errors increase in relative terms (MAPE) deeper in the pool due to low point totals; correlation remains high overall.
- Next refinement: split EV/PP rates and apply team PP/EV deployment baselines; optionally add expected GP.