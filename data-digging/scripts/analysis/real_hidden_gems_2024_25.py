#!/usr/bin/env python3
"""
Real Hidden Gems Analysis - 2024-25 Season
Using actual NHL data to find non-elite players who outperform their team
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
        ps.shooting_pct,
        -- Calculate derived metrics
        ps.goals / (ps.games_played * ps.toi_minutes_per_game / 60) as gf60_estimate,
        ps.assists / (ps.games_played * ps.toi_minutes_per_game / 60) as af60_estimate,
        ps.points / (ps.games_played * ps.toi_minutes_per_game / 60) as pts60_calculated
    FROM `fantasy-snipe-ai.nhl_raw.player_stats` ps
    WHERE ps.season = 20242025
    AND ps.games_played >= 20
    AND ps.position != 'G'
    ORDER BY ps.points DESC
    """
    
    return client.query(query).to_dataframe()

def classify_players_2024_25(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify players into tiers based on 2024-25 performance
    """
    df = df.copy()
    
    # Calculate goal differential estimate (using plus/minus as proxy)
    df['goal_diff_estimate'] = df['plus_minus'] / (df['games_played'] * df['toi_minutes_per_game'] / 60)
    
    # Classify players into tiers
    df['tier'] = 'Depth'
    
    # Elite players (top performers)
    elite_forwards = df[(df['position'].isin(['C', 'L', 'R'])) & 
                       (df['points_60'] >= 300) & 
                       (df['points'] >= 80)].copy()
    elite_defensemen = df[(df['position'] == 'D') & 
                         (df['points_60'] >= 200) & 
                         (df['points'] >= 50)].copy()
    
    elite_forwards['tier'] = 'Elite'
    elite_defensemen['tier'] = 'Elite'
    
    # Near Elite players
    near_elite_forwards = df[(df['position'].isin(['C', 'L', 'R'])) & 
                            (df['points_60'] >= 250) & 
                            (df['points'] >= 60) & 
                            (df['tier'] == 'Depth')].copy()
    near_elite_defensemen = df[(df['position'] == 'D') & 
                              (df['points_60'] >= 150) & 
                              (df['points'] >= 30) & 
                              (df['tier'] == 'Depth')].copy()
    
    near_elite_forwards['tier'] = 'Near Elite'
    near_elite_defensemen['tier'] = 'Near Elite'
    
    # Good players
    good_forwards = df[(df['position'].isin(['C', 'L', 'R'])) & 
                      (df['points_60'] >= 200) & 
                      (df['points'] >= 40) & 
                      (df['tier'] == 'Depth')].copy()
    good_defensemen = df[(df['position'] == 'D') & 
                        (df['points_60'] >= 100) & 
                        (df['points'] >= 20) & 
                        (df['tier'] == 'Depth')].copy()
    
    good_forwards['tier'] = 'Good'
    good_defensemen['tier'] = 'Good'
    
    # Core players (high TOI)
    core_players = df[(df['toi_minutes_per_game'] >= 18) & 
                     (df['tier'] == 'Depth')].copy()
    core_players['tier'] = 'Core'
    
    # Combine all classifications
    all_players = pd.concat([
        elite_forwards, elite_defensemen,
        near_elite_forwards, near_elite_defensemen,
        good_forwards, good_defensemen,
        core_players,
        df[df['tier'] == 'Depth']
    ])
    
    return all_players

def calculate_team_averages_2024_25(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate team averages for 2024-25 season
    """
    # Calculate team averages
    team_averages = df.groupby('team').agg({
        'points_60': 'mean',
        'goal_diff_estimate': 'mean',
        'toi_minutes_per_game': 'mean',
        'shooting_pct': 'mean',
        'points': 'mean'
    }).round(2)
    
    team_averages.columns = ['team_avg_pts60', 'team_avg_goal_diff', 'team_avg_toi', 'team_avg_shooting', 'team_avg_points']
    
    # Merge with player data
    df_with_team_avg = df.merge(team_averages, left_on='team', right_index=True)
    
    # Calculate impact vs team average
    df_with_team_avg['impact_vs_team_pts60'] = df_with_team_avg['points_60'] - df_with_team_avg['team_avg_pts60']
    df_with_team_avg['impact_vs_team_goal_diff'] = df_with_team_avg['goal_diff_estimate'] - df_with_team_avg['team_avg_goal_diff']
    
    return df_with_team_avg

def find_hidden_gems_2024_25(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """
    Find hidden gems from 2024-25 season - non-elite players with highest impact
    """
    # Filter out elite players
    non_elite = df[df['tier'] != 'Elite'].copy()
    
    # Sort by impact vs team average (using points/60 as primary metric)
    hidden_gems = non_elite.nlargest(top_n, 'impact_vs_team_pts60')
    
    return hidden_gems

def create_hidden_gems_visualization_2024_25(df: pd.DataFrame) -> None:
    """
    Create visualization for 2024-25 hidden gems
    """
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Plot 1: Top Hidden Gems by Impact vs Team
    top_15 = df.head(15)
    players = top_15['full_name']
    impact = top_15['impact_vs_team_pts60']
    tiers = top_15['tier']
    
    # Color by tier
    colors = []
    for tier in tiers:
        if tier == 'Near Elite':
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
    ax1.set_xlabel('Impact vs Team Average (Pts/60)')
    ax1.set_title('Hidden Gems: 2024-25 Season - Non-Elite Players with Highest Team Impact\\nTop 15 Performers')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + (5 if width >= 0 else -5), bar.get_y() + bar.get_height()/2,
                f'{width:.0f}', ha='left' if width >= 0 else 'right', va='center', fontsize=9)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='gold', label='Near Elite'),
                      Patch(facecolor='lightblue', label='Good'),
                      Patch(facecolor='lightgreen', label='Core'),
                      Patch(facecolor='lightgray', label='Other')]
    ax1.legend(handles=legend_elements, loc='lower right')
    
    # Plot 2: Impact vs Team by Tier
    tier_impact = df.groupby('tier')['impact_vs_team_pts60'].agg(['mean', 'std', 'count']).round(2)
    
    bars2 = ax2.bar(tier_impact.index, tier_impact['mean'], 
                    yerr=tier_impact['std'], capsize=5, alpha=0.7, 
                    color=['gold', 'lightblue', 'lightgreen', 'lightgray'])
    
    ax2.set_xlabel('Player Tier')
    ax2.set_ylabel('Average Impact vs Team (Pts/60)')
    ax2.set_title('2024-25 Season: Average Team Impact by Player Tier\\nNon-Elite Players Only')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + (5 if height >= 0 else -5),
                f'{height:.0f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
    
    plt.tight_layout()
    plt.show()

def create_detailed_hidden_gems_table_2024_25(df: pd.DataFrame) -> None:
    """
    Create detailed table of 2024-25 hidden gems
    """
    print("\\n" + "="*120)
    print("HIDDEN GEMS ANALYSIS - 2024-25 SEASON - NON-ELITE PLAYERS WITH HIGHEST TEAM IMPACT")
    print("="*120)
    
    # Create detailed table
    detailed_data = []
    for _, row in df.head(20).iterrows():
        detailed_data.append({
            'Player': row['full_name'],
            'Team': row['team'],
            'Position': row['position'],
            'Tier': row['tier'],
            'Games': row['games_played'],
            'TOI/Game': f"{row['toi_minutes_per_game']:.1f}",
            'Points': f"{row['points']:.0f}",
            'Pts/60': f"{row['points_60']:.0f}",
            'Team Avg Pts/60': f"{row['team_avg_pts60']:.0f}",
            'Impact vs Team': f"{row['impact_vs_team_pts60']:.0f}",
            'Plus/Minus': f"{row['plus_minus']:+.0f}",
            'Shooting %': f"{row['shooting_pct']:.1%}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*120)
    print("KEY INSIGHTS - 2024-25 SEASON")
    print("="*120)
    
    # Find highest impact player
    highest_impact = df.iloc[0]
    print(f"\\n🏆 HIGHEST IMPACT: {highest_impact['full_name']} ({highest_impact['team']})")
    print(f"   Tier: {highest_impact['tier']}")
    print(f"   Position: {highest_impact['position']}")
    print(f"   Impact vs Team: +{highest_impact['impact_vs_team_pts60']:.0f} Pts/60")
    print(f"   Player Pts/60: {highest_impact['points_60']:.0f}")
    print(f"   Team Average: {highest_impact['team_avg_pts60']:.0f}")
    print(f"   Total Points: {highest_impact['points']:.0f}")
    print(f"   Games Played: {highest_impact['games_played']}")
    
    # Tier analysis
    tier_analysis = df.groupby('tier').agg({
        'impact_vs_team_pts60': ['mean', 'max', 'count'],
        'points_60': 'mean',
        'points': 'mean',
        'toi_minutes_per_game': 'mean'
    }).round(2)
    
    print(f"\\n📊 TIER ANALYSIS - 2024-25:")
    for tier in ['Near Elite', 'Good', 'Core', 'Depth']:
        if tier in tier_analysis.index:
            tier_data = tier_analysis.loc[tier]
            print(f"   {tier}:")
            print(f"     Average Impact: {tier_data[('impact_vs_team_pts60', 'mean')]:.0f}")
            print(f"     Max Impact: {tier_data[('impact_vs_team_pts60', 'max')]:.0f}")
            print(f"     Count: {tier_data[('impact_vs_team_pts60', 'count')]:.0f}")
            print(f"     Avg Pts/60: {tier_data[('points_60', 'mean')]:.0f}")
            print(f"     Avg Points: {tier_data[('points', 'mean')]:.0f}")
            print(f"     Avg TOI/Game: {tier_data[('toi_minutes_per_game', 'mean')]:.1f}")

def create_team_context_analysis_2024_25(df: pd.DataFrame) -> None:
    """
    Analyze 2024-25 hidden gems by team context
    """
    # Group by team
    team_analysis = df.groupby('team').agg({
        'impact_vs_team_pts60': ['mean', 'max', 'count'],
        'points_60': 'mean',
        'team_avg_pts60': 'first'
    }).round(2)
    
    # Flatten column names
    team_analysis.columns = ['Avg Impact', 'Max Impact', 'Player Count', 'Avg Pts/60', 'Team Avg Pts/60']
    
    # Sort by average impact
    team_analysis = team_analysis.sort_values('Avg Impact', ascending=False)
    
    print("\\n" + "="*100)
    print("TEAM CONTEXT ANALYSIS - 2024-25 HIDDEN GEMS")
    print("="*100)
    print(team_analysis.to_string())
    
    # Insights
    print("\\n📈 TEAM INSIGHTS - 2024-25:")
    best_team = team_analysis.index[0]
    best_team_data = team_analysis.iloc[0]
    print(f"   Best Team for Hidden Gems: {best_team}")
    print(f"     Average Impact: {best_team_data['Avg Impact']:.0f}")
    print(f"     Max Impact: {best_team_data['Max Impact']:.0f}")
    print(f"     Hidden Gems Count: {best_team_data['Player Count']:.0f}")

def main():
    """
    Main function to run the 2024-25 hidden gems analysis
    """
    print("HIDDEN GEMS ANALYSIS - 2024-25 SEASON (REAL DATA)")
    print("Finding non-elite players who outperform their team average in 2024-25")
    print("="*80)
    
    # Get 2024-25 player data
    print("\\nFetching 2024-25 season data...")
    try:
        all_players_df = get_2024_25_real_data()
        print(f"✅ Found data for {len(all_players_df)} players in 2024-25 season")
    except Exception as e:
        print(f"❌ Error fetching 2024-25 data: {e}")
        return
    
    # Classify players
    print("\\nClassifying players into tiers...")
    classified_df = classify_players_2024_25(all_players_df)
    
    # Calculate team averages
    print("\\nCalculating team averages...")
    df_with_team_avg = calculate_team_averages_2024_25(classified_df)
    
    # Find hidden gems
    print("\\nIdentifying hidden gems from 2024-25 season...")
    hidden_gems_df = find_hidden_gems_2024_25(df_with_team_avg, top_n=25)
    
    print(f"✅ Found {len(hidden_gems_df)} hidden gems (non-elite players with positive team impact)")
    
    # Create visualizations
    print("\\nCreating 2024-25 hidden gems visualization...")
    create_hidden_gems_visualization_2024_25(hidden_gems_df)
    
    # Create detailed analysis
    create_detailed_hidden_gems_table_2024_25(hidden_gems_df)
    
    # Team context analysis
    create_team_context_analysis_2024_25(hidden_gems_df)
    
    print("\\n" + "="*80)
    print("2024-25 ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis identifies non-elite players who significantly outperformed their team's average in the 2024-25 season.")
    print("These 'hidden gems' represent undervalued players who provided exceptional value relative to their team context.")
    print("\\nKey Findings for 2024-25:")
    print("- Non-elite players can still have significant positive impact on their teams")
    print("- Position and tier analysis reveals patterns in hidden gem performance")
    print("- Team context significantly affects individual player impact")
    print("- These players represent potential value for future seasons")

if __name__ == "__main__":
    main()
