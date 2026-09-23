-- Remove the Kucherov test-auction contract from uhhp-barney (Mark Henderson).
--
-- This undoes the auction-created cbs_rosters row (source_url
-- 'uhhp-auction-2026') plus its nomination / bid-event / audit trail. The
-- player pool row for Nikita Kucherov is deliberately left untouched: he is
-- an unrostered UFA free agent and should be available for the real auction.
--
-- Safe to re-run: every statement is scoped to the specific nomination id.
-- (uhhp_auction_latest_effective_bids is a read-only view over bid_events;
--  deleting the underlying bid events clears it automatically.)
BEGIN;

-- Disable append-only triggers for this one transaction only (auto-reset on commit).
SET LOCAL session_replication_role = replica;

DELETE FROM uhhp_auction_bid_events
 WHERE nomination_id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM uhhp_auction_events
 WHERE nomination_id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM uhhp_auction_rfa_decisions
 WHERE nomination_id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM uhhp_auction_tie_audits
 WHERE nomination_id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM cbs_rosters
 WHERE uhhp_auction_nomination_id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM uhhp_auction_nominations
 WHERE id = '9caf432b-8df0-49cb-b66f-9d54ec156222';

DELETE FROM cbs_players
 WHERE cbs_player_id = 'uhhp-auction-9caf432b-8df';

COMMIT;