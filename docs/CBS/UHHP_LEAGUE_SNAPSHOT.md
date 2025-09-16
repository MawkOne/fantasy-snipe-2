### UHHP League Snapshot (CBS Sports)

This document captures identifiers, rules, teams, and data patterns for the “Ultimate Hardcore Hockey Pool” (UHHP) league hosted on CBS Sports, extracted from saved CBS pages in this repo.

### League identity
- League name: Ultimate Hardcore Hockey Pool
- League slug: `uhhp`
- Domain: `uhhp.hockey.cbssports.com`
- Sport/arena: NHL (hockey)
- League type: mgmt; Service level: gold
- League logo: `https://fantasy-media.cbssports.com/hockey/uhhp/...jpg`

### User/owner identifiers (league-scoped)
- CBS user handle: `markhend6789`
- League-scoped address: `markhend6789@uhhp.hockey.cbssports.com`
- Owner logo URLs show association with teams (e.g., `ownerlogo?...&teamname=New_Oilers_Nation&id=markhend6789`).

### Teams (IDs, names, logos)
- Stable numeric team IDs with names and logo URLs, examples:
  - 2: 3sheets Sports Entertainment
  - 14: The Dook of Sook
  - 11: CinStars
  - 15: The Inglorious Basteeerds
  - 8: South Calgary Oilers
  - 10: The Pylons
  - 6: re-degeneration X 2.0
- Logo URL pattern: `https://fantasy-media.cbssports.com/hockey/uhhp/team_logo/{teamId-suffix}.{ext}`

### Player identifiers (CBS)
- CBS numeric player IDs are present in player URLs: `/players/playerpage/{CBS_PLAYER_ID}`. Use as `provider_player_id` for mapping.

### Scoring system
- Mode: Head-to-Head, Points; period scoring based on total stats per period; ties allowed.
- Stat-to-points examples: +/- 0.25; Assists 2; Defenseman Assists 1; Defenseman Goals 2; Goals 3; Goals Against −1.25; OT Losses 1; PIM 0; Saves 0.2; SHG 2; Shootout Goals 1; Shootout Losses 1; Shutouts 1; Wins 2.

### Schedule & playoffs
- Weekly scoring periods starting Mondays; season start date displayed (e.g., Tue, Oct 7, 2025).
- Standings tiebreakers: Winning % → H2H → Total Points; playoff tiebreaker: better G.

### Lineup & roster policies
- Lineup deadline: for each player, 5 minutes before the first game of the period.
- IR options: All players are eligible.

### Waivers / FAAB
- Add/Drop via waivers; runs Sun/Fri/Sat; weekly reset; dropped players on waivers at least 1 day; FAAB budget $100.
- Page script indicates league uses FAAB.

### Data endpoint access note
- Structured projections endpoint referenced in Header requires CBS login; anonymous fetch redirects to login.
- A copy of the attempted fetch is saved as `docs/CBS/uhhp_projections.json` and contains the login HTML.

### Suggested DB mappings (for import/sync)
- external_league_map(provider='cbs', provider_league_id='uhhp', fantasy_league_id, meta)
- external_team_map(provider='cbs', provider_league_id, provider_team_id, fantasy_team_id, team_name, owner_handle, logo_url)
- external_player_map(provider='cbs', provider_player_id, nhl_player_id, full_name, team_abbr, positions[], confidence)

These enable joining CBS team/roster/player data to your NHL reference DB and fantasy tables.

---

### Comprehensive catalog of CBS league data (from saved files)

- **League identity**: slug, name, domain, sport, league_type, service_level, league_logo, project, requestUri, season markers
- **Owners & membership**: owner handle, league-scoped email, owner avatars/logos, role (commissioner/owner/member)
- **Teams**: team_id, team_name, short_name, division, logo_url, owner_id, active flag, schedule opponents by period, footer summary (active/reserve/injured counts, active/total salary)
- **Players**: cbs_player_id, full_name, pos_primary, nhl_team_abbr, draft-pick placeholders, optional shoots/birthdate
- **Rosters**: player rows per team with slot_type/status, salary/years, acquired_via, future_fa (RFA/UFA), effective dates
- **Transactions**: season, txn_type, occurred_at, description/raw_html; items with cbs_player_id, from_team_id, to_team_id, faab_delta
- **Scoring rules & policies**: scoring mode/policies; per-stat points; schedule/playoff settings; lineup/IR; waivers/FAAB
- **Scoring periods & matchups**: period_no, start/end dates, is_playoffs; matchups (home/away/scores/status)
- **Drafts & picks**: draft_type, status, start_time; picks (round, pick, team_id, cbs_player_id, is_keeper, price, metadata)
- **Projections**: season, scope, stats JSON, fantasy_points (requires auth)
- **Provenance**: source_url, captured_at, raw_html/raw_meta snapshots

---

### Schema deltas to capture everything

- **cbs_leagues**: + season INT, league_logo TEXT, league_type TEXT, service_level TEXT
- **cbs_league_rules**: ensure all policy fields; + raw_meta JSONB
- **cbs_scoring_rules**: as-is (stat_code, stat_name, points, category)
- **cbs_owners / cbs_league_owners**: + avatar_url TEXT (optional)
- **cbs_teams**: + short_name, division, active_count, reserve_count, injured_count, active_salary, total_salary, raw_meta
- **cbs_players**: + shoots, birthdate (optional)
- **cbs_player_map**: as-is (nhl_player_id, confidence, match_method, mapped_at)
- **cbs_rosters**: ensure slot_type, status, salary, years, acquired_via, future_fa, season, effective_from/to, source_url; optional roster_order
- **cbs_transactions / cbs_transaction_items**: as-is; items include faab_delta; transactions keep raw_html
- **cbs_scoring_periods / cbs_matchups**: as-is; ensure status on matchups
- **cbs_drafts / cbs_draft_picks**: as-is; include is_keeper, price, metadata
- **cbs_projections / cbs_import_runs**: as-is

---

### Next steps
- Implement robust BeautifulSoup importer to ingest teams (with roster summaries), rosters (slot/status/salary/years/future_fa), transactions (with items/FAAB), and scoring periods/matchups.
- Then backfill `cbs_player_map` using deterministic (name + DOB) and fuzzy matching; persist `confidence`.




Comprehensive catalog of CBS league data (from your saved files)
League identity (Header, schedule)
provider_slug (leagueId): “uhhp”
league_name: “Ultimate Hardcore Hockey Pool”
domain/base_url: “uhhp.hockey.cbssports.com”
sport/arena: “nhl”
league_type: “mgmt”
service_level: “gold”
league_logo url(s)
project: “openhockey”
requestUri (context of page)
season (in paths like transactions/2024)
authentication/user state markers (commissioner, is_commissioner)
Owners and membership (schedule, header)
owner_id/handle: e.g., “markhend6789”
league-scoped email: e.g., “markhend6789@uhhp.hockey.cbssports.com”
avatar/ownerlogo urls with teamname linkage
role: commissioner/owner/member (derived)
presence of chat/league state flags (not essential, optionally store)
Teams (schedule, teams)
team_id (numeric, consistent in links and team_logo/{id-...})
team_name (e.g., “3sheets Sports Entertainment”)
short_name (e.g., “3sheet”, “New Oi”)
division (if present)
logo_url (consistent pattern)
owner_id (linked by ownerlogo teamname=...&id=...)
is_active
schedule opponents per period (period_no → opponent team_id, home/away inferred by “@” symbol)
team record snapshots on schedule view (if present)
Scoring rules and policies (rules)
scoring_mode: Head-to-Head, Points
scoring_per_period policy
matchup_tiebreaker
per-stat scoring map:
examples: +/- .25; A 2; DA 1; DG 2; G 3; GA −1.25; OL 1; PIM 0; S 0.2; SHG 2; SHOG 1; SHOL 1; SO 1; W 2
schedule & playoffs:
period_length: Weekly
periods_start_day: Monday
season_start_date (displayed)
standings_tiebreakers ordering
playoffs_tiebreaker
lineup policies:
lineup_deadline (“5 minutes before first game for the player”)
IR options (“All players are eligible.”)
waivers/FAAB (transactions/rules scripts)
uses_faab, uses_waivers flags
faab_budget (e.g., $100)
waiver_run_days (Sun/Fri/Sat)
waiver_reset_policy (weekly)
waiver_period_days for drops
waivers start state (script JSON)
Players (skaters, teams)
cbs_player_id (from /players/playerpage/{id})
full_name (anchor text / aria-label)
pos_primary and/or listed position (C/W/D/G)
nhl_team_abbr (e.g., COL, WAS)
draft pick pseudo-players (ids like 1000000830, label “2027 Draft Pick ...”)
shoots, birthdate (if page reveals; else from other sources)
last_seen timestamps
team context (roster association per team)
Rosters (teams)
per-team roster rows with:
cbs_player_id, name, pos, nhl_team_abbr
slot_type (inferred: starters vs bench vs IR)
status (active/bench/ir)
salary (if displayed)
years (keeper years, if displayed)
acquired_via (draft/waiver/trade/fa if visible)
future FA type (“RFA”, “UFA”) if shown
roster footer summary:
active_count, reserve_count, injured_count
active_salary, total_salary
Transactions (2024 transactions)
season (from path)
txn_type (add, drop, trade, waiver, keeper)
occurred_at (timestamp if rendered)
description text
items: cbs_player_id moved, from_team_id, to_team_id, faab_delta
raw_html block (for provenance)
Scoring periods & matchups (schedule)
period_no
start_date, end_date (if present)
is_playoffs
matchups per period: home_team_id, away_team_id, scores if shown, status
Drafts & picks (teams/other pages)
draft_type (snake/auction)
status (pre_draft/drafting/complete)
start_time (if present)
picks: round_no, pick_no, team_id, cbs_player_id or pick placeholder, is_keeper, price, metadata
Projections (Header captured endpoint reference)
scope (e.g., restofseason:p/standard/projections)
per-player stats JSON, fantasy_points
source_url; requires auth, but we can stage if scraped later
Provenance
source_url, captured_at
raw_html/jsonb snapshots where parsing is brittle

---

### Complete UHHP snapshot (what we will store)

- League (cbs_leagues): slug `uhhp`, name, domain `uhhp.hockey.cbssports.com`, sport `nhl`, type `mgmt`, service `gold`, season, league_logo
- Owners (cbs_owners, cbs_league_owners): handle(s) (e.g., `markhend6789`), league email, avatar_url; membership role
- Teams (cbs_teams):
  - id → from `/teams/{id}` or `team_logo/{id-...}`
  - team_name, short_name, division, logo_url, owner_id
  - footer summary → active_count, reserve_count, injured_count, active_salary, total_salary
- Players (cbs_players):
  - cbs_player_id → from `/players/playerpage/{id}`
  - full_name/pos/team → from `aria-label` like "Connor McDavid C EDM"
  - CBS→NHL mapping (cbs_player_map) → nhl_player_id, confidence, match_method
- Rosters (cbs_rosters):
  - team_id via onTeamID (authoritative), cbs_player_id
  - salary (decimal), years (keeper), future_fa, slot/status (best effort), roster_order, season
- Scoring rules (cbs_league_rules, cbs_scoring_rules):
  - mode Head-to-Head, Points; per-stat points (+/-, G, A, W, SO, GA, S, …)
  - schedule/playoffs, lineup/IR, waivers/FAAB settings
- Schedule (cbs_scoring_periods, cbs_matchups):
  - period_no per team; opponent team_id; home/away ("@"); scores if present
- Transactions (cbs_transactions, cbs_transaction_items):
  - season, type, occurred_at, description/raw_html; items: player, from_team_id, to_team_id, faab_delta
- Drafts/picks (cbs_drafts, cbs_draft_picks): type, status; picks (round, pick, team_id, player or placeholder, is_keeper, price)
- Projections (cbs_projections staging): season, scope, stats JSON, fantasy_points

This mirrors the data in your CBS files and maps each field to a concrete table/column in the database.