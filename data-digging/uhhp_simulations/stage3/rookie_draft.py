"""
Stage 3: Rookie Draft assembly and NHLe application.
Writes stage3_rookie_draft.json
"""
import os
from ..run_simulation import update_stage3_rookie_draft, apply_nhle_to_stage3


def run(stage1_path: str, stage3_path: str, nhle_path: str) -> str:
    update_stage3_rookie_draft(stage1_path, stage3_path, {})
    apply_nhle_to_stage3(stage3_path, nhle_path)
    return stage3_path


