#!/usr/bin/env python3
"""
Leon Draisaitl Shot Coordinates Analysis - CORRECTED NHL Coordinate System
Using proper NHL coordinate system: X=0-100 (center line to end), Y=-43 to +43 (left to right)
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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
        -- Normalize coordinates to always shoot toward goal at X=89
        -- This accounts for teams switching sides between periods
        CASE 
            WHEN ge.period IN (1, 3) THEN ge.coordinates_x  -- Odd periods: use as-is
            ELSE 100 - ge.coordinates_x  -- Even periods: flip X coordinate
        END as normalized_x,
        CASE 
            WHEN ge.period IN (1, 3) THEN ge.coordinates_y  -- Odd periods: use as-is
            ELSE -ge.coordinates_y  -- Even periods: flip Y coordinate
        END as normalized_y,
        -- Calculate distance from goal line (always shooting toward X=89)
        CASE 
            WHEN ge.period IN (1, 3) THEN 89 - ge.coordinates_x  -- Odd periods: distance from X=89
            ELSE ge.coordinates_x - 11  -- Even periods: distance from X=11 (flipped)
        END as shot_distance_from_goal,
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

def create_corrected_shot_map(df: pd.DataFrame) -> None:
    """
    Create shot map using correct NHL coordinate system
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Chart 1: All shots with correct coordinates
    shots_on_goal = df[df['is_shot_on_goal'] == 1]
    missed_shots = df[df['is_missed_shot'] == 1]
    blocked_shots = df[df['is_blocked_shot'] == 1]
    goals = df[df['is_goal'] == 1]
    
    # Plot missed shots in yellow
    ax1.scatter(missed_shots['normalized_x'], missed_shots['normalized_y'], 
               alpha=0.4, color='yellow', s=15, label=f'Missed Shots ({len(missed_shots)})')
    
    # Plot blocked shots in orange
    ax1.scatter(blocked_shots['normalized_x'], blocked_shots['normalized_y'], 
               alpha=0.4, color='orange', s=15, label=f'Blocked Shots ({len(blocked_shots)})')
    
    # Plot shots on goal (non-goals) in light blue
    shots_on_goal_non_goals = shots_on_goal[shots_on_goal['is_goal'] == 0]
    ax1.scatter(shots_on_goal_non_goals['normalized_x'], shots_on_goal_non_goals['normalized_y'], 
               alpha=0.5, color='lightblue', s=20, label=f'Shots on Goal (No Goal) ({len(shots_on_goal_non_goals)})')
    
    # Plot goals in red
    ax1.scatter(goals['normalized_x'], goals['normalized_y'], 
               alpha=0.9, color='red', s=60, label=f'Goals ({len(goals)})')
    
    # Add rink markings
    # Goal lines
    ax1.axvline(x=11, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    ax1.axvline(x=89, color='red', linewidth=3, alpha=0.8)
    # Center line
    ax1.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--', label='Center Line')
    # Sideboards
    ax1.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax1.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    # Center ice
    ax1.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    ax1.set_xlabel('X Coordinate (0=Center Line, 11/89=Goal Lines)')
    ax1.set_ylabel('Y Coordinate (-43=Left Board, +43=Right Board)')
    ax1.set_title('Leon Draisaitl Shot Map - CORRECTED NHL Coordinates\\n2024-25 Season')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(-43, 43)
    
    # Chart 2: Goals only with distance from goal
    ax2.scatter(goals['normalized_x'], goals['normalized_y'], 
               c=goals['shot_distance_from_goal'], cmap='Reds', s=80, alpha=0.8, label=f'Goals ({len(goals)})')
    
    # Add colorbar for distance
    cbar = plt.colorbar(ax2.collections[0], ax=ax2)
    cbar.set_label('Distance from Goal Line (feet)')
    
    # Add rink markings
    ax2.axvline(x=11, color='red', linewidth=3, alpha=0.8)
    ax2.axvline(x=89, color='red', linewidth=3, alpha=0.8)
    ax2.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--')
    ax2.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax2.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    ax2.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    ax2.set_xlabel('X Coordinate (0=Center Line, 11/89=Goal Lines)')
    ax2.set_ylabel('Y Coordinate (-43=Left Board, +43=Right Board)')
    ax2.set_title('Leon Draisaitl Goals - Distance from Goal Line\\n2024-25 Season')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-43, 43)
    
    plt.tight_layout()
    plt.show()

def print_corrected_analysis(df: pd.DataFrame) -> None:
    """
    Print analysis with corrected coordinate interpretation
    """
    print("\\n" + "="*100)
    print("LEON DRAISAITL SHOT COORDINATES - CORRECTED NHL SYSTEM")
    print("="*100)
    
    print(f"\\n📊 NORMALIZED COORDINATE SUMMARY:")
    print(f"   Raw X Range: {df['coordinates_x'].min():.1f} to {df['coordinates_x'].max():.1f}")
    print(f"   Raw Y Range: {df['coordinates_y'].min():.1f} to {df['coordinates_y'].max():.1f}")
    print(f"   Normalized X Range: {df['normalized_x'].min():.1f} to {df['normalized_x'].max():.1f}")
    print(f"   Normalized Y Range: {df['normalized_y'].min():.1f} to {df['normalized_y'].max():.1f}")
    print(f"   Average Normalized X: {df['normalized_x'].mean():.1f}")
    print(f"   Average Normalized Y: {df['normalized_y'].mean():.1f}")
    
    # Goals analysis
    goals_df = df[df['is_goal'] == 1]
    print(f"\\n🎯 GOALS ANALYSIS (NORMALIZED):")
    print(f"   Goals Normalized X Range: {goals_df['normalized_x'].min():.1f} to {goals_df['normalized_x'].max():.1f}")
    print(f"   Goals Normalized Y Range: {goals_df['normalized_y'].min():.1f} to {goals_df['normalized_y'].max():.1f}")
    print(f"   Average Goals Normalized X: {goals_df['normalized_x'].mean():.1f}")
    print(f"   Average Goals Normalized Y: {goals_df['normalized_y'].mean():.1f}")
    print(f"   Average Distance from Goal: {goals_df['shot_distance_from_goal'].mean():.1f} feet")
    
    # Distance analysis
    print(f"\\n📏 DISTANCE FROM GOAL ANALYSIS:")
    close_shots = df[df['shot_distance_from_goal'] <= 20]
    medium_shots = df[(df['shot_distance_from_goal'] > 20) & (df['shot_distance_from_goal'] <= 40)]
    far_shots = df[df['shot_distance_from_goal'] > 40]
    
    for category, shots_df, zone_name in [("Close (≤20ft)", close_shots, "Close Range"), ("Medium (20-40ft)", medium_shots, "Medium Range"), ("Far (>40ft)", far_shots, "Long Range")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {zone_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Side analysis
    print(f"\\n🎯 SIDE ANALYSIS (NORMALIZED):")
    left_side = df[df['normalized_y'] < -10]
    center_ice = df[(df['normalized_y'] >= -10) & (df['normalized_y'] <= 10)]
    right_side = df[df['normalized_y'] > 10]
    
    for zone, shots_df, zone_name in [("Left Side", left_side, "Left Side (Y < -10)"), ("Center Ice", center_ice, "Center Ice (Y -10 to 10)"), ("Right Side", right_side, "Right Side (Y > 10)")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {zone_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Show sample goals with normalized interpretation
    print(f"\\n🏒 SAMPLE GOALS WITH NORMALIZED COORDINATES:")
    goals_sample = goals_df.head(10)
    for i, goal in goals_sample.iterrows():
        distance = goal['shot_distance_from_goal']
        side = "Left" if goal['normalized_y'] < -10 else "Right" if goal['normalized_y'] > 10 else "Center"
        print(f"   Goal {i+1}: Raw X={goal['coordinates_x']:.1f}, Raw Y={goal['coordinates_y']:.1f}")
        print(f"         Normalized X={goal['normalized_x']:.1f}, Normalized Y={goal['normalized_y']:.1f}")
        print(f"         Distance={distance:.1f}ft, Side={side}, Type={goal['secondary_type']}")
        print(f"         Period={goal['period']}")
        print()
    
    print(f"\\n📋 NHL COORDINATE SYSTEM EXPLANATION:")
    print(f"   Raw coordinates are relative to the rink and change when teams switch sides")
    print(f"   Normalized coordinates account for period changes (teams switch sides)")
    print(f"   X-axis: 0 = Center Line, 11 = Goal Line (close), 89 = Goal Line (far), 100 = End Boards")
    print(f"   Y-axis: -43 = Left Sideboard, 0 = Center Ice, +43 = Right Sideboard")
    print(f"   Center of rink: (50, 0)")
    print(f"   Goal lines: X = 11 and X = 89")
    print(f"   All shots normalized to shoot toward goal at X = 89")

def main():
    """
    Main function to run corrected coordinate analysis
    """
    print("LEON DRAISAITL SHOT COORDINATES - CORRECTED NHL SYSTEM")
    print("Using proper NHL coordinate system: X=0-100, Y=-43 to +43")
    print("="*80)
    
    # Get shot data
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
    
    # Create corrected shot map
    print("\\nCreating corrected shot coordinate visualizations...")
    create_corrected_shot_map(df)
    
    # Print corrected analysis
    print_corrected_analysis(df)
    
    print("\\n" + "="*80)
    print("CORRECTED COORDINATE ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
