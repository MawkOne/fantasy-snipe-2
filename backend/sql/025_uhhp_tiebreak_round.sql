-- Tie-break re-bid round for the silent auction.
--
-- When a reveal ends in a positive tie, the nomination moves to
-- 'tie_break_bidding': only the tied teams submit one more sealed number.
-- A second reveal resolves it (highest increase wins; otherwise the
-- rotating tie-break order decides). The winner always moves to the bottom
-- of the tie-break order.

-- 1) Allow the tie-break-bidding nomination status.
ALTER TABLE public.uhhp_auction_nominations
  DROP CONSTRAINT IF EXISTS uhhp_auction_nominations_status_ck;

ALTER TABLE public.uhhp_auction_nominations
  ADD CONSTRAINT uhhp_auction_nominations_status_ck
  CHECK (
    status IN (
      'awaiting_nomination',
      'sealed_bidding',
      'tie_break_bidding',
      'revealed',
      'rfa_match_pending',
      'finalized',
      'no_sale',
      'void'
    )
  );

-- 2) One sealed re-bid per tied team per nomination.
CREATE TABLE IF NOT EXISTS public.uhhp_auction_tiebreak_bids (
  id BIGSERIAL PRIMARY KEY,
  nomination_id UUID NOT NULL,
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  team_id TEXT NOT NULL,
  amount INTEGER NOT NULL,
  idempotency_key TEXT NOT NULL,
  actor_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uhhp_auction_tiebreak_bids_amount_ck
    CHECK (
      amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
      AND amount >= 0
      AND amount = TRUNC(amount)
    ),
  CONSTRAINT uhhp_auction_tiebreak_bids_key_ck
    CHECK (BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_tiebreak_bids_team_uk
    UNIQUE (nomination_id, team_id)
);

ALTER TABLE public.uhhp_auction_tiebreak_bids
  ADD CONSTRAINT uhhp_auction_tiebreak_bids_nomination_fk
  FOREIGN KEY (nomination_id, draft_id, league_id)
  REFERENCES public.uhhp_auction_nominations (id, draft_id, league_id)
  ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_uhhp_tiebreak_bids_nomination
  ON public.uhhp_auction_tiebreak_bids (nomination_id, team_id);