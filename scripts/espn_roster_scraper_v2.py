#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import re

def scrape_espn_roster_v2(team_abbr: str, team_name: str) -> Dict:
    """Scrape roster data from ESPN with better parsing"""
    
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
        
        # Look for player name links and extract data
        player_links = soup.find_all('a', href=lambda x: x and '/nhl/player/' in x)
        print(f"Found {len(player_links)} player links")
        
        roster_data = {
            'team': team_abbr,
            'team_name': team_name,
            'forwards': [],
            'defensemen': [],
            'goalies': []
        }
        
        # Process each player link
        for link in player_links:
            player_name = link.get_text().strip()
            if not player_name or len(player_name) < 2:
                continue
                
            # Find the parent row to get additional data
            row = link.find_parent('tr')
            if not row:
                continue
                
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            # Extract data from cells
            player_data = {'name': player_name}
            
            for i, cell in enumerate(cells):
                text = cell.get_text().strip()
                if not text or text == player_name:
                    continue
                    
                # Try to identify what type of data this is
                if re.match(r'^\d+$', text) and i == 0:  # Jersey number
                    player_data['number'] = text
                elif re.match(r'^\d+$', text) and 'age' not in player_data:  # Age
                    player_data['age'] = text
                elif re.match(r'^\d+-\d+$', text):  # Height
                    player_data['height'] = text
                elif re.match(r'^\d+$', text) and 'age' in player_data:  # Weight
                    player_data['weight'] = text
                elif text in ['L', 'R']:  # Shot hand
                    player_data['shot'] = text
                elif text in ['G']:  # Glove hand for goalies
                    player_data['glove'] = text
                elif re.match(r'^[A-Za-z\s,]+$', text) and len(text) > 3:  # Birth place
                    player_data['birth_place'] = text
                elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', text):  # Birth date
                    player_data['birth_date'] = text
            
            # Determine position based on context or try to infer
            # Look for position indicators in the row or nearby elements
            position = None
            
            # Check if this is in a forwards section
            section = row.find_parent(['div', 'section'])
            if section:
                section_text = section.get_text().lower()
                if 'forward' in section_text or 'center' in section_text or 'wing' in section_text:
                    position = 'F'
                elif 'defense' in section_text or 'defenseman' in section_text:
                    position = 'D'
                elif 'goalie' in section_text or 'goaltender' in section_text:
                    position = 'G'
            
            # If no position found, try to infer from player name patterns or other data
            if not position:
                # Check if it's a known goalie
                goalie_names = ['Skinner', 'Pickard', 'Tomkins', 'Jonsson', 'Day', 'Ungar']
                if any(goalie in player_name for goalie in goalie_names):
                    position = 'G'
                # Check if it's a known defenseman
                elif any(dman in player_name for dman in ['Bouchard', 'Nurse', 'Kulak', 'Walman', 'Stecher', 'Stillman']):
                    position = 'D'
                else:
                    position = 'F'  # Default to forward
            
            player_data['position'] = position
            
            # Add to appropriate list
            if position == 'F':
                roster_data['forwards'].append(player_data)
            elif position == 'D':
                roster_data['defensemen'].append(player_data)
            elif position == 'G':
                roster_data['goalies'].append(player_data)
        
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
    return scrape_espn_roster_v2("EDM", "edmonton-oilers")

if __name__ == "__main__":
    result = test_edmonton_oilers()
    if result:
        print("\n" + "="*50)
        print("EDMONTON OILERS ROSTER:")
        print("="*50)
        
        print("\nFORWARDS:")
        for player in result['forwards']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')}) - {player.get('shot', 'N/A')} shot")
        
        print("\nDEFENSEMEN:")
        for player in result['defensemen']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')}) - {player.get('shot', 'N/A')} shot")
        
        print("\nGOALIES:")
        for player in result['goalies']:
            print(f"  {player.get('number', 'N/A')} - {player.get('name', 'N/A')} ({player.get('position', 'N/A')}) - {player.get('glove', 'N/A')} glove")
        
        # Save to JSON for inspection
        with open('edmonton_oilers_roster_v2.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved detailed roster to edmonton_oilers_roster_v2.json")
    else:
        print("Failed to scrape roster")
