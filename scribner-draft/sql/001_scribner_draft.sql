BEGIN;

CREATE TABLE IF NOT EXISTS scribner_rooms (
  id TEXT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  admin_token TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('setup', 'in_progress', 'completed')),
  current_round INTEGER NOT NULL DEFAULT 0 CHECK (current_round >= 0),
  rounds_count INTEGER NOT NULL CHECK (rounds_count BETWEEN 1 AND 30),
  roster_requirements JSONB NOT NULL,
  scoring_metrics JSONB NOT NULL,
  admin_team_id TEXT,
  available_player_ids JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scribner_teams (
  id TEXT PRIMARY KEY,
  room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
  name VARCHAR(80) NOT NULL,
  owner_email TEXT,
  invite_token TEXT NOT NULL UNIQUE,
  invite_state TEXT NOT NULL CHECK (invite_state IN ('not_sent', 'sent', 'joined')),
  invite_sent_at TIMESTAMPTZ,
  joined_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (room_id, id)
);

CREATE TABLE IF NOT EXISTS scribner_rounds (
  room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
  round_number INTEGER NOT NULL CHECK (round_number BETWEEN 1 AND 30),
  status TEXT NOT NULL CHECK (status IN ('submitting', 'revealed')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revealed_at TIMESTAMPTZ,
  PRIMARY KEY (room_id, round_number)
);

CREATE TABLE IF NOT EXISTS scribner_picks (
  room_id TEXT NOT NULL,
  round_number INTEGER NOT NULL,
  team_id TEXT NOT NULL,
  player_id TEXT NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  revealed_at TIMESTAMPTZ,
  PRIMARY KEY (room_id, round_number, team_id),
  FOREIGN KEY (room_id, round_number)
    REFERENCES scribner_rounds(room_id, round_number) ON DELETE CASCADE,
  FOREIGN KEY (room_id, team_id)
    REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scribner_rosters (
  room_id TEXT NOT NULL,
  team_id TEXT NOT NULL,
  round_number INTEGER NOT NULL,
  player_id TEXT NOT NULL,
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (room_id, team_id, round_number),
  FOREIGN KEY (room_id, team_id)
    REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE,
  FOREIGN KEY (room_id, round_number)
    REFERENCES scribner_rounds(room_id, round_number) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scribner_manual_rosters (
  id TEXT PRIMARY KEY,
  room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
  team_id TEXT NOT NULL,
  player_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (room_id, team_id, player_id),
  FOREIGN KEY (room_id, team_id)
    REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS scribner_teams_room_idx
  ON scribner_teams(room_id);
CREATE INDEX IF NOT EXISTS scribner_teams_invite_token_idx
  ON scribner_teams(invite_token);
CREATE INDEX IF NOT EXISTS scribner_picks_room_round_idx
  ON scribner_picks(room_id, round_number);
CREATE INDEX IF NOT EXISTS scribner_rosters_room_team_idx
  ON scribner_rosters(room_id, team_id);
CREATE INDEX IF NOT EXISTS scribner_manual_rosters_room_team_idx
  ON scribner_manual_rosters(room_id, team_id);

COMMIT;
