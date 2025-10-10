-- Canonical memberships table and optional backfill from legacy

CREATE TABLE IF NOT EXISTS memberships (
  user_id BIGINT,
  league_id BIGINT,
  team_id TEXT,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, league_id)
);
CREATE INDEX IF NOT EXISTS idx_memberships_league_team ON memberships(league_id, team_id);

-- Optional backfill from cbs_user_memberships if present
DO $$
BEGIN
  IF to_regclass('public.cbs_user_memberships') IS NOT NULL THEN
    INSERT INTO memberships(user_id, league_id, team_id, role, created_at)
    SELECT NULL::BIGINT, m.league_id, m.team_id, COALESCE(m.role,'member'), m.created_at
      FROM cbs_user_memberships m
    ON CONFLICT (user_id, league_id) DO NOTHING;
  END IF;
END$$;
