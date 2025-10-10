-- Add updated_at and unique key for upsert on cbs_extractions

ALTER TABLE IF EXISTS public.cbs_extractions
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

UPDATE public.cbs_extractions
   SET updated_at = COALESCE(updated_at, created_at, now())
 WHERE updated_at IS NULL;

-- Unique combination to support upsert; allows multiple rows when any component is NULL
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ux_cbs_extractions_user_league_site'
  ) THEN
    ALTER TABLE public.cbs_extractions
      ADD CONSTRAINT ux_cbs_extractions_user_league_site UNIQUE (user_id, league_id, site_url);
  END IF;
END$$;


