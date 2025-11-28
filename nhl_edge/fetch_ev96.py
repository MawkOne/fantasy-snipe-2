import requests
import json

game_id = 2025020360
pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

print(f"Fetching PBP: {pbp_url}")
resp = requests.get(pbp_url)
data = resp.json()

# Find Event 96
event_96 = next((p for p in data.get('plays', []) if p.get('eventId') == 96), None)

if event_96:
    print("\n--- Event 96 Found ---")
    print(f"Type: {event_96.get('typeDescKey')}")
    print(f"Details: {json.dumps(event_96, indent=2)}")
    
    if 'pptReplayUrl' in event_96:
        print(f"pptReplayUrl: {event_96['pptReplayUrl']}")
    else:
        print("No pptReplayUrl for this event.")
else:
    print("\nEvent 96 NOT found in PBP.")

# Check a goal to see the URL pattern
goal = next((p for p in data.get('plays', []) if p.get('typeDescKey') == 'goal'), None)
if goal:
    print("\n--- Example Goal URL Pattern ---")
    print(f"Goal ID: {goal.get('eventId')}")
    print(f"URL: {goal.get('pptReplayUrl')}")
