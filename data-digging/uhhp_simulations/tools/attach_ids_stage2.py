import os
import json
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


def attach_ids_to_file(path: str, pidx: Dict[str, Dict]) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception:
        return

    changed = False
    # stage2_buyouts.json structure: list or dict with entries containing 'player'
    def attach_in_obj(obj):
        nonlocal changed
        if isinstance(obj, dict):
            # try player field
            name = obj.get('player') or obj.get('player_name')
            pos = (obj.get('pos') or '').upper()
            if name and 'player_id' not in obj:
                pid, pname = best_id(pidx, name, pos)
                if pid is not None:
                    obj['player_id'] = pid
                    obj['player_full_name'] = pname or name
                    changed = True
            # recurse into values
            for v in obj.values():
                attach_in_obj(v)
        elif isinstance(obj, list):
            for it in obj:
                attach_in_obj(it)

    attach_in_obj(data)

    if changed:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stage2'))
    buyouts = os.path.join(base, 'stage2_buyouts.json')
    trades = os.path.join(base, 'stage2_trades.json')
    engine = create_engine(EXT_DB)
    pidx = build_player_index(engine)
    attach_ids_to_file(buyouts, pidx)
    attach_ids_to_file(trades, pidx)


if __name__ == '__main__':
    main()


