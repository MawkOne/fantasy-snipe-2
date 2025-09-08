import os
import json
import unicodedata
from typing import Dict, List, Optional, Tuple
import argparse


def norm(s: str) -> str:
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


def build_contract_maps(seed_path: str) -> Tuple[Dict[int, Dict], Dict[str, Dict]]:
    """
    Returns:
      - player_id -> {salary, years}
      - caphit_key -> {salary, years} where caphit_key is normalized display_name starting with z-caphit
    """
    with open(seed_path, 'r') as f:
        seed = json.load(f)
    pid_map: Dict[int, Dict] = {}
    cap_map: Dict[str, Dict] = {}
    for team, obj in (seed.get('teams') or {}).items():
        for p in obj.get('players', []):
            if p.get('is_cap_hit'):
                key = norm(p.get('display_name') or p.get('player') or '')
                cap_map[key] = {
                    'salary': p.get('salary'),
                    'years': p.get('years'),
                }
                continue
            pid = p.get('player_id')
            if pid is None:
                continue
            pid_map[int(pid)] = {
                'salary': p.get('salary'),
                'years': p.get('years'),
            }
    return pid_map, cap_map


def enrich_week1_with_contracts(week1_path: str, seed_path: str) -> None:
    try:
        with open(week1_path, 'r') as f:
            data = json.load(f)
    except Exception:
        return
    pid_map, cap_map = build_contract_maps(seed_path)

    changed = False
    for team, entries in data.items():
        if not isinstance(entries, list):
            continue
        for ent in entries:
            pid = ent.get('player_id')
            if pid is not None:
                info = pid_map.get(int(pid))
                if info:
                    if ent.get('salary') != info.get('salary') or ent.get('years') != info.get('years'):
                        ent['salary'] = info.get('salary')
                        ent['years'] = info.get('years')
                        changed = True
            else:
                # cap hit rows
                disp = norm(ent.get('display_name') or ent.get('parsed_name') or '')
                if disp.startswith('z-caphit'):
                    info = cap_map.get(disp)
                    if info:
                        if ent.get('salary') != info.get('salary') or ent.get('years') != info.get('years'):
                            ent['salary'] = info.get('salary')
                            ent['years'] = info.get('years')
                            changed = True

    if changed:
        with open(week1_path, 'w') as f:
            json.dump(data, f, indent=2)


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
        week1 = os.path.join(base, 'outputs', f'week1_rosters_{y}_enriched.json')
        seed = os.path.join(base, 'outputs', f'{y}_rosters.json')
        if os.path.exists(week1) and os.path.exists(seed):
            enrich_week1_with_contracts(week1, seed)


if __name__ == '__main__':
    main()


