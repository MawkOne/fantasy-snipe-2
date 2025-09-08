"""
Stage 1: Roll-forward contracts and tag RFAs/UFAs. Writes stage1_rollforward.json
"""
import os
from sqlalchemy import create_engine

from ..run_simulation import (
    roll_forward_and_classify,
    load_stage1_rollforward_path,
    RAILWAY_DB,
    EXT_DB,
)


def run(output_path: str | None = None, season_year: int = 2024) -> str:
    engine_local = create_engine(RAILWAY_DB, pool_pre_ping=True)
    engine_ext = create_engine(EXT_DB, pool_pre_ping=True)
    caps_commit, free_agents, teams = roll_forward_and_classify(engine_local, engine_ext, season_year)
    out = output_path or load_stage1_rollforward_path()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    import json
    with open(out, 'w') as f:
        json.dump({"caps": caps_commit, "free_agents": free_agents, "teams": teams}, f, indent=2)
    return out


