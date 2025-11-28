#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def update_rosters_from_raw_db():
    """Update projected rosters to match raw database team assignments"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("UPDATING PROJECTED ROSTERS TO MATCH RAW DATABASE TEAM ASSIGNMENTS")
    print("="*80)
    
    # Get all players from raw database with their current teams
    query = """
    SELECT 
        p.full_name as player_name,
        t.tri_code as current_team,
        p.position,
        CASE 
            WHEN p.position = 'G' THEN 'Goalie'
            WHEN p.position IN ('C', 'L', 'R') THEN 'Forward'
            WHEN p.position = 'D' THEN 'Defenseman'
            ELSE 'Unknown'
        END as position_type
    FROM `fantasy-snipe-ai.nhl_raw.players` p
    JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON p.current_team_id = t.id
    WHERE p.full_name IS NOT NULL
    AND t.tri_code IS NOT NULL
    ORDER BY t.tri_code, p.full_name
    """
    
    print("Loading current team assignments from raw database...")
    raw_players = client.query(query).to_dataframe()
    
    print(f"Found {len(raw_players)} players in raw database")
    
    # Get current projected rosters
    query2 = """
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    ORDER BY team_abbr, player_name
    """
    
    print("Loading current projected rosters...")
    projected_rosters = client.query(query2).to_dataframe()
    
    print(f"Found {len(projected_rosters)} players in projected rosters")
    
    # Check for mismatches
    print("\nChecking for team assignment mismatches...")
    print("=" * 60)
    
    mismatches = []
    for _, proj_player in projected_rosters.iterrows():
        raw_match = raw_players[
            (raw_players['player_name'] == proj_player['player_name'])
        ]
        
        if not raw_match.empty:
            raw_team = raw_match.iloc[0]['current_team']
            if proj_player['team_abbr'] != raw_team:
                mismatches.append({
                    'player_name': proj_player['player_name'],
                    'projected_team': proj_player['team_abbr'],
                    'raw_team': raw_team,
                    'position_type': proj_player['position_type'],
                    'toi_tier': proj_player['toi_tier']
                })
    
    print(f"Found {len(mismatches)} players with team mismatches:")
    for mismatch in mismatches:
        print(f"{mismatch['player_name']:25} | {mismatch['projected_team']:4} → {mismatch['raw_team']:4} | {mismatch['position_type']:8} | {mismatch['toi_tier']}")
    
    # Check for players in raw DB but missing from projected rosters
    print(f"\nChecking for players in raw DB but missing from projected rosters...")
    print("=" * 60)
    
    missing_players = []
    for _, raw_player in raw_players.iterrows():
        proj_match = projected_rosters[
            (projected_rosters['player_name'] == raw_player['player_name'])
        ]
        
        if proj_match.empty:
            missing_players.append(raw_player)
    
    print(f"Found {len(missing_players)} players in raw DB but missing from projected rosters:")
    for player in missing_players[:20]:  # Show first 20
        print(f"{player['player_name']:25} | {player['current_team']:4} | {player['position_type']:8}")
    
    if len(missing_players) > 20:
        print(f"... and {len(missing_players) - 20} more")
    
    # Key players to highlight
    key_players = ['Mitch Marner', 'Mikko Rantanen', 'Jakob Chychrun', 'Sam Bennett', 'Ivan Provorov']
    
    print(f"\nKey players status:")
    print("=" * 30)
    for player_name in key_players:
        raw_match = raw_players[raw_players['player_name'] == player_name]
        proj_match = projected_rosters[projected_rosters['player_name'] == player_name]
        
        if not raw_match.empty:
            raw_team = raw_match.iloc[0]['current_team']
            if not proj_match.empty:
                proj_team = proj_match.iloc[0]['team_abbr']
                status = "MATCH" if raw_team == proj_team else "MISMATCH"
                print(f"{player_name:20} | Raw: {raw_team:4} | Proj: {proj_team:4} | {status}")
            else:
                print(f"{player_name:20} | Raw: {raw_team:4} | Proj: MISSING | MISSING")
        else:
            print(f"{player_name:20} | Raw: MISSING | Proj: {'FOUND' if not proj_match.empty else 'MISSING'} | UNKNOWN")
    
    print(f"\n✅ Analysis complete!")
    print(f"Total mismatches: {len(mismatches)}")
    print(f"Missing players: {len(missing_players)}")
    print("\nTo fix these issues, we would need to update the projected_rosters_2025_26 table")
    print("to match the current team assignments from the raw database.")

if __name__ == "__main__":
    update_rosters_from_raw_db()
