#!/bin/bash
# Cloud Run Job script for player stats ingestion

set -e

echo "Starting NHL Player Stats Ingestion"
echo "===================================="

# Get season from environment variable or default to 2025
SEASON=${SEASON:-2025}
GAME_TYPE=${GAME_TYPE:-2}

echo "Season: $SEASON"
echo "Game Type: $GAME_TYPE"
echo ""

cd /app/data-digging

# Run the ingestion
python3 scripts/ingestion/nhl_api/populate_player_game_stats_v2.py $SEASON --game-type $GAME_TYPE

echo ""
echo "✅ Player stats ingestion complete!"


