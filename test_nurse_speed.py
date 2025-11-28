#!/usr/bin/env python3
"""
Get ALL speed data for Darnell Nurse
"""

from nhlpy import NHLClient
import json
import requests

def get_nurse_speed_data():
    """Fetch all Edge speed data for Darnell Nurse"""
    
    print("=" * 100)
    print("  🏒 DARNELL NURSE - COMPLETE SPEED DATA")
    print("=" * 100)
    
    client = NHLClient()
    
    # Darnell Nurse - EDM Defenseman
    nurse_id = 8477498
    season = "20242025"
    
    print(f"\n📋 Player: Darnell Nurse")
    print(f"   Player ID: {nurse_id}")
    print(f"   Season: {season}")
    
    # ====================
    # 1. SKATING SPEED DETAIL
    # ====================
    
    print("\n" + "=" * 100)
    print("  ⚡ SKATING SPEED DATA")
    print("=" * 100)
    
    try:
        speed_data = client.edge.skater_skating_speed_detail(
            player_id=nurse_id,
            season=season
        )
        
        print("\n🔹 TOP SPEED EVENTS (Top 10 Fastest Moments)")
        print("─" * 100)
        
        top_speeds = speed_data.get('topSkatingSpeeds', [])
        
        if top_speeds:
            for i, event in enumerate(top_speeds, 1):
                speed_mph = event.get('skatingSpeed', {}).get('imperial')
                speed_kph = event.get('skatingSpeed', {}).get('metric')
                game_date = event.get('gameDate')
                period = event.get('periodDescriptor', {}).get('number')
                time_in_period = event.get('timeInPeriod')
                home_team = event.get('homeTeam', {}).get('abbrev')
                away_team = event.get('awayTeam', {}).get('abbrev')
                
                print(f"\n#{i} - {speed_mph} MPH ({speed_kph} KPH)")
                print(f"     Game: {away_team} @ {home_team} on {game_date}")
                print(f"     Time: Period {period} at {time_in_period}")
                print(f"     Link: {event.get('gameCenterLink')}")
        else:
            print("❌ No top speed events found")
        
        # Game-level speed details
        print("\n\n🔹 SPEED BY GAME (Recent Games)")
        print("─" * 100)
        
        speed_details = speed_data.get('skatingSpeedDetails', [])
        
        if speed_details:
            for game in speed_details:
                game_date = game.get('gameDate')
                max_speed_mph = game.get('maxSpeed', {}).get('imperial')
                max_speed_kph = game.get('maxSpeed', {}).get('metric')
                avg_speed_mph = game.get('avgSpeed', {}).get('imperial')
                avg_speed_kph = game.get('avgSpeed', {}).get('metric')
                home_team = game.get('homeTeam', {}).get('abbrev')
                away_team = game.get('awayTeam', {}).get('abbrev')
                
                print(f"\n📅 {game_date} - {away_team} @ {home_team}")
                print(f"   Max Speed: {max_speed_mph} MPH ({max_speed_kph} KPH)")
                print(f"   Avg Speed: {avg_speed_mph} MPH ({avg_speed_kph} KPH)")
        else:
            print("❌ No game-level speed details found")
        
        # Full JSON dump for reference
        print("\n\n🔹 COMPLETE RAW DATA")
        print("─" * 100)
        print(json.dumps(speed_data, indent=2))
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # ====================
    # 2. OVERALL SKATER DETAIL (includes speed summary)
    # ====================
    
    print("\n" + "=" * 100)
    print("  📊 OVERALL EDGE SUMMARY (All Metrics)")
    print("=" * 100)
    
    try:
        overall_data = client.edge.skater_detail(
            player_id=nurse_id,
            season=season
        )
        
        player = overall_data.get('player', {})
        skating_speed = overall_data.get('skatingSpeed', {})
        
        print(f"\n🏒 {player.get('firstName', {}).get('default')} {player.get('lastName', {}).get('default')}")
        print(f"   Position: {player.get('position')}")
        print(f"   Team: {player.get('team', {}).get('abbrev')}")
        print(f"   Number: {player.get('sweaterNumber')}")
        print(f"   Stats: {player.get('goals')}G, {player.get('assists')}A, {player.get('points')}P in {player.get('gamesPlayed')}GP")
        
        print(f"\n⚡ SKATING SPEED SUMMARY:")
        speed_max = skating_speed.get('speedMax', {})
        speed_avg = skating_speed.get('speedAvg', {})
        
        print(f"   Max Speed: {speed_max.get('imperial')} MPH ({speed_max.get('metric')} KPH)")
        print(f"   Percentile: {speed_max.get('percentile', 0) * 100:.1f}%")
        print(f"   League Avg Max: {speed_max.get('leagueAvg', {}).get('imperial')} MPH")
        
        print(f"\n   Avg Speed: {speed_avg.get('imperial')} MPH ({speed_avg.get('metric')} KPH)")
        print(f"   Percentile: {speed_avg.get('percentile', 0) * 100:.1f}%")
        print(f"   League Avg: {speed_avg.get('leagueAvg', {}).get('imperial')} MPH")
        
        # Check available seasons
        seasons = overall_data.get('seasonsWithEdgeStats', [])
        print(f"\n📅 Available Edge Data Seasons:")
        for s in seasons:
            print(f"   - {s.get('id')}: Game types {s.get('gameTypes')}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # ====================
    # 3. COMPARISON WITH OTHER DEFENSEMEN
    # ====================
    
    print("\n" + "=" * 100)
    print("  🔄 COMPARISON WITH OTHER EDM DEFENSEMEN")
    print("=" * 100)
    
    oilers_dmen = [
        {"id": 8477498, "name": "Darnell Nurse"},
        {"id": 8480803, "name": "Evan Bouchard"},
        {"id": 8479325, "name": "Mattias Ekholm"},
        {"id": 8476461, "name": "Brett Kulak"},
    ]
    
    print("\n📊 Top Speeds Comparison:")
    print("─" * 100)
    
    for dman in oilers_dmen:
        try:
            data = client.edge.skater_skating_speed_detail(
                player_id=dman['id'],
                season=season
            )
            top_speeds = data.get('topSkatingSpeeds', [])
            if top_speeds:
                max_speed = top_speeds[0].get('skatingSpeed', {}).get('imperial')
                print(f"   {dman['name']:<20} {max_speed} MPH")
            else:
                print(f"   {dman['name']:<20} No data")
        except:
            print(f"   {dman['name']:<20} Error fetching data")
    
    print("\n" + "=" * 100)
    print("  🎉 COMPLETE SPEED DATA RETRIEVED")
    print("=" * 100)

if __name__ == "__main__":
    get_nurse_speed_data()

