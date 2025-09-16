-- Map authenticated users to a CBS league and team

CREATE TABLE IF NOT EXISTS cbs_user_memberships (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  team_id TEXT, -- references cbs_teams.team_id (text) for this league
  user_subject TEXT NOT NULL, -- auth subject (e.g., Kinde sub)
  user_email TEXT,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (league_id, user_subject)
);

CREATE INDEX IF NOT EXISTS idx_cbs_user_memberships_lookup ON cbs_user_memberships(league_id, team_id);


