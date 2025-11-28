import requests
import json

# Game: 2025020360 (EDM vs DAL)
# Players to check:
# - Leon Draisaitl (EDM #29) - Scorer
# - Wyatt Johnston (DAL #53) - Assist? Or nearby

url = "https://api.nhle.com/stats/rest/en/skater/speed?isAggregate=false&isGame=true&sort=%5B%7B%22property%22:%22maxSpeed%22,%22direction%22:%22DESC%22%7D%5D&start=0&limit=100&factCayenneExp=gameId=2024020360&cayenneExp=gameId=2024020360"

# Note: GameID in stats API is often 202402xxxx for 2024-25 season, 
# but our PBP ID was 2025020360? Wait.
# Let's check the PBP again. The URL had 2025020360.
# This implies Season 2025-2026? Or is the user living in the future?
# User provided date: Nov 27, 2025. So this is the 2025-26 season.
# The standard public stats API might fail if this is a future sim or I need to guess the season ID.

# Let's try the standard endpoint for that game ID directly.
# The stats API uses gameId=YYYY02xxxx
game_id = 2025020360 

print(f"Fetching Speed Stats for Game {game_id}...")

# Attempt 1: Standard NHL Edge Stats API (if accessible publicly this way)
# Using the season 20252026
stats_url = f"https://api.nhle.com/stats/rest/en/skater/speed?isAggregate=false&isGame=true&sort=%5B%7B%22property%22:%22maxSpeed%22,%22direction%22:%22DESC%22%7D%5D&start=0&limit=100&factCayenneExp=gameId={game_id}&cayenneExp=gameId={game_id}"

try:
    resp = requests.get(stats_url)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Found {len(data.get('data', []))} records.")
        for row in data.get('data', [])[:5]:
            print(f"{row['skaterFullName']} ({row['teamAbbrev']}): {row['maxSpeed']} MPH")
    else:
        print(f"Failed: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")

