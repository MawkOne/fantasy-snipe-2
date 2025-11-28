-- ============================================================================
-- PLAYER SEASON EDGE STATS TABLE
-- Stores NHL Edge tracking data (speed, distance, shots, zone time) per season
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_season_edge_stats (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys & Season Info
    player_id INTEGER NOT NULL,
    season VARCHAR(8) NOT NULL,  -- Format: '20242025'
    game_type INTEGER NOT NULL DEFAULT 2,  -- 2 = Regular Season, 3 = Playoffs
    team_id INTEGER,
    
    -- Data Freshness
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ========================================
    -- SPEED METRICS
    -- ========================================
    
    -- Max Speed
    max_speed_mph NUMERIC(5,2),          -- e.g., 22.03
    max_speed_kph NUMERIC(5,2),          -- e.g., 35.45
    max_speed_percentile NUMERIC(5,4),   -- e.g., 0.6260 (62.6th percentile)
    max_speed_league_avg_mph NUMERIC(5,2),
    
    -- Speed Events
    bursts_over_20mph INTEGER,           -- Count of 20+ MPH bursts
    
    -- Top Speed Event Details (JSON for top 10)
    top_speed_events JSONB,              -- Store top 10 speed events with timestamps
    
    -- ========================================
    -- SHOT VELOCITY METRICS
    -- ========================================
    
    -- Max Shot Velocity
    max_shot_mph NUMERIC(5,2),           -- e.g., 98.24
    max_shot_kph NUMERIC(5,2),           -- e.g., 158.10
    max_shot_percentile NUMERIC(5,4),    -- e.g., 0.6633
    max_shot_league_avg_mph NUMERIC(5,2),
    
    -- Top Shot Event Details (JSON for top 10)
    top_shot_events JSONB,               -- Store top 10 hardest shots with timestamps
    
    -- ========================================
    -- DISTANCE METRICS
    -- ========================================
    
    -- Total Distance
    total_distance_km NUMERIC(8,2),      -- Season total km
    total_distance_mi NUMERIC(8,2),      -- Season total miles
    avg_distance_per_game_km NUMERIC(5,2),
    avg_distance_per_game_mi NUMERIC(5,2),
    
    -- Distance by Situation
    distance_even_strength_km NUMERIC(8,2),
    distance_power_play_km NUMERIC(8,2),
    distance_penalty_kill_km NUMERIC(8,2),
    
    -- ========================================
    -- ZONE TIME METRICS
    -- ========================================
    
    -- All Situations
    zone_time_offensive_pct NUMERIC(5,4),      -- e.g., 0.4662 (46.62%)
    zone_time_offensive_percentile NUMERIC(5,4),
    zone_time_neutral_pct NUMERIC(5,4),
    zone_time_defensive_pct NUMERIC(5,4),
    
    -- Even Strength
    zone_time_es_offensive_pct NUMERIC(5,4),
    zone_time_es_neutral_pct NUMERIC(5,4),
    zone_time_es_defensive_pct NUMERIC(5,4),
    
    -- Power Play
    zone_time_pp_offensive_pct NUMERIC(5,4),
    zone_time_pp_neutral_pct NUMERIC(5,4),
    zone_time_pp_defensive_pct NUMERIC(5,4),
    
    -- Penalty Kill
    zone_time_pk_offensive_pct NUMERIC(5,4),
    zone_time_pk_neutral_pct NUMERIC(5,4),
    zone_time_pk_defensive_pct NUMERIC(5,4),
    
    -- ========================================
    -- SHOT LOCATION METRICS
    -- ========================================
    
    -- Shot Location Summary (JSON for heat map)
    shot_locations JSONB,                -- Store all shot location stats by area
    
    -- Key Areas (for quick queries)
    shots_from_crease INTEGER,
    goals_from_crease INTEGER,
    shooting_pct_crease NUMERIC(5,4),
    
    shots_from_high_slot INTEGER,
    goals_from_high_slot INTEGER,
    shooting_pct_high_slot NUMERIC(5,4),
    
    -- ========================================
    -- RAW EDGE DATA (for reference)
    -- ========================================
    
    raw_edge_response JSONB,             -- Store complete API response
    
    -- ========================================
    -- CONSTRAINTS & INDEXES
    -- ========================================
    
    -- Unique constraint: one record per player/season/game_type
    UNIQUE(player_id, season, game_type)
);

-- Create indexes for common queries
CREATE INDEX idx_player_season_edge_player ON player_season_edge_stats(player_id);
CREATE INDEX idx_player_season_edge_season ON player_season_edge_stats(season);
CREATE INDEX idx_player_season_edge_player_season ON player_season_edge_stats(player_id, season);
CREATE INDEX idx_player_season_edge_team ON player_season_edge_stats(team_id);

-- Create index on max_speed for rankings
CREATE INDEX idx_player_season_edge_max_speed ON player_season_edge_stats(max_speed_mph DESC);
CREATE INDEX idx_player_season_edge_max_shot ON player_season_edge_stats(max_shot_mph DESC);

-- Add foreign key (if players table has proper constraint)
-- ALTER TABLE player_season_edge_stats 
--   ADD CONSTRAINT fk_player 
--   FOREIGN KEY (player_id) REFERENCES players(id);

-- Add comment
COMMENT ON TABLE player_season_edge_stats IS 'NHL Edge tracking data (speed, distance, shots, zone time) aggregated by player season';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Get Darnell Nurse's Edge stats for 2024-25
-- SELECT * FROM player_season_edge_stats 
-- WHERE player_id = 8477498 AND season = '20242025' AND game_type = 2;

-- Find fastest players in 2024-25
-- SELECT player_id, max_speed_mph, max_speed_percentile 
-- FROM player_season_edge_stats 
-- WHERE season = '20242025' AND game_type = 2 
-- ORDER BY max_speed_mph DESC LIMIT 10;

-- Compare speed to Corsi (join with your existing data)
-- SELECT 
--     e.player_id,
--     e.max_speed_mph,
--     e.max_speed_percentile,
--     AVG(a.CF_pct) as avg_cf_pct
-- FROM player_season_edge_stats e
-- JOIN player_game_advanced_metrics_flat a 
--   ON e.player_id = a.player_id 
--   AND e.season = a.season 
--   AND e.game_type = a.game_type
-- WHERE e.season = '20242025'
-- GROUP BY e.player_id, e.max_speed_mph, e.max_speed_percentile;

