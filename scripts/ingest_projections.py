#!/usr/bin/env python3
"""
Ingest player projections from JSON files into fantasy database.

Schema: fantasy_player_projections
  - id SERIAL PK
  - season INT NOT NULL
  - source TEXT NOT NULL
  - kind TEXT NULL  -- 'skaters' | 'goalies' | NULL
  - nhl_player_id INT NOT NULL
  - player_name TEXT
  - position TEXT
  - team TEXT
  - metrics JSONB NOT NULL
  - created_at TIMESTAMPTZ DEFAULT now()
  - updated_at TIMESTAMPTZ DEFAULT now()
  - UNIQUE (season, source, nhl_player_id)

Usage:
  python scripts/ingest_projections.py --season 2025 /abs/path/file1 /abs/path/file2 ...
"""
import argparse
import json
import os
from typing import Any, Dict, List

from sqlalchemy import text as sa_text

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.fantasy_connection import get_fantasy_session  # type: ignore


CREATE_TABLE_SQL = sa_text(
    """
    CREATE TABLE IF NOT EXISTS fantasy_player_projections (
      id SERIAL PRIMARY KEY,
      season INT NOT NULL,
      source TEXT NOT NULL,
      kind TEXT NULL,
      nhl_player_id INT NOT NULL,
      player_name TEXT,
      position TEXT,
      team TEXT,
      metrics JSONB NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now(),
      UNIQUE (season, source, nhl_player_id)
    );
    """
)

UPSERT_SQL = sa_text(
    """
    INSERT INTO fantasy_player_projections
      (season, source, kind, nhl_player_id, player_name, position, team, metrics)
    VALUES
      (:season, :source, :kind, :nhl_player_id, :player_name, :position, :team, CAST(:metrics AS JSONB))
    ON CONFLICT (season, source, nhl_player_id)
    DO UPDATE SET
      player_name = EXCLUDED.player_name,
      position = EXCLUDED.position,
      team = EXCLUDED.team,
      metrics = EXCLUDED.metrics,
      kind = EXCLUDED.kind,
      updated_at = now();
    """
)


def detect_kind(path: str) -> str | None:
    low = path.lower()
    if "goalie" in low or "goalies" in low:
        return "goalies"
    if "skater" in low or "skaters" in low:
        return "skaters"
    return None


def detect_source(path: str) -> str:
    base = os.path.basename(path)
    name = base.replace(".json", "").strip()
    # Trim obvious tokens
    name = name.replace("2025_", "").replace("_2025", "")
    return name


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    nhl_player_id = raw.get("player_id") or raw.get("nhl_player_id")
    try:
        nhl_player_id = int(nhl_player_id)
    except Exception:
        nhl_player_id = None
    player_name = (
        raw.get("Player_Name")
        or raw.get("player")
        or raw.get("name")
        or raw.get("Goalie")
        or None
    )
    position = raw.get("Position") or raw.get("pos") or None
    team = raw.get("Team_Abbreviation") or raw.get("team") or None

    # Build metrics by excluding identity fields (case-insensitive)
    exclude_keys = {
        "player_id", "nhl_player_id", "Player_Name", "player", "name", "Goalie",
        "Position", "pos", "Team_Abbreviation", "team",
    }
    metrics: Dict[str, Any] = {}
    for k, v in raw.items():
        if k in exclude_keys:
            continue
        metrics[k] = v

    return {
        "nhl_player_id": nhl_player_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "metrics": metrics,
    }


def ingest_file(session, season: int, path: str) -> int:
    if not os.path.exists(path):
        print(f"WARN: file not found: {path}")
        return 0
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"WARN: file not a JSON array: {path}")
        return 0
    source = detect_source(path)
    kind = detect_kind(path)
    inserted = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        row = normalize_record(item)
        if not row["nhl_player_id"]:
            continue
        session.execute(
            UPSERT_SQL,
            {
                "season": season,
                "source": source,
                "kind": kind,
                "nhl_player_id": row["nhl_player_id"],
                "player_name": row.get("player_name"),
                "position": row.get("position"),
                "team": row.get("team"),
                "metrics": json.dumps(row.get("metrics") or {}),
            },
        )
        inserted += 1
    return inserted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="JSON files to ingest")
    parser.add_argument("--season", type=int, default=2025)
    args = parser.parse_args()

    total = 0
    with get_fantasy_session() as session:
        session.execute(CREATE_TABLE_SQL)
        for p in args.paths:
            count = ingest_file(session, args.season, p)
            total += count
        session.commit()
    print(f"Ingested {total} projection rows for season {args.season}")


if __name__ == "__main__":
    main()


