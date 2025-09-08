import os
import json
import csv
import re
import unicodedata
from collections import defaultdict, deque
from typing import Dict, List, Tuple

from sqlalchemy import create_engine, text

# Config
RAILWAY_DB = "postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway"
EXT_DB = "postgresql://postgres:new-password-123@34.47.23.137:5432/postgres"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs"))
# Current-season projections inputs
PROJ_DTZ_SKATERS = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/Forecasts/2025_26_DtZ/Copy of Preliminary - DtZ 2025-2026 NHL Fantasy Projections - Skater Projections.csv"))
PROJ_DTZ_GOALIES = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/Forecasts/2025_26_DtZ/Copy of Preliminary - DtZ 2025-2026 NHL Fantasy Projections - Goalie Projections.csv"))
PROJ_FANTASYPROS = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/Forecasts/2025_26_fantasy_pros/FantasyPros_2025_Draft_ALL_Rankings.csv"))

# UHHP lineup slots across 12 teams
NUM_TEAMS = 12
SLOTS_PER_TEAM = {"G": 2, "C": 2, "W": 3, "F": 4, "D": 4}
# We allocate F to 2 C and 2 W for replacement computations
AGG_SLOTS = {"G": 2 * NUM_TEAMS, "C": (2 + 2) * NUM_TEAMS, "W": (3 + 2) * NUM_TEAMS, "D": 4 * NUM_TEAMS}

NOMINATION_ORDER = [
    "The Dook of Sook",
    "South Calgary Oilers",
    "New Oilers Nation",
    "HawtSawwce",
    "re-degeneration X 2.0",
    "3sheets Sports Entertainment",
    "Shazam!!!",
    "CinStars",
    "G' Stars",
    "The Pylons",
    "LIP's Lasers",
    "The Inglorious Basteeerds",
]

name_norm = lambda s: unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def to_float(x: str) -> float:
    if x is None:
        return 0.0
    s = str(x).strip()
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else 0.0


def to_int(x: str) -> int:
    if x is None:
        return 0
    s = str(x).strip()
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else 0


def load_2025_26_projections() -> Dict[str, Dict[str, float]]:
    """Load 2025/26 projections from DtZ (skaters & goalies) and FantasyPros as fallback.
    Returns mapping: norm_name -> {fp: float, pos: one of C/W/D/G}
    """
    proj: Dict[str, Dict[str, float]] = {}
    # DtZ Skaters
    if os.path.exists(PROJ_DTZ_SKATERS):
        with open(PROJ_DTZ_SKATERS, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nm = (row.get("Player") or "").strip()
                if not nm:
                    continue
                pos_raw = (row.get("Pos") or row.get("POS") or "").upper()
                goals = to_float(row.get("Goals") or row.get("G") or "0")
                assists = to_float(row.get("Assists") or row.get("A") or "0")
                is_d = "D" in pos_raw
                # UHHP scoring for skaters + D bonuses
                fp = 3.0 * goals + 2.0 * assists + (2.0 * goals + 1.0 * assists if is_d else 0.0)
                if fp <= 0 and not is_d:
                    continue
                # Bucket positions
                pos = "D" if is_d else ("C" if "C" in pos_raw else "W")
                proj[name_norm(nm)] = {"fp": fp, "pos": pos}
    # DtZ Goalies
    if os.path.exists(PROJ_DTZ_GOALIES):
        with open(PROJ_DTZ_GOALIES, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nm = (row.get("player") or row.get("Player") or "").strip()
                if not nm:
                    continue
                w = to_float(row.get("W") or "0")
                ga = to_float(row.get("GA") or "0")
                sv = to_float(row.get("SV") or row.get("Saves") or "0")
                otl = to_float(row.get("OTL") or "0")
                so = to_float(row.get("SO") or "0")
                fp = 2.0 * w + (-1.25) * ga + 0.2 * sv + 1.0 * otl + 1.0 * so
                proj.setdefault(name_norm(nm), {"fp": fp, "pos": "G"})
                # If skater and goalie share name (unlikely), prefer higher FP and keep skater pos
                if proj[name_norm(nm)]["fp"] < fp:
                    proj[name_norm(nm)] = {"fp": fp, "pos": "G"}
    # FantasyPros ranking as light fallback for missing players (impute small FP)
    if os.path.exists(PROJ_FANTASYPROS):
        with open(PROJ_FANTASYPROS, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nm = (row.get("PLAYER NAME") or row.get("Player") or "").strip()
                if not nm:
                    continue
                key = name_norm(nm)
                if key in proj:
                    continue
                pos_raw = (row.get("POS") or "").upper()
                try:
                    rk = float(str(row.get("RK") or row.get("Rank") or "0").replace("#", "").strip())
                except Exception:
                    rk = 0.0
                # Impute a conservative FP declining with rank (kept small to avoid bias)
                base = max(0.0, 200.0 - rk) * 0.4
                pos = "D" if "D" in pos_raw else ("G" if "G" in pos_raw else ("C" if "C" in pos_raw else "W"))
                proj[key] = {"fp": base, "pos": pos}
    return proj


def compute_replacement(proj: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    pos_to_fps: Dict[str, List[float]] = {"C": [], "W": [], "D": [], "G": []}
    # Replacement levels per position
    for v in proj.values():
        p = v["pos"]
        if p in ("L", "R", "W"):
            pos_to_fps["W"].append(v["fp"])
        elif p == "D":
            pos_to_fps["D"].append(v["fp"])
        elif p == "C":
            pos_to_fps["C"].append(v["fp"])
        else:
            pos_to_fps["W"].append(v["fp"])  # default into W
    for arr in pos_to_fps.values():
        arr.sort(reverse=True)
    rep: Dict[str, float] = {}
    for p in ("C", "W", "D", "G"):
        pool = pos_to_fps[p]
        rk = max(1, min(len(pool), AGG_SLOTS.get(p, 0) or 1))
        rep[p] = pool[rk - 1] if pool else 0.0
    return rep


def compute_elite_thresholds(proj: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Return 90th percentile FP per position as an elite cutoff."""
    pos_to_fp: Dict[str, List[float]] = {"C": [], "W": [], "D": [], "G": []}
    for v in proj.values():
        p = v.get("pos") or "W"
        fp = float(v.get("fp") or 0.0)
        bucket = p if p in ("C", "W", "D", "G") else "W"
        pos_to_fp[bucket].append(fp)
    import math
    def pct(arr, p):
        if not arr:
            return 9e9
        arr = sorted(arr)
        k = max(0, min(len(arr) - 1, int(math.floor(p * (len(arr) - 1)))))
        return arr[k]
    return {pos: pct(vals, 0.90) for pos, vals in pos_to_fp.items()}


def roll_forward_and_classify(engine_local, engine_ext, season_year: int) -> Tuple[Dict, List[Dict], List[Dict]]:
    """Roll forward rosters one year, classify FA types, and build team structures with players.
    Returns: (caps_commit_state, free_agents_list, teams_list)
    """
    rows = []
    with engine_local.connect() as c:
        rows = c.execute(text(
            """
            SELECT team_name, owner_name, player_name, salary, years, rookie, status, position
            FROM cbs_team_rosters
            WHERE league_subdomain=:lg AND sport=:sp AND season_year=:yr
            """), {"lg": "uhhp", "sp": "hockey", "yr": season_year}).fetchall()
    # Birthdates for RFA/UFA classification
    births = {}
    name_to_id = {}
    with engine_ext.connect() as c:
        # Load name->id map
        try:
            res_ids = c.execute(text(
                """
                SELECT full_name, id FROM players
                """
            ))
            for full_name, pid in res_ids:
                name_to_id[name_norm(full_name)] = int(pid)
        except Exception:
            name_to_id = {}
        # Load cached birthdates via join
        res = c.execute(text(
            """
            SELECT p.full_name, i.birthdate
            FROM players p
            LEFT JOIN player_info_tmp i ON i.player_id = p.id
            WHERE i.birthdate IS NOT NULL
            """
        ))
        for full_name, bdate in res:
            births[name_norm(full_name)] = bdate
        # Also load firstname+lastname directly for broader coverage
        try:
            res2 = c.execute(text(
                """
                SELECT firstname, lastname, birthdate FROM player_info_tmp WHERE birthdate IS NOT NULL
                """
            ))
            for fn, ln, bd in res2:
                nm = f"{(fn or '').strip()} {(ln or '').strip()}".strip()
                if nm:
                    births.setdefault(name_norm(nm), bd)
        except Exception:
            pass
    def age_on(dob, on_date):
        from datetime import datetime
        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob[:10], "%Y-%m-%d").date()
            except Exception:
                return None
        return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))
    def fmt_birthdate(dob):
        try:
            if dob is None:
                return None
            s = str(dob)
            return s[:10]
        except Exception:
            return None
    def fetch_birthdate_from_api(player_id: int) -> str | None:
        try:
            import json as _json
            from urllib.request import urlopen
            url = f"https://statsapi.web.nhl.com/api/v1/people/{player_id}"
            with urlopen(url, timeout=5) as resp:
                data = _json.loads(resp.read().decode('utf-8'))
            people = (data or {}).get('people') or []
            if not people:
                return None
            bd = (people[0] or {}).get('birthDate')
            return bd
        except Exception:
            return None
    from datetime import date
    cutoff = date(season_year + 1, 7, 1)

    # Fallback: infer RFA when birthdate is missing
    def _infer_rfa_from_row(rook, status) -> bool:
        s = str(status or '').lower()
        if 'rfa' in s or 'restricted' in s:
            return True
        try:
            if rook is True:
                return True
            if isinstance(rook, (int, float)) and int(rook) == 1:
                return True
            if isinstance(rook, str) and rook.strip().lower() in ('1', 'true', 'yes', 'y'):
                return True
        except Exception:
            pass
        return False

    team_commit: Dict[str, float] = defaultdict(float)
    team_players: Dict[str, List[Dict]] = defaultdict(list)
    team_owner: Dict[str, str] = {}
    free_agents: List[Dict] = []

    for r in rows:
        team, owner, player, sal, yrs, rook, status, pos = r
        team_owner[team] = owner
        sal_f = to_float(sal)
        yrs_i = to_int(yrs)
        new_yrs = max(0, yrs_i - 1)
        # Handle explicit cap hit rows labelled like 'z-CAPHIT ...'
        if name_norm(player).startswith('z-caphit'):
            if new_yrs > 0:
                team_commit[team] += sal_f
                team_players[team].append({
                    "player": player,
                    "display_name": player,
                    "pos": (pos or '').upper(),
                    "salary": sal_f,
                    "years": new_yrs,
                    "is_cap_hit": True,
                })
            # cap-hit entries do not become free agents
            continue
        # Convert roster display name to full name for matching
        s = (player or '').strip()
        toks = s.split()
        if len(toks) >= 2 and re.match(r"^[A-Z]{2,3}$", toks[-1]) and re.match(r"^[A-Z]{1,2}W|[CDG]$", toks[-2]):
            toks = toks[:-2]
        joined = " ".join(toks)
        if "," in joined:
            last, first = [p.strip() for p in joined.split(",", 1)]
            full = f"{first} {last}"
        else:
            full = joined
        key = name_norm(full)
        bd = births.get(key)
        if not bd:
            pid = name_to_id.get(key)
            if pid:
                fetched = fetch_birthdate_from_api(pid)
                if fetched:
                    bd = births[key] = fetched
        age = age_on(bd, cutoff) if bd else None

        if new_yrs > 0:
            team_commit[team] += sal_f
            future_fa = None
            if new_yrs == 1:
                if age is not None:
                    # July 1 cutoff: RFA if age < 27 on July 1
                    future_fa = "RFA" if age < 27 else "UFA"
                else:
                    # Fallback only from roster status hints
                    future_fa = "RFA" if _infer_rfa_from_row(rook, status) else "UFA"
            team_players[team].append({
                "player": full,
                "display_name": player,
                "pos": (pos or '').upper(),
                "salary": sal_f,
                "years": new_yrs,
                "future_fa": future_fa,
                "birthdate": fmt_birthdate(bd),
            })
        else:
            if age is not None:
                # July 1 cutoff: RFA if age < 27 on July 1
                fa_type = "RFA" if age < 27 else "UFA"
            else:
                # Fallback only from roster status hints
                fa_type = "RFA" if _infer_rfa_from_row(rook, status) else "UFA"
            free_agents.append({
                "team": team,
                "owner": owner,
                "player": full,
                "pos": (pos or '').upper(),
                "last_salary": sal_f,
                "fa_type": fa_type,
                "birthdate": fmt_birthdate(bd),
            })
    team_caps = {t: max(0.0, 100.0 - team_commit.get(t, 0.0)) for t in set([r[0] for r in rows])}
    teams_list: List[Dict] = []
    for t in sorted(team_owner.keys()):
        players = sorted(team_players.get(t, []), key=lambda x: (-int(x.get("salary") or 0), x.get("player") or ""))
        teams_list.append({
            "team_name": t,
            "owner_name": team_owner[t],
            "cap_commit": int(team_commit.get(t, 0)),
            "cap_space": int(team_caps.get(t, 0)),
            "players": players,
        })
    return {"team_caps": team_caps, "commit": team_commit}, free_agents, teams_list


def auction_simulation(team_caps_in: Dict[str, float], free_agents: List[Dict], proj: Dict[str, Dict[str, float]], rep: Dict[str, float], team_filled_init: Dict[str, Dict[str, int]] = None) -> Tuple[List[Dict], Dict[str, float], Dict[str, Dict]]:
    # Private value model: k_pos * VORP; constants calibrated roughly (no actuals)
    K = {"C": 0.21, "W": 0.18, "D": 0.13, "G": 0.03}
    # Build FA pool with projected FP and VORP (include all FAs; fallback if projection missing)
    pool: List[Dict] = []
    for fa in free_agents:
        key = name_norm(fa.get("player") or "")
        v = proj.get(key)
        # Determine position from projections or from FA entry
        pos_raw = None
        if v:
            pos_raw = v.get("pos")
        if not pos_raw:
            pos_raw = (fa.get("pos") or "").upper()
        pos = pos_raw if pos_raw in ("C","W","D","G") else ("W" if pos_raw in ("L","R","LW","RW","W") else "W")
        # Determine FP and VORP; if missing projections, use replacement-level (vorp=0) so player is still in pool
        if v and v.get("fp") is not None:
            fp = float(v.get("fp"))
        else:
            fp = float(rep.get(pos, 0.0))
        vorp = max(0.0, fp - rep.get(pos, 0.0))
        pool.append({
            "player": fa.get("player"),
            "player_id": fa.get("player_id"),
            "pos": pos,
            "type": fa.get("fa_type"),
            "owner_team": fa.get("team"),
            "fp": fp,
            "vorp": vorp,
        })
    # Map for quick lookups
    pool.sort(key=lambda x: (-x["fp"], x["player"]))
    taken = set()
    caps = {t: min(98.0, float(cap)) for t, cap in team_caps_in.items()}
    # Required roster targets per team (allocate F as 2C+2W)
    REQ = {"G": 2, "C": 4, "W": 5, "D": 4}
    # Initialize filled slots per team (can pass a snapshot from Stage 1 if available)
    team_filled: Dict[str, Dict[str, int]] = {}
    for t in caps.keys():
        base = {"G": 0, "C": 0, "W": 0, "D": 0}
        if team_filled_init and t in team_filled_init:
            for p in base.keys():
                try:
                    base[p] = int(team_filled_init[t].get(p, 0))
                except Exception:
                    base[p] = 0
        team_filled[t] = base

    def remaining_slots_after_pick(team: str, pick_pos: str) -> int:
        filled = team_filled[team].copy()
        if pick_pos in filled:
            filled[pick_pos] += 1
        total_req = sum(REQ.values())
        total_filled = sum(min(filled[p], REQ[p]) for p in REQ)
        return max(0, total_req - total_filled)
    results: List[Dict] = []
    # State tracking: budgets and needs snapshots
    def compute_needs_snapshot() -> Dict[str, Dict[str, int]]:
        snap: Dict[str, Dict[str, int]] = {}
        for t, filled in team_filled.items():
            snap[t] = {p: max(0, REQ[p] - int(filled.get(p, 0))) for p in REQ}
        return snap
    state_log: Dict[str, Dict] = {
        "start_caps": {t: float(caps[t]) for t in caps},
        "start_needs": compute_needs_snapshot(),
        "pick_states": {},
    }
    initial_total_cap = sum(caps.values()) or 1.0

    def private_value(team: str, p: Dict) -> float:
        # Needs-aware: scale by unmet requirement share for that position
        pos = p["pos"]
        need = max(0, REQ[pos] - team_filled[team].get(pos, 0))
        need_share = (need / max(1, REQ[pos]))
        budget_scale = (sum(caps.values()) or 0.0) / initial_total_cap
        return K.get(pos, 0.15) * p["vorp"] * (1.0 + 0.5 * need_share) * max(0.5, budget_scale)

    # Round helpers
    def nominate_best(filter_func, phase: str) -> List[Dict]:
        picks: List[Dict] = []
        for team in NOMINATION_ORDER:
            # choose best affordable by this team under filter
            chosen = None
            for cand in pool:
                if cand["player"] in taken:
                    continue
                if not filter_func(cand):
                    continue
                pv = private_value(team, cand)
                # Reserve rule: leave $2 for each remaining slot after this pick
                rem_after = remaining_slots_after_pick(team, cand["pos"])
                cap = caps.get(team, 0.0)
                max_bid_allowed = int(max(0, cap - 2 * rem_after))
                price = max(2, int(round(2 + pv)))
                if price > max_bid_allowed:
                    continue
                if cap >= price:
                    chosen = (cand, price)
                    break
            if not chosen:
                continue
            cand, price = chosen
            # simple competitive bidding: find max of other teams' pv within cap
            high = price
            winner = team
            for rival in NOMINATION_ORDER:
                if rival == team:
                    continue
                rv = private_value(rival, cand)
                # Rival affordability with reserve rule
                rem_after_r = remaining_slots_after_pick(rival, cand["pos"])
                cap_r = caps.get(rival, 0.0)
                max_bid_r = int(max(0, cap_r - 2 * rem_after_r))
                bid = max(2, int(round(2 + rv)))
                if bid > max_bid_r:
                    bid = 0
                if cap_r >= bid and bid > high:
                    high = bid
                    winner = rival
            # RFA match
            if cand["type"] == "RFA" and cand["owner_team"] in caps:
                owner_pv = private_value(cand["owner_team"], cand)
                rem_after_o = remaining_slots_after_pick(cand["owner_team"], cand["pos"])
                cap_o = caps.get(cand["owner_team"], 0.0)
                max_bid_o = int(max(0, cap_o - 2 * rem_after_o))
                owner_bid = max(2, int(round(2 + owner_pv)))
                if owner_bid > max_bid_o:
                    owner_bid = 0
                if cap_o >= high and owner_bid >= high:
                    winner = cand["owner_team"]
            # award
            caps[winner] = max(0.0, caps[winner] - high)
            taken.add(cand["player"])
            # Update team filled counts for positional needs
            pos = cand["pos"]
            if pos in team_filled[winner]:
                team_filled[winner][pos] = min(REQ[pos], team_filled[winner][pos] + 1)
            pick_idx = len(results) + len(picks) + 1
            picks.append({
                "team": winner,
                "player": cand["player"],
                "player_id": cand.get("player_id"),
                "pos": pos,
                "type": cand["type"],
                "price": high,
                "phase": phase
            })
            # Log state after this pick
            state_log["pick_states"][str(pick_idx)] = {
                "caps": {t: float(caps[t]) for t in caps},
                "needs": compute_needs_snapshot(),
            }
        return picks

    # Round 1: any
    results.extend(nominate_best(lambda c: True, phase="superstar"))
    # Round 2: UFA only
    results.extend(nominate_best(lambda c: c["type"] == "UFA", phase="ufa"))
    # Round 3: RFA loop once through order (stop if no affordable RFA)
    r3 = nominate_best(lambda c: c["type"] == "RFA", phase="rfa")
    results.extend(r3)
    return results, caps, state_log


def waiver_to_exact_100(caps_after_auction: Dict[str, float]) -> List[Dict]:
    # Each team must be exactly at $100 by Week 1; fill remaining with $2/$3 signings.
    # Strategy: if remaining is odd, place one $3 first, then fill rest with $2s.
    signings: List[Dict] = []
    for team, rem in caps_after_auction.items():
        remaining = int(round(rem))
        if remaining <= 0:
            continue
        if remaining % 2 == 1:
            signings.append({"team": team, "player": "Waiver Replacement", "price": 3})
            remaining -= 3
        if remaining > 0:
            n_twos = remaining // 2
            for _ in range(n_twos):
                signings.append({"team": team, "player": "Waiver Replacement", "price": 2})
    return signings


def rebuild_gm_profiles() -> None:
    """Parse 2022/2023 markdown sources to fill gm_profiles.json with rosters, transactions, and weekly results.
    This is a lightweight pass to avoid missing data and can be expanded later.
    """
    base = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    paths = {
        '2022_rosters': os.path.join(base, '2022_rosters.md'),
        '2022_tx': os.path.join(base, '2022_transactions.md'),
        '2023_rosters': os.path.join(base, '2023_rosters.md'),
        '2023_tx': os.path.join(base, '2023_transactions.md'),
    }
    data = {k: None for k in paths}
    for k, p in paths.items():
        if os.path.exists(p):
            with open(p, 'r') as f:
                data[k] = f.read()
    def parse_roster(md: str) -> Dict[str, Dict]:
        teams: Dict[str, Dict] = {}
        if not md:
            return teams
        cur = None
        for line in md.splitlines():
            line = line.strip()
            if not line:
                continue
            if ' - ' in line and not line.startswith('Player') and not line.startswith('TOTALS'):
                cur = line.split(' - ', 1)[0].strip()
                teams.setdefault(cur, {'players': 0, 'salary': 0})
                continue
            if cur and '\t' in line and not line.startswith('TOTALS') and not line.startswith('Player'):
                parts = [p for p in line.split('\t') if p != '']
                if len(parts) >= 3:
                    try:
                        salary = float(parts[1])
                    except Exception:
                        salary = 0
                    teams[cur]['players'] += 1
                    teams[cur]['salary'] += salary
        return teams
    def parse_transactions(md: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        if not md:
            return counts
        for line in md.splitlines():
            if '\t' not in line:
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            team = parts[1].strip()
            if team and not team.lower().startswith('date'):
                counts[team] = counts.get(team, 0) + 1
        return counts
    profiles: Dict[str, Dict] = {}
    # Aggregate 2022 and 2023
    for yr in ('2022', '2023'):
        ro = parse_roster(data.get(f'{yr}_rosters') or '')
        tx = parse_transactions(data.get(f'{yr}_tx') or '')
        for team, rinfo in ro.items():
            prof = profiles.setdefault(team, {'years': {}})
            prof['years'][yr] = {'roster_players': rinfo['players'], 'roster_salary': rinfo['salary'], 'transactions': int(tx.get(team, 0))}
        # also capture teams with transactions only
        for team, cnt in tx.items():
            prof = profiles.setdefault(team, {'years': {}})
            yr_ent = prof['years'].setdefault(yr, {'roster_players': 0, 'roster_salary': 0, 'transactions': 0})
            yr_ent['transactions'] = int(cnt)
    out_path = os.path.join(base, 'gm_profiles.json')
    try:
        with open(out_path, 'w') as f:
            json.dump({'profiles': profiles}, f, indent=2)
    except Exception:
        pass


def season_totals_from_rosters(auction_results: List[Dict], waiver_signings: List[Dict], proj: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    # Deterministic first pass: team PF = sum of projected FP for drafted players; waivers contribute 0 baseline
    team_pf: Dict[str, float] = defaultdict(float)
    for r in auction_results:
        key = name_norm(r["player"])
        v = proj.get(key)
        if v:
            team_pf[r["team"]] += v["fp"]
    # Waiver placeholders assumed replacement-level; ignore FP in first pass
    standings = sorted(team_pf.items(), key=lambda x: x[1], reverse=True)
    return {"team_pf": team_pf, "rank": {t: i + 1 for i, (t, _) in enumerate(standings)}}


def _write_team_outlooks_generic(teams: List[Dict], projections: Dict[str, Dict[str, float]], stage3_path: str, out_path: str) -> None:
    """Compute and write team outlooks for the provided teams list.
    Uses rookie draft pick values if available to inform win_next.
    """
    _pick_vals, team_pick_vals = _compute_pick_values_from_stage3(stage3_path)
    team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)
    # Blueprint-level details (match Stage 2 richness)
    budgets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gm', 'positional_budgets.json'))
    try:
        with open(budgets_path, 'r') as f:
            blueprint_cfg = json.load(f)
    except Exception:
        blueprint_cfg = {}
    replacement_map = compute_replacement(projections)
    thresholds = compute_elite_thresholds(projections)

    def _norm_name(s: str) -> str:
        import unicodedata
        return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()

    def _pos_bucket(p: str) -> str:
        p = (p or '').upper()
        if p in ('C', 'W', 'D', 'G'):
            return p
        if p in ('L', 'R', 'LW', 'RW', 'F'):
            return 'W'
        return 'W'

    def _player_fp_and_pos(pname: str, fallback_pos: str):
        v = projections.get(_norm_name(pname or ''))
        if v:
            return float(v.get('fp') or 0.0), _pos_bucket(v.get('pos') or fallback_pos)
        return 0.0, _pos_bucket(fallback_pos)

    def _team_spend(t: Dict) -> Dict[str, int]:
        sums = {'F': 0, 'D': 0, 'G': 0}
        for pl in t.get('players', []):
            try:
                sal = int(pl.get('salary') or 0)
            except Exception:
                sal = 0
            pos = _pos_bucket(pl.get('pos'))
            if pos == 'D':
                sums['D'] += sal
            elif pos == 'G':
                sums['G'] += sal
            else:
                sums['F'] += sal
        return sums

    position_targets = (blueprint_cfg.get('position_budgets') or {})
    depth_min = int((blueprint_cfg.get('guidelines') or {}).get('depth_count_min') or 6)
    blueprint_needs: Dict[str, Dict] = {}
    for t in teams:
        spend = _team_spend(t)
        needs = {}
        for k in ('F', 'D', 'G'):
            tgt = position_targets.get(k) or {}
            try:
                mn = int(tgt.get('min') or 0)
                mx = int(tgt.get('max') or 0)
            except Exception:
                mn = 0
                mx = 0
            needs[k] = {
                'spend': spend.get(k, 0),
                'min': mn,
                'max': mx,
                'delta_to_min': max(0, mn - spend.get(k, 0)),
                'delta_over_max': max(0, spend.get(k, 0) - mx) if mx else 0,
            }
        # Evaluate elite counts, keeper value, starters, depth
        elite_counts = {'C': 0, 'W': 0, 'D': 0, 'G': 0}
        cheap_keepers = {'F': 0, 'D': 0, 'G': 0}
        goalie_starters = 0
        depth_count = 0
        for pl in t.get('players', []):
            yrs = int(pl.get('years') or 0)
            try:
                sal = int(pl.get('salary') or 0)
            except Exception:
                sal = 0
            pos_raw = (pl.get('pos') or '').upper()
            fp, pos = _player_fp_and_pos(pl.get('player') or pl.get('display_name') or '', pos_raw)
            thr_pos = 'W' if pos not in ('C', 'W', 'D', 'G') else pos
            thr = thresholds.get(thr_pos, 9e9)
            if fp >= thr:
                elite_counts[thr_pos] = elite_counts.get(thr_pos, 0) + 1
            rep = replacement_map.get(thr_pos if thr_pos in ('C', 'W', 'D', 'G') else 'W', 0.0)
            vorp = max(0.0, fp - rep)
            if yrs >= 2 and sal <= 4 and ((thr_pos == 'G' and vorp >= 4.0) or (thr_pos != 'G' and vorp >= 5.0)):
                bucket = 'F' if thr_pos in ('C', 'W') else thr_pos
                cheap_keepers[bucket] = cheap_keepers.get(bucket, 0) + 1
            if thr_pos == 'G' and fp >= (replacement_map.get('G', 0.0) + 4.0):
                goalie_starters += 1
            if yrs > 0 and 2 <= sal <= 5:
                depth_count += 1

        # Adjusted targets based on cheap keepers and add actions
        adj_targets = {kk: dict(needs[kk]) for kk in needs}
        actions: List[str] = []
        if cheap_keepers.get('F', 0) >= 1:
            adj_targets['F']['min'] = max(0, adj_targets['F']['min'] - 3)
            adj_targets['D']['max'] = adj_targets['D']['max'] + 3
            actions.append('cheap_F_keeper: prioritize elite D or stabilize G')
        if cheap_keepers.get('D', 0) >= 1:
            adj_targets['D']['min'] = max(0, adj_targets['D']['min'] - 2)
            adj_targets['F']['max'] = adj_targets['F']['max'] + 2
            actions.append('cheap_D_keeper: expand to 3rd premium F if value')
        if cheap_keepers.get('G', 0) >= 1:
            adj_targets['G']['max'] = max(0, adj_targets['G']['max'] - 2)
            adj_targets['F']['max'] = adj_targets['F']['max'] + 2
            actions.append('cheap_G_keeper: cap goalie spend; redirect to skaters')
        if elite_counts.get('D', 0) < 2:
            actions.append('need_elite_D: secure 1–2 D anchors')
        if elite_counts.get('C', 0) + elite_counts.get('W', 0) < 2:
            actions.append('need_elite_F: secure at least 2 elite F')
        if goalie_starters < 2:
            actions.append('need_goalies: ensure two starters (total $7–12)')
        if depth_count < depth_min:
            actions.append(f'need_depth: target {depth_min - depth_count}+ depth bids at $2–5')

        blueprint_needs[t.get('team_name') or ''] = {
            'position_spend_vs_targets': needs,
            'elite_counts': elite_counts,
            'cheap_keepers': cheap_keepers,
            'goalie_starters': goalie_starters,
            'depth_count': depth_count,
            'adjusted_targets': adj_targets,
            'suggested_actions': actions,
        }

    try:
        with open(out_path, 'w') as f:
            json.dump({'team_outlooks': team_outlooks, 'blueprint_needs': blueprint_needs}, f, indent=2)
    except Exception:
        pass


def perform_pre_draft_trades(stage1_path: str, out_path: str) -> None:
    """Simple trade pass: teams with zero cap_space attempt to move their largest carryover contract
    to teams with available cap. Produces a trade log and updated caps per team.
    """
    try:
        with open(stage1_path, 'r') as f:
            stage1 = json.load(f)
    except Exception:
        with open(out_path, 'w') as f:
            json.dump({"trades": [], "teams": {}}, f, indent=2)
        return

    teams = stage1.get('teams', [])
    # Build structures
    team_by_name = {t['team_name']: t for t in teams}
    zero_space = [t for t in teams if int(t.get('cap_space') or 0) == 0]
    # Candidates to receive: sort by cap_space desc
    receivers = sorted([t for t in teams if int(t.get('cap_space') or 0) > 0], key=lambda x: int(x.get('cap_space') or 0), reverse=True)

    trades = []
    for sender in zero_space:
        # select largest carryover contract (years>0) to move
        carry = [pl for pl in sender.get('players', []) if (pl.get('years') or 0) > 0 and int(pl.get('salary') or 0) > 0]
        if not carry:
            continue
        carry.sort(key=lambda x: int(x.get('salary') or 0), reverse=True)
        asset = carry[0]
        cost = int(asset.get('salary') or 0)
        # find a receiver with enough space
        recv = next((r for r in receivers if int(r.get('cap_space') or 0) >= cost and r['team_name'] != sender['team_name']), None)
        if not recv:
            continue
        # execute trade (simplified): move asset from sender to receiver, adjust caps
        sender['players'].remove(asset)
        recv['players'].append(asset)
        sender['cap_commit'] = int(sender.get('cap_commit') or 0) - cost
        sender['cap_space'] = int(sender.get('cap_space') or 0) + cost
        recv['cap_commit'] = int(recv.get('cap_commit') or 0) + cost
        recv['cap_space'] = max(0, int(recv.get('cap_space') or 0) - cost)
        trades.append({
            'from_team': sender['team_name'],
            'to_team': recv['team_name'],
            'player': asset['player'],
            'salary': cost,
            'note': 'pre-draft cap relief trade'
        })
        # update receivers sorted order
        receivers = sorted([t for t in teams if int(t.get('cap_space') or 0) > 0], key=lambda x: int(x.get('cap_space') or 0), reverse=True)

    result = {
        'trades': trades,
        'teams': {t['team_name']: {'cap_commit': t.get('cap_commit'), 'cap_space': t.get('cap_space')} for t in teams}
    }
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)


def find_2025_pick_ownership_from_md(md_path: str) -> Dict[str, str]:
    """Parse 2024_rosters.md to find 2025 rookie draft picks and owners.
    Returns mapping original_team_name -> current_owner_team_name.
    """
    # Synonym map for shorthand to canonical
    synonyms = {
        "3sse": "3sheets Sports Entertainment",
        "3sheets": "3sheets Sports Entertainment",
        "3sheets sports entertainment": "3sheets Sports Entertainment",
        "dook": "The Dook of Sook",
        "dooms": "Doomsday Machine",
        "doomsday machine": "Doomsday Machine",
        "redegen": "re-degeneration X 2.0",
        "re-degeneration x 2.0": "re-degeneration X 2.0",
        "lip": "LIP's Lasers",
        "lips": "LIP's Lasers",
        "g": "G' Stars",
        "g stars": "G' Stars",
        "g' stars": "G' Stars",
        "cin": "CinStars",
        "cinstars": "CinStars",
        "socal": "South Calgary Oilers",
        "south calgary oilers": "South Calgary Oilers",
        "hawtsawce": "HawtSawwce",
        "hawtsauce": "HawtSawwce",
        "non": "New Oilers Nation",
        "basteerds": "The Inglorious Basteeerds",
        "pylons": "The Pylons",
        "shax": "Shazam!!!",
        "shazam": "Shazam!!!",
    }
    def canon_team(s: str) -> str:
        k = name_norm(s)
        return synonyms.get(k, s)
    pick_map: Dict[str, str] = {}
    current_team: str = None
    try:
        with open(md_path, 'r') as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                # Section header: "Team - Owner"
                if " - " in line and not line.startswith("Player") and not line.startswith("TOTALS"):
                    current_team = line.split(" - ", 1)[0].strip()
                    continue
                if "2025 Draft Pick" in line and current_team:
                    # Expected formats seen: "2025 Draft Pick <token>, C" or similar
                    # Extract token after label up to comma or EOL
                    s = line
                    # remove leading columns if tab-separated
                    token_part = s.split("2025 Draft Pick", 1)[1].strip()
                    token_part = token_part.split(",")[0].strip()
                    token = token_part
                    # Some tokens are like "G" or "3sSE" or "Hawtsawce" etc.
                    orig = canon_team(token)
                    pick_map[orig] = current_team
    except Exception:
        return {}
    return pick_map


def update_stage3_rookie_draft(stage1_path: str, stage3_path: str, pick_map: Dict[str, str]) -> None:
    # Load owners map from stage1
    try:
        with open(stage1_path, 'r') as f:
            stage1 = json.load(f)
    except Exception:
        stage1 = {}
    owner_by_team = {t.get('team_name'): t.get('owner_name') for t in stage1.get('teams', [])}
    # Load stage 3 file
    try:
        with open(stage3_path, 'r') as f:
            draft = json.load(f)
    except Exception:
        draft = {"rookie_draft_rounds": 1, "picks": []}
    # Enrich available players with stats from NHL_Rookie_Draft_2025.md
    try:
        stats_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'NHL_Rookie_Draft_2025.md'))
        stats = {}
        if os.path.exists(stats_path):
            import re as _re
            with open(stats_path, 'r') as sf:
                for line in sf:
                    line = line.strip()
                    if not line or line.startswith('#') or line.upper().startswith('ROUND'):
                        continue
                    # Expect tab-separated columns; find the token with (Pos)
                    parts = [p for p in line.split('\t') if p != '']
                    if len(parts) < 5:
                        continue
                    # Find player cell containing '(' and ')'
                    player_cell = next((p for p in parts if '(' in p and ')' in p), None)
                    if not player_cell:
                        continue
                    # Extract name and position
                    m = _re.search(r"(.+?)\s*\(([^)]+)\)", player_cell)
                    if not m:
                        continue
                    pname = m.group(1).strip()
                    ppos = m.group(2).strip()
                    # Try to locate junior team and league following player cell
                    try:
                        idx = parts.index(player_cell)
                        team_jr = parts[idx + 1].strip() if idx + 1 < len(parts) else ''
                        league = parts[idx + 2].strip() if idx + 2 < len(parts) else ''
                        # Stats columns typically GP, G, A, TP
                        gp = parts[idx + 3] if idx + 3 < len(parts) else ''
                        g = parts[idx + 4] if idx + 4 < len(parts) else ''
                        a = parts[idx + 5] if idx + 5 < len(parts) else ''
                        tp = parts[idx + 6] if idx + 6 < len(parts) else ''
                    except Exception:
                        team_jr = league = gp = g = a = tp = ''
                    def _to_num(s):
                        try:
                            return int(float(str(s).replace(',', '').strip()))
                        except Exception:
                            return None
                    stats[name_norm(pname)] = {
                        'pos': ppos[:1].upper(),
                        'league': league,
                        'team': team_jr,
                        'gp': _to_num(gp),
                        'g': _to_num(g),
                        'a': _to_num(a),
                        'tp': _to_num(tp),
                    }
        # Merge into available_players
        for pl in draft.get('available_players', []):
            key = name_norm(pl.get('name') or '')
            st = stats.get(key)
            if st:
                pl.setdefault('pos', st.get('pos'))
                if st.get('league'):
                    pl['league'] = st['league']
                if st.get('team'):
                    pl['nhl_team'] = st['team']
                pl['stats'] = {
                    'gp': st.get('gp'),
                    'g': st.get('g'),
                    'a': st.get('a'),
                    'tp': st.get('tp'),
                }
    except Exception:
        pass
    picks = draft.get('picks', [])
    for p in picks:
        orig_team = p.get('team_name')
        new_team = pick_map.get(orig_team, orig_team)
        p['original_team'] = orig_team
        p['team_name'] = new_team
        p['owner_name'] = owner_by_team.get(new_team)
        # Ensure pick status/selection fields present
        if 'status' not in p:
            p['status'] = 'pending'
        if 'selection' not in p:
            p['selection'] = None
    # Ensure available player state fields present
    avail = draft.get('available_players', [])
    for pl in avail:
        if 'state' not in pl:
            pl['state'] = 'available'
        if 'selected_by' not in pl:
            pl['selected_by'] = None
        if 'selected_at_pick' not in pl:
            pl['selected_at_pick'] = None
    with open(stage3_path, 'w') as f:
        json.dump(draft, f, indent=2)


def apply_nhle_to_stage3(stage3_path: str, nhle_json_path: str) -> None:
    try:
        with open(stage3_path, 'r') as f:
            draft = json.load(f)
    except Exception:
        return
    try:
        with open(nhle_json_path, 'r') as f:
            nhle = json.load(f)
    except Exception:
        return
    # Build factor map (Points NHLe preferred for points projection)
    fac_map: Dict[str, float] = {}
    for e in nhle.get('leagues', []):
        nm = (e.get('league') or '').strip()
        if not nm:
            continue
        fac = e.get('points_nhle')
        if fac is None:
            fac = e.get('points') or e.get('nhle') or e.get('factor')
        try:
            fac_map[name_norm(nm)] = float(fac)
        except Exception:
            continue
    # Synonyms for mapping
    synonyms = {
        "hockeyallsv...": "allsvenskan",
        "hockeyallsvenskan": "allsvenskan",
        "boston college": "ncaa",
        "ohl": "ohl",
        "whl": "whl",
        "qmjhl": "qmjhl",
        "ncaa": "ncaa",
        "mhl": "mhl",
        "czech": "czech",
        "czech u20": "czech u20",
        "u20 swiss": "u20 swiss",
        "usports": "usports",
        "slovakia": "slovakia",
        "slovakia u20": "slovakia u20",
        "swiss": "sl",
        "sl": "sl",
        "del": "del",
        "del2": "del2",
        "liiga": "liiga",
        "magnus": "magnus",
        "kazakhstan": "kazakhstan",
        "dnl u20": "dnl u20",
        "bchl": "bchl",
        "ajhl": "ajhl",
        "ushl": "ushl",
        "alpshl": "alpshl",
        "j20 nationell": "j20 nationell",
        "nahl": "nahl",
        "u20 finland": "u20 finland",
        "latvia": "latvia",
        "poland": "poland",
        "erste liga": "erste liga",
        "sphl": "sphl",
        "eihl": "eihl",
        "denmark": "denmark",
    }
    def lookup_factor(league: str) -> float:
        if not league:
            return 0.0
        k = name_norm(league)
        k = synonyms.get(k, k)
        return float(fac_map.get(k, 0.0))
    # Apply factors
    changed = False
    for pl in draft.get('available_players', []):
        league = pl.get('league') or pl.get('nhl_team')
        factor = lookup_factor(league)
        st = pl.get('stats') or {}
        g = st.get('g')
        a = st.get('a')
        tp = st.get('tp')
        try:
            if tp is None and g is not None and a is not None:
                tp = int(g) + int(a)
        except Exception:
            pass
        nhle_tp = None
        if isinstance(tp, (int, float)) and factor:
            nhle_tp = round(float(tp) * float(factor), 2)
        if 'nhle' not in pl:
            pl['nhle'] = {}
        pl['nhle']['league_factor'] = factor
        pl['nhle']['tp_nhle'] = nhle_tp
        changed = True
    if changed:
        with open(stage3_path, 'w') as f:
            json.dump(draft, f, indent=2)


def simulate_rookie_draft_best_available(stage3_path: str) -> None:
    """Stage 3: simulate one-round rookie draft selecting best available by NHLe tp.
    Updates picks with 'selection' and marks players as selected with selected_by/pick.
    """
    try:
        with open(stage3_path, 'r') as f:
            draft = json.load(f)
    except Exception:
        return
    avail = draft.get('available_players', [])
    picks = draft.get('picks', [])
    # Build ranking list: only players with numeric tp_nhle
    def tp_val(pl):
        nh = pl.get('nhle') or {}
        v = nh.get('tp_nhle')
        try:
            return float(v) if v is not None else -1.0
        except Exception:
            return -1.0
    ranked = sorted(avail, key=lambda pl: tp_val(pl), reverse=True)
    taken = set()
    # Use cursor through ranked list
    idx = 0
    for pk in sorted(picks, key=lambda x: int(x.get('pick') or 0)):
        # find next untaken with non-negative tp
        sel = None
        while idx < len(ranked):
            cand = ranked[idx]
            idx += 1
            if tp_val(cand) < 0:
                continue
            nm = cand.get('name')
            if nm in taken:
                continue
            sel = cand
            break
        if not sel:
            continue
        taken.add(sel.get('name'))
        # update pick
        pk['status'] = 'selected'
        pk['selection'] = sel.get('name')
        # update player state
        sel['state'] = 'selected'
        sel['selected_by'] = pk.get('team_name')
        sel['selected_at_pick'] = pk.get('pick')
    # write back
    with open(stage3_path, 'w') as f:
        json.dump(draft, f, indent=2)


def compute_vorp_per_dollar_thresholds(teams: List[Dict], projections: Dict[str, Dict[str, float]], replacement: Dict[str, float]) -> Tuple[float, float]:
    values: List[float] = []
    for t in teams:
        for pl in t.get('players', []):
            if (pl.get('years') or 0) != 1:
                continue
            if (pl.get('future_fa') or '') != 'UFA':
                continue
            salary = float(pl.get('salary') or 0.0)
            if salary <= 0:
                continue
            key = name_norm(pl.get('player') or '')
            v = projections.get(key)
            if not v:
                continue
            pos = v.get('pos') or 'W'
            rep = replacement.get(pos, 0.0)
            vorp = max(0.0, v['fp'] - rep)
            vpd = vorp / salary if salary > 0 else 0.0
            if vpd > 0:
                values.append(vpd)
    if not values:
        return 0.1, 0.3
    values.sort()
    import math
    def pct(arr, p):
        if not arr:
            return 0.0
        k = max(0, min(len(arr) - 1, int(math.floor(p * (len(arr) - 1)))))
        return arr[k]
    poor = pct(values, 0.25)
    good = pct(values, 0.60)
    return poor, good


def _compute_pick_values_from_stage3(stage3_path: str) -> Tuple[Dict[int, float], Dict[str, float]]:
    """Read stage3 rookie draft file and compute value for each pick number using NHLe tp.
    Returns (pick_number -> value, team_name -> value for their pick).
    """
    try:
        with open(stage3_path, 'r') as f:
            d = json.load(f)
    except Exception:
        return {}, {}
    avail = d.get('available_players', [])
    picks = d.get('picks', [])
    # Rank players by NHLe tp
    def tp(pl):
        nh = pl.get('nhle') or {}
        v = nh.get('tp_nhle')
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    ranked = sorted(avail, key=lambda x: tp(x), reverse=True)
    pick_vals: Dict[int, float] = {}
    for i, pk in enumerate(sorted(picks, key=lambda x: int(x.get('pick') or 0)), start=1):
        val = tp(ranked[i-1]) if i-1 < len(ranked) else 0.0
        pick_vals[int(pk.get('pick') or i)] = round(val, 2)
    team_vals: Dict[str, float] = {}
    for pk in picks:
        team = pk.get('team_name')
        pno = int(pk.get('pick') or 0)
        if team:
            team_vals[team] = pick_vals.get(pno, 0.0)
    return pick_vals, team_vals


def _compute_team_outlooks(teams: List[Dict], projections: Dict[str, Dict[str, float]], team_pick_vals: Dict[str, float]) -> Dict[str, str]:
    """Compute win outlook per team: 'win_now' | 'win_next' | 'build_following'.
    current_fp = sum FP for players under contract (years>0)
    y2_fp = sum FP for players with years>1 plus estimated FP from pick value.
    """
    def team_fp_current(t):
        s = 0.0
        for pl in t.get('players', []):
            if int(pl.get('years') or 0) > 0:
                v = projections.get(name_norm(pl.get('player') or ''))
                if v:
                    s += float(v.get('fp') or 0.0)
        return s
    def team_fp_y2(t):
        s = 0.0
        for pl in t.get('players', []):
            if int(pl.get('years') or 0) > 1:
                v = projections.get(name_norm(pl.get('player') or ''))
                if v:
                    s += float(v.get('fp') or 0.0)
        # Convert pick value (NHLe TP) to approximate FP using factor ~2.5 per point
        pick_tp = float(team_pick_vals.get(t.get('team_name'), 0.0) or 0.0)
        s += pick_tp * 2.5
        return s
    curr_map = {t['team_name']: team_fp_current(t) for t in teams}
    y2_map = {t['team_name']: team_fp_y2(t) for t in teams}
    arr_curr = sorted(curr_map.values())
    arr_y2 = sorted(y2_map.values())
    def pct_rank(arr, val):
        if not arr:
            return 0.0
        # position in sorted array
        import bisect
        i = bisect.bisect_left(arr, val)
        return i / max(1, len(arr) - 1)
    out: Dict[str, str] = {}
    for t in teams:
        nm = t['team_name']
        pc = pct_rank(arr_curr, curr_map[nm])
        py2 = pct_rank(arr_y2, y2_map[nm])
        if pc >= 0.70:
            out[nm] = 'win_now'
        elif py2 >= 0.70:
            out[nm] = 'win_next'
        else:
            out[nm] = 'rebuild'
    return out


def stage2_buyouts_and_trades(stage1_path: str, projections: Dict[str, Dict[str, float]], replacement: Dict[str, float], out_buyouts: str, out_trades: str, update_stage1_path: str, stage3_path: str) -> None:
    try:
        with open(stage1_path, 'r') as f:
            stage1 = json.load(f)
    except Exception:
        with open(out_buyouts, 'w') as f:
            json.dump({"buyouts": []}, f, indent=2)
        with open(out_trades, 'w') as f:
            json.dump({"trades": []}, f, indent=2)
        return

    teams = stage1.get('teams', [])
    free_agents_global: List[Dict] = stage1.get('free_agents', [])
    if not teams:
        # nothing to do
        with open(out_buyouts, 'w') as f:
            json.dump({"buyouts": []}, f, indent=2)
        with open(out_trades, 'w') as f:
            json.dump({"trades": []}, f, indent=2)
        return

    poor_thr, good_thr = compute_vorp_per_dollar_thresholds(teams, projections, replacement)
    elite_thr = compute_elite_thresholds(projections)

    buyouts: List[Dict] = []
    # Apply buyouts first (1-year UFA poor value)
    for t in teams:
        remaining_players: List[Dict] = []
        for pl in t.get('players', []):
            years = int(pl.get('years') or 0)
            salary = int(pl.get('salary') or 0)
            if years == 1 and (pl.get('future_fa') == 'UFA') and salary > 0:
                v = projections.get(name_norm(pl.get('player') or ''))
                pos = (v or {}).get('pos') or 'W'
                rep = replacement.get(pos, 0.0)
                vorp = (v['fp'] - rep) if v else 0.0
                vpd = (vorp / salary) if (vorp and salary > 0) else 0.0
                # Elite guardrail: avoid buying out elite unless a better elite or younger near-elite is affordable
                is_elite = bool(v and (v['fp'] >= elite_thr.get(pos, 9e9)))
                allow_elite_buyout = False
                elite_note = None
                if is_elite:
                    # Budget equals freed salary + current cap_space
                    budget = int(t.get('cap_space') or 0) + int(salary)
                    K = {"C": 0.21, "W": 0.18, "D": 0.13, "G": 0.03}
                    # Search candidate upgrades within same position family
                    def same_family(p1, p2):
                        if p1 in ("C","W") and p2 in ("C","W"):
                            return True
                        return p1 == p2
                    for fa in free_agents_global:
                        key = name_norm(fa.get('player') or '')
                        vv = projections.get(key)
                        if not vv or not same_family(pos, vv.get('pos') or 'W'):
                            continue
                        vrep = replacement.get(vv.get('pos') or 'W', 0.0)
                        vvorp = max(0.0, (vv.get('fp') or 0.0) - vrep)
                        est_price = max(2, int(round(2 + K.get(vv.get('pos') or 'W', 0.15) * vvorp)))
                        if est_price > budget:
                            continue
                        # Clear upgrade: >=10% FP
                        if (vv.get('fp') or 0.0) >= (v.get('fp') or 0.0) * 1.10:
                            allow_elite_buyout = True
                            elite_note = f"target {fa.get('player')} est_price {est_price} >=10% FP upgrade"
                            break
                # Buy out if at/below replacement (vorp <= 0) or poor vorp per dollar
                should_buyout = (vorp <= 0) or (vpd > 0 and vpd < poor_thr)
                if (is_elite and allow_elite_buyout and should_buyout) or ((not is_elite) and should_buyout):
                    # Buyout: remove player; no cap hit for 1-year per rules
                    t['cap_commit'] = max(0, int(t.get('cap_commit') or 0) - salary)
                    t['cap_space'] = int(t.get('cap_space') or 0) + salary
                    # Re-introduce the player into the free agent pool as current UFA for the auction
                    free_agents_global.append({
                        'team': t['team_name'],
                        'owner': t.get('owner_name'),
                        'player': pl.get('player'),
                        'pos': (pl.get('pos') or '').upper(),
                        'last_salary': float(salary),
                        'fa_type': 'UFA',
                    })
                    buyouts.append({
                        'team': t['team_name'],
                        'player': pl.get('player'),
                        'salary': salary,
                        'cap_hit': 0,
                        'reintroduced_to_auction': True,
                        'reason': f'vorp {vorp:.2f} (pos {pos}, rep {rep:.2f}); vorp_per_$ {vpd:.2f} < thr {poor_thr:.2f}' + (f"; elite_ok: {elite_note}" if is_elite and elite_note else ''),
                    })
                    continue
            # Consider multi-year buyouts (2+ years): add cap hit entry
            if years >= 2 and (pl.get('future_fa') == 'UFA') and int(pl.get('salary') or 0) > 0:
                v = projections.get(name_norm(pl.get('player') or ''))
                pos = (v or {}).get('pos') or 'W'
                rep = replacement.get(pos, 0.0)
                vorp = (v['fp'] - rep) if v else 0.0
                vpd = (vorp / salary) if (vorp and salary > 0) else 0.0
                should_buyout = (vorp <= 0) or (vpd > 0 and vpd < poor_thr)
                if should_buyout:
                    # remove full salary first
                    t['cap_commit'] = max(0, int(t.get('cap_commit') or 0) - salary)
                    t['cap_space'] = int(t.get('cap_space') or 0) + salary
                    import math
                    cap_hit = int(math.ceil(salary / 2))
                    # add cap hit entry
                    cap_entry = {
                        'player': f'z-CAPHIT Buyout {pl.get("player")}',
                        'display_name': f'z-CAPHIT Buyout {pl.get("player")}',
                        'pos': (pl.get('pos') or '').upper(),
                        'salary': cap_hit,
                        'years': 1,
                        'is_cap_hit': True,
                    }
                    t['players'].append(cap_entry)
                    t['cap_commit'] = int(t.get('cap_commit') or 0) + cap_hit
                    t['cap_space'] = max(0, int(t.get('cap_space') or 0) - cap_hit)
                    buyouts.append({
                        'team': t['team_name'],
                        'player': pl.get('player'),
                        'salary': salary,
                        'cap_hit': cap_hit,
                        'reintroduced_to_auction': True,
                        'reason': f'multi-year buyout; cap_hit half rounded up',
                    })
                    continue
                # If elite and not allowed, keep
                if is_elite and not allow_elite_buyout:
                    remaining_players.append(pl)
                    continue
            remaining_players.append(pl)
        t['players'] = remaining_players

    # Trades: teams with cap_space < 20 and generally OK value try to move largest contract
    # Build receivers list sorted by cap_space desc
    trades: List[Dict] = []
    def refresh_receivers():
        return sorted([x for x in teams if int(x.get('cap_space') or 0) > 0], key=lambda x: int(x.get('cap_space') or 0), reverse=True)

    receivers = refresh_receivers()
    # Draft pick values and team outlooks influence trade offers
    pick_vals, team_pick_vals = _compute_pick_values_from_stage3(stage3_path)
    team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)
    for sender in sorted(teams, key=lambda x: int(x.get('cap_space') or 0)):
        if int(sender.get('cap_space') or 0) >= 20:
            continue
        # choose largest remaining contract (years>0)
        carry = [pl for pl in sender.get('players', []) if int(pl.get('years') or 0) > 0 and int(pl.get('salary') or 0) > 0]
        if not carry:
            continue
        carry.sort(key=lambda x: int(x.get('salary') or 0), reverse=True)
        asset = carry[0]
        # Check value: only trade if value per $ is not poor (i.e., >= poor_thr)
        v = projections.get(name_norm(asset.get('player') or ''))
        salary = int(asset.get('salary') or 0)
        vpd = (v['fp'] / salary) if (v and salary > 0) else 0.0
        if vpd < poor_thr:
            continue
        # find receiver with enough space
        recv = next((r for r in receivers if r['team_name'] != sender['team_name'] and int(r.get('cap_space') or 0) >= salary), None)
        if not recv:
            continue
        # execute trade
        sender['players'].remove(asset)
        recv['players'].append(asset)
        sender['cap_commit'] = max(0, int(sender.get('cap_commit') or 0) - salary)
        sender['cap_space'] = int(sender.get('cap_space') or 0) + salary
        recv['cap_commit'] = int(recv.get('cap_commit') or 0) + salary
        recv['cap_space'] = max(0, int(recv.get('cap_space') or 0) - salary)
        trade_entry = {
            'from_team': sender['team_name'],
            'to_team': recv['team_name'],
            'player': asset.get('player'),
            'salary': salary,
            'note': f'cap_space<{20}, vpd {vpd:.2f} >= poor_thr {poor_thr:.2f}'
        }
        # If sender is win_now, allow attaching their rookie pick as sweetener
        outlook = team_outlooks.get(sender['team_name'])
        if outlook == 'win_now':
            pv = float(team_pick_vals.get(sender['team_name'], 0.0) or 0.0)
            if pv > 0:
                trade_entry['attached_pick'] = {'pick_value_tp_nhle': pv}
        trades.append(trade_entry)
        receivers = refresh_receivers()

    # Persist outputs and updated stage1
    with open(out_buyouts, 'w') as f:
        json.dump({"thresholds": {"poor_vorp_per_dollar": poor_thr}, "buyouts": buyouts}, f, indent=2)
    with open(out_trades, 'w') as f:
        json.dump({"trades": trades, "pick_values": pick_vals, "team_pick_values": team_pick_vals, "team_outlooks": team_outlooks}, f, indent=2)
    # Update stage1 file
    stage1['teams'] = teams
    stage1['free_agents'] = free_agents_global
    # Recompute caps summary maps from teams to keep stage1 consistent
    new_commit = {t['team_name']: int(t.get('cap_commit') or 0) for t in teams}
    new_caps = {t['team_name']: int(t.get('cap_space') or 0) for t in teams}
    stage1['caps'] = {"team_caps": new_caps, "commit": new_commit}
    with open(update_stage1_path, 'w') as f:
        json.dump(stage1, f, indent=2)


def load_stage1_rollforward_path() -> str:
    return os.path.abspath(os.path.join(OUTPUT_DIR, 'stage1_rollforward.json'))


def main():
    ensure_output_dir()
    engine_local = create_engine(RAILWAY_DB, pool_pre_ping=True)
    engine_ext = create_engine(EXT_DB, pool_pre_ping=True)

    # Stage 1: roll-forward & RFA/UFA, and include team rosters
    state1_caps_commit, free_agents, teams_list = roll_forward_and_classify(engine_local, engine_ext, season_year=2024)
    stage1_obj = {"caps": state1_caps_commit, "free_agents": free_agents, "teams": teams_list}
    with open(os.path.join(OUTPUT_DIR, "stage1_rollforward.json"), "w") as f:
        json.dump(stage1_obj, f, indent=2)
    # Stage 1 outlook snapshot
    try:
        _write_team_outlooks_generic(teams_list, load_2025_26_projections(), os.path.join(OUTPUT_DIR, 'stage3_rookie_draft.json'), os.path.join(OUTPUT_DIR, 'stage1_team_outlooks.json'))
    except Exception:
        pass

    # Load current-season projections and replacement
    projections = load_2025_26_projections()
    replacement = compute_replacement(projections)

    # Stage 2: buyouts for poor 1-yr UFA value and pre-draft trades for low-cap teams
    stage1_path = load_stage1_rollforward_path()
    stage2_buyouts_path = os.path.join(OUTPUT_DIR, "stage2_buyouts.json")
    stage2_trades_path = os.path.join(OUTPUT_DIR, "stage2_trades.json")
    stage2_stage1_update_path = stage1_path
    stage3_path = os.path.join(OUTPUT_DIR, 'stage3_rookie_draft.json')
    # Stage 2 outlook snapshot (pre-actions)
    try:
        _write_team_outlooks_generic(teams_list, load_2025_26_projections(), stage3_path, os.path.join(OUTPUT_DIR, 'stage2_team_outlooks_pre.json'))
    except Exception:
        pass
    stage2_buyouts_and_trades(stage1_path, projections, replacement, stage2_buyouts_path, stage2_trades_path, stage2_stage1_update_path, stage3_path)
    # Reload teams after Stage 2 and write post snapshot
    try:
        with open(load_stage1_rollforward_path(), 'r') as f:
            stage1_after2 = json.load(f)
        _write_team_outlooks_generic(stage1_after2.get('teams', []), projections, stage3_path, os.path.join(OUTPUT_DIR, 'stage2_team_outlooks_post.json'))
    except Exception:
        pass

    # Reload updated stage1 (after Stage 2) for caps and FAs
    with open(load_stage1_rollforward_path(), 'r') as f:
        stage1_after2 = json.load(f)
    caps_for_auction = stage1_after2.get("caps", {}).get("team_caps", state1_caps_commit["team_caps"])
    free_agents_for_auction = stage1_after2.get("free_agents", free_agents)
    # Stage 4 outlook snapshot (pre-auction)
    try:
        _write_team_outlooks_generic(stage1_after2.get('teams', []), projections, os.path.join(OUTPUT_DIR, 'stage3_rookie_draft.json'), os.path.join(OUTPUT_DIR, 'stage4_team_outlooks_pre.json'))
    except Exception:
        pass

    # Stage 4: auction (needs-aware, cap compliant)
    auction_results, caps_after, auction_state = auction_simulation(caps_for_auction, free_agents_for_auction, projections, replacement)
    with open(os.path.join(OUTPUT_DIR, "stage4_auction.json"), "w") as f:
        json.dump({"order": NOMINATION_ORDER, "results": auction_results, "caps_after": caps_after, "state": auction_state}, f, indent=2)
    # Stage 4 outlook snapshot (post-auction)
    try:
        # Construct simple rosters from auction results to approximate outlook
        teams_after4 = []
        caps_map = {t: float(caps_after[t]) for t in caps_after}
        by_team = {t: [] for t in caps_after}
        for r in auction_results:
            by_team.setdefault(r['team'], []).append({'player': r['player'], 'pos': r.get('pos'), 'salary': r.get('price'), 'years': 3})
        for t in by_team:
            teams_after4.append({'team_name': t, 'players': by_team[t], 'cap_space': caps_map.get(t, 0)})
        _write_team_outlooks_generic(teams_after4, projections, os.path.join(OUTPUT_DIR, 'stage3_rookie_draft.json'), os.path.join(OUTPUT_DIR, 'stage4_team_outlooks_post.json'))
    except Exception:
        pass

    # Stage 5: waivers to hit exactly $100
    waiver_signings = waiver_to_exact_100(caps_after)
    with open(os.path.join(OUTPUT_DIR, "stage5_waivers.json"), "w") as f:
        json.dump({"signings": waiver_signings}, f, indent=2)

    # Stage 6: regular season totals (deterministic baseline)
    season_summary = season_totals_from_rosters(auction_results, waiver_signings, projections)
    with open(os.path.join(OUTPUT_DIR, "stage6_season.json"), "w") as f:
        json.dump(season_summary, f, indent=2)

    # Stage 3: identify 2025 draft pick ownership and update rookie draft file
    md_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '2024_rosters.md'))
    pick_map = find_2025_pick_ownership_from_md(md_path)
    update_stage3_rookie_draft(load_stage1_rollforward_path(), stage3_path, pick_map)
    # Apply NHLe factors to rookie pool
    nhle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'nhle_2025.json'))
    apply_nhle_to_stage3(stage3_path, nhle_path)
    simulate_rookie_draft_best_available(stage3_path)

    print("Simulation stages written to:", OUTPUT_DIR)

    # Optional: rebuild GM profiles from 2022/2023 sources if present
    try:
        rebuild_gm_profiles()
    except Exception:
        pass


if __name__ == "__main__":
    main()
