#!/usr/bin/env python3

import pandas as pd
import json
import re
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

def extract_team_rosters(dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data):
    """Extract roster information by team"""
    
    print("\nExtracting team rosters...")
    
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
    
    team_rosters = defaultdict(lambda: {
        'forwards': [],
        'defensemen': [],
        'goalies': []
    })
    
    # Process Dobber data
    for _, row in dobber_data.iterrows():
        player_name = str(row['Player']) if pd.notna(row['Player']) else ''
        team_raw = row['Team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row.get('D?', '')) if pd.notna(row.get('D?', '')) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if position == 'y':  # Defenseman
            team_rosters[team]['defensemen'].append({
                'name': player_name,
                'source': 'dobber',
                'rating': row.get('Rating', 0)
            })
        else:  # Forward
            team_rosters[team]['forwards'].append({
                'name': player_name,
                'source': 'dobber',
                'rating': row.get('Rating', 0)
            })
    
    # Process FantasyPros data
    for _, row in fantasy_pros_data.iterrows():
        player_name = str(row['PLAYER NAME']) if pd.notna(row['PLAYER NAME']) else ''
        team_raw = row['TEAM']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row['POS']) if pd.notna(row['POS']) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if 'G' in position:  # Goalie
            team_rosters[team]['goalies'].append({
                'name': player_name,
                'source': 'fantasy_pros',
                'rank': row['RK'],
                'avg_rank': row['AVG.']
            })
        elif 'D' in position:  # Defenseman
            team_rosters[team]['defensemen'].append({
                'name': player_name,
                'source': 'fantasy_pros',
                'rank': row['RK'],
                'avg_rank': row['AVG.']
            })
        else:  # Forward
            team_rosters[team]['forwards'].append({
                'name': player_name,
                'source': 'fantasy_pros',
                'rank': row['RK'],
                'avg_rank': row['AVG.']
            })
    
    # Process DtZ skater data
    for _, row in dtz_skater_data.iterrows():
        player_name = str(row['Player']) if pd.notna(row['Player']) else ''
        team_raw = row['Team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        position = str(row['Pos']) if pd.notna(row['Pos']) else ''
        
        if not player_name or team == 'UNK':
            continue
        
        if 'D' in position:  # Defenseman
            team_rosters[team]['defensemen'].append({
                'name': player_name,
                'source': 'dtz',
                'age': row.get('Age'),
                'toi_es': row.get('TOI ES'),
                'toi_pp': row.get('TOI PP'),
                'toi_pk': row.get('TOI PK'),
                'points': row.get('Points'),
                'rank': row.get('Rank')
            })
        else:  # Forward
            team_rosters[team]['forwards'].append({
                'name': player_name,
                'source': 'dtz',
                'age': row.get('Age'),
                'toi_es': row.get('TOI ES'),
                'toi_pp': row.get('TOI PP'),
                'toi_pk': row.get('TOI PK'),
                'points': row.get('Points'),
                'rank': row.get('Rank')
            })
    
    # Process DtZ goalie data
    for _, row in dtz_goalie_data.iterrows():
        player_name = str(row['player']) if pd.notna(row['player']) else ''
        team_raw = row['team']
        team = team_mapping.get(str(team_raw), str(team_raw)) if pd.notna(team_raw) else 'UNK'
        
        if not player_name or team == 'UNK':
            continue
        
        team_rosters[team]['goalies'].append({
            'name': player_name,
            'source': 'dtz',
            'age': row.get('age'),
            'gp': row.get('GP'),
            'wins': row.get('W'),
            'sv_pct': row.get('SV%'),
            'rank': row.get('Rank')
        })
    
    return dict(team_rosters)

def assign_toi_tiers(team_rosters):
    """Assign TOI tiers based on forecast data"""
    
    print("\nAssigning TOI tiers...")
    
    for team, positions in team_rosters.items():
        for pos_type in ['forwards', 'defensemen', 'goalies']:
            players = positions[pos_type]
            
            # Sort by rating/rank (lower is better)
            if pos_type == 'goalies':
                players.sort(key=lambda x: x.get('rank', 999) if x.get('rank') else 999)
            else:
                players.sort(key=lambda x: x.get('rating', 0) if x.get('rating') else x.get('rank', 999), reverse=True)
            
            # Assign tiers based on ranking
            for i, player in enumerate(players):
                if i < 3:  # Top 3
                    player['toi_tier'] = 'Elite'
                elif i < 6:  # Next 3
                    player['toi_tier'] = 'Top Line'
                elif i < 12:  # Next 6
                    player['toi_tier'] = 'Middle 6'
                elif i < 18:  # Next 6
                    player['toi_tier'] = 'Bottom 6'
                else:  # Rest
                    player['toi_tier'] = 'Depth'

def create_roster_template(team_rosters):
    """Create the roster template structure"""
    
    print("\nCreating roster template...")
    
    template = {
        "season": "2025-26",
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
        
        # Create projected lineup structure
        projected_lineup = {
            "forwards": {
                "line_1": positions['forwards'][:3] if len(positions['forwards']) >= 3 else positions['forwards'],
                "line_2": positions['forwards'][3:6] if len(positions['forwards']) >= 6 else positions['forwards'][3:],
                "line_3": positions['forwards'][6:9] if len(positions['forwards']) >= 9 else positions['forwards'][6:],
                "line_4": positions['forwards'][9:12] if len(positions['forwards']) >= 12 else positions['forwards'][9:],
                "prospects": positions['forwards'][12:] if len(positions['forwards']) > 12 else []
            },
            "defensemen": {
                "pair_1": positions['defensemen'][:2] if len(positions['defensemen']) >= 2 else positions['defensemen'],
                "pair_2": positions['defensemen'][2:4] if len(positions['defensemen']) >= 4 else positions['defensemen'][2:],
                "pair_3": positions['defensemen'][4:6] if len(positions['defensemen']) >= 6 else positions['defensemen'][4:],
                "depth": positions['defensemen'][6:] if len(positions['defensemen']) > 6 else []
            },
            "goalies": positions['goalies']
        }
        
        # Add special teams assignments (simplified)
        special_teams = {
            "pp1": positions['forwards'][:3] + positions['defensemen'][:2] if len(positions['forwards']) >= 3 and len(positions['defensemen']) >= 2 else [],
            "pp2": positions['forwards'][3:6] + positions['defensemen'][2:4] if len(positions['forwards']) >= 6 and len(positions['defensemen']) >= 4 else [],
            "pk1": positions['forwards'][6:8] + positions['defensemen'][:2] if len(positions['forwards']) >= 8 and len(positions['defensemen']) >= 2 else [],
            "pk2": positions['forwards'][8:10] + positions['defensemen'][2:4] if len(positions['forwards']) >= 10 and len(positions['defensemen']) >= 4 else []
        }
        
        template["teams"][team_abbr] = {
            "team_name": team_name,
            "projected_lineup": projected_lineup,
            "special_teams": special_teams
        }
    
    return template

def main():
    """Main function to extract roster data from forecasts"""
    
    print("="*60)
    print("EXTRACTING ROSTER DATA FROM FORECASTS")
    print("="*60)
    
    # Load forecast data
    dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data = load_forecast_data()
    
    # Extract team rosters
    team_rosters = extract_team_rosters(dobber_data, fantasy_pros_data, dtz_skater_data, dtz_goalie_data)
    
    # Assign TOI tiers
    assign_toi_tiers(team_rosters)
    
    # Create roster template
    template = create_roster_template(team_rosters)
    
    # Save to file
    with open('projected_rosters_2025_26_from_forecasts.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"\nCreated roster template with {len(template['teams'])} teams")
    print("Saved to: projected_rosters_2025_26_from_forecasts.json")
    
    # Show sample for Edmonton
    if 'EDM' in template['teams']:
        print("\n" + "="*50)
        print("EDMONTON OILERS SAMPLE:")
        print("="*50)
        
        edm = template['teams']['EDM']
        
        print("\nFORWARDS:")
        for line_name, players in edm['projected_lineup']['forwards'].items():
            if players:
                print(f"  {line_name.upper()}:")
                for player in players:
                    print(f"    - {player['name']} ({player.get('toi_tier', 'N/A')})")
        
        print("\nDEFENSEMEN:")
        for pair_name, players in edm['projected_lineup']['defensemen'].items():
            if players:
                print(f"  {pair_name.upper()}:")
                for player in players:
                    print(f"    - {player['name']} ({player.get('toi_tier', 'N/A')})")
        
        print("\nGOALIES:")
        for player in edm['projected_lineup']['goalies']:
            print(f"  - {player['name']} ({player.get('toi_tier', 'N/A')})")

if __name__ == "__main__":
    main()
