#!/bin/bash
# Nightly NHL API Data Ingestion Pipeline
# Runs in correct dependency order: Teams → Players → Games → PBP → Stats → Shifts

set -e

echo "=========================================="
echo "NHL NIGHTLY DATA INGESTION PIPELINE"
echo "Started: $(date)"
echo "=========================================="

# Get current season (defaults to 2025-26)
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%m)

# If we're past October, use current year, otherwise previous year
if [ $CURRENT_MONTH -ge 10 ]; then
    SEASON=$CURRENT_YEAR
else
    SEASON=$((CURRENT_YEAR - 1))
fi

echo "Season: $SEASON-$((SEASON + 1))"
echo ""

cd /app/data-digging
export PYTHONPATH="/app/data-digging:$PYTHONPATH"

# Step 1: Update Teams (rarely changes, but quick to run)
echo "=========================================="
echo "STEP 1: Updating Teams"
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_teams.py || echo "⚠️  Teams update failed (non-critical)"
echo ""

# Step 2: Update Players (runs quickly, only adds new players)
echo "=========================================="
echo "STEP 2: Updating Players"  
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_players.py || echo "⚠️  Players update failed (non-critical)"
echo ""

# Step 3: Update Games/Schedule
echo "=========================================="
echo "STEP 3: Updating Games/Schedule"
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_games.py $SEASON || echo "⚠️  Games update failed"
echo ""

# Step 4: Ingest Play-by-Play (only new games)
echo "=========================================="
echo "STEP 4: Ingesting Play-by-Play Events"
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_play_by_play.py --all --season ${SEASON}${SEASON+1} --game-type 2
echo ""

# Step 5: Ingest Player Stats (only new games)
echo "=========================================="
echo "STEP 5: Ingesting Player Game Stats"
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_player_game_stats_v2.py $SEASON --game-type 2
echo ""

# Step 6: Ingest Shift Charts (only new games)
echo "=========================================="
echo "STEP 6: Ingesting Shift Charts"
echo "=========================================="
python3 scripts/ingestion/nhl_api/populate_shift_charts.py --all --season ${SEASON}${SEASON+1} --game-type 2
echo ""

# Summary
echo "=========================================="
echo "✅ NIGHTLY INGESTION COMPLETE"
echo "Finished: $(date)"
echo "=========================================="


