"""
Quick script to populate game_events table with 2025 season play-by-play data
"""
import psycopg2
import requests
import json
from datetime import datetime

DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

def fetch_schedule(season="20252026"):
    """Get all games for the 2025 season"""
    start_date = "2025-10-01"
    end_date = "2025-11-30"
    
    game_ids = set()
    check_date = start_date
    
    while check_date <= end_date:
        resp = requests.get(f"https://api-web.nhle.com/v1/schedule/{check_date}")
        if resp.status_code == 200:
            data = resp.json()
            for day in data.get('gameWeek', []):
                for game in day.get('games', []):
                    if game.get('gameState') in ['OFF', 'FINAL']:
                        game_ids.add(game.get('id'))
        
        # Move forward 7 days
        from datetime import datetime, timedelta
        dt = datetime.strptime(check_date, "%Y-%m-%d")
        dt += timedelta(days=7)
        check_date = dt.strftime("%Y-%m-%d")
    
    return sorted(list(game_ids))

def fetch_pbp(game_id):
    """Fetch play-by-play data for a game"""
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return None

def insert_events(conn, game_id, pbp_data):
    """Insert play-by-play events into game_events table"""
    cur = conn.cursor()
    
    plays = pbp_data.get('plays', [])
    inserted = 0
    
    for play in plays:
        event_id = play.get('eventId')
        period_desc = play.get('periodDescriptor', {})
        details = play.get('details', {})
        
        # Extract data
        period = period_desc.get('number')
        time_in_period = play.get('timeInPeriod')
        event_type = play.get('typeDescKey')
        scorer_id = details.get('scoringPlayerId') if event_type == 'goal' else None
        
        try:
            # Check if event already exists
            cur.execute("SELECT 1 FROM game_events WHERE game_id = %s AND event_idx = %s", (game_id, event_id))
            if cur.fetchone():
                continue
                
            cur.execute("""
                INSERT INTO game_events 
                (game_id, event_idx, period, period_time, event_type, scorer_id, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                game_id,
                event_id,
                period,
                time_in_period,
                event_type,
                scorer_id,
                json.dumps(play)
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting event {event_id}: {e}")
            continue
    
    conn.commit()
    return inserted

def main():
    print("Fetching 2025 season schedule...")
    game_ids = fetch_schedule()
    print(f"Found {len(game_ids)} completed games")
    
    conn = psycopg2.connect(DB_URL)
    
    for i, game_id in enumerate(game_ids):
        print(f"[{i+1}/{len(game_ids)}] Processing game {game_id}...")
        
        pbp_data = fetch_pbp(game_id)
        if pbp_data:
            inserted = insert_events(conn, game_id, pbp_data)
            print(f"  ✓ Inserted {inserted} events")
        else:
            print(f"  ✗ Failed to fetch data")
    
    conn.close()
    print("\n✅ Ingestion complete!")

if __name__ == "__main__":
    main()

