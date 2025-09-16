-- CBS Auction tables for draft flow

CREATE TABLE IF NOT EXISTS cbs_auctions (
  id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES cbs_leagues(id) ON DELETE CASCADE,
  nhl_player_id BIGINT NOT NULL,
  cbs_player_id TEXT,
  nominated_by_team_id TEXT,
  status TEXT NOT NULL DEFAULT 'open', -- open|closed|cancelled
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at TIMESTAMPTZ,
  UNIQUE (league_id, nhl_player_id) -- prevent duplicates per league
);

CREATE INDEX IF NOT EXISTS idx_cbs_auctions_league_open ON cbs_auctions(league_id, status);

CREATE TABLE IF NOT EXISTS cbs_auction_bids (
  id BIGSERIAL PRIMARY KEY,
  auction_id BIGINT NOT NULL REFERENCES cbs_auctions(id) ON DELETE CASCADE,
  team_id TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cbs_auction_bids_auction ON cbs_auction_bids(auction_id, amount DESC, created_at DESC);


