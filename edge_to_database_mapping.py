#!/usr/bin/env python3
"""
Map Edge API data to database granularity levels
Show what Edge data can be attached to shift/game/season summaries
"""

print("=" * 100)
print("  🔗 EDGE API → DATABASE ATTACHMENT MAPPING")
print("=" * 100)

print("""
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 1. SHIFT-LEVEL ATTACHMENTS                                                        │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ Database: player_shifts (15,404 shifts for Nurse)                                 │
│   - shift_number, period, start_time, end_time, duration                          │
│                                                                                    │
│ ✅ CAN ATTACH (by matching timestamps):                                           │
│                                                                                    │
│   🏃 Speed Events (from skater_skating_speed_detail)                              │
│      - Top 10 speed bursts per season                                             │
│      - Each has: period, timeInPeriod, speed (MPH/KPH)                            │
│      - MATCH: If speed event timestamp falls within shift start/end               │
│      └─ Result: "Shift had max speed of 22.5 MPH at 8:49 in P2"                   │
│                                                                                    │
│   🏒 Shot Events (from skater_shot_speed_detail)                                  │
│      - Top 10 hardest shots per season                                            │
│      - Each has: period, timeInPeriod, shotSpeed (MPH/KPH)                        │
│      - MATCH: If shot timestamp falls within shift start/end                      │
│      └─ Result: "Shift included 98 MPH shot at 10:27 in P3"                       │
│                                                                                    │
│ ❌ CANNOT ATTACH (wrong granularity):                                             │
│   - Distance skated (only per-game totals, not per-shift)                         │
│   - Zone time % (only season aggregates, not per-shift)                           │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 2. GAME-LEVEL ATTACHMENTS                                                         │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ Database: player_game_stats (589 games for Nurse)                                 │
│   - goals, assists, points, shots, toi, plus_minus                                │
│                                                                                    │
│ ✅ CAN ATTACH:                                                                     │
│                                                                                    │
│   📏 Distance Skated (from skater_skating_distance_detail)                        │
│      - distanceSkatedAll (total km/miles for game)                                │
│      - distanceSkatedEven, distanceSkatedPP, distanceSkatedPK                     │
│      - toiAll, toiEven, toiPP, toiPK                                              │
│      - MATCH: By game_date                                                        │
│      └─ Result: "Game: 5.05 km skated, 874s ES, 177s PP"                          │
│                                                                                    │
│   🏃 Max Speed in Game (aggregate from speed events)                              │
│      - Get all speed events for that game                                         │
│      - Take max speed from events in that game                                    │
│      - MATCH: By game_date                                                        │
│      └─ Result: "Game max speed: 22.1 MPH"                                        │
│                                                                                    │
│   🏒 Max Shot Velocity in Game (aggregate from shot events)                       │
│      - Get all shot events for that game                                          │
│      - Take max shot speed from events in that game                               │
│      - MATCH: By game_date                                                        │
│      └─ Result: "Game hardest shot: 95 MPH"                                       │
│                                                                                    │
│   📊 Event Counts                                                                 │
│      - Count of speed bursts > X MPH in game                                      │
│      - Count of shots > Y MPH in game                                             │
│      └─ Result: "Game had 3 speeds over 21 MPH, 2 shots over 90 MPH"             │
│                                                                                    │
│ ❌ CANNOT ATTACH (wrong granularity):                                             │
│   - Zone time % (only season aggregates)                                          │
│   - Percentile rankings (season-level comparisons)                                │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 3. SEASON-LEVEL ATTACHMENTS                                                       │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ Database: Aggregated from player_game_stats                                       │
│   - SUM(goals), SUM(assists), AVG(plus_minus), etc.                               │
│                                                                                    │
│ ✅ CAN ATTACH (from skater_detail - CAT endpoint):                                │
│                                                                                    │
│   🏃 Speed Summary                                                                │
│      - speedMax (imperial/metric, percentile, leagueAvg)                          │
│      - burstsOver20 (count of 20+ MPH bursts)                                     │
│      └─ Result: "Season max: 22.03 MPH (62.6th percentile)"                       │
│                                                                                    │
│   🏒 Shot Velocity Summary                                                        │
│      - topShotSpeed (imperial/metric, percentile, leagueAvg)                      │
│      └─ Result: "Season max shot: 98.24 MPH (66.3rd percentile)"                  │
│                                                                                    │
│   📏 Distance Summary                                                             │
│      - totalDistanceSkated (season total km/miles)                                │
│      - Average per game                                                           │
│      └─ Result: "Season: ~350 km total, ~4.3 km/game"                             │
│                                                                                    │
│   🗺️  Zone Time (from skater_zone_time)                                           │
│      - offensiveZonePctg (with percentile)                                        │
│      - neutralZonePctg (with percentile)                                          │
│      - defensiveZonePctg (with percentile)                                        │
│      - By strength: all, es, pp, pk                                               │
│      └─ Result: "Season: 46% offensive zone (98th percentile)"                    │
│                                                                                    │
│   📊 Shot Location Heat Map (from skater_shot_location_detail)                    │
│      - Shots/goals by area (crease, high slot, circles, etc.)                     │
│      - Shooting % and percentiles per area                                        │
│      └─ Result: "Season: 13 SOG from crease (96.7th percentile)"                  │
│                                                                                    │
│   🎯 Rankings & Comparisons                                                       │
│      - All percentiles (vs entire league)                                         │
│      - League averages for context                                                │
│      └─ Result: "Faster than 62.6% of NHL, shoots harder than 66.3%"             │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────┐
│ 4. COMBINED QUERIES - WHAT YOU CAN BUILD                                          │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│ 🔷 Shift-Level Analysis:                                                          │
│    "Show me all shifts where Nurse hit 22+ MPH AND had Corsi >60%"                │
│    - Match Edge speed events to shifts                                            │
│    - Filter by player_shift_metrics.CF > player_shift_metrics.CA                  │
│                                                                                    │
│ 🔷 Game-Level Analysis:                                                           │
│    "Games where Nurse skated 5+ km AND had 2+ points"                             │
│    - Attach Edge distance data to game stats                                      │
│    - Filter by points >= 2                                                        │
│                                                                                    │
│ 🔷 Season-Level Analysis:                                                         │
│    "Compare Nurse's speed percentile to his CF% rank"                             │
│    - Edge speed percentile: 62.6%                                                 │
│    - Calculate CF% rank from player_game_advanced_metrics_flat                    │
│    - Compare correlations                                                         │
│                                                                                    │
│ 🔷 Multi-Level Analysis:                                                          │
│    "How does distance per game correlate with +/- rating?"                        │
│    - Edge distance per game (game-level)                                          │
│    - Plus/minus from player_game_stats (game-level)                               │
│    - Calculate correlation across all games                                       │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 100)
print("  📊 ATTACHMENT SUMMARY")
print("=" * 100)

print("""
SHIFT-LEVEL:
  ✅ Speed events (if timestamp matches)
  ✅ Shot events (if timestamp matches)
  ❌ Distance (only game-level)
  ❌ Zone time (only season-level)

GAME-LEVEL:
  ✅ Total distance skated
  ✅ Distance by situation (ES/PP/PK)
  ✅ Max speed in game
  ✅ Max shot in game
  ✅ Event counts (speeds >X, shots >Y)
  ❌ Zone time % (only season-level)

SEASON-LEVEL:
  ✅ Max speed (with percentile)
  ✅ Max shot velocity (with percentile)
  ✅ Total/avg distance
  ✅ Zone time % by strength
  ✅ Shot location heat map
  ✅ All league rankings/percentiles
  
CROSS-LEVEL QUERIES:
  ✅ ANY combination of database + Edge data!
""")

print("=" * 100)

