
### Notes

- Keep “no money in/out” invariant throughout. Use clear UI language (no bets/odds).
- Start binary Over/Under vs consensus; later expand to alternative lines or scalar markets.
- Prioritize schema auditability (timestamps, versions, provenance) for trust and resale.

### LMSR AMM Integration (from fantasy-lmsr-amm.yaml)

- Reference: `docs/prediction-markets/fs-prediction/fantasy-lmsr-amm.yaml`

- Config highlights
  - Liquidity `b`: default as fraction of expected per-market active VC; dynamic scaling by season phase and active traders.
  - Trading guards: `min_delta`, `max_delta_per_trade`, per-user exposure cap, optional close-only window.
  - Lock policy: rolling/global/per_round; `allow_close_only` prior to lock.
  - Resolution: dispute window; stat-correction policy: re-resolve and replay PnL.
  - Economy: VC symbol, weekly stipend, initial bankroll (no fiat conversion).
  - IPOs: cadence, markets per drop, contract lifetime.
  - Fairness: rebase when extreme pricing persists (split shares & b by factor).

- Entities → Tables
  - Market → `amm_markets(id, type, sport, subject, metric, threshold, outcomes[], b, q[], status, oracle_ref, created_at, locked_at, resolved_at, result_index, rebase_factor, ipo_round)`
  - Trade → `amm_trades(id, market_id, user_id, outcome_index, delta, cost_paid, price_before, price_after, created_at)`
  - Position → `amm_positions(user_id, market_id, outcome_index, shares, avg_cost)`
  - AuditLog → use global `audit_logs` with `target_type='amm_*'`

- Pure functions (engine-side)
  - `C(q,b)`, `price(q,b)`, `quote_trade(market, outcome_index, delta)` — implement as deterministic utilities with unit tests.

- Procedures (API-backed)
  - `execute_trade` → POST `/api/amm/markets/{id}/trade`
  - `lock_market` → POST `/api/amm/markets/{id}/lock`
  - `set_close_only` → POST `/api/amm/markets/{id}/close-only`
  - `resolve_market` → POST `/api/amm/markets/{id}/resolve`
  - `rebase_market` → POST `/api/amm/markets/{id}/rebase`

- HTTP API (extend base)
  - GET `/api/amm/markets/{id}` returns Market + current prices `price(q,b)`
  - POST `/api/amm/markets` (admin create)
  - POST `/api/amm/markets/{id}/quote` → `{ cost, prices_after }`
  - POST `/api/amm/markets/{id}/trade` → `{ cost, price_after, user_vc_balance }`

- Jobs/Schedulers
  - `ipo_drop`: create N markets/round from consensus forecasts; seed `b`; announce.
  - `lock_enforcer`: enforce close-only/lock by calendars and policy.
  - `resolver`: detect resolvable markets from oracle; trigger settlement.
  - `rebase_watcher`: apply splits based on sustained extreme prices.
  - `weekly_stipend`: stipend VC to active users with `audit_logs` entries.

- Metrics
  - `market_liquidity_b`, `trade_volume_vc`, `avg_price_move`, `per_market_active_vc`, `amm_pnl`.
