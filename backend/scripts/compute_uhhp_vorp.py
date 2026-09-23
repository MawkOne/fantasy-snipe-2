"""Compute VORP and VORP$ for the UHHP 2026 auction pool.

Canonical methodology (public/UHHP_2026_projection_methodology.md):

  VORP = projected FPTS - position replacement FPTS
    Forward replacement : 149.51  (108 active forward slots: 9 x 12 teams)
    Defense  replacement :  93.98  (48  active defense  slots: 4 x 12 teams)
    Goalie   replacement : 120.34  (24  active goalie   slots: 2 x 12 teams)

  VORP$ = max($2, $2 + positive VORP x 0.10791), rounded to whole dollars

The computed values are stored in uhhp_auction_player_pool.projection under
the `vorp` and `vorp_salary` keys so the API can serve them per player.

Default mode is a pure-stdlib dry run. ``--apply`` lazily imports psycopg2
and writes the values in one transaction.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

EXPECTED_PYTHON = (3, 11)

REPLACEMENT_FPTS = {
    "F": 149.51,
    "D": 93.98,
    "G": 120.34,
}
VORP_DOLLAR_RATE = 0.10791
MIN_AUCTION_SALARY = 2


def import_psycopg2() -> Tuple[Any, Any]:
    try:
        import psycopg2  # type: ignore[import-not-found]
        import psycopg2.extras  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("--apply requires psycopg2 (install psycopg2-binary)") from exc
    return psycopg2, psycopg2.extras


def normalize_postgres_dsn(value: str) -> str:
    return value.replace("postgresql+psycopg2://", "postgresql://", 1)


def position_group(positions: Sequence[str]) -> Optional[str]:
    """Normalize skaters into F / D / G valuation groups per the methodology."""
    s = {(p or "").strip().upper() for p in positions}
    forward = bool(s & {"C", "W", "LW", "RW", "F"})
    if "G" in s and not forward and not ("D" in s):
        return "G"
    if "D" in s and not forward:
        return "D"
    return "F" if s else None


def vorp_dollar(vorp: float) -> int:
    positive = max(0.0, vorp)
    return max(MIN_AUCTION_SALARY, round(MIN_AUCTION_SALARY + positive * VORP_DOLLAR_RATE))


def apply(season: int) -> Dict[str, Any]:
    psycopg2, extras = import_psycopg2()
    dsn = os.environ.get("FANTASY_DATABASE_URL")
    if not dsn:
        raise RuntimeError("--apply requires FANTASY_DATABASE_URL to be set")
    connection = psycopg2.connect(normalize_postgres_dsn(dsn), connect_timeout=10)
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT draft.id
                  FROM uhhp_auction_drafts AS draft
                  JOIN cbs_leagues AS league ON league.id = draft.league_id
                 WHERE draft.draft_year = %s
                   AND league.provider_slug = 'uhhp'
                 ORDER BY draft.created_at DESC
                 LIMIT 1
                """,
                (season,),
            )
            draft_row = cursor.fetchone()
            if not draft_row:
                raise RuntimeError(f"No UHHP draft found for {season}")
            draft_id = draft_row[0]

            cursor.execute(
                """
                SELECT id, player_name, positions, projected_fantasy_points,
                       entry_type
                  FROM uhhp_auction_player_pool
                 WHERE draft_id = %s
                   AND projected_fantasy_points IS NOT NULL
                """,
                (draft_id,),
            )
            players = [
                {
                    "id": row[0],
                    "name": row[1],
                    "positions": list(row[2] or []),
                    "fp": float(row[3]),
                    "entry_type": row[4],
                }
                for row in cursor.fetchall()
            ]

            counts: Dict[str, int] = {"F": 0, "D": 0, "G": 0}
            updated = 0
            skipped = 0
            by_group: Dict[str, List[Dict[str, Any]]] = {"F": [], "D": [], "G": []}
            for player in players:
                if player["entry_type"] not in ("player", "rookie"):
                    skipped += 1
                    continue
                group = position_group(player["positions"])
                if not group:
                    skipped += 1
                    continue
                player["group"] = group
                by_group[group].append(player)
                counts[group] += 1

            # Apply the formula and persist.
            for group, group_players in by_group.items():
                replacement = REPLACEMENT_FPTS[group]
                for player in group_players:
                    fp = player["fp"]
                    vorp = round(fp - replacement, 2)
                    salary = vorp_dollar(vorp)
                    cursor.execute(
                        """
                        UPDATE uhhp_auction_player_pool
                           SET projection = projection || %s::jsonb,
                               updated_at = NOW()
                         WHERE id = %s AND draft_id = %s
                        """,
                        (
                            extras.Json({
                                "vorp": vorp,
                                "vorp_salary": salary,
                                "replacement_fpts": replacement,
                            }),
                            player["id"],
                            draft_id,
                        ),
                    )
                    if cursor.rowcount:
                        updated += 1

            connection.commit()
            return {
                "draft_id": str(draft_id),
                "players_with_fp": len(players),
                "groups": counts,
                "updated": updated,
                "skipped": skipped,
            }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute UHHP VORP and VORP$ for the auction pool per the canonical "
            "methodology. Default mode is a database-free dry run."
        )
    )
    parser.add_argument("--season", type=int, default=2026, help="Season year")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write VORP/VORP$ into uhhp_auction_player_pool.projection "
        "(requires FANTASY_DATABASE_URL and psycopg2).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if sys.version_info < EXPECTED_PYTHON:
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2

    print(
        "VORP$ conversion: max($2, $2 + positive VORP x "
        f"{VORP_DOLLAR_RATE}) -> whole dollars"
    )
    if not args.apply:
        for group, replacement in REPLACEMENT_FPTS.items():
            print(f"  replacement {group}: {replacement} FPTS")
        print("Dry run only; pass --apply to write to the database.")
        return 0

    try:
        report = apply(args.season)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key, value in report.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())