#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

def update_roster_markdown_simple():
    """Update the projected rosters markdown with current corrected analysis"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("UPDATING PROJECTED ROSTERS MARKDOWN - SIMPLE VERSION")
    print("="*80)
    
    # Get team summary data
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
    
    # Get elite players data
    elite_query = """
    WITH projected_rosters AS (
        SELECT 
            team_abbr,
            player_name,
            position_type
        FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26_deduplicated`
    ),
    player_performance AS (
        SELECT 
            t.tri_code as team,
            p.full_name as player_name,
            p.position,
            EXTRACT(YEAR FROM CURRENT_DATE()) - EXTRACT(YEAR FROM p.birth_date) as current_age,
            pst.toi_minutes / pst.games_played as toi_per_game,
            pst.pts60_weighted as points_60,
            COALESCE(ps.points, 0) as points,
            COALESCE(ps.goals, 0) as goals,
            COALESCE(ps.assists, 0) as assists
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst 
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id 
        JOIN `fantasy-snipe-ai.nhl_raw.players` p ON pst.player_id = p.player_id 
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps 
            ON pst.player_id = ps.player_id 
            AND pst.season = ps.season
        WHERE pst.season = 20242025 
        AND pst.game_type = 2 
        AND pst.games_played >= 20 
        AND p.position IN ("C", "L", "R", "D")
        AND pst.pts60_weighted IS NOT NULL
    )
    SELECT 
        pr.team_abbr,
        pr.player_name,
        pr.position_type,
        pp.current_age,
        pp.toi_per_game,
        pp.points_60,
        pp.points,
        pp.goals,
        pp.assists,
        CASE 
            WHEN pp.position IN ("C", "L", "R") AND pp.points_60 >= 2.5 AND pp.points >= 80 THEN "Elite"
            WHEN pp.position = "D" AND pp.points_60 >= 1.2 AND pp.points >= 40 THEN "Elite"
            WHEN pp.position IN ("C", "L", "R") AND pp.points_60 >= 2.0 AND pp.points >= 60 THEN "Near Elite"
            WHEN pp.position = "D" AND pp.points_60 >= 1.0 AND pp.points >= 30 THEN "Near Elite"
            WHEN pp.position IN ("C", "L", "R") AND pp.points_60 >= 1.5 AND pp.points >= 40 THEN "Good"
            WHEN pp.position = "D" AND pp.points_60 >= 0.8 AND pp.points >= 20 THEN "Good"
            WHEN pp.toi_per_game >= 18 THEN "Core"
            WHEN pp.toi_per_game >= 15 THEN "Middle 6"
            WHEN pp.toi_per_game >= 12 THEN "Bottom 6"
            ELSE "Depth"
        END as performance_tier
    FROM projected_rosters pr
    JOIN player_performance pp ON pr.player_name = pp.player_name AND pr.team_abbr = pp.team
    ORDER BY pr.team_abbr, performance_tier DESC, pp.points_60 DESC
    """
    
    player_results = client.query(elite_query).to_dataframe()
    
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
            team_elite_players = player_results[
                (player_results['team_abbr'] == team_abbr) & 
                (player_results['performance_tier'] == 'Elite')
            ]
            
            if not team_elite_players.empty:
                markdown_content += f"**{team_abbr}:**\n"
                for _, player in team_elite_players.iterrows():
                    markdown_content += f"- {player['player_name']} ({player['position_type']}) - Age {player['current_age']}, {player['toi_per_game']:.1f} TOI, {player['points_60']:.1f} Pts/60, {player['points']} points\n"
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
    print(f"Total players: {len(player_results)}")
    print(f"Elite players: {len(player_results[player_results['performance_tier'] == 'Elite'])}")
    print(f"Near elite players: {len(player_results[player_results['performance_tier'] == 'Near Elite'])}")

if __name__ == "__main__":
    update_roster_markdown_simple()
