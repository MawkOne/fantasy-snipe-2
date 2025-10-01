#!/usr/bin/env python3

import requests
import json
from typing import Dict, List, Optional
import time

def get_nhl_roster_comprehensive(team_id: int) -> Dict:
    """Get comprehensive roster data from NHL API"""
    
    # NHL API endpoints
    base_url = "https://statsapi.web.nhl.com/api/v1"
    
    try:
        print(f"Getting comprehensive roster data for team {team_id}")
        
        # Get team info
        team_url = f"{base_url}/teams/{team_id}"
        team_response = requests.get(team_url, timeout=10)
        team_data = team_response.json()
        
        team_info = team_data['teams'][0]
        team_name = team_info['name']
        team_abbr = team_info['abbreviation']
        
        print(f"Team: {team_name} ({team_abbr})")
        
        # Get roster
        roster_url = f"{base_url}/teams/{team_id}/roster"
        roster_response = requests.get(roster_url, timeout=10)
        roster_data = roster_response.json()
        
        roster_info = {
            'team_id': team_id,
            'team_name': team_name,
            'team_abbr': team_abbr,
            'forwards': [],
            'defensemen': [],
            'goalies': []
        }
        
        # Process roster
        for person in roster_data['roster']:
            player_id = person['person']['id']
            player_name = person['person']['fullName']
            position = person['position']['type']
            position_code = person['position']['code']
            jersey_number = person.get('jerseyNumber', 'N/A')
            
            # Get detailed player info
            player_url = f"{base_url}/people/{player_id}"
            player_response = requests.get(player_url, timeout=10)
            player_data = player_response.json()
            
            player_info = player_data['people'][0]
            
            player_details = {
                'player_id': player_id,
                'name': player_name,
                'position': position,
                'position_code': position_code,
                'jersey_number': jersey_number,
                'birth_date': player_info.get('birthDate'),
                'birth_city': player_info.get('birthCity'),
                'birth_country': player_info.get('birthCountry'),
                'nationality': player_info.get('nationality'),
                'height': player_info.get('height'),
                'weight': player_info.get('weight'),
                'shoots_catches': player_info.get('shootsCatches'),
                'active': player_info.get('active', True)
            }
            
            # Categorize by position
            if position == 'Forward':
                roster_info['forwards'].append(player_details)
            elif position == 'Defenseman':
                roster_info['defensemen'].append(player_details)
            elif position == 'Goalie':
                roster_info['goalies'].append(player_details)
        
        print(f"Roster Summary:")
        print(f"Forwards: {len(roster_info['forwards'])}")
        print(f"Defensemen: {len(roster_info['defensemen'])}")
        print(f"Goalies: {len(roster_info['goalies'])}")
        
        return roster_info
        
    except Exception as e:
        print(f"Error getting roster for team {team_id}: {e}")
        return None

def get_all_teams_rosters():
    """Get rosters for all NHL teams"""
    
    # Get all teams first
    teams_url = "https://statsapi.web.nhl.com/api/v1/teams"
    teams_response = requests.get(teams_url, timeout=10)
    teams_data = teams_response.json()
    
    all_rosters = {}
    
    for team in teams_data['teams']:
        team_id = team['id']
        team_name = team['name']
        team_abbr = team['abbreviation']
        
        print(f"\nProcessing {team_name} ({team_abbr}) - ID: {team_id}")
        
        roster = get_nhl_roster_comprehensive(team_id)
        if roster:
            all_rosters[team_abbr] = roster
        
        time.sleep(1)  # Be respectful to the API
    
    return all_rosters

def test_edmonton_oilers():
    """Test with Edmonton Oilers (team ID 22)"""
    return get_nhl_roster_comprehensive(22)

if __name__ == "__main__":
    print("="*60)
    print("NHL API COMPREHENSIVE ROSTER TEST")
    print("="*60)
    
    # Test with Edmonton Oilers
    result = test_edmonton_oilers()
    
    if result:
        print("\n" + "="*50)
        print(f"{result['team_name'].upper()} ROSTER:")
        print("="*50)
        
        print("\nFORWARDS:")
        for player in result['forwards']:
            print(f"  #{player['jersey_number']} - {player['name']} ({player['position_code']}) - {player['shoots_catches']} shot")
        
        print("\nDEFENSEMEN:")
        for player in result['defensemen']:
            print(f"  #{player['jersey_number']} - {player['name']} ({player['position_code']}) - {player['shoots_catches']} shot")
        
        print("\nGOALIES:")
        for player in result['goalies']:
            print(f"  #{player['jersey_number']} - {player['name']} ({player['position_code']}) - {player['shoots_catches']} catch")
        
        # Save to JSON
        with open('edmonton_oilers_nhl_api.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved detailed roster to edmonton_oilers_nhl_api.json")
    else:
        print("Failed to get roster data")
