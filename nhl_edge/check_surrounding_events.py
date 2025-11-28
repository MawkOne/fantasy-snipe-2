import requests
import json

game_id = 2025020360
pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

resp = requests.get(pbp_url)
data = resp.json()
plays = data.get('plays', [])

# Find index of Goal 97
for i, p in enumerate(plays):
    if p.get('eventId') == 97:
        print(f"--- Goal 97 found at index {i} ---")
        
        # Print surrounding events
        start = max(0, i-2)
        end = min(len(plays), i+3)
        
        for j in range(start, end):
            e = plays[j]
            print(f"Index {j} | ID: {e.get('eventId')} | Type: {e.get('typeDescKey')} | Period: {e.get('periodDescriptor', {}).get('number')} | Time: {e.get('timeInPeriod')}")
        break

