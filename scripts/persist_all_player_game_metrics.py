#!/usr/bin/env python3
import os
import sys
import argparse
from typing import List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker

from src.database.connection import connect_with_connector
from src.database.models import PlayerShiftMetrics
from scripts.player_metrics_report import aggregate_for_player


def get_distinct_player_games(session) -> List[Tuple[int, int]]:
    rows = (
        session.query(PlayerShiftMetrics.player_id, PlayerShiftMetrics.game_id)
        .distinct()
        .all()
    )
    return [(int(p), int(g)) for (p, g) in rows]


def main(include_danger: bool, exclude_zero_shifts: bool) -> None:
    # Ensure writer is enabled
    os.environ["WRITE_PLAYER_GAME_ADV"] = "1"

    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        pairs = get_distinct_player_games(session)
        print(f"Found {len(pairs)} (player, game) pairs to persist.")
    finally:
        session.close()

    processed = 0
    for player_id, game_id in pairs:
        try:
            # Avoid repeated connector initialization inside per-row call by letting the called function reuse a cached engine
            aggregate_for_player(
                player_id,
                game_id=game_id,
                include_danger=include_danger,
                exclude_zero_shifts=exclude_zero_shifts,
            )
            processed += 1
            if processed % 100 == 0:
                print(f"Persisted {processed}/{len(pairs)}...")
        except Exception as e:
            print(f"Failed to persist for player {player_id}, game {game_id}: {e}")

    print(f"Done. Persisted {processed} records.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-danger", action="store_true", help="Compute and persist HD/MD/LD tiers as part of summary")
    ap.add_argument("--exclude-zero-shifts", action="store_true", help="Ignore all-zero shifts when aggregating")
    args = ap.parse_args()
    main(include_danger=args.include_danger, exclude_zero_shifts=args.exclude_zero_shifts)

