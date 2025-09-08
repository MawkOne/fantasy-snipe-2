## Metrics catalog (derived from shift metrics)

This document lists all metrics that can be computed from the current data model and scripts, primarily from `player_shifts`, `player_shift_metrics`, and `game_events`.

### Base shift-level fields available
- player/game context: player_id, game_id, team_id, period, shift_number
- timing: start_time (MM:SS), end_time (MM:SS), duration (MM:SS)
- shot attempt buckets (from event classification):
  - attempts_for, attempts_against  (Corsi attempts; shot or miss or block or goal)
  - shots_for, shots_against        (shots on goal incl. goals)
  - goals_for, goals_against
  - unblocked_for, unblocked_against  (misses only in storage; Fenwick = shots + misses)
  - blocks_for, blocks_against
- other events: hits_for/against, takeaways_for/against, giveaways_for/against
- faceoff/zone context: zone_start (O/D/N), faceoff_won (bool)
- strength context: strength_state (EV/PP/SH) at shift start
- on-ice composition: teammates_on_ice, opponents_on_ice, teammates_on_ice_ids, opponents_on_ice_ids

Notes
- Fenwick uses shots + misses. In storage, `unblocked_*` counts misses; compute FF as `shots_* + unblocked_*`.
- Strength_state is estimated at shift start using overlapping shifts and on-ice counts.

### Core derived metrics (per any aggregation: per-shift, per-game, per-season, etc.)
Use F/A suffixes for For/Against. Totals are sums over included shifts; durations are sum of durations in seconds.

- Corsi
  - CF = sum(attempts_for)
  - CA = sum(attempts_against)
  - CF% = CF / (CF + CA)
  - CF60 = CF / (TOI_seconds / 3600)
  - CA60 = CA / (TOI_seconds / 3600)
  - CorsiDiff = CF − CA

- Fenwick
  - FF = sum(shots_for + unblocked_for)
  - FA = sum(shots_against + unblocked_against)
  - FF% = FF / (FF + FA)
  - FF60, FA60, FenwickDiff analogous to Corsi

- Shots
  - SF = sum(shots_for)
  - SA = sum(shots_against)
  - SF% = SF / (SF + SA)
  - SF60, SA60, ShotDiff analogous to Corsi

- Goals
  - GF = sum(goals_for)
  - GA = sum(goals_against)
  - GF% = GF / (GF + GA)
  - GF60, GA60, GoalDiff analogous to Corsi

- On-ice percentages and PDO
  - On-ice Shooting% (Sh%) = GF / max(SF, 1)
  - OnIce SV% = 1 − (GA / max(SA, 1))
  - PDO = (On-ice Sh% + OnIce SV%) × 1000  (or report as percentages separately)

- Blocks/Hits/Takeaways/Giveaways
  - BLK_FOR = sum(blocks_for), BLK_AGAINST = sum(blocks_against), BLKDiff = BLK_FOR − BLK_AGAINST, BLK60
  - HIT_FOR, HIT_AGAINST, HITDiff, HIT60
  - TK_FOR, TK_AGAINST, TKDiff, TK60
  - GV_FOR, GV_AGAINST, GVDiff, GV60

- Time-based
  - TOI_seconds = sum(duration_seconds)
  - TOI (HH:MM:SS), AvgShiftLength, MedianShiftLength, ShiftsCount

### Shot-location and danger-tier metrics (HD/MD/LD)
Prerequisites: shot coordinates available in `game_events` (`coordinates_x`, `coordinates_y`, and `raw.coordinates`). Coordinates are already used in `compute_shift_metrics.py`.

Classification (canonical frame)
- Normalize to attacking-net frame per shot (mirror as needed so the net is at x = +89 ft NHL rink coordinates; we will implement canonicalization in code).
- Proposed thresholds (tunable):
  - High Danger (HD): within home-plate/slot area and close range, e.g., distance_to_net ≤ 25 ft AND within slot polygon.
  - Mid Danger (MD): 25 ft < distance_to_net ≤ 40 ft OR inside slot but farther than 25 ft.
  - Low Danger (LD): distance_to_net > 40 ft or outside slot at poor angle.

Derived per tier (compute for For and Against, then aggregate):
- Shots: HD_SF, MD_SF, LD_SF; HD_SA, MD_SA, LD_SA
- Goals: HD_GF, MD_GF, LD_GF; HD_GA, MD_GA, LD_GA
- Attempts (Corsi): HD_CF, MD_CF, LD_CF; HD_CA, MD_CA, LD_CA
- Fenwick (unblocked): HD_FF, MD_FF, LD_FF; HD_FA, MD_FA, LD_FA

Percentages and shares:
- Tier win %: e.g., HD_SF% = HD_SF / (HD_SF + HD_SA); analogous for CF/FF/GF
- For-side composition: e.g., HD_Share_for = HD_SF / max(SF, 1) (share of for-shots that are HD)
- Against-side composition: e.g., HD_Share_against = HD_SA / max(SA, 1)

Tier shooting percentages (on-ice):
- HD Sh% (for) = HD_GF / max(HD_SF, 1); HD Sh% (against) = HD_GA / max(HD_SA, 1)
- MD Sh% and LD Sh% analogous for for/against

Rates and differentials:
- Per‑60: HD_SF60 = HD_SF / (TOI_seconds / 3600); similarly for MD/LD and CF/FF/GF, and Against variants
- Differentials: HD_SDiff = HD_SF − HD_SA; HD_CDiff, HD_FDiff, HD_GDiff (and MD/LD analogs)

Split support:
- All danger-tier metrics can be split by strength_state (EV/PP/SH), zone_start (O/D/N), period, home/away.

Notes:
- Slot polygon and exact distance cutoffs are implementation details; we will ship standard “home-plate + distance” logic with canonicalized coordinates. Thresholds can be adjusted later without changing the metric interfaces.

### Split dimensions (filter or group-by)
- Strength: EV, PP, SH
- Zone start: O, D, N (compute OZS% = OZS / (OZS + DZS); DZS% analogous)
- Period: 1/2/3/OT
- Home/Away (via team relation to game)
- Score state (can be derived by joining to `game_events`, if needed)

### Faceoff and zone-start metrics
- Shift-start faceoff win rate = wins / (wins + losses) where faceoff_won is not null
- OZS/DZS/NZS counts and percentages (exclude neutral for OZS%/DZS%)

### On-ice composition metrics (WOWY and quality)
- Most frequent linemates/opponents: from `teammates_on_ice_ids`/`opponents_on_ice_ids`
- WOWY (with/without): metrics (e.g., CF%, GF%) when with a given teammate vs without
- Quality of Teammates/Opponents (QoT/QoC): average partner/opponent strength via their season/game metrics (requires join)

### Strength/zone/period split metrics
All core metrics (CF/FF/SF/GF, %, per‑60, diffs) can be recomputed within:
- strength_state ∈ {EV, PP, SH}
- zone_start ∈ {O, D, N}
- period ∈ {1, 2, 3, OT}

### Team/player aggregations supported
- Per player–shift (as stored)
- Per player–game (sum over shifts in game)
- Per player–season or date range (sum over shifts)
- Per team–game/season

### Not currently implemented
- Expected Goals (xG/xGA/xGF%): coordinates are stored in `game_events.raw`, but no xG model is included. Can be added if a model/coefficients are provided.
- Score- and venue-adjusted metrics: possible with additional logic (pace/score effects) but not implemented.

### Implementation references
- Storage schema: `src/database/models.py` `PlayerShiftMetrics`
- Computation logic: `scripts/compute_shift_metrics.py`

