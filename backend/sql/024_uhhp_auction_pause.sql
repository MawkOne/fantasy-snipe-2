-- Allow the commissioner to pause/resume the live auction draft.
--
-- The commissioner can pause the draft (blocking new nominations and bids)
-- and resume it later; revealing an already-open nomination stays available
-- while paused so the room can conclude the current player auction.

ALTER TABLE public.uhhp_auction_drafts
  DROP CONSTRAINT IF EXISTS uhhp_auction_drafts_status_ck;

ALTER TABLE public.uhhp_auction_drafts
  ADD CONSTRAINT uhhp_auction_drafts_status_ck
  CHECK (status IN ('setup', 'active', 'paused', 'completed', 'void'));