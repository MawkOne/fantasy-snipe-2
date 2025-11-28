#!/usr/bin/env python3
"""
Get shot velocity data for EDM defensemen
"""

from nhlpy import NHLClient
import json

def get_dmen_shot_velocity():
    """Fetch shot velocity for EDM defensemen"""
    
    print("=" * 100)
    print("  🏒 EDM DEFENSEMEN - SHOT VELOCITY DATA")
    print("=" * 100)
    
    client = NHLClient()
    season = "20242025"
    
    defensemen = [
        {"id": 8477498, "name": "Darnell Nurse"},
        {"id": 8480803, "name": "Evan Bouchard"},
        {"id": 8479325, "name": "Mattias Ekholm"},
        {"id": 8476461, "name": "Brett Kulak"},
    ]
    
    all_shot_data = []
    
    for dman in defensemen:
        print(f"\n{'=' * 100}")
        print(f"  {dman['name'].upper()}")
        print(f"{'=' * 100}")
        
        try:
            shot_data = client.edge.skater_shot_speed_detail(
                player_id=dman['id'],
                season=season
            )
            
            hardest_shots = shot_data.get('hardestShots', [])
            
            if hardest_shots:
                print(f"\n🔥 TOP 10 HARDEST SHOTS:")
                print("─" * 100)
                
                speeds = []
                for i, shot in enumerate(hardest_shots, 1):
                    speed_mph = shot.get('shotSpeed', {}).get('imperial')
                    speed_kph = shot.get('shotSpeed', {}).get('metric')
                    game_date = shot.get('gameDate')
                    period = shot.get('periodDescriptor', {}).get('number')
                    time = shot.get('timeInPeriod')
                    home = shot.get('homeTeam', {}).get('abbrev')
                    away = shot.get('awayTeam', {}).get('abbrev')
                    
                    speeds.append(speed_mph)
                    
                    print(f"#{i:<3} {speed_mph} MPH ({speed_kph} KPH)")
                    print(f"     {away} @ {home} on {game_date} - P{period} at {time}")
                
                # Calculate stats
                max_shot = max(speeds)
                avg_shot = sum(speeds) / len(speeds)
                
                all_shot_data.append({
                    'name': dman['name'],
                    'max_shot': max_shot,
                    'avg_top_10': avg_shot,
                    'shots': speeds
                })
                
                print(f"\n📊 SUMMARY:")
                print(f"   Max shot: {max_shot} MPH")
                print(f"   Avg of top 10: {avg_shot:.2f} MPH")
                print(f"   Range: {min(speeds):.2f} - {max(speeds):.2f} MPH")
                
            else:
                print("❌ No shot speed data available")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    # Comparison
    print(f"\n\n{'=' * 100}")
    print(f"  ⚔️  SHOT VELOCITY COMPARISON")
    print(f"{'=' * 100}")
    
    # Sort by max shot speed
    all_shot_data.sort(key=lambda x: x['max_shot'], reverse=True)
    
    print(f"\n{'Rank':<6} {'Player':<20} {'Max Shot':<15} {'Avg Top 10':<15} {'Power':<15}")
    print("─" * 100)
    
    for i, player in enumerate(all_shot_data, 1):
        # Power tier
        if player['max_shot'] >= 95:
            power = "💥 Cannon"
        elif player['max_shot'] >= 90:
            power = "🔥 Heavy"
        elif player['max_shot'] >= 85:
            power = "⚡ Good"
        else:
            power = "🏒 Average"
        
        print(f"{i:<6} {player['name']:<20} {player['max_shot']:.2f} MPH      "
              f"{player['avg_top_10']:.2f} MPH      {power}")
    
    # Analysis
    print(f"\n{'=' * 100}")
    print(f"  💡 SHOT POWER ANALYSIS")
    print(f"{'=' * 100}")
    
    if all_shot_data:
        hardest_shooter = all_shot_data[0]
        avg_max_shot = sum(p['max_shot'] for p in all_shot_data) / len(all_shot_data)
        
        print(f"\n🎯 Key Insights:")
        print(f"   • Hardest shooter: {hardest_shooter['name']} at {hardest_shooter['max_shot']} MPH")
        print(f"   • Team avg max shot: {avg_max_shot:.2f} MPH")
        print(f"   • Shot advantage: {hardest_shooter['max_shot'] - avg_max_shot:.2f} MPH harder than avg")
        
        # Who's the point shot threat
        point_shot_threats = [p for p in all_shot_data if p['max_shot'] >= 90]
        print(f"\n🚀 Point Shot Threats (90+ MPH):")
        for p in point_shot_threats:
            print(f"   ✓ {p['name']} - {p['max_shot']} MPH")
        
        if not point_shot_threats:
            print(f"   ⚠️  No defensemen with 90+ MPH shot (may struggle on PP)")
    
    # Save data
    output = {
        'team': 'Edmonton Oilers',
        'position': 'Defense',
        'season': season,
        'players': all_shot_data
    }
    
    with open('edm_dmen_shot_velocity.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Data saved to: edm_dmen_shot_velocity.json")
    
    print("\n" + "=" * 100)
    print("  ✅ SHOT VELOCITY DATA COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    get_dmen_shot_velocity()

