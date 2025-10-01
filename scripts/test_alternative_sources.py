#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import time

def test_alternative_sources():
    """Test alternative sources for depth charts and rosters"""
    
    sources = [
        {
            "name": "EliteProspects Depth Chart",
            "url": "https://www.eliteprospects.com/team/52/edmonton-oilers",
            "description": "EliteProspects team page"
        },
        {
            "name": "HockeyDB Roster",
            "url": "https://www.hockeydb.com/ihdb/stats/leagues/seasons/teams/0000042025.html",
            "description": "HockeyDB 2024-25 roster"
        },
        {
            "name": "NHL.com Team Page",
            "url": "https://www.nhl.com/oilers/roster",
            "description": "Official NHL team roster"
        },
        {
            "name": "ESPN Roster",
            "url": "https://www.espn.com/nhl/team/roster/_/name/edm/edmonton-oilers",
            "description": "ESPN team roster"
        }
    ]
    
    results = {}
    
    for source in sources:
        print(f"\nTesting: {source['name']}")
        print(f"URL: {source['url']}")
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(source['url'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for player names
                player_indicators = ['McDavid', 'Draisaitl', 'Hyman', 'Bouchard', 'Nurse']
                found_players = []
                
                for player in player_indicators:
                    if player in response.text:
                        found_players.append(player)
                
                print(f"Found players: {found_players}")
                
                # Look for tables
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables")
                
                # Look for roster/depth chart indicators
                roster_indicators = ['roster', 'depth', 'lineup', 'forwards', 'defensemen', 'goalies']
                found_indicators = []
                
                page_text = response.text.lower()
                for indicator in roster_indicators:
                    if indicator in page_text:
                        found_indicators.append(indicator)
                
                print(f"Found indicators: {found_indicators}")
                
                results[source['name']] = {
                    'status': 'success',
                    'players_found': found_players,
                    'tables': len(tables),
                    'indicators': found_indicators
                }
                
            else:
                print(f"Failed: {response.status_code}")
                results[source['name']] = {'status': 'failed', 'code': response.status_code}
                
        except Exception as e:
            print(f"Error: {e}")
            results[source['name']] = {'status': 'error', 'error': str(e)}
        
        time.sleep(1)  # Be respectful
    
    print("\n" + "="*50)
    print("SUMMARY:")
    for name, result in results.items():
        if result['status'] == 'success':
            print(f"✅ {name}: Found {len(result['players_found'])} players, {result['tables']} tables")
        else:
            print(f"❌ {name}: {result['status']}")
    
    return results

if __name__ == "__main__":
    test_alternative_sources()
