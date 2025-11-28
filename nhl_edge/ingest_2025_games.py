"""
Quick script to populate games table with 2025 season data
"""
import psycopg2
import requests
from datetime import datetime

DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

TEAM_ABBREVS = [
    "ANA", "ARI", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SJS", "SEA", "STL", "TBL", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]

def fetch_team_schedule(team, season=20252026):
    """Fetch schedule for one team"""
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}"
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("games", [])
    except Exception as e:
        print(f"Error fetching {team}: {e}")
    return []

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Get existing game IDs
    cur.execute("SELECT id FROM games WHERE id >= 2025000000")
    existing = {row[0] for row in cur.fetchall()}
    print(f"Found {len(existing)} existing 2025 games in database")
    
    all_games = {}
    print("Fetching schedules from all teams...")
    
    for team in TEAM_ABBREVS:
        print(f"  Fetching {team}...")
        games = fetch_team_schedule(team)
        
        for g in games:
            gid = g.get("id")
            if gid and gid not in existing and gid >= 2025000000:
                all_games[gid] = g
    
    print(f"\nFound {len(all_games)} new games to insert")
    
    inserted = 0
    for gid, g in all_games.items():
        try:
            cur.execute("""
                INSERT INTO games 
                (id, season, game_type, game_date, game_state, home_team_id, away_team_id, home_score, away_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                gid,
                g.get('season'),
                g.get('gameType'),
                g.get('startTimeUTC') or g.get('gameDate'),
                g.get('gameState'),
                (g.get('homeTeam') or {}).get('id'),
                (g.get('awayTeam') or {}).get('id'),
                (g.get('homeTeam') or {}).get('score'),
                (g.get('awayTeam') or {}).get('score')
            ))
            inserted += 1
            
            if inserted % 50 == 0:
                conn.commit()
                print(f"  Committed {inserted} games...")
                
        except Exception as e:
            print(f"Error inserting game {gid}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully inserted {inserted} games!")

if __name__ == "__main__":
    main()

