#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def show_all_teams_analysis():
    """Show complete analysis for all 32 teams"""
    
    client = bigquery.Client()
    
    print("="*120)
    print("COMPLETE TEAM ANALYSIS - ALL 32 TEAMS")
    print("="*120)
    
    # Get complete team analysis
    query = """
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        near_elite_players,
        good_players,
        future_elites,
        young_elite,
        peak_elite,
        veteran_elite,
        aging_elite,
        young_core,
        peak_core,
        veteran_core,
        aging_core,
        avg_elite_age,
        avg_cf_pct,
        avg_gf60,
        avg_core_toi,
        total_points,
        original_strength,
        contention_cycle
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected`
    ORDER BY 
        CASE 
            WHEN elite_players >= 3 THEN 1
            WHEN elite_players >= 2 AND (aging_elite = 0 OR aging_elite < elite_players) THEN 1
            WHEN elite_players = 1 AND (near_elite_players >= 2 OR good_players >= 3) THEN 2
            WHEN elite_players = 1 AND aging_elite > 0 AND peak_elite = 0 THEN 3
            WHEN future_elites > 0 AND elite_players > 0 THEN 4
            WHEN future_elites > 0 AND elite_players = 0 THEN 5
            WHEN elite_players = 0 AND (near_elite_players >= 3 OR good_players >= 5) THEN 6
            ELSE 7
        END,
        elite_players DESC,
        near_elite_players DESC
    """
    
    results = client.query(query).to_dataframe()
    
    # Group by contention cycle
    cycle_groups = results.groupby('contention_cycle')
    
    for cycle, group in cycle_groups:
        print(f'\n{cycle.upper()} ({len(group)} teams)')
        print('='*80)
        print(f'Team | Players | Core | Elite | Near Elite | Good | Future | Young | Peak | Aging | Elite Age | CF% | GF60 | TOI | Points | Strength')
        print('-'*80)
        
        for _, row in group.iterrows():
            print(f'{row.team_abbr:4} | {row.total_players:7} | {row.core_players:4} | {row.elite_players:5} | {row.near_elite_players:10} | {row.good_players:4} | {row.future_elites:6} | {row.young_elite:5} | {row.peak_elite:4} | {row.aging_elite:6} | {row.avg_elite_age:9.1f} | {row.avg_cf_pct:3.0f} | {row.avg_gf60:4.1f} | {row.avg_core_toi:3.0f} | {row.total_points:6.0f} | {row.original_strength:8.1f}')
    
    print('\n📊 SUMMARY STATISTICS')
    print('='*50)
    print(f'Total Teams: {len(results)}')
    print(f'Total Players: {results["total_players"].sum()}')
    print(f'Total Elite Players: {results["elite_players"].sum()}')
    print(f'Total Near Elite Players: {results["near_elite_players"].sum()}')
    print(f'Total Good Players: {results["good_players"].sum()}')
    print(f'Total Future Elite Players: {results["future_elites"].sum()}')
    print(f'Total Core Players: {results["core_players"].sum()}')
    
    print('\nContention Cycle Distribution:')
    cycle_counts = results['contention_cycle'].value_counts()
    for cycle, count in cycle_counts.items():
        print(f'  {cycle:15}: {count:2} teams ({count/len(results)*100:.1f}%)')
    
    # Show top teams by different metrics
    print('\n🏆 TOP TEAMS BY METRIC')
    print('='*50)
    
    print('\nMost Elite Players:')
    top_elite = results.nlargest(5, 'elite_players')[['team_abbr', 'elite_players', 'contention_cycle']]
    for _, row in top_elite.iterrows():
        print(f'  {row.team_abbr:4}: {row.elite_players} elite → {row.contention_cycle}')
    
    print('\nHighest Team Strength:')
    top_strength = results.nlargest(5, 'original_strength')[['team_abbr', 'original_strength', 'elite_players', 'contention_cycle']]
    for _, row in top_strength.iterrows():
        print(f'  {row.team_abbr:4}: {row.original_strength:.1f} strength, {row.elite_players} elite → {row.contention_cycle}')
    
    print('\nMost Total Points:')
    top_points = results.nlargest(5, 'total_points')[['team_abbr', 'total_points', 'elite_players', 'contention_cycle']]
    for _, row in top_points.iterrows():
        print(f'  {row.team_abbr:4}: {row.total_points:.0f} points, {row.elite_players} elite → {row.contention_cycle}')
    
    print('\nMost Future Elite Players:')
    top_future = results.nlargest(5, 'future_elites')[['team_abbr', 'future_elites', 'elite_players', 'contention_cycle']]
    for _, row in top_future.iterrows():
        print(f'  {row.team_abbr:4}: {row.future_elites} future elite, {row.elite_players} elite → {row.contention_cycle}')

if __name__ == "__main__":
    show_all_teams_analysis()
