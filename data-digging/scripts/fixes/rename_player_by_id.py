#!/usr/bin/env python3
from sqlalchemy import text as sa_text
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.fantasy_connection import get_fantasy_session  # type: ignore


def main():
    target_id = int(os.getenv('PLAYER_ID', '8483457'))
    new_name = os.getenv('PLAYER_NAME', 'Lane Hutson')
    total = 0
    with get_fantasy_session() as session:
        res = session.execute(sa_text(
            """
            UPDATE fantasy_player_projections
               SET player_name = :new_name
             WHERE nhl_player_id = :pid
            """
        ), {"new_name": new_name, "pid": target_id})
        total += res.rowcount or 0
        session.commit()
    print(f"Renamed {total} rows for nhl_player_id={target_id} -> {new_name}")


if __name__ == '__main__':
    main()


