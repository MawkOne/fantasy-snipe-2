#!/usr/bin/env python3

import json
from google.cloud import bigquery
from typing import Dict, List

def save_rosters_to_bigquery():
    """Save the consolidated 2025-26 rosters to BigQuery nhl_projections dataset"""
    
    # Load the consolidated roster data
    with open('projected_rosters_2025_26_consolidated.json', 'r') as f:
        roster_data = json.load(f)
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    # Ensure schema exists
    print("Creating schema if it doesn't exist...")
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_projections`").result()
    
    # Create the projected rosters table
    print("Creating projected_rosters_2025_26 table...")
    client.query("""
        CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26` (
            season STRING,
            team_abbr STRING,
            team_name STRING,
            player_name STRING,
            position STRING,
            position_type STRING,
            jersey_number STRING,
            toi_tier STRING,
            line_position STRING,
            special_teams_pp1 BOOL,
            special_teams_pp2 BOOL,
            special_teams_pk1 BOOL,
            special_teams_pk2 BOOL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """).result()
    
    # Prepare data for insertion
    rows = []
    
    for team_abbr, team_info in roster_data['teams'].items():
        team_name = team_info['team_name']
        
        # Process forwards
        for i, player_name in enumerate(team_info['forwards']):
            # Assign TOI tier based on our data-driven analysis
            if i < 3:  # Top 3 forwards
                toi_tier = 'Elite'
                line_position = 'line_1'
            elif i < 6:  # Next 3 forwards
                toi_tier = 'Top Line'
                line_position = 'line_2'
            elif i < 12:  # Next 6 forwards
                toi_tier = 'Middle 6'
                line_position = 'line_3' if i < 9 else 'line_4'
            else:  # Rest
                toi_tier = 'Depth'
                line_position = 'prospects'
            
            # Determine position (simplified - would need more detailed data)
            position = 'F'  # Forward
            position_type = 'Forward'
            
            # Special teams assignments (simplified)
            special_teams_pp1 = i < 3  # Top 3 forwards get PP1
            special_teams_pp2 = 3 <= i < 6  # Next 3 forwards get PP2
            special_teams_pk1 = 6 <= i < 8  # Some middle 6 get PK1
            special_teams_pk2 = 8 <= i < 10  # Some middle 6 get PK2
            
            rows.append({
                'season': roster_data['season'],
                'team_abbr': team_abbr,
                'team_name': team_name,
                'player_name': player_name,
                'position': position,
                'position_type': position_type,
                'jersey_number': '',  # Would need to be filled in manually
                'toi_tier': toi_tier,
                'line_position': line_position,
                'special_teams_pp1': special_teams_pp1,
                'special_teams_pp2': special_teams_pp2,
                'special_teams_pk1': special_teams_pk1,
                'special_teams_pk2': special_teams_pk2
            })
        
        # Process defensemen
        for i, player_name in enumerate(team_info['defensemen']):
            # Assign TOI tier based on our data-driven analysis
            if i < 2:  # Top 2 defensemen
                toi_tier = 'Elite'
                line_position = 'pair_1'
            elif i < 4:  # Next 2 defensemen
                toi_tier = 'Top Line'
                line_position = 'pair_2'
            elif i < 6:  # Next 2 defensemen
                toi_tier = 'Middle 6'
                line_position = 'pair_3'
            else:  # Rest
                toi_tier = 'Depth'
                line_position = 'depth'
            
            position = 'D'  # Defenseman
            position_type = 'Defenseman'
            
            # Special teams assignments (defensemen more likely to get special teams)
            special_teams_pp1 = i < 2  # Top 2 defensemen get PP1
            special_teams_pp2 = 2 <= i < 4  # Next 2 defensemen get PP2
            special_teams_pk1 = i < 2  # Top 2 defensemen get PK1
            special_teams_pk2 = 2 <= i < 4  # Next 2 defensemen get PK2
            
            rows.append({
                'season': roster_data['season'],
                'team_abbr': team_abbr,
                'team_name': team_name,
                'player_name': player_name,
                'position': position,
                'position_type': position_type,
                'jersey_number': '',
                'toi_tier': toi_tier,
                'line_position': line_position,
                'special_teams_pp1': special_teams_pp1,
                'special_teams_pp2': special_teams_pp2,
                'special_teams_pk1': special_teams_pk1,
                'special_teams_pk2': special_teams_pk2
            })
        
        # Process goalies
        for i, player_name in enumerate(team_info['goalies']):
            if i == 0:  # First goalie
                toi_tier = 'Elite'
                line_position = 'starter'
            else:  # Backup goalies
                toi_tier = 'Top Line'
                line_position = 'backup'
            
            position = 'G'  # Goalie
            position_type = 'Goalie'
            
            # Goalies don't get special teams
            special_teams_pp1 = False
            special_teams_pp2 = False
            special_teams_pk1 = False
            special_teams_pk2 = False
            
            rows.append({
                'season': roster_data['season'],
                'team_abbr': team_abbr,
                'team_name': team_name,
                'player_name': player_name,
                'position': position,
                'position_type': position_type,
                'jersey_number': '',
                'toi_tier': toi_tier,
                'line_position': line_position,
                'special_teams_pp1': special_teams_pp1,
                'special_teams_pp2': special_teams_pp2,
                'special_teams_pk1': special_teams_pk1,
                'special_teams_pk2': special_teams_pk2
            })
    
    # Load data into BigQuery
    print(f"Loading {len(rows)} roster entries into BigQuery...")
    
    job = client.load_table_from_json(
        rows,
        "fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26",
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
    )
    job.result()
    
    print("✅ Successfully loaded roster data into BigQuery!")
    
    # Verify the data
    print("\nVerifying data...")
    query = """
        SELECT 
            team_abbr,
            COUNT(*) as total_players,
            COUNT(CASE WHEN position_type = 'Forward' THEN 1 END) as forwards,
            COUNT(CASE WHEN position_type = 'Defenseman' THEN 1 END) as defensemen,
            COUNT(CASE WHEN position_type = 'Goalie' THEN 1 END) as goalies,
            COUNT(CASE WHEN toi_tier = 'Elite' THEN 1 END) as elite_players
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        GROUP BY team_abbr
        ORDER BY total_players DESC
        LIMIT 10
    """
    
    results = client.query(query).result()
    
    print("\nTop 10 teams by roster size:")
    print("Team | Total | F | D | G | Elite")
    print("-" * 40)
    for row in results:
        print(f"{row.team_abbr:4} | {row.total_players:5} | {row.forwards:1} | {row.defensemen:1} | {row.goalies:1} | {row.elite_players:5}")
    
    # Show Edmonton example
    print(f"\nEdmonton Oilers roster:")
    edm_query = """
        SELECT 
            player_name,
            position_type,
            toi_tier,
            line_position,
            special_teams_pp1,
            special_teams_pp2,
            special_teams_pk1,
            special_teams_pk2
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
        WHERE team_abbr = 'EDM'
        ORDER BY position_type, toi_tier, player_name
    """
    
    edm_results = client.query(edm_query).result()
    
    current_position = None
    for row in edm_results:
        if row.position_type != current_position:
            current_position = row.position_type
            print(f"\n{current_position.upper()}S:")
        
        special_teams = []
        if row.special_teams_pp1:
            special_teams.append("PP1")
        if row.special_teams_pp2:
            special_teams.append("PP2")
        if row.special_teams_pk1:
            special_teams.append("PK1")
        if row.special_teams_pk2:
            special_teams.append("PK2")
        
        special_teams_str = f" ({', '.join(special_teams)})" if special_teams else ""
        
        print(f"  {row.player_name} - {row.toi_tier} ({row.line_position}){special_teams_str}")

if __name__ == "__main__":
    save_rosters_to_bigquery()
