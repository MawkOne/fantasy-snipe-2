# UHHP Auction Build Plan

Canonical rules: `docs/UHHP_AUCTION_RULES_2026.md`  
Machine-readable rules: `backend/config/uhhp_auction_rules_2026.json`  
Canonical frontend route: `/draft-room-uhhp`

## Goal

Keep the existing `/draft-room-uhhp` visual design while replacing prototype and insecure behavior with a server-authoritative, auditable silent-auction workflow suitable for local testing and eventual Coolify deployment.

## Current implementation status

- Canonical rules and machine-readable configuration are committed to source files.
- Migration `022_uhhp_auction_state.sql` defines the new auction state/audit schema.
- `import_uhhp_auction_2026.py` parses and validates all three league data sources plus skater and goalie projections in database-free dry-run mode.
- The dependency-free rule engine has tests for July 1 classification, valid bids, cancellation/replacement, No Sale, rotating tie priority, RFA decisions, and cap warnings.
- A secure viewer-safe read API contract exists for auction state and stage-filtered players.
- Migration/application against the target database and mutation endpoints are not complete yet.

## Phase 0 — Data and secrets

- [ ] Remove tracked `.env.local` files from Git.
- [ ] Add environment-file patterns to `.gitignore`.
- [ ] Rotate database and API credentials that have been committed.
- [x] Parse the private 12-team GM directory without exposing manager emails to client payloads; keep `public/gms.md` ignored and use `public/gms.example.md` as the committed template.
- [ ] Import the 2026 roster snapshot.
- [ ] Import the September 22 skater projection pool, skipping the report title/footer.
- [x] Import the full goalie projection pool from `public/goalies.csv`.
- [ ] Map players by CBS ID, then normalized name + position + NHL team as fallback.
- [ ] Enrich expired contracts with NHL ID and birthdate.
- [ ] Snapshot UFA/RFA status and controlling team for draft year 2026.

## Phase 1 — Database schema

Create versioned migrations for:

- [x] `auction_drafts`: league, season, stage, round, nomination pointer, status, version.
- [x] `auction_stage_teams`: order, active/passed status, pass timestamp.
- [x] Rotating tie-break priority per draft team.
- [x] `auction_nominations`: player snapshot, nominator, UFA/RFA status, controlling team and result fields.
- [x] `auction_bid_events`: submit, cancel, replacement, explicit zero, actor, sequence, idempotency key.
- [x] `auction_rfa_decisions`: match/pass, actor, timestamp.
- [x] `auction_events`: append-only audit/outbox events.
- [x] Contract/acquisition link from roster row to auction nomination.
- [x] One-active-auction constraint per league.
- [x] Unique effective bid sequence and nomination numbering.

Remove auction-related runtime `CREATE TABLE` and `ALTER TABLE` operations from request handlers.

## Phase 2 — Authentication and authorization

- [ ] Fix FastAPI auth dependency definition/import order.
- [ ] Choose one canonical user/membership model.
- [ ] Map authenticated users to one UHHP team and role.
- [ ] Remove client-authoritative `team_id` for ordinary GM mutations.
- [ ] Owner permissions: submit/cancel own bid; nominate only on own turn.
- [ ] RFA controller permission: Match/Pass only for owned RFA.
- [ ] Commissioner permissions: reveal, order management, stage transitions, corrections.
- [ ] Authenticate WebSockets and validate allowed origins.
- [ ] Keep impersonation only as a visibly marked commissioner/development mode.

## Phase 3 — Server auction state machine

Persist and enforce:

```text
awaiting_nomination
sealed_bidding
revealed
rfa_match_pending
finalized
no_sale
void
```

- [ ] Enforce Superstar, UFA 1, UFA 2, and unlimited RFA Poaching stages.
- [ ] Enforce current nominator and eligibility.
- [ ] Persist Pass Remaining Nominations during RFA Poaching.
- [ ] Ensure passed GMs may still bid and match owned RFAs.
- [ ] Enforce one active nomination.
- [ ] Provide viewer-safe state with no pre-reveal bid leakage.

## Phase 4 — Bid API

- [ ] Default/non-response effective bid is 0.
- [ ] Allow explicit 0.
- [ ] Allow whole positive bids of 2 or more.
- [ ] Reject 1, negative, fractional, NaN, and infinite values.
- [ ] Store append-only submit/cancel/replacement events.
- [ ] Compute one effective bid per team.
- [ ] Allow cancellation and replacement only before reveal.
- [ ] Lock all bid changes atomically on commissioner reveal.
- [ ] Use idempotency keys for mutations.
- [ ] Pre-reveal response returns only viewer bid and safe response status.

## Phase 5 — Reveal, No Sale, and tie-break

- [ ] Commissioner reveal endpoint with optional non-response confirmation.
- [ ] Treat all non-responses as 0.
- [ ] Persist explicit zero versus non-response distinction.
- [ ] If highest bid is 0, finalize as No Sale and advance nomination order.
- [ ] For positive ties, choose highest-priority tied team.
- [ ] Move priority winner to bottom and persist the order.
- [ ] Record tie audit.
- [ ] Remove tie rebidding from frontend and backend.

## Phase 6 — RFA resolution

- [ ] Positive RFA result enters `rfa_match_pending`.
- [ ] Expose Match/Pass only to controlling GM.
- [ ] No decision timeout.
- [ ] Block ordinary finalization while decision is pending.
- [ ] Match assigns controlling team at revealed price for three years.
- [ ] Pass assigns highest bidder at revealed price for three years.
- [ ] Zero-high-bid RFA auction is No Sale and requires no decision.

## Phase 7 — Cap and roster calculations

- [ ] Calculate committed salary from protected contracts plus cap hits.
- [ ] Exclude expired contracts from committed salary.
- [ ] Exclude rookies and draft-pick placeholders from active position counts.
- [ ] Permit over-cap bids and assignments.
- [ ] Display warnings rather than blocking.
- [ ] Preserve and display negative cap space.
- [ ] Show Week 1 cap and positional compliance status.

## Phase 8 — Frontend refactor

Keep the existing design and create focused components/hooks:

- [ ] `useUhhpAuction`
- [ ] `AuctionStageHeader`
- [ ] `NominationPanel`
- [ ] `SealedBidPanel`
- [ ] `GmResponseStrip`
- [ ] `TieBreakOrder`
- [ ] `RfaDecisionPanel`
- [ ] `AuctionHistory`
- [ ] `TeamCapSummary`
- [ ] `CommissionerControls`

UI changes:

- [ ] Remove production Controlling Team dropdown.
- [ ] Keep GM response circles in the existing GM Bids section.
- [ ] Add checkmarks and response count.
- [ ] Hide all amounts until reveal.
- [ ] Default bid input to 0.
- [ ] Add Submit, Cancel, and Submit Replacement states.
- [ ] Add commissioner non-response reveal confirmation.
- [ ] Add No Sale result.
- [ ] Add current stage, round, nominator, and next-team display.
- [ ] Add Pass Remaining Nominations confirmation.
- [ ] Wire actual RFA Match/Pass actions.
- [ ] Remove timer, minimum-raise, current-high-bid, local winner, and tie-rebid behavior.
- [ ] Update rosters only from server-confirmed results.
- [ ] Always display auction contracts as three years.

## Phase 9 — Testing

Backend integration tests:

- [ ] Pre-reveal confidentiality across multiple clients.
- [ ] Explicit 0, non-response, positive bid, invalid 1.
- [ ] Cancel and replacement.
- [ ] Reveal with and without every response.
- [ ] No Sale.
- [ ] Positive tie and priority-order rotation.
- [ ] RFA Match and Pass.
- [ ] RFA indefinite pending state.
- [ ] Passed nominator can still bid and match.
- [ ] Unauthorized team/commissioner actions.
- [ ] Concurrent bid/reveal/finalize requests.
- [ ] Retry/idempotency and restart recovery.

Frontend/E2E tests:

- [ ] GM response circles and hidden amounts.
- [ ] Own-bid visibility.
- [ ] Cancel/replacement controls.
- [ ] Admin reveal warning.
- [ ] No Sale screen.
- [ ] Tie-break display.
- [ ] RFA decision permissions.
- [ ] Over-cap warning.
- [ ] Reconnect in every auction state.

## Phase 10 — Coolify readiness

- [ ] Make `npx tsc --noEmit` pass.
- [ ] Remove Next.js `ignoreBuildErrors` and lint suppression.
- [ ] Add missing frontend dependencies.
- [ ] Add FastAPI dependency manifest and Python 3.11+ Dockerfile.
- [ ] Add versioned migration job.
- [ ] Add frontend and backend health/readiness checks.
- [ ] Configure explicit CORS origins and WSS.
- [ ] Deploy API initially with one worker/replica while WebSocket state is in-process.
- [ ] Move WebSocket broadcasts to Redis before horizontal scaling.
- [ ] Run a complete 12-team staging simulation before production.

## Immediate next milestone

Build Phases 1–3 first: database schema, identity/permissions, and server auction state machine. The frontend should not be wired to more prototype state until the authoritative API contract is available.
