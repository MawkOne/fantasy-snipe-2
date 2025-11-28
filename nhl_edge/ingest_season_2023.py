import requests
import subprocess
import time
import sys

SEASON = "20232024"

def get_played_games(season):
    """
    Fetches the full schedule and returns a list of completed game IDs.
    """
    print(f"Fetching schedule for season {season}...")
    
    # Calculate start date based on season ID
    start_year = int(season[:4])
    start_date = f"{start_year}-10-01"
    end_date = f"{start_year + 1}-06-30"
    
    game_ids = set()
    check_date = start_date
    
    while check_date < end_date:
        resp = requests.get(f"https://api-web.nhle.com/v1/schedule/{check_date}")
        
        if resp.status_code != 200:
            break
            
        data = resp.json()
        week_dates = data.get('gameWeek', [])
        
        for day in week_dates:
            games = day.get('games', [])
            for game in games:
                game_id = game.get('id')
                game_state = game.get('gameState')
                
                # Only include regular season games (02xxxx) and playoffs (03xxxx)
                if game_state in ['OFF', 'FINAL'] and game_id:
                    game_id_str = str(game_id)
                    if '02' in game_id_str or '03' in game_id_str:
                        game_ids.add(game_id)
        
        # Move forward 7 days
        from datetime import datetime, timedelta
        dt = datetime.strptime(check_date, "%Y-%m-%d")
        dt += timedelta(days=7)
        check_date = dt.strftime("%Y-%m-%d")
            
    return sorted(list(game_ids))

def run_ingestion():
    print(f"--- INGESTION JOB FOR SEASON {SEASON} ---")
        
    games = get_played_games(SEASON)
    print(f"\nFound {len(games)} completed games for {SEASON}.")
    print("Starting Batch Ingestion...")
    
    for i, game_id in enumerate(games):
        print(f"[{i+1}/{len(games)}] Processing Game {game_id}...", flush=True)
        
        try:
            result = subprocess.run(
                [sys.executable, "nhl_edge/etl_pipeline.py", str(game_id)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Error processing {game_id}:")
                print(result.stderr)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    run_ingestion()

