## Vision

Build a multi-provider fantasy hockey platform that lets a single user manage multiple pools across services (CBS, Yahoo, ESPN), delivers data-driven recommendations powered by Google Cloud pipelines, generates weekly personalized podcast content via Play.ht, and provides an AI-assisted chat and a prediction marketplace — all on a reliable Railway-hosted backend.

## Architecture Overview

- **Railway (Postgres + FastAPI)**: primary app backend, auth, user data, normalized league/team/roster views, recommendations API, chat service, marketplace service.
- **Google Cloud (BigQuery + GCS + Cloud Run/Batch)**: projections/statistics compute and storage; outputs replicated to Railway Postgres for fast API joins.
- **3rd-party Audio (Play.ht)**: podcast/script TTS generation and asset delivery. See `https://app.play.ht/home`.
- **Chrome Extension / Scrapers**: capture provider pages and push raw JSON to backend; backend normalizes into provider_* then upserts into internal schema.
- **Frontend (website)**: lives in `/Users/markhenderson/Cursor Projects/NHL-API/frontend`.

## Chrome extension ingestion & CBS credentials

- Ingestion
  - The `chrome-extension` is our primary CBS data capture tool. It collects structured tables from pages (Rules, Teams & Managers, Teams/All, Projections, etc.) and POSTs a consolidated payload to the backend.
  - Backend persists raw payloads (`extractions`) and upserts into provider_* and normalized internal tables (teams, rosters, rules, scoring, projections).

- Credentials & session tokens (CBS)
  - Goal: enable authenticated syncs after the user has completed any CBS verification challenges.
  - Storage model:
    - Use `provider_accounts` for per-user, per-provider credentials. Store `login` (email/username) and a `secret_ref` only (reference to an encrypted secret/token) instead of plaintext.
    - Persist short-lived session tokens/cookies as secrets via a vault/KMS; associate by `provider_accounts.id`.
  - Sync flow:
    - User signs in on CBS in the browser and passes any verification/2FA.
    - Extension or backend captures valid session tokens (with explicit user consent) and updates the `secret_ref`.
    - A backend worker uses these tokens to fetch/sync league data periodically (respecting rate limits and user-configured schedules).
  - Security & compliance:
    - Never store plaintext passwords. Enforce encryption-at-rest for tokens; rotate/expire tokens; scope them minimally.
    - Allow users to revoke tokens at any time. Log all sync attempts and token usage.

## Data stores and connection details

- **Railway Postgres (App DB)**: FastAPI services, users, normalized league/team/roster/rules, recommendations, chat, marketplace.
- **Projections & Stats Postgres (GCP)**: authoritative projections/stats replica used by APIs for joins.
  - Connection: `postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require`
- **Google Cloud BigQuery/GCS**: projections and model artifacts source-of-truth; nightly jobs export snapshots to the Projections & Stats Postgres and/or Railway Postgres as needed.

## Data Model (normalized, provider-agnostic)

- **Users**
  - users(id, email, display_name, timezone, created_at)
  - auth_identities(user_id, provider, subject, created_at)
  - api_keys(user_id, key_hash, scope, created_at, last_used_at)
  - user_settings(user_id, preferences JSON)

- **External Providers**
  - providers(id, slug, name)
  - provider_accounts(id, user_id, provider_id, login, secret_ref, created_at, last_verified_at)
  - provider_leagues(id, provider_id, external_id, slug, name, domain, sport, season, raw_meta JSON)
  - provider_teams(provider_league_id, team_id, team_name, abbrev, logo_url, owner_external_id, raw_meta)
  - provider_owners(provider_league_id, owner_id, display_name, email, avatar_url)
  - provider_player_map(provider_id, provider_player_id, nhl_player_id, last_seen_at)

- **Internal Core**
  - leagues(id, name, sport, season, owner_user_id, created_at)
  - league_links(league_id, provider_league_id)
  - teams(league_id, team_id, name, abbrev, logo_url, owner_user_id, created_at)
  - team_links(team_id, provider_team_id)
  - owners(id, display_name, email, avatar_url)
  - owner_links(owner_id, provider_owner_id)
  - memberships(user_id, league_id, team_id, role, created_at)

- **Rules & Scoring**
  - league_rules(league_id, roster_positions JSON, lineup_deadline, ir_options, scoring_mode, scoring_policies JSON, source_url, captured_at, raw_meta JSON)
  - scoring_rules(league_id, stat_code, stat_name, points, category)

- **Players & Projections**
  - nhl_players(id, full_name, pos_primary, birthdate, shoots, team_abbr)
  - projections(season, source, nhl_player_id, kind, metrics JSON, created_at)
  - projection_runs(id, season, source, started_at, completed_at, config JSON)

- **Rosters, Schedule, Transactions**
  - rosters_current(league_id, team_id, nhl_player_id, slot_type, status, salary, years, rookie, updated_at)
  - rosters_history(league_id, team_id, nhl_player_id, slot_type, status, salary, years, rookie, effective_from, effective_to, source_url)
  - scoring_periods(league_id, period_no, start_date, end_date, is_playoffs)
  - matchups(league_id, period_no, home_team_id, away_team_id, home_score, away_score, status)
  - transactions(id, league_id, occurred_at, txn_type, description, source_url, raw JSON)
  - transaction_items(txn_id, nhl_player_id, from_team_id, to_team_id, faab_delta, notes)

- **Recommendations**
  - recommendation_runs(id, user_id, league_id, team_id, season, inputs_ref JSON, started_at, completed_at)
  - recommendation_items(run_id, kind, subject_id, priority, action_payload JSON, rationale JSON, score)

- **Content & Podcast**
  - content_jobs(id, user_id, league_id, week, status, requested_at, completed_at, inputs_ref JSON)
  - content_assets(job_id, kind(script,audio,transcript), url(GCS), size, created_at)
  - outbound_api_clients(id, name, base_url, api_key_hash, scopes, created_at)
  - outbound_webhooks(id, job_id, client_id, endpoint, status, last_attempt_at, response_meta)

- **Chat**
  - conversations(id, league_id, team_id, topic, created_by_user_id, created_at)
  - participants(conversation_id, user_id, role)
  - messages(id, conversation_id, user_id, content, kind, created_at, tool_call JSON)
  - chat_tools(id, name, schema JSON, enabled)

- **Prediction Marketplace**
  - markets(id, league_id, title, status, created_at)
  - outcomes(market_id, outcome_id, title, status, implied_prob)
  - orders(id, user_id, market_id, outcome_id, side, price, size, status, placed_at)
  - trades(id, order_buy_id, order_sell_id, outcome_id, price, size, executed_at)
  - user_wallets(user_id, balance, currency, updated_at)
  - compliance_kyc(user_id, provider, status, doc_refs JSON)

## Player identity mapping

- Each fantasy provider uses its own player IDs distinct from NHL IDs. We will maintain a canonical mapping:
  - `provider_player_map(provider_id, provider_player_id, nhl_player_id, last_seen_at)`
  - Constraints: `UNIQUE(provider_id, provider_player_id)`; index on `(nhl_player_id)` for fast joins.
  - Population: updated on every ingestion from provider pages/APIs; backfilled by heuristics (name, team, position) when needed.
  - Usage:
    - Normalize provider rosters/transactions into internal rows keyed by `nhl_player_id`.
    - Join provider projections/stats to internal `nhl_players` and downstream analytics.
    - Support re-ingestion without breaking references via idempotent upserts.

## Data Flow

1) Extension/Scrapers → Railway: `extractions` raw → provider_* normalized → internal core tables.
2) GCP pipelines → BigQuery: projections computed, exported/snapshotted nightly → replicated to Railway `projections` for fast API joins.
3) API (Railway) → Frontend/Integrations: user-scoped endpoints (overview, waivers, recs), public league endpoints, and Play.ht content jobs.

## Simulations

- This project includes league simulation tooling and historical run artifacts in:
  - `/Users/markhenderson/Cursor Projects/NHL-API/uhhp_simulations`
- We will expose simulation inputs/outputs via internal endpoints for recommendation scenarios and content generation (weekly podcast narratives and previews).

## Play.ht Integration (podcast)

- Service: Play.ht for TTS generation (`https://app.play.ht/home`). API quickstart and headers per docs: `https://docs.play.ht/reference/api-getting-started`.
- Auth & endpoints (per docs):
  - Headers: `X-USER-ID: <YOUR_USER_ID>`, `AUTHORIZATION: <YOUR_API_KEY>`, plus `Content-Type`.
  - Streaming TTS: `POST https://api.play.ht/api/v2/tts/stream` (accepts `audio/mpeg`).
  - Batch TTS: Create job and poll for completion (v2.3 Batch Text-to-Speech endpoints).
- SDK options:
  - Node: `npm install playht`
  - Python: `pip install pyht`
- Our flow:
  - API creates `content_jobs` with script, voice selection, voice engine (e.g., PlayDialog), output format (mp3), and desired delivery (stream or batch).
  - Worker (Railway job or Cloud Run) calls Play.ht with the above headers, streams or polls for completion, and writes audio/transcript to GCS.
  - Persist GCS links in `content_assets`; return signed URLs to clients and 3rd parties.
- Security:
  - Store Play.ht `userId`/`apiKey` in Railway secrets; worker reads from env. Do not store plaintext in DB.
  - Rate-limit content jobs per user and per league to control cost.
  - Capture response metadata (duration, voice, engine, token usage if exposed) in `content_assets`.

## Change Management Plan (Phased)

Phase 0 – Foundations (Railway + GCP) [Week 0-1]
- Stand up Railway Postgres schemas (users, providers, internal core).
- Wire auth (Kinde/Password) → `users` + `auth_identities`, issue API keys.
- Provision GCP BigQuery datasets and GCS buckets for projections/assets.

Phase 1 – Provider Ingestion & Normalization [Week 1-2]
- Update extension/backend to write to `provider_*` then upsert into internal `leagues/teams/rosters`.
- Implement owner/team linking and user `memberships` across providers.
- Backfill existing CBS data into normalized tables.

Phase 2 – Core Endpoints & UI [Week 2-3]
- User-scoped: `/api/user/leagues`, `/api/user/league/{id}/overview`, `/waivers`, `/recommendations`.
- Public: `/api/public/league/{slug}/state`, `/schedule`, `/transactions`.
- Add caching for hot queries (per league snapshot).

Phase 3 – Projections & Recs [Week 3-4]
- GCP pipeline for nightly projections; publish to BigQuery; replicate to Railway.
- Recommendations service (Cloud Run) writes `recommendation_*` tables.
- Surface recs in UI + via API.

Phase 4 – Podcast Generation [Week 4-5]
- Implement `content_jobs` and worker calling Play.ht.
- Generate weekly episode per user/league; store to GCS and index in `content_assets`.
- Expose `/api/integrations/content/jobs` and `/assets` for 3rd-party.

Phase 5 – Chat & Marketplace [Week 5-7]
- Chat service with AI tool-calls (waivers, trade_eval) tied to internal IDs.
- Prediction marketplace tables + minimal matching engine; wallet stub (credits) and compliance stubs.

Phase 6 – Hardening & Ops [Week 7-8]
- RBAC, rate limits, audit logs; background jobs; backups/DR.
- Observability (metrics, tracing); load testing; cost monitoring.

## Security & Ops Notes

- Credentials: store provider secrets only via KMS/secret manager references.
- PII: minimize fields; encrypt at rest; enable row-level scoping per membership.
- Backups: Railway snapshots; GCS lifecycle for assets; export BigQuery snapshots.
- Indexing: (league_id, team_id) for rosters; (league_id, occurred_at) for transactions; unique constraints on links/maps.

## Next Steps

- Approve schema groups (Users, Providers, Internal Core).
- Generate SQL migrations and stub services.
- Migrate existing CBS data; cut over endpoints to normalized reads.



## Current progress

- Backend/API
  - Added user-scoped league overview endpoint and public waivers/schedule/transactions; owners are now persisted and wired to teams.
  - Migration runner updated to apply all SQL files sequentially.

- Database (Railway)
  - Applied migrations: providers/accounts/leagues/teams/owners, provider_player_map, canonical memberships (+legacy backfill), new_cbs_* hardening (uniques/indexes), projections snapshot, recommendations/content, content ingestion.

- Plan alignment
  - Delivers Phase 0/1 core DB work and part of Phase 2 endpoints.

- Immediate next steps
  - Implement provider account connect/revoke/token-status endpoints; add background sync worker using stored tokens.
  - Tighten CORS and add rate limiting middleware; add health/metrics endpoints.

## Remaining tasks

- Worker deploy: deploy sync worker on Railway with env; schedule and alerts.
- Auth + cookies capture UI for provider connect/status/revoke.
- Sync robustness: domain detection, retries/backoff, 2FA detection, richer parsing, telemetry.
- Security/ops: lock CORS; add rate limiting; enforce x-api-key on import; DB health checks; metrics.
- Data normalization: backfill normalized views; migrate memberships; create unified views.
- Projections pipeline: nightly BigQuery → Postgres replication and validation.
- Recommendations: generator service + API exposure.
- Content ingestion: RSS/social polling worker; feed/prompts/jobs; Play.ht runner integration.
- Frontend: provider UI, league pages (user-scoped endpoints), content UIs; later chat/marketplace UIs.
- Testing/docs: unit/integration/e2e; runbooks and secrets policy.
## Content ingestion and generation infra

- Monitored sources
  - RSS feeds: official team sites, league news, analytics blogs. User-configurable via `content_sources` table.
  - Social: X/Twitter lists, Reddit subs, YouTube channels (where permitted). Use connectors or 3rd-party APIs; store OAuth tokens via `secret_ref` if needed.

- Components
  - Scheduler: cron jobs (Railway or Cloud Run) to poll sources at intervals (e.g., 5–15 min); dedupe with URL/hash.
  - Queue: lightweight work queue (e.g., Postgres advisory queue or Redis if added) to process items.
  - Processor: text extraction/cleaning, entity tagging (players/teams), topic classification; persist to `content_items` with metadata.
  - Recommender hooks: link items to leagues/teams/users via memberships and player/entity matches; generate prompts for podcast/newsletters.
  - Storage: raw + normalized text (GCS for large assets), references to source URLs, and attribution.

- Schema (sketch)
  - content_sources(id, user_id, kind[rss, social], url_or_handle, filters JSON, active, created_at)
  - content_items(id, source_id, title, url, published_at, text, entities JSON, hash, created_at, UNIQUE(hash))
  - content_prompts(id, item_id, user_id, league_id, prompt_text, created_at)
  - content_jobs(id, user_id, league_id, kind[podcast, summary], status, requested_at, completed_at)
  - content_assets(job_id, kind[script,audio,transcript], url, size, created_at)

- APIs
  - POST /api/user/content/sources (create/update/delete/list)
  - GET /api/user/content/feed (personalized feed by memberships and filters)
  - POST /api/user/content/prompts (create generation prompt)
  - POST /api/user/content/jobs (kick off podcast/summary) → Play.ht integration for audio

- Notes
  - Respect robots.txt and platform ToS; use official APIs where required.
  - Rate-limit polling; exponential backoff on failures.
  - Attribute sources in all content; store provenance.