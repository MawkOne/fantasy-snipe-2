#!/usr/bin/env python3
"""
Leon Draisaitl Shot Analysis - Normalized to Always Show One End of Ice
All shots normalized to shoot toward the same goal regardless of period or home/away
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def get_draisaitl_normalized_shots() -> pd.DataFrame:
    """
    Get Leon Draisaitl's shot data normalized to always show one end of ice
    """
    client = bigquery.Client()
    
    query = """
    WITH draisaitl_shots AS (
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
            g.home_team_id,
            g.away_team_id,
            -- Determine if Oilers are home or away
            CASE WHEN g.home_team_id = 22 THEN 'HOME' ELSE 'AWAY' END as oilers_status,
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
    )
    
    SELECT 
        *,
        -- Normalize coordinates to always shoot toward positive X end (X=89 goal)
        -- Based on the pattern analysis:
        -- HOME: Periods 1,3 shoot toward positive X, Period 2 toward negative X
        -- AWAY: Periods 1,3 shoot toward positive X, Period 2 toward negative X
        CASE 
            -- For periods 1 and 3, use coordinates as-is (shooting toward positive X)
            WHEN period IN (1, 3) THEN coordinates_x
            -- For period 2, flip X coordinate (shooting toward negative X, so flip to positive)
            ELSE -coordinates_x
        END as normalized_x,
        CASE 
            -- For periods 1 and 3, use Y coordinates as-is
            WHEN period IN (1, 3) THEN coordinates_y
            -- For period 2, flip Y coordinate to maintain relative positioning
            ELSE -coordinates_y
        END as normalized_y,
        -- Calculate distance from goal line (always shooting toward X=89)
        CASE 
            WHEN period IN (1, 3) THEN 89 - coordinates_x
            ELSE 89 - (-coordinates_x)  -- Distance from flipped coordinate
        END as shot_distance_from_goal
    FROM draisaitl_shots
    ORDER BY game_date, period, period_time
    """
    
    return client.query(query).to_dataframe()

def create_normalized_shot_map(df: pd.DataFrame) -> None:
    """
    Create shot map with all shots normalized to one end of ice
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Chart 1: All shots normalized to one end
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
    ax1.axvline(x=11, color='red', linewidth=3, alpha=0.8, label='Goal Line')
    ax1.axvline(x=89, color='red', linewidth=3, alpha=0.8)
    ax1.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--', label='Center Line')
    ax1.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax1.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    ax1.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    ax1.set_xlabel('X Coordinate (Normalized - Always Shooting Toward X=89)')
    ax1.set_ylabel('Y Coordinate (Normalized)')
    ax1.set_title('Leon Draisaitl Shot Map - Normalized to One End\\n2024-25 Season')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(-43, 43)
    
    # Chart 2: Goals by distance from goal
    ax2.scatter(goals['normalized_x'], goals['normalized_y'], 
               c=goals['shot_distance_from_goal'], cmap='Reds', s=80, alpha=0.8)
    
    cbar = plt.colorbar(ax2.collections[0], ax=ax2)
    cbar.set_label('Distance from Goal Line (feet)')
    
    ax2.axvline(x=11, color='red', linewidth=3, alpha=0.8)
    ax2.axvline(x=89, color='red', linewidth=3, alpha=0.8)
    ax2.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--')
    ax2.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax2.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    ax2.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    ax2.set_xlabel('X Coordinate (Normalized)')
    ax2.set_ylabel('Y Coordinate (Normalized)')
    ax2.set_title('Leon Draisaitl Goals - Distance from Goal Line\\n2024-25 Season')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-43, 43)
    
    # Chart 3: Goals by period (showing normalization effect)
    periods = [1, 2, 3, 4]
    colors = ['blue', 'red', 'green', 'orange']
    
    for period, color in zip(periods, colors):
        period_goals = goals[goals['period'] == period]
        if len(period_goals) > 0:
            ax3.scatter(period_goals['normalized_x'], period_goals['normalized_y'], 
                       alpha=0.7, color=color, s=60, label=f'Period {period} ({len(period_goals)} goals)')
    
    ax3.axvline(x=11, color='red', linewidth=3, alpha=0.8)
    ax3.axvline(x=89, color='red', linewidth=3, alpha=0.8)
    ax3.axvline(x=50, color='blue', linewidth=2, alpha=0.6, linestyle='--')
    ax3.axhline(y=-43, color='black', linewidth=2, alpha=0.5)
    ax3.axhline(y=43, color='black', linewidth=2, alpha=0.5)
    ax3.axhline(y=0, color='blue', linewidth=1, alpha=0.4, linestyle='--')
    
    ax3.set_xlabel('X Coordinate (Normalized)')
    ax3.set_ylabel('Y Coordinate (Normalized)')
    ax3.set_title('Leon Draisaitl Goals by Period\\n2024-25 Season (Normalized)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 100)
    ax3.set_ylim(-43, 43)
    
    # Chart 4: Distance distribution
    ax4.hist(goals['shot_distance_from_goal'], bins=20, alpha=0.7, color='red', 
             label=f'Goals ({len(goals)})', density=True)
    ax4.hist(shots_on_goal['shot_distance_from_goal'], bins=20, alpha=0.5, color='blue', 
             label=f'All Shots on Goal ({len(shots_on_goal)})', density=True)
    
    ax4.set_xlabel('Distance from Goal Line (feet)')
    ax4.set_ylabel('Density')
    ax4.set_title('Shot Distance Distribution\\n2024-25 Season (Normalized)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def print_normalized_analysis(df: pd.DataFrame) -> None:
    """
    Print analysis with normalized coordinates
    """
    print("\\n" + "="*100)
    print("LEON DRAISAITL SHOT ANALYSIS - NORMALIZED TO ONE END OF ICE")
    print("="*100)
    
    print(f"\\n📊 NORMALIZED COORDINATE SUMMARY:")
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
    
    # Period analysis
    print(f"\\n⏰ PERIOD ANALYSIS:")
    for period in [1, 2, 3, 4]:
        period_shots = df[df['period'] == period]
        if len(period_shots) > 0:
            goals = period_shots['is_goal'].sum()
            shots_on_goal = period_shots['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   Period {period}: {len(period_shots)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Home vs Away analysis
    print(f"\\n🏠 HOME vs AWAY ANALYSIS:")
    home_shots = df[df['oilers_status'] == 'HOME']
    away_shots = df[df['oilers_status'] == 'AWAY']
    
    for status, shots_df, status_name in [("HOME", home_shots, "Home Games"), ("AWAY", away_shots, "Away Games")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {status_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    print(f"\\n📋 NORMALIZATION EXPLANATION:")
    print(f"   All shots normalized to always shoot toward goal at X = 89")
    print(f"   Periods 1 & 3: Coordinates used as-is")
    print(f"   Period 2: X and Y coordinates flipped to maintain consistent view")
    print(f"   This ensures all shots are displayed from the same perspective")

def main():
    """
    Main function to run normalized shot analysis
    """
    print("LEON DRAISAITL SHOT ANALYSIS - NORMALIZED TO ONE END OF ICE")
    print("All shots normalized to always show the same goal perspective")
    print("="*80)
    
    # Get normalized shot data
    print("\\nFetching Leon Draisaitl normalized shot data...")
    try:
        df = get_draisaitl_normalized_shots()
        print(f"✅ Found {len(df)} shot attempts with normalized coordinates for Leon Draisaitl")
    except Exception as e:
        print(f"❌ Error fetching shot data: {e}")
        return
    
    if df.empty:
        print("❌ No shot coordinate data found for Leon Draisaitl")
        return
    
    # Create normalized shot map
    print("\\nCreating normalized shot coordinate visualizations...")
    create_normalized_shot_map(df)
    
    # Print normalized analysis
    print_normalized_analysis(df)
    
    print("\\n" + "="*80)
    print("NORMALIZED SHOT ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
