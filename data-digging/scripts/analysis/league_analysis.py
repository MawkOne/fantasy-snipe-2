#!/usr/bin/env python3
"""
League Analysis for UHHP

This script analyzes the entire league to identify potential free agents,
trade targets, and provide strategic recommendations for New Oilers Nation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def load_league_data(file_path: str) -> pd.DataFrame:
    """Load the projections data for the entire league."""
    
    # Read the CSV file
    df = pd.read_csv(file_path, skiprows=1)  # Skip the header row
    
    # Parse position information
    df['Position'] = df['Player'].str.extract(r'([CDW]) \|')
    df['NHL_Team'] = df['Player'].str.extract(r'\| ([A-Z]+)')
    df['Position_Group'] = df['Position'].map({
        'C': 'Center',
        'W': 'Wing', 
        'D': 'Defense'
    })
    
    return df

def calculate_fantasy_points(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate fantasy points based on league scoring system."""
    
    df = df.copy()
    
    # Basic scoring
    df['FPTS_Goals'] = df['G'] * 3
    df['FPTS_Assists'] = df['A'] * 2
    df['FPTS_PlusMinus'] = df['+/-'] * 0.25
    df['FPTS_PIM'] = df['PIM'] * 0
    df['FPTS_SHG'] = df['SHG'] * 2
    df['FPTS_SHOG'] = 0  # Column doesn't exist in data
    
    # Defenseman bonuses
    df['FPTS_DA'] = np.where(df['Position'] == 'D', df['A'] * 1, 0)
    df['FPTS_DG'] = np.where(df['Position'] == 'D', df['G'] * 2, 0)
    
    # Total fantasy points
    df['Total_FPTS'] = (
        df['FPTS_Goals'] + 
        df['FPTS_Assists'] + 
        df['FPTS_PlusMinus'] + 
        df['FPTS_PIM'] + 
        df['FPTS_SHG'] + 
        df['FPTS_SHOG'] + 
        df['FPTS_DA'] + 
        df['FPTS_DG']
    )
    
    return df

def analyze_team_rosters(df: pd.DataFrame) -> Dict:
    """Analyze all team rosters in the league."""
    
    team_analysis = {}
    
    for team in df['Avail'].unique():
        if team == 'Avail':  # Skip header
            continue
            
        team_players = df[df['Avail'] == team]
        
        # Count positions
        position_counts = team_players['Position_Group'].value_counts()
        
        # Calculate team stats
        total_fpts = team_players['Total_FPTS'].sum()
        avg_fpts = team_players['Total_FPTS'].mean()
        
        if len(team_players) > 0 and not team_players['Total_FPTS'].isna().all():
            top_player_idx = team_players['Total_FPTS'].idxmax()
            top_player = team_players.loc[top_player_idx, 'Player']
            top_fpts = team_players['Total_FPTS'].max()
        else:
            top_player = "No players"
            top_fpts = 0
        
        team_analysis[team] = {
            'player_count': len(team_players),
            'position_counts': position_counts.to_dict(),
            'total_fpts': total_fpts,
            'avg_fpts': avg_fpts,
            'top_player': top_player,
            'top_fpts': top_fpts,
            'players': team_players
        }
    
    return team_analysis

def find_potential_free_agents(df: pd.DataFrame) -> pd.DataFrame:
    """Find players who might be available (not on top teams or underperforming)."""
    
    # This is tricky since we don't have actual free agent data
    # We'll look for players on teams with deep rosters who might be available
    # or players who are underperforming relative to their team's depth
    
    # Get all players sorted by fantasy points
    all_players = df.sort_values('Total_FPTS', ascending=False)
    
    # Look for players who might be available based on team depth
    potential_fa = []
    
    for team in df['Avail'].unique():
        if team == 'Avail':
            continue
            
        team_players = df[df['Avail'] == team].sort_values('Total_FPTS', ascending=False)
        
        # If team has more than 15 players, bottom players might be available
        if len(team_players) > 15:
            bottom_players = team_players.tail(len(team_players) - 15)
            potential_fa.extend(bottom_players['Player'].tolist())
        
        # Look for players under 100 FPTS who might be dropped
        low_performers = team_players[team_players['Total_FPTS'] < 100]
        if len(low_performers) > 0:
            potential_fa.extend(low_performers['Player'].tolist())
    
    # Remove duplicates and get unique players
    potential_fa = list(set(potential_fa))
    
    # Get the actual player data
    fa_players = df[df['Player'].isin(potential_fa)].sort_values('Total_FPTS', ascending=False)
    
    return fa_players

def identify_trade_targets(df: pd.DataFrame, my_team: str = 'New Oilers Nation') -> Dict:
    """Identify potential trade targets from other teams."""
    
    my_team_players = df[df['Avail'] == my_team]
    my_team_fpts = my_team_players['Total_FPTS'].sum()
    
    trade_targets = {}
    
    for team in df['Avail'].unique():
        if team == 'Avail' or team == my_team:
            continue
            
        team_players = df[df['Avail'] == team]
        team_fpts = team_players['Total_FPTS'].sum()
        
        # Look for teams that might be willing to trade
        # Teams with high total FPTS might be looking to consolidate
        # Teams with low total FPTS might be looking to rebuild
        
        if team_fpts > my_team_fpts * 1.2:  # Much stronger team
            # Look for their depth players
            depth_players = team_players.sort_values('Total_FPTS', ascending=False).iloc[5:10]
            trade_targets[team] = {
                'type': 'depth_from_strong_team',
                'players': depth_players,
                'team_fpts': team_fpts
            }
        elif team_fpts < my_team_fpts * 0.8:  # Much weaker team
            # Look for their top players
            top_players = team_players.sort_values('Total_FPTS', ascending=False).head(5)
            trade_targets[team] = {
                'type': 'top_from_weak_team',
                'players': top_players,
                'team_fpts': team_fpts
            }
    
    return trade_targets

def main():
    print("🏒 UHHP League Analysis for New Oilers Nation")
    print("=" * 60)
    
    # Load league data
    df = load_league_data('/Users/markhenderson/Cursor Projects/NHL-API/docs/projections.csv')
    df = calculate_fantasy_points(df)
    
    print(f"Total players in league: {len(df)}")
    print()
    
    # Analyze team rosters
    team_analysis = analyze_team_rosters(df)
    
    # Print league standings by total fantasy points
    print("📊 League Standings (by Total Fantasy Points):")
    print("-" * 50)
    standings = sorted(team_analysis.items(), key=lambda x: x[1]['total_fpts'], reverse=True)
    
    for i, (team, stats) in enumerate(standings, 1):
        print(f"{i:2d}. {team:25s} | {stats['total_fpts']:6.1f} FPTS | {stats['player_count']:2d} players | Top: {stats['top_player'][:20]}")
    
    print()
    
    # Find my team's position
    my_team = 'New Oilers Nation'
    my_position = next(i for i, (team, _) in enumerate(standings, 1) if team == my_team)
    my_stats = team_analysis[my_team]
    
    print(f"🎯 Your Team Position: #{my_position} out of {len(standings)}")
    print(f"Total Fantasy Points: {my_stats['total_fpts']:.1f}")
    print(f"Average per Player: {my_stats['avg_fpts']:.1f}")
    print()
    
    # Find potential free agents
    print("🔍 Potential Free Agents (Players who might be available):")
    print("-" * 60)
    potential_fa = find_potential_free_agents(df)
    
    if len(potential_fa) > 0:
        print("Top 20 potential free agents:")
        for i, (_, player) in enumerate(potential_fa.head(20).iterrows(), 1):
            print(f"{i:2d}. {player['Player']:30s} | {player['Total_FPTS']:6.1f} FPTS | {player['Position_Group']:8s}")
    else:
        print("No obvious free agents identified from the data.")
    
    print()
    
    # Identify trade targets
    print("🤝 Potential Trade Targets:")
    print("-" * 40)
    trade_targets = identify_trade_targets(df, my_team)
    
    for team, info in trade_targets.items():
        print(f"\n{team} ({info['type']}):")
        for _, player in info['players'].iterrows():
            player_name = str(player['Player']) if pd.notna(player['Player']) else 'Unknown Player'
            pos_group = str(player['Position_Group']) if pd.notna(player['Position_Group']) else 'Unknown'
            fpts = player['Total_FPTS'] if pd.notna(player['Total_FPTS']) else 0
            print(f"  {player_name:30s} | {fpts:6.1f} FPTS | {pos_group:8s}")
    
    print()
    
    # Strategic recommendations
    print("💡 Strategic Recommendations for New Oilers Nation:")
    print("-" * 55)
    
    # Compare to league average
    league_avg_fpts = np.mean([stats['total_fpts'] for stats in team_analysis.values()])
    league_avg_players = np.mean([stats['player_count'] for stats in team_analysis.values()])
    
    print(f"1. Your team has {my_stats['total_fpts']:.1f} total FPTS vs league average of {league_avg_fpts:.1f}")
    print(f"2. Your team has {my_stats['player_count']} players vs league average of {league_avg_players:.1f}")
    
    if my_stats['total_fpts'] < league_avg_fpts:
        print("   → Consider adding more high-scoring players")
    
    if my_stats['player_count'] < league_avg_players:
        print("   → Consider adding more depth to your roster")
    
    # Position-specific recommendations
    my_positions = my_stats['position_counts']
    print(f"\n3. Position Analysis:")
    print(f"   Centers: {my_positions.get('Center', 0)} (need 2 minimum)")
    print(f"   Wings: {my_positions.get('Wing', 0)} (need 3 minimum)")
    print(f"   Defense: {my_positions.get('Defense', 0)} (need 4 minimum)")
    print(f"   Goalies: 0 (URGENT: need 2 minimum!)")
    
    print(f"\n4. Top Priority: Add 2 goalies immediately!")
    print(f"5. Consider trading depth for elite talent")
    print(f"6. Look for undervalued players on struggling teams")

if __name__ == "__main__":
    main()
