-- Snapshot table for projections replicated from BigQuery

CREATE TABLE IF NOT EXISTS fantasy_player_projections (
  id BIGSERIAL PRIMARY KEY,
  season INT NOT NULL,
  source TEXT NOT NULL,
  kind TEXT,
  nhl_player_id INT NOT NULL,
  player_name TEXT,
  position TEXT,
  team TEXT,
  metrics JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (season, source, nhl_player_id)
);


