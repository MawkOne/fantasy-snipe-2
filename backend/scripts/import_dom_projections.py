"""Import Dom Luszczyszyn (The Athletic) 2026 season projections.

Reads ``public/dom-projections.json`` (per-game rates for 671 players),
computes UHHP fantasy points using the league's scoring rules, stores the
rows in ``dom_player_projections``, then overlays the numbers onto
``uhhp_auction_player_pool`` so the auction UI projects with Dom's numbers.

Scoring (derived from the uhhp-sept-22.csv / goalies.csv FPTS columns and
the league snapshot; verified to reproduce the source FPTS exactly for
skaters and within rounding for goalies):

  skater FP = G*3 + A*2 + (+/-)*0.25 + SHG*2        (on season totals)
  goalie FP = GP * (W*2 + SO*1 + SV*0.2 + GA*(-1.25))

The default mode is a pure-stdlib dry run. ``--apply`` lazily imports
psycopg2 and writes both tables inside one transaction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

EXPECTED_PYTHON = (3, 11)
SOURCE = "the-athletic-dom"
SEASON = 2026


class SourceError(Exception):
    pass


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_name(value: str) -> str:
    cleaned = collapse_whitespace(value or "").replace("’", "'")
    decomposed = unicodedata.normalize("NFKD", cleaned).casefold()
    characters: list[str] = []
    for character in decomposed:
        if unicodedata.combining(character):
            continue
        characters.append(character if character.isalnum() else " ")
    return collapse_whitespace("".join(characters))


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number == number else None  # reject NaN


SOURCE_STAT_KEYS: Dict[str, str] = {
    "GP": "gp", "G": "g", "A": "a", "PTS": "pts", "SOG": "sog",
    "PPG": "ppg", "PPP": "ppp", "SHG": "shg", "SHP": "shp",
    "BLK": "blk", "HIT": "hit", "+/-": "plus_minus", "PIM": "pim",
    "GWG": "gwg", "FOW": "fow", "FOL": "fol", "FO%": "fo_pct",
    "W": "w", "L": "l", "OTL": "otl", "SO": "so", "SV": "sv",
    "SV%": "sv_pct", "GA": "ga",
}


def normalize_team(value: str) -> Optional[str]:
    """Normalize Dom's team column (e.g. 'T.B', 'S.J') to plain abbrevs."""
    if not value:
        return None
    cleaned = "".join(ch for ch in value.strip().upper() if ch.isalnum())
    return cleaned or None


# Dom spellings that differ from the pool's display names. Keys/values are
# normalized forms (see normalize_name); ambiguous twins are resolved by
# position below (e.g. Elias Pettersson the C vs the D).
NAME_ALIASES: Dict[str, str] = {
    "mitch marner": "mitchell marner",
    "jj peterka": "john-jason peterka",
    "aliaksei protas": "alexei protas",
    "matt coronato": "matthew coronato",
    "yegor chinakhov": "egor chinakhov",
    "thomas novak": "tommy novak",
    "matt savoie": "matthew savoie",
    "ben kindel": "benjamin kindel",
    "zachary bolduc": "zack bolduc",
    "alex nikishin": "alexander nikishin",
    "alex texier": "alexandre texier",
    "max shabanov": "maxim shabanov",
    "alex kerfoot": "alexander kerfoot",
    "michael eyssimont": "mikey eyssimont",
    "alex holtz": "alexander holtz",
    "nick perbix": "nicklaus perbix",
    "alex romanov": "alexander romanov",
    "alex carrier": "alexandre carrier",
    "william borgen": "will borgen",
    "chris tanev": "christopher tanev",
    "dmitri simashev": "dmitriy simashev",
    "joe veleno": "joseph veleno",
    "nico daws": "nicolas daws",
    "daniil tarasov g": "daniil tarasov",  # Dom tags the goalie '(G)'
    "elias pettersson": "elias pettersson",  # the center; D twin disambiguated by position
    "elias pettersson d": "elias pettersson",  # the defenseman; C twin disambiguated by position
}


def _position_hits(dom_position: Optional[str], pool_positions: Sequence[str]) -> bool:
    dom_set = {
        piece.strip().upper() for piece in (dom_position or "").split(",") if piece.strip()
    }
    pool_set = {(p or "").strip().upper() for p in pool_positions if p}
    return bool(dom_set & pool_set)


def parse_dom_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise SourceError(f"Missing Dom projections file: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceError(f"Could not parse Dom projections file: {exc}") from exc
    if not isinstance(payload, list):
        raise SourceError("dom-projections.json must contain a JSON array of players")

    rows: List[Dict[str, Any]] = []
    for index, raw in enumerate(payload):
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("Player") or "").strip()
        if not name:
            continue
        team = normalize_team(raw.get("Team"))
        position = str(raw.get("Pos") or "").strip().upper() or None
        is_goalie = position == "G"

        if is_goalie:
            games_played = _as_float(raw.get("GP_2")) or _as_float(raw.get("GP"))
        else:
            games_played = _as_float(raw.get("GP"))

        stats: Dict[str, Any] = {}
        for source_key, target_key in SOURCE_STAT_KEYS.items():
            value = _as_float(raw.get(source_key))
            if value is not None:
                stats[target_key] = value

        rows.append({
            "source_row": index,
            "name": name,
            "normalized_name": normalize_name(name),
            "team": team,
            "position": position,
            "is_goalie": is_goalie,
            "games_played": games_played,
            "stats": stats,
        })
    return rows


def compute_fantasy_points(row: Dict[str, Any]) -> Optional[float]:
    stats = row["stats"]
    games_played = row["games_played"]
    if not games_played or games_played <= 0:
        return None
    if row["is_goalie"]:
        per_game = (
            (stats.get("w") or 0.0) * 2.0
            + (stats.get("so") or 0.0) * 1.0
            + (stats.get("sv") or 0.0) * 0.2
            + (stats.get("ga") or 0.0) * (-1.25)
        )
        return round(games_played * per_game, 2)
    per_game = (
        (stats.get("g") or 0.0) * 3.0
        + (stats.get("a") or 0.0) * 2.0
        + (stats.get("plus_minus") or 0.0) * 0.25
        + (stats.get("shg") or 0.0) * 2.0
    )
    return round(games_played * per_game, 2)


def build_projection_metrics(row: Dict[str, Any], fantasy_points: float) -> Dict[str, Any]:
    stats = row["stats"]
    games_played = row["games_played"] or 0.0
    metrics: Dict[str, Any] = {"source": SOURCE}
    if row["is_goalie"]:
        ga_total = round(games_played * (stats.get("ga") or 0.0), 2)
        mappings = {
            "games_played": round(games_played, 1),
            "wins": round(games_played * (stats.get("w") or 0.0), 2),
            "losses": round(games_played * (stats.get("l") or 0.0), 2),
            "shutouts": round(games_played * (stats.get("so") or 0.0), 2),
            "goals_against": ga_total,
            "saves": round(games_played * (stats.get("sv") or 0.0), 2),
            "save_percentage": stats.get("sv_pct"),
            "goals_against_average": stats.get("ga"),
            "fantasy_points": fantasy_points,
        }
    else:
        mappings = {
            "gp": round(games_played, 1),
            "goals": round(games_played * (stats.get("g") or 0.0), 2),
            "assists": round(games_played * (stats.get("a") or 0.0), 2),
            "points": round(games_played * (stats.get("pts") or 0.0), 2),
            "plus_minus": round(games_played * (stats.get("plus_minus") or 0.0), 2),
            "pim": round(games_played * (stats.get("pim") or 0.0), 2),
            "power_play_goals": round(games_played * (stats.get("ppg") or 0.0), 2),
            "short_handed_goals": round(games_played * (stats.get("shg") or 0.0), 2),
            "shots_on_goal": round(games_played * (stats.get("sog") or 0.0), 2),
            "fantasy_points": fantasy_points,
        }
    metrics.update(mappings)
    return metrics


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import Dom Luszczyszyn (The Athletic) projections for the UHHP "
            "auction. Default mode is a database-free dry run."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to dom-projections.json (default: repo public/ directory)",
    )
    parser.add_argument(
        "--season", type=int, default=SEASON, help=f"Season year (default {SEASON})"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Write to the database. Requires FANTASY_DATABASE_URL and psycopg2; "
            "the JSON rows are upserted into dom_player_projections and matched "
            "pool rows are updated with Dom-based projections."
        ),
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Process only the first N rows (debug)"
    )
    return parser


def normalize_postgres_dsn(value: str) -> str:
    return value.replace("postgresql+psycopg2://", "postgresql://", 1)


def import_psycopg2() -> Tuple[Any, Any]:
    try:
        import psycopg2  # type: ignore[import-not-found]
        import psycopg2.extras  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SourceError("--apply requires psycopg2 (install psycopg2-binary)") from exc
    return psycopg2, psycopg2.extras


def apply_rows(rows: List[Dict[str, Any]], season: int) -> Dict[str, Any]:
    psycopg2, extras = import_psycopg2()
    dsn = os.environ.get("FANTASY_DATABASE_URL")
    if not dsn:
        raise SourceError("--apply requires FANTASY_DATABASE_URL to be set")
    connection = psycopg2.connect(normalize_postgres_dsn(dsn), connect_timeout=10)
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            # Locate the canonical 2026 draft for the UHHP league.
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
                raise SourceError(f"No UHHP draft found for {season}")

            # Load the pool's own key for matching: normalized name + team.
            cursor.execute(
                """
                SELECT id, player_name, nhl_team_abbrev, positions
                  FROM uhhp_auction_player_pool
                 WHERE draft_id = %s
                """,
                (draft_row[0],),
            )
            pool_by_name: Dict[str, List[Dict[str, Any]]] = {}
            for pool_id, pool_name, pool_team, pool_positions in cursor.fetchall():
                key = normalize_name(pool_name)
                pool_by_name.setdefault(key, []).append({
                    "id": pool_id,
                    "name": pool_name,
                    "team": (pool_team or "").upper(),
                    "positions": list(pool_positions or []),
                })

            dom_inserted = 0
            dom_updated = 0
            pool_updated = 0
            matched = 0
            skipped = 0
            unmatched_names: Counter = Counter()

            for row in rows:
                normalized = row["normalized_name"]
                team = row["team"]
                fantasy_points = compute_fantasy_points(row)
                metrics = (
                    build_projection_metrics(row, fantasy_points)
                    if fantasy_points is not None
                    else {"source": SOURCE}
                )
                cursor.execute(
                    """
                    INSERT INTO dom_player_projections (
                      season, source, source_key, player_name, normalized_name,
                      nhl_team, position, is_goalie, games_played, stats, fantasy_points
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (season, source_key) DO UPDATE SET
                      player_name = EXCLUDED.player_name,
                      nhl_team = EXCLUDED.nhl_team,
                      position = EXCLUDED.position,
                      is_goalie = EXCLUDED.is_goalie,
                      games_played = EXCLUDED.games_played,
                      stats = EXCLUDED.stats,
                      fantasy_points = EXCLUDED.fantasy_points,
                      updated_at = NOW()
                    """,
                    (
                        season, SOURCE, f"{normalized}|{team or ''}",
                        row["name"], normalized, team, row["position"],
                        row["is_goalie"], row["games_played"],
                        extras.Json(row["stats"]), fantasy_points,
                    ),
                )
                if cursor.rowcount == 0:
                    dom_inserted += 0
                elif cursor.statusmessage.startswith("INSERT"):
                    dom_inserted += 1
                else:
                    dom_updated += 1

                # Overlay onto the pool by normalized name (+ team tiebreak).
                pool_key = normalize_name(NAME_ALIASES.get(normalized, normalized))
                candidates = pool_by_name.get(pool_key, [])
                if not candidates:
                    unmatched_names[normalized] += 1
                    skipped += 1
                    continue
                target = None
                if len(candidates) == 1:
                    target = candidates[0]
                else:
                    if team:
                        team_matches = [c for c in candidates if c["team"] == team]
                        candidates = team_matches or candidates
                    position_matches = [
                        c for c in candidates if _position_hits(row["position"], c["positions"])
                    ]
                    if len(position_matches) == 1:
                        target = position_matches[0]
                    elif len(candidates) == 1:
                        target = candidates[0]
                if target is None:
                    unmatched_names[f"{normalized} (ambiguous)"] += 1
                    skipped += 1
                    continue
                if fantasy_points is None:
                    continue
                cursor.execute(
                    """
                    UPDATE uhhp_auction_player_pool
                       SET projection = %s::jsonb,
                           projected_fantasy_points = %s,
                           updated_at = NOW()
                     WHERE id = %s AND draft_id = %s
                    """,
                    (extras.Json(metrics), fantasy_points, target["id"], draft_row[0]),
                )
                if cursor.rowcount:
                    pool_updated += 1
                    matched += 1

            connection.commit()
            return {
                "dom_inserted": dom_inserted,
                "dom_updated": dom_updated,
                "pool_matched": matched,
                "skipped": skipped,
                "unmatched_examples": unmatched_names.most_common(10),
            }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if sys.version_info < EXPECTED_PYTHON:
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2

    if args.input is None:
        args.input = Path(__file__).resolve().parents[2] / "public" / "dom-projections.json"

    rows = parse_dom_rows(args.input)
    if args.limit > 0:
        rows = rows[: args.limit]

    goalies = sum(1 for r in rows if r["is_goalie"])
    with_points = 0
    for r in rows:
        if compute_fantasy_points(r) is not None:
            with_points += 1
    print(f"Parsed {len(rows)} rows ({len(rows) - goalies} skaters, {goalies} goalies)")
    print(f"Fantasy points computed for {with_points} players")

    if not args.apply:
        for row in rows[:5]:
            print(
                f"  {row['name']:<28} {row['team'] or '-':<4} {row['position'] or '-':<8} "
                f"GP={row['games_played']} FP={compute_fantasy_points(row)}"
            )
        print("Dry run only; pass --apply to write to the database.")
        return 0

    try:
        report = apply_rows(rows, args.season)
    except SourceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Applied:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())