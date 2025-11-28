#!/usr/bin/env python3
"""
Simple test script to ingest play-by-play for recent 2025 games
"""

import os
import requests
import psycopg2
import json
from datetime import datetime

DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

def fetch_games_from_date(date_str):
    """Fetch games from NHL API for a specific date"""
    url = f"https://api-web.nhle.com/v1/score/{date_str}"
    print(f"Fetching games for {date_str}...")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        games = data.get('games', [])
        print(f"Found {len(games)} games")
        return games
    except Exception as e:
        print(f"Error fetching games: {e}")
        return []

def fetch_pbp_for_game(game_id):
    """Fetch play-by-play data for a game"""
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    print(f"  Fetching PBP for game {game_id}...")
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 404:
            print(f"  Game {game_id} not found (404)")
            return None
        r.raise_for_status()
        data = r.json()
        plays = data.get('plays', [])
        print(f"  Found {len(plays)} events")
        return plays
    except Exception as e:
        print(f"  Error fetching PBP: {e}")
        return None

def insert_pbp_to_db(conn, game_id, plays):
    """Insert play-by-play events into database"""
    cur = conn.cursor()
    
    # Check if game exists
    cur.execute("SELECT id FROM games WHERE id = %s", (game_id,))
    if not cur.fetchone():
        print(f"  Game {game_id} not in database - skipping")
        cur.close()
        return 0
    
    # Check existing events
    cur.execute("SELECT COUNT(*) FROM game_events WHERE game_id = %s", (game_id,))
    existing_count = cur.fetchone()[0]
    
    if existing_count > 0:
        print(f"  Game {game_id} already has {existing_count} events - skipping")
        cur.close()
        return 0
    
    inserted = 0
    for play in plays:
        try:
            event_idx = play.get('eventId')
            period = play.get('periodDescriptor', {}).get('number')
            period_time = play.get('timeInPeriod')
            period_time_remaining = play.get('timeRemaining')
            event_type = play.get('typeDescKey')
            
            # Get description - handle different formats
            details = play.get('details', {})
            description = details.get('eventDescription') or details.get('description') or event_type or ''
            
            # Get team info
            team_abbrev = details.get('eventOwnerTeamId')
            team_id = None
            if team_abbrev:
                cur.execute("SELECT id FROM teams WHERE tri_code = %s OR raw_tricode = %s", 
                           (team_abbrev, team_abbrev))
                team_row = cur.fetchone()
                if team_row:
                    team_id = team_row[0]
            
            # Get coordinates
            coords_x = details.get('xCoord')
            coords_y = details.get('yCoord')
            
            # Get primary player
            primary_player_id = details.get('scoringPlayerId') or details.get('shootingPlayerId') or details.get('hitteePlayerId') or details.get('playerId')
            
            # Insert event
            cur.execute("""
                INSERT INTO game_events 
                (game_id, event_idx, period, period_time, period_time_remaining, 
                 event_type, description, team_id, primary_player_id, 
                 coordinates_x, coordinates_y, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                game_id, event_idx, period, period_time, period_time_remaining,
                event_type, description, team_id, primary_player_id,
                coords_x, coords_y, json.dumps(play)
            ))
            inserted += 1
            
        except Exception as e:
            print(f"  Error inserting event: {e}")
            continue
    
    conn.commit()
    cur.close()
    print(f"  ✅ Inserted {inserted} events for game {game_id}")
    return inserted

def main():
    # Test with November 26, 2025
    test_date = "2025-11-26"
    
    print(f"\n{'='*80}")
    print(f"Testing NHL PBP Ingestion for {test_date}")
    print(f"{'='*80}\n")
    
    # Fetch games from that date
    games = fetch_games_from_date(test_date)
    
    if not games:
        print("No games found for that date")
        return
    
    # Connect to database
    conn = psycopg2.connect(DB_URL)
    
    total_inserted = 0
    for game in games:
        game_id = game.get('id')
        if not game_id:
            continue
        
        home_team = game.get('homeTeam', {}).get('abbrev')
        away_team = game.get('awayTeam', {}).get('abbrev')
        print(f"\nGame {game_id}: {away_team} @ {home_team}")
        
        # Fetch PBP
        plays = fetch_pbp_for_game(game_id)
        if not plays:
            continue
        
        # Insert to DB
        inserted = insert_pbp_to_db(conn, game_id, plays)
        total_inserted += inserted
    
    conn.close()
    
    print(f"\n{'='*80}")
    print(f"✅ Test Complete: Inserted {total_inserted} events across {len(games)} games")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()


