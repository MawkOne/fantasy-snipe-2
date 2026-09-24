"""Apply final UHHP roster transactions through 2026-09-23 21:51 ET.

Updates both the canonical roster JSON (``--update-source``) and the live
PostgreSQL snapshot/pool (``--apply``). Operations are idempotent.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
ROSTER_PATH = ROOT / "public" / "fantasy_hockey_rosters_2026_updated_2026-09-23.json"
STATUS_PATH = ROOT / "public" / "uhhp_roster_free_agent_status_2026.json"

DROPS = [
    ("South Calgary Oilers", "Barrett Hayton"),
    ("The Pylons", "Nathan MacKinnon"),
    ("3sheets Sports Entertainment", "Seth Jarvis"),
    ("The Dook of Sook", "Yegor Sharangovich"),
    ("LIP's Lasers", "Kent Johnson"),
]
TRADES = [
    ("Cole Caufield", "LIP's Lasers", "The Pylons"),
    ("2027 Draft Pick LIP", "The Pylons", "LIP's Lasers"),
]
CAP_HIT_ID = "1000000862"


def normalize_dsn(value: str) -> str:
    return value.replace("postgresql+psycopg2://", "postgresql://", 1)


def find_team(data: dict[str, Any], name: str) -> dict[str, Any]:
    return next(team for team in data["teams"] if team["team"] == name)


def pop_player(team: dict[str, Any], name: str) -> tuple[dict[str, Any] | None, str | None]:
    for section in ("skaters", "goalies"):
        rows = team.get(section, [])
        for index, player in enumerate(rows):
            if str(player.get("name") or "").replace("*", "").strip().casefold() == name.casefold():
                return rows.pop(index), section
    return None, None


def update_source() -> dict[str, Any]:
    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    removed: dict[str, dict[str, Any]] = {}
    changes: list[str] = []
    for team_name, player_name in DROPS:
        team = find_team(data, team_name)
        player, _ = pop_player(team, player_name)
        if player:
            removed[player_name] = player
            changes.append(f"dropped {player_name} from {team_name}")

    for player_name, from_team_name, to_team_name in TRADES:
        from_team = find_team(data, from_team_name)
        to_team = find_team(data, to_team_name)
        player, section = pop_player(from_team, player_name)
        if player:
            target_section = "goalies" if str(player.get("position") or "").upper() == "G" else "skaters"
            to_team.setdefault(target_section, []).append(player)
            changes.append(f"moved {player_name}: {from_team_name} -> {to_team_name}")
        elif not any(
            str(p.get("name") or "").casefold() == player_name.casefold()
            for p in to_team.get("skaters", []) + to_team.get("goalies", [])
        ):
            raise RuntimeError(f"Could not find {player_name} in source or destination")

    socal = find_team(data, "South Calgary Oilers")
    if not any(str(p.get("name") or "").casefold() == "z-caphit hayton" for p in socal.get("skaters", [])):
        hayton = removed.get("Barrett Hayton")
        if not hayton:
            raise RuntimeError("Barrett Hayton source row required to create cap hit")
        socal.setdefault("skaters", []).append(
            {
                "cbs_player_id": int(CAP_HIT_ID),
                "name": "z-CAPHIT Hayton",
                "roster_position": "C",
                "position": "C",
                "nhl_team": "-",
                "status": "active",
                "first_opponent": None,
                "first_game": None,
                "schedule": None,
                "rank": None,
                "rostered_pct": None,
                "start_pct": None,
                "salary": hayton.get("salary"),
                "years": hayton.get("years"),
                "rookie": False,
                "fantasy_points_2025": 0,
                "fantasy_points_3yr_avg": 0,
                "fantasy_points_proj": 0,
                "cbs_url": f"https://uhhp.hockey.cbssports.com/players/playerpage/{CAP_HIT_ID}",
                "placeholder_type": "cap_hit",
                "note": "Added 9/23/26 after Barrett Hayton was dropped; salary/years carried forward from Hayton's prior roster contract.",
            }
        )
        changes.append("added z-CAPHIT Hayton to South Calgary Oilers")

    data["transactions_applied_through"] = "2026-09-23 21:51 ET"
    data["source"] = "CBS Sports fantasy hockey roster export supplied by user; updated with user-supplied transactions through 9/23/26 9:51 PM ET"
    ROSTER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if STATUS_PATH.exists():
        status_data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        for row in status_data.get("players", []):
            if row.get("player_name") == "Cole Caufield":
                row["fantasy_team"] = "The Pylons"
        STATUS_PATH.write_text(json.dumps(status_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"changes": changes, "source": str(ROSTER_PATH)}


def apply_db() -> dict[str, Any]:
    try:
        import psycopg2  # type: ignore[import-not-found]
        import psycopg2.extras  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary is required") from exc
    dsn = os.environ.get("FANTASY_DATABASE_URL")
    if not dsn:
        raise RuntimeError("FANTASY_DATABASE_URL is required")
    connection = psycopg2.connect(normalize_dsn(dsn), connect_timeout=10)
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT draft.id, draft.league_id
                  FROM uhhp_auction_drafts draft
                  JOIN cbs_leagues league ON league.id=draft.league_id
                 WHERE league.provider_slug='uhhp' AND draft.draft_year=2026
                 LIMIT 1
                """
            )
            draft_id, league_id = cursor.fetchone()
            cursor.execute("SELECT team_id, team_name FROM cbs_teams WHERE league_id=%s", (league_id,))
            team_ids = {name: tid for tid, name in cursor.fetchall()}
            dropped = moved = 0
            for team_name, player_name in DROPS:
                cursor.execute(
                    """
                    SELECT pool.id, pool.cbs_player_id
                      FROM uhhp_auction_player_pool pool
                     WHERE pool.draft_id=%s AND LOWER(pool.player_name)=LOWER(%s)
                     LIMIT 1
                    """,
                    (draft_id, player_name),
                )
                pool_id, cbs_id = cursor.fetchone()
                cursor.execute(
                    """
                    DELETE FROM cbs_rosters
                     WHERE league_id=%s AND team_id=%s AND cbs_player_id=%s
                       AND uhhp_auction_nomination_id IS NULL
                    """,
                    (league_id, team_ids[team_name], cbs_id),
                )
                dropped += cursor.rowcount
                cursor.execute(
                    """
                    UPDATE uhhp_auction_player_pool
                       SET eligibility='UFA', free_agent_status='UFA',
                           controlling_team_id=NULL, salary=NULL, contract_years=0,
                           source_availability='W', source_team=NULL,
                           source_status='waiver',
                           metadata=metadata || %s::jsonb, updated_at=NOW()
                     WHERE id=%s
                    """,
                    (
                        psycopg2.extras.Json(
                            {
                                "rostered": False,
                                "is_waiver": True,
                                "roster_team": None,
                                "roster_team_id": None,
                                "roster_team_key": None,
                                "listed_fantasy_team": None,
                                "auction_eligible": True,
                                "classification_reason": "released before auction; unrestricted free agent",
                                "transaction_date": "2026-09-23",
                            }
                        ),
                        pool_id,
                    ),
                )

            # Cole Caufield: RFA rights move from LIP to Pylons.
            cursor.execute("SELECT cbs_player_id FROM uhhp_auction_player_pool WHERE draft_id=%s AND LOWER(player_name)=LOWER('Cole Caufield')", (draft_id,))
            caufield_id = cursor.fetchone()[0]
            cursor.execute(
                """
                UPDATE cbs_rosters SET team_id=%s
                 WHERE league_id=%s AND team_id=%s AND cbs_player_id=%s
                   AND uhhp_auction_nomination_id IS NULL
                """,
                (team_ids["The Pylons"], league_id, team_ids["LIP's Lasers"], caufield_id),
            )
            moved += cursor.rowcount
            cursor.execute(
                """
                UPDATE uhhp_auction_player_pool
                   SET controlling_team_id=%s, source_team=%s,
                       metadata=metadata || %s::jsonb, updated_at=NOW()
                 WHERE draft_id=%s AND cbs_player_id=%s
                """,
                (
                    team_ids["The Pylons"], "The Pylons",
                    psycopg2.extras.Json(
                        {
                            "rostered": True,
                            "roster_team": "The Pylons",
                            "roster_team_id": team_ids["The Pylons"],
                            "roster_team_key": "jg",
                            "listed_fantasy_team": "The Pylons",
                            "transaction_date": "2026-09-23",
                        }
                    ),
                    draft_id, caufield_id,
                ),
            )

            # Draft-pick asset moves from Pylons to LIP.
            cursor.execute(
                """
                UPDATE uhhp_auction_player_pool
                   SET source_team=%s, metadata=metadata || %s::jsonb, updated_at=NOW()
                 WHERE draft_id=%s AND LOWER(player_name)=LOWER('2027 Draft Pick LIP')
                """,
                (
                    "LIP's Lasers",
                    psycopg2.extras.Json(
                        {
                            "rostered": True,
                            "roster_team": "LIP's Lasers",
                            "roster_team_id": team_ids["LIP's Lasers"],
                            "roster_team_key": "lp",
                            "listed_fantasy_team": "LIP's Lasers",
                            "transaction_date": "2026-09-23",
                        }
                    ),
                    draft_id,
                ),
            )
            moved += cursor.rowcount

            # South Calgary cap-hit placeholder, carried from Hayton's $2/2y deal.
            cursor.execute(
                """
                INSERT INTO cbs_players (cbs_player_id, full_name, pos_primary, positions, nhl_team_abbr)
                VALUES (%s, 'z-CAPHIT Hayton', 'C', ARRAY['C']::TEXT[], '-')
                ON CONFLICT (cbs_player_id) DO UPDATE SET full_name=EXCLUDED.full_name
                """,
                (CAP_HIT_ID,),
            )
            cursor.execute(
                """
                INSERT INTO uhhp_auction_player_pool (
                  draft_id, league_id, source_key, cbs_player_id, player_name,
                  positions, nhl_team_abbrev, source_availability, source_team,
                  contract_years, salary, is_rookie, source_status, entry_type,
                  eligibility, projection, projected_fantasy_points, metadata
                ) VALUES (
                  %s,%s,'z caphit hayton|C|-',%s,'z-CAPHIT Hayton',ARRAY['C']::TEXT[],'-',
                  'South Calgary Oilers','South Calgary Oilers',2,2,FALSE,'active','cap_hit',
                  'CAP_HIT','{}'::jsonb,0,%s::jsonb
                )
                ON CONFLICT (draft_id, source_key) DO UPDATE SET
                  source_team=EXCLUDED.source_team, contract_years=EXCLUDED.contract_years,
                  salary=EXCLUDED.salary, eligibility='CAP_HIT', entry_type='cap_hit',
                  metadata=EXCLUDED.metadata, updated_at=NOW()
                """,
                (
                    draft_id, league_id, CAP_HIT_ID,
                    psycopg2.extras.Json(
                        {
                            "rostered": True,
                            "is_waiver": False,
                            "roster_team": "South Calgary Oilers",
                            "roster_team_id": team_ids["South Calgary Oilers"],
                            "roster_team_key": "socal",
                            "roster_section": "skaters",
                            "listed_fantasy_team": "South Calgary Oilers",
                            "auction_eligible": False,
                            "classification_reason": "z-CAPHIT cap obligation from Barrett Hayton release",
                            "transaction_date": "2026-09-23",
                        }
                    ),
                ),
            )
            connection.commit()
            return {"dropped_roster_rows": dropped, "moved_rows": moved, "cap_hit": "z-CAPHIT Hayton"}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-source", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.update_source:
        print(update_source())
    if args.apply:
        print(apply_db())
    if not args.update_source and not args.apply:
        print({"drops": DROPS, "trades": TRADES, "cap_hit": "z-CAPHIT Hayton"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
