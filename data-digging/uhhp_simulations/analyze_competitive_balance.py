#!/usr/bin/env python3
"""
Analyze UHHP League Competitive Balance
Questions:
1. Can you buy a championship?
2. Can you buy to compete?
3. Can you rebuild with draft picks?
4. Does doing butt loads of in-season player pickups prevent others from competing?
"""

import json
from collections import defaultdict
from typing import Dict, List, Tuple

def load_data():
    with open('uhhp_league_history_full.json', 'r') as f:
        return json.load(f)

def analyze_salary_vs_success(data):
    """Question 1 & 2: Can you buy a championship? Can you buy to compete?"""
    
    print("=" * 80)
    print("QUESTION 1 & 2: CAN YOU BUY A CHAMPIONSHIP? CAN YOU BUY TO COMPETE?")
    print("=" * 80)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        print(f"\n{season_name} Analysis:")
        print("-" * 80)
        
        team_stats = []
        
        for team_name, team_data in season['teams'].items():
            # Get final salary
            roster = team_data.get('final_roster', {})
            total_salary = roster.get('totals', {}).get('total_salary', 0)
            
            # Get final record from last weekly result
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            if weekly_results:
                last_result = weekly_results[-1]
                record = last_result.get('record', {})
                wins = record.get('wins', 0)
                losses = record.get('losses', 0)
                win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
                
                # Check if made playoffs (>= 8 wins typically)
                made_playoffs = wins >= 8
                
                team_stats.append({
                    'team': team_name,
                    'salary': total_salary,
                    'wins': wins,
                    'losses': losses,
                    'win_pct': win_pct,
                    'made_playoffs': made_playoffs
                })
        
        # Sort by wins
        team_stats.sort(key=lambda x: x['wins'], reverse=True)
        
        # Print results
        print(f"\n{'Team':<35} {'Salary':<10} {'Record':<12} {'Win %':<8} {'Playoffs'}")
        print("-" * 80)
        
        for i, stats in enumerate(team_stats):
            playoff_marker = "✓" if stats['made_playoffs'] else "✗"
            champion_marker = "🏆 " if i == 0 else "   "
            print(f"{champion_marker}{stats['team']:<32} ${stats['salary']:<9} "
                  f"{stats['wins']}-{stats['losses']:<9} {stats['win_pct']:.3f}    {playoff_marker}")
        
        # Calculate correlation between salary and success
        champion = team_stats[0]
        median_salary = sorted([t['salary'] for t in team_stats])[len(team_stats)//2]
        
        print(f"\n📊 Key Findings:")
        print(f"   Champion: {champion['team']}")
        print(f"   Champion Salary: ${champion['salary']} (Median: ${median_salary})")
        print(f"   Champion Rank by Salary: {sorted(team_stats, key=lambda x: x['salary'], reverse=True).index(champion) + 1}/{len(team_stats)}")
        
        # High spenders vs low spenders
        high_spenders = sorted(team_stats, key=lambda x: x['salary'], reverse=True)[:4]
        low_spenders = sorted(team_stats, key=lambda x: x['salary'])[:4]
        
        high_spender_avg_wins = sum(t['wins'] for t in high_spenders) / len(high_spenders)
        low_spender_avg_wins = sum(t['wins'] for t in low_spenders) / len(low_spenders)
        
        print(f"   Top 4 Spenders Avg Wins: {high_spender_avg_wins:.1f}")
        print(f"   Bottom 4 Spenders Avg Wins: {low_spender_avg_wins:.1f}")
        print(f"   Difference: {high_spender_avg_wins - low_spender_avg_wins:.1f} wins")

def analyze_rebuild_success(data):
    """Question 3: Can you rebuild with draft picks?"""
    
    print("\n\n" + "=" * 80)
    print("QUESTION 3: CAN YOU REBUILD WITH DRAFT PICKS?")
    print("=" * 80)
    
    # Track teams with draft picks and their trajectories
    team_trajectories = defaultdict(list)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        for team_name, team_data in season['teams'].items():
            # Count draft picks held
            roster = team_data.get('final_roster', {})
            draft_picks = 0
            
            # Check injured reserve and reserve for draft picks
            for section in ['injured', 'reserve', 'active']:
                players = roster.get(section, [])
                for player in players:
                    if 'Draft Pick' in player.get('name', ''):
                        draft_picks += 1
            
            # Get wins
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            wins = 0
            if weekly_results:
                last_result = weekly_results[-1]
                wins = last_result.get('record', {}).get('wins', 0)
            
            team_trajectories[team_name].append({
                'season': season_name,
                'draft_picks': draft_picks,
                'wins': wins
            })
    
    # Analyze teams that accumulated picks and bounced back
    print("\nTeam Trajectories (3-Year View):")
    print("-" * 80)
    
    rebuild_stories = []
    
    for team_name in sorted(team_trajectories.keys()):
        trajectory = team_trajectories[team_name]
        if len(trajectory) == 3:
            # Calculate improvement
            wins_change = trajectory[2]['wins'] - trajectory[0]['wins']
            total_picks = sum(t['draft_picks'] for t in trajectory)
            
            # Check if they rebuilt (had bad year then improved)
            had_bad_year = any(t['wins'] <= 7 for t in trajectory[:2])
            improved = wins_change > 3
            
            if had_bad_year and total_picks >= 3:
                rebuild_stories.append({
                    'team': team_name,
                    'trajectory': trajectory,
                    'wins_change': wins_change,
                    'total_picks': total_picks,
                    'improved': improved
                })
    
    # Print rebuild stories
    for story in sorted(rebuild_stories, key=lambda x: x['wins_change'], reverse=True):
        team = story['team']
        traj = story['trajectory']
        
        print(f"\n{team}:")
        print(f"  2022-23: {traj[0]['wins']} wins, {traj[0]['draft_picks']} picks")
        print(f"  2023-24: {traj[1]['wins']} wins, {traj[1]['draft_picks']} picks")
        print(f"  2024-25: {traj[2]['wins']} wins, {traj[2]['draft_picks']} picks")
        print(f"  Total Picks: {story['total_picks']}")
        print(f"  3-Year Change: {'+' if story['wins_change'] > 0 else ''}{story['wins_change']} wins")
        print(f"  Rebuild Success: {'✓ YES' if story['improved'] else '✗ NO'}")
    
    print(f"\n📊 Key Findings:")
    successful_rebuilds = sum(1 for s in rebuild_stories if s['improved'])
    print(f"   Teams that accumulated picks: {len(rebuild_stories)}")
    print(f"   Successful rebuilds (3+ win improvement): {successful_rebuilds}/{len(rebuild_stories)}")

def analyze_transaction_volume(data):
    """Question 4: Does doing butt loads of in-season pickups prevent others from competing?"""
    
    print("\n\n" + "=" * 80)
    print("QUESTION 4: DOES HIGH TRANSACTION VOLUME PREVENT OTHERS FROM COMPETING?")
    print("=" * 80)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        print(f"\n{season_name} Analysis:")
        print("-" * 80)
        
        team_activity = []
        
        for team_name, team_data in season['teams'].items():
            # Count signings (in-season pickups)
            signings = [a for a in team_data['actions'] if a.get('type') == 'signing']
            trades = [a for a in team_data['actions'] if a.get('type') == 'trade']
            drops = [a for a in team_data['actions'] if a.get('type') == 'drop']
            
            # Get wins
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            wins = 0
            if weekly_results:
                last_result = weekly_results[-1]
                wins = last_result.get('record', {}).get('wins', 0)
            
            team_activity.append({
                'team': team_name,
                'signings': len(signings),
                'trades': len(trades),
                'drops': len(drops),
                'total_moves': len(signings) + len(trades) + len(drops),
                'wins': wins
            })
        
        # Sort by transaction volume
        team_activity.sort(key=lambda x: x['total_moves'], reverse=True)
        
        print(f"\n{'Team':<35} {'Signings':<10} {'Trades':<8} {'Drops':<8} {'Total':<8} {'Wins'}")
        print("-" * 80)
        
        for stats in team_activity:
            print(f"{stats['team']:<35} {stats['signings']:<10} {stats['trades']:<8} "
                  f"{stats['drops']:<8} {stats['total_moves']:<8} {stats['wins']}")
        
        # Analyze correlation
        most_active = team_activity[:4]
        least_active = team_activity[-4:]
        
        most_active_avg_wins = sum(t['wins'] for t in most_active) / len(most_active)
        least_active_avg_wins = sum(t['wins'] for t in least_active) / len(least_active)
        
        print(f"\n📊 Key Findings:")
        print(f"   Most Active 4 Teams Avg Wins: {most_active_avg_wins:.1f}")
        print(f"   Least Active 4 Teams Avg Wins: {least_active_avg_wins:.1f}")
        print(f"   Difference: {most_active_avg_wins - least_active_avg_wins:.1f} wins")
        
        # Check if most active teams won
        champion = max(team_activity, key=lambda x: x['wins'])
        champion_rank_by_activity = team_activity.index([t for t in team_activity if t['team'] == champion['team']][0]) + 1
        print(f"   Champion's Activity Rank: {champion_rank_by_activity}/{len(team_activity)}")
        print(f"   Champion Total Moves: {champion['total_moves']}")

def generate_summary(data):
    """Generate overall league health summary"""
    
    print("\n\n" + "=" * 80)
    print("OVERALL LEAGUE COMPETITIVE BALANCE SUMMARY")
    print("=" * 80)
    
    # Track unique champions
    champions = []
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        team_wins = []
        
        for team_name, team_data in season['teams'].items():
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            if weekly_results:
                wins = weekly_results[-1].get('record', {}).get('wins', 0)
                team_wins.append((team_name, wins))
        
        champion = max(team_wins, key=lambda x: x[1])
        champions.append(champion[0])
    
    print(f"\nChampions by Season:")
    print(f"  2022-23: {champions[0]}")
    print(f"  2023-24: {champions[1]}")
    print(f"  2024-25: {champions[2]}")
    print(f"\n  Unique Champions: {len(set(champions))} of 3 seasons")
    print(f"  Repeat Champion: {'Yes - ' + max(set(champions), key=champions.count) if len(set(champions)) < 3 else 'No'}")
    
    # Check playoff consistency
    playoff_appearances = defaultdict(int)
    
    for season_name in ['2022-2023', '2023-2024', '2024-2025']:
        season = data['seasons'][season_name]
        
        for team_name, team_data in season['teams'].items():
            weekly_results = [a for a in team_data['actions'] if a.get('type') == 'weekly_result']
            if weekly_results:
                wins = weekly_results[-1].get('record', {}).get('wins', 0)
                if wins >= 8:  # Made playoffs
                    playoff_appearances[team_name] += 1
    
    print(f"\nPlayoff Appearances (3 seasons):")
    for team, appearances in sorted(playoff_appearances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {team:<35} {appearances}/3")
    
    consistent_contenders = sum(1 for count in playoff_appearances.values() if count == 3)
    never_playoffs = 13 - len(playoff_appearances)
    
    print(f"\n  Consistent Contenders (3/3 playoffs): {consistent_contenders}")
    print(f"  Never Made Playoffs: {never_playoffs}")

if __name__ == "__main__":
    data = load_data()
    
    analyze_salary_vs_success(data)
    analyze_rebuild_success(data)
    analyze_transaction_volume(data)
    generate_summary(data)
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

