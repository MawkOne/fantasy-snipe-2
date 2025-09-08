import os
import re
import json
import time
import unicodedata
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
import argparse


EXT_DB = "postgresql://postgres:new-password-123@34.47.23.137:5432/postgres"


def norm(s: str) -> str:
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


def build_player_index(engine) -> Dict[str, Dict]:
    idx: Dict[str, Dict] = {}
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, full_name, position_code FROM players WHERE full_name IS NOT NULL")).fetchall()
    for r in rows:
        pid = int(r[0])
        full = (r[1] or '').strip()
        pos = (r[2] or '').strip() or None
        if not full:
            continue
        n1 = norm(full)
        idx[n1] = {"id": pid, "full_name": full, "position_code": pos}
        parts = full.split()
        if len(parts) >= 2:
            flipped = norm(f"{parts[-1]} {parts[0]}")
            idx.setdefault(flipped, {"id": pid, "full_name": full, "position_code": pos})
    return idx


def parse_player_blob(blob: str) -> Tuple[str, Optional[str], Optional[str]]:
    # Example: "Matthew Knies W • TOR" -> ("Matthew Knies", "W", "TOR")
    s = blob.strip()
    # split around bullets
    parts = [p.strip() for p in re.split(r"\u2022|•", s)]
    left = parts[0].strip()
    pos = None
    team = None
    # Left side like "Name W" or "Name C" or just Name
    m = re.match(r"^(.*?)[\s]+([A-Z]{1,2}W|[CDG])$", left)
    if m:
        name = m.group(1).strip()
        pos = m.group(2)
    else:
        name = left.strip()
        # Fallback: token parse last token as pos if it looks like POS
        toks = name.split()
        if toks:
            last = toks[-1].upper()
            if last in {"C","D","G","W","LW","RW","F"}:
                pos = last
                name = " ".join(toks[:-1]).strip()
    if len(parts) > 1:
        right = parts[1].strip()
        if right:
            toks = right.split()
            if toks:
                team = toks[0]
    return name, pos, team


def best_id(idx: Dict[str, Dict], name: str, pos_hint: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
    n = norm(name)
    hit = idx.get(n)
    if hit:
        return int(hit['id']), str(hit['full_name'])
    # coarse fallback by last name
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


def parse_md(md_text: str) -> List[Dict]:
    events: List[Dict] = []
    lines = md_text.splitlines()
    i = 0
    txn_id = 0

    date_re = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}\s+\d{1,2}:\d{2}\s+[AP]M\s+ET\t")
    time_only_tab_re = re.compile(r"^\d{1,2}:\d{2}\s+[AP]M\s+ET\t")
    time_only_space_re = re.compile(r"^\d{1,2}:\d{2}\s+[AP]M\s+ET\s+")

    while i < len(lines):
        line = lines[i].rstrip('\n')
        if not line:
            i += 1
            continue
        if not date_re.match(line):
            # skip stray or header lines until we hit a date line
            i += 1
            continue

        # Start a transaction block
        head_parts = line.split('\t')
        if len(head_parts) < 3:
            i += 1
            continue
        date_part = head_parts[0].strip()
        team = head_parts[1].strip()
        first_rest = '\t'.join(head_parts[2:])

        action_lines: List[str] = []
        if first_rest:
            action_lines.append(first_rest)

        i += 1
        # collect continuation lines until next date line or EOF
        while i < len(lines) and not date_re.match(lines[i]):
            cont = lines[i].rstrip('\n')
            if cont:
                action_lines.append(cont)
            i += 1

        # Emit one event per action line within this transaction block
        txn_id += 1
        current_team = team
        for act in action_lines:
            # Detect mid-block team switch with time-only prefix (tolerate leading spaces)
            # Case 1: tab-delimited time-only, e.g., "7:21 PM ET\tNew Oilers Nation\tMorgan Frost C • CGY - Traded from ..."
            act_l = act.lstrip()
            if '\t' in act_l and time_only_tab_re.match(act_l):
                parts = act_l.split('\t')
                # parts: [time_only, team, rest...]
                if len(parts) >= 3:
                    current_team = parts[1].strip()
                    act = '\t'.join(parts[2:])
            else:
                # Case 2: space-delimited time-only
                if time_only_space_re.match(act_l):
                    # Extract team then rest
                    mto = re.match(r"^(\d{1,2}:\d{2}\s+[AP]M\s+ET)\s+([^\t]+?)\s+(.*)$", act_l)
                    if mto:
                        current_team = mto.group(2).strip()
                        act = mto.group(3)

            mm = re.match(r"^(.*?)\s+-\s+(.*)$", act.strip())
            if not mm:
                continue
            player_blob = mm.group(1).strip()
            action_blob = mm.group(2).strip()
            action_blob = action_blob.split('\t')[0].strip()

            name, pos, nhl_team = parse_player_blob(player_blob)

            ev: Dict = {
                "transaction_id": txn_id,
                "date_raw": date_part,
                "team": current_team,
                "player": name,
                "pos": pos,
                "nhl_team": nhl_team,
                "raw": f"{player_blob} - {action_blob}",
            }

            ab = action_blob.lower()
            if 'signed for $' in ab:
                ev['type'] = 'signed'
                mpr = re.search(r"\$(\d+(?:\.\d{1,2})?)", action_blob)
                if mpr:
                    try:
                        ev['price'] = int(float(mpr.group(1)))
                    except Exception:
                        pass
            elif 'dropped' in ab:
                ev['type'] = 'dropped'
            elif 'activated' in ab:
                ev['type'] = 'activated'
            elif 'added' in ab:
                ev['type'] = 'added'
            elif 'traded from' in ab:
                ev['type'] = 'traded_in'
                mfr = re.search(r"traded from\s+(.*)$", action_blob, re.I)
                if mfr:
                    ev['from_team'] = mfr.group(1).strip()
            else:
                ev['type'] = 'other'

            events.append(ev)

    return events


def run_for_year(year: int) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    md_path = os.path.join(base, f'{year}_transactions.md')
    if not os.path.exists(md_path):
        raise FileNotFoundError(md_path)
    out_path = os.path.join(base, 'outputs', f'transactions_{year}.json')
    alt_out = os.path.join(base, f'transactions_{year}.json')

    with open(md_path, 'r') as f:
        md = f.read()

    events = parse_md(md)

    engine = create_engine(EXT_DB)
    idx = build_player_index(engine)
    for e in events:
        if e.get('player'):
            pid, pname = best_id(idx, e['player'], e.get('pos'))
            e['player_id'] = pid
            if pname:
                e['player_full_name'] = pname

    obj = {
        "year": year,
        "transactions": events,
        "record_count": len(events),
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": os.path.basename(md_path),
    }

    os.makedirs(os.path.join(base, 'outputs'), exist_ok=True)
    with open(alt_out, 'w') as f:
        json.dump(obj, f, indent=2)
    with open(out_path, 'w') as f:
        json.dump(obj, f, indent=2)
    return alt_out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=str, help='Comma-separated years like 2022,2023,2024')
    args = parser.parse_args()

    if args.years:
        years = [int(y.strip()) for y in args.years.split(',') if y.strip()]
    else:
        years = [2024]

    for y in years:
        run_for_year(y)


if __name__ == '__main__':
    main()


