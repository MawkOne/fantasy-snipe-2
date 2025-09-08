import os
import json
from typing import Dict, List

from ..run_simulation import load_2025_26_projections


def cluster_by_position(n_clusters: Dict[str, int] = None, target_k: int = 6, caps: Dict[str, int] | None = None, top_tier_caps: Dict[str, int] | None = None) -> Dict[str, Dict]:
    """Tier projected FP per position using Jenks Natural Breaks with fixed tiers (default 6).
    - Produces exactly target_k tiers when feasible; respects minimal segment sizes.
    - Enforces optional top-tier headcount caps and overall caps (demote beyond cap to lowest tier).
    Returns: {pos: {method: 'jenks', k: int, centers: [...], assignments: [{name, fp, cluster}]}}
    """

    projections = load_2025_26_projections()
    pos_to = {'C': [], 'W': [], 'D': [], 'G': []}
    names = {'C': [], 'W': [], 'D': [], 'G': []}
    for name, v in projections.items():
        pos = v.get('pos') or 'W'
        pos = 'W' if pos not in ('C','W','D','G') else pos
        fp = float(v.get('fp') or 0.0)
        pos_to[pos].append([fp])
        names[pos].append(name)
    result: Dict[str, Dict] = {}
    import numpy as np
    if n_clusters is None:
        n_clusters = {}
    for pos, X in pos_to.items():
        if not X:
            result[pos] = {'centers': [], 'assignments': []}
            continue
        X_arr = np.array(X, dtype=float).flatten()
        order_desc = np.argsort(-X_arr)
        sorted_fp_desc = X_arr[order_desc]
        sorted_names_desc = [names[pos][i] for i in order_desc.tolist()]
        # Jenks expects ascending order
        order_asc = np.argsort(X_arr)
        vals = X_arr[order_asc]
        n = len(vals)
        if n == 1:
            result[pos] = {'method': 'jenks', 'k': 1, 'centers': [float(vals[0])], 'assignments': [{'name': sorted_names_desc[0], 'fp': float(sorted_fp_desc[0]), 'cluster': 0}]}
            continue
        # Helper: Jenks DP matrices
        def jenks_matrices(data: List[float], classes: int):
            m = len(data)
            lower = [[0] * (classes + 1) for _ in range(m + 1)]
            var = [[0.0] * (classes + 1) for _ in range(m + 1)]
            for i in range(1, classes + 1):
                lower[1][i] = 1
                var[1][i] = 0.0
                for j in range(2, m + 1):
                    var[j][i] = float('inf')
            s1 = [0.0] * (m + 1)
            s2 = [0.0] * (m + 1)
            for i in range(1, m + 1):
                val = data[i - 1]
                s1[i] = s1[i - 1] + val
                s2[i] = s2[i - 1] + val * val
                var[i][1] = s2[i] - (s1[i] * s1[i]) / i
                lower[i][1] = 1
            for l in range(2, m + 1):
                for j in range(2, classes + 1):
                    var[l][j] = float('inf')
                    for i in range(1, l + 1):
                        w = l - i + 1
                        ssum = s1[l] - s1[i - 1]
                        ssum2 = s2[l] - s2[i - 1]
                        v = ssum2 - (ssum * ssum) / w
                        if var[l][j] > (v + var[i - 1][j - 1]):
                            lower[l][j] = i
                            var[l][j] = v + var[i - 1][j - 1]
            return lower, var
        def jenks_breaks(data: List[float], classes: int) -> List[int]:
            lower, var = jenks_matrices(data, classes)
            k = classes
            kclass = [0] * (k + 1)
            count_num = len(data)
            kclass[k] = count_num
            while k > 1:
                idx = int(lower[count_num][k] - 1)
                kclass[k - 1] = idx
                count_num = idx
                k -= 1
            return kclass  # index starts for each class on ascending data
        # Restrict tiering to in-scope players by cap; others go to lowest tier
        cap_count = int((caps or {}).get(pos, n))
        in_scope_desc_idx = order_desc[:cap_count]
        in_scope_vals_desc = sorted_fp_desc[:cap_count]
        in_scope_names_desc = sorted_names_desc[:cap_count]
        # Build ascending view for Jenks on in-scope only
        pairs = list(enumerate(in_scope_vals_desc))  # (desc_pos, fp)
        pairs.sort(key=lambda p: p[1])  # ascending by fp
        asc_vals = [p[1] for p in pairs]
        # Build segments for fixed target_k using Jenks indices (on asc_vals)
        idxs = jenks_breaks(asc_vals, max(2, min(target_k, len(asc_vals))))
        segs = []
        start = 0
        for b in idxs[1:]:
            segs.append((start, b))
            start = b
        if not segs:
            segs = [(0, len(asc_vals))]
        # Enforce minimal segment sizes by merging tiny ones forward
        min_seg = 2 if pos == 'G' else 4
        merged = []
        for a0, b0 in segs:
            if b0 - a0 < min_seg and merged:
                pa, pb = merged[-1]
                merged[-1] = (pa, b0)
            else:
                merged.append((a0, b0))
        if not merged:
            merged = [(0, len(asc_vals))]
        # If fewer than target_k, split largest segments until target_k or cannot due to min_seg
        segments_asc = merged[:]
        def seg_size(seg):
            a0, b0 = seg
            return b0 - a0
        while len(segments_asc) < min(target_k, len(asc_vals) // min_seg):
            largest_idx = max(range(len(segments_asc)), key=lambda i: seg_size(segments_asc[i]))
            a0, b0 = segments_asc[largest_idx]
            size = b0 - a0
            if size < 2 * min_seg:
                break
            mid = a0 + size // 2
            left = (a0, mid)
            right = (mid, b0)
            segments_asc[largest_idx:largest_idx+1] = [left, right]
        # Now assign clusters to in-scope by mapping asc segments back to desc positions
        assignments = [{'name': nm, 'fp': float(fpv), 'cluster': target_k - 1} for nm, fpv in zip(sorted_names_desc, sorted_fp_desc)]
        rank = 0
        for a0, b0 in segments_asc[::-1]:  # highest fp segment first -> rank 0
            desc_positions = [pairs[i][0] for i in range(a0, b0)]
            for di in desc_positions:
                assignments[di]['cluster'] = rank
            rank += 1
        chosen_k = rank if rank > 0 else 1
        # Enforce top-tier caps on in-scope (cluster 0)
        if top_tier_caps and pos in top_tier_caps:
            tt_cap = int(top_tier_caps[pos])
            assignments.sort(key=lambda r: r['fp'], reverse=True)
            count0 = 0
            for a in assignments[:cap_count]:
                if a['cluster'] == 0:
                    if count0 >= tt_cap:
                        a['cluster'] = 1 if chosen_k > 1 else 0
                    else:
                        count0 += 1
        # Players beyond cap_count already default to last tier
        # Ensure exactly target_k tiers by compressing if fewer
        assignments.sort(key=lambda r: r['fp'], reverse=True)
        existing = []
        for a in assignments:
            c = a['cluster']
            if c not in existing:
                existing.append(c)
        # Map to 0..len(existing)-1 while keeping last tier at target_k-1
        last_tier = target_k - 1
        if last_tier not in existing:
            existing.append(last_tier)
        remap = {old: (i if old != last_tier else target_k - 1) for i, old in enumerate(existing) if i < target_k - 1 or old == last_tier}
        for a in assignments:
            a['cluster'] = int(remap.get(a['cluster'], target_k - 1))
        # Compute centers for 0..target_k-1
        centers = []
        for c in range(target_k):
            vals_c = [a['fp'] for a in assignments if a['cluster'] == c]
            centers.append(float(np.median(vals_c)) if vals_c else 0.0)
        result[pos] = {'method': 'jenks', 'k': int(target_k), 'centers': centers, 'assignments': assignments}
    return result


def main():
    clusters = cluster_by_position(
        target_k=6,
        caps={'G': 40, 'C': 75, 'W': 120, 'D': 60},
        top_tier_caps={'G': 6, 'C': 10, 'W': 10, 'D': 8}
    )
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outputs'))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'fp_clusters_tiers8.json')
    with open(out_path, 'w') as f:
        json.dump(clusters, f, indent=2)
    print(out_path)


if __name__ == '__main__':
    main()


