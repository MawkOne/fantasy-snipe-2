-- Dom Luszczyszyn (The Athletic) 2026 season projections.
--
-- Stores the raw per-game projection rows from public/dom-projections.json
-- (671 players: 607 skaters + 64 goalies) keyed by (season, source_key) so
-- re-imports are idempotent. The import script also overlays these numbers
-- onto uhhp_auction_player_pool (projection + projected_fantasy_points).

CREATE TABLE IF NOT EXISTS dom_player_projections (
  id BIGSERIAL PRIMARY KEY,
  season INT NOT NULL,
  source TEXT NOT NULL DEFAULT 'the-athletic-dom',
  source_key TEXT NOT NULL,
  player_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  nhl_team TEXT,
  position TEXT,
  is_goalie BOOLEAN NOT NULL DEFAULT FALSE,
  games_played NUMERIC,
  stats JSONB NOT NULL DEFAULT '{}'::jsonb,
  fantasy_points NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT dom_player_projections_key_uk UNIQUE (season, source_key)
);

CREATE INDEX IF NOT EXISTS idx_dom_projections_season_name
  ON dom_player_projections (season, normalized_name);

CREATE INDEX IF NOT EXISTS idx_dom_projections_season_gp
  ON dom_player_projections (season, fantasy_points DESC NULLS LAST);