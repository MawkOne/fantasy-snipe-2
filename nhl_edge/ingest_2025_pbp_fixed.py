"""
Populate game_events table with 2025 season play-by-play data
"""
import psycopg2
import requests
import json

DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

def get_2025_games():
    """Get all 2025 games from the games table"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id FROM games WHERE id >= 2025000000 AND game_type = 2 ORDER BY id")
    games = [row[0] for row in cur.fetchall()]
    conn.close()
    return games

def fetch_pbp(game_id):
    """Fetch play-by-play data"""
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"  Error fetching: {e}")
    return None

def insert_events(conn, game_id, pbp_data):
    """Insert events for one game"""
    cur = conn.cursor()
    
    plays = pbp_data.get('plays', [])
    inserted = 0
    skipped = 0
    
    for play in plays:
        event_idx = play.get('eventId')
        if not event_idx:
            continue
            
        # Check if exists
        cur.execute("SELECT 1 FROM game_events WHERE game_id = %s AND event_idx = %s", (game_id, event_idx))
        if cur.fetchone():
            skipped += 1
            continue
        
        period_desc = play.get('periodDescriptor', {})
        details = play.get('details', {})
        
        try:
            cur.execute("""
                INSERT INTO game_events 
                (game_id, event_idx, period, period_time, event_type, scorer_id, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                game_id,
                event_idx,
                period_desc.get('number'),
                play.get('timeInPeriod'),
                play.get('typeDescKey'),
                details.get('scoringPlayerId'),
                json.dumps(play)
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error on event {event_idx}: {e}")
            conn.rollback()
            return inserted, skipped
    
    conn.commit()
    return inserted, skipped

def main():
    print("Fetching 2025 games from database...")
    games = get_2025_games()
    print(f"Found {len(games)} games to process\n")
    
    conn = psycopg2.connect(DB_URL)
    
    total_inserted = 0
    total_skipped = 0
    
    for i, game_id in enumerate(games):
        print(f"[{i+1}/{len(games)}] Game {game_id}...", end=" ", flush=True)
        
        pbp = fetch_pbp(game_id)
        if pbp:
            inserted, skipped = insert_events(conn, game_id, pbp)
            total_inserted += inserted
            total_skipped += skipped
            print(f"✓ {inserted} new, {skipped} skipped")
        else:
            print("✗ Failed to fetch")
        
        if (i+1) % 50 == 0:
            print(f"\n--- Progress: {total_inserted} total events inserted ---\n")
    
    conn.close()
    print(f"\n✅ Complete! Inserted {total_inserted} events across {len(games)} games")

if __name__ == "__main__":
    main()

