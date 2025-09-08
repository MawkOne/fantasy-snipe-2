#!/usr/bin/env python3
"""
Derive per-team baseline ice-time deployment shares for forecasting from
docs/ice_time/team_deployment_clusters.csv.

Outputs: docs/ice_time/team_forecast_baselines.csv
Columns:
  team_id, full_name, tri_code, deployment_cluster,
  ev_line1_share, ev_line2_share, ev_line3_share, ev_line4_share,
  pp1_share, pp2_share,
  pk_pair1_share, pk_pair2_share, pk_pair3_share, pk_rest_share,
  ev_pair_ff_share, ev_pair_dd_share, trios_ev_fwd_line_share

Heuristics:
  - EV line shares scaled by pairs_EV__share_top_5 (concentration)
  - PP unit shares scaled by pairs_PP__share_top_5
  - PK pair shares scaled by pairs_SH__share_top_5
"""

import os
import argparse
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INP = os.path.join(ROOT, 'docs', 'ice_time', 'team_deployment_clusters.csv')
DEFAULT_OUT = os.path.join(ROOT, 'docs', 'ice_time', 'team_forecast_baselines.csv')


def derive_ev_shares(ev_top5: float) -> tuple[float, float, float, float]:
    if ev_top5 >= 0.09:
        return (0.38, 0.30, 0.20, 0.12)
    if ev_top5 >= 0.075:
        return (0.36, 0.30, 0.22, 0.12)
    return (0.34, 0.30, 0.23, 0.13)


def derive_pp_shares(pp_top5: float) -> tuple[float, float]:
    if pp_top5 >= 0.15:
        return (0.70, 0.30)
    if pp_top5 >= 0.12:
        return (0.65, 0.35)
    return (0.60, 0.40)


def derive_pk_shares(sh_top5: float) -> tuple[float, float, float, float]:
    # Returns pair1, pair2, pair3, rest shares
    if sh_top5 >= 0.17:
        return (0.40, 0.32, 0.18, 0.10)
    if sh_top5 >= 0.15:
        return (0.38, 0.30, 0.20, 0.12)
    return (0.35, 0.27, 0.22, 0.16)


def main():
    parser = argparse.ArgumentParser(description='Derive per-team forecast baselines')
    parser.add_argument('--input', type=str, default=DEFAULT_INP, help='Path to team_deployment_clusters.csv')
    parser.add_argument('--output', type=str, default=DEFAULT_OUT, help='Output CSV path for team_forecast_baselines.csv')
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    rows = []
    for _, r in df.iterrows():
        team_id = int(r['team_id'])
        tri = r.get('tri_code')
        name = r.get('full_name')
        cluster = int(r.get('deployment_cluster', 0))
        ev_top5 = float(r.get('pairs_EV__share_top_5') or 0)
        pp_top5 = float(r.get('pairs_PP__share_top_5') or 0)
        sh_top5 = float(r.get('pairs_SH__share_top_5') or 0)
        ev_ff = float(r.get('pairs_EV__pair_ff_share') or 0)
        ev_dd = float(r.get('pairs_EV__pair_dd_share') or 0)
        fwd_line_share = float(r.get('trios_EV__trio_fwd_share') or 0)

        ev_l1, ev_l2, ev_l3, ev_l4 = derive_ev_shares(ev_top5)
        pp1, pp2 = derive_pp_shares(pp_top5)
        pk1, pk2, pk3, pkr = derive_pk_shares(sh_top5)

        rows.append({
            'team_id': team_id,
            'full_name': name,
            'tri_code': tri,
            'deployment_cluster': cluster,
            'ev_line1_share': ev_l1,
            'ev_line2_share': ev_l2,
            'ev_line3_share': ev_l3,
            'ev_line4_share': ev_l4,
            'pp1_share': pp1,
            'pp2_share': pp2,
            'pk_pair1_share': pk1,
            'pk_pair2_share': pk2,
            'pk_pair3_share': pk3,
            'pk_rest_share': pkr,
            'ev_pair_ff_share': ev_ff,
            'ev_pair_dd_share': ev_dd,
            'trios_ev_fwd_line_share': fwd_line_share,
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output, index=False)
    print(f"Wrote {len(out)} team baselines to {args.output}")


if __name__ == '__main__':
    main()


