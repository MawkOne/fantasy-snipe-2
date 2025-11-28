#!/usr/bin/env python3
"""
Test script to query NHL Edge API using nhlpy package
"""

from nhlpy import NHLClient
import json
from datetime import datetime

def test_edge_stats():
    """Test NHL Edge statistics endpoints"""
    
    print("=" * 60)
    print("NHL EDGE API TEST")
    print("=" * 60)
    
    client = NHLClient()
    
    # Test 1: Player Edge Stats (Connor McDavid - 8478402)
    print("\n[TEST 1] Connor McDavid Edge Stats")
    print("-" * 60)
    try:
        # Try to get edge stats
        edge_data = client.stats.player_edge_stats(player_id=8478402)
        print("✅ SUCCESS - Edge stats retrieved!")
        print(json.dumps(edge_data, indent=2)[:500])  # First 500 chars
    except AttributeError as e:
        print(f"❌ Method not available: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Check available methods on stats object
    print("\n[TEST 2] Available Stats Methods")
    print("-" * 60)
    stats_methods = [m for m in dir(client.stats) if not m.startswith('_')]
    print("Available methods:")
    for method in stats_methods:
        print(f"  - {method}")
    
    # Test 3: Try team edge stats
    print("\n[TEST 3] Team Edge Stats (Edmonton Oilers)")
    print("-" * 60)
    try:
        team_edge = client.stats.team_edge_stats(team_id=22)
        print("✅ SUCCESS - Team edge stats retrieved!")
        print(json.dumps(team_edge, indent=2)[:500])
    except AttributeError as e:
        print(f"❌ Method not available: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Check what Edge module exists
    print("\n[TEST 4] Check for Edge Module")
    print("-" * 60)
    if hasattr(client, 'edge'):
        print("✅ Edge module found!")
        edge_methods = [m for m in dir(client.edge) if not m.startswith('_')]
        print("Available edge methods:")
        for method in edge_methods:
            print(f"  - {method}")
    else:
        print("❌ No 'edge' module found on client")
    
    # Test 5: Try skater stats (regular stats)
    print("\n[TEST 5] Regular Skater Stats (Connor McDavid)")
    print("-" * 60)
    try:
        skater_stats = client.stats.player_summary_stats(
            player_id=8478402,
            season="20242025",
            game_type="2"
        )
        print("✅ SUCCESS - Skater stats retrieved!")
        print(json.dumps(skater_stats, indent=2)[:500])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 6: Check all available client modules
    print("\n[TEST 6] All Available Client Modules")
    print("-" * 60)
    client_modules = [m for m in dir(client) if not m.startswith('_')]
    print("Available modules on NHLClient:")
    for module in client_modules:
        print(f"  - {module}")
    
    # Test 7: Try to access raw edge API endpoint
    print("\n[TEST 7] Raw Edge API Endpoint Test")
    print("-" * 60)
    try:
        import requests
        # Try the edge API directly
        url = "https://api.nhle.com/stats/rest/en/skater/skatingsummary?cayenneExp=playerId=8478402"
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.ok:
            data = response.json()
            print("✅ SUCCESS - Direct Edge API call worked!")
            print(json.dumps(data, indent=2)[:800])
        else:
            print(f"❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_edge_stats()

