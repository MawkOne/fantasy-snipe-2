-- Multi-pool fantasy schema (Railway / FANTASY_DATABASE_URL)

CREATE TABLE IF NOT EXISTS users (
  id text PRIMARY KEY,
  email text UNIQUE,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pools (
  id text PRIMARY KEY,
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  season int NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pool_members (
  user_id text REFERENCES users(id) ON DELETE CASCADE,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'gm',
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (user_id, pool_id)
);

CREATE TABLE IF NOT EXISTS pool_teams (
  id text PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  name text NOT NULL,
  abbrev text NOT NULL,
  owner_user_id text REFERENCES users(id),
  created_at timestamptz DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pool_teams_name ON pool_teams(pool_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pool_teams_abbrev ON pool_teams(pool_id, abbrev);

CREATE TABLE IF NOT EXISTS auctions (
  id text PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  season int NOT NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auction_orders (
  id text PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  season int NOT NULL,
  order_list jsonb NOT NULL,
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auction_picks (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  season int NOT NULL,
  pick_no int NOT NULL,
  nhl_player_id bigint NOT NULL,
  team_id text REFERENCES pool_teams(id),
  pos text,
  price int NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(pool_id, season, pick_no)
);
CREATE INDEX IF NOT EXISTS idx_picks_pool_season ON auction_picks(pool_id, season);

CREATE TABLE IF NOT EXISTS bids (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  pick_id bigint REFERENCES auction_picks(id) ON DELETE CASCADE,
  team_id text REFERENCES pool_teams(id) ON DELETE CASCADE,
  amount int NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_bids_lookup ON bids(pool_id, pick_id);

CREATE TABLE IF NOT EXISTS tie_audit (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  pick_id bigint REFERENCES auction_picks(id) ON DELETE CASCADE,
  contenders jsonb NOT NULL,
  advantage_team_id text REFERENCES pool_teams(id),
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contracts (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  team_id text REFERENCES pool_teams(id) ON DELETE CASCADE,
  nhl_player_id bigint NOT NULL,
  years int,
  salary int,
  fa_type text,
  start_season int,
  created_at timestamptz DEFAULT now(),
  UNIQUE(pool_id, team_id, nhl_player_id, start_season)
);

CREATE TABLE IF NOT EXISTS pool_slot_targets (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  season int NOT NULL,
  team_id text REFERENCES pool_teams(id) ON DELETE CASCADE,
  slot_id text NOT NULL,
  pos text NOT NULL,
  budget int,
  suggested_nhl_player_id bigint,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(pool_id, season, team_id, slot_id)
);
CREATE INDEX IF NOT EXISTS idx_slot_targets_scope ON pool_slot_targets(pool_id, season, team_id);

CREATE TABLE IF NOT EXISTS pool_position_budgets (
  id bigserial PRIMARY KEY,
  pool_id text REFERENCES pools(id) ON DELETE CASCADE,
  season int NOT NULL,
  team_id text REFERENCES pool_teams(id) ON DELETE CASCADE,
  pos text NOT NULL,
  budget int,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(pool_id, season, team_id, pos)
);


