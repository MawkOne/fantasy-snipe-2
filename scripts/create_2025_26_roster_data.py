#!/usr/bin/env python3

import json
from typing import Dict, List

def create_manual_roster_template():
    """Create a manual roster template for 2025-26 season"""
    
    # This is a template structure for manually entering projected rosters
    template = {
        "season": "2025-26",
        "teams": {
            "EDM": {
                "team_name": "Edmonton Oilers",
                "projected_lineup": {
                    "forwards": {
                        "line_1": [
                            {"name": "Connor McDavid", "position": "C", "number": "97", "toi_tier": "Elite"},
                            {"name": "Leon Draisaitl", "position": "C", "number": "29", "toi_tier": "Elite"},
                            {"name": "Zach Hyman", "position": "L", "number": "18", "toi_tier": "Top Line"}
                        ],
                        "line_2": [
                            {"name": "Trent Frederic", "position": "C", "number": "10", "toi_tier": "Top Line"},
                            {"name": "Adam Henrique", "position": "C", "number": "19", "toi_tier": "Middle 6"},
                            {"name": "Andrew Mangiapane", "position": "L", "number": "88", "toi_tier": "Middle 6"}
                        ],
                        "line_3": [
                            {"name": "Mattias Janmark", "position": "C", "number": "13", "toi_tier": "Bottom 6"},
                            {"name": "Curtis Lazar", "position": "C", "number": "20", "toi_tier": "Bottom 6"},
                            {"name": "Kasperi Kapanen", "position": "R", "number": "42", "toi_tier": "Bottom 6"}
                        ],
                        "line_4": [
                            {"name": "Max Jones", "position": "L", "number": "46", "toi_tier": "Depth"},
                            {"name": "James Hamblin", "position": "L", "number": "52", "toi_tier": "Depth"},
                            {"name": "Jayden Grubbe", "position": "C", "number": "47", "toi_tier": "Depth"}
                        ],
                        "prospects": [
                            {"name": "Isaac Howard", "position": "L", "number": "53", "toi_tier": "Middle 6"},
                            {"name": "Quinn Hutson", "position": "R", "number": "28", "toi_tier": "Middle 6"},
                            {"name": "Roby Jarventie", "position": "L", "number": "15", "toi_tier": "Bottom 6"}
                        ]
                    },
                    "defensemen": {
                        "pair_1": [
                            {"name": "Evan Bouchard", "position": "D", "number": "2", "toi_tier": "Elite"},
                            {"name": "Darnell Nurse", "position": "D", "number": "25", "toi_tier": "Top Line"}
                        ],
                        "pair_2": [
                            {"name": "Brett Kulak", "position": "D", "number": "27", "toi_tier": "Middle 6"},
                            {"name": "Jake Walman", "position": "D", "number": "96", "toi_tier": "Middle 6"}
                        ],
                        "pair_3": [
                            {"name": "Troy Stecher", "position": "D", "number": "51", "toi_tier": "Bottom 6"},
                            {"name": "Riley Stillman", "position": "D", "number": "61", "toi_tier": "Bottom 6"}
                        ],
                        "depth": [
                            {"name": "Ty Emberson", "position": "D", "number": "49", "toi_tier": "Depth"},
                            {"name": "Alec Regula", "position": "D", "number": "75", "toi_tier": "Depth"},
                            {"name": "Atro Leppanen", "position": "D", "number": "37", "toi_tier": "Depth"}
                        ]
                    },
                    "goalies": [
                        {"name": "Stuart Skinner", "position": "G", "number": "74", "toi_tier": "Elite"},
                        {"name": "Calvin Pickard", "position": "G", "number": "30", "toi_tier": "Top Line"},
                        {"name": "Matt Tomkins", "position": "G", "number": "90", "toi_tier": "Depth"},
                        {"name": "Samuel Jonsson", "position": "G", "number": "34", "toi_tier": "Depth"},
                        {"name": "Nathaniel Day", "position": "G", "number": "40", "toi_tier": "Depth"},
                        {"name": "Connor Ungar", "position": "G", "number": "32", "toi_tier": "Depth"}
                    ]
                },
                "special_teams": {
                    "pp1": [
                        {"name": "Connor McDavid", "position": "C"},
                        {"name": "Leon Draisaitl", "position": "C"},
                        {"name": "Zach Hyman", "position": "L"},
                        {"name": "Evan Bouchard", "position": "D"},
                        {"name": "Darnell Nurse", "position": "D"}
                    ],
                    "pp2": [
                        {"name": "Trent Frederic", "position": "C"},
                        {"name": "Adam Henrique", "position": "C"},
                        {"name": "Andrew Mangiapane", "position": "L"},
                        {"name": "Brett Kulak", "position": "D"},
                        {"name": "Jake Walman", "position": "D"}
                    ],
                    "pk1": [
                        {"name": "Mattias Janmark", "position": "C"},
                        {"name": "Curtis Lazar", "position": "C"},
                        {"name": "Darnell Nurse", "position": "D"},
                        {"name": "Brett Kulak", "position": "D"}
                    ],
                    "pk2": [
                        {"name": "Adam Henrique", "position": "C"},
                        {"name": "Kasperi Kapanen", "position": "R"},
                        {"name": "Troy Stecher", "position": "D"},
                        {"name": "Riley Stillman", "position": "D"}
                    ]
                }
            }
        }
    }
    
    return template

def create_roster_ingestion_script():
    """Create a script to ingest manual roster data into BigQuery"""
    
    script_content = '''#!/usr/bin/env python3

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
'''
    
    with open('scripts/ingest_roster_data.py', 'w') as f:
        f.write(script_content)
    
    print("Created roster ingestion script: scripts/ingest_roster_data.py")

if __name__ == "__main__":
    print("Creating 2025-26 roster data template...")
    
    # Create the template
    template = create_manual_roster_template()
    
    # Save to JSON file
    with open('projected_rosters_2025_26_template.json', 'w') as f:
        json.dump(template, f, indent=2)
    
    print("Created template: projected_rosters_2025_26_template.json")
    
    # Create ingestion script
    create_roster_ingestion_script()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Edit projected_rosters_2025_26_template.json with all 32 teams")
    print("2. Add projected lineups from PuckPedia or other sources")
    print("3. Run: python3 scripts/ingest_roster_data.py projected_rosters_2025_26_template.json")
    print("4. Use the roster data in your Foster forecasting model")
    print("\nThis approach gives you:")
    print("- Complete control over projected lineups")
    print("- Integration with your existing BigQuery setup")
    print("- Data structure compatible with Foster methodology")
    print("- TOI tier assignments based on our data-driven analysis")
