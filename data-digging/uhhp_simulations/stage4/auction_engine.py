import os
import json
from typing import Dict, List, Tuple, Callable

from ..run_simulation import (
	load_2025_26_projections,
	compute_replacement,
	waiver_to_exact_100,
    _compute_team_outlooks,
    compute_elite_thresholds,
)


def _name_norm(s: str) -> str:
	import unicodedata
	return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()


# Fixed UHHP roster requirements (allocate F as 2C + 2W)
REQ_SLOTS = {"G": 2, "C": 4, "W": 5, "D": 4}

# Nomination order (stable baseline; can be overridden later from input if present)
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


def _pos_bucket(raw: str) -> str:
	p = (raw or '').upper()
	if p in ("C", "W", "D", "G"):
		return p
	if p in ("L", "R", "LW", "RW", "F"):
		return "W"
	return "W"


def _load_clusters_map() -> Dict[str, Tuple[str, int]]:
	"""Load tiers from outputs/fp_clusters_tiers8.json and return name->(pos,tier)."""
	try:
		base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
		path = os.path.join(base, 'fp_clusters_tiers8.json')
		with open(path, 'r') as f:
			data = json.load(f)
		m: Dict[str, Tuple[str, int]] = {}
		for pos in ('C', 'W', 'D', 'G'):
			info = data.get(pos, {})
			for a in info.get('assignments', []):
				name = _name_norm(a.get('name') or '')
				try:
					tier = int(a.get('cluster') or 5)
				except Exception:
					tier = 5
				m.setdefault(name, (pos, tier))
		return m
	except Exception:
		return {}


def _compute_salary_guardrails() -> Dict[Tuple[str, int], Dict[str, float]]:
	"""Compute salary guardrails (min/p25/median/p75/max) by (pos, tier) from 2024 rosters."""
	try:
		clusters = _load_clusters_map()
		base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
		rosters_path = os.path.join(base, '2024_rosters.json')
		with open(rosters_path, 'r') as f:
			teams = (json.load(f) or {}).get('teams', {})
		from collections import defaultdict
		buckets: Dict[Tuple[str, int], List[float]] = defaultdict(list)
		def extract_name(it: Dict) -> str:
			nm = it.get('player_full_name')
			if nm:
				return _name_norm(nm)
			dn = it.get('display_name') or ''
			if ',' in dn:
				last, rest = dn.split(',', 1)
				first = (rest.strip().split() or [''])[0]
				return _name_norm(f"{first} {last}")
			p = it.get('player') or ''
			parts = p.split()
			if len(parts) >= 2:
				return _name_norm(f"{parts[0]} {parts[-1]}")
			return _name_norm(p)
		for team in teams.values():
			for it in team.get('players', []):
				try:
					sal = it.get('salary')
					if sal is None:
						continue
					nm = extract_name(it)
					pos_tier = clusters.get(nm)
					if not pos_tier:
						continue
					buckets[pos_tier].append(float(sal))
				except Exception:
					continue
		import statistics
		guard: Dict[Tuple[str, int], Dict[str, float]] = {}
		for pos in ('C', 'W', 'D', 'G'):
			for t in range(6):
				arr = sorted(buckets.get((pos, t), []))
				if not arr:
					guard[(pos, t)] = {"min": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "max": 0.0}
					continue
				q25 = arr[len(arr)//4]
				med = statistics.median(arr)
				q75 = arr[(3*len(arr))//4]
				guard[(pos, t)] = {"min": float(arr[0]), "p25": float(q25), "median": float(med), "p75": float(q75), "max": float(arr[-1])}
		return guard
	except Exception:
		# Fallback defaults if needed
		g: Dict[Tuple[str, int], Dict[str, float]] = {}
		for pos in ('C', 'W', 'D', 'G'):
			for t in range(6):
				g[(pos, t)] = {"min": 2.0, "p25": 2.0, "median": 3.0, "p75": 6.0, "max": 10.0}
		return g


def _initial_filled_from_roster(teams: List[Dict]) -> Dict[str, Dict[str, int]]:
	filled: Dict[str, Dict[str, int]] = {}
	for t in teams:
		name = t.get('team_name')
		cnt = {"G": 0, "C": 0, "W": 0, "D": 0}
		for pl in t.get('players', []):
			if int(pl.get('years') or 0) <= 0:
				continue
			pos = _pos_bucket(pl.get('pos'))
			if pos in cnt:
				cnt[pos] += 1
		filled[name] = cnt
	return filled


def _rookie_tiebreak_order(rookie_draft: Dict) -> List[str]:
	# Build tiebreak order from earliest rookie pick of each team; lower pick wins ties
	order: List[Tuple[int, str]] = []
	seen = set()
	for pk in sorted(rookie_draft.get('picks', []), key=lambda x: int(x.get('pick') or 0)):
		team = pk.get('team_name')
		if not team or team in seen:
			continue
		seen.add(team)
		try:
			order.append((int(pk.get('pick') or 0), team))
		except Exception:
			continue
	order.sort(key=lambda x: x[0])
	return [t for _, t in order]


def _compute_needs_snapshot(filled: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
	return {t: {p: max(0, REQ_SLOTS[p] - int(v.get(p, 0))) for p in REQ_SLOTS} for t, v in filled.items()}


def _recompute_replacement_dynamic(pool: List[Dict]) -> Dict[str, float]:
	# Compute replacement levels from still-available pool
	pos_to = {"C": [], "W": [], "D": [], "G": []}
	for p in pool:
		pos = p.get('pos') or 'W'
		if pos not in pos_to:
			continue
		pos_to[pos].append(float(p.get('fp') or 0.0))
	for arr in pos_to.values():
		arr.sort(reverse=True)
	rep: Dict[str, float] = {}
	# Use total required slots across league as cutoff proxy
	for pos in ("C", "W", "D", "G"):
		pool_list = pos_to[pos]
		k = max(1, min(len(pool_list), REQ_SLOTS[pos] * 12))
		rep[pos] = pool_list[k - 1] if pool_list else 0.0
	return rep


def simulate_from_input(auction_input_path: str, out_dir: str) -> Tuple[str, str]:
	"""Run the auction using the consolidated input file and write outputs.
	Returns tuple of (stage4_out_path, stage5_out_path).
	"""
	os.makedirs(out_dir, exist_ok=True)
	with open(auction_input_path, 'r') as f:
		inp = json.load(f)

	teams: List[Dict] = inp.get('teams', [])
	free_agents_in: List[Dict] = inp.get('free_agents', [])
	rookie_draft = inp.get('rookie_draft', {})
	caps_map = (inp.get('caps') or {}).get('team_caps') or {t['team_name']: int(t.get('cap_space') or 0) for t in teams}

	# Load forecasts and baseline replacement
	projections = load_2025_26_projections()
	baseline_rep = compute_replacement(projections)
	elite_thresholds = compute_elite_thresholds(projections)

	# Build pool with FP and initial VORP
	pool: List[Dict] = []
	for fa in free_agents_in:
		key = _name_norm(fa.get('player') or '')
		v = projections.get(key)
		pos_raw = (v or {}).get('pos') or (fa.get('pos') or '')
		pos = _pos_bucket(pos_raw)
		fp = float((v or {}).get('fp') or baseline_rep.get(pos, 0.0))
		pool.append({
			"player": fa.get('player'),
			"player_id": fa.get('player_id'),
			"pos": pos,
			"type": (fa.get('fa_type') or '').upper(),
			"owner_team": fa.get('team'),
			"fp": fp,
		})
	# Sort stable by FP desc then name
	pool.sort(key=lambda x: (-x['fp'], x['player'] or ''))

	# Caps and roster state
	caps: Dict[str, float] = {t: float(caps_map.get(t, 0.0)) for t in caps_map}
	filled = _initial_filled_from_roster(teams)

	# Tier map and empirical guardrails
	clusters_map = _load_clusters_map()
	guardrails = _compute_salary_guardrails()

	# Global budget scaling: decline values as money is spent
	initial_total_budget = sum(float(v) for v in caps.values()) or 1.0

	# Compute team pick values from rookie draft (approx NHLe value for their pick)
	def _compute_team_pick_vals_from_rd(rd: Dict) -> Dict[str, float]:
		try:
			avail = rd.get('available_players', []) or []
			picks = rd.get('picks', []) or []
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
				try:
					pick_no = int(pk.get('pick') or i)
				except Exception:
					pick_no = i
				pick_vals[pick_no] = round(val, 2)
			team_vals: Dict[str, float] = {}
			for pk in picks:
				team = pk.get('team_name')
				try:
					pno = int(pk.get('pick') or 0)
				except Exception:
					pno = 0
				if team:
					team_vals[team] = pick_vals.get(pno, 0.0)
			return team_vals
		except Exception:
			return {}

	team_pick_vals = _compute_team_pick_vals_from_rd(rookie_draft)
	team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)

	# Ingest Stage 4 pre-outlooks and positional budgets for shopping plan
	def _load_json_if(path: str) -> Dict:
		try:
			with open(path, 'r') as f:
				return json.load(f)
		except Exception:
			return {}
	outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
	pre_path = os.path.join(outputs_dir, 'stage4_team_outlooks_pre.json')
	pre_outlooks = _load_json_if(pre_path)
	blueprint_needs = pre_outlooks.get('blueprint_needs') or {}
	bp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gm', 'positional_budgets.json'))
	bp_cfg = _load_json_if(bp_path)
	bp_caps = (bp_cfg.get('caps') or {})
	single_player_max = int(bp_caps.get('single_player_max') or 22)
	reserve_per_slot = int(bp_caps.get('reserve_per_empty_slot') or 2)

	# Build per-team shopping plan: elite targets and positional spend deltas
	shopping_plan: Dict[str, Dict] = {}
	# Helper to count current tier-0 elites on a team roster
	def _count_current_elites(team_entry: Dict) -> int:
		cnt = 0
		for pl in team_entry.get('players', []):
			try:
				if int(pl.get('years') or 0) <= 0:
					continue
				nm = _name_norm(pl.get('player') or pl.get('player_full_name') or pl.get('display_name') or '')
				pos_tier = clusters_map.get(nm)
				if not pos_tier:
					continue
				_, tier = pos_tier
				if int(tier) == 0:
					cnt += 1
			except Exception:
				continue
		return cnt
	for t in teams:
		name = t.get('team_name')
		bp = blueprint_needs.get(name) or {}
		# Use cluster-based elite count from current roster
		current_elite = _count_current_elites(t)
		ol = team_outlooks.get(name)
		if ol == 'win_now':
			target_elite = 2
		elif ol == 'win_next':
			target_elite = 1
		else:
			# rebuild
			target_elite = 1
		elite_remaining = max(0, target_elite - current_elite)
		pos_targets = (bp.get('adjusted_targets') or bp.get('position_spend_vs_targets') or {})
		pos_deltas = {k: int((pos_targets.get(k) or {}).get('delta_to_min') or 0) for k in ('F','D','G')}
		shopping_plan[name] = {
			'outlook': ol,
			'elite_remaining': elite_remaining,
			'pos_deltas': pos_deltas,
		}

	# Private value weights per position
	K = {"C": 0.21, "W": 0.18, "D": 0.13, "G": 0.03}

	# Tiebreaker order from rookie draft
	tiebreak_order = _rookie_tiebreak_order(rookie_draft)
	# Fallback to nomination order if rookie not available
	if not tiebreak_order:
		tiebreak_order = NOMINATION_ORDER

	def remaining_slots_after(team: str, pos: str) -> int:
		f = dict(filled.get(team, {}))
		if pos in f:
			f[pos] = min(REQ_SLOTS[pos], f[pos] + 1)
		total_req = sum(REQ_SLOTS.values())
		total_filled = sum(min(f.get(p, 0), REQ_SLOTS[p]) for p in REQ_SLOTS)
		return max(0, total_req - total_filled)

	def private_value(team: str, cand: Dict, rep_levels: Dict[str, float]) -> float:
		pos = cand['pos']
		need = max(0, REQ_SLOTS[pos] - int(filled.get(team, {}).get(pos, 0)))
		need_share = (need / max(1, REQ_SLOTS[pos]))
		vorp = max(0.0, float(cand['fp']) - float(rep_levels.get(pos, 0.0)))
		# Outlook aggressiveness: win_now > win_next > rebuild
		ol = team_outlooks.get(team)
		if ol == 'win_now':
			aggr = 1.20
		elif ol == 'win_next':
			aggr = 1.05
		else:
			aggr = 0.92
		pv = K.get(pos, 0.15) * vorp * (1.0 + 0.5 * need_share) * aggr
		# Shopping plan boosts
		sp = shopping_plan.get(team) or {}
		elite_left = int(sp.get('elite_remaining') or 0)
		# Elite test for this candidate
		is_elite = False
		try:
			cand_name_key = _name_norm(cand.get('player') or '')
			cand_pos, cand_tier = clusters_map.get(cand_name_key, (pos, 5))
			is_elite = (int(cand_tier) == 0)
		except Exception:
			is_elite = False
		if is_elite and elite_left > 0:
			pv *= 1.30
		# Positional spend gaps
		pos_delta_map = (sp.get('pos_deltas') or {})
		bucket = 'F' if pos in ('C','W') else pos
		if int(pos_delta_map.get(bucket, 0)) > 0:
			pv *= 1.12
		# Rebuild: slight RFA/value preference
		if ol == 'rebuild':
			if (cand.get('type') or '').upper() == 'RFA':
				pv *= 1.10
			if pv <= 8.0:
				pv *= 1.08
		# Tier-aware damping to empirical bands
		name_key = _name_norm(cand.get('player') or '')
		_, tier = clusters_map.get(name_key, (pos, 5))
		gr = guardrails.get((pos, tier), {"p75": 6.0, "max": 10.0})
		target_max = float(gr.get('max', 10.0)) if is_elite else float(gr.get('p75', 6.0))
		pv = min(pv, max(2.0, target_max))
		return pv

	results: List[Dict] = []
	state_log = {
		"start_caps": {t: float(caps[t]) for t in caps},
		"start_needs": _compute_needs_snapshot(filled),
		"start_outlooks": dict(team_outlooks),
		"pick_states": {},
	}

	taken = set()
	order = NOMINATION_ORDER

	def nominate_round(filter_func: Callable[[Dict], bool], phase: str, max_picks: int = None) -> None:
		nonlocal pool, caps, filled, results, state_log, taken
		picks_made = 0
		while True:
			progress = False
			for team in order:
				# recompute dynamic replacement from remaining pool
				rep_dyn = _recompute_replacement_dynamic([p for p in pool if p['player'] not in taken])
				# compute global budget ratio for this pick
				current_total_budget = sum(float(v) for v in caps.values())
				budget_ratio = max(0.0, min(1.0, current_total_budget / initial_total_budget))
				chosen = None
				for cand in pool:
					if cand['player'] in taken:
						continue
					if not filter_func(cand):
						continue
					rem_after = remaining_slots_after(team, cand['pos'])
					cap = float(caps.get(team, 0.0))
					max_bid_allowed = int(max(0, cap - 2 * rem_after))
					if max_bid_allowed < 2:
						continue
					# starting bid from team pv (tier-aware) scaled by budget ratio
					pv = private_value(team, cand, rep_dyn)
					pv *= budget_ratio
					start_price = max(2, int(round(pv)))
					if start_price > max_bid_allowed:
						continue
					chosen = (cand, start_price, budget_ratio)
					break
				if not chosen:
					continue
				cand, price, budget_ratio_used = chosen
				# Competitive bidding
				high = price
				leaders = [team]
				for rival in order:
					if rival == team:
						continue
					rep_dyn_r = rep_dyn  # same rep snapshot for all rivals in this bid
					rv = private_value(rival, cand, rep_dyn_r) * budget_ratio_used
					rem_after_r = remaining_slots_after(rival, cand['pos'])
					cap_r = float(caps.get(rival, 0.0))
					max_bid_r = int(max(0, cap_r - 2 * rem_after_r))
					bid = max(2, int(round(rv)))
					if bid > max_bid_r:
						bid = 0
					if cap_r >= bid:
						if bid > high:
							high = bid
							leaders = [rival]
						elif bid == high and bid > 0:
							leaders.append(rival)
				# RFA owner match opportunity
				if (cand.get('type') == 'RFA') and (cand.get('owner_team') in caps):
					owner = cand['owner_team']
					rem_after_o = remaining_slots_after(owner, cand['pos'])
					cap_o = float(caps.get(owner, 0.0))
					max_bid_o = int(max(0, cap_o - 2 * rem_after_o))
					owner_bid = max(2, int(round(private_value(owner, cand, rep_dyn) * budget_ratio_used)))
					if owner_bid > max_bid_o:
						owner_bid = 0
					if cap_o >= high and owner_bid >= high:
						if high > 0:
							leaders = [owner]
				# Tiebreak via rookie order if needed
				if len(leaders) > 1:
					for tb in tiebreak_order:
						if tb in leaders:
							leaders = [tb]
							break
				winner = leaders[0]
				# Award if affordable under reserve (respect single-player max implicitly via pv/max_bid)
				caps[winner] = max(0.0, caps[winner] - float(high))
				taken.add(cand['player'])
				# Update filled
				if cand['pos'] in filled[winner]:
					filled[winner][cand['pos']] = min(REQ_SLOTS[cand['pos']], filled[winner][cand['pos']] + 1)
				# Update shopping plan elite if acquired
				try:
					nm = _name_norm(cand.get('player') or '')
					_, tier = clusters_map.get(nm, (cand['pos'], 5))
					if int(tier) == 0 and winner in shopping_plan and int(shopping_plan[winner].get('elite_remaining') or 0) > 0:
						shopping_plan[winner]['elite_remaining'] = int(shopping_plan[winner]['elite_remaining']) - 1
				except Exception:
					pass
				pick_idx = len(results) + 1
				results.append({
					"team": winner,
					"player": cand['player'],
					"player_id": cand.get('player_id'),
					"pos": cand['pos'],
					"type": cand['type'],
					"price": int(high),
					"years": 3,
					"phase": phase,
				})
				# Update working team roster for outlook recompute
				for tt in teams:
					if tt.get('team_name') == winner:
						pl_ent = {
							'player': cand['player'],
							'pos': cand['pos'],
							'years': 3,
							'salary': int(high),
						}
						# Avoid duplicating if somehow present
						already = any((x.get('player') == cand['player']) for x in tt.get('players', []))
						if not already:
							tt.setdefault('players', []).append(pl_ent)
						break
				# Recompute outlooks with the new roster snapshot
				team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)
				state_log["pick_states"][str(pick_idx)] = {
					"caps": {t: float(caps[t]) for t in caps},
					"needs": _compute_needs_snapshot(filled),
					"shopping_plan": {tm: {"elite_remaining": int((shopping_plan.get(tm) or {}).get('elite_remaining') or 0)} for tm in shopping_plan},
					"outlooks": dict(team_outlooks),
					"budget_ratio": float(budget_ratio_used),
				}
				picks_made += 1
				progress = True
				if max_picks is not None and picks_made >= max_picks:
					return
			if not progress:
				return

	# Phases per agreed design
	# 1–12 superstar (UFA+RFA)
	nominate_round(lambda c: c['type'] in ('UFA', 'RFA'), phase="superstar", max_picks=len(order))
	# 13–24 UFA only
	nominate_round(lambda c: c['type'] == 'UFA', phase="ufa", max_picks=len(order))
	# 25–45 RFA only (up to 21 picks)
	nominate_round(lambda c: c['type'] == 'RFA', phase="rfa", max_picks=21)
	# Auction ends here; remaining RFAs handled in post-RFA decisions below

	# Post-RFA decisions: owners may sign remaining RFAs at $2 (3 years) if affordable
	rep_end = _recompute_replacement_dynamic([p for p in pool if p['player'] not in taken])
	rfa_outcomes = {"matched": [], "dropped": []}
	for cand in pool:
		if cand['player'] in taken:
			continue
		if cand.get('type') != 'RFA':
			continue
		owner = cand.get('owner_team')
		if owner not in caps:
			continue
		rem_after = remaining_slots_after(owner, cand['pos'])
		max_bid_allowed = int(max(0, float(caps.get(owner, 0.0)) - 2 * rem_after))
		if max_bid_allowed >= 2:
			caps[owner] = max(0.0, float(caps[owner]) - 2.0)
			taken.add(cand['player'])
			if cand['pos'] in filled[owner]:
				filled[owner][cand['pos']] = min(REQ_SLOTS[cand['pos']], filled[owner][cand['pos']] + 1)
			pick_idx = len(results) + 1
			results.append({
				"team": owner,
				"player": cand['player'],
				"player_id": cand.get('player_id'),
				"pos": cand['pos'],
				"type": "RFA",
				"price": 2,
				"years": 3,
				"phase": "post_rfa_match",
			})
			rfa_outcomes["matched"].append({"player": cand['player'], "team": owner, "price": 2})
			# Update team outlooks after post-RFA decision as well
			team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)
			state_log["pick_states"][str(pick_idx)] = {
				"caps": {t: float(caps[t]) for t in caps},
				"needs": _compute_needs_snapshot(filled),
				"outlooks": dict(team_outlooks),
			}
		else:
			# Explicit drop outcome for RFA not matched
			rfa_outcomes["dropped"].append({"player": cand['player'], "team": owner})
			# Record drop in results as a decision entry
			pick_idx = len(results) + 1
			results.append({
				"team": owner,
				"player": cand['player'],
				"player_id": cand.get('player_id'),
				"pos": cand['pos'],
				"type": "RFA",
				"price": 0,
				"years": 0,
				"phase": "post_rfa_drop",
				"decision": "dropped",
			})

	# Write outputs
	stage4_path = os.path.join(out_dir, 'stage4_auction.json')
	with open(stage4_path, 'w') as f:
		json.dump({
			"order": order,
			"results": results,
			"caps_after": caps,
			"state": state_log,
			"rfa_outcomes": rfa_outcomes,
		}, f, indent=2)

	# Stage 5: waivers to exact $100
	stage5_signings = waiver_to_exact_100(caps)
	stage5_dir = os.path.abspath(os.path.join(out_dir, '..', 'stage5'))
	os.makedirs(stage5_dir, exist_ok=True)
	stage5_path = os.path.join(stage5_dir, 'stage5_waivers.json')
	with open(stage5_path, 'w') as f:
		json.dump({"signings": stage5_signings}, f, indent=2)

	return stage4_path, stage5_path


