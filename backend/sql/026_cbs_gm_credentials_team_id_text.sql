-- Normalize cbs_gm_credentials.team_id to TEXT to match cbs_teams.team_id.
--
-- The original inline DDL created a fresh table with `team_id INT`, but this
-- league uses text team keys (e.g. 'uhhp-barney'), so every save silently
-- skipped rows (int(...) failed) and the /teams join never matched. Admin
-- flags were therefore never persisted or read.

CREATE TABLE IF NOT EXISTS cbs_gm_credentials (
  league_id INT NOT NULL,
  team_id TEXT NOT NULL,
  login TEXT,
  password_hash TEXT,
  salt TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (league_id, team_id)
);

-- Upgrade an existing INT-team_id table (created by the old endpoint DDL).
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = 'public'
       AND table_name = 'cbs_gm_credentials'
       AND column_name = 'team_id'
       AND data_type = 'integer'
  ) THEN
    ALTER TABLE cbs_gm_credentials DROP CONSTRAINT IF EXISTS cbs_gm_credentials_pkey;
    ALTER TABLE cbs_gm_credentials ALTER COLUMN team_id TYPE TEXT;
    ALTER TABLE cbs_gm_credentials ADD PRIMARY KEY (league_id, team_id);
  END IF;
END $$;