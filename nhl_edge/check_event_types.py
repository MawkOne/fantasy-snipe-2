import requests
import json

def check_all_events(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    print(f"Fetching PBP for Game {game_id}...")
    
    try:
        resp = requests.get(url)
        data = resp.json()
        
        ppt_types = {}
        
        print(f"Total Plays: {len(data.get('plays', []))}")
        
        for play in data.get('plays', []):
            event_type = play.get('typeDescKey')
            ppt_url = play.get('pptReplayUrl')
            
            if ppt_url:
                if event_type not in ppt_types:
                    ppt_types[event_type] = 0
                ppt_types[event_type] += 1
                
        print("\nEvent types with Animation Data (pptReplayUrl):")
        if ppt_types:
            for et, count in ppt_types.items():
                print(f"- {et}: {count} events")
        else:
            print("No events found with pptReplayUrl.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_events(2025020360)

