#!/usr/bin/env python3

import json
from google.cloud import bigquery
from typing import Dict, List

def ingest_roster_data(roster_file: str):
    """Ingest manual roster data into BigQuery"""
    
    client = bigquery.Client()
    
    # Create schema if it doesn't exist
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_projections`").result()
    
    # Create roster table
    client.query("""
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26` (
            season STRING,
            team_abbr STRING,
            team_name STRING,
            player_name STRING,
            position STRING,
            jersey_number STRING,
            toi_tier STRING,
            line_position STRING,
            special_teams_pp1 BOOL,
            special_teams_pp2 BOOL,
            special_teams_pk1 BOOL,
            special_teams_pk2 BOOL
        )
    """).result()
    
    # Load roster data
    with open(roster_file, 'r') as f:
        roster_data = json.load(f)
    
    rows = []
    
    for team_abbr, team_data in roster_data['teams'].items():
        lineup = team_data['projected_lineup']
        special_teams = team_data['special_teams']
        
        # Process forwards
        for line_name, players in lineup['forwards'].items():
            for player in players:
                row = {
                    'season': roster_data['season'],
                    'team_abbr': team_abbr,
                    'team_name': team_data['team_name'],
                    'player_name': player['name'],
                    'position': player['position'],
                    'jersey_number': player['number'],
                    'toi_tier': player['toi_tier'],
                    'line_position': line_name,
                    'special_teams_pp1': any(p['name'] == player['name'] for p in special_teams['pp1']),
                    'special_teams_pp2': any(p['name'] == player['name'] for p in special_teams['pp2']),
                    'special_teams_pk1': any(p['name'] == player['name'] for p in special_teams['pk1']),
                    'special_teams_pk2': any(p['name'] == player['name'] for p in special_teams['pk2'])
                }
                rows.append(row)
        
        # Process defensemen
        for pair_name, players in lineup['defensemen'].items():
            for player in players:
                row = {
                    'season': roster_data['season'],
                    'team_abbr': team_abbr,
                    'team_name': team_data['team_name'],
                    'player_name': player['name'],
                    'position': player['position'],
                    'jersey_number': player['number'],
                    'toi_tier': player['toi_tier'],
                    'line_position': pair_name,
                    'special_teams_pp1': any(p['name'] == player['name'] for p in special_teams['pp1']),
                    'special_teams_pp2': any(p['name'] == player['name'] for p in special_teams['pp2']),
                    'special_teams_pk1': any(p['name'] == player['name'] for p in special_teams['pk1']),
                    'special_teams_pk2': any(p['name'] == player['name'] for p in special_teams['pk2'])
                }
                rows.append(row)
        
        # Process goalies
        for player in lineup['goalies']:
            row = {
                'season': roster_data['season'],
                'team_abbr': team_abbr,
                'team_name': team_data['team_name'],
                'player_name': player['name'],
                'position': player['position'],
                'jersey_number': player['number'],
                'toi_tier': player['toi_tier'],
                'line_position': 'starter' if player['toi_tier'] == 'Elite' else 'backup',
                'special_teams_pp1': False,
                'special_teams_pp2': False,
                'special_teams_pk1': False,
                'special_teams_pk2': False
            }
            rows.append(row)
    
    # Load into BigQuery
    job = client.load_table_from_json(
        rows, 
        "fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26",
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
    )
    job.result()
    
    print(f"Loaded {len(rows)} roster entries into BigQuery")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ingest_roster_data.py <roster_file.json>")
        sys.exit(1)
    
    ingest_roster_data(sys.argv[1])
