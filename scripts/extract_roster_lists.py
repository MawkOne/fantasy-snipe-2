#!/usr/bin/env python3

import pandas as pd
import json
from typing import Dict, List, Set
from collections import defaultdict

def load_forecast_data():
    """Load all forecast data files"""
    
    print("Loading forecast data...")
    
    # Load Dobber data
    dobber_data = pd.read_csv('docs/Forecasts/2025_26_dobber/2025_26_dobber_forecast.md', sep='\t')
    print(f"Loaded Dobber data: {len(dobber_data)} players")
    
    # Load FantasyPros data
    fantasy_pros_data = pd.read_csv('docs/Forecasts/2025_26_fantasy_pros/FantasyPros_2025_Draft_ALL_Rankings.csv')
    print(f"Loaded FantasyPros data: {len(fantasy_pros_data)} players")
    
    # Load DtZ skater data
    dtz_skater_data = pd.read_csv('docs/Forecasts/2025_26_DtZ/Copy of Preliminary - DtZ 2025-2026 NHL Fantasy Projections - Skater Projections.csv')
    print(f"Loaded DtZ skater data: {len(dtz_skater_data)} players")
    
    # Load DtZ goalie data
    dtz_goalie_data = pd.read_csv('docs/Forecasts/2025_26_DtZ/Copy of Preliminary - DtZ 2025-2026 NHL Fantasy Projections - Goalie Projections.csv')
    print(f"Loaded DtZ goalie data: {len(dtz_goalie_data)} players")
    
    return dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data

def extract_roster_lists(dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data):
    """Extract just the roster lists by team - no rankings, just who's on each team"""
    
    print("\nExtracting roster lists...")
    
    # Team mapping for consistency
    team_mapping = {
        'TB': 'TBL', 'NJ': 'NJD', 'NYR': 'NYR', 'NYI': 'NYI', 'PIT': 'PIT',
        'PHI': 'PHI', 'WSH': 'WSH', 'CAR': 'CAR', 'FLA': 'FLA', 'BOS': 'BOS',
        'BUF': 'BUF', 'DET': 'DET', 'MTL': 'MTL', 'OTT': 'OTT', 'TOR': 'TOR',
        'CHI': 'CHI', 'COL': 'COL', 'DAL': 'DAL', 'MIN': 'MIN', 'NSH': 'NSH',
        'STL': 'STL', 'WPG': 'WPG', 'CGY': 'CGY', 'EDM': 'EDM', 'VAN': 'VAN',
        'VGK': 'VGK', 'SJ': 'SJS', 'SEA': 'SEA', 'UTA': 'UTA', 'CBJ': 'CBJ',
        'LAK': 'LAK', 'ARI': 'ARI'
    }
    
    # Use sets to automatically handle duplicates
    team_rosters = defaultdict(lambda: {
        'forwards': set(),
        'defensemen': set(),
        'goalies': set()
    })
    
    # Process Dobber data
    print("Processing Dobber data...")
    for _, row in dobber_data.iterrows():
        player_name = str(row['Player']) if pd.notna(row['Player']) else ''
        team_raw = row['Team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row.get('D?', '')) if pd.notna(row.get('D?', '')) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if position == 'y':  # Defenseman
            team_rosters[team]['defensemen'].add(player_name)
        else:  # Forward
            team_rosters[team]['forwards'].add(player_name)
    
    # Process FantasyPros data
    print("Processing FantasyPros data...")
    for _, row in fantasy_pros_data.iterrows():
        player_name = str(row['PLAYER NAME']) if pd.notna(row['PLAYER NAME']) else ''
        team_raw = row['TEAM']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row['POS']) if pd.notna(row['POS']) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if 'G' in position:  # Goalie
            team_rosters[team]['goalies'].add(player_name)
        elif 'D' in position:  # Defenseman
            team_rosters[team]['defensemen'].add(player_name)
        else:  # Forward
            team_rosters[team]['forwards'].add(player_name)
    
    # Process DtZ skater data
    print("Processing DtZ skater data...")
    for _, row in dtz_skater_data.iterrows():
        player_name = str(row['Player']) if pd.notna(row['Player']) else ''
        team_raw = row['Team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row['Pos']) if pd.notna(row['Pos']) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if 'D' in position:  # Defenseman
            team_rosters[team]['defensemen'].add(player_name)
        else:  # Forward
            team_rosters[team]['forwards'].add(player_name)
    
    # Process DtZ goalie data
    print("Processing DtZ goalie data...")
    for _, row in dtz_goalie_data.iterrows():
        player_name = str(row['player']) if pd.notna(row['player']) else ''
        team_raw = row['team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        
        if not player_name or team == 'UNK':
            continue
        
        team_rosters[team]['goalies'].add(player_name)
    
    # Convert sets back to lists for JSON serialization
    for team in team_rosters:
        for position in team_rosters[team]:
            team_rosters[team][position] = sorted(list(team_rosters[team][position]))
    
    return dict(team_rosters)

def create_roster_template(team_rosters):
    """Create a simple roster template with just player lists"""
    
    print("\nCreating roster template...")
    
    template = {
        "season": "2025-26",
        "description": "Projected rosters extracted from Dobber, FantasyPros, and DtZ forecasts",
        "teams": {}
    }
    
    for team_abbr, positions in team_rosters.items():
        if not positions['forwards'] and not positions['defensemen'] and not positions['goalies']:
            continue
            
        # Convert team abbreviation to team name
        team_name_mapping = {
            'TBL': 'tampa-bay-lightning', 'NJD': 'new-jersey-devils', 'NYR': 'new-york-rangers',
            'NYI': 'new-york-islanders', 'PIT': 'pittsburgh-penguins', 'PHI': 'philadelphia-flyers',
            'WSH': 'washington-capitals', 'CAR': 'carolina-hurricanes', 'FLA': 'florida-panthers',
            'BOS': 'boston-bruins', 'BUF': 'buffalo-sabres', 'DET': 'detroit-red-wings',
            'MTL': 'montreal-canadiens', 'OTT': 'ottawa-senators', 'TOR': 'toronto-maple-leafs',
            'CHI': 'chicago-blackhawks', 'COL': 'colorado-avalanche', 'DAL': 'dallas-stars',
            'MIN': 'minnesota-wild', 'NSH': 'nashville-predators', 'STL': 'st-louis-blues',
            'WPG': 'winnipeg-jets', 'CGY': 'calgary-flames', 'EDM': 'edmonton-oilers',
            'VAN': 'vancouver-canucks', 'VGK': 'vegas-golden-knights', 'SJS': 'san-jose-sharks',
            'SEA': 'seattle-kraken', 'UTA': 'utah-hockey-club', 'CBJ': 'columbus-blue-jackets',
            'LAK': 'los-angeles-kings', 'ARI': 'arizona-coyotes'
        }
        
        team_name = team_name_mapping.get(team_abbr, team_abbr.lower())
        
        template["teams"][team_abbr] = {
            "team_name": team_name,
            "forwards": positions['forwards'],
            "defensemen": positions['defensemen'],
            "goalies": positions['goalies'],
            "total_players": len(positions['forwards']) + len(positions['defensemen']) + len(positions['goalies'])
        }
    
    return template

def main():
    """Main function to extract roster lists from forecasts"""
    
    print("="*60)
    print("EXTRACTING ROSTER LISTS FROM FORECASTS")
    print("="*60)
    
    # Load forecast data
    dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data = load_forecast_data()
    
    # Extract roster lists
    team_rosters = extract_roster_lists(dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data)
    
    # Create roster template
    template = create_roster_template(team_rosters)
    
    # Save to file
    with open('projected_rosters_2025_26_lists.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"\nCreated roster lists with {len(template['teams'])} teams")
    print("Saved to: projected_rosters_2025_26_lists.json")
    
    # Show sample for Edmonton
    if 'EDM' in template['teams']:
        print("\n" + "="*50)
        print("EDMONTON OILERS ROSTER LIST:")
        print("="*50)
        
        edm = template['teams']['EDM']
        
        print(f"\nFORWARDS ({len(edm['forwards'])}):")
        for player in edm['forwards']:
            print(f"  - {player}")
        
        print(f"\nDEFENSEMEN ({len(edm['defensemen'])}):")
        for player in edm['defensemen']:
            print(f"  - {player}")
        
        print(f"\nGOALIES ({len(edm['goalies'])}):")
        for player in edm['goalies']:
            print(f"  - {player}")
        
        print(f"\nTotal Players: {edm['total_players']}")
    
    # Show summary stats
    print("\n" + "="*50)
    print("SUMMARY STATISTICS:")
    print("="*50)
    
    total_forwards = sum(len(team['forwards']) for team in template['teams'].values())
    total_defensemen = sum(len(team['defensemen']) for team in template['teams'].values())
    total_goalies = sum(len(team['goalies']) for team in template['teams'].values())
    
    print(f"Total Teams: {len(template['teams'])}")
    print(f"Total Forwards: {total_forwards}")
    print(f"Total Defensemen: {total_defensemen}")
    print(f"Total Goalies: {total_goalies}")
    print(f"Total Players: {total_forwards + total_defensemen + total_goalies}")
    
    # Show teams with most players
    print(f"\nTeams with most players:")
    team_counts = [(team, data['total_players']) for team, data in template['teams'].items()]
    team_counts.sort(key=lambda x: x[1], reverse=True)
    
    for team, count in team_counts[:10]:
        print(f"  {team}: {count} players")

if __name__ == "__main__":
    main()
