import os
import re
import json
import unicodedata
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
import argparse


EXT_DB = "postgresql://postgres:new-password-123@34.47.23.137:5432/postgres"


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii").strip().lower()


def parse_roster_display_to_full_name(display: str) -> Tuple[str, Optional[str]]:
    s = (display or "").strip()
    # flip Last, First
    if "," in s:
        last, first = [p.strip() for p in s.split(",", 1)]
        s = f"{first} {last}"
    # remove POS + NHL suffix if present
    toks = s.split()
    if len(toks) >= 2 and re.fullmatch(r"[A-Z]{2,3}", toks[-1]) and re.fullmatch(r"[A-Z]{1,2}W|[CDG]|F", toks[-2]):
        pos = toks[-2]
        name = " ".join(toks[:-2]).strip()
        return name, pos
    # fallback: last token as pos
    pos = None
    if toks:
        last = toks[-1].upper()
        if last in {"C","D","G","W","LW","RW","F"}:
            pos = last
            toks = toks[:-1]
    return " ".join(toks).strip(), pos


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


def convert_rosters(md_path: str, out_path: str) -> None:
    engine = create_engine(EXT_DB)
    pidx = build_player_index(engine)

    with open(md_path, 'r') as f:
        md = f.read()

    teams: Dict[str, Dict] = {}
    current_team = None
    owner = None

    for raw in md.splitlines():
        line = raw.rstrip('\n')
        if not line:
            continue
        # Detect team header: "Team Name - Owner"
        if ' - ' in line and not line.startswith('Player') and not line.startswith('TOTALS'):
            current_team = line.split(' - ', 1)[0].strip()
            owner = line.split(' - ', 1)[1].strip()
            teams.setdefault(current_team, {"owner": owner, "players": []})
            continue
        if current_team is None:
            continue
        if line.startswith('Player') or line.startswith('TOTALS'):
            continue
        # Rows are tab-delimited; first column is player display; salary/years may follow
        parts = [p for p in line.split('\t') if p != '']
        if not parts:
            continue
        disp = parts[0].strip()
        salary = None
        years = None
        # Try read salary and years if present
        if len(parts) >= 2:
            try:
                salary = float(parts[1].replace('$',''))
            except Exception:
                salary = None
        if len(parts) >= 3:
            try:
                years = int(float(parts[2]))
            except Exception:
                years = None

        # Skip cap hits rows; store as extras if needed
        if norm(disp).startswith('z-caphit'):
            teams[current_team]["players"].append({
                "player": disp,
                "display_name": disp,
                "player_id": None,
                "salary": salary,
                "years": years,
                "is_cap_hit": True,
            })
            continue

        full, pos = parse_roster_display_to_full_name(disp)
        pid, pname = best_id(pidx, full, pos)
        entry = {
            "player": full,
            "display_name": disp,
            "pos": pos,
            "salary": salary,
            "years": years,
            "player_id": pid,
            "player_full_name": pname or full,
        }
        teams[current_team]["players"].append(entry)

    # Deduplicate per team by player_id (or normalized name if id missing)
    for t, obj in teams.items():
        seen: set = set()
        deduped: List[Dict] = []
        for p in obj.get('players', []):
            key = (p.get('player_id') if p.get('player_id') is not None else norm(p.get('player') or ''))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)
        obj['players'] = deduped

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump({"year": os.path.basename(md_path)[:4], "teams": teams}, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=str, help='Comma-separated years like 2022,2023,2024')
    args = parser.parse_args()

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if args.years:
        years = [int(y.strip()) for y in args.years.split(',') if y.strip()]
    else:
        years = [2024]

    for y in years:
        md_path = os.path.join(base, f'{y}_rosters.md')
        out_path = os.path.join(base, 'outputs', f'{y}_rosters.json')
        convert_rosters(md_path, out_path)


if __name__ == '__main__':
    main()


