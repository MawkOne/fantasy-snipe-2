#!/usr/bin/env python3

import requests
import json
from typing import Dict, List, Optional

def test_yahoo_fantasy_api():
    """Test Yahoo Fantasy Sports API for NHL data"""
    
    # Yahoo Fantasy Sports API endpoints
    base_url = "https://fantasysports.yahooapis.com/fantasy/v2"
    
    # We'll need OAuth2 authentication, but let's first test if we can access public data
    print("Testing Yahoo Fantasy Sports API...")
    
    # Test 1: Try to access league data (might require authentication)
    try:
        # This is a sample endpoint - we'd need proper authentication
        url = f"{base_url}/league/414.l.123456/teams"
        print(f"Testing URL: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("Authentication required - this is expected")
        elif response.status_code == 200:
            print("Success! Got data without authentication")
            return response.json()
        else:
            print(f"Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing Yahoo API: {e}")
    
    return None

def test_yahoo_public_api():
    """Test Yahoo's public API endpoints"""
    
    # Try Yahoo's public sports API
    endpoints = [
        "https://query1.finance.yahoo.com/v8/finance/chart/NHL",
        "https://sports.yahoo.com/nhl/teams/edmonton-oilers/roster/",
        "https://api.sportsdata.io/v3/nhl/scores/json/teams",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting: {endpoint}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
            
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("Success! This endpoint is accessible")
                if 'json' in response.headers.get('content-type', ''):
                    try:
                        data = response.json()
                        print(f"JSON data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    except:
                        print("Response is not JSON")
                else:
                    print("Response is HTML/text")
            else:
                print(f"Failed: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_yahoo_sports_scraping():
    """Test scraping Yahoo Sports directly"""
    
    url = "https://sports.yahoo.com/nhl/teams/edmonton-oilers/roster/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        print(f"\nTesting Yahoo Sports scraping: {url}")
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for player data
            player_elements = soup.find_all(['a', 'span', 'div'], string=lambda text: text and any(name in text for name in ['McDavid', 'Draisaitl', 'Hyman', 'Bouchard', 'Nurse']))
            print(f"Found {len(player_elements)} player elements")
            
            # Look for tables
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")
            
            # Look for roster-specific elements
            roster_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['roster', 'player', 'team']))
            print(f"Found {len(roster_elements)} roster elements")
            
            return True
        else:
            print(f"Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("YAHOO API TESTING")
    print("="*60)
    
    # Test 1: Fantasy API
    print("\n1. Testing Yahoo Fantasy Sports API:")
    test_yahoo_fantasy_api()
    
    # Test 2: Public APIs
    print("\n2. Testing Yahoo Public APIs:")
    test_yahoo_public_api()
    
    # Test 3: Direct scraping
    print("\n3. Testing Yahoo Sports Scraping:")
    test_yahoo_sports_scraping()
    
    print("\n" + "="*60)
    print("YAHOO API TESTING COMPLETE")
    print("="*60)
