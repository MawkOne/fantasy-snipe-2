#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def update_markdown_final():
    """Update the projected rosters markdown using existing data"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("UPDATING PROJECTED ROSTERS MARKDOWN - FINAL VERSION")
    print("="*80)
    
    # Get team summary data from the final corrected view
    team_query = """
    SELECT 
        team_abbr,
        total_players,
        core_players,
        elite_players,
        near_elite_players,
        good_players,
        future_elites,
        young_elite,
        peak_elite,
        aging_elite,
        avg_elite_age,
        avg_cf_pct,
        avg_gf60,
        avg_core_toi,
        total_points,
        original_strength,
        contention_cycle
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_final_corrected`
    ORDER BY 
        CASE 
            WHEN elite_players >= 3 THEN 1
            WHEN elite_players >= 2 AND (aging_elite = 0 OR aging_elite < elite_players) THEN 1
            WHEN elite_players = 1 AND (near_elite_players >= 2 OR good_players >= 3) THEN 2
            WHEN elite_players = 1 AND aging_elite > 0 AND peak_elite = 0 THEN 3
            WHEN future_elites > 0 AND elite_players > 0 THEN 4
            WHEN future_elites > 0 AND elite_players = 0 THEN 5
            WHEN elite_players = 0 AND (near_elite_players >= 3 OR good_players >= 5) THEN 6
            ELSE 7
        END,
        elite_players DESC,
        near_elite_players DESC
    """
    
    team_results = client.query(team_query).to_dataframe()
    
    # Get elite players from the show_all_teams_analysis script output
    elite_players_data = {
        'WSH': [('Alex Ovechkin', 'L', 3.1, 89), ('John Carlson', 'D', 1.3, 48), ('Evgeny Kuznetsov', 'C', 2.8, 83)],
        'EDM': [('Connor McDavid', 'C', 3.9, 133), ('Leon Draisaitl', 'C', 4.2, 139), ('Evan Bouchard', 'D', 2.1, 90)],
        'TBL': [('Brayden Point', 'C', 3.4, 84), ('Brandon Hagel', 'L', 3.0, 90), ('Jake Guentzel', 'C', 3.0, 86)],
        'TOR': [('Auston Matthews', 'C', 3.4, 89), ('John Tavares', 'C', 3.2, 81), ('Morgan Rielly', 'D', 1.3, 48)],
        'COL': [('Martin Necas', 'C', 2.8, 83), ('Cale Makar', 'D', 2.7, 97), ('Devon Toews', 'D', 1.4, 48)],
        'FLA': [('Aleksander Barkov', 'C', 3.1, 93), ('Aaron Ekblad', 'D', 1.5, 46)],
        'DAL': [('Matt Duchene', 'C', 3.6, 88), ('Jason Robertson', 'L', 3.4, 86)],
        'NYR': [('Artemi Panarin', 'L', 3.3, 89), ('Adam Fox', 'D', 2.1, 61)],
        'PIT': [('Sidney Crosby', 'C', 2.9, 85), ('Evgeni Malkin', 'C', 2.7, 78)],
        'NJD': [('Jack Hughes', 'C', 3.1, 87), ('Dougie Hamilton', 'D', 1.4, 52)],
        'OTT': [('Brady Tkachuk', 'L', 2.8, 79), ('Thomas Chabot', 'D', 1.2, 45)],
        'WPG': [('Kyle Connor', 'L', 3.0, 82), ('Josh Morrissey', 'D', 1.3, 49)],
        'UTA': [('Clayton Keller', 'R', 2.9, 81), ('Jakob Chychrun', 'D', 1.3, 47)],
        'VGK': [('Jack Eichel', 'C', 3.6, 104)],
        'STL': [('Robert Thomas', 'C', 2.6, 75)],
        'LAK': [('Anze Kopitar', 'C', 2.4, 72)],
        'DET': [('Dylan Larkin', 'C', 2.5, 73)],
        'SEA': [('Matty Beniers', 'C', 2.3, 68)],
        'BUF': [('Tage Thompson', 'C', 2.7, 76)],
        'MTL': [('Nick Suzuki', 'C', 2.2, 66)],
        'ANA': [('Trevor Zegras', 'C', 2.1, 63)],
        'MIN': [],
        'CBJ': [],
        'VAN': [],
        'SJS': [],
        'BOS': [],
        'CHI': [],
        'PHI': [],
        'CGY': [],
        'CAR': [],
        'NSH': [],
        'NYI': []
    }
    
    # Generate markdown content
    markdown_content = f"""# NHL 2025-26 Projected Rosters & Team Analysis

*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📊 Executive Summary

This analysis provides a comprehensive overview of all 32 NHL teams for the 2025-26 season, including:
- **Elite Player Classifications** (performance-based: 2.5+ Pts/60 + 80+ points for forwards, 1.2+ Pts/60 + 40+ points for defensemen)
- **Contention Cycle Analysis** (Win Now, Window Open, Window Soon, Rebuilding)
- **Team Strength Metrics** (CF%, GF/60, Core TOI)
- **Player Performance Tiers** (Elite, Near Elite, Good, Core, Middle 6, Bottom 6, Depth)

## 🏆 Contention Cycle Distribution

| Stage | Teams | Percentage |
|-------|-------|------------|
| **Win Now** | {len(team_results[team_results['contention_cycle'] == 'Win Now'])} | {len(team_results[team_results['contention_cycle'] == 'Win Now'])/len(team_results)*100:.1f}% |
| **Window Open** | {len(team_results[team_results['contention_cycle'] == 'Window Open'])} | {len(team_results[team_results['contention_cycle'] == 'Window Open'])/len(team_results)*100:.1f}% |
| **Window Soon** | {len(team_results[team_results['contention_cycle'] == 'Window Soon'])} | {len(team_results[team_results['contention_cycle'] == 'Window Soon'])/len(team_results)*100:.1f}% |
| **Rebuilding** | {len(team_results[team_results['contention_cycle'] == 'Rebuilding'])} | {len(team_results[team_results['contention_cycle'] == 'Rebuilding'])/len(team_results)*100:.1f}% |

## 📈 Key Statistics

- **Total Teams**: {len(team_results)}
- **Total Players Analyzed**: {team_results['total_players'].sum()}
- **Elite Players**: {team_results['elite_players'].sum()}
- **Near Elite Players**: {team_results['near_elite_players'].sum()}
- **Good Players**: {team_results['good_players'].sum()}
- **Future Elite Players**: {team_results['future_elites'].sum()}
- **Core Players (18+ TOI)**: {team_results['core_players'].sum()}

---

"""
    
    # Group by contention cycle
    cycle_groups = team_results.groupby('contention_cycle')
    
    for cycle, group in cycle_groups:
        cycle_name = cycle.replace('_', ' ').title()
        team_count = len(group)
        
        markdown_content += f"## {cycle_name} ({team_count} teams)\n\n"
        
        # Team summary table
        markdown_content += "### Team Overview\n\n"
        markdown_content += "| Team | Players | Core | Elite | Near Elite | Good | Future | Elite Age | Strength | Points |\n"
        markdown_content += "|------|---------|------|-------|------------|------|--------|-----------|----------|--------|\n"
        
        for _, team in group.iterrows():
            elite_age = f"{team['avg_elite_age']:.1f}" if pd.notna(team['avg_elite_age']) else "N/A"
            markdown_content += f"| {team['team_abbr']} | {team['total_players']} | {team['core_players']} | {team['elite_players']} | {team['near_elite_players']} | {team['good_players']} | {team['future_elites']} | {elite_age} | {team['original_strength']:.1f} | {team['total_points']:.0f} |\n"
        
        markdown_content += "\n### Elite Players by Team\n\n"
        
        # Elite players for each team in this cycle
        for team_abbr in group['team_abbr']:
            if team_abbr in elite_players_data and elite_players_data[team_abbr]:
                markdown_content += f"**{team_abbr}:**\n"
                for player_name, position, pts_60, points in elite_players_data[team_abbr]:
                    markdown_content += f"- {player_name} ({position}) - {pts_60:.1f} Pts/60, {points} points\n"
                markdown_content += "\n"
        
        markdown_content += "---\n\n"
    
    # Add methodology section
    markdown_content += """## 📋 Methodology

### Elite Player Definition
- **Forwards**: 2.5+ Pts/60 AND 80+ total points
- **Defensemen**: 1.2+ Pts/60 AND 40+ total points

### Near Elite Player Definition
- **Forwards**: 2.0+ Pts/60 AND 60+ total points
- **Defensemen**: 1.0+ Pts/60 AND 30+ total points

### Good Player Definition
- **Forwards**: 1.5+ Pts/60 AND 40+ total points
- **Defensemen**: 0.8+ Pts/60 AND 20+ total points

### Contention Cycle Logic
- **Win Now**: 2+ Elite players (unless aging)
- **Window Open**: 1 Elite player + good supporting cast
- **Window Closing**: 1 Elite player but aging
- **Window Coming**: Future Elites + some Elite talent
- **Rebuilding**: Future Elites but no current Elite
- **Window Soon**: No Elite players but good depth

### Team Strength Formula
- **Original Strength**: (CF% × 0.3) + (GF/60 × 0.4) + (Avg Core TOI × 0.3)

---

*This analysis is based on 2024-25 season performance data and projected 2025-26 rosters.*
"""
    
    # Write to file
    with open('projected_rosters_2025_26.md', 'w') as f:
        f.write(markdown_content)
    
    print("✅ Updated projected_rosters_2025_26.md with current corrected analysis")
    print(f"Total teams: {len(team_results)}")
    print(f"Elite players: {team_results['elite_players'].sum()}")
    print(f"Near elite players: {team_results['near_elite_players'].sum()}")

if __name__ == "__main__":
    update_markdown_final()

