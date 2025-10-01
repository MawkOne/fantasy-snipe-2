#!/usr/bin/env python3
"""
Team Roster Analysis for New Oilers Nation

This script analyzes the current roster of New Oilers Nation and provides
recommendations for improvements based on league scoring and roster requirements.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def load_roster_data(file_path: str) -> pd.DataFrame:
    """Load the projections data and filter for New Oilers Nation."""
    
    # Read the CSV file
    df = pd.read_csv(file_path, skiprows=1)  # Skip the header row
    
    # Filter for New Oilers Nation
    team_df = df[df['Avail'] == 'New Oilers Nation'].copy()
    
    return team_df

def analyze_roster_structure(team_df: pd.DataFrame) -> Dict:
    """Analyze the current roster structure and identify gaps."""
    
    # Position information should already be parsed
    
    # Count positions
    position_counts = team_df['Position_Group'].value_counts()
    
    # League requirements
    requirements = {
        'Goalies': 2,
        'Centers': 2,
        'Wings': 3,
        'Forwards (C or W)': 4,
        'Defense': 4
    }
    
    # Current counts
    current_counts = {
        'Goalies': 0,  # No goalies in the data
        'Centers': position_counts.get('Center', 0),
        'Wings': position_counts.get('Wing', 0),
        'Forwards (C or W)': position_counts.get('Center', 0) + position_counts.get('Wing', 0),
        'Defense': position_counts.get('Defense', 0)
    }
    
    # Calculate gaps
    gaps = {}
    for pos, required in requirements.items():
        current = current_counts[pos]
        gaps[pos] = max(0, required - current)
    
    return {
        'position_counts': position_counts,
        'current_counts': current_counts,
        'requirements': requirements,
        'gaps': gaps,
        'total_players': len(team_df)
    }

def calculate_fantasy_points(team_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate fantasy points based on league scoring system."""
    
    # League scoring (from League_format.md):
    # G - Goals: 3
    # A - Assists: 2  
    # +/- - Plus Minus: 0.25
    # SHG - Short Handed Goals: 2 (bonus)
    # SHOG – Shootout Goals: 1
    # PIM - Penalty Minutes: 0
    # DA - Defenseman Assists: 1 (bonus)
    # DG - Defenseman Goals: 2 (bonus)
    
    team_df = team_df.copy()
    
    # Basic scoring
    team_df['FPTS_Goals'] = team_df['G'] * 3
    team_df['FPTS_Assists'] = team_df['A'] * 2
    team_df['FPTS_PlusMinus'] = team_df['+/-'] * 0.25
    team_df['FPTS_PIM'] = team_df['PIM'] * 0
    team_df['FPTS_SHG'] = team_df['SHG'] * 2
    # Note: SHOG column doesn't exist in this data, so we'll skip it
    team_df['FPTS_SHOG'] = 0
    
    # Defenseman bonuses
    team_df['FPTS_DA'] = np.where(team_df['Position'] == 'D', team_df['A'] * 1, 0)
    team_df['FPTS_DG'] = np.where(team_df['Position'] == 'D', team_df['G'] * 2, 0)
    
    # Total fantasy points
    team_df['Total_FPTS'] = (
        team_df['FPTS_Goals'] + 
        team_df['FPTS_Assists'] + 
        team_df['FPTS_PlusMinus'] + 
        team_df['FPTS_PIM'] + 
        team_df['FPTS_SHG'] + 
        team_df['FPTS_SHOG'] + 
        team_df['FPTS_DA'] + 
        team_df['FPTS_DG']
    )
    
    return team_df

def analyze_team_strengths_weaknesses(team_df: pd.DataFrame) -> Dict:
    """Analyze team strengths and weaknesses."""
    
    # Calculate per-game averages
    team_df['FPTS_per_game'] = team_df['Total_FPTS'] / team_df['GP']
    team_df['PTS_per_game'] = team_df['PTS'] / team_df['GP']
    
    # Position analysis
    position_analysis = {}
    for pos in ['Center', 'Wing', 'Defense']:
        pos_players = team_df[team_df['Position_Group'] == pos]
        if len(pos_players) > 0:
            position_analysis[pos] = {
                'count': len(pos_players),
                'avg_fpts': pos_players['Total_FPTS'].mean(),
                'avg_pts': pos_players['PTS'].mean(),
                'top_player': pos_players.loc[pos_players['Total_FPTS'].idxmax(), 'Player'],
                'top_fpts': pos_players['Total_FPTS'].max()
            }
    
    # Overall team stats
    team_stats = {
        'total_fpts': team_df['Total_FPTS'].sum(),
        'avg_fpts_per_player': team_df['Total_FPTS'].mean(),
        'top_scorer': team_df.loc[team_df['Total_FPTS'].idxmax(), 'Player'],
        'top_fpts': team_df['Total_FPTS'].max(),
        'depth_players': len(team_df[team_df['Total_FPTS'] > team_df['Total_FPTS'].median()])
    }
    
    return {
        'position_analysis': position_analysis,
        'team_stats': team_stats
    }

def identify_improvement_areas(team_df: pd.DataFrame, analysis: Dict) -> List[str]:
    """Identify areas for improvement."""
    
    recommendations = []
    
    # Check roster requirements
    gaps = analysis['gaps']
    for pos, gap in gaps.items():
        if gap > 0:
            recommendations.append(f"Need {gap} more {pos}")
    
    # Check for goalies
    if gaps['Goalies'] > 0:
        recommendations.append("URGENT: Need 2 goalies - this is a minimum requirement!")
    
    # Check position depth
    position_analysis = analysis['position_analysis']
    
    # Check defense depth
    if 'Defense' in position_analysis:
        def_count = position_analysis['Defense']['count']
        if def_count < 4:
            recommendations.append(f"Defense depth: Only {def_count}/4 required defensemen")
    
    # Check forward depth
    total_forwards = analysis['current_counts']['Forwards (C or W)']
    if total_forwards < 9:  # 2C + 3W + 4F
        recommendations.append(f"Forward depth: Only {total_forwards}/9 required forwards")
    
    # Check for elite talent
    top_fpts = analysis['team_stats']['top_fpts']
    if top_fpts < 250:
        recommendations.append("Consider adding more elite talent - top scorer under 250 FPTS")
    
    return recommendations

def main():
    print("🏒 New Oilers Nation Roster Analysis")
    print("=" * 50)
    
    # Load roster data
    team_df = load_roster_data('/Users/markhenderson/Cursor Projects/NHL-API/docs/projections.csv')
    
    if len(team_df) == 0:
        print("No players found for New Oilers Nation")
        return
    
    print(f"Current Roster: {len(team_df)} players")
    print()
    
    # Parse position information first
    team_df['Position'] = team_df['Player'].str.extract(r'([CDW]) \|')
    team_df['NHL_Team'] = team_df['Player'].str.extract(r'\| ([A-Z]+)')
    team_df['Position_Group'] = team_df['Position'].map({
        'C': 'Center',
        'W': 'Wing', 
        'D': 'Defense'
    })
    
    # Calculate fantasy points
    team_df = calculate_fantasy_points(team_df)
    
    # Analyze roster structure
    analysis = analyze_roster_structure(team_df)
    
    # Analyze strengths and weaknesses
    strengths_weaknesses = analyze_team_strengths_weaknesses(team_df)
    
    # Combine analysis
    analysis['position_analysis'] = strengths_weaknesses['position_analysis']
    analysis['team_stats'] = strengths_weaknesses['team_stats']
    
    # Print roster structure
    print("📊 Roster Structure:")
    print("-" * 30)
    for pos, count in analysis['position_counts'].items():
        print(f"{pos}: {count}")
    print(f"Total: {analysis['total_players']}")
    print()
    
    # Print requirements vs current
    print("📋 Requirements vs Current:")
    print("-" * 30)
    for pos, required in analysis['requirements'].items():
        current = analysis['current_counts'][pos]
        gap = analysis['gaps'][pos]
        status = "✅" if gap == 0 else "❌"
        print(f"{pos}: {current}/{required} {status}")
        if gap > 0:
            print(f"  Missing: {gap}")
    print()
    
    # Print position analysis
    print("🎯 Position Analysis:")
    print("-" * 30)
    for pos, stats in strengths_weaknesses['position_analysis'].items():
        print(f"\n{pos} ({stats['count']} players):")
        print(f"  Avg FPTS: {stats['avg_fpts']:.1f}")
        print(f"  Avg PTS: {stats['avg_pts']:.1f}")
        print(f"  Top Player: {stats['top_player']} ({stats['top_fpts']:.1f} FPTS)")
    
    # Print team stats
    print(f"\n🏆 Team Stats:")
    print("-" * 30)
    team_stats = strengths_weaknesses['team_stats']
    print(f"Total Fantasy Points: {team_stats['total_fpts']:.1f}")
    print(f"Average per Player: {team_stats['avg_fpts_per_player']:.1f}")
    print(f"Top Scorer: {team_stats['top_scorer']} ({team_stats['top_fpts']:.1f} FPTS)")
    print(f"Depth Players: {team_stats['depth_players']}")
    
    # Identify improvement areas
    recommendations = identify_improvement_areas(team_df, analysis)
    
    print(f"\n💡 Recommendations:")
    print("-" * 30)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Print top players by position
    print(f"\n⭐ Top Players by Position:")
    print("-" * 30)
    for pos in ['Center', 'Wing', 'Defense']:
        if pos in strengths_weaknesses['position_analysis']:
            pos_players = team_df[team_df['Position_Group'] == pos].nlargest(3, 'Total_FPTS')
            print(f"\n{pos}:")
            for _, player in pos_players.iterrows():
                print(f"  {player['Player']}: {player['Total_FPTS']:.1f} FPTS")
    
    print(f"\n📈 Complete Roster (sorted by Fantasy Points):")
    print("-" * 50)
    sorted_roster = team_df.sort_values('Total_FPTS', ascending=False)
    for _, player in sorted_roster.iterrows():
        print(f"{player['Player']:30s} | {player['Total_FPTS']:6.1f} FPTS | {player['PTS']:5.1f} PTS")

if __name__ == "__main__":
    main()
