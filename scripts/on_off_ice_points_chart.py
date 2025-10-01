#!/usr/bin/env python3
"""
On-Ice vs Off-Ice Points Chart - 2024-25 Season
Visualizing the difference between team points when player is on ice vs off ice
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Tuple, Optional

def get_game_level_data(team_abbr: str) -> pd.DataFrame:
    """
    Get game-level data for a specific team
    """
    client = bigquery.Client()
    
    # Query to get game-level data
    query = f"""
    WITH team_games AS (
        SELECT 
            g.id as game_id,
            g.season,
            g.game_date,
            CASE 
                WHEN g.home_team_id = t.id THEN 'home'
                ELSE 'away'
            END as home_away,
            CASE 
                WHEN g.home_team_id = t.id THEN g.home_score
                ELSE g.away_score
            END as team_score,
            CASE 
                WHEN g.home_team_id = t.id THEN g.away_score
                ELSE g.home_score
            END as opponent_score,
            CASE 
                WHEN g.home_team_id = t.id THEN g.home_score - g.away_score
                ELSE g.away_score - g.home_score
            END as goal_differential
        FROM `fantasy-snipe-ai.nhl_raw.games` g
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON (g.home_team_id = t.id OR g.away_team_id = t.id)
        WHERE t.tri_code = '{team_abbr}'
        AND g.season = 20242025
        AND g.game_type = 2
    ),
    
    player_games AS (
        SELECT 
            pgs.player_id,
            p.full_name,
            p.position,
            pgs.game_id,
            pgs.goals,
            pgs.assists,
            pgs.points,
            pgs.plus_minus,
            pgs.shots,
            pgs.shifts,
            tg.team_score,
            tg.opponent_score,
            tg.goal_differential
        FROM `fantasy-snipe-ai.nhl_raw.player_game_stats` pgs
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pgs.player_id = p.player_id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pgs.team_id = t.id
        JOIN team_games tg ON pgs.game_id = tg.game_id
        WHERE t.tri_code = '{team_abbr}'
        AND p.position != 'G'
    ),
    
    player_totals AS (
        SELECT 
            player_id,
            full_name,
            position,
            COUNT(*) as games_played,
            SUM(goals) as total_goals,
            SUM(assists) as total_assists,
            SUM(points) as total_points,
            SUM(plus_minus) as total_plus_minus,
            SUM(shots) as total_shots,
            SUM(shifts) as total_shifts,
            -- Calculate team performance when this player played
            SUM(team_score) as total_team_score_with_player,
            SUM(opponent_score) as total_opponent_score_with_player,
            SUM(goal_differential) as total_goal_differential_with_player,
            AVG(team_score) as avg_team_score_with_player,
            AVG(opponent_score) as avg_opponent_score_with_player,
            AVG(goal_differential) as avg_goal_differential_with_player
        FROM player_games
        GROUP BY player_id, full_name, position
    ),
    
    team_totals AS (
        SELECT 
            COUNT(DISTINCT game_id) as total_games,
            SUM(team_score) as total_team_score,
            SUM(opponent_score) as total_opponent_score,
            SUM(goal_differential) as total_goal_differential,
            AVG(team_score) as avg_team_score,
            AVG(opponent_score) as avg_opponent_score,
            AVG(goal_differential) as avg_goal_differential
        FROM team_games
    )
    
    SELECT 
        pt.*,
        tt.total_games,
        tt.total_team_score,
        tt.total_opponent_score,
        tt.total_goal_differential,
        tt.avg_team_score,
        tt.avg_opponent_score,
        tt.avg_goal_differential
    FROM player_totals pt
    CROSS JOIN team_totals tt
    WHERE pt.games_played >= 20  -- At least 20 games played
    ORDER BY pt.total_plus_minus DESC
    """
    
    return client.query(query).to_dataframe()

def create_on_off_ice_points_chart(df: pd.DataFrame, team_name: str) -> None:
    """
    Create the insightful on-ice vs off-ice points chart
    """
    # Calculate the metrics
    df = df.copy()
    
    # Calculate total points impact vs team total
    df['total_team_score_impact'] = df['total_team_score_with_player'] - (df['total_team_score'] * df['games_played'] / df['total_games'])
    df['total_opponent_score_impact'] = df['total_opponent_score_with_player'] - (df['total_opponent_score'] * df['games_played'] / df['total_games'])
    df['total_goal_differential_impact'] = df['total_goal_differential_with_player'] - (df['total_goal_differential'] * df['games_played'] / df['total_games'])
    
    # Calculate per-game impact vs team average
    df['team_score_impact'] = df['avg_team_score_with_player'] - df['avg_team_score']
    df['opponent_score_impact'] = df['avg_opponent_score_with_player'] - df['avg_opponent_score']
    df['goal_differential_impact'] = df['avg_goal_differential_with_player'] - df['avg_goal_differential']
    
    # Calculate games percentage
    df['games_percentage'] = (df['games_played'] / df['total_games']) * 100
    
    # Create the main chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
    
    # Chart 1: Team Points When Player On-Ice vs Team Average Off-Ice
    players = df['full_name']
    team_on_ice_points = df['total_team_score_with_player']  # Team points when this player was in lineup
    team_off_ice_avg = df['total_team_score'] * df['games_played'] / df['total_games']  # Expected team points based on average
    
    # Color by position
    position_colors = {
        'C': 'red',
        'L': 'blue', 
        'R': 'green',
        'D': 'orange'
    }
    colors = [position_colors.get(pos, 'gray') for pos in df['position']]
    
    x = np.arange(len(players))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, team_on_ice_points, width, label='Team Points (when player in lineup)', 
                    color=colors, alpha=0.7)
    bars2 = ax1.bar(x + width/2, team_off_ice_avg, width, label='Team Average Points (expected)', 
                    color='lightcoral', alpha=0.7)
    
    ax1.set_xlabel('Players')
    ax1.set_ylabel('Total Team Points')
    ax1.set_title(f'{team_name}: Team Points On-Ice vs Off-Ice Average\\n2024-25 Season')
    ax1.set_xticks(x)
    ax1.set_xticklabels(players, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        # Team on-ice points
        height1 = bar1.get_height()
        ax1.text(bar1.get_x() + bar1.get_width()/2., height1 + 1,
                f'{height1:.0f}', ha='center', va='bottom', fontsize=8)
        
        # Team off-ice average
        height2 = bar2.get_height()
        ax1.text(bar2.get_x() + bar2.get_width()/2., height2 + 1,
                f'{height2:.0f}', ha='center', va='bottom', fontsize=8)
    
    # Add position legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='red', label='Center'),
                      Patch(facecolor='blue', label='Left Wing'),
                      Patch(facecolor='green', label='Right Wing'),
                      Patch(facecolor='orange', label='Defenseman')]
    ax1.legend(handles=legend_elements, loc='upper right')
    
    # Chart 2: Team Points Impact
    team_points_impact = df['total_team_score_impact']
    colors_impact = ['green' if x > 0 else 'red' for x in team_points_impact]
    
    bars3 = ax2.barh(range(len(players)), team_points_impact, color=colors_impact, alpha=0.7)
    
    ax2.set_yticks(range(len(players)))
    ax2.set_yticklabels(players)
    ax2.set_xlabel('Team Points Impact')
    ax2.set_title(f'{team_name}: Team Points Impact\\nPositive = Team scored more when player in lineup')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars3):
        width = bar.get_width()
        ax2.text(width + (1 if width >= 0 else -1), bar.get_y() + bar.get_height()/2,
                f'{width:+.0f}', ha='left' if width >= 0 else 'right', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Print detailed analysis
    print("\\n" + "="*120)
    print(f"{team_name.upper()} ON-ICE vs OFF-ICE POINTS ANALYSIS")
    print("="*120)
    
    # Create detailed table
    detailed_data = []
    for _, row in df.iterrows():
        detailed_data.append({
            'Player': row['full_name'],
            'Position': row['position'],
            'Games': f"{row['games_played']:.0f}",
            'Team Points (On-Ice)': f"{row['total_team_score_with_player']:.0f}",
            'Team Points (Expected)': f"{row['total_team_score'] * row['games_played'] / row['total_games']:.0f}",
            'Team Points Impact': f"{row['total_team_score_impact']:+.0f}",
            'Player Individual Points': f"{row['total_points']:.0f}",
            'Plus/Minus': f"{row['total_plus_minus']:+.0f}"
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    print(detailed_df.to_string(index=False))
    
    # Key insights
    print("\\n" + "="*120)
    print("KEY INSIGHTS")
    print("="*120)
    
    # Find highest team impact players
    highest_positive = df.loc[df['total_team_score_impact'].idxmax()]
    highest_negative = df.loc[df['total_team_score_impact'].idxmin()]
    
    print(f"\\n🏆 HIGHEST POSITIVE TEAM IMPACT: {highest_positive['full_name']}")
    print(f"   Team Points (On-Ice): {highest_positive['total_team_score_with_player']:.0f}")
    print(f"   Team Points (Expected): {highest_positive['total_team_score'] * highest_positive['games_played'] / highest_positive['total_games']:.0f}")
    print(f"   Team Points Impact: {highest_positive['total_team_score_impact']:+.0f}")
    
    print(f"\\n⚠️ HIGHEST NEGATIVE TEAM IMPACT: {highest_negative['full_name']}")
    print(f"   Team Points (On-Ice): {highest_negative['total_team_score_with_player']:.0f}")
    print(f"   Team Points (Expected): {highest_negative['total_team_score'] * highest_negative['games_played'] / highest_negative['total_games']:.0f}")
    print(f"   Team Points Impact: {highest_negative['total_team_score_impact']:+.0f}")
    
    # Team totals
    print(f"\\n📊 TEAM TOTALS: {df['total_team_score'].iloc[0]:.0f} total points in {df['total_games'].iloc[0]:.0f} games")
    
    # Position analysis
    position_analysis = df.groupby('position')['total_team_score_impact'].agg(['mean', 'count']).round(0)
    print(f"\\n📈 POSITION ANALYSIS:")
    for pos in ['C', 'L', 'R', 'D']:
        if pos in position_analysis.index:
            pos_data = position_analysis.loc[pos]
            print(f"   {pos}: Average Team Impact {pos_data['mean']:+.0f} points ({pos_data['count']:.0f} players)")

def analyze_team(team_abbr: str, team_name: str) -> None:
    """
    Analyze a specific team's on-ice vs off-ice points
    """
    print(f"{team_name.upper()} ON-ICE vs OFF-ICE POINTS ANALYSIS - 2024-25 SEASON")
    print("Showing the difference between team points when player is on ice vs off ice")
    print("="*80)
    
    # Get game-level data
    print(f"\\nFetching {team_name} game-level data...")
    try:
        game_df = get_game_level_data(team_abbr)
        print(f"✅ Found game data for {len(game_df)} {team_name} players")
    except Exception as e:
        print(f"❌ Error fetching {team_name} game data: {e}")
        return
    
    # Create the insightful chart
    print(f"\\nCreating {team_name} on-ice vs off-ice points chart...")
    create_on_off_ice_points_chart(game_df, team_name)
    
    print("\\n" + "="*80)
    print(f"{team_name.upper()} ANALYSIS COMPLETE")
    print("="*80)
    print("\\nThis chart shows team performance with vs without each player:")
    print("- Team Points (On-Ice): Total points team scored when this player was in the lineup")
    print("- Team Points (Expected): What team should have scored based on their average")
    print("- Team Points Impact: How many more/fewer points team scored with this player")
    print("\\nKey Insights:")
    print("- Positive impact = Team scored more total points when this player was in lineup")
    print("- Negative impact = Team scored fewer total points when this player was in lineup")
    print("- This reveals true team value beyond individual statistics")

def main():
    """
    Main function to run on-ice vs off-ice points analysis
    """
    # Analyze Edmonton Oilers
    analyze_team('EDM', 'Edmonton Oilers')

if __name__ == "__main__":
    main()
