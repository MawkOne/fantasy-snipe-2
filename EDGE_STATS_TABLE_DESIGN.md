# Player Season Edge Stats Table Design

## 📊 Overview

The `player_season_edge_stats` table stores NHL Edge tracking data (speed, distance, shots, zone time) aggregated by player season.

---

## 🎯 Design Decisions

### **1. Why a New Table?**

✅ **Separate Edge data from traditional stats**
- Edge data is different granularity (season-level aggregates)
- Edge data only exists since 2021-22 (traditional stats go back further)
- Keeps Edge metrics isolated and easy to update

✅ **Follows your existing pattern**
- You have `player_game_stats` (game-level)
- You have `player_shift_metrics` (shift-level)
- This adds `player_season_edge_stats` (season-level)

✅ **`player_career_stats` is empty and has wrong schema**
- It's designed for career totals, not season-by-season
- Missing Edge-specific columns
- Better to keep Edge data separate

---

### **2. Table Structure**

```
player_season_edge_stats
├─ Primary Key: id (serial)
├─ Composite Unique: (player_id, season, game_type)
├─ Foreign Keys: player_id, team_id
├─ Season Info: season, game_type (2=regular, 3=playoffs)
├─ Speed Metrics: max_speed, percentile, top_speed_events
├─ Shot Metrics: max_shot, percentile, top_shot_events
├─ Distance Metrics: total_km, avg_per_game, by_situation
├─ Zone Time Metrics: offensive/neutral/defensive % by strength
├─ Shot Location: JSONB heat map data
└─ Metadata: last_updated, raw_edge_response
```

---

### **3. Key Design Choices**

#### **Composite Unique Key: (player_id, season, game_type)**
```sql
UNIQUE(player_id, season, game_type)
```
- **Why**: One record per player per season per game type
- **Example**: Nurse has 2 records for 2024-25 (regular season + playoffs)

#### **JSONB Columns for Top Events**
```sql
top_speed_events JSONB  -- Top 10 speed bursts
top_shot_events JSONB   -- Top 10 hardest shots
shot_locations JSONB    -- Shot location heat map
```
- **Why**: Flexible storage for arrays of events
- **Benefit**: Can query within JSON (e.g., "speeds on home ice")
- **Example**:
```json
{
  "events": [
    {"speed": 22.03, "date": "2025-03-06", "period": 4, "time": "02:39", "game_id": 2024030416},
    {"speed": 21.93, "date": "2024-11-23", "period": 2, "time": "09:15", "game_id": 2024020332}
  ]
}
```

#### **Separate Columns for Common Queries**
```sql
max_speed_mph NUMERIC(5,2)
max_shot_mph NUMERIC(5,2)
zone_time_offensive_pct NUMERIC(5,4)
```
- **Why**: Fast queries without parsing JSON
- **Benefit**: Easy rankings (ORDER BY max_speed_mph DESC)

#### **Season Format: '20242025'**
```sql
season VARCHAR(8) NOT NULL  -- '20242025'
```
- **Why**: Matches your existing `player_game_advanced_metrics_flat.season` format
- **Benefit**: Easy joins between tables

---

## 🔗 Integration with Existing Tables

### **Join with Game Stats**
```sql
-- Get season Edge data + game-by-game performance
SELECT 
    e.season,
    e.max_speed_mph,
    e.max_shot_mph,
    COUNT(g.id) as games_played,
    SUM(g.goals) as total_goals
FROM player_season_edge_stats e
JOIN player_game_stats g 
  ON e.player_id = g.player_id
  AND LEFT(g.game_id::text, 8) = e.season
WHERE e.player_id = 8477498
GROUP BY e.season, e.max_speed_mph, e.max_shot_mph;
```

### **Join with Advanced Metrics**
```sql
-- Compare speed to Corsi by season
SELECT 
    e.season,
    e.max_speed_mph,
    e.max_speed_percentile,
    AVG(a.CF_pct) as avg_corsi_pct
FROM player_season_edge_stats e
JOIN player_game_advanced_metrics_flat a 
  ON e.player_id = a.player_id 
  AND e.season = a.season
WHERE e.player_id = 8477498
GROUP BY e.season, e.max_speed_mph, e.max_speed_percentile;
```

---

## 📥 Populating the Table

### **Step 1: Create Table**
```bash
psql $DATABASE_URL -f create_edge_stats_table.sql
```

### **Step 2: Populate from Edge API**

```python
from nhlpy import NHLClient
from sqlalchemy import create_engine, text

client = NHLClient()
engine = create_engine(DATABASE_URL)

def populate_edge_stats(player_id, season, game_type=2):
    """Fetch Edge data and insert into database"""
    
    # Get Edge data
    data = client.edge.skater_detail(
        player_id=player_id, 
        season=season
    )
    
    # Extract metrics
    speed = data.get('skatingSpeed', {}).get('speedMax', {})
    shot = data.get('topShotSpeed', {})
    zone_time = data.get('zoneTimeDetails', [])
    
    # Insert into database
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO player_season_edge_stats (
                player_id, season, game_type,
                max_speed_mph, max_speed_kph, max_speed_percentile,
                max_shot_mph, max_shot_kph, max_shot_percentile,
                zone_time_offensive_pct, zone_time_neutral_pct,
                raw_edge_response
            ) VALUES (
                :player_id, :season, :game_type,
                :max_speed_mph, :max_speed_kph, :max_speed_percentile,
                :max_shot_mph, :max_shot_kph, :max_shot_percentile,
                :zone_off_pct, :zone_neu_pct,
                :raw::jsonb
            )
            ON CONFLICT (player_id, season, game_type) 
            DO UPDATE SET
                max_speed_mph = EXCLUDED.max_speed_mph,
                last_updated = CURRENT_TIMESTAMP
        """), {
            'player_id': player_id,
            'season': season,
            'game_type': game_type,
            'max_speed_mph': speed.get('imperial'),
            'max_speed_kph': speed.get('metric'),
            'max_speed_percentile': speed.get('percentile'),
            'max_shot_mph': shot.get('imperial'),
            'max_shot_kph': shot.get('metric'),
            'max_shot_percentile': shot.get('percentile'),
            'zone_off_pct': zone_time[0].get('offensiveZonePctg') if zone_time else None,
            'zone_neu_pct': zone_time[0].get('neutralZonePctg') if zone_time else None,
            'raw': json.dumps(data)
        })
        conn.commit()

# Populate Darnell Nurse's Edge stats
for season in ['20212022', '20222023', '20232024', '20242025']:
    populate_edge_stats(8477498, season)
```

---

## 📈 Example Queries

### **1. Get All Edge Stats for a Player**
```sql
SELECT * FROM player_season_edge_stats 
WHERE player_id = 8477498 
ORDER BY season DESC;
```

### **2. Find Fastest Defensemen in 2024-25**
```sql
SELECT 
    p.full_name,
    e.max_speed_mph,
    e.max_speed_percentile
FROM player_season_edge_stats e
JOIN players p ON e.player_id = p.id
WHERE e.season = '20242025' 
  AND e.game_type = 2
  AND p.position_code = 'D'
ORDER BY e.max_speed_mph DESC
LIMIT 10;
```

### **3. Compare Regular Season vs Playoffs**
```sql
SELECT 
    player_id,
    game_type,
    max_speed_mph,
    max_shot_mph,
    zone_time_offensive_pct
FROM player_season_edge_stats
WHERE player_id = 8477498 
  AND season = '20242025'
ORDER BY game_type;
```

### **4. Speed Trend Over Time**
```sql
SELECT 
    season,
    max_speed_mph,
    max_speed_percentile
FROM player_season_edge_stats
WHERE player_id = 8477498 
  AND game_type = 2
ORDER BY season;
```

---

## 🎯 Benefits of This Design

✅ **Efficient Queries**: Indexed columns for fast lookups  
✅ **Flexible Data**: JSONB for complex event arrays  
✅ **Easy Joins**: Matches existing table patterns  
✅ **Conflict Handling**: UPSERT support for updates  
✅ **Scalable**: One record per player/season (~3,500 players × 5 seasons = 17,500 rows)  
✅ **Future-Proof**: Can add new Edge metrics as columns

---

## 📊 Storage Estimate

**Per Record**: ~2-3 KB (with JSONB)  
**Total for NHL** (~700 active players × 5 seasons): ~3,500 records = ~7-10 MB  
**With all historical players** (~3,500 × 5 seasons): ~17,500 records = ~35-50 MB

**Very lightweight!** ✨

