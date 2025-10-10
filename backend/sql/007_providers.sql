-- Providers and multi-provider player map

CREATE TABLE IF NOT EXISTS providers (
  id BIGSERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT
);

CREATE TABLE IF NOT EXISTS provider_accounts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  provider_id BIGINT REFERENCES providers(id) ON DELETE CASCADE,
  login TEXT,
  secret_ref TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  last_verified_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_provider_accounts_user ON provider_accounts(user_id, provider_id);

CREATE TABLE IF NOT EXISTS provider_leagues (
  id BIGSERIAL PRIMARY KEY,
  provider_id BIGINT REFERENCES providers(id) ON DELETE CASCADE,
  external_id TEXT NOT NULL,
  slug TEXT,
  name TEXT,
  domain TEXT,
  sport TEXT,
  season INT,
  raw_meta JSONB,
  UNIQUE (provider_id, external_id)
);

CREATE TABLE IF NOT EXISTS provider_teams (
  provider_league_id BIGINT REFERENCES provider_leagues(id) ON DELETE CASCADE,
  team_id TEXT NOT NULL,
  team_name TEXT NOT NULL,
  abbrev TEXT,
  logo_url TEXT,
  owner_external_id TEXT,
  raw_meta JSONB,
  PRIMARY KEY (provider_league_id, team_id)
);

CREATE TABLE IF NOT EXISTS provider_owners (
  provider_league_id BIGINT REFERENCES provider_leagues(id) ON DELETE CASCADE,
  owner_id TEXT NOT NULL,
  display_name TEXT,
  email TEXT,
  avatar_url TEXT,
  PRIMARY KEY (provider_league_id, owner_id)
);

CREATE TABLE IF NOT EXISTS provider_player_map (
  provider_id BIGINT REFERENCES providers(id) ON DELETE CASCADE,
  provider_player_id TEXT NOT NULL,
  nhl_player_id BIGINT,
  last_seen_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (provider_id, provider_player_id)
);
CREATE INDEX IF NOT EXISTS idx_provider_player_map_nhl ON provider_player_map(nhl_player_id);
