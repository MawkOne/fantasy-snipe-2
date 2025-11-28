import requests
import json
import sys

def list_goals(game_id):
    """
    Fetches all goals from a game and prints their Event IDs and Animation URLs.
    """
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    print(f"Fetching PBP for Game {game_id}...")
    
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        goals = []
        for play in data.get('plays', []):
            if play.get('typeDescKey') == 'goal':
                goals.append(play)
        
        if not goals:
            print("No goals found.")
            return

        print(f"\nFound {len(goals)} Goals:\n")
        print(f"{'Time':<10} | {'Event ID':<10} | {'Scorer ID':<10} | {'Animation URL'}")
        print("-" * 80)
        
        for g in goals:
            details = g.get('details', {})
            ppt_url = g.get('pptReplayUrl', 'N/A')
            print(f"{g.get('timeInPeriod'):<10} | {g.get('eventId'):<10} | {details.get('scoringPlayerId'):<10} | {ppt_url}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python list_goals.py <GAME_ID>")
        print("Example: python list_goals.py 2025020360")
    else:
        list_goals(sys.argv[1])

