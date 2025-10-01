#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import time

def test_frozenpool_scraping():
    """Test if we can scrape from FrozenPool"""
    
    url = "https://frozenpool.dobbersports.com/frozenpool_depthchart.php?team=EDM"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        print(f"Testing FrozenPool scraping for: {url}")
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for depth chart content
            depth_chart = soup.find('div', class_='depth-chart') or soup.find('table', class_='depth-chart')
            if depth_chart:
                print("Found depth chart content!")
                print(depth_chart.get_text()[:500] + "...")
            else:
                print("No depth chart found, checking for any tables...")
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables")
                for i, table in enumerate(tables[:3]):  # Show first 3 tables
                    print(f"Table {i+1}: {table.get_text()[:200]}...")
            
            # Look for player names
            player_links = soup.find_all('a', href=lambda x: x and 'player' in x.lower())
            print(f"Found {len(player_links)} player links")
            
            if player_links:
                print("Sample player links:")
                for link in player_links[:5]:
                    print(f"  - {link.get_text().strip()}: {link.get('href')}")
            
            return True
            
        else:
            print(f"Failed to access: {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_frozenpool_scraping()
    print(f"\nScraping test {'SUCCESSFUL' if success else 'FAILED'}")
