# NHL Nightly Data Ingestion Setup

## 🌙 Automated Nightly Pipeline

Your NHL data ingestion now runs automatically **every night at 2:00 AM PST**.

### 📋 Pipeline Order (Correct Dependencies)

1. **Teams** - Base team data
2. **Players** - Player roster  
3. **Games/Schedule** - Game schedule
4. **Play-by-Play** - Game events (needs games)
5. **Player Stats** - Player statistics (needs games + players)
6. **Shift Charts** - Shift data (needs games + players)

---

## 🚀 Setup Instructions

### 1. Build and Deploy the Docker Image

```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API"

# Build the image
gcloud builds submit --config cloudbuild.ingestion.yaml --timeout=20m
```

### 2. Setup Cloud Scheduler

```bash
chmod +x setup_nightly_scheduler.sh
./setup_nightly_scheduler.sh
```

This will:
- Create the Cloud Run job `nhl-nightly-ingestion`
- Create a Cloud Scheduler that triggers it at 2am PST daily
- Configure proper environment variables

---

## 📊 Monitoring & Management

### Manual Execution

Run the ingestion manually anytime:

```bash
gcloud run jobs execute nhl-nightly-ingestion --region us-central1
```

### View Logs

```bash
# Recent logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=nhl-nightly-ingestion" \
  --limit 50 \
  --format=json

# Live tail
gcloud alpha logging tail "resource.type=cloud_run_job AND resource.labels.job_name=nhl-nightly-ingestion"
```

### Check Scheduler Status

```bash
gcloud scheduler jobs describe nhl-nightly-scheduler \
  --location us-central1
```

### Pause/Resume Scheduler

```bash
# Pause
gcloud scheduler jobs pause nhl-nightly-scheduler --location us-central1

# Resume  
gcloud scheduler jobs resume nhl-nightly-scheduler --location us-central1
```

---

## 🗓️ Schedule Details

- **Frequency**: Daily
- **Time**: 2:00 AM Pacific Time (10:00 AM UTC)
- **Duration**: ~30-60 minutes (depends on number of games)
- **Timezone**: America/Los_Angeles

---

## 🔧 Configuration

### Environment Variables

Set in the Cloud Run job:

- `DATABASE_URL` - PostgreSQL connection string
- `SEASON` - Auto-detected from current date (optional override)
- `GAME_TYPE` - 2 = Regular season (default)

### Update Configuration

```bash
gcloud run jobs update nhl-nightly-ingestion \
  --region us-central1 \
  --set-env-vars NEW_VAR=value
```

---

## 📁 Files

- `Dockerfile.ingestion` - Docker image definition
- `cloudbuild.ingestion.yaml` - Cloud Build configuration
- `run_nightly_ingestion.sh` - Main orchestration script
- `setup_nightly_scheduler.sh` - Scheduler setup script

### Individual Ingestion Scripts

Located in `data-digging/scripts/ingestion/nhl_api/`:

- `populate_teams.py` 
- `populate_players.py`
- `populate_games.py`
- `populate_play_by_play.py`
- `populate_player_game_stats_v2.py` ⭐ (NEW - uses modern NHL API)
- `populate_shift_charts.py`

---

## ✅ What Gets Updated

Each night, the pipeline will:

1. ✅ Check for new teams (rare)
2. ✅ Add any new players
3. ✅ Update the game schedule
4. ✅ Ingest play-by-play for any **new** games (skips existing)
5. ✅ Ingest player stats for any **new** games (skips existing)
6. ✅ Ingest shift data for any **new** games (skips existing)

**Smart Skip Logic**: Only processes games that don't already have data, making it fast and efficient!

---

## 🐛 Troubleshooting

### Job Failed

Check logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND severity>=ERROR" --limit 20
```

### Rate Limiting (429 Errors)

The scripts have built-in retry logic with exponential backoff. If persistent:
- Increase delays in the scripts
- Reduce concurrency

### Database Connection Issues

Verify the `DATABASE_URL` is correct:
```bash
gcloud run jobs describe nhl-nightly-ingestion \
  --region us-central1 \
  --format="value(template.template.containers[0].env)"
```

### Scheduler Not Triggering

Check scheduler status:
```bash
gcloud scheduler jobs list --location us-central1
```

Manually trigger to test:
```bash
gcloud scheduler jobs run nhl-nightly-scheduler --location us-central1
```

---

## 📈 Expected Data Growth

Per day during season:
- ~8-15 NHL games
- ~5,000-7,000 play-by-play events  
- ~400-600 player stat records
- ~3,000-5,000 shift records

---

## 🎯 Success Criteria

After each run, verify:

```sql
-- Check latest data
SELECT 
    MAX(game_date) as latest_game,
    COUNT(*) as total_games
FROM games 
WHERE id >= 2025020000;

-- Check events for recent games
SELECT COUNT(*) FROM game_events 
WHERE game_id IN (
    SELECT id FROM games 
    WHERE game_date >= CURRENT_DATE - INTERVAL '2 days'
);
```

---

## 🔄 Updating the Pipeline

To modify the ingestion logic:

1. Edit scripts in `data-digging/scripts/ingestion/nhl_api/`
2. Rebuild the Docker image:
   ```bash
   gcloud builds submit --config cloudbuild.ingestion.yaml
   ```
3. The Cloud Run job will automatically use the new image on next run

---

## 📞 Support

- **NHL API Reference**: https://github.com/Zmalski/NHL-API-Reference
- **Cloud Run Docs**: https://cloud.google.com/run/docs/
- **Cloud Scheduler Docs**: https://cloud.google.com/scheduler/docs/

---

**Last Updated**: November 28, 2025


