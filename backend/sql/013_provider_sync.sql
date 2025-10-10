-- Provider sync run tracking

CREATE TABLE IF NOT EXISTS provider_sync_runs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  provider_id BIGINT,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT,
  meta JSONB
);
CREATE INDEX IF NOT EXISTS idx_provider_sync_runs_user_provider ON provider_sync_runs(user_id, provider_id, started_at DESC);


