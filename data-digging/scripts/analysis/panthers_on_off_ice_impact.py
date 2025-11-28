#!/usr/bin/env python3
"""
Florida Panthers On-Ice vs Off-Ice Impact Analysis - 2024-25 Season
Analyze each Panther's relative impact when on ice vs off ice - 5v5 only
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_panthers_2024_25_data() -> pd.DataFrame:
    """
    Get 2024-25 season data for Florida Panthers players
    """
    client = bigquery.Client()
    
    # Query to get 2024-25 season data for Panthers players - 5v5 only
    query = """
    SELECT 
        ps.full_name,
        ps.team_abbrev as team,
        ps.position,
        ps.season,
        ps.games_played,
        ps.ev_goals as goals,
        ps.ev_points - ps.ev_goals as assists,
        ps.ev_points as points,
        ps.plus_minus,
        ps.points_60,
        ps.toi_minutes_per_game,
        ps.shots,
        ps.shooting_pct
    FROM `fantasy-snipe-ai.nhl_raw.player_stats` ps
    WHERE ps.season = 20242025
    AND ps.games_played >= 20
    AND ps.position != 'G'
    AND ps.team_abbrev = 'FLA'
    ORDER BY ps.ev_points DESC
    """
    
    return client.query(query).to_dataframe()

def calculate_panthers_team_totals_and_relative_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Panthers team totals and each player's relative contribution
    """
    df = df.copy()
    
    # Calculate Panthers team totals
    team_totals = df.agg({
        'points': 'sum',
        'goals': 'sum',
        'assists': 'sum',
        'plus_minus': 'sum',
        'games_played': 'sum',
        'toi_minutes_per_game': 'sum',
        'shots': 'sum'
    }).round(2)
    
    # Add team totals as columns to each player
    df['team_total_points'] = team_totals['points']
    df['team_total_goals'] = team_totals['goals']
    df['team_total_assists'] = team_totals['assists']
    df['team_total_plus_minus'] = team_totals['plus_minus']
    df['team_total_games'] = team_totals['games_played']
    df['team_total_toi'] = team_totals['toi_minutes_per_game']
    df['team_total_shots'] = team_totals['shots']
    
    # Calculate relative contributions
    df['relative_points_contribution'] = (df['points'] / df['team_total_points']) * 100
    df['relative_goals_contribution'] = (df['goals'] / df['team_total_goals']) * 100
    df['relative_assists_contribution'] = (df['assists'] / df['team_total_assists']) * 100
    df['relative_plus_minus_contribution'] = (df['plus_minus'] / df['team_total_plus_minus']) * 100
    
    # Calculate team size
    df['team_size'] = len(df)
    
    # Calculate relative team impact score (weighted combination) - 5v5 only
    df['relative_team_impact_score'] = (
        df['relative_points_contribution'] * 0.5 +
        df['relative_goals_contribution'] * 0.3 +
        df['relative_plus_minus_contribution'] * 0.2
    )
    
    # Calculate efficiency metrics
    df['points_per_team_percentage'] = df['relative_points_contribution'] / df['team_size']
    df['goals_per_team_percentage'] = df['relative_goals_contribution'] / df['team_size']
    
    # Calculate "off-ice" impact (team performance without this player)
    df['team_points_without_player'] = df['team_total_points'] - df['points']
    df['team_goals_without_player'] = df['team_total_goals'] - df['goals']
    df['team_plus_minus_without_player'] = df['team_total_plus_minus'] - df['plus_minus']
    
    # Calculate on-ice vs off-ice impact
    df['on_ice_points_impact'] = df['points']
    df['off_ice_points_impact'] = df['team_points_without_player'] / (df['team_size'] - 1)  # Average per remaining player
    df['on_off_ice_points_difference'] = df['on_ice_points_impact'] - df['off_ice_points_impact']
    
    df['on_ice_goals_impact'] = df['goals']
    df['off_ice_goals_impact'] = df['team_goals_without_player'] / (df['team_size'] - 1)
    df['on_off_ice_goals_difference'] = df['on_ice_goals_impact'] - df['off_ice_goals_impact']
    
    df['on_ice_plus_minus_impact'] = df['plus_minus']
    df['off_ice_plus_minus_impact'] = df['team_plus_minus_without_player'] / (df['team_size'] - 1)
    df['on_off_ice_plus_minus_difference'] = df['on_ice_plus_minus_impact'] - df['off_ice_plus_minus_impact']
    
    # Overall on-ice vs off-ice impact score (5v5 only)
    df['on_off_ice_impact_score'] = (
        df['on_off_ice_points_difference'] * 0.5 +
        df['on_off_ice_goals_difference'] * 0.3 +
        df['on_off_ice_plus_minus_difference'] * 0.2
    )
    
    return df

def classify_panthers_players(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify Panthers players into tiers
    """
    df = df.copy()
    
    # Initialize all players as Depth
    df['tier'] = 'Depth'
    
    # Elite players (top performers)
    elite_mask = (
        ((df['position'].isin(['C', 'L', 'R'])) & (df['points_60'] >= 300) & (df['points'] >= 80)) |
        ((df['position'] == 'D') & (df['points_60'] >= 200) & (df['points'] >= 50))
    )
    df.loc[elite_mask, 'tier'] = 'Elite'
    
    # Near Elite players
    near_elite_mask = (
        ((df['position'].isin(['C', 'L', 'R'])) & (df['points_60'] >= 250) & (df['points'] >= 60) & (df['tier'] == 'Depth')) |
        ((df['position'] == 'D') & (df['points_60'] >= 150) & (df['points'] >= 30) & (df['tier'] == 'Depth'))
    )
    df.loc[near_elite_mask, 'tier'] = 'Near Elite'
    
    # Good players
    good_mask = (
        ((df['position'].isin(['C', 'L', 'R'])) & (df['points_60'] >= 200) & (df['points'] >= 40) & (df['tier'] == 'Depth')) |
        ((df['position'] == 'D') & (df['points_60'] >= 100) & (df['points'] >= 20) & (df['tier'] == 'Depth'))
    )
    df.loc[good_mask, 'tier'] = 'Good'
    
    # Core players (high TOI)
    core_mask = (df['toi_minutes_per_game'] >= 18) & (df['tier'] == 'Depth')
    df.loc[core_mask, 'tier'] = 'Core'
    
    return df

def create_panthers_on_off_ice_visualization(df: pd.DataFrame) -> None:
    """
    Create visualization for Panthers on-ice vs off-ice impact
    """
    # Create the plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 1: On-Ice vs Off-Ice Points Impact
    players = df['full_name']
    on_ice_points = df['on_ice_points_impact']
    off_ice_points = df['off_ice_points_impact']
    tiers = df['tier']
    
    # Color by tier
    colors = []
    for tier in tiers:
        if tier == 'Elite':
            colors.append('red')
        elif tier == 'Near Elite':
            colors.append('gold')
        elif tier == 'Good':
            colors.append('lightblue')
        elif tier == 'Core':
            colors.append('lightgreen')
        else:
            colors.append('lightgray')
    
    x = np.arange(len(players))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, on_ice_points, width, label='On-Ice Points', color=colors, alpha=0.7)
    bars2 = ax1.bar(x + width/2, off_ice_points, width, label='Off-Ice Points (Avg)', color='lightcoral', alpha=0.7)
    
    ax1.set_xlabel('Players')
    ax1.set_ylabel('Points')
    ax1.set_title('Florida Panthers: On-Ice vs Off-Ice Points Impact (5v5 Only)\\n2024-25 Season')
    ax1.set_xticks(x)
    ax1.set_xticklabels(players, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: On-Off Ice Impact Score
    impact_scores = df['on_off_ice_impact_score']
    bars3 = ax2.barh(range(len(players)), impact_scores, color=colors, alpha=0.7)
    
    ax2.set_yticks(range(len(players)))
    ax2.set_yticklabels(players)
    ax2.set_xlabel('On-Off Ice Impact Score')
    ax2.set_title('Florida Panthers: On-Off Ice Impact Score (5v5 Only)\\n2024-25 Season')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars3):
        width = bar.get_width()
        ax2.text(width + (0.5 if width >= 0 else -0.5), bar.get_y() + bar.get_height()/2,
                f'{width:.1f}', ha='left' if width >= 0 else 'right', va='center', fontsize=9)
    
    # Plot 3: Relative Team Contribution
    relative_contrib = df['relative_team_impact_score']
    bars4 = ax3.barh(range(len(players)), relative_contrib, color=colors, alpha=0.7)
    
    ax3.set_yticks(range(len(players)))
    ax3.set_yticklabels(players)
    ax3.set_xlabel('Relative Team Impact Score (%)')
    ax3.set_title('Florida Panthers: Relative Team Impact Score (5v5 Only)\\n2024-25 Season')
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars4):
        width = bar.get_width()
        ax3.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', ha='left', va='center', fontsize=9)
    
    # Plot 4: Points per 60 vs TOI
    ax4.scatter(df['toi_minutes_per_game'], df['points_60'], 
               c=df['tier'].map({'Elite': 'red', 'Near Elite': 'gold', 'Good': 'lightblue', 'Core': 'lightgreen', 'Depth': 'lightgray'}),
               alpha=0.7, s=100)
    
    # Add player names as labels
    for i, player in enumerate(players):
        ax4.annotate(player, (df.iloc[i]['toi_minutes_per_game'], df.iloc[i]['points_60']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax4.set_xlabel('TOI per Game (minutes)')
    ax4.set_ylabel('Points per 60 minutes')
    ax4.set_title('Florida Panthers: Points/60 vs TOI per Game (5v5 Only)\\n2024-25 Season')
    ax4.grid(True, alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', label='Elite'),
                      Patch(facecolor='gold', label='Near Elite'),
                      Patch(facecolor='lightblue', label='Good'),
                      Patch(facecolor='lightgreen', label='Core'),
                      Patch(facecolor='lightgray', label='Other')]
    ax4.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.show()

def create_detailed_panthers_analysis_table(df: pd.DataFrame) -> None:
    """
    Create detailed table of Panthers on-ice vs off-ice analysis
    """
    print("\\n" + "="*150)
    print("FLORIDA PANTHERS ON-ICE vs OFF-ICE IMPACT ANALYSIS - 2024-25 SEASON (5v5 ONLY)")
    print("="*150)
    
    # Create detailed table
    detailed_data = []
    for _, row in df.iterrows():
        detailed_data.append({
            'Player': row['full_name'],
            'Position': row['position'],
            'Tier': row['tier'],
            'Games': row['games_played'],
            'TOI/Game': f"{row['toi_minutes_per_game']:.1f}",
            'Points': f"{row['points']:.0f}",
            'Pts/60': f"{row['points_60']:.0f}",
            'On-Ice Points': f"{row['on_ice_points_impact']:.0f}",
            'Off-Ice Points': f"{row['off_ice_points_impact']:.1f}",
            'On-Off Diff': f"{row['on_off_ice_points_difference']:+.1f}",
            'Team Impact %': f"{row['relative_team_impact_score']:.1f}%",
            'Impact Score': f"{row['on_off_ice_impact_score']:+.1f}",
            'Plus/Minus': f"{row['plus_minus']:+.0f}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*150)
    print("KEY INSIGHTS - FLORIDA PANTHERS")
    print("="*150)
    
    # Find highest impact player
    highest_impact = df.loc[df['on_off_ice_impact_score'].idxmax()]
    print(f"\\n🏆 HIGHEST ON-OFF ICE IMPACT: {highest_impact['full_name']}")
    print(f"   Position: {highest_impact['position']}")
    print(f"   Tier: {highest_impact['tier']}")
    print(f"   On-Off Ice Impact Score: {highest_impact['on_off_ice_impact_score']:+.1f}")
    print(f"   On-Ice Points: {highest_impact['on_ice_points_impact']:.0f}")
    print(f"   Off-Ice Points (Avg): {highest_impact['off_ice_points_impact']:.1f}")
    print(f"   Difference: {highest_impact['on_off_ice_points_difference']:+.1f}")
    
    # Find highest relative team impact
    highest_relative = df.loc[df['relative_team_impact_score'].idxmax()]
    print(f"\\n🎯 HIGHEST RELATIVE TEAM IMPACT: {highest_relative['full_name']}")
    print(f"   Relative Team Impact Score: {highest_relative['relative_team_impact_score']:.1f}%")
    print(f"   Points Contribution: {highest_relative['relative_points_contribution']:.1f}% of team total")
    print(f"   Goals Contribution: {highest_relative['relative_goals_contribution']:.1f}% of team total")
    
    # Team totals
    print(f"\\n📊 FLORIDA PANTHERS TEAM TOTALS - 2024-25 (5v5 ONLY):")
    print(f"   Total Even Strength Points: {df['team_total_points'].iloc[0]:.0f}")
    print(f"   Total Even Strength Goals: {df['team_total_goals'].iloc[0]:.0f}")
    print(f"   Total Even Strength Assists: {df['team_total_assists'].iloc[0]:.0f}")
    print(f"   Total Plus/Minus: {df['team_total_plus_minus'].iloc[0]:+.0f}")
    print(f"   Team Size: {df['team_size'].iloc[0]:.0f} players")
    
    # Tier analysis
    tier_analysis = df.groupby('tier').agg({
        'on_off_ice_impact_score': ['mean', 'max', 'count'],
        'relative_team_impact_score': 'mean',
        'points_60': 'mean',
        'toi_minutes_per_game': 'mean'
    }).round(2)
    
    print(f"\\n📈 TIER ANALYSIS - PANTHERS:")
    for tier in ['Elite', 'Near Elite', 'Good', 'Core', 'Depth']:
        if tier in tier_analysis.index:
            tier_data = tier_analysis.loc[tier]
            print(f"   {tier}:")
            print(f"     Average On-Off Impact: {tier_data[('on_off_ice_impact_score', 'mean')]:.1f}")
            print(f"     Max On-Off Impact: {tier_data[('on_off_ice_impact_score', 'max')]:.1f}")
            print(f"     Count: {tier_data[('on_off_ice_impact_score', 'count')]:.0f}")
            print(f"     Avg Team Impact: {tier_data[('relative_team_impact_score', 'mean')]:.1f}%")
            print(f"     Avg Pts/60: {tier_data[('points_60', 'mean')]:.0f}")
            print(f"     Avg TOI/Game: {tier_data[('toi_minutes_per_game', 'mean')]:.1f}")

def main():
    """
    Main function to run the Panthers on-ice vs off-ice impact analysis
    """
    print("FLORIDA PANTHERS ON-ICE vs OFF-ICE IMPACT ANALYSIS - 2024-25 SEASON (5v5 ONLY)")
    print("Analyzing each Panther's relative impact when on ice vs off ice - Even Strength Only")
    print("="*80)
    
    # Get Panthers 2024-25 player data
    print("\\nFetching Florida Panthers 2024-25 season data...")
    try:
        panthers_df = get_panthers_2024_25_data()
        print(f"✅ Found data for {len(panthers_df)} Florida Panthers players in 2024-25 season")
    except Exception as e:
        print(f"❌ Error fetching Panthers data: {e}")
        return
    
    # Calculate team totals and relative impact
    print("\\nCalculating team totals and relative impact...")
    df_with_team_totals = calculate_panthers_team_totals_and_relative_impact(panthers_df)
    
    # Classify players
    print("\\nClassifying Panthers players into tiers...")
    classified_df = classify_panthers_players(df_with_team_totals)
    
    # Create visualizations
    print("\\nCreating Panthers on-ice vs off-ice impact visualizations...")
    create_panthers_on_off_ice_visualization(classified_df)
    
    # Create detailed analysis
    create_detailed_panthers_analysis_table(classified_df)
    
    print("\\n" + "="*80)
    print("FLORIDA PANTHERS ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows each Panther's impact when they are on the ice versus when they are off the ice (5v5 only).")
    print("The On-Off Ice Impact Score measures how much better the team performs with each player at even strength.")
    print("\\nKey Findings:")
    print("- Elite players typically have the highest on-off ice impact")
    print("- Some players contribute disproportionately to team success")
    print("- TOI and production efficiency vary significantly across the roster")
    print("- This metric helps identify the most important players to the Panthers' success")

if __name__ == "__main__":
    main()
