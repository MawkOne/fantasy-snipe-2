import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse


def parse_period1_start(weekly_md_path: str) -> datetime:
    # Expect a line like: "Period 1: 10/4/24 - 10/13/24"
    with open(weekly_md_path, 'r') as f:
        for line in f:
            m = re.search(r"Period\s*1:\s*(\d{1,2}/\d{1,2}/\d{2})\s*-", line)
            if m:
                dt = datetime.strptime(m.group(1), "%m/%d/%y")
                # Start of day
                return dt
    raise RuntimeError("Unable to find Period 1 start in weekly file")


def parse_date_raw(s: str) -> Optional[datetime]:
    # Examples: "12/23/24 7:21 PM ET", "10/5/24 7:55 AM ET"
    s = (s or '').strip()
    try:
        parts = s.split(' ET')[0]
        return datetime.strptime(parts, "%m/%d/%y %I:%M %p")
    except Exception:
        return None


def load_transactions(transactions_json_path: str, cutoff: datetime) -> List[Dict]:
    with open(transactions_json_path, 'r') as f:
        tx = json.load(f)
    evs = tx.get('transactions', [])
    # Keep only events after or on cutoff to reverse them
    out: List[Dict] = []
    for e in evs:
        dt = parse_date_raw(e.get('date_raw') or '')
        if dt is None:
            continue
        if dt >= cutoff:
            out.append(e)
    # Sort ascending so reversals are applied in chronological order (removing later adds first works fine)
    out.sort(key=lambda e: parse_date_raw(e.get('date_raw') or ''))
    return out


def _load_initial_enriched(base_dir: str, year: int) -> Dict[str, List[Dict]]:
    enriched_path = os.path.join(base_dir, "outputs", f"week1_rosters_{year}_enriched.json")
    # If enriched file exists and has data, use it
    try:
        with open(enriched_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and data:
                return data
    except Exception:
        pass
    # Else, bootstrap from outputs/{year}_rosters.json
    seed_path = os.path.join(base_dir, 'outputs', f'{year}_rosters.json')
    with open(seed_path, 'r') as f:
        seed = json.load(f)
    teams = seed.get('teams', {})
    out: Dict[str, List[Dict]] = {}
    for team, obj in teams.items():
        ents: List[Dict] = []
        for p in obj.get('players', []):
            pid = p.get('player_id')
            if pid is None:
                ents.append({
                    "display_name": p.get('display_name') or p.get('player') or '',
                    "parsed_name": p.get('player') or '',
                    "position_hint": p.get('pos'),
                    "player_id": None,
                    "player_full_name": None,
                    "note": "non-player-entry" if p.get('is_cap_hit') else None,
                })
            else:
                ents.append({
                    "display_name": p.get('display_name') or p.get('player_full_name') or p.get('player') or '',
                    "parsed_name": p.get('player_full_name') or p.get('player') or '',
                    "position_hint": p.get('pos'),
                    "player_id": int(pid),
                    "player_full_name": p.get('player_full_name') or p.get('player') or '',
                })
        out[team] = ents
    return out


def rebuild_week1_for_year(base_dir: str, year: int) -> None:
    weekly_md = os.path.join(base_dir, f"{year}_weekly.md")
    tx_json = os.path.join(base_dir, "outputs", f"transactions_{year}.json")
    roster_enriched = os.path.join(base_dir, "outputs", f"week1_rosters_{year}_enriched.json")

    cutoff = parse_period1_start(weekly_md)
    events = load_transactions(tx_json, cutoff)

    rosters = _load_initial_enriched(base_dir, year)

    # Build team -> {id -> entry} map for quick updates; keep non-player entries
    team_players: Dict[str, Dict[int, Dict]] = {}
    team_extras: Dict[str, List[Dict]] = {}
    for team, entries in rosters.items():
        pid_map: Dict[int, Dict] = {}
        extras: List[Dict] = []
        for ent in entries:
            pid = ent.get('player_id')
            if pid is None:
                extras.append(ent)
            else:
                pid_map[int(pid)] = ent
        team_players[team] = pid_map
        team_extras[team] = extras

    # Helper to ensure team keys exist
    def ensure_team(t: str):
        if t not in team_players:
            team_players[t] = {}
            team_extras[t] = []

    # Reverse events to get to start of Period 1
    for e in events:
        t = e.get('team') or ''
        ensure_team(t)
        pid = e.get('player_id')
        if pid is None:
            continue
        pid = int(pid)
        et = (e.get('type') or '').lower()
        # Non-player cap hits are ignored
        if str(e.get('player') or '').lower().startswith('z-caphit'):
            continue
        if et in ('signed', 'added', 'activated'):
            # Reverse: remove from team if present
            team_players[t].pop(pid, None)
        elif et == 'dropped':
            # Reverse: add back to team if missing
            if pid not in team_players[t]:
                team_players[t][pid] = {
                    "display_name": e.get('player_full_name') or e.get('player') or '',
                    "parsed_name": e.get('player_full_name') or e.get('player') or '',
                    "position_hint": e.get('pos'),
                    "player_id": pid,
                    "player_full_name": e.get('player_full_name') or e.get('player') or '',
                }
        elif et == 'traded_in':
            # Reverse: move from team back to from_team
            from_team = e.get('from_team') or ''
            ensure_team(from_team)
            # Remove from current team
            ent = team_players[t].pop(pid, None)
            # Add to from_team if missing
            if pid not in team_players[from_team]:
                if ent is None:
                    ent = {
                        "display_name": e.get('player_full_name') or e.get('player') or '',
                        "parsed_name": e.get('player_full_name') or e.get('player') or '',
                        "position_hint": e.get('pos'),
                        "player_id": pid,
                        "player_full_name": e.get('player_full_name') or e.get('player') or '',
                    }
                team_players[from_team][pid] = ent
        else:
            # Other: no-op
            pass

    # Reassemble enriched structure
    rebuilt: Dict[str, List[Dict]] = {}
    for team in sorted(set(list(team_players.keys()) + list(team_extras.keys()))):
        entries: List[Dict] = []
        # Keep extras (cap hits, Draft) as-is
        entries.extend(team_extras.get(team, []))
        # Add players sorted by name for stability
        players_sorted = sorted(team_players.get(team, {}).values(), key=lambda x: (x.get('player_full_name') or x.get('parsed_name') or ''))
        entries.extend(players_sorted)
        rebuilt[team] = entries

    # Write back
    with open(roster_enriched, 'w') as f:
        json.dump(rebuilt, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', type=str, help='Comma-separated years like 2022,2023,2024')
    args = parser.parse_args()

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if args.years:
        years = [int(y.strip()) for y in args.years.split(',') if y.strip()]
    else:
        years = [2024]
    for year in years:
        rebuild_week1_for_year(base, year)


if __name__ == '__main__':
    main()


