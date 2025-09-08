#!/usr/bin/env python3
"""
Aggregates advanced metrics for a single player over a chosen scope, using
precomputed per-shift metrics and (optionally) shot-location danger tiers.

Data sources:
- PlayerShiftMetrics (primary rollup source)
- Game (for filtering by season/game_type)
- GameEvent (optional, to derive HD/MD/LD on the fly per shift)

Outputs a JSON object to stdout with totals, percentages, per-60s, zone/strength
splits, and (optional) HD/MD/LD tiers.

Note: HD/MD/LD classification here uses distance-to-nearest-net thresholds
(HD ≤ 25 ft, MD (25, 40], LD > 40). This can be refined later to include a
slot/home-plate polygon; the interface will remain stable.
"""

import os
import sys
import json
import math
import argparse
from typing import Any, Dict, List, Optional, Tuple

import site

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure SQLAlchemy is importable even if user-site path differs on the VM
try:
    from sqlalchemy.orm import sessionmaker  # type: ignore
except ModuleNotFoundError:
    try:
        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path:
            sys.path.append(user_site)
    except Exception:
        pass
    # Fallback to common per-user site-packages location
    fallback_user_site = os.path.expanduser("~/.local/lib/python3.9/site-packages")
    if os.path.isdir(fallback_user_site) and fallback_user_site not in sys.path:
        sys.path.append(fallback_user_site)
    from sqlalchemy.orm import sessionmaker  # type: ignore

from src.database.connection import connect_with_connector
from src.database.models import (
    PlayerShiftMetrics,
    Game,
    GameEvent,
    PlayerGameAdvancedMetrics,
    create_tables,
)
from sqlalchemy import and_, func

# Cache a single Engine/Sessionmaker per process to avoid repeated connector initialization
_ENGINE = None
_Session = None


def _get_session():
    global _ENGINE, _Session
    if _ENGINE is None or _Session is None:
        _ENGINE = connect_with_connector()
        _Session = sessionmaker(bind=_ENGINE)
    return _Session()


def mmss_to_seconds(mmss: Optional[str]) -> Optional[int]:
    if not mmss or ":" not in mmss:
        return None
    try:
        m, s = mmss.split(":")
        return int(m) * 60 + int(s)
    except Exception:
        return None


def safe_div(n: float, d: float) -> float:
    return n / d if d not in (0, 0.0) else 0.0


def rink_distance_to_nearest_net(x: Optional[float], y: Optional[float]) -> Optional[float]:
    """
    Approximate distance in feet to the nearest goal post using standard NHL
    event coordinates, where nets are at approximately x=±89, y=0.
    This avoids team/period mirroring complexity and is suitable for tiering.
    """
    if x is None or y is None:
        return None
    # Distances to each net
    dx1, dy1 = (x - 89.0), y
    dx2, dy2 = (x + 89.0), y
    d1 = math.hypot(dx1, dy1)
    d2 = math.hypot(dx2, dy2)
    return min(d1, d2)


HD_FT: float = 25.0
MD_FT: float = 40.0


def classify_danger(distance_ft: Optional[float]) -> Optional[str]:
    if distance_ft is None:
        return None
    if distance_ft <= HD_FT:
        return "HD"
    if distance_ft <= MD_FT:
        return "MD"
    return "LD"


def is_for(team_id: Optional[int], event_team_id: Optional[int]) -> Optional[bool]:
    if team_id is None or event_team_id is None:
        return None
    return team_id == event_team_id


def load_game_events(session, game_id: int) -> List[Dict[str, Any]]:
    rows = (
        session.query(
            GameEvent.period,
            GameEvent.period_time,
            GameEvent.team_id,
            GameEvent.event_type,
            GameEvent.coordinates_x,
            GameEvent.coordinates_y,
            GameEvent.event_idx,
            GameEvent.raw,
        )
        .filter(GameEvent.game_id == game_id)
        .all()
    )
    events: List[Dict[str, Any]] = []
    for r in rows:
        events.append(
            {
                "period": r.period,
                "period_time": r.period_time,
                "team_id": r.team_id,
                "event_type": r.event_type,
                "x": r.coordinates_x,
                "y": r.coordinates_y,
                "event_idx": r.event_idx,
                "raw": r.raw,
            }
        )
    # Deduplicate by event_idx or fallback composite key
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for ev in events:
        key = ev.get("event_idx")
        if key is None:
            key = (
                ev.get("period"),
                ev.get("period_time"),
                (ev.get("event_type") or "").upper(),
                ev.get("team_id"),
            )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ev)
    return deduped


def event_is_attempt(ev_type: Optional[str]) -> bool:
    if not ev_type:
        return False
    et = str(ev_type).strip().lower().replace(" ", "-").replace("_", "-")
    return (
        ("missed-shot" in et or et == "miss")
        or ("blocked-shot" in et or et == "block")
        or ("shot-on-goal" in et or et == "shot")
        or (et == "goal" or et.endswith("-goal"))
    )


def event_is_shot(ev_type: Optional[str]) -> bool:
    if not ev_type:
        return False
    et = str(ev_type).strip().lower().replace(" ", "-").replace("_", "-")
    return ("shot-on-goal" in et or et == "shot" or et == "goal" or et.endswith("-goal"))


def event_is_goal(ev_type: Optional[str]) -> bool:
    if not ev_type:
        return False
    et = str(ev_type).strip().lower().replace(" ", "-").replace("_", "-")
    return (et == "goal" or et.endswith("-goal"))


def aggregate_for_player(
    player_id: int,
    *,
    game_id: Optional[int] = None,
    season: Optional[int] = None,
    game_type: Optional[int] = None,
    strength: Optional[str] = None,  # EV, PP, SH
    include_danger: bool = False,
    exclude_zero_shifts: bool = False,
) -> Dict[str, Any]:
    session = _get_session()

    try:
        # Build base filter on PlayerShiftMetrics
        q = session.query(PlayerShiftMetrics).filter(PlayerShiftMetrics.player_id == player_id)

        if game_id is not None:
            q = q.filter(PlayerShiftMetrics.game_id == game_id)

        if season is not None or game_type is not None:
            # Join to games for season/game_type filtering
            q = (
                q.join(Game, Game.id == PlayerShiftMetrics.game_id)
            )
            if season is not None:
                q = q.filter(Game.season == season)
            if game_type is not None:
                q = q.filter(Game.game_type == game_type)

        if strength is not None:
            q = q.filter(PlayerShiftMetrics.strength_state == strength)

        rows: List[PlayerShiftMetrics] = q.all()
        if not rows:
            return {"player_id": player_id, "summary": {}, "message": "No shift metrics found for filters."}

        # Aggregate base totals
        totals: Dict[str, float] = {
            "CF": 0.0, "CA": 0.0, "FF": 0.0, "FA": 0.0,
            "SF": 0.0, "SA": 0.0, "GF": 0.0, "GA": 0.0,
            "BLK_FOR": 0.0, "BLK_AGAINST": 0.0,
            "HIT_FOR": 0.0, "HIT_AGAINST": 0.0,
            "TK_FOR": 0.0, "TK_AGAINST": 0.0,
            "GV_FOR": 0.0, "GV_AGAINST": 0.0,
            "TOI_seconds": 0.0, "Shifts": 0.0,
            "OZS": 0.0, "DZS": 0.0, "NZS": 0.0,
        }

        # Optional danger buckets
        danger: Dict[str, float] = {
            # Shots
            "HD_SF": 0.0, "MD_SF": 0.0, "LD_SF": 0.0,
            "HD_SA": 0.0, "MD_SA": 0.0, "LD_SA": 0.0,
            # Goals
            "HD_GF": 0.0, "MD_GF": 0.0, "LD_GF": 0.0,
            "HD_GA": 0.0, "MD_GA": 0.0, "LD_GA": 0.0,
            # Attempts (Corsi)
            "HD_CF": 0.0, "MD_CF": 0.0, "LD_CF": 0.0,
            "HD_CA": 0.0, "MD_CA": 0.0, "LD_CA": 0.0,
            # Fenwick (shots + misses)
            "HD_FF": 0.0, "MD_FF": 0.0, "LD_FF": 0.0,
            "HD_FA": 0.0, "MD_FA": 0.0, "LD_FA": 0.0,
        }

        # Preload events per game if danger is requested
        events_cache: Dict[int, List[Dict[str, Any]]] = {}

        for r in rows:
            # Detect all-zero counters early to optionally exclude this shift from aggregation
            counters_sum = (
                (r.attempts_for or 0)
                + (r.attempts_against or 0)
                + (r.unblocked_for or 0)
                + (r.unblocked_against or 0)
                + (r.shots_for or 0)
                + (r.shots_against or 0)
                + (r.goals_for or 0)
                + (r.goals_against or 0)
                + (r.hits_for or 0)
                + (r.hits_against or 0)
                + (r.takeaways_for or 0)
                + (r.takeaways_against or 0)
                + (r.giveaways_for or 0)
                + (r.giveaways_against or 0)
                + (r.blocks_for or 0)
                + (r.blocks_against or 0)
            )
            if exclude_zero_shifts and counters_sum == 0:
                continue

            # Base tallies
            totals["CF"] += float(r.attempts_for or 0)
            totals["CA"] += float(r.attempts_against or 0)
            # Fenwick = shots + misses; here unblocked_* stores misses count
            totals["FF"] += float((r.shots_for or 0) + (r.unblocked_for or 0))
            totals["FA"] += float((r.shots_against or 0) + (r.unblocked_against or 0))
            totals["SF"] += float(r.shots_for or 0)
            totals["SA"] += float(r.shots_against or 0)
            totals["GF"] += float(r.goals_for or 0)
            totals["GA"] += float(r.goals_against or 0)
            totals["BLK_FOR"] += float(r.blocks_for or 0)
            totals["BLK_AGAINST"] += float(r.blocks_against or 0)
            totals["HIT_FOR"] += float(r.hits_for or 0)
            totals["HIT_AGAINST"] += float(r.hits_against or 0)
            totals["TK_FOR"] += float(r.takeaways_for or 0)
            totals["TK_AGAINST"] += float(r.takeaways_against or 0)
            totals["GV_FOR"] += float(r.giveaways_for or 0)
            totals["GV_AGAINST"] += float(r.giveaways_against or 0)
            dsec = mmss_to_seconds(r.duration)
            if dsec is not None:
                totals["TOI_seconds"] += float(dsec)
            totals["Shifts"] += 1.0
            # Zone starts
            if r.zone_start == "O":
                totals["OZS"] += 1.0
            elif r.zone_start == "D":
                totals["DZS"] += 1.0
            elif r.zone_start == "N":
                totals["NZS"] += 1.0

            if include_danger:
                # Fetch/dedupe events for this game
                if r.game_id not in events_cache:
                    events_cache[r.game_id] = load_game_events(session, r.game_id)
                evs = events_cache[r.game_id]
                # Shift window
                start_s = mmss_to_seconds(r.start_time)
                end_s = mmss_to_seconds(r.end_time)
                if start_s is None or end_s is None:
                    continue
                # Filter window events same period and within [start, end]
                window: List[Dict[str, Any]] = []
                for ev in evs:
                    if ev.get("period") != r.period:
                        continue
                    t = mmss_to_seconds(ev.get("period_time"))
                    if t is None or t < start_s or t > end_s:
                        continue
                    window.append(ev)

                # Classify and tally
                for ev in window:
                    # Prefer normalized columns, but fall back to raw.coordinates if missing
                    _x = ev.get("x")
                    _y = ev.get("y")
                    if _x is None or _y is None:
                        _raw = ev.get("raw") or {}
                        if isinstance(_raw, dict):
                            _coords = (
                                _raw.get("coordinates")
                                or (_raw.get("details") or {}).get("coordinates")
                                or _raw.get("coords")
                                or {}
                            )
                            if isinstance(_coords, dict):
                                _x = _coords.get("x", _x)
                                _y = _coords.get("y", _y)
                            if _x is None or _y is None:
                                det = _raw.get("details") or {}
                                # Support xCoord/yCoord (and possible casing variants)
                                if isinstance(det, dict):
                                    _x = det.get("xCoord", det.get("xcoord", det.get("x", _x)))
                                    _y = det.get("yCoord", det.get("ycoord", det.get("y", _y)))
                    d_ft = rink_distance_to_nearest_net(_x, _y)
                    tier = classify_danger(d_ft)
                    if tier is None:
                        continue
                    side = is_for(r.team_id, ev.get("team_id"))
                    etype = ev.get("event_type")
                    # Attempts (Corsi)
                    if event_is_attempt(etype):
                        if side is True:
                            danger[f"{tier}_CF"] += 1.0
                        elif side is False:
                            danger[f"{tier}_CA"] += 1.0
                    # Fenwick: shots + misses (exclude blocks)
                    # We approximate by counting shots + misses here via event types
                    if event_is_shot(etype) or (etype and str(etype).lower().find("miss") >= 0):
                        if side is True:
                            danger[f"{tier}_FF"] += 1.0
                        elif side is False:
                            danger[f"{tier}_FA"] += 1.0
                    # Shots
                    if event_is_shot(etype):
                        if side is True:
                            danger[f"{tier}_SF"] += 1.0
                        elif side is False:
                            danger[f"{tier}_SA"] += 1.0
                    # Goals
                    if event_is_goal(etype):
                        if side is True:
                            danger[f"{tier}_GF"] += 1.0
                        elif side is False:
                            danger[f"{tier}_GA"] += 1.0

        # Derived
        toi = totals["TOI_seconds"]
        summary: Dict[str, Any] = {
            "totals": {
                **totals,
                "CorsiDiff": totals["CF"] - totals["CA"],
                "FenwickDiff": totals["FF"] - totals["FA"],
                "ShotDiff": totals["SF"] - totals["SA"],
                "GoalDiff": totals["GF"] - totals["GA"],
            },
            "percentages": {
                "CF%": safe_div(totals["CF"], (totals["CF"] + totals["CA"])),
                "FF%": safe_div(totals["FF"], (totals["FF"] + totals["FA"])),
                "SF%": safe_div(totals["SF"], (totals["SF"] + totals["SA"])),
                "GF%": safe_div(totals["GF"], (totals["GF"] + totals["GA"])),
                "OnIce_Sh%": safe_div(totals["GF"], max(totals["SF"], 1.0)),
                "OnIce_SV%": 1.0 - safe_div(totals["GA"], max(totals["SA"], 1.0)),
            },
            "per60": {
                "CF60": safe_div(totals["CF"], (toi / 3600.0) if toi > 0 else 0.0),
                "CA60": safe_div(totals["CA"], (toi / 3600.0) if toi > 0 else 0.0),
                "FF60": safe_div(totals["FF"], (toi / 3600.0) if toi > 0 else 0.0),
                "FA60": safe_div(totals["FA"], (toi / 3600.0) if toi > 0 else 0.0),
                "SF60": safe_div(totals["SF"], (toi / 3600.0) if toi > 0 else 0.0),
                "SA60": safe_div(totals["SA"], (toi / 3600.0) if toi > 0 else 0.0),
                "GF60": safe_div(totals["GF"], (toi / 3600.0) if toi > 0 else 0.0),
                "GA60": safe_div(totals["GA"], (toi / 3600.0) if toi > 0 else 0.0),
                "HIT60": safe_div(totals["HIT_FOR"], (toi / 3600.0) if toi > 0 else 0.0),
                "BLK60": safe_div(totals["BLK_FOR"], (toi / 3600.0) if toi > 0 else 0.0),
                "TK60": safe_div(totals["TK_FOR"], (toi / 3600.0) if toi > 0 else 0.0),
                "GV60": safe_div(totals["GV_FOR"], (toi / 3600.0) if toi > 0 else 0.0),
            },
            "zone": {
                "OZS": totals["OZS"],
                "DZS": totals["DZS"],
                "NZS": totals["NZS"],
                "OZS%": safe_div(totals["OZS"], max(totals["OZS"] + totals["DZS"], 1.0)),
            },
        }

        # PDO as scaled sum of on-ice shooting and save percentages
        summary["percentages"]["PDO"] = (
            (summary["percentages"]["OnIce_Sh%"] + summary["percentages"]["OnIce_SV%"]) * 1000.0
        )

        if include_danger:
            # Add tier percentages, shares, per60, and diffs
            def tier_pct(f: float, a: float) -> float:
                return safe_div(f, (f + a))

            tier = {
                "HD": {
                    "SF": danger["HD_SF"], "SA": danger["HD_SA"],
                    "CF": danger["HD_CF"], "CA": danger["HD_CA"],
                    "FF": danger["HD_FF"], "FA": danger["HD_FA"],
                    "GF": danger["HD_GF"], "GA": danger["HD_GA"],
                },
                "MD": {
                    "SF": danger["MD_SF"], "SA": danger["MD_SA"],
                    "CF": danger["MD_CF"], "CA": danger["MD_CA"],
                    "FF": danger["MD_FF"], "FA": danger["MD_FA"],
                    "GF": danger["MD_GF"], "GA": danger["MD_GA"],
                },
                "LD": {
                    "SF": danger["LD_SF"], "SA": danger["LD_SA"],
                    "CF": danger["LD_CF"], "CA": danger["LD_CA"],
                    "FF": danger["LD_FF"], "FA": danger["LD_FA"],
                    "GF": danger["LD_GF"], "GA": danger["LD_GA"],
                },
            }

            summary["danger"] = {
                "totals": danger,
                "percentages": {
                    "HD_SF%": tier_pct(tier["HD"]["SF"], tier["HD"]["SA"]),
                    "MD_SF%": tier_pct(tier["MD"]["SF"], tier["MD"]["SA"]),
                    "LD_SF%": tier_pct(tier["LD"]["SF"], tier["LD"]["SA"]),
                    "HD_CF%": tier_pct(tier["HD"]["CF"], tier["HD"]["CA"]),
                    "MD_CF%": tier_pct(tier["MD"]["CF"], tier["MD"]["CA"]),
                    "LD_CF%": tier_pct(tier["LD"]["CF"], tier["LD"]["CA"]),
                    "HD_FF%": tier_pct(tier["HD"]["FF"], tier["HD"]["FA"]),
                    "MD_FF%": tier_pct(tier["MD"]["FF"], tier["MD"]["FA"]),
                    "LD_FF%": tier_pct(tier["LD"]["FF"], tier["LD"]["FA"]),
                    "HD_GF%": tier_pct(tier["HD"]["GF"], tier["HD"]["GA"]),
                    "MD_GF%": tier_pct(tier["MD"]["GF"], tier["MD"]["GA"]),
                    "LD_GF%": tier_pct(tier["LD"]["GF"], tier["LD"]["GA"]),
                    # On-ice shooting% by tier
                    "HD_Sh%": safe_div(tier["HD"]["GF"], max(tier["HD"]["SF"], 1.0)),
                    "MD_Sh%": safe_div(tier["MD"]["GF"], max(tier["MD"]["SF"], 1.0)),
                    "LD_Sh%": safe_div(tier["LD"]["GF"], max(tier["LD"]["SF"], 1.0)),
                },
                "per60": {
                    "HD_SF60": safe_div(tier["HD"]["SF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "MD_SF60": safe_div(tier["MD"]["SF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "LD_SF60": safe_div(tier["LD"]["SF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "HD_CF60": safe_div(tier["HD"]["CF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "MD_CF60": safe_div(tier["MD"]["CF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "LD_CF60": safe_div(tier["LD"]["CF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "HD_FF60": safe_div(tier["HD"]["FF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "MD_FF60": safe_div(tier["MD"]["FF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "LD_FF60": safe_div(tier["LD"]["FF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "HD_GF60": safe_div(tier["HD"]["GF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "MD_GF60": safe_div(tier["MD"]["GF"], (toi / 3600.0) if toi > 0 else 0.0),
                    "LD_GF60": safe_div(tier["LD"]["GF"], (toi / 3600.0) if toi > 0 else 0.0),
                },
                "diffs": {
                    "HD_SDiff": tier["HD"]["SF"] - tier["HD"]["SA"],
                    "MD_SDiff": tier["MD"]["SF"] - tier["MD"]["SA"],
                    "LD_SDiff": tier["LD"]["SF"] - tier["LD"]["SA"],
                    "HD_CDiff": tier["HD"]["CF"] - tier["HD"]["CA"],
                    "MD_CDiff": tier["MD"]["CF"] - tier["MD"]["CA"],
                    "LD_CDiff": tier["LD"]["CF"] - tier["LD"]["CA"],
                    "HD_FDiff": tier["HD"]["FF"] - tier["HD"]["FA"],
                    "MD_FDiff": tier["MD"]["FF"] - tier["MD"]["FA"],
                    "LD_FDiff": tier["LD"]["FF"] - tier["LD"]["FA"],
                    "HD_GDiff": tier["HD"]["GF"] - tier["HD"]["GA"],
                    "MD_GDiff": tier["MD"]["GF"] - tier["MD"]["GA"],
                    "LD_GDiff": tier["LD"]["GF"] - tier["LD"]["GA"],
                },
            }

        result = {"player_id": player_id, "summary": summary}

        # Optional persistence to player_game_advanced_metrics
        try:
            if os.environ.get("WRITE_PLAYER_GAME_ADV", "0") in ("1", "true", "True") and game_id is not None:
                # Ensure tables exist (idempotent) only once per process to avoid repeated connector init
                if os.environ.get("PG_ADV_TABLES_CREATED", "0") != "1":
                    try:
                        create_tables()
                        os.environ["PG_ADV_TABLES_CREATED"] = "1"
                    except Exception:
                        pass
                # Enrich metadata
                gm = session.query(Game).filter(Game.id == int(game_id)).first()
                season_val = gm.season if gm else None
                game_type_val = gm.game_type if gm else None
                team_id_val = None
                any_row = (
                    session.query(PlayerShiftMetrics.team_id)
                    .filter(
                        PlayerShiftMetrics.player_id == int(player_id),
                        PlayerShiftMetrics.game_id == int(game_id),
                    )
                    .limit(1)
                    .first()
                )
                if any_row:
                    (team_id_val,) = any_row
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                stmt = pg_insert(PlayerGameAdvancedMetrics.__table__).values({
                    "player_id": int(player_id),
                    "game_id": int(game_id),
                    "team_id": team_id_val,
                    "season": season_val,
                    "game_type": game_type_val,
                    "summary": result["summary"],
                })
                update_cols = {k: stmt.excluded[k] for k in ["team_id", "season", "game_type", "summary"]}
                stmt = stmt.on_conflict_do_update(index_elements=["player_id", "game_id"], set_=update_cols)
                session.execute(stmt)
                session.commit()
        except Exception:
            session.rollback()

        return result
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate advanced metrics for a single player.")
    parser.add_argument("--player-id", type=int, required=True)
    parser.add_argument("--game-id", type=int, default=None, help="Restrict to a single game")
    parser.add_argument("--season", type=int, default=None, help="Restrict by season (e.g., 20242025)")
    parser.add_argument("--game-type", type=int, default=None, help="2=Regular, 3=Playoffs")
    parser.add_argument("--strength", type=str, default=None, choices=["EV", "PP", "SH"], help="Filter by strength state")
    parser.add_argument("--include-danger", action="store_true", help="Compute HD/MD/LD tiers from event coordinates")
    parser.add_argument("--exclude-zero-shifts", action="store_true", help="Ignore all-zero shifts when aggregating (stabilizes OZS% and shift counts)")
    parser.add_argument("--hd-ft", type=float, default=30.0, help="High-danger distance threshold in feet (default 30)")
    parser.add_argument("--md-ft", type=float, default=50.0, help="Mid-danger distance threshold in feet (default 50)")
    args = parser.parse_args()

    # Apply danger thresholds
    global HD_FT, MD_FT
    if args.hd_ft is not None:
        HD_FT = float(args.hd_ft)
    if args.md_ft is not None:
        MD_FT = float(args.md_ft)

    result = aggregate_for_player(
        args.player_id,
        game_id=args.game_id,
        season=args.season,
        game_type=args.game_type,
        strength=args.strength,
        include_danger=args.include_danger,
        exclude_zero_shifts=args.exclude_zero_shifts,
    )
    print(json.dumps(result, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()

