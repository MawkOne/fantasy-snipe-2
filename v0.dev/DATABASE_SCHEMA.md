# NHL API Database Schema

## ✅ Connection Successful!

**Status:** Healthy ✅  
**Database:** `postgres`  
**Total Players:** 3,513  
**Total Games:** 16,132  

## Database Tables (21 Total)

### Core Tables

#### `players` (3,513 records)
- Player information, names, positions, team assignments
- Fields: `id`, `full_name`, `first_name`, `last_name`, `sweater_number`, `position_code`, `headshot_url`, `is_active`, `team_id`
- Example: Cole Caufield (#13, MTL, Right Wing)

#### `teams`
- NHL team information

#### `games` (16,132 records)
- Game schedules and results

### Stats Tables

#### `player_game_stats`
- Individual player stats for each game (goals, assists, etc.)

#### `goalie_game_stats`
- Goalie-specific game stats (saves, GAA, etc.)

#### `player_career_stats`
- Career aggregated statistics

#### `player_game_advanced_metrics`
- Advanced analytics (Corsi, Fenwick, etc.)

#### `player_game_advanced_metrics_flat`
- Flattened version of advanced metrics

#### `player_shift_metrics`
- Shift-by-shift analytics

### Detail Tables

#### `player_details`
- Extended player information (birthdate, height, weight, etc.)

#### `player_shifts`
- Individual shift data for players

#### `game_events`
- All in-game events (goals, penalties, etc.)

### Temporary/Staging Tables

- `game_tmp`, `game_plays_tmp`, `game_plays_players_tmp`
- `game_skater_stats_tmp`, `game_goalie_stats_tmp`
- `game_teams_stats_tmp`, `game_shifts_tmp`
- `player_info_tmp`, `team_info_tmp`

## What This Means

This database contains **real NHL data** from the official NHL API! You can:

✅ Get player info, stats, headshots  
✅ Get game schedules and results  
✅ Get real-time player performance  
✅ Calculate advanced metrics  
✅ Track player shifts and ice time  

## For Your Fantasy League App

You can use this data to:

1. **Show real player stats** in team rosters
2. **Display player headshots** (URLs included!)
3. **Calculate fantasy points** based on real stats
4. **Show game schedules** for upcoming matchups
5. **Track player performance** over time
6. **Compare players** for trade analysis
7. **Show advanced metrics** for deeper analysis

## Sample Data

```sql
-- Cole Caufield (Montreal Canadiens)
{
  id: 8481540,
  full_name: "Cole Caufield",
  first_name: "Cole",
  last_name: "Caufield",
  sweater_number: 13,
  position_code: "R",
  headshot_url: "https://assets.nhle.com/mugs/nhl/20242025/MTL/8481540.png",
  is_active: true,
  team_id: 8
}
```

## Next Steps

1. ✅ Database connected
2. ✅ Schema documented
3. 🔲 Create FastAPI endpoints for player search
4. 🔲 Create React hooks to display player data
5. 🔲 Integrate with fantasy league roster view
6. 🔲 Show real stats in chat when discussing players

