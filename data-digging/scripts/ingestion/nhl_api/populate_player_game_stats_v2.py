#!/usr/bin/env python3
"""
Populate player_game_stats using NEW NHL API (api-web.nhle.com)
Based on: https://github.com/Zmalski/NHL-API-Reference
"""
import os
import sys
import time
import argparse
import requests
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Game, PlayerGameStats, GoalieGameStats, create_tables


def upsert_stats_for_game(session, game_id: int) -> int:
    """
    Fetch and upsert player stats for a single game using NEW NHL API
    API Reference: https://github.com/Zmalski/NHL-API-Reference
    """
    # Use NEW NHL API endpoint
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
    
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 404:
            print(f"Game {game_id} not found (404)")
            return 0
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error on game {game_id}: {e}")
        return 0
    except Exception as e:
        print(f"Error fetching game {game_id}: {e}")
        return 0

    added = 0
    
    # Process both home and away teams
    for side in ['homeTeam', 'awayTeam']:
        team_data = data.get(side, {})
        team_id = team_data.get('id')
        
        # Process forwards
        for player in team_data.get('forwards', []):
            added += process_skater(session, game_id, team_id, player)
        
        # Process defense
        for player in team_data.get('defense', []):
            added += process_skater(session, game_id, team_id, player)
        
        # Process goalies
        for player in team_data.get('goalies', []):
            added += process_goalie(session, game_id, team_id, player)
    
    if added > 0:
        session.commit()
        print(f"✅ Game {game_id}: Added {added} player stat rows")
    
    return added


def process_skater(session, game_id: int, team_id: int, player: dict) -> int:
    """Process a skater's stats"""
    try:
        player_id = player.get('playerId')
        if not player_id:
            return 0
        
        # Check if already exists
        existing = session.query(PlayerGameStats).filter(
            PlayerGameStats.player_id == player_id,
            PlayerGameStats.game_id == game_id
        ).first()
        
        if existing:
            return 0  # Skip if already exists
        
        # Extract stats
        goals = player.get('goals', 0)
        assists = player.get('assists', 0)
        points = player.get('points', 0)
        plus_minus = player.get('plusMinus', 0)
        pim = player.get('pim', 0)
        shots = player.get('sog', 0)  # shots on goal
        
        # Power play stats
        power_play_goals = player.get('powerPlayGoals', 0)
        
        # Shorthanded stats  
        shorthanded_goals = player.get('shorthandedGoals', 0)
        
        # Time on ice (in format "MM:SS")
        toi = player.get('toi', '0:00')
        
        # Create new record
        stat = PlayerGameStats(
            player_id=player_id,
            game_id=game_id,
            team_id=team_id,
            goals=goals,
            assists=assists,
            points=points,
            plus_minus=plus_minus,
            pim=pim,
            shots=shots,
            power_play_goals=power_play_goals,
            shorthanded_goals=shorthanded_goals,
            toi=toi
        )
        
        session.add(stat)
        return 1
        
    except Exception as e:
        print(f"Error processing skater {player.get('playerId')}: {e}")
        return 0


def process_goalie(session, game_id: int, team_id: int, player: dict) -> int:
    """Process a goalie's stats"""
    try:
        player_id = player.get('playerId')
        if not player_id:
            return 0
        
        # Check if already exists
        existing = session.query(GoalieGameStats).filter(
            GoalieGameStats.player_id == player_id,
            GoalieGameStats.game_id == game_id
        ).first()
        
        if existing:
            return 0  # Skip if already exists
        
        # Extract goalie stats
        shots_against = player.get('shotsAgainst', 0)
        saves = player.get('saves', 0)
        goals_against = player.get('goalsAgainst', 0)
        
        # Calculate save percentage
        save_pct = player.get('savePctg', 0.0)
        
        # Even strength stats
        even_strength_shots_against = player.get('evenStrengthShotsAgainst', 0)
        even_strength_saves = player.get('evenStrengthSaves', 0)
        
        # Power play stats
        power_play_shots_against = player.get('powerPlayShotsAgainst', 0)
        power_play_saves = player.get('powerPlaySaves', 0)
        
        # Shorthanded stats
        shorthanded_shots_against = player.get('shorthandedShotsAgainst', 0)
        shorthanded_saves = player.get('shorthandedSaves', 0)
        
        # Time on ice
        toi = player.get('toi', '0:00')
        
        # Win/Loss (if available)
        # Note: decision field might be 'W', 'L', 'O' (OT loss)
        decision = player.get('decision')  
        
        # Create new record
        stat = GoalieGameStats(
            player_id=player_id,
            game_id=game_id,
            team_id=team_id,
            shots_against=shots_against,
            saves=saves,
            goals_against=goals_against,
            save_percentage=save_pct,
            even_strength_shots_against=even_strength_shots_against,
            even_strength_saves=even_strength_saves,
            power_play_shots_against=power_play_shots_against,
            power_play_saves=power_play_saves,
            shorthanded_shots_against=shorthanded_shots_against,
            shorthanded_saves=shorthanded_saves,
            toi=toi
        )
        
        session.add(stat)
        return 1
        
    except Exception as e:
        print(f"Error processing goalie {player.get('playerId')}: {e}")
        return 0


def populate_player_game_stats(season_start_year: int, game_type: int = 2):
    """
    Populate player_game_stats for all games in a season
    
    Args:
        season_start_year: Starting year (e.g., 2025 for 2025-26 season)
        game_type: 2 = Regular season, 3 = Playoffs
    """
    season_id = int(f"{season_start_year}{season_start_year + 1}")
    
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")
    
    # Ensure tables exist
    try:
        create_tables()
        print("Tables created successfully.")
    except Exception:
        pass
    
    try:
        # Get all games for the season
        games = session.query(Game.id).filter(
            Game.season == season_id,
            Game.game_type == game_type
        ).all()
        
        game_ids = [g[0] for g in games]
        print(f"Found {len(game_ids)} games for season {season_id}.")
        
        processed = 0
        total_stats = 0
        
        for game_id in game_ids:
            # Check if we already have stats for this game
            existing_count = session.query(PlayerGameStats).filter(
                PlayerGameStats.game_id == game_id
            ).count()
            
            if existing_count > 0:
                continue  # Skip games we've already processed
            
            # Fetch and process with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    added = upsert_stats_for_game(session, game_id)
                    if added > 0:
                        total_stats += added
                        processed += 1
                    break  # Success, exit retry loop
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        # Rate limited, wait longer and retry
                        wait_time = (attempt + 1) * 2
                        print(f"Rate limited, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        break  # Give up after retries
            
            # Delay to be respectful to API (increased to avoid rate limits)
            time.sleep(0.5)
        
        print(f"\n{'='*80}")
        print(f"✅ Finished. Processed {processed} games.")
        print(f"✅ Added {total_stats} player stat records.")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Critical error: {e}")
        session.rollback()
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate player_game_stats from NEW NHL API (api-web.nhle.com)"
    )
    parser.add_argument(
        "season_start_year", 
        type=int, 
        help="Starting year of the season, e.g., 2025 for 2025-26"
    )
    parser.add_argument(
        "--game-type", 
        type=int, 
        default=2, 
        help="2=Regular, 3=Playoffs"
    )
    args = parser.parse_args()
    
    populate_player_game_stats(args.season_start_year, game_type=args.game_type)

