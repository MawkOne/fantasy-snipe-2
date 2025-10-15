-- Markets and LMSR AMM schema (binary outcomes for MVP)

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid

CREATE TABLE IF NOT EXISTS markets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  outcome_type TEXT NOT NULL CHECK (outcome_type IN ('binary')), -- extend later
  status TEXT NOT NULL CHECK (status IN ('draft','open','halted','closed','resolved')),
  b NUMERIC NOT NULL CHECK (b > 0), -- LMSR liquidity parameter
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_outcomes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  outcome TEXT NOT NULL CHECK (outcome IN ('yes','no')),
  UNIQUE (market_id, outcome)
);

CREATE TABLE IF NOT EXISTS amm_inventory (
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  outcome TEXT NOT NULL CHECK (outcome IN ('yes','no')),
  shares NUMERIC NOT NULL DEFAULT 0,
  PRIMARY KEY (market_id, outcome)
);

CREATE TABLE IF NOT EXISTS trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('buy','sell')),
  outcome TEXT NOT NULL CHECK (outcome IN ('yes','no')),
  shares NUMERIC NOT NULL CHECK (shares > 0),
  price NUMERIC NOT NULL CHECK (price >= 0 AND price <= 1),
  cost NUMERIC NOT NULL CHECK (cost >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS balances (
  user_id UUID NOT NULL,
  asset TEXT NOT NULL DEFAULT 'VC',
  available NUMERIC NOT NULL DEFAULT 0,
  reserved NUMERIC NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, asset)
);

CREATE TABLE IF NOT EXISTS ledger_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  asset TEXT NOT NULL DEFAULT 'VC',
  delta NUMERIC NOT NULL,
  reason TEXT NOT NULL,
  ref_type TEXT,
  ref_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


