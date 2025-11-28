#!/usr/bin/env python3
"""
Real Elite Player Impact Analysis
Using actual NHL data for McDavid, MacKinnon, Matthews, Draisaitl, and Hughes
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import numpy as np

def get_elite_player_data() -> pd.DataFrame:
    """
    Get real data for elite players using available tables
    """
    client = bigquery.Client()
    
    # Use the data we know works - from our projections
    query = """
    WITH elite_players AS (
        SELECT 
            player_name,
            team_abbr,
            position_type,
            toi_tier,
            age,
            cf_pct,
            gf60,
            ga60,
            gf60 - ga60 as goal_diff_60,
            pts60,
            points
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected`
        WHERE player_name IN ('Connor McDavid', 'Nathan MacKinnon', 'Auston Matthews', 'Leon Draisaitl', 'Quinn Hughes')
    ),
    
    team_averages AS (
        SELECT 
            team_abbr,
            AVG(gf60 - ga60) as team_avg_goal_diff_60,
            AVG(gf60) as team_avg_gf60,
            AVG(ga60) as team_avg_ga60,
            AVG(cf_pct) as team_avg_cf_pct
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected`
        WHERE toi_tier IN ('Elite', 'Top Line', 'Middle 6')
        GROUP BY team_abbr
    )
    
    SELECT 
        ep.player_name,
        ep.team_abbr,
        ep.position_type,
        ep.toi_tier,
        ep.age,
        ep.goal_diff_60 as player_goal_diff_60,
        ep.gf60 as player_gf60,
        ep.ga60 as player_ga60,
        ep.cf_pct as player_cf_pct,
        ep.pts60,
        ep.points,
        ta.team_avg_goal_diff_60,
        ta.team_avg_gf60,
        ta.team_avg_ga60,
        ta.team_avg_cf_pct,
        -- Calculate impact vs team average
        ep.goal_diff_60 - ta.team_avg_goal_diff_60 as impact_vs_team_60
    FROM elite_players ep
    JOIN team_averages ta ON ep.team_abbr = ta.team_abbr
    ORDER BY ep.goal_diff_60 DESC
    """
    
    return client.query(query).to_dataframe()

def create_elite_comparison_visualization(df: pd.DataFrame) -> None:
    """
    Create the elite player comparison visualization with real data
    """
    if df.empty:
        print("No data found for elite players")
        return
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Player Goal Differential vs Team Average
    players = df['player_name']
    player_goal_diff = df['player_goal_diff_60']
    team_avg_goal_diff = df['team_avg_goal_diff_60']
    
    x = np.arange(len(players))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, player_goal_diff, width, 
                    label='Player Goal Diff/60', alpha=0.7, color='green')
    bars2 = ax1.bar(x + width/2, team_avg_goal_diff, width, 
                    label='Team Average Goal Diff/60', alpha=0.7, color='blue')
    
    ax1.set_xlabel('Player')
    ax1.set_ylabel('Goal Differential per 60 Minutes')
    ax1.set_title('Elite Player Impact Analysis - 2025-26 Projections\\nPlayer Performance vs Team Average')
    ax1.set_xticks(x)
    ax1.set_xticklabels(players, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
                    f'{height:.1f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)
    
    # Plot 2: Player Impact vs Team Average
    impact_vs_team = df['impact_vs_team_60']
    
    bars3 = ax2.bar(players, impact_vs_team, alpha=0.7, color='purple', 
                    label='Impact vs Team Average')
    
    ax2.set_xlabel('Player')
    ax2.set_ylabel('Impact per 60 Minutes')
    ax2.set_title('Elite Player Impact - Above Team Average Performance')
    ax2.set_xticklabels(players, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Color bars based on positive/negative impact
    for i, bar in enumerate(bars3):
        if impact_vs_team.iloc[i] > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')
    
    # Add value labels
    for i, impact in enumerate(impact_vs_team):
        ax2.text(i, impact + (0.1 if impact >= 0 else -0.1), f'{impact:.1f}', 
                ha='center', va='bottom' if impact >= 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.show()

def create_detailed_comparison_table(df: pd.DataFrame) -> None:
    """
    Create a detailed comparison table
    """
    if df.empty:
        print("No data found for elite players")
        return
    
    print("\\n" + "="*100)
    print("ELITE PLAYER IMPACT ANALYSIS - 2025-26 PROJECTIONS")
    print("="*100)
    
    # Create comparison table
    comparison_data = []
    for _, row in df.iterrows():
        comparison_data.append({
            'Player': row['player_name'],
            'Team': row['team_abbr'],
            'Position': row['position_type'],
            'Age': row['age'],
            'Player Goal Diff/60': f"{row['player_goal_diff_60']:.2f}",
            'Team Avg Goal Diff/60': f"{row['team_avg_goal_diff_60']:.2f}",
            'Impact vs Team': f"{row['impact_vs_team_60']:.2f}",
            'Player GF/60': f"{row['player_gf60']:.2f}",
            'Player GA/60': f"{row['player_ga60']:.2f}",
            'Player CF%': f"{row['player_cf_pct']:.1f}%",
            'Pts/60': f"{row['pts60']:.2f}",
            'Total Points': f"{row['points']:.0f}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*100)
    print("KEY INSIGHTS")
    print("="*100)
    
    # Find highest impact player
    highest_impact = df.loc[df['impact_vs_team_60'].idxmax()]
    print(f"\\n🏆 HIGHEST IMPACT: {highest_impact['player_name']} ({highest_impact['team_abbr']})")
    print(f"   Impact vs Team: +{highest_impact['impact_vs_team_60']:.2f} Goal Diff/60")
    print(f"   Player Performance: {highest_impact['player_goal_diff_60']:.2f} Goal Diff/60")
    print(f"   Team Average: {highest_impact['team_avg_goal_diff_60']:.2f} Goal Diff/60")
    
    # Find most efficient scorer
    highest_pts60 = df.loc[df['pts60'].idxmax()]
    print(f"\\n⚡ HIGHEST PTS/60: {highest_pts60['player_name']} ({highest_pts60['team_abbr']})")
    print(f"   Points per 60: {highest_pts60['pts60']:.2f}")
    print(f"   Total Points: {highest_pts60['points']:.0f}")
    
    # Find best possession player
    highest_cf = df.loc[df['player_cf_pct'].idxmax()]
    print(f"\\n🎯 BEST POSSESSION: {highest_cf['player_name']} ({highest_cf['team_abbr']})")
    print(f"   CF%: {highest_cf['player_cf_pct']:.1f}%")
    print(f"   Goal Diff/60: {highest_cf['player_goal_diff_60']:.2f}")
    
    # Team context analysis
    print(f"\\n📊 TEAM CONTEXT:")
    for _, row in df.iterrows():
        team_strength = "Strong" if row['team_avg_goal_diff_60'] > 0.5 else "Average" if row['team_avg_goal_diff_60'] > 0 else "Weak"
        print(f"   {row['team_abbr']}: {team_strength} team ({row['team_avg_goal_diff_60']:.2f} Goal Diff/60)")

def create_team_context_analysis(df: pd.DataFrame) -> None:
    """
    Create team context analysis
    """
    if df.empty:
        return
    
    # Group by team to show team context
    team_analysis = df.groupby('team_abbr').agg({
        'player_goal_diff_60': 'mean',
        'team_avg_goal_diff_60': 'first',
        'impact_vs_team_60': 'mean',
        'player_name': 'count'
    }).round(2)
    
    team_analysis.columns = ['Avg Player Goal Diff/60', 'Team Avg Goal Diff/60', 'Avg Impact vs Team', 'Elite Players']
    
    print("\\n" + "="*80)
    print("TEAM CONTEXT ANALYSIS")
    print("="*80)
    print(team_analysis.to_string())
    
    # Insights about team strength
    print("\\n📈 TEAM STRENGTH INSIGHTS:")
    for team, row in team_analysis.iterrows():
        if row['Team Avg Goal Diff/60'] > 1.0:
            strength = "Elite"
        elif row['Team Avg Goal Diff/60'] > 0.5:
            strength = "Strong"
        elif row['Team Avg Goal Diff/60'] > 0:
            strength = "Average"
        else:
            strength = "Weak"
        
        print(f"   {team}: {strength} team with {row['Elite Players']:.0f} elite players")

def main():
    """
    Main function to run the real elite player impact analysis
    """
    print("ELITE PLAYER IMPACT ANALYSIS - REAL DATA")
    print("Analyzing: McDavid, MacKinnon, Matthews, Draisaitl, Hughes")
    print("="*80)
    
    # Get real data
    print("\\nFetching real player data...")
    df = get_elite_player_data()
    
    if df.empty:
        print("❌ No data found. This might be due to table access issues.")
        print("\\nAvailable alternatives:")
        print("1. Check table permissions")
        print("2. Use different data source")
        print("3. Run with mock data for demonstration")
        return
    
    print(f"✅ Found data for {len(df)} elite players")
    
    # Create visualizations
    print("\\nCreating elite player comparison visualization...")
    create_elite_comparison_visualization(df)
    
    # Create detailed analysis
    create_detailed_comparison_table(df)
    
    # Team context analysis
    create_team_context_analysis(df)
    
    print("\\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis analysis shows real 2025-26 projected data for elite NHL players.")
    print("The impact metrics reveal how much each player contributes above their team's average performance.")

if __name__ == "__main__":
    main()
