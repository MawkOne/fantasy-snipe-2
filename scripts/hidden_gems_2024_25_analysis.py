#!/usr/bin/env python3
"""
Hidden Gems Analysis - 2024-25 Season Only
Find non-elite players who outperform their team average in 2024-25
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_2024_25_player_data() -> pd.DataFrame:
    """
    Get 2024-25 season data for all players from our database
    """
    client = bigquery.Client()
    
    # Query to get 2024-25 season data for all players
    query = """
    WITH player_2024_25 AS (
        SELECT 
            p.player_id,
            p.full_name,
            t.tri_code as team_abbr,
            p.position,
            p.age,
            pst.season,
            pst.games_played,
            pst.toi_minutes / pst.games_played as toi_per_game,
            pst.cf_pct_weighted as cf_pct,
            pst.gf60,
            pst.ga60,
            pst.gf60 - pst.ga60 as goal_diff_60,
            pst.pts60_weighted as pts60,
            ps.points,
            ps.goals,
            ps.assists,
            ps.plus_minus
        FROM `fantasy-snipe-ai.nhl_raw.players` p
        JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst ON p.player_id = pst.player_id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON p.player_id = ps.player_id AND pst.season = ps.season
        WHERE pst.season = 20242025
        AND pst.game_type = 2
        AND pst.games_played >= 20
        AND p.position != 'G'
    ),
    
    -- Calculate team averages for 2024-25
    team_averages_2024_25 AS (
        SELECT 
            team_abbr,
            AVG(gf60 - ga60) as team_avg_goal_diff_60,
            AVG(gf60) as team_avg_gf60,
            AVG(ga60) as team_avg_ga60,
            AVG(cf_pct) as team_avg_cf_pct,
            COUNT(*) as team_player_count
        FROM player_2024_25
        GROUP BY team_abbr
    ),
    
    -- Classify players into tiers based on 2024-25 performance
    player_tiers AS (
        SELECT 
            *,
            CASE 
                WHEN (position IN ('C', 'L', 'R') AND pts60 >= 2.0 AND points >= 60) 
                     OR (position = 'D' AND pts60 >= 1.2 AND points >= 40) THEN 'Elite'
                WHEN (position IN ('C', 'L', 'R') AND pts60 >= 1.5 AND points >= 40) 
                     OR (position = 'D' AND pts60 >= 0.8 AND points >= 25) THEN 'Near Elite'
                WHEN (position IN ('C', 'L', 'R') AND pts60 >= 1.0 AND points >= 25) 
                     OR (position = 'D' AND pts60 >= 0.5 AND points >= 15) THEN 'Good'
                WHEN toi_per_game >= 18 THEN 'Core'
                WHEN toi_per_game >= 15 THEN 'Middle 6'
                WHEN toi_per_game >= 12 THEN 'Bottom 6'
                ELSE 'Depth'
            END as toi_tier
        FROM player_2024_25
    )
    
    SELECT 
        pt.player_id,
        pt.full_name,
        pt.team_abbr,
        pt.position,
        pt.age,
        pt.games_played,
        pt.toi_per_game,
        pt.goal_diff_60,
        pt.cf_pct,
        pt.gf60,
        pt.ga60,
        pt.pts60,
        pt.points,
        pt.toi_tier,
        ta.team_avg_goal_diff_60,
        ta.team_avg_gf60,
        ta.team_avg_ga60,
        ta.team_avg_cf_pct,
        ta.team_player_count,
        -- Calculate impact vs team average
        pt.goal_diff_60 - ta.team_avg_goal_diff_60 as impact_vs_team_60
    FROM player_tiers pt
    JOIN team_averages_2024_25 ta ON pt.team_abbr = ta.team_abbr
    ORDER BY impact_vs_team_60 DESC
    """
    
    return client.query(query).to_dataframe()

def find_hidden_gems_2024_25(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """
    Find the top hidden gems from 2024-25 season - non-elite players with highest impact vs team
    """
    # Filter out elite players
    non_elite = df[df['toi_tier'] != 'Elite'].copy()
    
    # Sort by impact vs team average
    hidden_gems = non_elite.nlargest(top_n, 'impact_vs_team_60')
    
    return hidden_gems

def create_hidden_gems_visualization_2024_25(df: pd.DataFrame) -> None:
    """
    Create visualization for 2024-25 hidden gems analysis
    """
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Plot 1: Top Hidden Gems by Impact vs Team
    top_15 = df.head(15)
    players = top_15['full_name']
    impact = top_15['impact_vs_team_60']
    tiers = top_15['toi_tier']
    
    # Color by tier
    colors = []
    for tier in tiers:
        if tier == 'Near Elite':
            colors.append('gold')
        elif tier == 'Good':
            colors.append('lightblue')
        elif tier == 'Core':
            colors.append('lightgreen')
        elif tier == 'Middle 6':
            colors.append('lightcoral')
        else:
            colors.append('lightgray')
    
    bars1 = ax1.barh(range(len(players)), impact, color=colors, alpha=0.7)
    
    ax1.set_yticks(range(len(players)))
    ax1.set_yticklabels(players)
    ax1.set_xlabel('Impact vs Team Average (Goal Diff/60)')
    ax1.set_title('Hidden Gems: 2024-25 Season - Non-Elite Players with Highest Team Impact\\nTop 15 Performers')
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + (0.1 if width >= 0 else -0.1), bar.get_y() + bar.get_height()/2,
                f'{width:.2f}', ha='left' if width >= 0 else 'right', va='center', fontsize=9)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='gold', label='Near Elite'),
                      Patch(facecolor='lightblue', label='Good'),
                      Patch(facecolor='lightgreen', label='Core'),
                      Patch(facecolor='lightcoral', label='Middle 6'),
                      Patch(facecolor='lightgray', label='Other')]
    ax1.legend(handles=legend_elements, loc='lower right')
    
    # Plot 2: Impact vs Team by Tier
    tier_impact = df.groupby('toi_tier')['impact_vs_team_60'].agg(['mean', 'std', 'count']).round(2)
    
    bars2 = ax2.bar(tier_impact.index, tier_impact['mean'], 
                    yerr=tier_impact['std'], capsize=5, alpha=0.7, 
                    color=['gold', 'lightblue', 'lightgreen', 'lightcoral', 'lightgray'])
    
    ax2.set_xlabel('Player Tier')
    ax2.set_ylabel('Average Impact vs Team (Goal Diff/60)')
    ax2.set_title('2024-25 Season: Average Team Impact by Player Tier\\nNon-Elite Players Only')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height >= 0 else -0.05),
                f'{height:.2f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
    
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
            'Team': row['team_abbr'],
            'Position': row['position'],
            'Tier': row['toi_tier'],
            'Age': row['age'],
            'Games': row['games_played'],
            'TOI/Game': f"{row['toi_per_game']:.1f}",
            'Player Goal Diff/60': f"{row['goal_diff_60']:.2f}",
            'Team Avg Goal Diff/60': f"{row['team_avg_goal_diff_60']:.2f}",
            'Impact vs Team': f"{row['impact_vs_team_60']:.2f}",
            'Player CF%': f"{row['cf_pct']:.1f}%",
            'Pts/60': f"{row['pts60']:.2f}",
            'Total Points': f"{row['points']:.0f}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*120)
    print("KEY INSIGHTS - 2024-25 SEASON")
    print("="*120)
    
    # Find highest impact player
    highest_impact = df.iloc[0]
    print(f"\\n🏆 HIGHEST IMPACT: {highest_impact['full_name']} ({highest_impact['team_abbr']})")
    print(f"   Tier: {highest_impact['toi_tier']}")
    print(f"   Position: {highest_impact['position']}")
    print(f"   Impact vs Team: +{highest_impact['impact_vs_team_60']:.2f} Goal Diff/60")
    print(f"   Player Performance: {highest_impact['goal_diff_60']:.2f} Goal Diff/60")
    print(f"   Team Average: {highest_impact['team_avg_goal_diff_60']:.2f} Goal Diff/60")
    print(f"   Games Played: {highest_impact['games_played']}")
    
    # Tier analysis
    tier_analysis = df.groupby('toi_tier').agg({
        'impact_vs_team_60': ['mean', 'max', 'count'],
        'goal_diff_60': 'mean',
        'cf_pct': 'mean',
        'toi_per_game': 'mean'
    }).round(2)
    
    print(f"\\n📊 TIER ANALYSIS - 2024-25:")
    for tier in ['Near Elite', 'Good', 'Core', 'Middle 6', 'Bottom 6']:
        if tier in tier_analysis.index:
            tier_data = tier_analysis.loc[tier]
            print(f"   {tier}:")
            print(f"     Average Impact: {tier_data[('impact_vs_team_60', 'mean')]:.2f}")
            print(f"     Max Impact: {tier_data[('impact_vs_team_60', 'max')]:.2f}")
            print(f"     Count: {tier_data[('impact_vs_team_60', 'count')]:.0f}")
            print(f"     Avg Goal Diff/60: {tier_data[('goal_diff_60', 'mean')]:.2f}")
            print(f"     Avg CF%: {tier_data[('cf_pct', 'mean')]:.1f}%")
            print(f"     Avg TOI/Game: {tier_data[('toi_per_game', 'mean')]:.1f}")

def create_team_context_analysis_2024_25(df: pd.DataFrame) -> None:
    """
    Analyze 2024-25 hidden gems by team context
    """
    # Group by team
    team_analysis = df.groupby('team_abbr').agg({
        'impact_vs_team_60': ['mean', 'max', 'count'],
        'goal_diff_60': 'mean',
        'team_avg_goal_diff_60': 'first',
        'team_player_count': 'first'
    }).round(2)
    
    # Flatten column names
    team_analysis.columns = ['Avg Impact', 'Max Impact', 'Player Count', 'Avg Goal Diff/60', 'Team Avg Goal Diff/60', 'Total Team Players']
    
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
    print(f"     Average Impact: {best_team_data['Avg Impact']:.2f}")
    print(f"     Max Impact: {best_team_data['Max Impact']:.2f}")
    print(f"     Hidden Gems Count: {best_team_data['Player Count']:.0f}")
    print(f"     Total Team Players: {best_team_data['Total Team Players']:.0f}")

def create_position_analysis_2024_25(df: pd.DataFrame) -> None:
    """
    Analyze 2024-25 hidden gems by position
    """
    position_analysis = df.groupby('position').agg({
        'impact_vs_team_60': ['mean', 'max', 'count'],
        'goal_diff_60': 'mean',
        'cf_pct': 'mean',
        'toi_per_game': 'mean'
    }).round(2)
    
    # Flatten column names
    position_analysis.columns = ['Avg Impact', 'Max Impact', 'Count', 'Avg Goal Diff/60', 'Avg CF%', 'Avg TOI/Game']
    
    # Sort by average impact
    position_analysis = position_analysis.sort_values('Avg Impact', ascending=False)
    
    print("\\n" + "="*80)
    print("POSITION ANALYSIS - 2024-25 HIDDEN GEMS")
    print("="*80)
    print(position_analysis.to_string())
    
    # Insights
    print("\\n🏒 POSITION INSIGHTS - 2024-25:")
    best_position = position_analysis.index[0]
    best_position_data = position_analysis.iloc[0]
    print(f"   Best Position for Hidden Gems: {best_position}")
    print(f"     Average Impact: {best_position_data['Avg Impact']:.2f}")
    print(f"     Max Impact: {best_position_data['Max Impact']:.2f}")
    print(f"     Count: {best_position_data['Count']:.0f}")

def main():
    """
    Main function to run the 2024-25 hidden gems analysis
    """
    print("HIDDEN GEMS ANALYSIS - 2024-25 SEASON ONLY")
    print("Finding non-elite players who outperform their team average in 2024-25")
    print("="*80)
    
    # Get 2024-25 player data
    print("\\nFetching 2024-25 season data...")
    try:
        all_players_df = get_2024_25_player_data()
        print(f"✅ Found data for {len(all_players_df)} players in 2024-25 season")
    except Exception as e:
        print(f"❌ Error fetching 2024-25 data: {e}")
        print("\\nThis might be due to table access issues. The analysis requires:")
        print("1. Access to player_season_totals_corrected table")
        print("2. 2024-25 season data availability")
        print("3. Proper table permissions")
        return
    
    # Find hidden gems
    print("\\nIdentifying hidden gems from 2024-25 season...")
    hidden_gems_df = find_hidden_gems_2024_25(all_players_df, top_n=25)
    
    print(f"✅ Found {len(hidden_gems_df)} hidden gems (non-elite players with positive team impact)")
    
    # Create visualizations
    print("\\nCreating 2024-25 hidden gems visualization...")
    create_hidden_gems_visualization_2024_25(hidden_gems_df)
    
    # Create detailed analysis
    create_detailed_hidden_gems_table_2024_25(hidden_gems_df)
    
    # Team context analysis
    create_team_context_analysis_2024_25(hidden_gems_df)
    
    # Position analysis
    create_position_analysis_2024_25(hidden_gems_df)
    
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
