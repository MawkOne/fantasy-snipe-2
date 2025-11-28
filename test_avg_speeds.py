#!/usr/bin/env python3
"""
Check what average speed data is available in Edge API
"""

from nhlpy import NHLClient
import json

def check_average_speeds():
    """Check all available average speed metrics"""
    
    print("=" * 100)
    print("  🔬 CHECKING AVERAGE SPEED DATA AVAILABILITY")
    print("=" * 100)
    
    client = NHLClient()
    season = "20242025"
    
    # Test multiple players
    test_players = [
        {"id": 8478402, "name": "Connor McDavid"},
        {"id": 8477498, "name": "Darnell Nurse"},
        {"id": 8477406, "name": "Mattias Janmark"},
    ]
    
    for player in test_players:
        print(f"\n{'=' * 100}")
        print(f"  {player['name']}")
        print(f"{'=' * 100}")
        
        # Get overall detail which has speed summary
        overall = client.edge.skater_detail(
            player_id=player['id'],
            season=season
        )
        
        skating_speed = overall.get('skatingSpeed', {})
        
        print(f"\n📊 SPEED METRICS:")
        print("─" * 100)
        
        # Max speed
        speed_max = skating_speed.get('speedMax', {})
        print(f"\n1️⃣  MAX SPEED (Peak Burst):")
        print(f"    Value: {speed_max.get('imperial')} MPH ({speed_max.get('metric')} KPH)")
        print(f"    Percentile: {speed_max.get('percentile', 0) * 100:.1f}%")
        print(f"    League Avg: {speed_max.get('leagueAvg', {}).get('imperial')} MPH")
        
        # Average speed
        speed_avg = skating_speed.get('speedAvg', {})
        print(f"\n2️⃣  AVERAGE SPEED:")
        if speed_avg.get('imperial'):
            print(f"    Value: {speed_avg.get('imperial')} MPH ({speed_avg.get('metric')} KPH)")
            print(f"    Percentile: {speed_avg.get('percentile', 0) * 100:.1f}%")
            print(f"    League Avg: {speed_avg.get('leagueAvg', {}).get('imperial')} MPH")
        else:
            print(f"    ❌ Not available in data")
        
        # Check what other speed metrics exist
        print(f"\n3️⃣  ALL AVAILABLE SPEED KEYS:")
        for key in skating_speed.keys():
            print(f"    - {key}")
        
        # Get the detail endpoint too
        print(f"\n{'─' * 100}")
        print(f"SPEED DETAIL ENDPOINT:")
        print("─" * 100)
        
        speed_detail = client.edge.skater_skating_speed_detail(
            player_id=player['id'],
            season=season
        )
        
        # Check if there's per-game average
        speed_details = speed_detail.get('skatingSpeedDetails', [])
        print(f"\n4️⃣  PER-GAME SPEED DATA:")
        print(f"    Available games: {len(speed_details)}")
        
        if speed_details and len(speed_details) > 0:
            # Check first game structure
            sample = speed_details[0] if isinstance(speed_details[0], dict) else {}
            print(f"    Keys per game: {list(sample.keys()) if sample else 'Unknown structure'}")
            if sample:
                print(f"\n    Sample game:")
                print(json.dumps(sample, indent=6)[:500])
    
    # Summary of what's available
    print("\n" + "=" * 100)
    print("  📊 SUMMARY - AVERAGE SPEED DATA")
    print("=" * 100)
    
    print("""
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ WHAT AVERAGES ARE AVAILABLE:                                               │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                                            │
    │ ❓ SEASON AVERAGE SPEED:                                                   │
    │    - Appears in data structure but returns None/null                       │
    │    - May not be calculated by NHL's Edge system                            │
    │                                                                            │
    │ ✅ YOU CAN CALCULATE:                                                      │
    │    1. Average of top 10 peak speeds (peak burst average)                  │
    │    2. Approximate from distance/time data                                  │
    │       Formula: avg_speed = total_distance / total_time                     │
    │                                                                            │
    │ 📏 DISTANCE DATA:                                                          │
    │    - Total distance skated per game (in km/miles)                          │
    │    - Time on ice per game (in seconds)                                     │
    │    - Can derive approximate average speed from these                       │
    │                                                                            │
    └────────────────────────────────────────────────────────────────────────────┘
    """)

if __name__ == "__main__":
    check_average_speeds()

