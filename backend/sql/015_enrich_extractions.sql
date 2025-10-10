-- Backfill cbs_extractions.site_url and league_id from existing raw payloads

-- 1) Fill site_url from the first page url in raw, when missing
UPDATE public.cbs_extractions e
SET site_url = COALESCE(
  e.site_url,
  NULLIF((e.raw->'pages'->0->>'url'), '')
)
WHERE e.site_url IS NULL;

-- 2) Fill league_id by matching site_url domain to new_cbs_leagues.domain
WITH cand AS (
  SELECT id AS extraction_id,
         lower(regexp_replace(COALESCE(site_url, (raw->'pages'->0->>'url')), '^https?://([^/]+).*$', '\1')) AS domain
  FROM public.cbs_extractions
  WHERE league_id IS NULL
)
UPDATE public.cbs_extractions e
SET league_id = nl.id
FROM cand c
JOIN public.new_cbs_leagues nl ON lower(nl.domain) = c.domain
WHERE e.id = c.extraction_id
  AND e.league_id IS NULL;

-- 3) Fallback: fill league_id by matching provider_slug to first label of domain in legacy cbs_leagues
WITH cand AS (
  SELECT id AS extraction_id,
         lower(regexp_replace(COALESCE(site_url, (raw->'pages'->0->>'url')), '^https?://([^/]+).*$', '\1')) AS domain
  FROM public.cbs_extractions
  WHERE league_id IS NULL
)
UPDATE public.cbs_extractions e
SET league_id = cl.id
FROM cand c
JOIN public.cbs_leagues cl ON (
  lower(cl.domain) = c.domain OR lower(cl.provider_slug) = split_part(c.domain, '.', 1)
)
WHERE e.id = c.extraction_id
  AND e.league_id IS NULL;

-- 4) Helpful indexes
CREATE INDEX IF NOT EXISTS idx_cbs_extractions_site ON public.cbs_extractions(site_url);
CREATE INDEX IF NOT EXISTS idx_cbs_extractions_league ON public.cbs_extractions(league_id);


