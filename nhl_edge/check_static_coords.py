import requests
import json

game_id = 2025020360
pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

resp = requests.get(pbp_url)
data = resp.json()
plays = data.get('plays', [])

print("Checking for location data in non-goal events...")

events_to_check = ['shot-on-goal', 'blocked-shot', 'hit', 'faceoff']
found_types = set()

for p in plays:
    etype = p.get('typeDescKey')
    if etype in events_to_check and etype not in found_types:
        print(f"\n--- {etype} (ID: {p.get('eventId')}) ---")
        # Print specific location details if they exist
        details = p.get('details', {})
        print(f"x: {details.get('xCoord')}, y: {details.get('yCoord')}")
        print(f"Zone: {details.get('zoneCode')}")
        # Check for any other potential url
        print(f"Keys: {list(p.keys())}")
        found_types.add(etype)
        
print("\nFinished checking.")

