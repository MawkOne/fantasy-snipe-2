#!/usr/bin/env python3
"""
Relative Team Impact Analysis - 2024-25 Season
Calculate each player's relative impact on their team's overall performance
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_2024_25_real_data() -> pd.DataFrame:
    """
    Get real 2024-25 season data for all players
    """
    client = bigquery.Client()
    
    # Query to get 2024-25 season data for all players
    query = """
    SELECT 
        ps.full_name,
        ps.team_abbrev as team,
        ps.position,
        ps.season,
        ps.games_played,
        ps.goals,
        ps.assists,
        ps.points,
        ps.plus_minus,
        ps.points_60,
        ps.toi_minutes_per_game,
        ps.shots,
        ps.shooting_pct
    FROM `fantasy-snipe-ai.nhl_raw.player_stats` ps
    WHERE ps.season = 20242025
    AND ps.games_played >= 20
    AND ps.position != 'G'
    ORDER BY ps.points DESC
    """
    
    return client.query(query).to_dataframe()

def calculate_team_totals_and_relative_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate team totals and each player's relative contribution
    """
    df = df.copy()
    
    # Calculate team totals
    team_totals = df.groupby('team').agg({
        'points': 'sum',
        'goals': 'sum',
        'assists': 'sum',
        'plus_minus': 'sum',
        'games_played': 'sum',
        'toi_minutes_per_game': 'sum',
        'shots': 'sum'
    }).round(2)
    
    team_totals.columns = ['team_total_points', 'team_total_goals', 'team_total_assists', 
                          'team_total_plus_minus', 'team_total_games', 'team_total_toi', 'team_total_shots']
    
    # Merge team totals with player data
    df_with_team_totals = df.merge(team_totals, left_on='team', right_index=True)
    
    # Calculate relative contributions
    df_with_team_totals['relative_points_contribution'] = (df_with_team_totals['points'] / df_with_team_totals['team_total_points']) * 100
    df_with_team_totals['relative_goals_contribution'] = (df_with_team_totals['goals'] / df_with_team_totals['team_total_goals']) * 100
    df_with_team_totals['relative_assists_contribution'] = (df_with_team_totals['assists'] / df_with_team_totals['team_total_assists']) * 100
    df_with_team_totals['relative_plus_minus_contribution'] = (df_with_team_totals['plus_minus'] / df_with_team_totals['team_total_plus_minus']) * 100
    
    # Calculate team size and player's relative importance
    team_sizes = df.groupby('team').size().reset_index(name='team_size')
    df_with_team_totals = df_with_team_totals.merge(team_sizes, left_on='team', right_on='team')
    
    # Calculate relative team impact score (weighted combination)
    # This combines points contribution, goals contribution, and plus/minus contribution
    df_with_team_totals['relative_team_impact_score'] = (
        df_with_team_totals['relative_points_contribution'] * 0.5 +
        df_with_team_totals['relative_goals_contribution'] * 0.3 +
        df_with_team_totals['relative_plus_minus_contribution'] * 0.2
    )
    
    # Calculate efficiency metrics
    df_with_team_totals['points_per_team_percentage'] = df_with_team_totals['relative_points_contribution'] / df_with_team_totals['team_size']
    df_with_team_totals['goals_per_team_percentage'] = df_with_team_totals['relative_goals_contribution'] / df_with_team_totals['team_size']
    
    return df_with_team_totals

def classify_players_properly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Properly classify players into tiers - each player gets ONE tier
    """
    df = df.copy()
    
    # Initialize all players as Depth
    df['tier'] = 'Depth'
    
    # Elite players (top performers) - these will be EXCLUDED from hidden gems
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

def find_top_relative_impact_players(df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """
    Find players with highest relative team impact
    """
    # Sort by relative team impact score
    top_players = df.nlargest(top_n, 'relative_team_impact_score')
    
    return top_players

def create_relative_impact_visualization(df: pd.DataFrame) -> None:
    """
    Create visualization for relative team impact analysis
    """
    # Create the plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 1: Top 25 Players by Relative Team Impact
    top_25 = df.head(25)
    players = top_25['full_name']
    impact = top_25['relative_team_impact_score']
    tiers = top_25['tier']
    
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
    
    bars1 = ax1.barh(range(len(players)), impact, color=colors, alpha=0.7)
    
    ax1.set_yticks(range(len(players)))
    ax1.set_yticklabels(players)
    ax1.set_xlabel('Relative Team Impact Score')
    ax1.set_title('Top 25 Players by Relative Team Impact\\n2024-25 Season')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', ha='left', va='center', fontsize=8)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', label='Elite'),
                      Patch(facecolor='gold', label='Near Elite'),
                      Patch(facecolor='lightblue', label='Good'),
                      Patch(facecolor='lightgreen', label='Core'),
                      Patch(facecolor='lightgray', label='Other')]
    ax1.legend(handles=legend_elements, loc='lower right')
    
    # Plot 2: Points Contribution vs Team Size
    ax2.scatter(df['team_size'], df['relative_points_contribution'], 
               c=df['tier'].map({'Elite': 'red', 'Near Elite': 'gold', 'Good': 'lightblue', 'Core': 'lightgreen', 'Depth': 'lightgray'}),
               alpha=0.6, s=50)
    ax2.set_xlabel('Team Size (Number of Players)')
    ax2.set_ylabel('Relative Points Contribution (%)')
    ax2.set_title('Points Contribution vs Team Size\\n2024-25 Season')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Relative Impact by Tier
    tier_impact = df.groupby('tier')['relative_team_impact_score'].agg(['mean', 'std', 'count']).round(2)
    
    bars3 = ax3.bar(tier_impact.index, tier_impact['mean'], 
                    yerr=tier_impact['std'], capsize=5, alpha=0.7, 
                    color=['red', 'gold', 'lightblue', 'lightgreen', 'lightgray'])
    
    ax3.set_xlabel('Player Tier')
    ax3.set_ylabel('Average Relative Team Impact Score')
    ax3.set_title('Average Relative Team Impact by Tier\\n2024-25 Season')
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars3):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # Plot 4: Team Impact Distribution
    team_impact = df.groupby('team')['relative_team_impact_score'].agg(['mean', 'max', 'count']).round(2)
    team_impact = team_impact.sort_values('mean', ascending=False)
    
    bars4 = ax4.bar(range(len(team_impact)), team_impact['mean'], alpha=0.7, color='skyblue')
    ax4.set_xlabel('Teams')
    ax4.set_ylabel('Average Relative Team Impact Score')
    ax4.set_title('Average Relative Team Impact by Team\\n2024-25 Season')
    ax4.set_xticks(range(len(team_impact)))
    ax4.set_xticklabels(team_impact.index, rotation=45, ha='right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def create_detailed_relative_impact_table(df: pd.DataFrame) -> None:
    """
    Create detailed table of relative team impact analysis
    """
    print("\\n" + "="*140)
    print("RELATIVE TEAM IMPACT ANALYSIS - 2024-25 SEASON")
    print("="*140)
    
    # Create detailed table
    detailed_data = []
    for _, row in df.head(30).iterrows():
        detailed_data.append({
            'Player': row['full_name'],
            'Team': row['team'],
            'Position': row['position'],
            'Tier': row['tier'],
            'Points': f"{row['points']:.0f}",
            'Team Total Points': f"{row['team_total_points']:.0f}",
            'Points %': f"{row['relative_points_contribution']:.1f}%",
            'Goals %': f"{row['relative_goals_contribution']:.1f}%",
            'Assists %': f"{row['relative_assists_contribution']:.1f}%",
            'Plus/Minus %': f"{row['relative_plus_minus_contribution']:.1f}%",
            'Impact Score': f"{row['relative_team_impact_score']:.1f}%",
            'Team Size': f"{row['team_size']:.0f}",
            'Efficiency': f"{row['points_per_team_percentage']:.2f}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*140)
    print("KEY INSIGHTS - RELATIVE TEAM IMPACT")
    print("="*140)
    
    # Find highest impact player
    highest_impact = df.iloc[0]
    print(f"\\n🏆 HIGHEST RELATIVE IMPACT: {highest_impact['full_name']} ({highest_impact['team']})")
    print(f"   Tier: {highest_impact['tier']}")
    print(f"   Position: {highest_impact['position']}")
    print(f"   Relative Team Impact Score: {highest_impact['relative_team_impact_score']:.1f}%")
    print(f"   Points Contribution: {highest_impact['relative_points_contribution']:.1f}% of team total")
    print(f"   Goals Contribution: {highest_impact['relative_goals_contribution']:.1f}% of team total")
    print(f"   Team Size: {highest_impact['team_size']} players")
    print(f"   Efficiency Score: {highest_impact['points_per_team_percentage']:.2f}")
    
    # Tier analysis
    tier_analysis = df.groupby('tier').agg({
        'relative_team_impact_score': ['mean', 'max', 'count'],
        'relative_points_contribution': 'mean',
        'points_per_team_percentage': 'mean'
    }).round(2)
    
    print(f"\\n📊 TIER ANALYSIS - RELATIVE IMPACT:")
    for tier in ['Elite', 'Near Elite', 'Good', 'Core', 'Depth']:
        if tier in tier_analysis.index:
            tier_data = tier_analysis.loc[tier]
            print(f"   {tier}:")
            print(f"     Average Impact Score: {tier_data[('relative_team_impact_score', 'mean')]:.1f}%")
            print(f"     Max Impact Score: {tier_data[('relative_team_impact_score', 'max')]:.1f}%")
            print(f"     Count: {tier_data[('relative_team_impact_score', 'count')]:.0f}")
            print(f"     Avg Points Contribution: {tier_data[('relative_points_contribution', 'mean')]:.1f}%")
            print(f"     Avg Efficiency: {tier_data[('points_per_team_percentage', 'mean')]:.2f}")

def create_team_impact_analysis(df: pd.DataFrame) -> None:
    """
    Analyze relative team impact by team
    """
    # Group by team
    team_analysis = df.groupby('team').agg({
        'relative_team_impact_score': ['mean', 'max', 'count'],
        'relative_points_contribution': 'mean',
        'team_size': 'first',
        'team_total_points': 'first'
    }).round(2)
    
    # Flatten column names
    team_analysis.columns = ['Avg Impact Score', 'Max Impact Score', 'Player Count', 'Avg Points Contribution', 'Team Size', 'Team Total Points']
    
    # Sort by average impact score
    team_analysis = team_analysis.sort_values('Avg Impact Score', ascending=False)
    
    print("\\n" + "="*120)
    print("TEAM IMPACT ANALYSIS - 2024-25 SEASON")
    print("="*120)
    print(team_analysis.to_string())
    
    # Insights
    print("\\n📈 TEAM INSIGHTS - RELATIVE IMPACT:")
    best_team = team_analysis.index[0]
    best_team_data = team_analysis.iloc[0]
    print(f"   Best Team for Relative Impact: {best_team}")
    print(f"     Average Impact Score: {best_team_data['Avg Impact Score']:.1f}%")
    print(f"     Max Impact Score: {best_team_data['Max Impact Score']:.1f}%")
    print(f"     Team Size: {best_team_data['Team Size']:.0f} players")
    print(f"     Total Team Points: {best_team_data['Team Total Points']:.0f}")

def main():
    """
    Main function to run the relative team impact analysis
    """
    print("RELATIVE TEAM IMPACT ANALYSIS - 2024-25 SEASON")
    print("Calculating each player's relative impact on their team's overall performance")
    print("="*80)
    
    # Get 2024-25 player data
    print("\\nFetching 2024-25 season data...")
    try:
        all_players_df = get_2024_25_real_data()
        print(f"✅ Found data for {len(all_players_df)} players in 2024-25 season")
    except Exception as e:
        print(f"❌ Error fetching 2024-25 data: {e}")
        return
    
    # Calculate team totals and relative impact
    print("\\nCalculating team totals and relative impact...")
    df_with_team_totals = calculate_team_totals_and_relative_impact(all_players_df)
    
    # Classify players
    print("\\nClassifying players into tiers...")
    classified_df = classify_players_properly(df_with_team_totals)
    
    # Find top relative impact players
    print("\\nIdentifying top relative impact players...")
    top_impact_df = find_top_relative_impact_players(classified_df, top_n=50)
    
    print(f"✅ Found {len(top_impact_df)} players with highest relative team impact")
    
    # Create visualizations
    print("\\nCreating relative impact visualizations...")
    create_relative_impact_visualization(top_impact_df)
    
    # Create detailed analysis
    create_detailed_relative_impact_table(top_impact_df)
    
    # Team impact analysis
    create_team_impact_analysis(top_impact_df)
    
    print("\\n" + "="*80)
    print("RELATIVE TEAM IMPACT ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows each player's relative contribution to their team's overall performance.")
    print("The Relative Team Impact Score combines points, goals, and plus/minus contributions.")
    print("\\nKey Findings:")
    print("- Elite players typically have the highest relative team impact")
    print("- Team size affects individual player impact scores")
    print("- Some players contribute disproportionately to their team's success")
    print("- This metric helps identify the most important players to each team")

if __name__ == "__main__":
    main()
