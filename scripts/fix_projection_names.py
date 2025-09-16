#!/usr/bin/env python3
from sqlalchemy import text as sa_text
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.fantasy_connection import get_fantasy_session  # type: ignore


def main():
    names_map = {
        'cole hutson': 'Lane Hutson',
    }
    season = int(os.getenv('SEASON', '2025'))
    total = 0
    with get_fantasy_session() as session:
        for bad_lower, good in names_map.items():
            res = session.execute(sa_text(
                """
                UPDATE fantasy_player_projections
                   SET player_name = :good
                 WHERE season = :season
                   AND LOWER(player_name) = :bad
                """
            ), {"good": good, "season": season, "bad": bad_lower})
            total += res.rowcount or 0
        session.commit()
    print(f"Renamed {total} rows for season {season}")


if __name__ == '__main__':
    main()


