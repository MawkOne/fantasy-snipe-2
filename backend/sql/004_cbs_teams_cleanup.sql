-- Cleanup cbs_teams: remove roster summary columns; add long_abbr

ALTER TABLE IF EXISTS cbs_teams
  DROP COLUMN IF EXISTS active_count,
  DROP COLUMN IF EXISTS reserve_count,
  DROP COLUMN IF EXISTS injured_count,
  DROP COLUMN IF EXISTS active_salary,
  DROP COLUMN IF EXISTS total_salary;

ALTER TABLE IF EXISTS cbs_teams
  ADD COLUMN IF NOT EXISTS long_abbr TEXT;


