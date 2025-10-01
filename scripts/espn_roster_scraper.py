#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re

def scrape_espn_roster(team_abbr: str, team_name: str) -> Dict:
    """Scrape roster data from ESPN"""
    
    url = f"https://www.espn.com/nhl/team/roster/_/name/{team_abbr}/{team_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.espn.com/nhl/",
    }
    
    try:
        print(f"Scraping ESPN roster for {team_name} ({team_abbr})")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all roster tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        roster_data = {
            'team': team_abbr,
            'team_name': team_name,
            'forwards': [],
            'defensemen': [],
            'goalies': []
        }
        
        for i, table in enumerate(tables):
            print(f"\nProcessing table {i+1}:")
            
            # Get table headers
            headers = []
            header_row = table.find('thead')
            if header_row:
                headers = [th.get_text().strip() for th in header_row.find_all('th')]
            else:
                # Try first row as headers
                first_row = table.find('tr')
                if first_row:
                    headers = [td.get_text().strip() for td in first_row.find_all(['th', 'td'])]
            
            print(f"Headers: {headers}")
            
            # Process table rows
            rows = table.find_all('tr')[1:] if header_row else table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:  # Need at least name, position, number
                    continue
                
                # Extract player data
                player_data = {}
                for j, cell in enumerate(cells):
                    if j < len(headers):
                        header = headers[j].lower()
                        text = cell.get_text().strip()
                        
                        # Clean up the text
                        if header in ['name', 'player']:
                            # Remove position from name if it's there
                            name = re.sub(r'\s+[A-Z]+$', '', text)
                            player_data['name'] = name
                        elif header in ['pos', 'position']:
                            player_data['position'] = text
                        elif header in ['#', 'num', 'number']:
                            player_data['number'] = text
                        elif header in ['age']:
                            player_data['age'] = text
                        elif header in ['ht', 'height']:
                            player_data['height'] = text
                        elif header in ['wt', 'weight']:
                            player_data['weight'] = text
                        elif header in ['gp', 'games']:
                            player_data['gp'] = text
                        elif header in ['g', 'goals']:
                            player_data['goals'] = text
                        elif header in ['a', 'assists']:
                            player_data['assists'] = text
                        elif header in ['pts', 'points']:
                            player_data['points'] = text
                        else:
                            player_data[header] = text
                
                # Determine position and add to appropriate list
                if 'position' in player_data:
                    pos = player_data['position'].upper()
                    if 'F' in pos or 'C' in pos or 'LW' in pos or 'RW' in pos:
                        roster_data['forwards'].append(player_data)
                    elif 'D' in pos or 'DEF' in pos:
                        roster_data['defensemen'].append(player_data)
                    elif 'G' in pos or 'GOAL' in pos:
                        roster_data['goalies'].append(player_data)
                    else:
                        # Try to infer from name or other data
                        if 'name' in player_data:
                            roster_data['forwards'].append(player_data)  # Default to forward
        
        print(f"\nRoster Summary:")
        print(f"Forwards: {len(roster_data['forwards'])}")
        print(f"Defensemen: {len(roster_data['defensemen'])}")
        print(f"Goalies: {len(roster_data['goalies'])}")
        
        return roster_data
        
    except Exception as e:
        print(f"Error scraping {team_name}: {e}")
        return None

def test_edmonton_oilers():
    """Test with Edmonton Oilers"""
    return scrape_espn_roster("EDM", "edmonton-oilers")

if __name__ == "__main__":
    result = test_edmonton_oilers()
    if result:
        print("\n" + "="*50)
        print("EDMONTON OILERS ROSTER:")
        print("="*50)
        
        print("\nFORWARDS:")
        for player in result['forwards']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')})")
        
        print("\nDEFENSEMEN:")
        for player in result['defensemen']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')})")
        
        print("\nGOALIES:")
        for player in result['goalies']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')})")
        
        # Save to JSON for inspection
        with open('edmonton_oilers_roster.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved detailed roster to edmonton_oilers_roster.json")
    else:
        print("Failed to scrape roster")
