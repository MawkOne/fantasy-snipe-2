-- Extend CBS schema to capture team summaries and raw metadata

ALTER TABLE IF EXISTS cbs_leagues
  ADD COLUMN IF NOT EXISTS season INT,
  ADD COLUMN IF NOT EXISTS league_logo TEXT,
  ADD COLUMN IF NOT EXISTS league_type TEXT,
  ADD COLUMN IF NOT EXISTS service_level TEXT;

ALTER TABLE IF EXISTS cbs_league_rules
  ADD COLUMN IF NOT EXISTS raw_meta JSONB;

ALTER TABLE cbs_teams
  ADD COLUMN IF NOT EXISTS short_name TEXT,
  ADD COLUMN IF NOT EXISTS division TEXT,
  ADD COLUMN IF NOT EXISTS active_count INT,
  ADD COLUMN IF NOT EXISTS reserve_count INT,
  ADD COLUMN IF NOT EXISTS injured_count INT,
  ADD COLUMN IF NOT EXISTS active_salary NUMERIC,
  ADD COLUMN IF NOT EXISTS total_salary NUMERIC,
  ADD COLUMN IF NOT EXISTS raw_meta JSONB;

ALTER TABLE cbs_players
  ADD COLUMN IF NOT EXISTS shoots TEXT,
  ADD COLUMN IF NOT EXISTS birthdate DATE,
  ADD COLUMN IF NOT EXISTS first_name TEXT,
  ADD COLUMN IF NOT EXISTS last_name TEXT,
  ADD COLUMN IF NOT EXISTS nhl_player_id BIGINT;

CREATE INDEX IF NOT EXISTS idx_cbs_players_nhl_id ON cbs_players(nhl_player_id);

ALTER TABLE cbs_rosters
  ADD COLUMN IF NOT EXISTS future_fa TEXT,
  ADD COLUMN IF NOT EXISTS roster_order INT;


