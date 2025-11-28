import os
import json
from typing import Dict, List


def load_week1(year: int, base: str) -> Dict[str, List[Dict]]:
    path = os.path.join(base, 'outputs', f'week1_rosters_{year}_enriched.json')
    with open(path, 'r') as f:
        return json.load(f)


def load_roster_owner_map(year: int, base: str) -> Dict[str, str]:
    path = os.path.join(base, 'outputs', f'{year}_rosters.json')
    with open(path, 'r') as f:
        data = json.load(f)
    teams = data.get('teams', {})
    return {team: obj.get('owner') for team, obj in teams.items()}


def compute_spend(entries: List[Dict]) -> float:
    total = 0.0
    for e in entries:
        sal = e.get('salary')
        yrs = e.get('years')
        if e.get('player_id') is None and (e.get('display_name') or '').lower().startswith('z-caphit'):
            # cap hits count to spend
            if isinstance(sal, (int, float)):
                total += float(sal or 0)
            continue
        if not isinstance(sal, (int, float)):
            continue
        if isinstance(yrs, (int, float)) and yrs is not None and yrs > 0:
            total += float(sal)
        else:
            # RFAs/UFAs at 0 years should not count as carryover spend
            pass
    return round(total, 2)


def build_profiles(base: str, years: List[int]) -> Dict:
    profiles: Dict[str, Dict] = {}
    for y in years:
        w = load_week1(y, base)
        owners = load_roster_owner_map(y, base)
        for team, entries in w.items():
            owner = owners.get(team) or team
            prof = profiles.setdefault(owner, {"teams": set(), "years": {}, "total_spend": 0.0})
            prof["teams"].add(team)
            spend = compute_spend(entries)
            prof["years"][str(y)] = {"team": team, "week1_spend": spend}
            prof["total_spend"] += spend
    # Convert sets to lists and add averages
    for owner, p in profiles.items():
        p["teams"] = sorted(list(p["teams"]))
        year_vals = [v["week1_spend"] for v in p["years"].values()]
        p["avg_week1_spend"] = round(sum(year_vals) / max(1, len(year_vals)), 2)
    return profiles


def main():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    years = [2022, 2023, 2024]
    profs = build_profiles(base, years)
    out_path = os.path.join(base, 'gm', 'gm_week1_spend_profiles.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump({"profiles": profs, "years": years}, f, indent=2)


if __name__ == '__main__':
    main()


