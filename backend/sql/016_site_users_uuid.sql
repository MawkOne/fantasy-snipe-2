-- Add a stable UUID to site_users (without breaking existing integer PK)

-- Ensure uuid generator is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Add user_uuid column and backfill
ALTER TABLE IF EXISTS public.site_users
  ADD COLUMN IF NOT EXISTS user_uuid uuid DEFAULT gen_random_uuid();

UPDATE public.site_users
   SET user_uuid = COALESCE(user_uuid, gen_random_uuid())
 WHERE user_uuid IS NULL;

ALTER TABLE public.site_users
  ALTER COLUMN user_uuid SET NOT NULL;

-- Uniqueness guarantee for API usage
CREATE UNIQUE INDEX IF NOT EXISTS ux_site_users_user_uuid ON public.site_users(user_uuid);


