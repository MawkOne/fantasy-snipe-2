"""Apply the authoritative UHHP 2026 roster RFA/UFA classification source.

Input: public/uhhp_roster_free_agent_status_2026.json
Writes birthdates/NHL IDs to CBS tables and age/status/controlling rights to
uhhp_auction_player_pool. Only roster rows with contract years == 0 are touched.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("public/uhhp_roster_free_agent_status_2026.json")


def normalize_dsn(value: str) -> str:
    return value.replace("postgresql+psycopg2://", "postgresql://", 1)


def apply(path: Path) -> dict[str, Any]:
    try:
        import psycopg2  # type: ignore[import-not-found]
        import psycopg2.extras  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary is required") from exc

    dsn = os.environ.get("FANTASY_DATABASE_URL")
    if not dsn:
        raise RuntimeError("FANTASY_DATABASE_URL is required")
    source = json.loads(path.read_text(encoding="utf-8"))
    records = source.get("players") or []
    if len(records) != 65 or source.get("unresolved"):
        raise RuntimeError("Expected 65 resolved roster free-agent records")

    connection = psycopg2.connect(normalize_dsn(dsn), connect_timeout=10)
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT draft.id, draft.league_id
                  FROM uhhp_auction_drafts AS draft
                  JOIN cbs_leagues AS league ON league.id = draft.league_id
                 WHERE league.provider_slug = 'uhhp' AND draft.draft_year = 2026
                 LIMIT 1
                """
            )
            draft_row = cursor.fetchone()
            if not draft_row:
                raise RuntimeError("UHHP 2026 draft not initialized")
            draft_id, league_id = draft_row
            pool_updates = roster_updates = player_updates = 0
            for record in records:
                cbs_id = str(record["cbs_player_id"])
                status = str(record["free_agent_status"])
                cursor.execute(
                    """
                    UPDATE cbs_players
                       SET birthdate = %s,
                           nhl_team_abbr = COALESCE(%s, nhl_team_abbr),
                           last_seen_at = NOW()
                     WHERE cbs_player_id = %s
                    """,
                    (record["birthdate"], record.get("nhl_team"), cbs_id),
                )
                player_updates += cursor.rowcount
                cursor.execute(
                    """
                    INSERT INTO cbs_player_map (
                      cbs_player_id, nhl_player_id, confidence, match_method, mapped_at
                    ) VALUES (%s, %s, 1.0, 'exact_name_position_nhl_api', NOW())
                    ON CONFLICT (cbs_player_id) DO UPDATE SET
                      nhl_player_id = EXCLUDED.nhl_player_id,
                      confidence = EXCLUDED.confidence,
                      match_method = EXCLUDED.match_method,
                      mapped_at = NOW()
                    """,
                    (cbs_id, int(record["nhl_player_id"])),
                )
                cursor.execute(
                    """
                    UPDATE cbs_rosters
                       SET nhl_player_id = %s,
                           future_fa = %s
                     WHERE league_id = %s
                       AND cbs_player_id = %s
                       AND years = 0
                       AND uhhp_auction_nomination_id IS NULL
                    """,
                    (int(record["nhl_player_id"]), status, int(league_id), cbs_id),
                )
                roster_updates += cursor.rowcount
                cursor.execute(
                    """
                    UPDATE uhhp_auction_player_pool AS pool
                       SET nhl_player_id = %s,
                           birthdate = %s,
                           age_cutoff_date = %s,
                           age_at_cutoff = %s,
                           free_agent_status = %s,
                           eligibility = CASE
                             WHEN pool.entry_type = 'rookie' THEN pool.eligibility
                             ELSE %s
                           END,
                           controlling_team_id = CASE
                             WHEN %s = 'RFA' THEN (
                               SELECT roster.team_id
                                 FROM cbs_rosters AS roster
                                WHERE roster.league_id = pool.league_id
                                  AND roster.cbs_player_id = pool.cbs_player_id
                                  AND roster.years = 0
                                  AND roster.uhhp_auction_nomination_id IS NULL
                                LIMIT 1
                             )
                             ELSE NULL
                           END,
                           metadata = pool.metadata || %s::jsonb,
                           updated_at = NOW()
                     WHERE pool.draft_id = %s
                       AND pool.cbs_player_id = %s
                    """,
                    (
                        int(record["nhl_player_id"]),
                        record["birthdate"],
                        record["age_cutoff_date"],
                        int(record["age_at_cutoff"]),
                        status,
                        status,
                        status,
                        psycopg2.extras.Json(
                            {
                                "age_source": record["source"],
                                "free_agent_status": status,
                                "classification_reason": (
                                    f"expired contract; age {record['age_at_cutoff']} on "
                                    f"{record['age_cutoff_date']}"
                                ),
                            }
                        ),
                        draft_id,
                        cbs_id,
                    ),
                )
                pool_updates += cursor.rowcount
            connection.commit()
            return {
                "records": len(records),
                "cbs_players_updated": player_updates,
                "cbs_rosters_updated": roster_updates,
                "pool_rows_updated": pool_updates,
            }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for record in source.get("players") or []:
        status = str(record["free_agent_status"])
        counts[status] = counts.get(status, 0) + 1
    print({"records": len(source.get("players") or []), "unresolved": len(source.get("unresolved") or []), "statuses": counts})
    if args.apply:
        print(apply(args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
