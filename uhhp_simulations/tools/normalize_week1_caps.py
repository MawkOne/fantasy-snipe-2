import os
import json
import re
from typing import Dict, List
import argparse


def last_name_key(name: str) -> str:
    if not name:
        return ''
    parts = re.sub(r"[^A-Za-z\s]", " ", name).split()
    return parts[-1].lower() if parts else ''


def dedupe_and_fix(team_entries: List[Dict]) -> List[Dict]:
    # Map of caphit last name to True (if present)
    cap_lastnames = set()
    for e in team_entries:
        disp = (e.get('display_name') or e.get('parsed_name') or '').lower()
        if disp.startswith('z-caphit'):
            # try to extract a name token after label
            key = last_name_key(e.get('display_name') or e.get('parsed_name') or '')
            if key:
                cap_lastnames.add(key)

    seen_pid = set()
    out: List[Dict] = []
    for e in team_entries:
        pid = e.get('player_id')
        # Neutralize contract if caphit exists for same last name
        if pid is not None:
            ln = last_name_key(e.get('player_full_name') or e.get('parsed_name') or e.get('display_name') or '')
            if ln and ln in cap_lastnames:
                e['salary'] = None
                e['years'] = None
        # Set 0-year RFAs to salary 0
        yrs = e.get('years')
        if isinstance(yrs, (int, float)) and int(yrs) == 0:
            e['salary'] = 0.0

        # Dedupe by player_id when present; if None, allow (cap hits, draft, unknowns)
        if pid is not None:
            if pid in seen_pid:
                continue
            seen_pid.add(pid)
        out.append(e)
    return out


def recompute_totals(obj: Dict[str, List[Dict]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for team, entries in obj.items():
        if not isinstance(entries, list):
            continue
        s = 0.0
        for e in entries:
            sal = e.get('salary')
            yrs = e.get('years')
            disp = (e.get('display_name') or e.get('parsed_name') or '').lower()
            if disp.startswith('z-caphit'):
                if isinstance(sal, (int, float)):
                    s += float(sal or 0)
                continue
            if isinstance(yrs, (int, float)) and float(yrs) > 0 and isinstance(sal, (int, float)):
                s += float(sal or 0)
        totals[team] = round(s, 2)
    return totals


def normalize_week1(path: str) -> None:
    with open(path, 'r') as f:
        obj = json.load(f)
    # Remove existing summary if any
    if isinstance(obj, dict) and 'team_salary_totals' in obj:
        teams_only = {k: v for k, v in obj.items() if k != 'team_salary_totals'}
    else:
        teams_only = obj

    fixed: Dict[str, List[Dict]] = {}
    for team, entries in teams_only.items():
        fixed[team] = dedupe_and_fix(entries if isinstance(entries, list) else [])

    totals = recompute_totals(fixed)
    new_obj = {'team_salary_totals': totals}
    new_obj.update(fixed)
    with open(path, 'w') as f:
        json.dump(new_obj, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=str, help='Comma-separated years like 2022,2023,2024')
    args = parser.parse_args()
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    years = [2024] if not args.years else [int(y.strip()) for y in args.years.split(',') if y.strip()]
    for y in years:
        p = os.path.join(base, 'outputs', f'week1_rosters_{y}_enriched.json')
        if os.path.exists(p):
            normalize_week1(p)


if __name__ == '__main__':
    main()


