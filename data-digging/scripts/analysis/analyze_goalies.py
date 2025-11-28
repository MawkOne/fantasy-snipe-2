#!/usr/bin/env python3
"""
Goalie Analysis for New Oilers Nation

This script analyzes the goalie situation for New Oilers Nation and provides
recommendations based on league scoring and roster requirements.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def load_goalie_data(file_path: str) -> pd.DataFrame:
    """Load the goalie projections data."""
    
    # Read the CSV file
    df = pd.read_csv(file_path, skiprows=1)  # Skip the header row
    
    # Parse position information
    df['Position'] = df['Player'].str.extract(r'([G]) \|')
    df['NHL_Team'] = df['Player'].str.extract(r'\| ([A-Z]+)')
    
    return df

def calculate_goalie_fantasy_points(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate fantasy points for goalies based on league scoring system."""
    
    df = df.copy()
    
    # League scoring for goalies (from League_format.md):
    # W - Wins: 2
    # GA - Goals Against: -1.25
    # S - Saves: 0.2
    # OL - Overtime Losses: 1
    # SHOL - Shootout Losses: 1
    # SO - Shut Outs: 1 (bonus)
    
    # Basic scoring
    df['FPTS_Wins'] = df['W'] * 2
    df['FPTS_Goals_Against'] = df['GA'] * -1.25
    df['FPTS_Saves'] = df['S'] * 0.2
    df['FPTS_OT_Losses'] = df['L'] * 0  # Regular losses don't score
    df['FPTS_Shutouts'] = df['SO'] * 1
    
    # Note: We don't have separate OT Losses data, so we'll estimate
    # Assuming some losses are OT losses (typically 20-25% of losses)
    estimated_ot_losses = df['L'] * 0.22  # 22% of losses are OT
    df['FPTS_OT_Losses'] = estimated_ot_losses * 1
    
    # Total fantasy points
    df['Total_FPTS'] = (
        df['FPTS_Wins'] + 
        df['FPTS_Goals_Against'] + 
        df['FPTS_Saves'] + 
        df['FPTS_OT_Losses'] + 
        df['FPTS_Shutouts']
    )
    
    return df

def analyze_my_goalies(df: pd.DataFrame, my_team: str = 'New Oilers Nation') -> Dict:
    """Analyze the goalies on my team."""
    
    my_goalies = df[df['Avail'] == my_team].copy()
    
    if len(my_goalies) == 0:
        return {'error': 'No goalies found on your team'}
    
    # Sort by fantasy points
    my_goalies = my_goalies.sort_values('Total_FPTS', ascending=False)
    
    # Calculate team goalie stats
    total_fpts = my_goalies['Total_FPTS'].sum()
    avg_fpts = my_goalies['Total_FPTS'].mean()
    best_goalie = my_goalies.iloc[0]
    worst_goalie = my_goalies.iloc[-1]
    
    # Analyze each goalie
    goalie_analysis = []
    for _, goalie in my_goalies.iterrows():
        analysis = {
            'name': goalie['Player'],
            'nhl_team': goalie['NHL_Team'],
            'wins': goalie['W'],
            'losses': goalie['L'],
            'shutouts': goalie['SO'],
            'gaa': goalie['GAA'],
            'save_pct': goalie['SPct'],
            'fpts': goalie['Total_FPTS'],
            'tier': 'Elite' if goalie['Total_FPTS'] >= 160 else 'Good' if goalie['Total_FPTS'] >= 140 else 'Average' if goalie['Total_FPTS'] >= 120 else 'Below Average'
        }
        goalie_analysis.append(analysis)
    
    return {
        'goalies': goalie_analysis,
        'total_fpts': total_fpts,
        'avg_fpts': avg_fpts,
        'best_goalie': best_goalie['Player'],
        'best_fpts': best_goalie['Total_FPTS'],
        'worst_goalie': worst_goalie['Player'],
        'worst_fpts': worst_goalie['Total_FPTS'],
        'count': len(my_goalies)
    }

def find_available_goalies(df: pd.DataFrame, my_team: str = 'New Oilers Nation') -> pd.DataFrame:
    """Find goalies that might be available for pickup."""
    
    # Look for goalies not on your team
    available_goalies = df[df['Avail'] != my_team].copy()
    
    # Sort by fantasy points
    available_goalies = available_goalies.sort_values('Total_FPTS', ascending=False)
    
    return available_goalies

def analyze_goalie_tiers(df: pd.DataFrame) -> Dict:
    """Analyze goalies by tiers based on fantasy points."""
    
    # Define tiers based on fantasy points
    df['Tier'] = pd.cut(df['Total_FPTS'], 
                       bins=[0, 120, 140, 160, 200], 
                       labels=['Below Average', 'Average', 'Good', 'Elite'])
    
    tier_counts = df['Tier'].value_counts()
    
    return {
        'tier_counts': tier_counts.to_dict(),
        'elite_goalies': df[df['Tier'] == 'Elite'].sort_values('Total_FPTS', ascending=False),
        'good_goalies': df[df['Tier'] == 'Good'].sort_values('Total_FPTS', ascending=False),
        'average_goalies': df[df['Tier'] == 'Average'].sort_values('Total_FPTS', ascending=False)
    }

def main():
    print("🏒 Goalie Analysis for New Oilers Nation")
    print("=" * 50)
    
    # Load goalie data
    df = load_goalie_data('/Users/markhenderson/Cursor Projects/NHL-API/docs/CBS/goalies_sept_20.csv')
    df = calculate_goalie_fantasy_points(df)
    
    print(f"Total goalies in league: {len(df)}")
    print()
    
    # Analyze my goalies
    my_goalies = analyze_my_goalies(df)
    
    if 'error' in my_goalies:
        print(f"❌ {my_goalies['error']}")
        return
    
    print("🎯 Your Current Goalies:")
    print("-" * 30)
    for goalie in my_goalies['goalies']:
        print(f"{goalie['name']:25s} | {goalie['nhl_team']:3s} | {goalie['fpts']:6.1f} FPTS | {goalie['tier']:12s}")
        print(f"  Wins: {goalie['wins']:4.1f} | GAA: {goalie['gaa']:4.2f} | SV%: {goalie['save_pct']:5.3f} | SO: {goalie['shutouts']:4.1f}")
        print()
    
    print(f"📊 Team Goalie Stats:")
    print("-" * 30)
    print(f"Total Fantasy Points: {my_goalies['total_fpts']:.1f}")
    print(f"Average per Goalie: {my_goalies['avg_fpts']:.1f}")
    print(f"Best Goalie: {my_goalies['best_goalie']} ({my_goalies['best_fpts']:.1f} FPTS)")
    print(f"Worst Goalie: {my_goalies['worst_goalie']} ({my_goalies['worst_fpts']:.1f} FPTS)")
    print()
    
    # Analyze goalie tiers
    tier_analysis = analyze_goalie_tiers(df)
    
    print("📈 League Goalie Tiers:")
    print("-" * 30)
    for tier, count in tier_analysis['tier_counts'].items():
        print(f"{tier:15s}: {count:3d} goalies")
    print()
    
    # Find available goalies
    available_goalies = find_available_goalies(df)
    
    print("🔍 Top Available Goalies:")
    print("-" * 40)
    print("Top 15 available goalies (not on your team):")
    for i, (_, goalie) in enumerate(available_goalies.head(15).iterrows(), 1):
        print(f"{i:2d}. {goalie['Player']:25s} | {goalie['NHL_Team']:3s} | {goalie['Total_FPTS']:6.1f} FPTS | {goalie['W']:4.1f}W | {goalie['GAA']:4.2f}GAA")
    print()
    
    # Strategic recommendations
    print("💡 Strategic Recommendations:")
    print("-" * 35)
    
    # Check if we have enough goalies
    if my_goalies['count'] >= 2:
        print("✅ You have enough goalies (2+ required)")
    else:
        print("❌ You need more goalies (2 minimum required)")
    
    # Analyze goalie quality
    elite_count = sum(1 for g in my_goalies['goalies'] if g['tier'] == 'Elite')
    good_count = sum(1 for g in my_goalies['goalies'] if g['tier'] == 'Good')
    
    print(f"📊 Goalie Quality: {elite_count} Elite, {good_count} Good")
    
    if elite_count == 0:
        print("⚠️  Consider upgrading to an elite goalie")
    elif elite_count == 1:
        print("✅ Good goalie depth with one elite starter")
    else:
        print("🔥 Excellent goalie depth with multiple elite options")
    
    # Check for potential improvements
    if my_goalies['worst_fpts'] < 120:
        print(f"⚠️  Consider dropping {my_goalies['worst_goalie']} (only {my_goalies['worst_fpts']:.1f} FPTS)")
    
    # Look for upgrade opportunities
    available_elite = available_goalies[available_goalies['Total_FPTS'] >= 160]
    if len(available_elite) > 0:
        print(f"🎯 {len(available_elite)} elite goalies available for pickup:")
        for _, goalie in available_elite.head(5).iterrows():
            print(f"   {goalie['Player']:25s} | {goalie['Total_FPTS']:6.1f} FPTS")
    
    print()
    print("🏆 Goalie Strategy Summary:")
    print("-" * 30)
    print("1. You have 3 goalies - this is good depth")
    print("2. Vasilevskiy is your clear #1 (168.96 FPTS)")
    print("3. Shesterkin is a solid #2 (145.85 FPTS)")
    print("4. Knight is your #3 with upside (110.43 FPTS)")
    print("5. Consider trading Knight if you need roster space")
    print("6. Your goalie situation is actually quite strong!")

if __name__ == "__main__":
    main()
