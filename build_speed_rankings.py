#!/usr/bin/env python3
"""
Build speed rankings for NHL players
Shows who has the speed advantage
"""

from nhlpy import NHLClient
import json

def build_team_speed_profile(team_id, team_name, season="20242025"):
    """Build speed profile for an entire team"""
    
    print(f"\n{'=' * 100}")
    print(f"  🏃 {team_name.upper()} - SPEED PROFILE")
    print(f"{'=' * 100}")
    
    client = NHLClient()
    
    # Get team roster (using a recent game to find players)
    # For demo, using known EDM players
    if team_name == "Edmonton Oilers":
        roster = [
            # Forwards
            {"id": 8478402, "name": "Connor McDavid", "pos": "F"},
            {"id": 8477934, "name": "Leon Draisaitl", "pos": "F"},
            {"id": 8478550, "name": "Zach Hyman", "pos": "F"},
            {"id": 8479344, "name": "Ryan Nugent-Hopkins", "pos": "F"},
            {"id": 8477406, "name": "Mattias Janmark", "pos": "F"},
            {"id": 8478042, "name": "Viktor Arvidsson", "pos": "F"},
            {"id": 8476899, "name": "Evander Kane", "pos": "F"},
            {"id": 8479325, "name": "Adam Henrique", "pos": "F"},
            {"id": 8475324, "name": "Corey Perry", "pos": "F"},
            
            # Defense
            {"id": 8480803, "name": "Evan Bouchard", "pos": "D"},
            {"id": 8477498, "name": "Darnell Nurse", "pos": "D"},
            {"id": 8479325, "name": "Mattias Ekholm", "pos": "D"},
            {"id": 8476461, "name": "Brett Kulak", "pos": "D"},
            {"id": 8478851, "name": "Troy Stecher", "pos": "D"},
            {"id": 8478319, "name": "Ty Emberson", "pos": "D"},
        ]
    else:
        print("Demo only works for Edmonton Oilers")
        return None
    
    speed_data = []
    
    print(f"\n📊 Fetching speed data for {len(roster)} players...")
    print("─" * 100)
    
    for player in roster:
        try:
            edge_data = client.edge.skater_skating_speed_detail(
                player_id=player['id'],
                season=season
            )
            
            top_speeds = edge_data.get('topSkatingSpeeds', [])
            
            if top_speeds:
                # Get max and average of top speeds
                speeds_mph = [s.get('skatingSpeed', {}).get('imperial', 0) for s in top_speeds]
                max_speed = max(speeds_mph) if speeds_mph else 0
                avg_top_speed = sum(speeds_mph) / len(speeds_mph) if speeds_mph else 0
                
                # Get overall detail for percentile
                overall = client.edge.skater_detail(player_id=player['id'], season=season)
                percentile = overall.get('skatingSpeed', {}).get('speedMax', {}).get('percentile', 0)
                
                speed_data.append({
                    'name': player['name'],
                    'pos': player['pos'],
                    'max_speed': max_speed,
                    'avg_top_speed': avg_top_speed,
                    'percentile': percentile * 100,
                    'top_speed_count': len(speeds_mph)
                })
                
                print(f"✓ {player['name']:<25} {max_speed:.2f} MPH")
            else:
                print(f"✗ {player['name']:<25} No speed data")
                
        except Exception as e:
            print(f"✗ {player['name']:<25} Error: {e}")
    
    # Sort by max speed
    speed_data.sort(key=lambda x: x['max_speed'], reverse=True)
    
    # Display rankings
    print(f"\n{'=' * 100}")
    print(f"  🏆 {team_name.upper()} - SPEED RANKINGS")
    print(f"{'=' * 100}")
    
    print(f"\n{'Rank':<6} {'Player':<25} {'Pos':<5} {'Max Speed':<12} {'Avg Top 10':<12} {'Percentile':<12}")
    print("─" * 100)
    
    for i, player in enumerate(speed_data, 1):
        # Speed tier
        if player['percentile'] >= 90:
            tier = "🔥 Elite"
        elif player['percentile'] >= 75:
            tier = "⚡ Fast"
        elif player['percentile'] >= 50:
            tier = "🏃 Avg+"
        else:
            tier = "🐢 Below Avg"
        
        print(f"{i:<6} {player['name']:<25} {player['pos']:<5} "
              f"{player['max_speed']:.2f} MPH    "
              f"{player['avg_top_speed']:.2f} MPH    "
              f"{player['percentile']:.1f}%   {tier}")
    
    # Speed analysis
    print(f"\n{'=' * 100}")
    print(f"  📊 SPEED ANALYSIS")
    print(f"{'=' * 100}")
    
    forwards = [p for p in speed_data if p['pos'] == 'F']
    defensemen = [p for p in speed_data if p['pos'] == 'D']
    
    if forwards:
        avg_fwd_speed = sum(p['max_speed'] for p in forwards) / len(forwards)
        fastest_fwd = forwards[0]
        print(f"\n🏒 FORWARDS:")
        print(f"   Fastest: {fastest_fwd['name']} at {fastest_fwd['max_speed']:.2f} MPH")
        print(f"   Average max speed: {avg_fwd_speed:.2f} MPH")
        print(f"   Speed advantage: {fastest_fwd['max_speed'] - avg_fwd_speed:.2f} MPH faster than team avg")
    
    if defensemen:
        avg_def_speed = sum(p['max_speed'] for p in defensemen) / len(defensemen)
        fastest_def = defensemen[0]
        print(f"\n🛡️  DEFENSE:")
        print(f"   Fastest: {fastest_def['name']} at {fastest_def['max_speed']:.2f} MPH")
        print(f"   Average max speed: {avg_def_speed:.2f} MPH")
        print(f"   Speed gap (F-D): {avg_fwd_speed - avg_def_speed:.2f} MPH")
    
    # Matchup insights
    print(f"\n{'=' * 100}")
    print(f"  ⚔️  MATCHUP INSIGHTS")
    print(f"{'=' * 100}")
    
    print(f"""
    💡 SPEED ADVANTAGE SCENARIOS:
    
    1. Top speed forwards (23+ MPH):
       {', '.join([p['name'] for p in forwards if p['max_speed'] >= 23])}
       → Can beat most defenders in foot races
    
    2. Defensemen who can match elite speed (22+ MPH):
       {', '.join([p['name'] for p in defensemen if p['max_speed'] >= 22])}
       → Can keep up with fast forwards
    
    3. Speed mismatches (slower defenders):
       {', '.join([p['name'] for p in defensemen if p['max_speed'] < 22])}
       → Vulnerable to speed rushes, need good positioning
    
    4. Team speed tier: {"Elite speed team" if avg_fwd_speed >= 22.5 else "Above average speed" if avg_fwd_speed >= 22 else "Average speed"}
    """)
    
    # Save to JSON
    output_file = f"{team_name.replace(' ', '_').lower()}_speed_profile.json"
    with open(output_file, 'w') as f:
        json.dump({
            'team': team_name,
            'season': season,
            'players': speed_data,
            'summary': {
                'avg_forward_speed': avg_fwd_speed if forwards else 0,
                'avg_defense_speed': avg_def_speed if defensemen else 0,
                'fastest_player': speed_data[0]['name'] if speed_data else None
            }
        }, f, indent=2)
    
    print(f"\n💾 Full data saved to: {output_file}")
    
    return speed_data

if __name__ == "__main__":
    print("=" * 100)
    print("  🏒 NHL TEAM SPEED PROFILE BUILDER")
    print("  'Hockey is a game of speed' - Speed Rankings & Matchup Analysis")
    print("=" * 100)
    
    # Build speed profile
    speed_profile = build_team_speed_profile(22, "Edmonton Oilers")
    
    print("\n" + "=" * 100)
    print("  ✅ SPEED PROFILE COMPLETE")
    print("=" * 100)

