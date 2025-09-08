import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
import argparse


def parse_period1_start(weekly_md_path: str) -> datetime:
    import re
    with open(weekly_md_path, 'r') as f:
        for line in f:
            m = re.search(r"Period\s*1:\s*(\d{1,2}/\d{1,2}/\d{2})\s*-", line)
            if m:
                return datetime.strptime(m.group(1), "%m/%d/%y")
    raise RuntimeError("Unable to find Period 1 start")


def parse_date_raw(s: str) -> datetime:
    s = (s or '').strip()
    parts = s.split(' ET')[0]
    return datetime.strptime(parts, "%m/%d/%y %I:%M %p")


def build_signed_prices(transactions_json: str, cutoff: datetime) -> Dict[Tuple[str, int], float]:
    with open(transactions_json, 'r') as f:
        tx = json.load(f)
    out: Dict[Tuple[str, int], float] = {}
    for e in tx.get('transactions', []):
        t = (e.get('type') or '').lower()
        if t != 'signed':
            continue
        pid = e.get('player_id')
        if pid is None:
            continue
        dt = parse_date_raw(e.get('date_raw') or '')
        if dt >= cutoff:
            continue
        price = e.get('price')
        if price is None:
            continue
        key = (e.get('team') or '', int(pid))
        # Keep last price before cutoff for the team
        out[key] = float(price)
    return out


def build_carryover_map(rosters_json: str) -> Dict[Tuple[str, int], Tuple[float, int]]:
    with open(rosters_json, 'r') as f:
        data = json.load(f)
    res: Dict[Tuple[str, int], Tuple[float, int]] = {}
    for team, obj in (data.get('teams') or {}).items():
        for p in obj.get('players', []):
            pid = p.get('player_id')
            if pid is None:
                continue
            sal = p.get('salary')
            yrs = p.get('years')
            res[(team, int(pid))] = (float(sal) if isinstance(sal, (int, float)) else 0.0, int(yrs) if isinstance(yrs, (int, float)) else 0)
    return res


def recompute_week1(base_dir: str, year: int) -> None:
    weekly_md = os.path.join(base_dir, f'{year}_weekly.md')
    cutoff = parse_period1_start(weekly_md)
    tx_json = os.path.join(base_dir, 'outputs', f'transactions_{year}.json')
    w1_path = os.path.join(base_dir, 'outputs', f'week1_rosters_{year}_enriched.json')
    carry_path = os.path.join(base_dir, 'outputs', f'{year}_rosters.json')

    signed_prices = build_signed_prices(tx_json, cutoff)
    carry = build_carryover_map(carry_path)

    with open(w1_path, 'r') as f:
        w1 = json.load(f)

    # Update entries: prefer signed price before cutoff; else carryover salary/years; RFAs at 0 years -> salary 0
    for team, entries in w1.items():
        if not isinstance(entries, list):
            continue
        for ent in entries:
            pid = ent.get('player_id')
            if pid is None:
                continue
            key = (team, int(pid))
            if key in signed_prices:
                ent['salary'] = float(signed_prices[key])
                ent['years'] = 1
            else:
                if key in carry:
                    sal, yrs = carry[key]
                    ent['salary'] = sal
                    ent['years'] = yrs
            # RFAs at 0 years -> salary 0
            if isinstance(ent.get('years'), (int, float)) and int(ent.get('years')) == 0:
                ent['salary'] = 0.0

    # Recompute totals at top
    totals: Dict[str, float] = {}
    for team, entries in w1.items():
        s = 0.0
        if isinstance(entries, list):
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

    new_obj = {'team_salary_totals': totals}
    new_obj.update(w1)
    with open(w1_path, 'w') as f:
        json.dump(new_obj, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=str, help='Comma-separated years like 2022,2023,2024')
    args = parser.parse_args()
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    years = [2024] if not args.years else [int(y.strip()) for y in args.years.split(',') if y.strip()]
    for y in years:
        recompute_week1(base, y)


if __name__ == '__main__':
    main()


