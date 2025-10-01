#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def generate_roster_markdown():
    """Generate markdown file with all team rosters and TOI assumptions"""
    
    client = bigquery.Client()
    
    print("Generating roster markdown file...")
    
    # Get all projected rosters with TOI forecasts
    query = """
    SELECT 
        team_abbr,
        team_name,
        player_name,
        position_type,
        toi_tier,
        line_position,
        projected_toi_per_game,
        projected_games_played,
        total_season_toi,
        special_teams_pp1,
        special_teams_pp2,
        special_teams_pk1,
        special_teams_pk2,
        special_teams_minutes
    FROM `fantasy-snipe-ai.nhl_projections.toi_forecasts_2025_26`
    ORDER BY team_abbr, position_type, projected_toi_per_game DESC
    """
    
    results = client.query(query).to_dataframe()
    
    # Create markdown output
    with open('projected_rosters_2025_26.md', 'w') as f:
        f.write('# 2025-26 Projected NHL Rosters with TOI Forecasts\n\n')
        f.write('Generated from data-driven TOI tiers and Foster methodology\n\n')
        
        for team_abbr in sorted(results['team_abbr'].unique()):
            team_data = results[results['team_abbr'] == team_abbr]
            team_name = team_data['team_name'].iloc[0]
            
            f.write(f'## {team_abbr} - {team_name.title()}\n\n')
            
            # Forwards
            forwards = team_data[team_data['position_type'] == 'Forward'].sort_values('projected_toi_per_game', ascending=False)
            if not forwards.empty:
                f.write('### Forwards\n\n')
                f.write('| Player | TOI Tier | Line | TOI/Game | GP | Total TOI | PP1 | PP2 | PK1 | PK2 | ST Min |\n')
                f.write('|--------|----------|------|----------|----|-----------|-----|-----|-----|-----|--------|\n')
                for _, player in forwards.iterrows():
                    pp1 = '✅' if player['special_teams_pp1'] else ''
                    pp2 = '✅' if player['special_teams_pp2'] else ''
                    pk1 = '✅' if player['special_teams_pk1'] else ''
                    pk2 = '✅' if player['special_teams_pk2'] else ''
                    f.write(f'| {player["player_name"]} | {player["toi_tier"]} | {player["line_position"]} | {player["projected_toi_per_game"]} | {player["projected_games_played"]} | {player["total_season_toi"]} | {pp1} | {pp2} | {pk1} | {pk2} | {player["special_teams_minutes"]} |\n')
                f.write('\n')
            
            # Defensemen
            defensemen = team_data[team_data['position_type'] == 'Defenseman'].sort_values('projected_toi_per_game', ascending=False)
            if not defensemen.empty:
                f.write('### Defensemen\n\n')
                f.write('| Player | TOI Tier | Pair | TOI/Game | GP | Total TOI | PP1 | PP2 | PK1 | PK2 | ST Min |\n')
                f.write('|--------|----------|------|----------|----|-----------|-----|-----|-----|-----|--------|\n')
                for _, player in defensemen.iterrows():
                    pp1 = '✅' if player['special_teams_pp1'] else ''
                    pp2 = '✅' if player['special_teams_pp2'] else ''
                    pk1 = '✅' if player['special_teams_pk1'] else ''
                    pk2 = '✅' if player['special_teams_pk2'] else ''
                    f.write(f'| {player["player_name"]} | {player["toi_tier"]} | {player["line_position"]} | {player["projected_toi_per_game"]} | {player["projected_games_played"]} | {player["total_season_toi"]} | {pp1} | {pp2} | {pk1} | {pk2} | {player["special_teams_minutes"]} |\n')
                f.write('\n')
            
            # Goalies
            goalies = team_data[team_data['position_type'] == 'Goalie'].sort_values('projected_toi_per_game', ascending=False)
            if not goalies.empty:
                f.write('### Goalies\n\n')
                f.write('| Player | TOI Tier | Role | TOI/Game | GP | Total TOI |\n')
                f.write('|--------|----------|------|----------|----|-----------|\n')
                for _, player in goalies.iterrows():
                    f.write(f'| {player["player_name"]} | {player["toi_tier"]} | {player["line_position"]} | {player["projected_toi_per_game"]} | {player["projected_games_played"]} | {player["total_season_toi"]} |\n')
                f.write('\n')
            
            # Team summary
            total_players = len(team_data)
            total_toi = team_data['total_season_toi'].sum()
            avg_toi = team_data['projected_toi_per_game'].mean()
            elite_players = len(team_data[team_data['toi_tier'] == 'Elite'])
            
            f.write('### Team Summary\n\n')
            f.write(f'- **Total Players**: {total_players}\n')
            f.write(f'- **Elite Players**: {elite_players}\n')
            f.write(f'- **Average TOI/Game**: {avg_toi:.1f} minutes\n')
            f.write(f'- **Total Season TOI**: {total_toi:.0f} minutes\n\n')
            f.write('---\n\n')
    
    print('✅ Created projected_rosters_2025_26.md with all team rosters and TOI assumptions')

if __name__ == "__main__":
    generate_roster_markdown()
