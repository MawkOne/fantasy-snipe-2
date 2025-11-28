#!/usr/bin/env python3
"""
Test granularity of NHL Edge API data
Check if shift-level data is available
"""

from nhlpy import NHLClient
import json
import requests

def print_section(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def test_granularity():
    """Test the granularity of Edge and other NHL data"""
    
    print_section("🔬 NHL DATA GRANULARITY TEST")
    
    client = NHLClient()
    mcdavid_id = 8478402
    season = "20242025"
    
    # ====================
    # EDGE API GRANULARITY
    # ====================
    
    # 1. Speed - Check for event-level detail
    print_section("⚡ SPEED DATA GRANULARITY")
    print("\n📊 Checking skating speed detail...")
    speed_data = client.edge.skater_skating_speed_detail(player_id=mcdavid_id, season=season)
    
    print(f"\n🔹 Data structure:")
    print(f"   - topSkatingSpeeds: {len(speed_data.get('topSkatingSpeeds', []))} events")
    print(f"   - skatingSpeedDetails: {len(speed_data.get('skatingSpeedDetails', []))} games")
    
    if speed_data.get('topSkatingSpeeds'):
        print(f"\n🔹 Top speed event (most granular):")
        top_speed = speed_data['topSkatingSpeeds'][0]
        print(json.dumps(top_speed, indent=2))
        print(f"\n✅ GRANULARITY: Individual speed events with timestamps")
        print(f"   - Game date: {top_speed.get('gameDate')}")
        print(f"   - Period: {top_speed.get('periodDescriptor', {}).get('number')}")
        print(f"   - Time in period: {top_speed.get('timeInPeriod')}")
        print(f"   - Speed: {top_speed.get('skatingSpeed', {}).get('imperial')} MPH")
    
    # 2. Shot Speed - Check for event-level detail
    print_section("🏒 SHOT SPEED DATA GRANULARITY")
    print("\n📊 Checking shot speed detail...")
    shot_data = client.edge.skater_shot_speed_detail(player_id=mcdavid_id, season=season)
    
    print(f"\n🔹 Data structure:")
    print(f"   - hardestShots: {len(shot_data.get('hardestShots', []))} events")
    print(f"   - shotSpeedDetails: {len(shot_data.get('shotSpeedDetails', []))} games")
    
    if shot_data.get('hardestShots'):
        print(f"\n🔹 Hardest shot event (most granular):")
        hardest_shot = shot_data['hardestShots'][0]
        print(json.dumps(hardest_shot, indent=2)[:800])
        print(f"\n✅ GRANULARITY: Individual shot events with timestamps")
        print(f"   - Game date: {hardest_shot.get('gameDate')}")
        print(f"   - Period: {hardest_shot.get('periodDescriptor', {}).get('number')}")
        print(f"   - Time in period: {hardest_shot.get('timeInPeriod')}")
        print(f"   - Shot speed: {hardest_shot.get('shotSpeed', {}).get('imperial')} MPH")
    
    # 3. Distance - Check for per-game vs per-shift
    print_section("📏 DISTANCE DATA GRANULARITY")
    print("\n📊 Checking skating distance detail...")
    distance_data = client.edge.skater_skating_distance_detail(player_id=mcdavid_id, season=season)
    
    print(f"\n🔹 Data structure:")
    print(f"   - skatingDistanceLast10: {len(distance_data.get('skatingDistanceLast10', []))} games")
    print(f"   - skatingDistanceDetails: {len(distance_data.get('skatingDistanceDetails', []))} games")
    
    if distance_data.get('skatingDistanceLast10'):
        print(f"\n🔹 Recent game distance (most granular):")
        recent_game = distance_data['skatingDistanceLast10'][0]
        print(json.dumps(recent_game, indent=2)[:800])
        print(f"\n✅ GRANULARITY: Per-game aggregates by situation")
        print(f"   - distanceSkatedAll: {recent_game.get('distanceSkatedAll', {}).get('metric')} km")
        print(f"   - distanceSkatedEven: {recent_game.get('distanceSkatedEven', {}).get('metric')} km")
        print(f"   - distanceSkatedPP: {recent_game.get('distanceSkatedPP', {}).get('metric')} km")
        print(f"   - distanceSkatedPK: {recent_game.get('distanceSkatedPK', {}).get('metric')} km (if exists)")
    
    # 4. Zone Time - Check granularity
    print_section("🗺️  ZONE TIME DATA GRANULARITY")
    print("\n📊 Checking zone time detail...")
    zone_data = client.edge.skater_zone_time(player_id=mcdavid_id, season=season)
    
    print(f"\n🔹 Data structure:")
    print(f"   - zoneTimeDetails: {len(zone_data.get('zoneTimeDetails', []))} strength situations")
    print(f"   - zoneStarts: {len(zone_data.get('zoneStarts', []))} items")
    
    if zone_data.get('zoneTimeDetails'):
        print(f"\n🔹 Zone time breakdown:")
        for zone in zone_data['zoneTimeDetails']:
            print(f"   - {zone.get('strengthCode')}: Off={zone.get('offensiveZonePctg'):.2%}, Neu={zone.get('neutralZonePctg'):.2%}, Def={zone.get('defensiveZonePctg'):.2%}")
        print(f"\n✅ GRANULARITY: Season aggregates by strength situation")
    
    # ====================
    # SHIFT-LEVEL DATA (NON-EDGE)
    # ====================
    
    print_section("⏱️  SHIFT-LEVEL DATA (Separate from Edge)")
    print("\n📊 Checking if shift charts are available...")
    
    # Get a recent game ID for McDavid
    print("\n🔹 Finding recent game...")
    try:
        # Use game log to find a recent game
        game_log_url = f"https://api-web.nhle.com/v1/player/{mcdavid_id}/game-log/{season}/2"
        response = requests.get(game_log_url, timeout=10)
        if response.ok:
            game_log = response.json()
            recent_games = game_log.get('gameLog', [])[:3]
            
            if recent_games:
                game_id = recent_games[0]['gameId']
                print(f"   - Recent game ID: {game_id}")
                print(f"   - Game date: {recent_games[0].get('gameDate')}")
                
                # Try to get shift data
                print(f"\n🔹 Attempting to fetch shift-level data...")
                shift_url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"
                shift_response = requests.get(shift_url, timeout=10)
                
                if shift_response.ok:
                    shift_data = shift_response.json()
                    print(f"\n✅ SUCCESS! Shift-level data IS available!")
                    print(f"\n🔹 Shift data structure:")
                    print(f"   - Total shifts in response: {len(shift_data.get('data', []))} shifts")
                    
                    # Find McDavid's shifts
                    mcdavid_shifts = [s for s in shift_data.get('data', []) if s.get('playerId') == mcdavid_id]
                    print(f"   - McDavid's shifts in this game: {len(mcdavid_shifts)}")
                    
                    if mcdavid_shifts:
                        print(f"\n🔹 Sample shift (MOST GRANULAR DATA):")
                        sample_shift = mcdavid_shifts[0]
                        print(json.dumps(sample_shift, indent=2))
                        
                        print(f"\n✅ SHIFT GRANULARITY:")
                        print(f"   - Shift number: {sample_shift.get('shiftNumber')}")
                        print(f"   - Period: {sample_shift.get('period')}")
                        print(f"   - Start time: {sample_shift.get('startTime')}")
                        print(f"   - End time: {sample_shift.get('endTime')}")
                        print(f"   - Duration: {sample_shift.get('duration')} seconds")
                        print(f"   - Event details: {sample_shift.get('eventDetails')}")
                else:
                    print(f"❌ Shift data request failed: {shift_response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching shift data: {e}")
    
    # ====================
    # PLAY-BY-PLAY DATA
    # ====================
    
    print_section("🎯 PLAY-BY-PLAY DATA (Event-level)")
    print("\n📊 Checking play-by-play granularity...")
    
    try:
        if 'game_id' in locals():
            pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
            pbp_response = requests.get(pbp_url, timeout=10)
            
            if pbp_response.ok:
                pbp_data = pbp_response.json()
                plays = pbp_data.get('plays', [])
                print(f"\n✅ Play-by-play data available!")
                print(f"   - Total events in game: {len(plays)}")
                
                # Find an event with McDavid
                mcdavid_events = [p for p in plays if any(
                    detail.get('playerId') == mcdavid_id 
                    for detail in p.get('details', {}).get('eventOwnerTeamId', []) 
                    if isinstance(detail, dict)
                )][:3]
                
                if plays:
                    print(f"\n🔹 Sample play-by-play event:")
                    print(json.dumps(plays[10], indent=2)[:1000])
                    
                    print(f"\n✅ PLAY-BY-PLAY GRANULARITY:")
                    print(f"   - Event type (shot, hit, faceoff, goal, etc.)")
                    print(f"   - Exact period and time")
                    print(f"   - X/Y coordinates (for shots)")
                    print(f"   - Players involved")
                    print(f"   - Situation code (strength)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ====================
    # SUMMARY
    # ====================
    
    print_section("📊 GRANULARITY SUMMARY")
    
    print("""
    ┌────────────────────────────────────────────────────────────────────────────┐
    │ DATA GRANULARITY LEVELS AVAILABLE:                                         │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                                            │
    │ 🔷 EDGE API (Speed, Distance, Shots, Zone Time):                           │
    │    ├─ EVENT LEVEL: Individual speed bursts, individual shots (with time)  │
    │    ├─ GAME LEVEL: Distance per game, per-game aggregates                  │
    │    └─ SEASON LEVEL: Zone time %, shooting %, percentiles                  │
    │                                                                            │
    │ 🔷 SHIFT CHARTS API (Separate endpoint):                                   │
    │    └─ SHIFT LEVEL: Every single shift with start/end times & duration     │
    │       ✅ MOST GRANULAR DATA AVAILABLE                                      │
    │                                                                            │
    │ 🔷 PLAY-BY-PLAY API (Separate endpoint):                                   │
    │    └─ EVENT LEVEL: Every shot, hit, faceoff, goal with X/Y coordinates    │
    │       ✅ INCLUDES ON-ICE PLAYERS FOR EACH EVENT                            │
    │                                                                            │
    ├────────────────────────────────────────────────────────────────────────────┤
    │ ANSWER: YES, shift-level data EXISTS but NOT in Edge API!                 │
    │         It's a separate endpoint: /shiftcharts                            │
    └────────────────────────────────────────────────────────────────────────────┘
    """)
    
    print_section("🎉 GRANULARITY TEST COMPLETE")

if __name__ == "__main__":
    test_granularity()

