### UHHP Backend and API Plan (multi-pool, Kinde-auth)

#### Goals
- Support multiple independent pools (leagues) per season.
- Split data stores: Railway (fantasy, read/write, realtime) and GCP Postgres (NHL historical, read-only).
- Pool-scoped APIs, secure via Kinde authentication and role-based authorization.
- Persist real-time auction state, budgets, suggestions, and tie-break audit.

---

### Architecture Overview
- UI: Next.js app (existing frontend), calls internal API routes.
- Auth: Kinde (OIDC). Next.js middleware verifies tokens; API receives user identity + roles/claims.
- Datastores:
  - Railway Postgres (RW): multi-tenant fantasy schema, transactional state.
  - GCP Postgres (RO): canonical NHL data (players, teams, season stats, projections views).
- Join key: `nhl_player_id` everywhere.

---

### Multi-Pool Model (Tenancy)
- Every mutable row is scoped with `pool_id` (and `season` where relevant).
- Recommended tables (Railway):
  - `pools(id, name, slug, season, created_at)`
  - `pool_members(user_id, pool_id, role, created_at)`
  - `pool_teams(id, pool_id, name, abbrev, owner_user_id, created_at)`
  - `auctions(id, pool_id, season, status, created_at)`
  - `auction_orders(id, pool_id, season, order jsonb, updated_at)`
  - `auction_picks(id, pool_id, season, pick_no, nhl_player_id, team_id, pos, price, created_at)`
  - `bids(id, pool_id, pick_id, team_id, amount, created_at)`
  - `tie_audit(id, pool_id, pick_id, contenders jsonb, advantage_team_id, created_at)`
  - `contracts(id, pool_id, team_id, nhl_player_id, years, salary, fa_type, start_season, created_at)`
  - `projections_overrides(id, pool_id, season, nhl_player_id, source, fp, updated_at)` (optional)
  - `pool_slot_targets(id, pool_id, season, team_id, slot_id, pos, budget, suggested_nhl_player_id, updated_at)`
  - `pool_position_budgets(id, pool_id, season, team_id, pos, budget, updated_at)` (optional)

Indexes & constraints (examples):
```sql
-- Uniqueness within a pool
ALTER TABLE pool_teams ADD CONSTRAINT uq_pool_teams_name UNIQUE (pool_id, name);
ALTER TABLE pool_teams ADD CONSTRAINT uq_pool_teams_abbrev UNIQUE (pool_id, abbrev);

ALTER TABLE auction_picks ADD CONSTRAINT uq_picks UNIQUE (pool_id, season, pick_no);
CREATE INDEX idx_picks_pool_season ON auction_picks(pool_id, season);

ALTER TABLE pool_slot_targets ADD CONSTRAINT uq_slot UNIQUE (pool_id, season, team_id, slot_id);
CREATE INDEX idx_slot_targets_scope ON pool_slot_targets(pool_id, season, team_id);

CREATE INDEX idx_bids_lookup ON bids(pool_id, pick_id);
```

---

### NHL (GCP) Read-Only Schema (expected)
- `nhl_players(nhl_player_id PK, first, last, birthdate, shoots, pos_primary)`
- `nhl_teams(nhl_team_id PK, name, abbrev, active)`
- `seasons(nhl_player_id, season, team_abbr, gp, g, a, pim, toi, fp, ...)`
- Views to simplify joins:
  - `v_current_rosters(nhl_player_id, team_abbr)`
  - `v_latest_fp(nhl_player_id, season, fp)`

Access: create RO user, allow-list app IPs, use connection pooling.

---

### Authentication & Users (Kinde)
- Frontend: integrate Kinde SDK; users log in → receive ID token (JWT).
- Backend: Next.js API verifies Kinde JWT (issuer, audience). Extract `user_id`, email.
- On first authenticated call:
  - Upsert `users(id, email, created_at)` in Railway.
  - Optional invite/accept flow to join a pool → create `pool_members(user_id, pool_id, role)`.
- Authorization: check `pool_members` on each pool-scoped request; roles: `owner`, `gm`, `viewer`.

---

### API Surface (pool-scoped)
All routes are prefixed with `/api/pools/:poolId` (poolSlug works too). `season` optional where implicit.

- State
  - `GET /state` → auction picks, nomination order, roster snapshot, projections (pool overrides + GCP), budgets/targets.
  - Query merges Railway RW data with GCP RO views.

- Auction
  - `POST /bid` body `{ pick_id, team_id, amount }` → validates window; stores/upserts in `bids`.
  - `POST /pick` body `{ season, pick_no, nhl_player_id, team_id, price, pos }` → writes `auction_picks`; resolves tie per order; updates `auction_orders` (winner moved to bottom) and logs in `tie_audit`.

- Orders
  - `GET /order` → current order array
  - `PUT /order` → admin updates/reset

- Budgets & Suggestions
  - `GET /teams/:teamId/targets` → slot targets + position budgets
  - `PUT /teams/:teamId/targets/:slotId` body `{ budget?, suggested_nhl_player_id? }`
  - `PUT /teams/:teamId/position-budgets/:pos` body `{ budget }`

- Players/Projections
  - `GET /players?pos=&q=` → search with joins to GCP `nhl_players` & `v_current_rosters`
  - `GET /projections?source=` → pool overrides first; fallback to GCP view

Response contracts are pool-scoped and omit other pools’ data.

---

### Tie-Break Logic (per pool)
1) Initial order from `auction_orders.order` (nomination order).
2) On tie: winner is the GM highest in current order among tied teams.
3) After resolving, move that winner to end of order; persist.
4) Append `tie_audit` row: `{ pick_id, contenders, advantage_team_id }`.

---

### Budgets & Slot Targets (My Team)
- Persist per-slot inputs as the user types (debounced 300ms).
- Keep optimistic UI; reconcile on success.
- Suggested player selections update `suggested_nhl_player_id` only; clearing suggestion preserves `budget`.

---

### Caching & Performance
- Short-lived cache (60–300s) for read-heavy endpoints (state, players, projections), keyed by `pool_id`.
- Consider edge KV for small denormalized snapshots (current order, last 20 picks).
- If needed, nightly ETL copies `nhl_players`, `v_current_rosters`, `v_latest_fp` into slim Railway tables.

---

### Migrations / Environment
- Use a single migration tool (Prisma/Drizzle/SQL) targeting Railway.
- Environment variables:
  - `FANTASY_DATABASE_URL` (Railway RW - fantasy multi-pool schema)
  - `NHL_DATABASE_URL` (GCP RO - historical/canonical NHL data)
  - `KINDE_ISSUER`, `KINDE_AUDIENCE`, `KINDE_CLIENT_ID`, `KINDE_CLIENT_SECRET`, redirect URIs

---

### Realtime (optional, phase 2)
- WebSocket or server-sent events channels namespaced: `draft:pool:{poolId}` for bid updates, timer, pick reveals.

---

### Security & Auditing
- All queries include `pool_id` filter; enforce in service layer.
- Row-level audit tables if needed: `audit_log(id, pool_id, actor_user_id, action, payload, created_at)`.
- Principle of least privilege: GCP RO creds; Railway RW creds; rotate regularly.

---

### Initial Delivery Checklist
1) Create Railway schema with tables and indexes above.
2) Add Kinde auth (login, middleware, user bootstrap + pool membership).
3) Implement pool-scoped API routes (`/api/pools/:poolId/...`).
4) Wire frontend to new endpoints (poolId from subdomain or query).
5) Persist My Team slot targets and suggestions.
6) Implement tie-break order mutation + audit log in pick finalization.
7) Connect GCP RO DB and integrate `v_current_rosters` + `v_latest_fp` joins.

---

### Future Enhancements
- Per-pool projection sources and weights, custom tiers.
- Partitioning large tables by `season`.
- Read replicas and queue-based event ingestion for heavy analytics.


