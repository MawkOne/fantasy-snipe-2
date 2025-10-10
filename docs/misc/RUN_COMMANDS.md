## Run Commands (GCE VM)

All commands below assume the code is on the VM at `/home/markhenderson/NHL-API`.

### Use the venv
- Activate:
  ```bash
  source /home/markhenderson/NHL-API/.venv/bin/activate
  ```
- Or call the venv python directly (no activation needed):
  ```bash
  /home/markhenderson/NHL-API/.venv/bin/python --version
  ```

### Teams
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_teams.py
```

### Players (recent seasons)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_players.py
```

### Player details (bio)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_player_details.py
```

### Goalie game logs
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_goalies.py 2024
```

### Team season schedule → `games`
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_team_season_schedule.py 2024
```

### League schedule by date → `games`
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_schedule_by_date.py 2024-10-01 2024-10-31
```

### Populate games from player logs (backfill)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_games.py 2024
```

### Shift charts (single game)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_shift_charts.py 2023020001
```

### Shift charts (all games; optional filters)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_shift_charts.py --all --season 20242025 --game-type 2
```

### Play-by-Play (single game)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_play_by_play.py 2023020001
# Re-ingest a game
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_play_by_play.py 2023020001 --refresh
```

### Play-by-Play (all games; optional filters)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_play_by_play.py --all
# With filters
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_play_by_play.py --all --season 20242025 --game-type 2
```

### Compute per-shift metrics (streamed/batched)
Idempotent; safe to re-run.
```bash
# Streamed (recommended for large runs)
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/compute_shift_metrics.py \
  --batch-commit 100 --player-chunk 25 --shift-chunk 300

# Scope to a single game
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/compute_shift_metrics.py \
  --game-id 2023020001 --batch-commit 100 --player-chunk 25 --shift-chunk 300

# Scope to a single player
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/compute_shift_metrics.py \
  --player-id 8478402 --batch-commit 50 --shift-chunk 200
```

### Background worker (runs one game at a time; low memory)
Runs continuously in the background, processing one `game_id` per subprocess, keeping memory bounded. Logs to `logs/shift_metrics_worker.log`.
```bash
# Start (no venv activation needed)
nohup /home/markhenderson/NHL-API/.venv/bin/python \
  /home/markhenderson/NHL-API/scripts/shift_metrics_background_worker.py \
  --repo-root /home/markhenderson/NHL-API \
  --python-exe /home/markhenderson/NHL-API/.venv/bin/python \
  --batch-commit 100 --player-chunk 25 --shift-chunk 300 \
  --loop --sleep 2 >> /home/markhenderson/NHL-API/logs/shift_metrics_worker.log 2>&1 &

# View tail of logs
tail -n 200 -f /home/markhenderson/NHL-API/logs/shift_metrics_worker.log

# To stop the worker (find pid, then kill)
pgrep -f "shift_metrics_background_worker.py" | xargs -r kill
```

### Career stats (from local logs)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_player_career_stats.py
```

### Career stats (from NHL API; requires nhl-api-py)
```bash
/home/markhenderson/NHL-API/.venv/bin/python /home/markhenderson/NHL-API/scripts/populate_player_career_stats_api.py
```

### Notes
- All scripts call `create_tables()` and skip existing rows.
- Use smaller `--batch-commit` / chunk sizes to reduce transaction time.
- If not using activation, always call the venv python via absolute path as shown above.

