import os
import json
import re
import unicodedata
from typing import Dict, Optional, Tuple

from sqlalchemy import create_engine, text


EXT_DB = "postgresql://postgres:new-password-123@34.47.23.137:5432/postgres"


def norm(s: str) -> str:
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


def build_player_index(engine) -> Dict[str, Dict]:
    idx: Dict[str, Dict] = {}
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, full_name, position_code FROM players WHERE full_name IS NOT NULL")).fetchall()
    for r in rows:
        pid = int(r[0]); full = (r[1] or '').strip(); pos = (r[2] or '').strip() or None
        if not full:
            continue
        n1 = norm(full)
        idx[n1] = {"id": pid, "full_name": full, "position_code": pos}
        parts = full.split()
        if len(parts) >= 2:
            flipped = norm(f"{parts[-1]} {parts[0]}")
            idx.setdefault(flipped, {"id": pid, "full_name": full, "position_code": pos})
    return idx


def best_id(idx: Dict[str, Dict], name: str, pos_hint: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    n = norm(name)
    hit = idx.get(n)
    if hit:
        return int(hit['id']), str(hit['full_name'])
    toks = n.split()
    if not toks:
        return None, None
    last = toks[-1]
    cands = [v for k, v in idx.items() if k.endswith(" "+last) or k.startswith(last+" ")]
    if pos_hint:
        cpos = [c for c in cands if (c.get('position_code') or '').upper().startswith(pos_hint[0])]
        if cpos:
            cands = cpos
    if cands:
        def score(v):
            nm = norm(v.get('full_name') or '')
            return len(set(nm.split()) & set(toks))
        cands.sort(key=score, reverse=True)
        top = cands[0]
        return int(top['id']), str(top.get('full_name') or name)
    return None, None


def attach_ids_stage1(stage1_path: str) -> None:
    with open(stage1_path, 'r') as f:
        data = json.load(f)

    engine = create_engine(EXT_DB)
    pidx = build_player_index(engine)

    # Teams
    teams = data.get('teams') or []
    for t in teams:
        for p in t.get('players', []):
            name = p.get('player') or p.get('display_name') or ''
            pos = (p.get('pos') or '').upper()
            if not name:
                continue
            pid, pname = best_id(pidx, name, pos)
            if pid is not None:
                p['player_id'] = pid
                p['player_full_name'] = pname or name

    # Free agents
    fas = data.get('free_agents') or []
    for fa in fas:
        name = fa.get('player') or ''
        pos = (fa.get('pos') or '').upper()
        if not name:
            continue
        pid, pname = best_id(pidx, name, pos)
        if pid is not None:
            fa['player_id'] = pid
            fa['player_full_name'] = pname or name

    with open(stage1_path, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    candidates = [
        os.path.join(base, 'stage1', 'stage1_rollforward.json'),
        os.path.join(base, 'outputs', 'stage1_rollforward.json'),
    ]
    path = None
    for c in candidates:
        if os.path.exists(c):
            path = c
            break
    if not path:
        raise SystemExit('stage1_rollforward.json not found')
    attach_ids_stage1(path)


if __name__ == '__main__':
    main()


