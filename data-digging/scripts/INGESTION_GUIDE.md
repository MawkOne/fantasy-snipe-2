# NHL Data Ingestion Guide

## 🚨 Current Status (Nov 27, 2025)

### ❌ Problem Identified
Your NHL API data ingestion **stopped on October 20, 2025** - you're missing ~5 weeks of data!

- **Last ingested**: October 20, 2025 (Game 2025020095)
- **Current date**: November 27, 2025
- **Missing**: ~200-250 games of play-by-play and stats

### ✅ What's Working
- **NHL Edge Tracking Data**: Up to date (Nov 26, 2025) ✅
- **Game Schedule**: Full 2025-26 schedule loaded (1,312 games) ✅

### ❌ What's Broken
- **Play-by-Play**: 37 days behind ❌
- **Player Game Stats**: Not being ingested (0 rows) ❌
- **Goalie Stats**: Not being ingested (0 rows) ❌
- **Shift Data**: Not being ingested (0 rows) ❌

---

## 🔧 Quick Fix - Backfill Missing Data

### Option 1: Backfill October 21 - November 27, 2025

```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts"

python3 run_nhl_ingestion.py \
  --backfill \
  --start-date 2025-10-21 \
  --end-date 2025-11-27
```

### Option 2: Run Full 2025 Season (Slower but Complete)

```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts"

python3 run_nhl_ingestion.py --season 2025
```

This will run:
1. ✅ Games (already complete)
2. 🔄 Play-by-Play (will fill in missing games)
3. 🔄 Player Game Stats (will populate from scratch)
4. 🔄 Shift Charts (will populate from scratch)

---

## 📋 Individual Script Usage

If you prefer to run scripts individually:

### 1. Play-by-Play Only
```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts/ingestion/nhl_api"

python3 populate_play_by_play.py \
  --all \
  --season 20252026 \
  --game-type 2
```

### 2. Player Stats Only
```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts/ingestion/nhl_api"

python3 populate_player_game_stats.py --season 20252026
```

### 3. Shift Data Only
```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts/ingestion/nhl_api"

python3 populate_shift_charts.py --season 20252026
```

---

## 🤖 Automated Ingestion (Recommended)

### Set Up Daily Cron Job

To prevent this from happening again, set up a daily cron job:

```bash
# Edit your crontab
crontab -e

# Add this line to run every day at 3 AM
0 3 * * * cd "/Users/markhenderson/Cursor Projects/NHL-API/data-digging/scripts" && python3 run_nhl_ingestion.py --season 2025 --continue-on-error >> /tmp/nhl_ingestion.log 2>&1
```

### Set Up Google Cloud Run Job

Alternatively, create a Cloud Run job to run this automatically:

```bash
# Build and deploy
cd "/Users/markhenderson/Cursor Projects/NHL-API"

gcloud builds submit --tag gcr.io/fantasy-snipe-ai/nhl-ingestion

gcloud run jobs create nhl-daily-ingestion \
  --image gcr.io/fantasy-snipe-ai/nhl-ingestion \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --max-retries 3 \
  --task-timeout 3600s \
  --set-env-vars FANTASY_DATABASE_URL="$FANTASY_DATABASE_URL"

# Schedule to run daily at 3 AM
gcloud scheduler jobs create http nhl-ingestion-daily \
  --location us-central1 \
  --schedule "0 3 * * *" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/fantasy-snipe-ai/jobs/nhl-daily-ingestion:run" \
  --http-method POST \
  --oauth-service-account-email YOUR_SERVICE_ACCOUNT@fantasy-snipe-ai.iam.gserviceaccount.com
```

---

## 📊 Verify After Running

Check your data status:

```bash
python3 -c "
import psycopg2
import os

conn = psycopg2.connect(os.environ['FANTASY_DATABASE_URL'])
cur = conn.cursor()

# Check play-by-play
cur.execute('SELECT MAX(ge.game_id), MAX(g.game_date) FROM game_events ge JOIN games g ON ge.game_id = g.id WHERE g.id >= 2025020000')
print(f'Latest PBP game: {cur.fetchone()}')

# Check player stats
cur.execute('SELECT COUNT(*), COUNT(DISTINCT game_id) FROM player_game_stats WHERE game_id >= 2025020000')
print(f'Player stats: {cur.fetchone()}')

cur.close()
conn.close()
"
```

---

## 🆘 Troubleshooting

### Error: "Game not found in local DB"
**Solution**: Run `populate_games.py` first to ensure all games are in the schedule.

### Error: "Database connection failed"
**Solution**: Check that `FANTASY_DATABASE_URL` environment variable is set:
```bash
echo $FANTASY_DATABASE_URL
```

### Error: "Module not found"
**Solution**: Install dependencies:
```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API"
pip3 install -r requirements.txt
```

### Scripts are slow
**Solution**: Add `--continue-on-error` flag to skip games that fail and continue processing.

---

## 📁 Script Locations

- **Main Runner**: `data-digging/scripts/run_nhl_ingestion.py`
- **NHL API Scripts**: `data-digging/scripts/ingestion/nhl_api/`
  - `populate_games.py`
  - `populate_play_by_play.py`
  - `populate_player_game_stats.py`
  - `populate_shift_charts.py`
  - `populate_players.py`
  - `populate_teams.py`
  - `populate_player_details_from_nhl.py`

---

## 💡 Next Steps

1. **Immediate**: Run backfill to catch up on missing 5 weeks
2. **Short-term**: Set up automated daily ingestion
3. **Long-term**: Monitor data quality and set up alerts for ingestion failures


