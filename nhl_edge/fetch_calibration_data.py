from nhlpy import NHLClient
import json

# Players in Goal 97 (Game 2025020360)
players = [
    {"id": 8477934, "name": "Leon Draisaitl", "team": "EDM"},
    {"id": 8482740, "name": "Wyatt Johnston", "team": "DAL"},
    {"id": 8480803, "name": "Evan Bouchard", "team": "EDM"}
]

client = NHLClient()

print(f"{'='*60}")
print(f"  OFFICIAL TOP SPEEDS (Calibration Data)")
print(f"{'='*60}")

for p in players:
    print(f"\nFetching data for {p['name']} ({p['team']})...")
    try:
        # Try 20252026 first (Current simulated season)
        season = "20252026"
        data = client.edge.skater_skating_speed_detail(player_id=p['id'], season=season)
        
        # If empty/fail, try 20242025 as fallback
        if not data.get('topSkatingSpeeds'):
            print(f"  -> No data for {season}, trying 20242025...")
            season = "20242025"
            data = client.edge.skater_skating_speed_detail(player_id=p['id'], season=season)

        top_speeds = data.get('topSkatingSpeeds', [])
        
        if top_speeds:
            print(f"  Season: {season}")
            print(f"  Top 3 Speeds Recorded:")
            for i, record in enumerate(top_speeds[:3]):
                speed = record.get('skatingSpeed', {}).get('imperial', 0)
                game_date = record.get('gameDate')
                print(f"    {i+1}. {speed:.2f} MPH (on {game_date})")
        else:
            print("  -> No top speed data found.")

    except Exception as e:
        print(f"  -> Error: {e}")

print(f"\n{'='*60}")

