#!/usr/bin/env python3
"""
Detailed test of NHL Edge API endpoints
Testing actual data retrieval
"""

from nhlpy import NHLClient
import json

def test_edge_endpoints():
    """Test all Edge API endpoints with real data"""
    
    print("=" * 80)
    print("NHL EDGE API DETAILED TEST")
    print("=" * 80)
    
    client = NHLClient()
    
    # Connor McDavid ID
    mcdavid_id = 8478402
    
    # Test 1: Skater Detail
    print("\n[TEST 1] Skater Detail - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_detail(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Skater Landing Page Data
    print("\n[TEST 2] Skater Landing - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_landing(player_id=mcdavid_id)
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Skating Speed
    print("\n[TEST 3] Skating Speed - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_skating_speed_detail(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: Skating Distance
    print("\n[TEST 4] Skating Distance - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_skating_distance_detail(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 5: Shot Speed
    print("\n[TEST 5] Shot Speed - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_shot_speed_detail(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 6: Zone Time
    print("\n[TEST 6] Zone Time - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_zone_time(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 7: Shot Location
    print("\n[TEST 7] Shot Location - Connor McDavid")
    print("-" * 80)
    try:
        data = client.edge.skater_shot_location_detail(player_id=mcdavid_id, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 8: Team Edge Data (Edmonton Oilers - Team ID 22)
    print("\n[TEST 8] Team Landing - Edmonton Oilers")
    print("-" * 80)
    try:
        data = client.edge.team_landing(team_id=22)
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 9: Team Skating Speed
    print("\n[TEST 9] Team Skating Speed - Edmonton Oilers")
    print("-" * 80)
    try:
        data = client.edge.team_skating_speed_detail(team_id=22, season="20242025")
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 10: Goalie Edge Stats (Igor Shesterkin - 8480045)
    print("\n[TEST 10] Goalie Landing - Igor Shesterkin")
    print("-" * 80)
    try:
        data = client.edge.goalie_landing(player_id=8480045)
        print("✅ SUCCESS!")
        print(f"Keys available: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        print(json.dumps(data, indent=2)[:1000])
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("DETAILED TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_edge_endpoints()

