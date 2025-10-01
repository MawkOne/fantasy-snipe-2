#!/usr/bin/env python3

import json
from google.cloud import bigquery
from typing import Dict, List
import pandas as pd

def generate_toi_forecasts():
    """Generate TOI forecasts for every team using data-driven TOI tiers"""
    
    client = bigquery.Client()
    
    print("="*60)
    print("GENERATING TOI FORECASTS FOR ALL TEAMS")
    print("="*60)
    
    # Get our data-driven TOI tier analysis from 2024-25
    print("Loading data-driven TOI tier analysis...")
    
    toi_tier_query = """
    WITH team_performance AS (
        SELECT 
            t.tri_code as team,
            ROUND((AVG(pst.cf_pct_weighted) * 0.3 + AVG(pst.gf60) * 0.4 + AVG(CASE WHEN pst.toi_minutes / pst.games_played >= 18 THEN pst.toi_minutes / pst.games_played END) * 0.3), 1) as team_strength
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position != "G"
        GROUP BY t.tri_code
    ),
    contention_cycle AS (
        SELECT 
            team,
            team_strength,
            CASE 
                WHEN team_strength >= 40 THEN "Win Now"
                WHEN team_strength >= 37 THEN "Window Closing" 
                WHEN team_strength >= 34 THEN "Window Soon"
                ELSE "Rebuilding"
            END as cycle_stage
        FROM team_performance
    )
    SELECT * FROM contention_cycle
    """
    
    contention_data = client.query(toi_tier_query).to_dataframe()
    contention_dict = dict(zip(contention_data['team'], contention_data['cycle_stage']))
    
    print(f"Loaded contention cycle data for {len(contention_dict)} teams")
    
    # Data-driven TOI tier definitions based on our 2024-25 analysis
    toi_tier_ranges = {
        'Win Now': {
            'Elite': {'min_toi': 20.0, 'max_toi': 27.0, 'avg_toi': 22.0},
            'Top Line': {'min_toi': 18.0, 'max_toi': 19.9, 'avg_toi': 18.9},
            'Middle 6': {'min_toi': 15.0, 'max_toi': 17.9, 'avg_toi': 16.3},
            'Bottom 6': {'min_toi': 12.0, 'max_toi': 14.9, 'avg_toi': 13.6},
            'Depth': {'min_toi': 5.8, 'max_toi': 11.9, 'avg_toi': 10.4}
        },
        'Window Closing': {
            'Elite': {'min_toi': 20.0, 'max_toi': 27.0, 'avg_toi': 21.8},
            'Top Line': {'min_toi': 18.0, 'max_toi': 19.9, 'avg_toi': 19.0},
            'Middle 6': {'min_toi': 15.0, 'max_toi': 17.9, 'avg_toi': 16.6},
            'Bottom 6': {'min_toi': 12.0, 'max_toi': 14.9, 'avg_toi': 13.5},
            'Depth': {'min_toi': 5.8, 'max_toi': 11.9, 'avg_toi': 10.3}
        },
        'Window Soon': {
            'Elite': {'min_toi': 20.0, 'max_toi': 27.0, 'avg_toi': 22.1},
            'Top Line': {'min_toi': 18.0, 'max_toi': 19.9, 'avg_toi': 18.8},
            'Middle 6': {'min_toi': 15.0, 'max_toi': 17.9, 'avg_toi': 16.6},
            'Bottom 6': {'min_toi': 12.0, 'max_toi': 14.9, 'avg_toi': 13.8},
            'Depth': {'min_toi': 5.8, 'max_toi': 11.9, 'avg_toi': 10.2}
        },
        'Rebuilding': {
            'Elite': {'min_toi': 20.0, 'max_toi': 27.0, 'avg_toi': 22.2},
            'Top Line': {'min_toi': 18.0, 'max_toi': 19.9, 'avg_toi': 18.4},
            'Middle 6': {'min_toi': 15.0, 'max_toi': 17.9, 'avg_toi': 16.1},
            'Bottom 6': {'min_toi': 12.0, 'max_toi': 14.9, 'avg_toi': 13.4},
            'Depth': {'min_toi': 5.8, 'max_toi': 11.9, 'avg_toi': 11.7}
        }
    }
    
    # Get all projected rosters
    print("Loading projected rosters...")
    roster_query = """
    SELECT 
        team_abbr,
        team_name,
        player_name,
        position_type,
        toi_tier,
        line_position,
        special_teams_pp1,
        special_teams_pp2,
        special_teams_pk1,
        special_teams_pk2
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    ORDER BY team_abbr, position_type, toi_tier, player_name
    """
    
    roster_data = client.query(roster_query).to_dataframe()
    
    print(f"Loaded roster data for {roster_data['team_abbr'].nunique()} teams")
    
    # Generate TOI forecasts
    print("Generating TOI forecasts...")
    
    forecasts = []
    
    for team_abbr in sorted(roster_data['team_abbr'].unique()):
        team_roster = roster_data[roster_data['team_abbr'] == team_abbr]
        team_name = team_roster['team_name'].iloc[0]
        
        # Get team's contention cycle stage
        cycle_stage = contention_dict.get(team_abbr, 'Window Soon')
        
        print(f"\n{team_abbr} ({team_name}) - {cycle_stage}")
        
        # Process each player
        for _, player in team_roster.iterrows():
            toi_tier = player['toi_tier']
            position_type = player['position_type']
            
            # Get TOI range for this tier and contention cycle
            tier_data = toi_tier_ranges[cycle_stage][toi_tier]
            
            # Calculate projected TOI
            projected_toi = tier_data['avg_toi']
            
            # Adjust for special teams (add 1-2 minutes for PP/PK)
            special_teams_minutes = 0
            if player['special_teams_pp1']:
                special_teams_minutes += 2.0  # PP1 gets more time
            elif player['special_teams_pp2']:
                special_teams_minutes += 1.5  # PP2 gets less time
            
            if player['special_teams_pk1']:
                special_teams_minutes += 1.5  # PK1 gets more time
            elif player['special_teams_pk2']:
                special_teams_minutes += 1.0  # PK2 gets less time
            
            # Total projected TOI
            total_projected_toi = projected_toi + special_teams_minutes
            
            # Calculate games played (82 games for most players, adjust for depth)
            if toi_tier == 'Depth':
                projected_gp = 30  # Depth players play fewer games
            elif toi_tier == 'Bottom 6':
                projected_gp = 60  # Bottom 6 players miss some games
            else:
                projected_gp = 82  # Top players play most games
            
            # Calculate total TOI for season
            total_season_toi = total_projected_toi * projected_gp
            
            forecast = {
                'season': '2025-26',
                'team_abbr': team_abbr,
                'team_name': team_name,
                'player_name': player['player_name'],
                'position_type': position_type,
                'toi_tier': toi_tier,
                'line_position': player['line_position'],
                'contention_cycle': cycle_stage,
                'projected_toi_per_game': round(total_projected_toi, 1),
                'projected_games_played': projected_gp,
                'total_season_toi': round(total_season_toi, 1),
                'special_teams_pp1': player['special_teams_pp1'],
                'special_teams_pp2': player['special_teams_pp2'],
                'special_teams_pk1': player['special_teams_pk1'],
                'special_teams_pk2': player['special_teams_pk2'],
                'special_teams_minutes': round(special_teams_minutes, 1)
            }
            
            forecasts.append(forecast)
    
    # Create BigQuery table for TOI forecasts
    print("\nCreating TOI forecasts table in BigQuery...")
    
    client.query("""
        CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26` (
            season STRING,
            team_abbr STRING,
            team_name STRING,
            player_name STRING,
            position_type STRING,
            toi_tier STRING,
            line_position STRING,
            contention_cycle STRING,
            projected_toi_per_game FLOAT64,
            projected_games_played INT64,
            total_season_toi FLOAT64,
            special_teams_pp1 BOOL,
            special_teams_pp2 BOOL,
            special_teams_pk1 BOOL,
            special_teams_pk2 BOOL,
            special_teams_minutes FLOAT64,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """).result()
    
    # Load forecasts into BigQuery
    print(f"Loading {len(forecasts)} TOI forecasts into BigQuery...")
    
    job = client.load_table_from_json(
        forecasts,
        "fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26",
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
    )
    job.result()
    
    print("✅ Successfully loaded TOI forecasts into BigQuery!")
    
    # Generate summary report
    print("\n" + "="*60)
    print("TOI FORECAST SUMMARY REPORT")
    print("="*60)
    
    # Team summary
    team_summary_query = """
    SELECT 
        team_abbr,
        team_name,
        contention_cycle,
        COUNT(*) as total_players,
        COUNT(CASE WHEN toi_tier = 'Elite' THEN 1 END) as elite_players,
        ROUND(AVG(projected_toi_per_game), 1) as avg_toi_per_game,
        ROUND(SUM(total_season_toi), 0) as total_team_toi,
        ROUND(SUM(projected_games_played), 0) as total_team_gp
    FROM `fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26`
    GROUP BY team_abbr, team_name, contention_cycle
    ORDER BY avg_toi_per_game DESC
    """
    
    team_summary = client.query(team_summary_query).to_dataframe()
    
    print("\nTop 10 Teams by Average TOI per Game:")
    print("Team | Cycle Stage | Players | Elite | Avg TOI | Total TOI")
    print("-" * 70)
    for _, row in team_summary.head(10).iterrows():
        print(f"{row.team_abbr:4} | {row.contention_cycle:12} | {row.total_players:7} | {row.elite_players:5} | {row.avg_toi_per_game:7} | {row.total_team_toi:9}")
    
    # Contention cycle analysis
    cycle_summary_query = """
    SELECT 
        contention_cycle,
        COUNT(DISTINCT team_abbr) as teams,
        COUNT(*) as total_players,
        ROUND(AVG(projected_toi_per_game), 1) as avg_toi_per_game,
        COUNT(CASE WHEN toi_tier = 'Elite' THEN 1 END) as elite_players,
        ROUND(COUNT(CASE WHEN toi_tier = 'Elite' THEN 1 END) * 100.0 / COUNT(*), 1) as elite_percentage
    FROM `fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26`
    GROUP BY contention_cycle
    ORDER BY avg_toi_per_game DESC
    """
    
    cycle_summary = client.query(cycle_summary_query).to_dataframe()
    
    print(f"\nContention Cycle Analysis:")
    print("Cycle Stage | Teams | Players | Avg TOI | Elite | Elite %")
    print("-" * 60)
    for _, row in cycle_summary.iterrows():
        print(f"{row.contention_cycle:12} | {row.teams:5} | {row.total_players:7} | {row.avg_toi_per_game:7} | {row.elite_players:5} | {row.elite_percentage:7}%")
    
    # Show Edmonton example
    print(f"\nEdmonton Oilers TOI Forecast:")
    edm_query = """
    SELECT 
        player_name,
        position_type,
        toi_tier,
        projected_toi_per_game,
        projected_games_played,
        total_season_toi,
        special_teams_minutes
    FROM `fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26`
    WHERE team_abbr = 'EDM'
    ORDER BY projected_toi_per_game DESC
    """
    
    edm_results = client.query(edm_query).to_dataframe()
    
    print("Player | Position | Tier | TOI/Game | GP | Total TOI | ST Min")
    print("-" * 70)
    for _, row in edm_results.head(15).iterrows():
        print(f"{row.player_name:20} | {row.position_type:8} | {row.toi_tier:5} | {row.projected_toi_per_game:8} | {row.projected_games_played:2} | {row.total_season_toi:9} | {row.special_teams_minutes:6}")
    
    print(f"\n✅ TOI forecasts generated for all {len(team_summary)} teams!")
    print("Data saved to: fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26")

if __name__ == "__main__":
    generate_toi_forecasts()
