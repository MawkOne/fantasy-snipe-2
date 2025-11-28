import os
import sys
import argparse
from typing import Optional, Tuple
import time

from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import (
    create_tables,
    PlayerShift,
    GameEvent,
    PlayerShiftMetrics,
)
from sqlalchemy import text


def mmss_to_seconds(mmss: Optional[str]) -> Optional[int]:
    if not mmss or ":" not in mmss:
        return None
    try:
        m, s = mmss.split(":")
        return int(m) * 60 + int(s)
    except Exception:
        return None


def guess_zone_start(first_event: Optional[dict]) -> Optional[str]:
    # Rough heuristic: faceoff event with x coordinate → O/D based on sign, else None
    if not first_event or not isinstance(first_event, dict):
        return None
    etype = (
        first_event.get("typeDescKey")
        or (first_event.get("result") or {}).get("event")
        or first_event.get("eventTypeId")
    )
    if etype and "FACEOFF" in str(etype).upper():
        coords = first_event.get("coordinates") or {}
        x = coords.get("x")
        if isinstance(x, (int, float)):
            if x > 0:
                return "O"
            if x < 0:
                return "D"
        return "N"
    return None


def is_for(team_id: Optional[int], event_team_id: Optional[int]) -> Optional[bool]:
    if team_id is None or event_team_id is None:
        return None
    return team_id == event_team_id


def extract_xy_zone_from_raw(ev: dict) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Extract x, y, and zoneCode ('O','D','N') from normalized fields or raw payload variants.
    Supports raw.details.xCoord/yCoord and raw.coordinates.x/y.
    """
    x = ev.get("x")
    y = ev.get("y")
    raw = ev.get("raw") or {}
    zone_code: Optional[str] = None
    if isinstance(raw, dict):
        det = raw.get("details") or {}
        if isinstance(det, dict):
            if x is None:
                x = det.get("xCoord", det.get("xcoord", det.get("x", x)))
            if y is None:
                y = det.get("yCoord", det.get("ycoord", det.get("y", y)))
            zc = det.get("zoneCode")
            if isinstance(zc, str) and zc:
                zone_code = zc.upper()[0]
        if x is None or y is None:
            coords = raw.get("coordinates") or {}
            if isinstance(coords, dict):
                if x is None:
                    x = coords.get("x", x)
                if y is None:
                    y = coords.get("y", y)
    return x, y, zone_code


def zone_for_my_team(event_zone_code: Optional[str], event_team_id: Optional[int], my_team_id: Optional[int], x_coord: Optional[float]) -> Optional[str]:
    """Resolve zone start from the event's zone (relative to event team) to the shift player's team perspective.
    If explicit zoneCode provided, flip relative to team if needed; else infer from x coordinate.
    """
    z = (event_zone_code or "").upper()[:1]
    if z in ("O", "D", "N"):
        if z == "N":
            return "N"
        if event_team_id is None or my_team_id is None:
            return None
        return z if event_team_id == my_team_id else ("D" if z == "O" else "O")
    # Fallback to x threshold
    if isinstance(x_coord, (int, float)):
        z_ev = "O" if x_coord > 25 else ("D" if x_coord < -25 else "N")
        if z_ev == "N" or event_team_id is None or my_team_id is None:
            return z_ev
        return z_ev if event_team_id == my_team_id else ("D" if z_ev == "O" else "O")
    return None


def classify_event(ev: dict) -> Tuple[Optional[str], Optional[bool]]:
    # Normalize a variety of event type spellings into canonical buckets
    raw = (
        ev.get("typeDescKey")
        or (ev.get("result") or {}).get("event")
        or ev.get("eventTypeId")
        or ""
    )
    et = str(raw).strip().lower().replace(" ", "-").replace("_", "-")

    # Distinguish clearly between shot-on-goal vs. goal; order matters
    if "missed-shot" in et or et == "miss":
        return ("miss", None)
    if "blocked-shot" in et or et == "block":
        return ("block", None)
    if "shot-on-goal" in et or et == "shot":
        return ("shot", None)
    # Treat only true goals as goals; exclude shot-on-goal above
    if et == "goal" or et.endswith("-goal"):
        return ("goal", None)

    if "hit" in et:
        return ("hit", None)
    if "takeaway" in et:
        return ("takeaway", None)
    if "giveaway" in et:
        return ("giveaway", None)
    if "faceoff" in et:
        return ("faceoff", None)
    return (None, None)


def compute_shift_metrics(
    season: Optional[int] = None,
    game_type: Optional[int] = None,
    batch_commit: int = 500,
    game_id: Optional[int] = None,
    limit: Optional[int] = None,
    shift_chunk: int = 1000,
    player_chunk: int = 100,
    player_id: Optional[int] = None,
    force_recompute: bool = False,
    recompute_zeros_only: bool = False,
    allow_zero_writes: bool = False,
) -> None:
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    try:
        create_tables()
    except Exception:
        pass

    try:
        print("Ensuring helpful indexes (no-op if already exist)...")
        # Safe to run repeatedly; IF NOT EXISTS avoids errors
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_game_events_game_id ON game_events (game_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_game_events_game_id_period ON game_events (game_id, period)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_player_shifts_game_id ON player_shifts (game_id)"))
        session.commit()

        # Determine which game_ids to process
        if game_id is not None:
            game_ids = [int(game_id)]
        else:
            # Optionally filter by season and game_type using the games table
            from src.database.models import Game as _Game
            q = session.query(PlayerShift.game_id).distinct()
            if season is not None:
                q = q.join(_Game, _Game.id == PlayerShift.game_id).filter(_Game.season == int(season))
            if game_type is not None:
                # Ensure we join Games if not already
                if season is None:
                    q = q.join(_Game, _Game.id == PlayerShift.game_id)
                q = q.filter(_Game.game_type == int(game_type))
            game_ids = [gid for (gid,) in q.all()]

        processed = 0
        committed = 0
        start_time = time.time()

        for current_gid in game_ids:
            print(f"\n=== Processing game {current_gid} ===")

            # Prefetch existing metrics for this game (keys always; optionally with zero-status)
            existing_metric_keys = set()
            existing_zero_map = {}
            if recompute_zeros_only and not force_recompute:
                rows = (
                    session.query(
                        PlayerShiftMetrics.player_id,
                        PlayerShiftMetrics.game_id,
                        PlayerShiftMetrics.shift_number,
                        PlayerShiftMetrics.attempts_for,
                        PlayerShiftMetrics.attempts_against,
                        PlayerShiftMetrics.unblocked_for,
                        PlayerShiftMetrics.unblocked_against,
                        PlayerShiftMetrics.shots_for,
                        PlayerShiftMetrics.shots_against,
                        PlayerShiftMetrics.goals_for,
                        PlayerShiftMetrics.goals_against,
                        PlayerShiftMetrics.hits_for,
                        PlayerShiftMetrics.hits_against,
                        PlayerShiftMetrics.takeaways_for,
                        PlayerShiftMetrics.takeaways_against,
                        PlayerShiftMetrics.giveaways_for,
                        PlayerShiftMetrics.giveaways_against,
                        PlayerShiftMetrics.blocks_for,
                        PlayerShiftMetrics.blocks_against,
                        PlayerShiftMetrics.zone_start,
                        PlayerShiftMetrics.faceoff_won,
                        PlayerShiftMetrics.strength_state,
                    ).filter(PlayerShiftMetrics.game_id == current_gid)
                )
                for r in rows.all():
                    key = (r.player_id, r.game_id, r.shift_number)
                    existing_metric_keys.add(key)
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
                    # Consider zeroish if all event counters are zero, regardless of zone/strength being set
                    is_zeroish = counters_sum == 0
                    existing_zero_map[key] = is_zeroish
            else:
                existing_metric_keys = set(
                    session.query(
                        PlayerShiftMetrics.player_id,
                        PlayerShiftMetrics.game_id,
                        PlayerShiftMetrics.shift_number,
                    ).filter(PlayerShiftMetrics.game_id == current_gid).all()
                )

            print("Preparing lazy event loader (per-game)...")
            # Per-game cache, cleared on each new game to bound memory
            events_by_game_cache: dict[int, list] = {}

            def load_events_for_game(gid: int) -> list:
                if gid in events_by_game_cache:
                    return events_by_game_cache[gid]
                q = (
                    session.query(
                        GameEvent.game_id,
                        GameEvent.period,
                        GameEvent.period_time,
                        GameEvent.team_id,
                        GameEvent.event_type,
                        GameEvent.coordinates_x,
                        GameEvent.coordinates_y,
                        GameEvent.event_idx,
                        GameEvent.raw,
                    )
                    .filter(GameEvent.game_id == gid)
                )
                rows_local = q.all()
                evs = []
                for row in rows_local:
                    evs.append(
                        {
                            "game_id": row.game_id,
                            "period": row.period,
                            "period_time": row.period_time,
                            "team_id": row.team_id,
                            "event_type": row.event_type,
                            "x": row.coordinates_x,
                            "y": row.coordinates_y,
                            "event_idx": row.event_idx,
                            "raw": row.raw,
                        }
                    )
                # Deduplicate per game
                seen = set()
                deduped = []
                for ev in evs:
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
                events_by_game_cache[gid] = deduped
                print(f"Loaded {len(deduped)} events for game {gid}.")
                return deduped

            # Preload all shifts within this game for on-ice estimation
            preloaded_shifts_by_period = None
            all_shifts = (
                session.query(
                    PlayerShift.period,
                    PlayerShift.team_id,
                    PlayerShift.player_id,
                    PlayerShift.start_time,
                    PlayerShift.end_time,
                )
                .filter(PlayerShift.game_id == current_gid)
                .all()
            )
            preloaded_shifts_by_period = {}
            for row in all_shifts:
                try:
                    s_sec = mmss_to_seconds(row.start_time)
                    e_sec = mmss_to_seconds(row.end_time)
                except Exception:
                    s_sec = None
                    e_sec = None
                preloaded_shifts_by_period.setdefault(row.period, []).append(
                    {"team_id": row.team_id, "player_id": row.player_id, "start_s": s_sec, "end_s": e_sec}
                )

            # Build base shift query scoped to this game
            base_query = session.query(PlayerShift).filter(PlayerShift.game_id == current_gid)

            # Build player list for this game (optionally restricted to a single player)
            if player_id is not None:
                player_ids = [int(player_id)]
            else:
                player_ids = [pid for (pid,) in base_query.with_entities(PlayerShift.player_id).distinct().all()]

            print(f"Processing players in chunks for game {current_gid} (total={len(player_ids)})...")
            to_upsert = []
            in_batch_keys = set()

            for i in range(0, len(player_ids), max(1, int(player_chunk))):
                batch_player_ids = player_ids[i:i + max(1, int(player_chunk))]
                for pid in batch_player_ids:
                    last_id = 0
                    while True:
                        q = base_query.filter(PlayerShift.player_id == pid, PlayerShift.id > last_id).order_by(PlayerShift.id).limit(shift_chunk)
                        batch = q.all()
                        if not batch:
                            break
                        last_id = batch[-1].id
                        if limit is not None and isinstance(limit, int) and limit > 0:
                            remaining = limit - processed
                            if remaining <= 0:
                                break
                            if len(batch) > remaining:
                                batch = batch[:remaining]

                        for shift in batch:
                            # Skip if we already computed metrics for this shift (scoped to current game), unless forcing recompute
                            shift_key = (shift.player_id, shift.game_id, shift.shift_number)
                            if not force_recompute and (shift_key in existing_metric_keys or shift_key in in_batch_keys):
                                # If zeros-only mode, allow recompute for zeroish rows
                                if recompute_zeros_only and existing_zero_map.get(shift_key) is True:
                                    pass
                                else:
                                    processed += 1
                                    if processed % 1000 == 0:
                                        elapsed = time.time() - start_time
                                        print(f"Processed {processed} shifts (skipped existing), elapsed {elapsed:.1f}s...")
                                    continue
                            # Lazy-load events for this game only when needed
                            game_events = load_events_for_game(shift.game_id)
                            if not game_events:
                                processed += 1
                                if processed % 1000 == 0:
                                    elapsed = time.time() - start_time
                                    print(f"Processed {processed} shifts (no events), elapsed {elapsed:.1f}s...")
                                continue

                            start_s = mmss_to_seconds(shift.start_time)
                            end_s = mmss_to_seconds(shift.end_time)
                            if start_s is None or end_s is None:
                                processed += 1
                                continue

                            # Filter events that occur within the shift period/time window
                            def ev_time_seconds(ev: dict) -> Optional[int]:
                                return mmss_to_seconds(ev["period_time"])

                            # Allow a small +/- 1s tolerance around shift bounds to account for feed rounding
                            start_bound = max(0, (start_s or 0) - 1)
                            end_bound = (end_s or 0) + 1
                            window_events = [
                                ev for ev in game_events
                                if (
                                    ev["period"] == shift.period
                                    and ev_time_seconds(ev) is not None
                                    and start_bound <= ev_time_seconds(ev) <= end_bound
                                )
                            ]

                            # Sort by time within period
                            window_events.sort(key=lambda e: mmss_to_seconds(e["period_time"]) or -1)

                            # De-duplicate within the window to avoid double counting
                            seen_window = set()
                            dedup_window = []
                            for ev in window_events:
                                wkey = ev.get("event_idx")
                                if wkey is None:
                                    wkey = (
                                        ev.get("period"),
                                        ev.get("period_time"),
                                        (ev.get("event_type") or "").upper(),
                                        ev.get("team_id"),
                                    )
                                if wkey in seen_window:
                                    continue
                                seen_window.add(wkey)
                                dedup_window.append(ev)
                            window_events = dedup_window

                            # Initialize counters
                            attempts_for = attempts_against = 0
                            unblocked_for = unblocked_against = 0
                            shots_for = shots_against = 0
                            goals_for = goals_against = 0
                            hits_for = hits_against = 0
                            takeaways_for = takeaways_against = 0
                            giveaways_for = giveaways_against = 0
                            blocks_for = blocks_against = 0

                            zone_start = None
                            faceoff_won = None
                            strength_state: Optional[str] = None
                            teammates_on_ice: Optional[int] = None
                            opponents_on_ice: Optional[int] = None
                            # Ensure IDs are always defined even if we skip estimation
                            teammates_on_ice_ids = None
                            opponents_on_ice_ids = None

                            # Determine team perspective
                            my_team_id = shift.team_id

                            # First relevant event (e.g., faceoff) for zone start
                            first_ev = window_events[0] if window_events else None
                            if first_ev:
                                etype_u = str(first_ev.get("event_type") or "").upper()
                                if "FACEOFF" in etype_u:
                                    x0, y0, z0 = extract_xy_zone_from_raw(first_ev)
                                    zone_start = zone_for_my_team(z0, first_ev.get("team_id"), my_team_id, x0) or "N"
                                    faceoff_won = True if first_ev.get("team_id") == my_team_id else False
                                else:
                                    zone_start = None
                            # Fallback: nearest faceoff within ±3 seconds of shift start
                            if zone_start is None or faceoff_won is None:
                                try:
                                    nearest_faceoffs = []
                                    for ev in game_events:
                                        if ev.get("period") != shift.period:
                                            continue
                                        tsec = ev_time_seconds(ev)
                                        if tsec is None or start_s is None:
                                            continue
                                        if abs(tsec - start_s) <= 3 and "FACEOFF" in str(ev.get("event_type") or "").upper():
                                            nearest_faceoffs.append((abs(tsec - start_s), ev))
                                    if nearest_faceoffs:
                                        nearest_faceoffs.sort(key=lambda x: x[0])
                                        _, fev = nearest_faceoffs[0]
                                        x1, y1, z1 = extract_xy_zone_from_raw(fev)
                                        zone_start = zone_for_my_team(z1, fev.get("team_id"), my_team_id, x1) or "N"
                                        faceoff_won = True if fev.get("team_id") == my_team_id else False
                                except Exception:
                                    pass

                            for ev in window_events:
                                # Normalize event type classification
                                ev_type, _ = classify_event({
                                    "typeDescKey": ev.get("event_type"),
                                    "eventTypeId": ev.get("event_type"),
                                    "result": {"event": ev.get("event_type")},
                                })
                                side = is_for(my_team_id, ev.get("team_id"))
                                if ev_type in ("shot", "miss", "block", "goal"):
                                    if side is True:
                                        attempts_for += 1
                                    elif side is False:
                                        attempts_against += 1
                                if ev_type in ("shot", "goal"):
                                    if side is True:
                                        shots_for += 1
                                    elif side is False:
                                        shots_against += 1
                                if ev_type == "goal":
                                    if side is True:
                                        goals_for += 1
                                    elif side is False:
                                        goals_against += 1
                                if ev_type == "miss":
                                    if side is True:
                                        unblocked_for += 1
                                    elif side is False:
                                        unblocked_against += 1
                                if ev_type == "block":
                                    if side is True:
                                        blocks_for += 1
                                    elif side is False:
                                        blocks_against += 1
                                if ev_type == "hit":
                                    if side is True:
                                        hits_for += 1
                                    elif side is False:
                                        hits_against += 1
                                if ev_type == "takeaway":
                                    if side is True:
                                        takeaways_for += 1
                                    elif side is False:
                                        takeaways_against += 1
                                if ev_type == "giveaway":
                                    if side is True:
                                        giveaways_for += 1
                                    elif side is False:
                                        giveaways_against += 1

                            # Estimate on-ice counts at shift start from PlayerShift overlaps within same period
                            try:
                                if preloaded_shifts_by_period is not None:
                                    starts = preloaded_shifts_by_period.get(shift.period, [])
                                    tm_ids = set()
                                    opp_ids = set()
                                    for r in starts:
                                        rs = r.get("start_s")
                                        re = r.get("end_s")
                                        if rs is None or re is None or start_s is None:
                                            continue
                                        if rs <= start_s < re:
                                            if r["team_id"] == shift.team_id:
                                                tm_ids.add(r["player_id"])
                                            else:
                                                opp_ids.add(r["player_id"])
                                    teammates_on_ice = len(tm_ids) if tm_ids else None
                                    opponents_on_ice = len(opp_ids) if opp_ids else None
                                    if teammates_on_ice is not None and opponents_on_ice is not None:
                                        if teammates_on_ice > opponents_on_ice:
                                            strength_state = "PP"
                                        elif teammates_on_ice < opponents_on_ice:
                                            strength_state = "SH"
                                        else:
                                            strength_state = "EV"
                                    teammates_on_ice_ids = sorted(tm_ids) if tm_ids else None
                                    opponents_on_ice_ids = sorted(opp_ids) if opp_ids else None
                            except Exception:
                                teammates_on_ice_ids = None
                                opponents_on_ice_ids = None

                            # Guard: optionally skip writing all-zero rows; when allow_zero_writes is True,
                            # we persist zero-baseline rows to fully backfill the table.
                            counters_sum = (
                                attempts_for + attempts_against + unblocked_for + unblocked_against +
                                shots_for + shots_against + goals_for + goals_against +
                                hits_for + hits_against + takeaways_for + takeaways_against +
                                giveaways_for + giveaways_against + blocks_for + blocks_against
                            )
                            if counters_sum == 0 and not allow_zero_writes:
                                processed += 1
                                continue

                            metrics = PlayerShiftMetrics(
                                player_id=shift.player_id,
                                game_id=shift.game_id,
                                team_id=shift.team_id,
                                shift_number=shift.shift_number,
                                period=shift.period,
                                start_time=shift.start_time,
                                end_time=shift.end_time,
                                duration=shift.duration,
                                attempts_for=attempts_for,
                                attempts_against=attempts_against,
                                unblocked_for=unblocked_for,
                                unblocked_against=unblocked_against,
                                shots_for=shots_for,
                                shots_against=shots_against,
                                goals_for=goals_for,
                                goals_against=goals_against,
                                hits_for=hits_for,
                                hits_against=hits_against,
                                takeaways_for=takeaways_for,
                                takeaways_against=takeaways_against,
                                giveaways_for=giveaways_for,
                                giveaways_against=giveaways_against,
                                blocks_for=blocks_for,
                                blocks_against=blocks_against,
                                zone_start=zone_start,
                                faceoff_won=faceoff_won,
                                strength_state=strength_state,
                                teammates_on_ice=teammates_on_ice,
                                opponents_on_ice=opponents_on_ice,
                                teammates_on_ice_ids=teammates_on_ice_ids,
                                opponents_on_ice_ids=opponents_on_ice_ids,
                            )
                            to_upsert.append(metrics)
                            in_batch_keys.add(shift_key)

                        if len(to_upsert) >= batch_commit:
                            # Deduplicate rows within the batch by (player_id, game_id, shift_number)
                            dedup = {}
                            for m in to_upsert:
                                key = (m.player_id, m.game_id, m.shift_number)
                                dedup[key] = {
                                    "player_id": m.player_id,
                                    "game_id": m.game_id,
                                    "team_id": m.team_id,
                                    "shift_number": m.shift_number,
                                    "period": m.period,
                                    "start_time": m.start_time,
                                    "end_time": m.end_time,
                                    "duration": m.duration,
                                    "attempts_for": m.attempts_for,
                                    "attempts_against": m.attempts_against,
                                    "unblocked_for": m.unblocked_for,
                                    "unblocked_against": m.unblocked_against,
                                    "shots_for": m.shots_for,
                                    "shots_against": m.shots_against,
                                    "goals_for": m.goals_for,
                                    "goals_against": m.goals_against,
                                    "hits_for": m.hits_for,
                                    "hits_against": m.hits_against,
                                    "takeaways_for": m.takeaways_for,
                                    "takeaways_against": m.takeaways_against,
                                    "giveaways_for": m.giveaways_for,
                                    "giveaways_against": m.giveaways_against,
                                    "blocks_for": m.blocks_for,
                                    "blocks_against": m.blocks_against,
                                    "zone_start": m.zone_start,
                                    "faceoff_won": m.faceoff_won,
                                    "strength_state": m.strength_state,
                                    "teammates_on_ice": m.teammates_on_ice,
                                    "opponents_on_ice": m.opponents_on_ice,
                                    "teammates_on_ice_ids": m.teammates_on_ice_ids,
                                    "opponents_on_ice_ids": m.opponents_on_ice_ids,
                                }
                            rows = list(dedup.values())
                            stmt = pg_insert(PlayerShiftMetrics.__table__).values(rows)
                            update_cols = {k: stmt.excluded[k] for k in rows[0].keys() if k not in ("player_id", "game_id", "shift_number")}
                            stmt = stmt.on_conflict_do_update(
                                index_elements=["player_id", "game_id", "shift_number"],
                                set_=update_cols,
                            )
                            session.execute(stmt)
                            session.commit()
                            committed += len(to_upsert)
                            to_upsert.clear()
                            # Extend existing keys with the ones we just wrote, clear in-batch set
                            existing_metric_keys.update(in_batch_keys)
                            in_batch_keys.clear()
                            if committed % (batch_commit * 10) == 0:
                                elapsed = time.time() - start_time
                                print(f"Committed {committed} rows so far, elapsed {elapsed:.1f}s...")

                        processed += 1
                        if processed % 1000 == 0:
                            elapsed = time.time() - start_time
                            print(f"Processed {processed} shifts, committed {committed}, elapsed {elapsed:.1f}s...")
        # end while chunks

        if to_upsert:
            # Upsert to avoid duplicates on re-runs
            dedup = {}
            for m in to_upsert:
                key = (m.player_id, m.game_id, m.shift_number)
                dedup[key] = {
                    "player_id": m.player_id,
                    "game_id": m.game_id,
                    "team_id": m.team_id,
                    "shift_number": m.shift_number,
                    "period": m.period,
                    "start_time": m.start_time,
                    "end_time": m.end_time,
                    "duration": m.duration,
                    "attempts_for": m.attempts_for,
                    "attempts_against": m.attempts_against,
                    "unblocked_for": m.unblocked_for,
                    "unblocked_against": m.unblocked_against,
                    "shots_for": m.shots_for,
                    "shots_against": m.shots_against,
                    "goals_for": m.goals_for,
                    "goals_against": m.goals_against,
                    "hits_for": m.hits_for,
                    "hits_against": m.hits_against,
                    "takeaways_for": m.takeaways_for,
                    "takeaways_against": m.takeaways_against,
                    "giveaways_for": m.giveaways_for,
                    "giveaways_against": m.giveaways_against,
                    "blocks_for": m.blocks_for,
                    "blocks_against": m.blocks_against,
                    "zone_start": m.zone_start,
                    "faceoff_won": m.faceoff_won,
                    "strength_state": m.strength_state,
                    "teammates_on_ice": m.teammates_on_ice,
                    "opponents_on_ice": m.opponents_on_ice,
                    "teammates_on_ice_ids": m.teammates_on_ice_ids,
                    "opponents_on_ice_ids": m.opponents_on_ice_ids,
                }
            rows = list(dedup.values())
            stmt = pg_insert(PlayerShiftMetrics.__table__).values(rows)
            update_cols = {k: stmt.excluded[k] for k in rows[0].keys() if k not in ("player_id", "game_id", "shift_number")}
            stmt = stmt.on_conflict_do_update(
                index_elements=["player_id", "game_id", "shift_number"],
                set_=update_cols,
            )
            session.execute(stmt)
            session.commit()
            committed += len(to_upsert)
            existing_metric_keys.update(in_batch_keys)
            in_batch_keys.clear()

        elapsed = time.time() - start_time
        print(f"Finished computing shift metrics. Processed {processed} shifts, committed {committed} rows in {elapsed:.1f}s.")

    except Exception as e:
        print(f"A critical error occurred: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute per-shift metrics by combining player_shifts and game_events.")
    parser.add_argument("--season", type=int, default=None, help="Season ID like 20182019 to filter games")
    parser.add_argument("--game-type", type=int, default=None, help="Game type (2=Regular, 3=Playoffs)")
    parser.add_argument("--game-id", type=int, default=None, help="Restrict computation to a single game_id")
    parser.add_argument("--player-id", type=int, default=None, help="Restrict computation to a single player_id")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of shifts processed (for testing)")
    parser.add_argument("--batch-commit", type=int, default=500, help="Batch size for inserts/commits")
    parser.add_argument("--shift-chunk", type=int, default=1000, help="Number of player_shifts to load/process per chunk")
    parser.add_argument("--player-chunk", type=int, default=100, help="Number of players to process per outer chunk")
    parser.add_argument("--force", action="store_true", help="Force recompute and overwrite existing shift metrics")
    parser.add_argument("--recompute-zeros-only", action="store_true", help="Only recompute existing shifts that are all zeros/no-info")
    parser.add_argument("--allow-zero-writes", action="store_true", help="Allow inserting/updating rows even when all counters are zero")
    args = parser.parse_args()
    compute_shift_metrics(
        season=args.season,
        game_type=args.game_type,
        batch_commit=args.batch_commit,
        game_id=args.game_id,
        limit=args.limit,
        shift_chunk=args.shift_chunk,
        player_chunk=args.player_chunk,
        player_id=args.player_id,
        force_recompute=args.force,
        recompute_zeros_only=args.recompute_zeros_only,
        allow_zero_writes=args.allow_zero_writes,
    )

