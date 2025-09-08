"""
Stage 2: Buyouts and Trades based on VORP thresholds and outlooks.
Writes stage2_buyouts.json and stage2_trades.json.
"""
import os
import json
from sqlalchemy import create_engine

from ..run_simulation import (
    RAILWAY_DB,
    EXT_DB,
    load_stage1_rollforward_path,
    load_2025_26_projections,
    compute_replacement,
    stage2_buyouts_and_trades,
    _compute_team_outlooks,
    _compute_pick_values_from_stage3,
    compute_elite_thresholds,
)


def run(stage1_path: str | None = None) -> tuple[str, str]:
    engine_local = create_engine(RAILWAY_DB, pool_pre_ping=True)
    _ = create_engine(EXT_DB, pool_pre_ping=True)
    projections = load_2025_26_projections()
    replacement = compute_replacement(projections)
    s1 = stage1_path or load_stage1_rollforward_path()
    out_dir = os.path.join(os.path.dirname(s1), '..', 'stage2')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    # Pre-step: compute team outlooks (win_now | win_next | rebuild) before Stage 2
    stage3_path = os.path.join(os.path.dirname(out_dir), 'stage3', 'stage3_rookie_draft.json')
    os.makedirs(os.path.dirname(stage3_path), exist_ok=True)
    try:
        with open(s1, 'r') as f:
            stage1_obj = json.load(f)
        teams = stage1_obj.get('teams', [])
    except Exception:
        teams = []
    _pick_vals, team_pick_vals = _compute_pick_values_from_stage3(stage3_path)
    # Load positional budget rails and perform a blueprint assessment mapping current roster spend to targets
    budgets_path = os.path.join(os.path.dirname(__file__), '..', 'gm', 'positional_budgets.json')
    budgets_path = os.path.abspath(budgets_path)
    blueprint = {}
    try:
        with open(budgets_path, 'r') as f:
            blueprint = json.load(f)
    except Exception:
        blueprint = {}
    thresholds = compute_elite_thresholds(projections)
    replacement_map = compute_replacement(projections)
    def _norm_name(s: str) -> str:
        import unicodedata
        return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii').strip().lower()
    def _team_spend(t):
        s = {"F": 0, "D": 0, "G": 0}
        for pl in t.get('players', []):
            try:
                sal = int(pl.get('salary') or 0)
            except Exception:
                sal = 0
            pos = (pl.get('pos') or '').upper()
            if pos == 'D':
                s['D'] += sal
            elif pos == 'G':
                s['G'] += sal
            else:
                s['F'] += sal
        return s
    def _pos_bucket(p: str) -> str:
        p = (p or '').upper()
        if p in ('C','W','D','G'):
            return p
        if p in ('L','R','LW','RW','F'):
            return 'W'
        return 'W'
    def _player_fp_and_pos(pname: str, fallback_pos: str):
        v = projections.get(_norm_name(pname or ''))
        if v:
            return float(v.get('fp') or 0.0), _pos_bucket(v.get('pos') or fallback_pos)
        return 0.0, _pos_bucket(fallback_pos)
    position_targets = (blueprint.get('position_budgets') or {})
    blueprint_needs = {}
    for t in teams:
        spend = _team_spend(t)
        needs = {}
        # Evaluate elite counts and cheap keeper assets by position
        elite_counts = {"C": 0, "W": 0, "D": 0, "G": 0}
        cheap_keepers = {"F": 0, "D": 0, "G": 0}
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
            # Elite check
            thr_pos = 'W' if pos not in ('C','W','D','G') else pos
            thr = thresholds.get(thr_pos, 9e9)
            if fp >= thr:
                elite_counts[thr_pos] = elite_counts.get(thr_pos, 0) + 1
            # Cheap keeper if multi-year and low salary but clearly above replacement
            rep = replacement_map.get('W' if thr_pos not in ('C','W','D','G') else thr_pos, 0.0)
            vorp = max(0.0, fp - rep)
            if yrs >= 2 and sal <= 4 and ((thr_pos == 'G' and vorp >= 4.0) or (thr_pos != 'G' and vorp >= 5.0)):
                bucket = 'F' if thr_pos in ('C','W') else thr_pos
                cheap_keepers[bucket] = cheap_keepers.get(bucket, 0) + 1
            # Goalie starter proxy
            if thr_pos == 'G' and fp >= (replacement_map.get('G', 0.0) + 4.0):
                goalie_starters += 1
            # Depth band
            if yrs > 0 and 2 <= sal <= 5:
                depth_count += 1
        for k in ('F','D','G'):
            tgt = position_targets.get(k) or {}
            try:
                mn = int(tgt.get('min') or 0)
                mx = int(tgt.get('max') or 0)
            except Exception:
                mn = 0; mx = 0
            needs[k] = {
                'spend': spend.get(k, 0),
                'min': mn,
                'max': mx,
                'delta_to_min': max(0, mn - spend.get(k, 0)),
                'delta_over_max': max(0, spend.get(k, 0) - mx) if mx else 0,
            }
        # Adjusted targets based on cheap keeper assets
        adj_targets = {kk: dict(needs[kk]) for kk in needs}
        actions: list[str] = []
        if cheap_keepers.get('F', 0) >= 1:
            # Reallocate a small portion from F to strengthen D/G
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
        # Positional scarcity / coverage
        if elite_counts.get('D', 0) < 2:
            actions.append('need_elite_D: secure 1–2 D anchors')
        if elite_counts.get('C', 0) + elite_counts.get('W', 0) < 2:
            actions.append('need_elite_F: secure at least 2 elite F')
        # Goalie stability
        if goalie_starters < 2:
            actions.append('need_goalies: ensure two starters (total $7–12)')
        # Depth
        depth_min = int((blueprint.get('guidelines') or {}).get('depth_count_min') or 6)
        if depth_count < depth_min:
            actions.append(f'need_depth: target {depth_min - depth_count}+ depth bids at $2–5')
        blueprint_needs[t['team_name']] = {
            'position_spend_vs_targets': needs,
            'elite_counts': elite_counts,
            'cheap_keepers': cheap_keepers,
            'goalie_starters': goalie_starters,
            'depth_count': depth_count,
            'adjusted_targets': adj_targets,
            'suggested_actions': actions,
        }
    # include blueprint assessment in outlooks file for transparency
    team_outlooks = _compute_team_outlooks(teams, projections, team_pick_vals)
    # Persist outlooks and simple recommendations
    outlook_path = os.path.join(out_dir, 'stage2_team_outlooks.json')
    rec = {
        'win_now': 'prioritize upgrades via trades; buy out poor VORP-per-$; lock 2 stable G',
        'win_next': 'favor age/term; selective buyouts; acquire 2–3y control assets',
        'rebuild': 'sell veterans for picks; aggressive multi-year buyouts to reset cap',
    }
    with open(outlook_path, 'w') as f:
        json.dump({'team_outlooks': team_outlooks, 'recommendations': rec, 'blueprint_needs': blueprint_needs}, f, indent=2)
    out_buy = os.path.join(out_dir, 'stage2_buyouts.json')
    out_trd = os.path.join(out_dir, 'stage2_trades.json')
    stage2_buyouts_and_trades(s1, projections, replacement, out_buy, out_trd, s1, stage3_path)
    return out_buy, out_trd


