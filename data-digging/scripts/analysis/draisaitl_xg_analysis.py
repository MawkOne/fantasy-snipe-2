#!/usr/bin/env python3
"""
Leon Draisaitl Expected Goals (xG) Analysis - 2024-25 Season
Calculate xG based on shot location and compare to actual goals
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional
import math

def get_draisaitl_shot_data() -> pd.DataFrame:
    """
    Get Leon Draisaitl's shot data for 2024-25 season with coordinates
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
            g.home_score,
            g.away_score,
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
    )
    
    SELECT 
        *,
        -- Calculate basic xG using distance (logistic function)
        1.0 / (1.0 + EXP((shot_distance - 25.0) / 5.0)) as xg_basic,
        
        -- Calculate enhanced xG using distance and angle (realistic NHL model)
        CASE 
            WHEN shot_distance <= 10 THEN 0.25  -- Very close shots (25% chance)
            WHEN shot_distance <= 20 THEN 0.15  -- Close shots (15% chance)
            WHEN shot_distance <= 30 THEN 0.10  -- Medium shots (10% chance)
            WHEN shot_distance <= 40 THEN 0.07  -- Far shots (7% chance)
            WHEN shot_distance <= 50 THEN 0.05  -- Very far shots (5% chance)
            ELSE 0.03  -- Extremely far shots (3% chance)
        END * 
        CASE 
            WHEN shot_angle <= 15 THEN 1.0      -- Center ice shots
            WHEN shot_angle <= 30 THEN 0.9      -- Slightly off-center
            WHEN shot_angle <= 45 THEN 0.8      -- Off-center
            WHEN shot_angle <= 60 THEN 0.6      -- Wide angle
            ELSE 0.4                            -- Very wide angle
        END as xg_enhanced,
        
        -- Shot type adjustment (calibrated for NHL)
        CASE 
            WHEN secondary_type = 'wrist' THEN 1.0
            WHEN secondary_type = 'snap' THEN 1.1
            WHEN secondary_type = 'slap' THEN 0.8
            WHEN secondary_type = 'backhand' THEN 0.9
            WHEN secondary_type = 'tip-in' THEN 1.3
            WHEN secondary_type = 'deflected' THEN 1.2
            WHEN secondary_type = 'wrap-around' THEN 0.6
            ELSE 1.0
        END as shot_type_multiplier
        
    FROM draisaitl_shots
    ORDER BY game_date, period, period_time
    """
    
    return client.query(query).to_dataframe()

def calculate_xg_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate comprehensive xG metrics for Draisaitl
    """
    # Basic xG calculations
    total_shots = len(df[df['is_shot_on_goal'] == 1])
    total_goals = df['is_goal'].sum()
    total_missed = df['is_missed_shot'].sum()
    total_blocked = df['is_blocked_shot'].sum()
    total_attempts = len(df)
    
    # xG calculations
    xg_basic_total = df['xg_basic'].sum()
    xg_enhanced_total = df['xg_enhanced'].sum()
    
    # Apply shot type multiplier to enhanced xG
    df['xg_final'] = df['xg_enhanced'] * df['shot_type_multiplier']
    xg_final_total = df['xg_final'].sum()
    
    # Shooting percentages
    shooting_pct = (total_goals / total_shots * 100) if total_shots > 0 else 0
    xg_shooting_pct = (total_goals / xg_final_total * 100) if xg_final_total > 0 else 0
    
    # Performance vs expected
    goals_vs_xg = total_goals - xg_final_total
    
    return {
        'total_attempts': total_attempts,
        'total_shots': total_shots,
        'total_goals': total_goals,
        'total_missed': total_missed,
        'total_blocked': total_blocked,
        'xg_basic_total': xg_basic_total,
        'xg_enhanced_total': xg_enhanced_total,
        'xg_final_total': xg_final_total,
        'shooting_pct': shooting_pct,
        'xg_shooting_pct': xg_shooting_pct,
        'goals_vs_xg': goals_vs_xg,
        'df': df
    }

def create_xg_visualizations(metrics: Dict, df: pd.DataFrame) -> None:
    """
    Create comprehensive xG visualizations for Draisaitl
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Chart 1: Goals vs xG Comparison
    categories = ['Actual Goals', 'xG (Basic)', 'xG (Enhanced)', 'xG (Final)']
    values = [metrics['total_goals'], metrics['xg_basic_total'], 
              metrics['xg_enhanced_total'], metrics['xg_final_total']]
    colors = ['red', 'orange', 'yellow', 'green']
    
    bars1 = ax1.bar(categories, values, color=colors, alpha=0.7)
    ax1.set_title('Leon Draisaitl: Goals vs Expected Goals (xG)\\n2024-25 Season', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Goals / Expected Goals')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars1, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{value:.1f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Chart 2: Shot Distribution by Distance
    shot_distances = df[df['is_shot_on_goal'] == 1]['shot_distance']
    goal_distances = df[df['is_goal'] == 1]['shot_distance']
    
    ax2.hist(shot_distances, bins=20, alpha=0.6, color='blue', label='All Shots', density=True)
    ax2.hist(goal_distances, bins=20, alpha=0.8, color='red', label='Goals', density=True)
    ax2.set_xlabel('Shot Distance (feet)')
    ax2.set_ylabel('Density')
    ax2.set_title('Shot Distribution by Distance\\nBlue=All Shots, Red=Goals')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Chart 3: Shot Map (All Shot Types)
    shots_on_goal = df[df['is_shot_on_goal'] == 1]
    missed_shots = df[df['is_missed_shot'] == 1]
    blocked_shots = df[df['is_blocked_shot'] == 1]
    goals = df[df['is_goal'] == 1]
    
    # Plot missed shots in yellow
    ax3.scatter(missed_shots['coordinates_x'], missed_shots['coordinates_y'], 
               alpha=0.4, color='yellow', s=15, label=f'Missed Shots ({len(missed_shots)})')
    
    # Plot blocked shots in orange
    ax3.scatter(blocked_shots['coordinates_x'], blocked_shots['coordinates_y'], 
               alpha=0.4, color='orange', s=15, label=f'Blocked Shots ({len(blocked_shots)})')
    
    # Plot shots on goal (non-goals) in light blue
    shots_on_goal_non_goals = shots_on_goal[shots_on_goal['is_goal'] == 0]
    ax3.scatter(shots_on_goal_non_goals['coordinates_x'], shots_on_goal_non_goals['coordinates_y'], 
               alpha=0.5, color='lightblue', s=20, label=f'Shots on Goal (No Goal) ({len(shots_on_goal_non_goals)})')
    
    # Plot goals in red
    ax3.scatter(goals['coordinates_x'], goals['coordinates_y'], 
               alpha=0.9, color='red', s=60, label=f'Goals ({len(goals)})')
    
    ax3.set_xlabel('X Coordinate (feet)')
    ax3.set_ylabel('Y Coordinate (feet)')
    ax3.set_title('Leon Draisaitl Complete Shot Map\\n2024-25 Season - All Shot Types')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(-50, 50)
    ax3.set_ylim(-25, 25)
    
    # Chart 4: xG by Game (rolling average)
    df['game_number'] = df.groupby('game_id').ngroup() + 1
    game_xg = df.groupby('game_number')['xg_final'].sum().reset_index()
    game_goals = df.groupby('game_number')['is_goal'].sum().reset_index()
    
    # Rolling averages
    game_xg['xg_rolling'] = game_xg['xg_final'].rolling(window=5, min_periods=1).mean()
    game_goals['goals_rolling'] = game_goals['is_goal'].rolling(window=5, min_periods=1).mean()
    
    ax4.plot(game_xg['game_number'], game_xg['xg_rolling'], 
             color='green', linewidth=2, label='xG (5-game avg)')
    ax4.plot(game_goals['game_number'], game_goals['goals_rolling'], 
             color='red', linewidth=2, label='Goals (5-game avg)')
    
    ax4.set_xlabel('Game Number')
    ax4.set_ylabel('Expected Goals / Goals')
    ax4.set_title('Leon Draisaitl: xG vs Goals Trend\\n5-Game Rolling Average')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def print_detailed_analysis(metrics: Dict, df: pd.DataFrame) -> None:
    """
    Print detailed xG analysis for Draisaitl
    """
    print("\\n" + "="*100)
    print("LEON DRAISAITL EXPECTED GOALS (xG) ANALYSIS - 2024-25 SEASON")
    print("="*100)
    
    print(f"\\n📊 SHOT SUMMARY:")
    print(f"   Total Shot Attempts: {metrics['total_attempts']}")
    print(f"   Shots on Goal: {metrics['total_shots']}")
    print(f"   Goals: {metrics['total_goals']}")
    print(f"   Missed Shots: {metrics['total_missed']}")
    print(f"   Blocked Shots: {metrics['total_blocked']}")
    
    print(f"\\n🎯 EXPECTED GOALS (xG) BREAKDOWN:")
    print(f"   xG (Basic - Distance Only): {metrics['xg_basic_total']:.2f}")
    print(f"   xG (Enhanced - Distance + Angle): {metrics['xg_enhanced_total']:.2f}")
    print(f"   xG (Final - Distance + Angle + Shot Type): {metrics['xg_final_total']:.2f}")
    
    print(f"\\n📈 PERFORMANCE ANALYSIS:")
    print(f"   Actual Shooting %: {metrics['shooting_pct']:.1f}%")
    print(f"   xG Shooting %: {metrics['xg_shooting_pct']:.1f}%")
    print(f"   Goals vs xG: {metrics['goals_vs_xg']:+.2f}")
    
    if metrics['goals_vs_xg'] > 0:
        print(f"   🏆 Draisaitl is OUTPERFORMING his xG by {metrics['goals_vs_xg']:.2f} goals!")
        print(f"   This suggests excellent finishing ability or favorable shooting conditions.")
    elif metrics['goals_vs_xg'] < 0:
        print(f"   ⚠️ Draisaitl is UNDERPERFORMING his xG by {abs(metrics['goals_vs_xg']):.2f} goals.")
        print(f"   This could indicate poor luck or suboptimal shot selection.")
    else:
        print(f"   ✅ Draisaitl is performing exactly as expected based on xG.")
    
    # Shot type analysis
    print(f"\\n🏒 SHOT TYPE ANALYSIS:")
    shot_types = df[df['is_shot_on_goal'] == 1]['secondary_type'].value_counts()
    for shot_type, count in shot_types.head(5).items():
        goals_of_type = df[(df['is_shot_on_goal'] == 1) & (df['secondary_type'] == shot_type)]['is_goal'].sum()
        shooting_pct_type = (goals_of_type / count * 100) if count > 0 else 0
        print(f"   {shot_type}: {count} shots, {goals_of_type} goals ({shooting_pct_type:.1f}%)")
    
    # Distance analysis for all shot types
    print(f"\\n📏 SHOT DISTANCE ANALYSIS (All Shot Types):")
    close_shots = df[df['shot_distance'] <= 20]
    medium_shots = df[(df['shot_distance'] > 20) & (df['shot_distance'] <= 35)]
    far_shots = df[df['shot_distance'] > 35]
    
    for category, shots_df in [("Close (≤20ft)", close_shots), ("Medium (20-35ft)", medium_shots), ("Far (>35ft)", far_shots)]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            missed = shots_df['is_missed_shot'].sum()
            blocked = shots_df['is_blocked_shot'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {category}: {len(shots_df)} total attempts")
            print(f"     - Goals: {goals} ({shooting_pct:.1f}% of shots on goal)")
            print(f"     - Shots on Goal: {shots_on_goal}")
            print(f"     - Missed: {missed}")
            print(f"     - Blocked: {blocked}")
    
    # Shot location analysis
    print(f"\\n🎯 SHOT LOCATION ANALYSIS:")
    # Left side shots (negative Y)
    left_shots = df[df['coordinates_y'] < -5]
    center_shots = df[(df['coordinates_y'] >= -5) & (df['coordinates_y'] <= 5)]
    right_shots = df[df['coordinates_y'] > 5]
    
    for side, shots_df, side_name in [("Left Side", left_shots, "Left"), ("Center", center_shots, "Center"), ("Right Side", right_shots, "Right")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {side_name} Side: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # High-danger area analysis (close to net)
    high_danger = df[df['shot_distance'] <= 15]
    medium_danger = df[(df['shot_distance'] > 15) & (df['shot_distance'] <= 30)]
    low_danger = df[df['shot_distance'] > 30]
    
    print(f"\\n🔥 DANGER ZONE ANALYSIS:")
    for zone, shots_df, zone_name in [("High Danger", high_danger, "High Danger (≤15ft)"), ("Medium Danger", medium_danger, "Medium Danger (15-30ft)"), ("Low Danger", low_danger, "Low Danger (>30ft)")]:
        if len(shots_df) > 0:
            goals = shots_df['is_goal'].sum()
            shots_on_goal = shots_df['is_shot_on_goal'].sum()
            shooting_pct = (goals / shots_on_goal * 100) if shots_on_goal > 0 else 0
            print(f"   {zone_name}: {len(shots_df)} attempts, {goals} goals ({shooting_pct:.1f}% of shots on goal)")
    
    # Game-by-game breakdown
    print(f"\\n🎮 GAME-BY-GAME BREAKDOWN (Last 10 Games):")
    game_stats = df.groupby('game_id').agg({
        'is_goal': 'sum',
        'xg_final': 'sum',
        'is_shot_on_goal': 'sum'
    }).reset_index()
    game_stats['goals_vs_xg'] = game_stats['is_goal'] - game_stats['xg_final']
    game_stats = game_stats.tail(10)
    
    for _, game in game_stats.iterrows():
        print(f"   Game {game['game_id']}: {game['is_goal']:.0f}G, {game['xg_final']:.2f}xG, {game['goals_vs_xg']:+.2f} diff")

def main():
    """
    Main function to run Leon Draisaitl xG analysis
    """
    print("LEON DRAISAITL EXPECTED GOALS (xG) ANALYSIS - 2024-25 SEASON")
    print("Calculating xG based on shot location, angle, and type")
    print("="*80)
    
    # Get shot data
    print("\\nFetching Leon Draisaitl shot data...")
    try:
        df = get_draisaitl_shot_data()
        print(f"✅ Found {len(df)} shot attempts for Leon Draisaitl")
    except Exception as e:
        print(f"❌ Error fetching shot data: {e}")
        return
    
    if df.empty:
        print("❌ No shot data found for Leon Draisaitl")
        return
    
    # Calculate xG metrics
    print("\\nCalculating expected goals metrics...")
    metrics = calculate_xg_metrics(df)
    
    # Create visualizations
    print("\\nCreating xG visualizations...")
    create_xg_visualizations(metrics, df)
    
    # Print detailed analysis
    print_detailed_analysis(metrics, df)
    
    print("\\n" + "="*80)
    print("LEON DRAISAITL xG ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows how Leon Draisaitl's actual goal scoring")
    print("compares to what we would expect based on shot quality and location.")
    print("\\nKey Insights:")
    print("- xG helps identify if a player is over/under-performing")
    print("- Shot location and angle significantly impact goal probability")
    print("- This can help predict future goal scoring regression or improvement")

if __name__ == "__main__":
    main()
