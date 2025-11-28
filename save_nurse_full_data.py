#!/usr/bin/env python3
"""
Save Darnell Nurse's complete Edge data to JSON file
"""

from nhlpy import NHLClient
import json

client = NHLClient()
nurse_id = 8477498
season = "20242025"

print("Fetching Darnell Nurse's complete Edge speed data...")

# Get speed detail
speed_data = client.edge.skater_skating_speed_detail(
    player_id=nurse_id,
    season=season
)

# Get overall detail
overall_data = client.edge.skater_detail(
    player_id=nurse_id,
    season=season
)

# Combine into one JSON
full_data = {
    "player": {
        "id": nurse_id,
        "name": "Darnell Nurse",
        "season": season
    },
    "speed_detail": speed_data,
    "overall_edge_data": overall_data
}

# Save to file
output_file = "darnell_nurse_edge_data.json"
with open(output_file, 'w') as f:
    json.dump(full_data, f, indent=2)

print(f"✅ Saved to {output_file}")
print(f"\nTop 10 speeds:")
for i, event in enumerate(speed_data.get('topSkatingSpeeds', [])[:10], 1):
    speed = event.get('skatingSpeed', {}).get('imperial')
    date = event.get('gameDate')
    print(f"  #{i}: {speed} MPH on {date}")

