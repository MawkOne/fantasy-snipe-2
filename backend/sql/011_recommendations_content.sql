-- Recommendations & Content core

CREATE TABLE IF NOT EXISTS recommendation_runs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  league_id BIGINT,
  team_id TEXT,
  season INT,
  inputs_ref JSONB,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_reco_runs_user ON recommendation_runs(user_id, league_id);

CREATE TABLE IF NOT EXISTS recommendation_items (
  run_id BIGINT REFERENCES recommendation_runs(id) ON DELETE CASCADE,
  kind TEXT,
  subject_id TEXT,
  priority NUMERIC,
  action_payload JSONB,
  rationale JSONB,
  score NUMERIC,
  PRIMARY KEY (run_id, kind, subject_id)
);

CREATE TABLE IF NOT EXISTS content_jobs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  league_id BIGINT,
  kind TEXT,
  status TEXT,
  requested_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  inputs_ref JSONB
);
CREATE TABLE IF NOT EXISTS content_assets (
  job_id BIGINT REFERENCES content_jobs(id) ON DELETE CASCADE,
  kind TEXT,
  url TEXT,
  size BIGINT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (job_id, kind, url)
);


