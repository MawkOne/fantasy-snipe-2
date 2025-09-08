import os
import json
import unicodedata
from collections import OrderedDict
from typing import Dict, List
import argparse


def norm(s: str) -> str:
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


def compute_team_totals(data: Dict[str, List[Dict]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for team, entries in data.items():
        if not isinstance(entries, list):
            continue
        s = 0.0
        for e in entries:
            sal = e.get('salary')
            yrs = e.get('years')
            if not isinstance(sal, (int, float)):
                continue
            # Count cap hits
            disp = norm(e.get('display_name') or e.get('parsed_name') or '')
            if disp.startswith('z-caphit'):
                s += float(sal or 0)
                continue
            # Count active contracts with years > 0
            if isinstance(yrs, (int, float)) and yrs and float(yrs) > 0:
                s += float(sal or 0)
        totals[team] = round(s, 2)
    return totals


def insert_summary(path: str) -> None:
    with open(path, 'r') as f:
        obj = json.load(f)
    # obj is mapping team->entries or already contains a summary; we will rebuild ordered dict
    # Remove existing summary if present
    if isinstance(obj, dict) and 'team_salary_totals' in obj:
        teams_only = {k: v for k, v in obj.items() if k != 'team_salary_totals'}
    else:
        teams_only = obj
    totals = compute_team_totals(teams_only)
    new_obj = OrderedDict()
    new_obj['team_salary_totals'] = totals
    for k, v in teams_only.items():
        new_obj[k] = v
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
            insert_summary(p)


if __name__ == '__main__':
    main()


