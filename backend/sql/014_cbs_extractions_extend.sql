-- Extend cbs_extractions with user/league/site and add pages upsert table

ALTER TABLE IF EXISTS public.cbs_extractions
  ADD COLUMN IF NOT EXISTS user_id BIGINT,
  ADD COLUMN IF NOT EXISTS league_id BIGINT,
  ADD COLUMN IF NOT EXISTS site_url TEXT;

CREATE TABLE IF NOT EXISTS public.cbs_extraction_pages (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  league_id BIGINT,
  site_url TEXT,
  url TEXT NOT NULL,
  title TEXT,
  page JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, league_id, url)
);

CREATE INDEX IF NOT EXISTS idx_cbs_extraction_pages_site ON public.cbs_extraction_pages(site_url);
CREATE INDEX IF NOT EXISTS idx_cbs_extraction_pages_league ON public.cbs_extraction_pages(league_id);


