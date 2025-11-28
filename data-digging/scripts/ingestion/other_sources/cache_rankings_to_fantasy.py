#!/usr/bin/env python3
"""
Cache NHL season rankings from Google Cloud SQL (NHL DB) into the Fantasy (Railway) DB.

Usage:
  python scripts/cache_rankings_to_fantasy.py --season 2024 --limit 300

Env:
  - DATABASE_URL (Fantasy DB; Railway): required
  - (Optional) Cloud SQL via connector from src.database.connection
    or set NHL_DATABASE_URL for direct connection
"""

import os
import sys
import logging
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.database.connection import connect_with_connector
from src.database.models import (
    Player as NHLPlayer,
    Team as NHLTeam,
    Game as NHLGame,
    PlayerGameStats as NHLPlayerGameStats,
)
from src.database.fantasy_models_v2 import Base as FantasyBase
from src.database.fantasy_models_v2 import FantasySeasonRanking

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_nhl_engine():
    # Load environment from .env in project root
    load_dotenv()
    nhl_url = os.getenv("NHL_DATABASE_URL")
    if nhl_url:
        return create_engine(nhl_url, pool_pre_ping=True)
    return connect_with_connector()


def get_fantasy_engine():
    # Load environment from .env in project root
    load_dotenv()
    fantasy_url = os.getenv("DATABASE_URL")
    if not fantasy_url:
        raise RuntimeError("DATABASE_URL (fantasy DB) is required")
    return create_engine(fantasy_url, pool_pre_ping=True)


def fetch_rankings(nhl_session, season_nhl: int, limit: int) -> List[Dict]:
    # Aggregate per player across all teams (players may change teams mid-season)
    query = (
        nhl_session.query(
            NHLPlayer.id.label("player_id"),
            NHLPlayer.full_name.label("name"),
            NHLPlayer.position_code.label("position"),
            func.max(NHLTeam.raw_tricode).label("team"),
            func.count(NHLPlayerGameStats.id).label("gp"),
            func.sum(NHLPlayerGameStats.goals).label("goals"),
            func.sum(NHLPlayerGameStats.assists).label("assists"),
            func.sum(NHLPlayerGameStats.points).label("points"),
            func.sum(NHLPlayerGameStats.shots).label("shots"),
            func.sum(NHLPlayerGameStats.pim).label("pim"),
            func.sum(NHLPlayerGameStats.plus_minus).label("plus_minus"),
        )
        .join(NHLGame, NHLGame.id == NHLPlayerGameStats.game_id)
        .join(NHLPlayer, NHLPlayer.id == NHLPlayerGameStats.player_id)
        .join(NHLTeam, NHLTeam.id == NHLPlayerGameStats.team_id)
        .filter(NHLGame.season == season_nhl, NHLGame.game_type == 2)
        .group_by(
            NHLPlayer.id,
            NHLPlayer.full_name,
            NHLPlayer.position_code,
        )
        .order_by(
            func.sum(NHLPlayerGameStats.points).desc(),
            func.sum(NHLPlayerGameStats.goals).desc(),
            func.sum(NHLPlayerGameStats.shots).desc(),
        )
        .limit(limit)
    )

    rows = query.all()
    results = []
    rank = 1
    for r in rows:
        results.append(
            {
                "rank": rank,
                "nhl_player_id": int(r.player_id),
                "player_name": r.name,
                "team": r.team,
                "position": r.position,
                "gp": int(r.gp or 0),
                "goals": int(r.goals or 0),
                "assists": int(r.assists or 0),
                "points": int(r.points or 0),
                "shots": int(r.shots or 0),
                "pim": int(r.pim or 0),
                "plus_minus": int(r.plus_minus or 0),
            }
        )
        rank += 1
    return results


def upsert_rankings(fantasy_session, season: int, rankings: List[Dict]):
    # Clear existing season rankings, then bulk insert
    fantasy_session.query(FantasySeasonRanking).filter(FantasySeasonRanking.season == season).delete()
    to_insert = []
    for r in rankings:
        row = FantasySeasonRanking(
            season=season,
            nhl_player_id=r["nhl_player_id"],
            player_name=r["player_name"],
            position=r["position"],
            team=r["team"],
            gp=r["gp"],
            goals=r["goals"],
            assists=r["assists"],
            points=r["points"],
            shots=r["shots"],
            pim=r["pim"],
            plus_minus=r["plus_minus"],
            rank=r["rank"],
        )
        to_insert.append(row)
    fantasy_session.bulk_save_objects(to_insert)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cache NHL season rankings to Fantasy DB")
    parser.add_argument("--season", type=int, default=2024, help="Canonical season year to store (e.g., 2024)")
    parser.add_argument("--nhl_season", type=int, default=None, help="NHL season code to query (e.g., 20242025)")
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()

    nhl_engine = get_nhl_engine()
    fantasy_engine = get_fantasy_engine()

    NHLSession = sessionmaker(bind=nhl_engine, autocommit=False, autoflush=False)
    FantasySession = sessionmaker(bind=fantasy_engine, autocommit=False, autoflush=False)

    # Ensure table exists in fantasy DB
    FantasyBase.metadata.create_all(bind=fantasy_engine, tables=[FantasySeasonRanking.__table__])

    with NHLSession() as nhl_sess, FantasySession() as fan_sess:
        # Determine NHL season code to query
        nhl_season = args.nhl_season
        if nhl_season is None:
            # If user passed a code like 20242025 as --season, use it. Otherwise derive code as YYYYYYYY+1
            if args.season and args.season >= 20000000:
                nhl_season = args.season
            else:
                nhl_season = int(f"{args.season}{args.season + 1}")

        logger.info(f"Fetching rankings from NHL season {nhl_season} to store as season {args.season}...")
        rankings = fetch_rankings(nhl_sess, nhl_season, args.limit)
        logger.info(f"Fetched {len(rankings)} rows. Writing to Fantasy DB...")
        upsert_rankings(fan_sess, args.season, rankings)
        fan_sess.commit()
        logger.info("Rankings cached successfully.")


if __name__ == "__main__":
    main()


