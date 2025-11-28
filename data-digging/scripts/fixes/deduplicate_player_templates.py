#!/usr/bin/env python3
"""
Deduplicate the player input templates table to ensure each player appears only once.
"""

import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def deduplicate_player_templates():
    """Deduplicate the player input templates table."""
    client = bigquery.Client()
    
    print("Deduplicating player input templates...")
    
    # Create deduplicated player input templates
    dedupe_query = """
    CREATE OR REPLACE TABLE `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated` AS
    WITH ranked_players AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, team 
                ORDER BY gp_3yr_avg DESC, ev_points_60 DESC, ev_toi_avg_minutes DESC
            ) as rn
        FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_final`
    )
    SELECT 
        player_id,
        player_name,
        position,
        position_group,
        team,
        age,
        gp_3yr_avg,
        gp_3yr_total,
        ev_toi_avg_minutes,
        player_archetype,
        player_archetype_2,
        line_role,
        style,
        ev_cf60,
        ev_ca60,
        ev_ff60,
        ev_fa60,
        ev_sf60,
        ev_sa60,
        ev_gf60,
        ev_ga60,
        ev_pts_conversion,
        ev_goals_60,
        ev_assists_60,
        ev_points_60,
        ev_shots_60,
        shooting_pct,
        faceoff_win_pct,
        pim_avg,
        plus_minus_avg,
        current_gp,
        current_goals,
        current_assists,
        current_points,
        current_toi_per_game_minutes,
        ev_cf_pct,
        ev_ff_pct,
        ev_sf_pct,
        ev_gf_pct,
        ev_pdo,
        pp_goals_avg,
        pp_points_avg,
        sh_goals_avg,
        sh_points_avg,
        created_at,
        model_version
    FROM ranked_players
    WHERE rn = 1
    ORDER BY team, position_group, ev_points_60 DESC
    """
    
    job = client.query(dedupe_query)
    job.result()
    print("✓ Created deduplicated player input templates")
    
    # Run QA on deduplicated table
    print("\nRunning QA on deduplicated table...")
    
    # Check for duplicates
    qa_duplicates = """
    SELECT 
        player_name, 
        team, 
        COUNT(*) as entry_count
    FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated`
    GROUP BY player_name, team
    HAVING COUNT(*) > 1
    LIMIT 5
    """
    
    qa_job = client.query(qa_duplicates)
    qa_results = qa_job.result()
    
    print("Duplicate entries check:")
    if qa_results.total_rows == 0:
        print("✓ No duplicate entries found")
    else:
        print("❌ Found duplicate entries:")
        for row in qa_results:
            print(f"  {row.player_name} ({row.team}): {row.entry_count} entries")
    
    # Check total records
    qa_total = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(DISTINCT CONCAT(player_id, '_', team)) as unique_player_team_combos
    FROM `fantasy-snipe-ai.nhl_projections.player_input_templates_deduplicated`
    """
    
    qa_job2 = client.query(qa_total)
    qa_results2 = qa_job2.result()
    
    for row in qa_results2:
        print(f"Total players: {row.total_players}")
        print(f"Unique player-team combinations: {row.unique_player_team_combos}")
        if row.total_players == row.unique_player_team_combos:
            print("✓ All players are unique")
        else:
            print("❌ Still have duplicates")

if __name__ == "__main__":
    deduplicate_player_templates()
