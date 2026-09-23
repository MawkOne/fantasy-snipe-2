-- Zero out salaries on expired (0 contract-year) roster contracts.
--
-- Players with years = 0 no longer hold a paying contract (they are
-- UFA/RFA/REVIEW free agents), so their stale CBS placeholder salary is set
-- to $0. Signed (1-3 year) and cap-hit rows are untouched.

BEGIN;

UPDATE cbs_rosters
   SET salary = 0
 WHERE league_id = (SELECT id FROM cbs_leagues WHERE provider_slug = 'uhhp')
   AND years = 0
   AND COALESCE(salary, 0) <> 0;

COMMIT;