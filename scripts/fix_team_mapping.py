#!/usr/bin/env python3

import json
from collections import defaultdict

def fix_team_mapping():
    """Fix the team mapping to consolidate duplicates and remove non-teams"""
    
    # Load the current data
    with open('projected_rosters_2025_26_lists.json', 'r') as f:
        data = json.load(f)
    
    # Team consolidation mapping
    team_consolidation = {
        # Standardize abbreviations
        'LA': 'LAK',      # Los Angeles Kings
        'MON': 'MTL',     # Montreal Canadiens  
        'S.J': 'SJS',     # San Jose Sharks
        'VEG': 'VGK',     # Vegas Golden Knights
        'WAS': 'WSH',     # Washington Capitals
        
        # Remove non-team entries
        '2TM': None,      # Multiple teams
        'FA': None,       # Free Agent
        'UFA': None,      # Unrestricted Free Agent
    }
    
    # Consolidate teams
    consolidated_rosters = defaultdict(lambda: {
        'forwards': set(),
        'defensemen': set(),
        'goalies': set()
    })
    
    for team_abbr, team_data in data['teams'].items():
        # Skip non-team entries
        if team_abbr in ['2TM', 'FA', 'UFA']:
            continue
            
        # Get the consolidated team name
        consolidated_team = team_consolidation.get(team_abbr, team_abbr)
        if consolidated_team is None:
            continue
            
        # Add players to consolidated roster
        for position in ['forwards', 'defensemen', 'goalies']:
            for player in team_data[position]:
                consolidated_rosters[consolidated_team][position].add(player)
    
    # Convert sets back to sorted lists
    for team in consolidated_rosters:
        for position in consolidated_rosters[team]:
            consolidated_rosters[team][position] = sorted(list(consolidated_rosters[team][position]))
    
    # Create new template
    template = {
        "season": "2025-26",
        "description": "Projected rosters extracted from Dobber, FantasyPros, and DtZ forecasts (consolidated)",
        "teams": {}
    }
    
    # Team name mapping
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
        'LAK': 'los-angeles-kings', 'ARI': 'arizona-coyotes', 'ANA': 'anaheim-ducks'
    }
    
    for team_abbr, positions in consolidated_rosters.items():
        if not positions['forwards'] and not positions['defensemen'] and not positions['goalies']:
            continue
            
        team_name = team_name_mapping.get(team_abbr, team_abbr.lower())
        
        template["teams"][team_abbr] = {
            "team_name": team_name,
            "forwards": positions['forwards'],
            "defensemen": positions['defensemen'],
            "goalies": positions['goalies'],
            "total_players": len(positions['forwards']) + len(positions['defensemen']) + len(positions['goalies'])
        }
    
    # Save consolidated data
    with open('projected_rosters_2025_26_consolidated.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"Consolidated rosters: {len(template['teams'])} teams")
    print("\nTeams:")
    for team in sorted(template['teams'].keys()):
        count = template['teams'][team]['total_players']
        print(f"  {team}: {count} players")
    
    # Show Edmonton example
    if 'EDM' in template['teams']:
        print(f"\nEDMONTON OILERS (consolidated):")
        edm = template['teams']['EDM']
        print(f"  Forwards: {len(edm['forwards'])}")
        print(f"  Defensemen: {len(edm['defensemen'])}")
        print(f"  Goalies: {len(edm['goalies'])}")
        print(f"  Total: {edm['total_players']}")

if __name__ == "__main__":
    fix_team_mapping()
