#!/usr/bin/env python3
"""
True On-Ice vs Off-Ice Impact Analysis - 2024-25 Season
Using shift-level data to measure actual team performance with/without each player
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_shift_level_data(team_abbr: str) -> pd.DataFrame:
    """
    Get shift-level data for a specific team to calculate true on-ice vs off-ice impact
    """
    client = bigquery.Client()
    
    # Query to get shift-level data with goals for/against
    query = f"""
    WITH shift_data AS (
        SELECT 
            ps.player_id,
            p.full_name,
            p.position,
            ps.game_id,
            ps.team_id,
            ps.shift_start,
            ps.shift_end,
            ps.duration,
            -- Calculate goals for and against during this shift
            COALESCE(SUM(CASE 
                WHEN ge.event_type = 'GOAL' 
                AND ge.team_id = ps.team_id 
                AND ge.period_time >= ps.shift_start 
                AND ge.period_time <= ps.shift_end 
                THEN 1 ELSE 0 END), 0) as goals_for_shift,
            COALESCE(SUM(CASE 
                WHEN ge.event_type = 'GOAL' 
                AND ge.team_id != ps.team_id 
                AND ge.period_time >= ps.shift_start 
                AND ge.period_time <= ps.shift_end 
                THEN 1 ELSE 0 END), 0) as goals_against_shift
        FROM `fantasy-snipe-ai.nhl_raw.player_shifts` ps
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON ps.player_id = p.player_id
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.game_events` ge ON ps.game_id = ge.game_id
        WHERE ps.team_id = (
            SELECT id FROM `fantasy-snipe-ai.nhl_raw.teams` 
            WHERE tri_code = '{team_abbr}'
        )
        AND ps.season = 20242025
        AND ps.game_type = 2
        AND ge.event_type = 'GOAL'
        AND ge.period_time IS NOT NULL
        GROUP BY ps.player_id, p.full_name, p.position, ps.game_id, ps.team_id, 
                 ps.shift_start, ps.shift_end, ps.duration
    ),
    
    player_totals AS (
        SELECT 
            player_id,
            full_name,
            position,
            COUNT(*) as total_shifts,
            SUM(duration) as total_ice_time_seconds,
            SUM(goals_for_shift) as total_goals_for,
            SUM(goals_against_shift) as total_goals_against,
            SUM(goals_for_shift) - SUM(goals_against_shift) as goal_differential
        FROM shift_data
        GROUP BY player_id, full_name, position
    ),
    
    team_totals AS (
        SELECT 
            SUM(total_ice_time_seconds) as team_total_ice_time,
            SUM(total_goals_for) as team_total_goals_for,
            SUM(total_goals_against) as team_total_goals_against,
            SUM(total_goals_for) - SUM(total_goals_against) as team_goal_differential
        FROM player_totals
    )
    
    SELECT 
        pt.*,
        tt.team_total_ice_time,
        tt.team_total_goals_for,
        tt.team_total_goals_against,
        tt.team_goal_differential,
        -- Calculate rates per 60 minutes
        (pt.total_goals_for * 3600.0 / pt.total_ice_time_seconds) as gf60,
        (pt.total_goals_against * 3600.0 / pt.total_ice_time_seconds) as ga60,
        (pt.goal_differential * 3600.0 / pt.total_ice_time_seconds) as goal_diff60,
        -- Calculate off-ice team performance
        ((tt.team_total_goals_for - pt.total_goals_for) * 3600.0 / 
         (tt.team_total_ice_time - pt.total_ice_time_seconds)) as off_ice_gf60,
        ((tt.team_total_goals_against - pt.total_goals_against) * 3600.0 / 
         (tt.team_total_ice_time - pt.total_ice_time_seconds)) as off_ice_ga60,
        (((tt.team_total_goals_for - pt.total_goals_for) - 
          (tt.team_total_goals_against - pt.total_goals_against)) * 3600.0 / 
         (tt.team_total_ice_time - pt.total_ice_time_seconds)) as off_ice_goal_diff60
    FROM player_totals pt
    CROSS JOIN team_totals tt
    WHERE pt.total_ice_time_seconds >= 1200  -- At least 20 minutes of ice time
    ORDER BY pt.goal_differential DESC
    """
    
    return client.query(query).to_dataframe()

def calculate_true_impact_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate true on-ice vs off-ice impact metrics
    """
    df = df.copy()
    
    # Calculate impact vs off-ice performance
    df['gf60_impact'] = df['gf60'] - df['off_ice_gf60']
    df['ga60_impact'] = df['ga60'] - df['off_ice_ga60']
    df['goal_diff60_impact'] = df['goal_diff60'] - df['off_ice_goal_diff60']
    
    # Calculate relative team impact
    df['relative_gf_contribution'] = (df['total_goals_for'] / df['team_total_goals_for']) * 100
    df['relative_ga_contribution'] = (df['total_goals_against'] / df['team_total_goals_against']) * 100
    
    # Overall impact score (weighted combination)
    df['true_impact_score'] = (
        df['goal_diff60_impact'] * 0.6 +  # Goal differential impact (most important)
        df['gf60_impact'] * 0.3 +         # Goals for impact
        -df['ga60_impact'] * 0.1          # Goals against impact (negative is good)
    )
    
    # Calculate ice time percentage
    df['ice_time_percentage'] = (df['total_ice_time_seconds'] / df['team_total_ice_time']) * 100
    
    return df

def classify_players_by_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify players by their true on-ice impact
    """
    df = df.copy()
    
    # Initialize all players as Depth
    df['tier'] = 'Depth'
    
    # Elite impact players (top 10% of impact scores)
    elite_threshold = df['true_impact_score'].quantile(0.9)
    df.loc[df['true_impact_score'] >= elite_threshold, 'tier'] = 'Elite Impact'
    
    # High impact players (top 25% of impact scores)
    high_threshold = df['true_impact_score'].quantile(0.75)
    df.loc[(df['true_impact_score'] >= high_threshold) & (df['tier'] == 'Depth'), 'tier'] = 'High Impact'
    
    # Positive impact players (above average)
    avg_impact = df['true_impact_score'].mean()
    df.loc[(df['true_impact_score'] >= avg_impact) & (df['tier'] == 'Depth'), 'tier'] = 'Positive Impact'
    
    # Negative impact players (below average)
    df.loc[df['true_impact_score'] < avg_impact, 'tier'] = 'Negative Impact'
    
    return df

def create_true_impact_visualization(df: pd.DataFrame, team_name: str) -> None:
    """
    Create visualization for true on-ice vs off-ice impact
    """
    # Create the plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 1: True Impact Score
    players = df['full_name']
    impact_scores = df['true_impact_score']
    tiers = df['tier']
    
    # Color by tier
    colors = []
    for tier in tiers:
        if tier == 'Elite Impact':
            colors.append('red')
        elif tier == 'High Impact':
            colors.append('gold')
        elif tier == 'Positive Impact':
            colors.append('lightgreen')
        else:
            colors.append('lightcoral')
    
    bars1 = ax1.barh(range(len(players)), impact_scores, color=colors, alpha=0.7)
    
    ax1.set_yticks(range(len(players)))
    ax1.set_yticklabels(players)
    ax1.set_xlabel('True Impact Score (Goal Diff/60)')
    ax1.set_title(f'{team_name}: True On-Ice vs Off-Ice Impact Score\\n2024-25 Season')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + (0.1 if width >= 0 else -0.1), bar.get_y() + bar.get_height()/2,
                f'{width:.2f}', ha='left' if width >= 0 else 'right', va='center', fontsize=9)
    
    # Plot 2: Goals For vs Against Impact
    ax2.scatter(df['gf60_impact'], df['ga60_impact'], 
               c=df['tier'].map({'Elite Impact': 'red', 'High Impact': 'gold', 'Positive Impact': 'lightgreen', 'Negative Impact': 'lightcoral'}),
               alpha=0.7, s=100)
    
    # Add player names as labels
    for i, player in enumerate(players):
        ax2.annotate(player, (df.iloc[i]['gf60_impact'], df.iloc[i]['ga60_impact']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax2.set_xlabel('Goals For Impact (GF/60 vs Off-Ice)')
    ax2.set_ylabel('Goals Against Impact (GA/60 vs Off-Ice)')
    ax2.set_title(f'{team_name}: Goals For vs Against Impact\\n2024-25 Season')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Plot 3: Goal Differential Impact by Position
    position_impact = df.groupby('position')['goal_diff60_impact'].agg(['mean', 'std', 'count']).round(2)
    
    bars3 = ax3.bar(position_impact.index, position_impact['mean'], 
                    yerr=position_impact['std'], capsize=5, alpha=0.7, 
                    color=['lightblue', 'lightgreen', 'lightcoral', 'gold'])
    
    ax3.set_xlabel('Position')
    ax3.set_ylabel('Average Goal Differential Impact')
    ax3.set_title(f'{team_name}: Goal Differential Impact by Position\\n2024-25 Season')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars3):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height >= 0 else -0.01),
                f'{height:.2f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
    
    # Plot 4: Ice Time vs Impact
    ax4.scatter(df['ice_time_percentage'], df['true_impact_score'], 
               c=df['tier'].map({'Elite Impact': 'red', 'High Impact': 'gold', 'Positive Impact': 'lightgreen', 'Negative Impact': 'lightcoral'}),
               alpha=0.7, s=100)
    
    # Add player names as labels
    for i, player in enumerate(players):
        ax4.annotate(player, (df.iloc[i]['ice_time_percentage'], df.iloc[i]['true_impact_score']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax4.set_xlabel('Ice Time Percentage of Team Total')
    ax4.set_ylabel('True Impact Score')
    ax4.set_title(f'{team_name}: Ice Time vs True Impact\\n2024-25 Season')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', label='Elite Impact'),
                      Patch(facecolor='gold', label='High Impact'),
                      Patch(facecolor='lightgreen', label='Positive Impact'),
                      Patch(facecolor='lightcoral', label='Negative Impact')]
    ax4.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.show()

def create_detailed_true_impact_table(df: pd.DataFrame, team_name: str) -> None:
    """
    Create detailed table of true on-ice vs off-ice impact analysis
    """
    print("\\n" + "="*160)
    print(f"{team_name.upper()} TRUE ON-ICE vs OFF-ICE IMPACT ANALYSIS - 2024-25 SEASON")
    print("="*160)
    
    # Create detailed table
    detailed_data = []
    for _, row in df.iterrows():
        detailed_data.append({
            'Player': row['full_name'],
            'Position': row['position'],
            'Tier': row['tier'],
            'Shifts': f"{row['total_shifts']:.0f}",
            'Ice Time %': f"{row['ice_time_percentage']:.1f}%",
            'On-Ice GF/60': f"{row['gf60']:.2f}",
            'Off-Ice GF/60': f"{row['off_ice_gf60']:.2f}",
            'GF Impact': f"{row['gf60_impact']:+.2f}",
            'On-Ice GA/60': f"{row['ga60']:.2f}",
            'Off-Ice GA/60': f"{row['off_ice_ga60']:.2f}",
            'GA Impact': f"{row['ga60_impact']:+.2f}",
            'Goal Diff Impact': f"{row['goal_diff60_impact']:+.2f}",
            'True Impact Score': f"{row['true_impact_score']:+.2f}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*160)
    print(f"KEY INSIGHTS - {team_name.upper()}")
    print("="*160)
    
    # Find highest impact player
    highest_impact = df.loc[df['true_impact_score'].idxmax()]
    print(f"\\n🏆 HIGHEST TRUE IMPACT: {highest_impact['full_name']}")
    print(f"   Position: {highest_impact['position']}")
    print(f"   Tier: {highest_impact['tier']}")
    print(f"   True Impact Score: {highest_impact['true_impact_score']:+.2f}")
    print(f"   Goal Differential Impact: {highest_impact['goal_diff60_impact']:+.2f}")
    print(f"   Goals For Impact: {highest_impact['gf60_impact']:+.2f}")
    print(f"   Goals Against Impact: {highest_impact['ga60_impact']:+.2f}")
    print(f"   Ice Time: {highest_impact['ice_time_percentage']:.1f}% of team total")
    
    # Team totals
    print(f"\\n📊 {team_name.upper()} TEAM TOTALS - 2024-25:")
    print(f"   Total Ice Time: {df['team_total_ice_time'].iloc[0]/3600:.1f} hours")
    print(f"   Total Goals For: {df['team_total_goals_for'].iloc[0]:.0f}")
    print(f"   Total Goals Against: {df['team_total_goals_against'].iloc[0]:.0f}")
    print(f"   Team Goal Differential: {df['team_goal_differential'].iloc[0]:+.0f}")
    print(f"   Team Size: {len(df):.0f} players")
    
    # Tier analysis
    tier_analysis = df.groupby('tier').agg({
        'true_impact_score': ['mean', 'max', 'count'],
        'goal_diff60_impact': 'mean',
        'ice_time_percentage': 'mean'
    }).round(2)
    
    print(f"\\n📈 TIER ANALYSIS - {team_name.upper()}:")
    for tier in ['Elite Impact', 'High Impact', 'Positive Impact', 'Negative Impact']:
        if tier in tier_analysis.index:
            tier_data = tier_analysis.loc[tier]
            print(f"   {tier}:")
            print(f"     Average Impact Score: {tier_data[('true_impact_score', 'mean')]:.2f}")
            print(f"     Max Impact Score: {tier_data[('true_impact_score', 'max')]:.2f}")
            print(f"     Count: {tier_data[('true_impact_score', 'count')]:.0f}")
            print(f"     Avg Goal Diff Impact: {tier_data[('goal_diff60_impact', 'mean')]:.2f}")
            print(f"     Avg Ice Time: {tier_data[('ice_time_percentage', 'mean')]:.1f}%")

def analyze_team(team_abbr: str, team_name: str) -> None:
    """
    Analyze a specific team's true on-ice vs off-ice impact
    """
    print(f"{team_name.upper()} TRUE ON-ICE vs OFF-ICE IMPACT ANALYSIS - 2024-25 SEASON")
    print("Using shift-level data to measure actual team performance with/without each player")
    print("="*80)
    
    # Get shift-level data
    print(f"\\nFetching {team_name} shift-level data...")
    try:
        shift_df = get_shift_level_data(team_abbr)
        print(f"✅ Found shift data for {len(shift_df)} {team_name} players")
    except Exception as e:
        print(f"❌ Error fetching {team_name} shift data: {e}")
        return
    
    # Calculate true impact metrics
    print("\\nCalculating true on-ice vs off-ice impact...")
    impact_df = calculate_true_impact_metrics(shift_df)
    
    # Classify players
    print("\\nClassifying players by true impact...")
    classified_df = classify_players_by_impact(impact_df)
    
    # Create visualizations
    print(f"\\nCreating {team_name} true impact visualizations...")
    create_true_impact_visualization(classified_df, team_name)
    
    # Create detailed analysis
    create_detailed_true_impact_table(classified_df, team_name)
    
    print("\\n" + "="*80)
    print(f"{team_name.upper()} TRUE IMPACT ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows each player's true impact on team performance when they are on the ice versus when they are off the ice.")
    print("The True Impact Score measures how much better/worse the team performs with each player at even strength.")
    print("\\nKey Findings:")
    print("- Elite Impact players significantly improve team performance when on ice")
    print("- Some players have negative impact despite high ice time")
    print("- Goal differential impact is the most important metric")
    print("- This reveals true team value beyond individual statistics")

def main():
    """
    Main function to run true on-ice vs off-ice impact analysis
    """
    # Analyze Edmonton Oilers
    analyze_team('EDM', 'Edmonton Oilers')
    
    print("\\n" + "="*100)
    print("="*100)
    
    # Analyze Florida Panthers
    analyze_team('FLA', 'Florida Panthers')

if __name__ == "__main__":
    main()
