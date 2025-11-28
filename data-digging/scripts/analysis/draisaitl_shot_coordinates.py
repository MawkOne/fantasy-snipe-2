#!/usr/bin/env python3
"""
Leon Draisaitl Shot Coordinates Analysis - 2024-25 Season
Show actual shot coordinates and create detailed ice map
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_draisaitl_shot_coordinates() -> pd.DataFrame:
    """
    Get Leon Draisaitl's shot data with coordinates for 2024-25 season
    """
    client = bigquery.Client()
    
    query = """
    SELECT 
        ge.id as event_id,
        ge.game_id,
        ge.period,
        ge.period_time,
        ge.event_type,
        ge.secondary_type,
        ge.coordinates_x,
        ge.coordinates_y,
        ge.team_id,
        ge.primary_player_id,
        p.full_name,
        g.season,
        g.game_date,
        -- Calculate shot distance from net
        SQRT(POWER(ge.coordinates_x, 2) + POWER(ge.coordinates_y, 2)) as shot_distance,
        -- Calculate shot angle (degrees from center line)
        ATAN2(ABS(ge.coordinates_y), ge.coordinates_x) * 180.0 / ACOS(-1) as shot_angle,
        -- Determine if it's a goal
        CASE WHEN ge.event_type = 'goal' THEN 1 ELSE 0 END as is_goal,
        -- Determine if it's a shot on goal
        CASE WHEN ge.event_type IN ('shot-on-goal', 'goal') THEN 1 ELSE 0 END as is_shot_on_goal,
        -- Determine if it's a missed shot
        CASE WHEN ge.event_type = 'missed-shot' THEN 1 ELSE 0 END as is_missed_shot,
        -- Determine if it's a blocked shot
        CASE WHEN ge.event_type = 'blocked-shot' THEN 1 ELSE 0 END as is_blocked_shot
    FROM `fantasy-snipe-ai.nhl_raw.game_events` ge
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON ge.primary_player_id = p.player_id
    JOIN `fantasy-snipe-ai.nhl_raw.games` g ON ge.game_id = g.id
    WHERE p.full_name = 'Leon Draisaitl'
    AND g.season = 20242025
    AND ge.event_type IN ('shot-on-goal', 'goal', 'missed-shot', 'blocked-shot')
    AND ge.coordinates_x IS NOT NULL 
    AND ge.coordinates_y IS NOT NULL
    ORDER BY g.game_date, ge.period, ge.period_time
    """
    
    return client.query(query).to_dataframe()

def create_detailed_shot_map(df: pd.DataFrame) -> None:
    """
    Create a detailed shot map showing actual coordinates
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Chart 1: All shots with coordinates
    shots_on_goal = df[df['is_shot_on_goal'] == 1]
    missed_shots = df[df['is_missed_shot'] == 1]
    blocked_shots = df[df['is_blocked_shot'] == 1]
    goals = df[df['is_goal'] == 1]
    
    # Plot missed shots in yellow
    ax1.scatter(missed_shots['coordinates_x'], missed_shots['coordinates_y'], 
               alpha=0.4, color='yellow', s=15, label=f'Missed Shots ({len(missed_shots)})')
    
    # Plot blocked shots in orange
    ax1.scatter(blocked_shots['coordinates_x'], blocked_shots['coordinates_y'], 
               alpha=0.4, color='orange', s=15, label=f'Blocked Shots ({len(blocked_shots)})')
    
    # Plot shots on goal (non-goals) in light blue
    shots_on_goal_non_goals = shots_on_goal[shots_on_goal['is_goal'] == 0]
    ax1.scatter(shots_on_goal_non_goals['coordinates_x'], shots_on_goal_non_goals['coordinates_y'], 
               alpha=0.5, color='lightblue', s=20, label=f'Shots on Goal (No Goal) ({len(shots_on_goal_non_goals)})')
    
    # Plot goals in red
    ax1.scatter(goals['coordinates_x'], goals['coordinates_y'], 
               alpha=0.9, color='red', s=60, label=f'Goals ({len(goals)})')
    
    # Add ice rink markings
    # Goal line
    ax1.axvline(x=0, color='black', linewidth=2, alpha=0.7)
    # Center line
    ax1.axvline(x=-25, color='red', linewidth=1, alpha=0.5, linestyle='--')
    # Faceoff circles (approximate)
    circle1 = plt.Circle((-20, 0), 15, fill=False, color='blue', alpha=0.3)
    circle2 = plt.Circle((-20, 0), 15, fill=False, color='blue', alpha=0.3)
    ax1.add_patch(circle1)
    
    ax1.set_xlabel('X Coordinate (feet from goal line)')
    ax1.set_ylabel('Y Coordinate (feet from center ice)')
    ax1.set_title('Leon Draisaitl Shot Map - All Shot Types\\n2024-25 Season (Actual Coordinates)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-50, 10)
    ax1.set_ylim(-25, 25)
    
    # Chart 2: Goals only with coordinate labels
    ax2.scatter(goals['coordinates_x'], goals['coordinates_y'], 
               alpha=0.8, color='red', s=80, label=f'Goals ({len(goals)})')
    
    # Add coordinate labels for goals
    for i, goal in goals.iterrows():
        ax2.annotate(f'({goal["coordinates_x"]:.0f}, {goal["coordinates_y"]:.0f})', 
                    (goal['coordinates_x'], goal['coordinates_y']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.7)
    
    # Add ice rink markings
    ax2.axvline(x=0, color='black', linewidth=2, alpha=0.7)
    ax2.axvline(x=-25, color='red', linewidth=1, alpha=0.5, linestyle='--')
    
    ax2.set_xlabel('X Coordinate (feet from goal line)')
    ax2.set_ylabel('Y Coordinate (feet from center ice)')
    ax2.set_title('Leon Draisaitl Goals - Exact Coordinates\\n2024-25 Season')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(-50, 10)
    ax2.set_ylim(-25, 25)
    
    plt.tight_layout()
    plt.show()

def print_coordinate_analysis(df: pd.DataFrame) -> None:
    """
    Print detailed coordinate analysis
    """
    print("\\n" + "="*100)
    print("LEON DRAISAITL SHOT COORDINATES ANALYSIS - 2024-25 SEASON")
    print("="*100)
    
    print(f"\\n📊 COORDINATE SUMMARY:")
    print(f"   X Coordinate Range: {df['coordinates_x'].min():.1f} to {df['coordinates_x'].max():.1f} feet")
    print(f"   Y Coordinate Range: {df['coordinates_y'].min():.1f} to {df['coordinates_y'].max():.1f} feet")
    print(f"   Average X: {df['coordinates_x'].mean():.1f} feet")
    print(f"   Average Y: {df['coordinates_y'].mean():.1f} feet")
    
    # Goals coordinate analysis
    goals_df = df[df['is_goal'] == 1]
    print(f"\\n🎯 GOALS COORDINATE ANALYSIS:")
    print(f"   Goals X Range: {goals_df['coordinates_x'].min():.1f} to {goals_df['coordinates_x'].max():.1f} feet")
    print(f"   Goals Y Range: {goals_df['coordinates_y'].min():.1f} to {goals_df['coordinates_y'].max():.1f} feet")
    print(f"   Average Goals X: {goals_df['coordinates_x'].mean():.1f} feet")
    print(f"   Average Goals Y: {goals_df['coordinates_y'].mean():.1f} feet")
    
    # Show first 10 goals with exact coordinates
    print(f"\\n🏒 FIRST 10 GOALS WITH EXACT COORDINATES:")
    goals_sample = goals_df.head(10)
    for i, goal in goals_sample.iterrows():
        print(f"   Goal {i+1}: X={goal['coordinates_x']:.1f}, Y={goal['coordinates_y']:.1f}, Distance={goal['shot_distance']:.1f}ft, Type={goal['secondary_type']}")
    
    # Coordinate zones analysis
    print(f"\\n📍 COORDINATE ZONES ANALYSIS:")
    
    # X zones (distance from goal)
    close_x = df[df['coordinates_x'] >= -10]  # Very close to goal
    medium_x = df[(df['coordinates_x'] < -10) & (df['coordinates_x'] >= -25)]  # Medium distance
    far_x = df[df['coordinates_x'] < -25]  # Far from goal
    
    for zone, shots_df, zone_name in [("Close to Goal", close_x, "Very Close (X ≥ -10ft)"), ("Medium Distance", medium_x, "Medium (X -25 to -10ft)"), ("Far from Goal", far_x, "Far (X < -25ft)")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {zone_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Y zones (left/center/right)
    left_y = df[df['coordinates_y'] < -10]  # Left side
    center_y = df[(df['coordinates_y'] >= -10) & (df['coordinates_y'] <= 10)]  # Center
    right_y = df[df['coordinates_y'] > 10]  # Right side
    
    print(f"\\n🎯 SIDE ANALYSIS:")
    for zone, shots_df, zone_name in [("Left Side", left_y, "Left (Y < -10ft)"), ("Center", center_y, "Center (Y -10 to 10ft)"), ("Right Side", right_y, "Right (Y > 10ft)")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {zone_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Show some specific coordinate examples
    print(f"\\n📋 SAMPLE SHOT COORDINATES:")
    sample_shots = df.head(20)
    for i, shot in sample_shots.iterrows():
        shot_type = "GOAL" if shot['is_goal'] else "SHOT" if shot['is_shot_on_goal'] else "MISSED" if shot['is_missed_shot'] else "BLOCKED"
        print(f"   {shot_type}: X={shot['coordinates_x']:.1f}, Y={shot['coordinates_y']:.1f}, Distance={shot['shot_distance']:.1f}ft, Type={shot['secondary_type']}")

def main():
    """
    Main function to run Leon Draisaitl shot coordinates analysis
    """
    print("LEON DRAISAITL SHOT COORDINATES ANALYSIS - 2024-25 SEASON")
    print("Showing actual shot coordinates and detailed ice map")
    print("="*80)
    
    # Get shot data with coordinates
    print("\\nFetching Leon Draisaitl shot coordinate data...")
    try:
        df = get_draisaitl_shot_coordinates()
        print(f"✅ Found {len(df)} shot attempts with coordinates for Leon Draisaitl")
    except Exception as e:
        print(f"❌ Error fetching shot data: {e}")
        return
    
    if df.empty:
        print("❌ No shot coordinate data found for Leon Draisaitl")
        return
    
    # Create detailed shot map
    print("\\nCreating detailed shot coordinate visualizations...")
    create_detailed_shot_map(df)
    
    # Print coordinate analysis
    print_coordinate_analysis(df)
    
    print("\\n" + "="*80)
    print("LEON DRAISAITL COORDINATE ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows the exact coordinates (X, Y) of every shot")
    print("Leon Draisaitl took during the 2024-25 season.")
    print("\\nCoordinate System:")
    print("- X: Distance from goal line (negative = closer to opponent's goal)")
    print("- Y: Distance from center ice (negative = left side, positive = right side)")
    print("- (0, 0) = Center of the goal line")

if __name__ == "__main__":
    main()
