-- Attach a specific site user to all cbs_extractions and de-duplicate by site_url
-- NOTE: This migration expects the user exists in site_users with user_uuid below.

-- 1) Attach user_id by mapping from provided user_uuid
WITH u AS (
  SELECT id AS user_id
  FROM public.site_users
  WHERE user_uuid = '37842e7b-38c3-4b5f-88bb-ec005ae0678b'::uuid
)
UPDATE public.cbs_extractions e
SET user_id = u.user_id
FROM u
WHERE e.user_id IS DISTINCT FROM u.user_id;

-- 2) De-duplicate cbs_extractions by site_url, keeping the most recent (created_at, then id)
WITH ranked AS (
  SELECT id,
         site_url,
         created_at,
         ROW_NUMBER() OVER (PARTITION BY site_url ORDER BY created_at DESC NULLS LAST, id DESC) AS rn
  FROM public.cbs_extractions
  WHERE site_url IS NOT NULL AND site_url <> ''
)
DELETE FROM public.cbs_extractions e
USING ranked r
WHERE e.id = r.id
  AND r.rn > 1;


