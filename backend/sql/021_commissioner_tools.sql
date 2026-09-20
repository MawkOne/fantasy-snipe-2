-- Commissioner tools schema
-- Tracks commissioner actions and provides tables needed for commissioner management

-- League status enum table
CREATE TABLE IF NOT EXISTS league_statuses (
    status TEXT PRIMARY KEY,
    description TEXT
);

INSERT INTO league_statuses (status, description) VALUES
    ('draft', 'League is in draft phase'),
    ('pre-season', 'Draft completed, pre-season active'),
    ('active', 'Regular season is active'),
    ('playoffs', 'Playoffs are in progress'),
    ('completed', 'Season completed'),
    ('archived', 'League is archived')
ON CONFLICT (status) DO NOTHING;

-- Commissioner action log for audit trail
CREATE TABLE IF NOT EXISTS commissioner_action_log (
    id BIGSERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    description TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commish_log_league ON commissioner_action_log(league_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_commish_log_user ON commissioner_action_log(user_id, created_at DESC);

-- League waiver order tracking
CREATE TABLE IF NOT EXISTS league_waiver_order (
    league_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    waiver_priority INTEGER NOT NULL,
    last_waiver_use TIMESTAMP,
    PRIMARY KEY (league_id, team_id)
);

-- Player transaction approvals (extends fantasy_transactions)
ALTER TABLE fantasy_transactions ADD COLUMN IF NOT EXISTS approved_by INTEGER REFERENCES fantasy_users(id);
ALTER TABLE fantasy_transactions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE fantasy_transactions ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE fantasy_transactions ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'));

-- League settings: add commissioner config fields
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS waiver_type TEXT DEFAULT 'standard' CHECK (waiver_type IN ('standard', 'faab', 'none'));
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS faab_budget INTEGER DEFAULT 100;
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS trade_review_period_hours INTEGER DEFAULT 48;
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS lineup_changes TEXT DEFAULT 'weekly' CHECK (lineup_changes IN ('daily', 'weekly', 'manual'));
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS playoff_teams INTEGER DEFAULT 4;
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS regular_season_weeks INTEGER;
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS divisions JSON;
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS season_status TEXT DEFAULT 'draft' REFERENCES league_statuses(status);
ALTER TABLE fantasy_league_settings ADD COLUMN IF NOT EXISTS last_updated_by INTEGER REFERENCES fantasy_users(id);

-- Fantasy users: add commissioner notes
ALTER TABLE fantasy_users ADD COLUMN IF NOT EXISTS commissioner_notes TEXT;

-- Team: add commissioner-only notes
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS commissioner_notes TEXT;
ALTER TABLE fantasy_teams ADD COLUMN IF NOT EXISTS division TEXT;