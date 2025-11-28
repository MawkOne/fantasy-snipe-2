"""
NHL 2025 Season - Edge Tracking Data Analysis

Available Data:
- 2,392 goals from 396 games
- 599 unique scorers
- High-fidelity X/Y tracking at 16.94 FPS
- Pre-calculated velocities for all players and puck
"""

import psycopg2
import json
import pandas as pd
import numpy as np
from datetime import datetime

DB_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

def get_connection():
    return psycopg2.connect(DB_URL)

# ============================================================================
# 1. BASIC STATISTICS
# ============================================================================

def get_season_summary():
    """Get high-level stats for the season"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_goals,
            COUNT(DISTINCT game_id) as total_games,
            COUNT(DISTINCT scorer_player_id) as unique_scorers,
            MIN(game_date) as first_game,
            MAX(game_date) as last_game
        FROM tracking_goals 
        WHERE game_id >= 2025000000
    """)
    
    result = cur.fetchone()
    conn.close()
    
    return {
        'total_goals': result[0],
        'total_games': result[1],
        'unique_scorers': result[2],
        'first_game': result[3],
        'last_game': result[4],
        'goals_per_game': round(result[0] / result[1], 2)
    }

# ============================================================================
# 2. PLAYER ANALYSIS
# ============================================================================

def get_top_scorers(limit=10):
    """Get top goal scorers with their goal counts"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            scorer_player_id,
            COUNT(*) as goals
        FROM tracking_goals 
        WHERE game_id >= 2025000000
        GROUP BY scorer_player_id
        ORDER BY goals DESC
        LIMIT %s
    """, (limit,))
    
    results = cur.fetchall()
    conn.close()
    
    return pd.DataFrame(results, columns=['player_id', 'goals'])

# ============================================================================
# 3. SHOT ANALYSIS
# ============================================================================

def analyze_shot_speeds():
    """Analyze puck velocities at goal scoring moments"""
    conn = get_connection()
    cur = conn.cursor()
    
    # This will extract max puck speed from each goal
    cur.execute("""
        SELECT 
            game_id,
            event_id,
            tracking_data->'data' as frames
        FROM tracking_goals 
        WHERE game_id >= 2025000000
        LIMIT 100
    """)
    
    shot_speeds = []
    for row in cur.fetchall():
        game_id, event_id, frames = row
        # Extract puck velocities (every 4th value starting at index 3)
        max_speed = 0
        for frame in frames:
            if len(frame) > 3:
                puck_speed = frame[3]  # Puck velocity is 4th value
                if puck_speed > max_speed:
                    max_speed = puck_speed
        
        shot_speeds.append({
            'game_id': game_id,
            'event_id': event_id,
            'max_puck_speed': max_speed
        })
    
    conn.close()
    return pd.DataFrame(shot_speeds)

# ============================================================================
# 4. SPATIAL ANALYSIS
# ============================================================================

def get_goal_locations():
    """Extract final puck positions for all goals"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            game_id,
            event_id,
            (tracking_data->'data'->-1->>0)::bigint as final_timestamp,
            (tracking_data->'data'->-1->>1)::float as final_x,
            (tracking_data->'data'->-1->>2)::float as final_y
        FROM tracking_goals 
        WHERE game_id >= 2025000000
    """)
    
    results = cur.fetchall()
    conn.close()
    
    return pd.DataFrame(results, columns=['game_id', 'event_id', 'timestamp', 'x', 'y'])

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("NHL 2025 SEASON ANALYSIS")
    print("=" * 80)
    
    # 1. Season Summary
    print("\n1. SEASON SUMMARY")
    print("-" * 80)
    summary = get_season_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # 2. Top Scorers
    print("\n2. TOP 10 SCORERS")
    print("-" * 80)
    top_scorers = get_top_scorers(10)
    print(top_scorers.to_string(index=False))
    
    # 3. Goal Locations
    print("\n3. GOAL LOCATIONS (Sample)")
    print("-" * 80)
    locations = get_goal_locations()
    print(f"Total goals with location data: {len(locations)}")
    print(f"\nX-coordinate range: {locations['x'].min():.1f} to {locations['x'].max():.1f} inches")
    print(f"Y-coordinate range: {locations['y'].min():.1f} to {locations['y'].max():.1f} inches")
    print(f"\nSample locations:")
    print(locations.head(10).to_string(index=False))
    
    # 4. Shot Speeds
    print("\n4. SHOT SPEEDS (Sample of 100 goals)")
    print("-" * 80)
    speeds = analyze_shot_speeds()
    print(f"Average max puck speed: {speeds['max_puck_speed'].mean():.1f} mph")
    print(f"Max recorded speed: {speeds['max_puck_speed'].max():.1f} mph")
    print(f"Min recorded speed: {speeds['max_puck_speed'].min():.1f} mph")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

