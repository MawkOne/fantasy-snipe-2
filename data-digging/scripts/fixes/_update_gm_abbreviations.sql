-- Update canonical team abbreviations per GM preference (2026 draft).
-- Matches public/gms.md:
--   New Oilers Nation    BARNEY      -> NoN
--   Jeff's Jackass's     Jeff'sJack  -> JJ
--   The Dook of Sook     SookDook    -> Dook

BEGIN;

UPDATE cbs_teams
   SET abbrev = 'NoN'
 WHERE team_id = 'uhhp-barney';

UPDATE cbs_teams
   SET abbrev = 'JJ'
 WHERE team_id = 'uhhp-jeffsjack';

UPDATE cbs_teams
   SET abbrev = 'Dook'
 WHERE team_id = 'uhhp-sookdook';

UPDATE uhhp_auction_draft_teams
   SET canonical_abbrev = 'NoN'
 WHERE team_id = 'uhhp-barney';

UPDATE uhhp_auction_draft_teams
   SET canonical_abbrev = 'JJ'
 WHERE team_id = 'uhhp-jeffsjack';

UPDATE uhhp_auction_draft_teams
   SET canonical_abbrev = 'Dook'
 WHERE team_id = 'uhhp-sookdook';

COMMIT;