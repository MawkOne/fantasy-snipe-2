## UHHP Draft Tool – Architecture and Implementation Spec

### Goals
- Build a robust auction draft tool for UHHP where GMs can join by email, participate live, manage budgets, and see cap impact in real time.
- Support multiple projection lists (JSON) selectable per GM.
- Expose a master JSON “single source of truth” for teams, owners, rosters, contracts, cap, and RFA/UFA state.
- Persist all draft actions with deterministic order, tiebreakers, and recovery.
- Allow solo testing without other users present.

### Roles and Authentication
- **Roles**: admin, commissioner, GM, viewer.
- **Membership**: a user can belong to exactly one team per league via `cbs_user_memberships`.
- **Invites**: email-based with expiring tokens; invitee becomes GM on accept; reassignable by commissioner.

### Data Model (DB) – Additions/Updates
- **Users**
  - Table: `users` (id, email, name, created_at, last_login_at, role)
- **Invitations**
  - Table: `invitations` (id, league_slug, team_id, email, token, status[pending|accepted|expired|revoked], invited_by_user_id, expires_at, created_at)
  - Indexes on `(league_slug, email)`, `(token)`, `(team_id)`
- **Teams & Memberships**
  - Existing: `cbs_teams`, `cbs_user_memberships` (ensure `unique(user_id, league_slug)` and `unique(team_id, league_slug)`)
  - Add `cbs_teams.logo_url` if missing
- **Players & Mapping**
  - Existing: `cbs_players (nhl_player_id, first_name, last_name, full_name)`
  - Existing: `cbs_player_map (cbs_player_id, nhl_player_id, nhl_first_name, nhl_last_name)`
  - Existing: `player_details (player_id, birth_date, landing_url)` in NHL DB; ensure local sync when needed
- **Rosters & Contracts**
  - Existing: `cbs_rosters (league_slug, team_id, nhl_player_id, cbs_player_id, slot_type[A|I], salary, years)`
  - Add: `contract_start_year`, `contract_end_year`, `status[rfa|ufa]` persisted (computed from birth_date but cached per league year)
  - Add index `(league_slug, team_id)`
- **Auctions**
  - Existing: `cbs_auctions` (id, league_slug, nominated_player_id, nominating_team_id, min_bid, status[pending|active|finalized|void], started_at, ends_at, winner_team_id, winning_bid, tie_breaker_note)
  - Existing: `cbs_auction_bids` (auction_id, team_id, amount, placed_at, is_highest, sequence)
  - Add: `auction_order` table: (league_slug, sequence_position, team_id, is_active, last_nominated_at)
  - Add: `auction_events` append-only audit (league_slug, event_type, payload_json, created_at, actor_user_id) for replay/debug
- **Budgets & Caps**
  - Table: `cbs_caps` (league_slug, cap_limit default 100, season_year)
  - Table: `cbs_team_budgets` (league_slug, team_id, budget_remaining, updated_at)
- **Projection Sources**
  - Table: `projection_sources` (id, slug, display_name, season_year, is_default)
  - Existing: `fantasy_player_projections` must include `source_slug`
  - Table: `team_projection_preferences` (league_slug, team_id, source_slug) and optionally `user_projection_preferences` for per-user overrides
- **Materialized Master State (optional for performance)**
  - View/table: `league_master_state` snapshot fields: team->roster with salaries, birthdates, RFA/UFA, cap usage; updated via triggers or scheduled refresh

### Master JSON (“Single Call”) and Endpoint Contracts
- **GET** `/api/public/cbs/league/{slug}/draft_state`
  - Includes:
    - League: cap_limit, scoring rules, roster limits
    - Teams: id, name, logo_url, owner GM (user), budget_remaining
    - My Membership: `team_id`, permissions
    - Rosters: by team → list of { nhl_player_id, player_name, position, salary, years, contract_end_year, status[rfa|ufa], birth_date }
    - Available Players: list of UFAs + RFAs (flag `has_matching_rights_team_id` for RFA)
    - Auction: current state (order, active auction with countdown, current high bid, bids), last finalized results
    - Projection: available `projection_sources`, current selected for user/team
    - Caching: ETag/If-None-Match; server invalidates on auction events
- **GET** `/api/public/cbs/league/{slug}/auction/state`
  - Active auction and queue; repeat in `draft_state` but separable for polling
- **GET** `/api/public/cbs/league/{slug}/auction/available`
  - Full searchable list with filters; include `is_rfa` and `rights_team_id` when applicable
- **POST** `/api/public/cbs/league/{slug}/auction/nominate`
  - Body: { player_id, opening_bid }
  - Validates: nominating team == turn, player eligible, budget, roster slots
- **POST** `/api/public/cbs/league/{slug}/auction/bid`
  - Body: { auction_id, amount }
  - Validates: greater than current, within budget, not already all-in locked by roster constraint
- **POST** `/api/public/cbs/league/{slug}/auction/finalize`
  - Commissioner or auto when timer expires; writes roster, adjusts budgets, advances order; handles RFA match window
- **POST** `/api/cbs/league/{slug}/budget/set`
  - Body: { team_id, budget } — commissioner or team owner if allowed by league settings
- **GET** `/api/public/cbs/league/{slug}/projections/sources`
- **POST** `/api/cbs/league/{slug}/projections/select`
  - Body: { team_id?, user_pref?, source_slug }
- **Invitations**
  - POST `/api/cbs/league/{slug}/invites` { team_id, email }
  - GET `/api/cbs/league/{slug}/invites`
  - POST `/api/public/invites/accept` { token }
  - POST `/api/cbs/league/{slug}/invites/resend` { invite_id }
  - POST `/api/cbs/league/{slug}/invites/revoke` { invite_id }

### Real-Time Updates
- **WebSocket** `/ws/cbs/league/{slug}`
  - Events:
    - `membership_joined`, `invite_sent`, `invite_accepted`
    - `auction_nominated`, `bid_placed`, `auction_finalized`, `auction_timer`
    - `roster_updated`, `budget_updated`, `cap_updated`
    - `projection_source_changed`
  - Fallback: Long-polling with ETag if WS not available
- **Concurrency**
  - Use optimistic locking by auction_id and `sequence` on bids
  - Server-side single-writer guarantees for finalize; dedup by idempotency key

### Auction Mechanics
- **Order**
  - Track rotating `auction_order`; pointer advances on finalize or pass
  - Allow commissioner to reorder; persist history
- **Nomination**
  - Only current team may nominate; one active auction per league
  - Validate eligibility: not rostered; RFAs allowed; correct positions left
- **Bidding**
  - Strictly increasing integer bids; min increment config (e.g., 1)
  - Tiebreaker: highest amount wins; ties resolved by earliest timestamp; if exact-tie window rule exists in code, honor it and log `tie_breaker_note`
- **Timer**
  - Restart small countdown on each new top bid; auto-finalize on expiry
- **Finalize**
  - Write to `cbs_rosters`, decrement `team_budget`, record `auction_events`
  - For RFA: notify rights team with match window (configurable). If matched: rights team takes at final price; if not: winner keeps.
  - Update `auction_order` next pointer (and any tiebreak “bump” rules required by code)
- **Recovery**
  - If server restarts mid-auction, reconstruct from `cbs_auctions` + `cbs_auction_bids`
  - Admin “void” and “replay” controls: create a replacement auction for the same player

### Cap and Budget Management
- Cap usage recalculated on every roster change; considers only Active `A` slots; `I` slots excluded or discounted per league rule.
- Prevent bids that would exceed cap when player assigned; optionally allow “over-cap temporarily” flags for in-progress auctions per league config.
- Team-settable budgets in “My Team” capped by league cap; audit changes in `auction_events`.

### Projection Lists
- Ingest JSON files from `Projections/2025/` and similar folders into `fantasy_player_projections` keyed by `source_slug`.
- GM can select source at runtime; UI reflects “Pro FTPS” from selected source.
- Cache per-league, per-source FP computations; invalidate on selection change or scoring rules update.

### RFA/UFA Model
- Master JSON includes `status` computed from `player_details.birth_date` and league year cutoff (July 1); persisted snapshot fields in `cbs_rosters`.
- Players not on any team → `UFA`.
- RFAs tied to a team remain nominatable; the rights team can match after finalize within configured window; enforce via a pending state before final commit or a final-with-recall path.

### Invitations Flow (Cog in Top Nav)
- Commissioner clicks cog → “Invite GM”
  - Inputs: team selection, email
  - Backend creates `invitations` row, sends email (or shows accept link for manual copy in dev)
- Accept Link → Auth/login → `POST /invites/accept` → creates/updates `cbs_user_memberships`
- Edge cases: duplicate invite to same email/team; expiration; revocation; reassignment

### Frontend Changes
- **Top Nav Cog**
  - Invite management modal: list pending, resend, revoke; create invite
- **My Team**
  - Budget set control and cap summary; live roster list; projection source selector
  - Real-time updates via WS; optimistic updates with server reconciliation
- **Cheat Sheet**
  - Source selection affects list; filters by position; visual RFA badge (with rights team)
- **Auction Panel**
  - Left: nomination order with current pointer; pass controls per team (if allowed)
  - Center: current nominated player; live bid stream; countdown
  - Right: available players; search; filters; “nominate” exposed only if it’s your turn

### Edge Cases and Failure Modes
- Duplicate bids at same amount/time → tie resolved by earliest `placed_at` then by sequence
- User disconnects → auto-pass on timer expiry; no implicit bid
- Winning bid but roster limit exceeded (position constraints) → all the user to breach the limits. They can make changes later. 
- Changing projection source mid-auction → allowed; affects only UI numbers, not auction mechanics
- Invite token reuse/expired → safe error; offer to request a new invite
- Data corrections (player mapping/name changes) during draft → read from `nhl_player_id`; name changes do not affect identity

### Solo Testing Mode
- Commissioner toggle: “Solo Test Mode”
  - User can act-as any team via dropdown in dev only
  - Optionally spawn bot bidders with simple heuristics (config off by default)
  - Flag league as sandbox; isolated data from production league or use separate slug
  - Clear/reset league state with one click in dev: purge auctions, rosters (dev-only endpoint)

### Observability and Audit
- Append-only `auction_events` for all actions with user_id and payload for replay and dispute resolution
- Structured logs on finalize with computed deltas (budget, cap, roster)

### Security and Validation
- Role checks on all mutating endpoints
- League scoping on all queries (never leak across leagues)
- Idempotency keys for bid/finalize calls to prevent double-commit on retries
- Rate limiting on bid endpoints to prevent abuse

### Step-by-Step Execution Plan
1. Migrations
  - Create `invitations`, `auction_order`, `auction_events`, `cbs_caps`, `cbs_team_budgets`, `projection_sources`, `team_projection_preferences`; add fields to `cbs_rosters` as above.
2. Backend
  - Implement invites CRUD and accept.
  - Extend `draft_state` to include: budgets, projection sources/prefs, RFA rights, enhanced auction state.
  - Implement budget set, projection select.
  - Harden auction endpoints: validate cap/slots; add RFA match flow; audit events.
  - Add WebSocket for league events; broadcast on all auction and roster mutations.
3. Ingestion
  - Load projection JSONs with `source_slug`; register in `projection_sources`.
  - Ensure `fantasy_player_projections` keyed by `nhl_player_id` and `source_slug`.
4. Frontend
  - Top nav cog → Invite modal.
  - My Team: budget control; projection selector; real-time roster/cap updates.
  - Auction UI: live bids, timer, order; nominate/ bid flows; pass control if supported.
  - Available players: RFA badge + rights team label; filters and search.
5. Solo Test
  - Add league flag and “act-as team” in dev builds; reset endpoints for sandbox.
6. QA
  - Multi-user simulation (two browsers): bid conflicts, timer expiry, finalize, RFA match.
  - Cap limit enforcement; roster slot constraints.
  - Projection switching; invite accept/revoke flows.
  - Recovery: restart backend during active auction → state reconstructs correctly.
7. Deploy
  - Run migrations; restart backend; restart frontend.
  - Seed `projection_sources`; verify `draft_state` shape matches UI needs.

### Minimal JSON Shapes (examples)
- Projection source:
```json
{ "slug": "uhhp_2025_v1", "display_name": "UHHP 2025 v1", "season_year": 2025, "is_default": true }
```
- Roster entry:
```json
{ "nhl_player_id": 8483457, "player_name": "Lane Hutson", "position": "D", "salary": 3, "years": 2, "contract_end_year": 2027, "status": "rfa", "birth_date": "2004-02-14" }
```
- Auction state:
```json
{ "active": { "auction_id": 123, "player_id": 8483457, "nominating_team_id": 6, "current_high_bid": 5, "current_high_team_id": 6, "ends_at": "2025-09-15T20:00:00Z" }, "order": [{ "team_id": 6 }, { "team_id": 2 }, { "team_id": 9 }] }
```


