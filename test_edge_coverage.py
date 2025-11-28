#!/usr/bin/env python3
"""
Test which players have Edge data available
Check if it's universal or selective
"""

from nhlpy import NHLClient
import json

def test_edge_coverage():
    """Test Edge data availability across different player types"""
    
    print("=" * 100)
    print("  🔬 EDGE DATA COVERAGE TEST - Who has Edge stats?")
    print("=" * 100)
    
    client = NHLClient()
    season = "20242025"
    
    # Test different player types
    test_players = [
        # Star players
        {"id": 8478402, "name": "Connor McDavid", "type": "Superstar", "team": "EDM"},
        {"id": 8479318, "name": "Auston Matthews", "type": "Star", "team": "TOR"},
        {"id": 8477492, "name": "Nathan MacKinnon", "type": "Star", "team": "COL"},
        
        # Good but not elite
        {"id": 8476453, "name": "Nikita Kucherov", "type": "Elite", "team": "TBL"},
        {"id": 8476945, "name": "Connor Hellebuyck", "type": "Goalie", "team": "WPG"},
        
        # Middle-tier players
        {"id": 8477406, "name": "Mattias Janmark", "type": "Middle-6", "team": "EDM"},
        {"id": 8478042, "name": "Viktor Arvidsson", "type": "Middle-6", "team": "EDM"},
        
        # Depth/4th liner
        {"id": 8475324, "name": "Corey Perry", "type": "Veteran 4th", "team": "EDM"},
        
        # Rookie/Young player
        {"id": 8482671, "name": "Connor Bedard", "type": "Rookie Star", "team": "CHI"},
        {"id": 8483808, "name": "Macklin Celebrini", "type": "Rookie", "team": "SJS"},
    ]
    
    results = {
        "has_edge_data": [],
        "no_edge_data": []
    }
    
    print("\n" + "=" * 100)
    print("  Testing Edge Data Availability...")
    print("=" * 100)
    
    for player in test_players:
        print(f"\n{'─' * 100}")
        print(f"🏒 {player['name']} ({player['type']}) - {player['team']}")
        print(f"{'─' * 100}")
        
        try:
            # Try to get Edge data
            edge_data = client.edge.skater_skating_speed_detail(
                player_id=player['id'], 
                season=season
            )
            
            # Check if there's actual data
            top_speeds = edge_data.get('topSkatingSpeeds', [])
            speed_details = edge_data.get('skatingSpeedDetails', [])
            
            if top_speeds or speed_details:
                print(f"✅ HAS EDGE DATA")
                print(f"   - Top speed events: {len(top_speeds)}")
                print(f"   - Games with speed data: {len(speed_details)}")
                
                if top_speeds:
                    max_speed = top_speeds[0].get('skatingSpeed', {}).get('imperial')
                    print(f"   - Max speed: {max_speed} MPH")
                
                results["has_edge_data"].append(player)
            else:
                print(f"⚠️  NO EDGE DATA (API returned empty)")
                results["no_edge_data"].append(player)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results["no_edge_data"].append(player)
    
    # Test if Edge data is per-game or season-wide
    print("\n" + "=" * 100)
    print("  📊 Checking Edge Data Availability by Season")
    print("=" * 100)
    
    print(f"\n🔹 Connor McDavid - Checking multiple seasons...")
    for test_season in ["20212022", "20222023", "20232024", "20242025"]:
        try:
            edge_data = client.edge.skater_detail(
                player_id=8478402,
                season=test_season
            )
            seasons_available = edge_data.get('seasonsWithEdgeStats', [])
            print(f"   - {test_season}: ✅ Available (Seasons in data: {[s['id'] for s in seasons_available]})")
        except Exception as e:
            print(f"   - {test_season}: ❌ {e}")
    
    # Summary
    print("\n" + "=" * 100)
    print("  📊 SUMMARY")
    print("=" * 100)
    
    print(f"\n✅ Players WITH Edge Data ({len(results['has_edge_data'])}):")
    for player in results["has_edge_data"]:
        print(f"   ✓ {player['name']} ({player['type']})")
    
    print(f"\n❌ Players WITHOUT Edge Data ({len(results['no_edge_data'])}):")
    for player in results["no_edge_data"]:
        print(f"   ✗ {player['name']} ({player['type']})")
    
    coverage_pct = len(results["has_edge_data"]) / len(test_players) * 100
    print(f"\n📈 Coverage Rate: {len(results['has_edge_data'])}/{len(test_players)} ({coverage_pct:.1f}%)")
    
    # Test what happens with a random/unknown player
    print("\n" + "=" * 100)
    print("  🔬 Testing Edge Data Requirements")
    print("=" * 100)
    
    print("""
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ EDGE DATA AVAILABILITY:                                                    │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                                            │
    │ Edge tracking started: 2021-2022 season                                    │
    │                                                                            │
    │ ✅ Available for:                                                          │
    │    - All NHL games (regular season + playoffs)                             │
    │    - All players who played in those games                                 │
    │    - Speed, distance, shots, zone time                                     │
    │                                                                            │
    │ ❌ NOT available for:                                                      │
    │    - Seasons before 2021-2022                                              │
    │    - Players who never played in NHL after 2021                            │
    │    - Minor league games                                                    │
    │                                                                            │
    │ 📊 Data Quality:                                                           │
    │    - Not every player may have "notable" top speeds tracked                │
    │    - Slower players might have fewer tracked speed events                  │
    │    - But ALL players have baseline Edge data if they played                │
    │                                                                            │
    └────────────────────────────────────────────────────────────────────────────┘
    """)
    
    print("\n" + "=" * 100)
    print("  🎉 COVERAGE TEST COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    test_edge_coverage()

