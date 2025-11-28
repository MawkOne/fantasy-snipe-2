#!/usr/bin/env python3
"""
Analyze Rookie Draft Strategy in UHHP League
Question: Does investing in rookie draft picks correlate with success?
"""

import json
from collections import defaultdict

def load_data():
    with open('uhhp_league_history_full.json', 'r') as f:
        return json.load(f)

def analyze_rookie_strategy(data):
    """Analyze correlation between rookie holdings and team success"""
    
    print("=" * 80)
    print("ROOKIE DRAFT STRATEGY ANALYSIS")
    print("=" * 80)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        print(f"\n{season_name}:")
        print("-" * 80)
        
        team_stats = []
        
        for team_name, team_data in season['teams'].items():
            # Count rookies
            rookie_count = 0
            if 'final_roster' in team_data:
                for section in ['active', 'reserve', 'injured']:
                    for player in team_data['final_roster'][section]:
                        if player.get('is_rookie', False):
                            rookie_count += 1
            
            # Get wins
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            wins = 0
            if weekly_results:
                wins = weekly_results[-1].get('record', {}).get('wins', 0)
            
            team_stats.append({
                'team': team_name,
                'rookies': rookie_count,
                'wins': wins
            })
        
        # Sort by rookies
        team_stats.sort(key=lambda x: x['rookies'], reverse=True)
        
        print(f"\n{'Team':<35} {'Rookies':<10} {'Wins'}")
        print("-" * 80)
        
        for stats in team_stats:
            print(f"{stats['team']:<35} {stats['rookies']:<10} {stats['wins']}")
        
        # Analyze correlation
        most_rookies = team_stats[:4]
        least_rookies = team_stats[-4:]
        
        most_avg_wins = sum(t['wins'] for t in most_rookies) / len(most_rookies)
        least_avg_wins = sum(t['wins'] for t in least_rookies) / len(least_rookies)
        
        print(f"\n📊 Key Findings:")
        print(f"   Teams with Most Rookies (Top 4) Avg Wins: {most_avg_wins:.1f}")
        print(f"   Teams with Least Rookies (Bottom 4) Avg Wins: {least_avg_wins:.1f}")
        print(f"   Difference: {most_avg_wins - least_avg_wins:.1f} wins")
        
        # Champion's rookie count
        champion = max(team_stats, key=lambda x: x['wins'])
        champion_rank_by_rookies = team_stats.index([t for t in team_stats if t['team'] == champion['team']][0]) + 1
        print(f"   Champion's Rookie Rank: {champion_rank_by_rookies}/{len(team_stats)}")
        print(f"   Champion Rookie Count: {champion['rookies']}")

def analyze_rookie_pipeline(data):
    """Analyze teams' rookie pipeline over time"""
    
    print("\n\n" + "=" * 80)
    print("ROOKIE PIPELINE ANALYSIS (3-Year View)")
    print("=" * 80)
    
    team_pipeline = defaultdict(list)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        for team_name, team_data in season['teams'].items():
            # Count rookies
            rookie_count = 0
            if 'final_roster' in team_data:
                for section in ['active', 'reserve', 'injured']:
                    for player in team_data['final_roster'][section]:
                        if player.get('is_rookie', False):
                            rookie_count += 1
            
            # Get wins
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            wins = 0
            if weekly_results:
                wins = weekly_results[-1].get('record', {}).get('wins', 0)
            
            team_pipeline[team_name].append({
                'season': season_name,
                'rookies': rookie_count,
                'wins': wins
            })
    
    # Find teams committed to rookie strategy
    print("\nTeams by Average Rookie Holdings:")
    print("-" * 80)
    
    team_summaries = []
    for team_name in sorted(team_pipeline.keys()):
        pipeline = team_pipeline[team_name]
        if len(pipeline) == 3:
            avg_rookies = sum(p['rookies'] for p in pipeline) / 3
            total_wins = sum(p['wins'] for p in pipeline)
            avg_wins = total_wins / 3
            
            team_summaries.append({
                'team': team_name,
                'avg_rookies': avg_rookies,
                'avg_wins': avg_wins,
                'total_wins': total_wins
            })
    
    # Sort by average rookies
    team_summaries.sort(key=lambda x: x['avg_rookies'], reverse=True)
    
    print(f"\n{'Team':<35} {'Avg Rookies':<15} {'Avg Wins':<12} {'Total Wins'}")
    print("-" * 80)
    
    for summary in team_summaries:
        print(f"{summary['team']:<35} {summary['avg_rookies']:<15.1f} "
              f"{summary['avg_wins']:<12.1f} {summary['total_wins']}")
    
    print(f"\n📊 Key Findings:")
    
    # High rookie teams vs low rookie teams
    high_rookie_teams = team_summaries[:4]
    low_rookie_teams = team_summaries[-4:]
    
    high_avg_wins = sum(t['avg_wins'] for t in high_rookie_teams) / len(high_rookie_teams)
    low_avg_wins = sum(t['avg_wins'] for t in low_rookie_teams) / len(low_rookie_teams)
    
    print(f"   Top 4 Rookie-Heavy Teams Avg Wins: {high_avg_wins:.1f}")
    print(f"   Bottom 4 Rookie-Light Teams Avg Wins: {low_avg_wins:.1f}")
    print(f"   Difference: {high_avg_wins - low_avg_wins:.1f} wins")

if __name__ == "__main__":
    data = load_data()
    
    analyze_rookie_strategy(data)
    analyze_rookie_pipeline(data)
    
    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("Holding rookies is a LONG-TERM strategy. Teams invest in the future,")
    print("not immediate success. The 3-year view shows if the strategy pays off.")
    print("=" * 80)

