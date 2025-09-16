-- CBS Sports multi-league schema
-- This migration defines CBS-specific tables and a mapping to NHL player IDs.

-- 1) Leagues and rules

CREATE TABLE IF NOT EXISTS cbs_leagues (
  id BIGSERIAL PRIMARY KEY,
  provider_slug TEXT NOT NULL,
  name TEXT NOT NULL,
  domain TEXT NOT NULL,
  sport TEXT NOT NULL DEFAULT 'nhl',
  league_type TEXT,
  service_level TEXT,
  season INT,
  logo_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(provider_slug)
);

CREATE TABLE IF NOT EXISTS cbs_league_rules (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  roster_positions JSONB,
  lineup_deadline TEXT,
  ir_options TEXT,
  scoring_mode TEXT,
  scoring_policies JSONB,
  periods_start_day TEXT,
  period_length TEXT,
  season_start_date DATE,
  standings_tiebreakers TEXT,
  playoffs_tiebreaker TEXT,
  uses_faab BOOLEAN,
  uses_waivers BOOLEAN,
  faab_budget NUMERIC,
  waiver_run_days TEXT,
  waiver_reset_policy TEXT,
  waiver_period_days INT,
  source_url TEXT,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (league_id)
);

CREATE TABLE IF NOT EXISTS cbs_scoring_rules (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  stat_code TEXT NOT NULL,
  stat_name TEXT NOT NULL,
  points NUMERIC NOT NULL,
  category TEXT,
  PRIMARY KEY (league_id, stat_code)
);

-- 2) Owners, teams, membership

CREATE TABLE IF NOT EXISTS cbs_owners (
  owner_id TEXT PRIMARY KEY,
  display_name TEXT,
  email TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cbs_league_owners (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  owner_id TEXT NOT NULL REFERENCES cbs_owners(owner_id) ON DELETE CASCADE,
  role TEXT,
  PRIMARY KEY (league_id, owner_id)
);

CREATE TABLE IF NOT EXISTS cbs_teams (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  team_id TEXT NOT NULL,
  team_name TEXT NOT NULL,
  abbrev TEXT,
  logo_url TEXT,
  owner_id TEXT REFERENCES cbs_owners(owner_id),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (league_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_cbs_teams_owner ON cbs_teams(league_id, owner_id);

-- 3) Players and mapping to NHL

CREATE TABLE IF NOT EXISTS cbs_players (
  cbs_player_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  pos_primary TEXT,
  positions TEXT[],
  nhl_team_abbr TEXT,
  shoots TEXT,
  birthdate DATE,
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Mapping table joining CBS player IDs to NHL player IDs (from your NHL reference DB)
-- No FK is enforced across databases; store the NHL ID and mapping metadata here.
CREATE TABLE IF NOT EXISTS cbs_player_map (
  cbs_player_id TEXT PRIMARY KEY REFERENCES cbs_players(cbs_player_id) ON DELETE CASCADE,
  nhl_player_id BIGINT,
  confidence NUMERIC DEFAULT 0.0,
  match_method TEXT,
  mapped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convenience view to expose the join
CREATE OR REPLACE VIEW cbs_players_with_map AS
SELECT p.cbs_player_id,
       p.full_name,
       p.pos_primary,
       p.positions,
       p.nhl_team_abbr,
       p.birthdate,
       m.nhl_player_id,
       m.confidence,
       m.match_method,
       m.mapped_at
  FROM cbs_players p
  LEFT JOIN cbs_player_map m USING (cbs_player_id);

-- Optional full-text search index on player names for fuzzy matching
CREATE INDEX IF NOT EXISTS idx_cbs_players_name_tsv ON cbs_players USING GIN (to_tsvector('simple', full_name));

-- 4) Rosters

CREATE TABLE IF NOT EXISTS cbs_rosters (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  team_id TEXT NOT NULL,
  season INT,
  cbs_player_id TEXT NOT NULL REFERENCES cbs_players(cbs_player_id) ON DELETE CASCADE,
  slot_type TEXT,
  status TEXT,
  acquired_via TEXT,
  salary NUMERIC,
  years INT,
  rookie BOOLEAN,
  effective_from TIMESTAMPTZ,
  effective_to TIMESTAMPTZ,
  source_url TEXT,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cbs_rosters_team ON cbs_rosters(league_id, team_id);
CREATE INDEX IF NOT EXISTS idx_cbs_rosters_player ON cbs_rosters(cbs_player_id);

-- 5) Transactions

CREATE TABLE IF NOT EXISTS cbs_transactions (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  season INT,
  txn_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ,
  description TEXT,
  source_url TEXT,
  raw_html JSONB
);

CREATE INDEX IF NOT EXISTS idx_cbs_txn_league_time ON cbs_transactions(league_id, occurred_at);

CREATE TABLE IF NOT EXISTS cbs_transaction_items (
  id BIGSERIAL PRIMARY KEY,
  txn_id BIGINT NOT NULL REFERENCES cbs_transactions(id) ON DELETE CASCADE,
  cbs_player_id TEXT REFERENCES cbs_players(cbs_player_id),
  from_team_id TEXT,
  to_team_id TEXT,
  faab_delta INT,
  notes TEXT
);

-- 6) Schedule and matchups

CREATE TABLE IF NOT EXISTS cbs_scoring_periods (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  period_no INT NOT NULL,
  start_date DATE,
  end_date DATE,
  is_playoffs BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (league_id, period_no)
);

CREATE TABLE IF NOT EXISTS cbs_matchups (
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  period_no INT NOT NULL,
  home_team_id TEXT NOT NULL,
  away_team_id TEXT NOT NULL,
  home_score NUMERIC,
  away_score NUMERIC,
  status TEXT,
  PRIMARY KEY (league_id, period_no, home_team_id, away_team_id),
  FOREIGN KEY (league_id, period_no) REFERENCES cbs_scoring_periods(league_id, period_no) ON DELETE CASCADE
);

-- 7) Drafts

CREATE TABLE IF NOT EXISTS cbs_drafts (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  draft_type TEXT,
  status TEXT,
  start_time TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS cbs_draft_picks (
  draft_id BIGINT NOT NULL REFERENCES cbs_drafts(id) ON DELETE CASCADE,
  round_no INT,
  pick_no INT,
  team_id TEXT NOT NULL,
  cbs_player_id TEXT REFERENCES cbs_players(cbs_player_id),
  is_keeper BOOLEAN,
  price NUMERIC,
  metadata JSONB,
  PRIMARY KEY (draft_id, pick_no)
);

-- 8) Projections staging and import runs

CREATE TABLE IF NOT EXISTS cbs_projections (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT,
  season INT,
  scope TEXT,
  cbs_player_id TEXT NOT NULL REFERENCES cbs_players(cbs_player_id) ON DELETE CASCADE,
  stats JSONB,
  fantasy_points NUMERIC,
  source_url TEXT,
  scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Uniqueness guarantees using expression indexes where needed
-- Prefer simple unique indexes (NULLs are distinct in Postgres)
CREATE UNIQUE INDEX IF NOT EXISTS ux_cbs_rosters_league_team_player_eff
  ON cbs_rosters (league_id, team_id, cbs_player_id, effective_from);

CREATE UNIQUE INDEX IF NOT EXISTS ux_cbs_txn_items_composite
  ON cbs_transaction_items (txn_id, cbs_player_id, from_team_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_cbs_projections_scope
  ON cbs_projections (league_id, season, scope, cbs_player_id);

CREATE TABLE IF NOT EXISTS cbs_import_runs (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  items_processed INT,
  errors JSONB
);


