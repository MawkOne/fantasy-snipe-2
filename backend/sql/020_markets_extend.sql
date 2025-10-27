-- Extend markets table with player projection fields

ALTER TABLE markets ADD COLUMN IF NOT EXISTS player_name TEXT;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS metric TEXT; -- G, A, PTS
ALTER TABLE markets ADD COLUMN IF NOT EXISTS threshold NUMERIC;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS sub_category TEXT;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS timeframe TEXT; -- Season | Monthly | Weekly
ALTER TABLE markets ADD COLUMN IF NOT EXISTS team TEXT;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS volume_total NUMERIC DEFAULT 0;
ALTER TABLE markets ADD COLUMN IF NOT EXISTS landing_url TEXT;

