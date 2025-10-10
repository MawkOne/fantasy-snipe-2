-- Add indexes/uniques to new_cbs_* tables

-- Teams unique per league
DO $$
BEGIN
  IF to_regclass('public.new_cbs_teams') IS NOT NULL THEN
    IF NOT EXISTS (
      SELECT 1 FROM pg_constraint WHERE conname = 'ux_new_cbs_teams_league_team'
    ) THEN
      ALTER TABLE new_cbs_teams
        ADD CONSTRAINT ux_new_cbs_teams_league_team UNIQUE (league_id, team_id);
    END IF;
  END IF;
END$$;

-- Scoring rules unique per league+stat
DO $$
BEGIN
  IF to_regclass('public.new_cbs_scoring_rules') IS NOT NULL THEN
    IF NOT EXISTS (
      SELECT 1 FROM pg_constraint WHERE conname = 'ux_new_cbs_scoring_rules'
    ) THEN
      ALTER TABLE new_cbs_scoring_rules
        ADD CONSTRAINT ux_new_cbs_scoring_rules UNIQUE (league_id, stat_code);
    END IF;
    CREATE INDEX IF NOT EXISTS idx_new_cbs_scoring_rules_league ON new_cbs_scoring_rules(league_id);
  END IF;
END$$;

-- Rosters indexes
DO $$
BEGIN
  IF to_regclass('public.new_cbs_rosters') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_new_cbs_rosters_league_team ON new_cbs_rosters(league_id, team_id);
    CREATE INDEX IF NOT EXISTS idx_new_cbs_rosters_league_player ON new_cbs_rosters(league_id, cbs_player_id);
  END IF;
END$$;


