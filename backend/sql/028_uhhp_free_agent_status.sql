-- Store roster free-agent classification separately from auction eligibility.
-- This lets rookies retain ROOKIE eligibility while still displaying their
-- age-based RFA/UFA status on roster pages.

ALTER TABLE public.uhhp_auction_player_pool
  ADD COLUMN IF NOT EXISTS free_agent_status TEXT;

ALTER TABLE public.uhhp_auction_player_pool
  DROP CONSTRAINT IF EXISTS uhhp_auction_player_pool_free_agent_status_ck;

ALTER TABLE public.uhhp_auction_player_pool
  ADD CONSTRAINT uhhp_auction_player_pool_free_agent_status_ck
  CHECK (free_agent_status IS NULL OR free_agent_status IN ('RFA', 'UFA'));

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_pool_free_agent_status
  ON public.uhhp_auction_player_pool (draft_id, free_agent_status)
  WHERE free_agent_status IS NOT NULL;
