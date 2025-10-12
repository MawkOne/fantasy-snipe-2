## Prediction Markets Backend Plan

### Vision

Build a production-grade prediction markets backend inspired by established exchanges, supporting a central limit order book (CLOB), real-time market data, authenticated trading, robust risk management, market resolution/oracle flows, and operator tooling. This plan mirrors patterns from Polymarket and Kalshi while remaining provider-agnostic and modular.

### Functional Scope

- **Core market model**
  - Yes/No (binary) outcomes for MVP; extensible to multi-outcome and scalar.
  - Market lifecycle: draft → open → paused/halted → closed → resolved.
  - Tags, events, series for discovery and grouping.

- **Order book & trading (CLOB)**
  - Price-time priority, partial fills, crossing, post-only, batch orders.
  - Order lifecycle events: accepted, booked, partially filled, filled, canceled, rejected.
  - Market data: best bid/ask, depth snapshots, top-of-book, spreads, recent trades.

- **Risk & funds**
  - User balances in a base asset (centralized credits/USDC abstraction for MVP).
  - Pre-trade checks: price/size bounds, available balance, self-trade prevention.
  - Fees: maker/taker schedule; per-market overrides.
  - Positions/PnL: per market and aggregated.

- **Resolution/oracle**
  - Admin resolution with evidence; settlement jobs update balances/positions.
  - Optional dispute hooks for future phases; external oracle input ingestion.

- **Admin & operations**
  - Market creation/editing, trading halts, circuit breakers.
  - Health, metrics, audit logs, rate-limit monitoring.

- **Realtime**
  - WebSocket market channels (order book diffs, trades, status changes).
  - WebSocket user channel (authenticated) for order acks/fills and balance updates.

### Public HTTP APIs (MVP)

- **Markets & discovery**
  - GET `/api/markets` (filters: status, tags, eventId, search q)
  - GET `/api/markets/{marketId}`
  - GET `/api/events`, GET `/api/events/{id}`
  - GET `/api/tags`

- **Market data**
  - GET `/api/orderbook/{marketId}?levels=50` (L2; defaults sensible)
  - GET `/api/trades/{marketId}?since=<ts>&limit=200`
  - GET `/api/search?q=...`

- **System**
  - GET `/api/healthz`
  - GET `/api/metrics`
  - GET `/api/rate_limits`

### Authenticated HTTP APIs (trading)

- **Auth & API keys**
  - POST `/api/auth/login`
  - POST `/api/auth/api-keys` (create), DELETE `/api/auth/api-keys/{id}`

- **Orders**
  - POST `/api/orders` (single place)
  - POST `/api/orders/batch` (multiple places in one request)
  - POST `/api/orders/{id}/cancel`
  - POST `/api/orders/cancel` (bulk by filters)
  - GET `/api/orders/{id}`
  - GET `/api/orders?status=active`

- **Trades, positions, balances**
  - GET `/api/trades/me?marketId=&since=&limit=`
  - GET `/api/positions?status=open|closed`
  - GET `/api/balances`
  - GET `/api/fees`

### Admin HTTP APIs

- POST `/api/admin/markets` (create)
- PATCH `/api/admin/markets/{id}` (update)
- POST `/api/admin/markets/{id}/resolve` (resolution + settlement trigger)
- POST `/api/admin/halts/{marketId}` (halt), DELETE `/api/admin/halts/{marketId}` (unhalt)
- GET `/api/admin/metrics`
- GET `/api/admin/audit`

### WebSocket APIs

- **Market channel**: `wss:///ws/market/{marketId}`
  - Messages: order book diffs (price level updates), trades, market status changes.
  - Start with periodic L2 snapshots + incremental diffs.

- **User channel (auth)**: `wss:///ws/user`
  - Messages: order acks, rejects, cancels, fills, balance and margin updates, alerts.

### Data Model (Relational)

- **Identity & auth**
  - `users(id, email, status, created_at, ...)`
  - `api_keys(id, user_id, key_hash, label, created_at, last_used_at)`
  - `roles(user_id, role)` (e.g., admin)

- **Funds & fees**
  - `assets(symbol, decimals)` (MVP: single base asset)
  - `balances(user_id, asset, available, reserved)`
  - `ledger_entries(id, user_id, asset, delta, reason, ref_type, ref_id, created_at)`
  - `fee_schedules(id, maker_bps, taker_bps, rules_json)`

- **Discovery**
  - `tags(id, slug, name)`
  - `events(id, slug, name, description, start_at, end_at, tags[])`
  - `markets(id, event_id, slug, title, outcome_type, status, fee_schedule_id, created_at)`
  - `contracts(id, market_id, outcome, tick_size, min_price, max_price)`

- **Trading**
  - `orders(id, user_id, market_id, side, price, size, remaining_size, tif, post_only, status, created_at)`
  - `order_events(id, order_id, type, delta_size, price, created_at)`
  - `trades(id, market_id, price, size, taker_order_id, maker_order_id, created_at)`
  - `fills(id, trade_id, user_id, order_id, price, size, fee, created_at)`
  - `positions(user_id, market_id, outcome, size, avg_price, realized_pnl, unrealized_pnl)`

- **Market state & analytics**
  - `order_snapshots(id, market_id, snapshot_ts, levels_json)`
  - `market_stats(market_id, interval, open, high, low, close, volume, vwap, ts)`

- **Resolution & compliance**
  - `resolutions(market_id, status, resolved_outcome, evidence_url, resolved_at)`
  - `audit_logs(id, actor, action, target_type, target_id, meta, created_at)`
  - `halts(market_id, reason, created_at, released_at)`
  - `ip_blocks(cidr, created_at)`
  - `rate_limits(subject, window, limit, created_at)`

### Matching Engine & Risk (Design)

- **Engine**
  - Single-writer event loop per market; in-memory book with append-only event log.
  - Price-time priority; cross at submission; partial fills; post-only checks.

- **Risk**
  - Pre-trade: validate price bounds, size, self-trade prevention, available balance.
  - Post-trade: update positions, PnL, fees; create ledger entries; adjust `available` vs `reserved`.

### Auth, Rate Limits, Permissions

- **Auth**: API keys (HMAC or static for MVP), JWT/OAuth optional later. WS auth via headers or query token.
- **Permissions**: user vs admin routes. Enforce least privilege.
- **Rate limiting**: per-IP and per-key; burst + sustained windows with 429 responses and headers.

### Architecture & Infra

- **Services**
  - API Gateway (FastAPI): REST/WS, validation, auth, rate limits.
  - Matching Engine: dedicated service managing order books and execution.
  - Risk/Funds Service: collateral checks and ledger/balances.
  - Market Data: snapshots, diff streams, OHLCV aggregation; Redis for caches and pub/sub.
  - Resolution/Oracle: admin workflows and external inputs; settlement jobs.
  - Admin/Ops: metrics, audit, halts, market management.

- **Storage & tooling**
  - Postgres (primary store), Redis (cache/pubsub), Kafka/NATS (event bus),
  - Prometheus/Grafana (metrics), OpenTelemetry (tracing), S3/GCS (snapshots/backups).

### MVP vs Later Roadmap

- **MVP**
  - Binary markets, discovery, public market data.
  - Order placement/cancel (single and batch), active orders, trades history.
  - Balances, basic maker/taker fees, positions/PnL.
  - Admin market resolution and settlement.
  - WS: market channel + user channel (acks/fills).

- **Later**
  - Advanced order types (IOC/FOK/pegged/iceberg), conditional bundles.
  - Cross-margin and portfolio risk, dispute system.
  - FIX gateway, sandbox/demo environment, KYC/AML integration, fiat/USDC rails.
  - Comments, richer search (events/series/sports directories).

### Compliance & Operations Notes

- Geo/IP controls, content moderation (market eligibility), retention and audit.
- Incident runbooks: halts/circuit breakers, degraded mode, snapshot restore.

### References

- Polymarket Developer Quickstart — CLOB, orders, market data, WS, rate limits: https://docs.polymarket.com/quickstart/introduction/main
- Kalshi Developer Docs — API keys, sandbox, websockets, FIX, market data: https://docs.kalshi.com/welcome

### Admin & Operations

- **Admin HTTP endpoints**
  - Markets & discovery
    - POST `/api/admin/markets` (create)
    - PATCH `/api/admin/markets/{id}` (title, tags, tick_size, fee schedule, status)
    - POST `/api/admin/markets/{id}/resolve` (outcome, evidence_url)
    - POST `/api/admin/events` (create), PATCH `/api/admin/events/{id}`
    - POST `/api/admin/tags` (create), DELETE `/api/admin/tags/{id}`
  - Halts & circuit breakers
    - POST `/api/admin/halts/{marketId}` (reason)
    - DELETE `/api/admin/halts/{marketId}` (resume)
    - POST `/api/admin/global_halt`
    - DELETE `/api/admin/global_halt`
  - Fees & economics
    - POST `/api/admin/fee_schedules` (maker_bps, taker_bps)
    - PATCH `/api/admin/fee_schedules/{id}`
  - Risk & limits
    - POST `/api/admin/risk/limits` (per-user/per-market exposure caps)
    - POST `/api/admin/stp/policies` (self-trade prevention)
  - Users & access control
    - GET `/api/admin/users?query=`
    - PATCH `/api/admin/users/{id}` (role/status flags)
    - POST `/api/admin/api-keys/rotate` (admin keys)
  - Compliance & surveillance
    - GET `/api/admin/surveillance/reports?type=wash_trade|spoofing`
    - POST `/api/admin/ip_blocks` (CIDR)
    - DELETE `/api/admin/ip_blocks/{id}`
  - Webhooks & integrations
    - POST `/api/admin/webhooks` (url, secret, kinds)
    - PATCH `/api/admin/webhooks/{id}` (status, retry policy)
    - GET `/api/admin/webhooks/{id}/deliveries` (logs)
  - Operations
    - GET `/api/admin/metrics`
    - GET `/api/admin/audit`
    - GET `/api/admin/jobs?status=`
    - POST `/api/admin/jobs/{id}/retry`
    - POST `/api/admin/exports` (markets, trades, orderbooks)
    - POST `/api/admin/announcements` (banners)

- **Admin data tables (schema suggestions)**
  - `audit_logs(id, actor_user_id, action, target_type, target_id, meta, created_at)`
  - `halts(market_id, reason, created_at, released_at, created_by)`
  - `fee_schedules(id, label, maker_bps, taker_bps, rules_json, created_at)`
  - `risk_limits(id, subject_type, subject_id, market_id, limit_json, created_at)`
  - `stp_policies(id, policy_json, created_at)`
  - `ip_blocks(id, cidr, created_at, created_by)`
  - `webhooks(id, url, secret_hash, kinds, status, retry_policy_json, created_at)`
  - `webhook_deliveries(id, webhook_id, payload_hash, status, attempts, last_error, created_at)`
  - `admin_jobs(id, kind, payload_json, status, run_at, attempts, last_error, created_at)`
  - `data_exports(id, kind, params_json, location, status, created_at)`
  - `announcements(id, scope, message, starts_at, ends_at, created_by)`

- **Operational workflows**
  - Market lifecycle: draft → review → open → paused/closed → resolved → settled.
  - Incident response: trigger market/global halt, set banner, notify, investigate, resume.
  - Resolution & settlement: collect evidence, resolve, run settlement batch, reconcile ledger.
  - Surveillance: periodic reports, alert triage, remediation (blocks/limits).
  - Webhooks: delivery with retries and HMAC signing; dead-letter replays.

- **Observability & SRE**
  - Metrics: order throughput, WS backpressure, book staleness, latency, error rates, settlement lag.
  - Tracing: order lifecycle spans (API → engine → risk → ledger → WS ack/fill).
  - Runbooks: snapshot/restore, schema migrations, replay from event log, disaster recovery.
  - Capacity: WS fanout limits, snapshot cadence, Kafka/NATS topic partitioning (if used).

- **Access control & security**
  - Role-based access (admin/operator/auditor); dual-control for sensitive actions (manual ledger adj.).
  - API key rotation schedules; secrets management; signed admin actions captured in `audit_logs`.


