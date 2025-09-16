-- Add nhl_player_id to cbs_rosters for downstream joins

ALTER TABLE IF EXISTS cbs_rosters
  ADD COLUMN IF NOT EXISTS nhl_player_id BIGINT;

-- Helpful index
CREATE INDEX IF NOT EXISTS idx_cbs_rosters_league_team ON cbs_rosters(league_id, team_id);


