## Fantasy Forecasts Backend (Prediction Markets Twist)

This document specializes the base plan in `docs/prediction-markets/README.md` for the “Fantasy Forecasts” platform: chat-first forecasting, virtual-cash league staking (no real money), and a monetized aggregated-forecasts API for DFS and analytics.

### References

- See core scope, APIs, data model, and admin operations in: `docs/prediction-markets/README.md`
- Product blueprints: `docs/prediction-markets/fs-prediction.md/ai-instruction.md`, `docs/prediction-markets/fs-prediction.md/project.md`

### Core Domain Differences vs. a pure exchange

- Markets are forecast metrics on sports entities (player/team) for a season or window, resolved by official stats. Binary first (Over/Under consensus), extensible to multi or scalar later.
- No real-money; virtual cash (VC) only. VC is non-purchasable and non-convertible.
- Crowd + model forecasts are first-class inputs; aggregation produces consensus lines used for staking.
- Social layer: chat, moderation, leaderboards tightly integrated with forecasts and leagues.
- Monetization is via subscriptions to aggregated forecast data (API), not trading fees.

### Modules

1) Forecasts & Aggregation
- Submission: structured forecasts with CI, rationale, versioning, lock-after deadline.
- Aggregation engine: mean/median, trimmed mean, RP-weighted, time-decay; outlier controls.
- Accuracy tracking: MAE, Brier, calibration per user/metric; reputation weighting.
- Resolution: official stats pipelines; re-resolution on provider corrections.

2) Virtual-Cash Leagues (Skill-based game)
- League config: starting VC, stake caps, eligible markets, season windows; commissioner certification logs.
- Staking: VC on Over/Under vs consensus; adjustable positions; audit trails.
- Settlement: auto at resolution into `pnl_tx` ledger; leaderboards per league and global.

3) Chat & Moderation
- Rooms by sport/team/league; forecast-card embeds.
- Moderation queues: flags, mutes/bans, takedowns; immutable moderator audit.

4) Aggregated-Forecasts API (Paid)
- REST endpoints for players, aggregated forecasts, distributions, leaderboards.
- Plans/quotas, API keys, webhooks, usage metering, billing.

### HTTP API Surface (build on README.md)

- Forecasts
  - POST `/api/forecasts` (submit)
  - GET `/api/forecasts/{id}`
  - GET `/api/forecasts?playerId=&metric=&season=&userId=`
  - POST `/api/forecasts/{id}/publish` (lock)

- Aggregation
  - GET `/api/forecasts/aggregated?league=NHL&metric=PTS&season=2025`
  - GET `/api/forecasts/distribution?player_id=&metric=&season=`
  - GET `/api/accuracy/leaderboard?metric=&window=`

- Leagues & VC staking
  - POST `/api/leagues` (commissioner)
  - GET `/api/leagues/{id}`
  - POST `/api/leagues/{id}/stake` (place stake vs consensus line)
  - POST `/api/leagues/{id}/stake/{stakeId}/close`
  - GET `/api/leagues/{id}/leaderboard`

- Chat
  - WS `/ws/chat/{channel}` (moderation hooks)
  - POST `/api/mod/flags`, POST `/api/mod/actions`

- Paid API (subset, external)
  - GET `/api/pub/players/search?q=`
  - GET `/api/pub/players/{id}/projections?metric=&season=`
  - GET `/api/pub/forecasts/aggregated?league=&metric=&season=`
  - GET `/api/pub/accuracy/leaderboard?metric=&window=`
  - GET `/api/pub/meta/{resource}`

Note: Inherit system, auth, admin, market data, and rate-limit endpoints from `README.md` (rename “markets” to “forecast-markets” where helpful).

### Data Model Additions (extend README.md)

- `forecast(id, user_id, sport, season, entity_type, entity_id, metric, value, ci_low, ci_high, notes, published_at, version, status)`
- `aggregation(id, sport, season, entity_id, metric, agg_value, method, as_of)`
- `stake(id, league_id, user_id, forecast_id|consensus_id, side, amount_vc, placed_at, status)`
- `pnl_tx(id, user_id, league_id, stake_id, delta_vc, reason, created_at)`
- `accuracy_snapshot(forecaster_id, metric, window, mae, brier, n)`
- `league(id, commissioner_id, settings_json, created_at)`
- `league_member(league_id, user_id, starting_vc, current_vc)`

Reuse `users`, `api_keys`, `audit_logs`, `rate_limits`, etc. from `README.md`.

### Jobs & Pipelines

- Ingest official stats; normalize player/team IDs; backfill corrections.
- Aggregation cron (per sport/metric); on-demand recompute.
- Settlement worker: apply resolutions to stakes → ledger → leaderboards.
- Accuracy jobs: compute metrics snapshots, drift alerts.

### Admin & Compliance (augment README.md)

- Commissioner certification logs; dispute workflows for stakes/results.
- Moderator queues; evidence export packs (chat + forecast histories, hashes).
- Legal: ToS/Privacy versioning, forecast IP license acceptance, geo-messaging flags.

### Observability & Safety

- Data freshness dashboards (per sport feed), re-resolution SLA.
- Anti-abuse: stake caps, device/IP clustering, spam throttles.
- Backups, restore drills, immutable event logs for key entities.

### MVP Cut

- Forecast submission + publish; aggregation (mean/median); player pages.
- Leagues with VC staking vs consensus; auto settlement; leaderboards.
- Chat basic + moderation actions; admin audit logs.
- Paid API read-only endpoints; keys/plans/usage; rate limits.

### Notes

- Keep “no money in/out” invariant throughout. Use clear UI language (no bets/odds).
- Start binary Over/Under vs consensus; later expand to alternative lines or scalar markets.
- Prioritize schema auditability (timestamps, versions, provenance) for trust and resale.


