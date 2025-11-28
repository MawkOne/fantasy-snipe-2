1️⃣ Situation classifiers we have (finalized)
A. Start-type (where the play starts) — exactly one per goal

These are mutually exclusive; we pick one in this order:

Breakaway

Scorer is ahead of all defenders in the final frame

No defender between scorer and goal in x-direction

Gap to nearest defender > ~180 in (≈ 15 ft)

DZ Turnover

Scoring team gains possession in its own defensive zone

Possession flips from other team → scoring team while puck is in DZ

No speed/“fast attack” requirement; just turnover location

NZ Turnover

Same as above, but possession flip happens in neutral zone

Rush Entry

No DZ/NZ turnover

Puck enters offensive half with speed

Offensive-zone time before goal < 7 seconds

In-Zone Start

No DZ/NZ turnover

Offensive-zone time ≥ 7 seconds before goal

B. Play-action tags (can be multiple per goal, all booleans)

These describe what the puck does before the shot, especially w.r.t. goalie movement.

Rebound Goal (is_rebound)

There is a previous shot in the last ~2 seconds

Puck speed drops low, then increases again → follow-up shot

Netfront / Crease Battle (is_netfront)

Puck at goal frame is close to goalie (< ~300 in)

At least a couple of skaters (any team) also within that radius

East–West (Royal Road) Goal (is_east_west)

In the last ~1 second before the goal, puck’s y-position crosses the rink centerline (sign change)

AND the change in y is big (e.g. > 200 in)

Cross-slot (non–royal road) (is_cross_slot)

In the last ~1 second before the goal, |Δy| is moderate/large (> 200 in)

BUT puck does not cross the centerline (no sign change)

Low-to-High Pass (is_low_to_high)

In the last ~2 seconds, puck moves from “low” (below hashmarks / near goal line) to “high” (toward point / top of circles) in the offensive zone

These 10 together give you a very rich description of each goal’s situation.