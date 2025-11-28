#!/usr/bin/env python3
"""
Analyze Connor McDavid's impact using available data
Replicating the Oilers Nation article analysis
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import numpy as np

def get_mcdavid_impact_data() -> pd.DataFrame:
    """
    Get McDavid's impact data using available tables
    """
    client = bigquery.Client()
    
    # Query to get McDavid's performance data
    query = """
    WITH mcdavid_data AS (
        SELECT 
            p.player_id,
            p.full_name,
            t.tri_code as team_abbr,
            pst.season,
            pst.games_played,
            pst.toi_minutes,
            pst.toi_minutes / pst.games_played as toi_per_game,
            pst.cf_pct_corrected,
            pst.gf60,
            pst.ga60,
            pst.gf60 - pst.ga60 as goal_diff_60,
            ps.points,
            ps.goals,
            ps.assists,
            ps.plus_minus
        FROM `fantasy-snipe-ai.nhl_raw.players` p
        JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst ON p.player_id = pst.player_id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON p.player_id = ps.player_id AND pst.season = ps.season
        WHERE p.full_name LIKE '%McDavid%'
        AND pst.season >= 20202021
        AND pst.game_type = 2
    ),
    
    oilers_team_data AS (
        SELECT 
            pst.season,
            AVG(pst.gf60) as team_avg_gf60,
            AVG(pst.ga60) as team_avg_ga60,
            AVG(pst.gf60 - pst.ga60) as team_avg_goal_diff_60,
            AVG(pst.cf_pct_corrected) as team_avg_cf_pct
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        WHERE t.tri_code = 'EDM'
        AND pst.season >= 20202021
        AND pst.game_type = 2
        AND pst.games_played >= 20
        GROUP BY pst.season
    )
    
    SELECT 
        md.full_name,
        md.team_abbr,
        md.season,
        md.games_played,
        md.toi_per_game,
        md.goal_diff_60 as mcdavid_goal_diff_60,
        md.gf60 as mcdavid_gf60,
        md.ga60 as mcdavid_ga60,
        md.cf_pct_corrected as mcdavid_cf_pct,
        td.team_avg_goal_diff_60,
        td.team_avg_gf60,
        td.team_avg_ga60,
        td.team_avg_cf_pct,
        -- Estimate team performance without McDavid
        td.team_avg_goal_diff_60 - md.goal_diff_60 as estimated_team_without_mcdavid_60,
        -- McDavid's impact (his performance - team without him)
        md.goal_diff_60 - (td.team_avg_goal_diff_60 - md.goal_diff_60) as mcdavid_impact_60
    FROM mcdavid_data md
    JOIN oilers_team_data td ON md.season = td.season
    ORDER BY md.season
    """
    
    return client.query(query).to_dataframe()

def create_mcdavid_visualization(df: pd.DataFrame) -> None:
    """
    Create a visualization similar to the Oilers Nation article
    """
    if df.empty:
        print("No data found for McDavid")
        return
    
    # Prepare data for visualization
    seasons = df['season'].astype(str).str[:4] + '-' + df['season'].astype(str).str[4:]
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Team performance with and without McDavid (similar to article)
    ax1.bar([x - 0.2 for x in range(len(seasons))], df['team_avg_goal_diff_60'], 
            alpha=0.7, color='orange', label='Expected Goal Diff (Team Average)', width=0.4)
    ax1.bar([x + 0.2 for x in range(len(seasons))], df['estimated_team_without_mcdavid_60'], 
            alpha=0.7, color='blue', label='Actual Goal Diff (Without McDavid)', width=0.4)
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Goal Differential per 60 Minutes')
    ax1.set_title('Edmonton Oilers - Performance Without McDavid On Ice\\nExpected vs Actual Goal Differential')
    ax1.set_xticks(range(len(seasons)))
    ax1.set_xticklabels(seasons)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (exp, act) in enumerate(zip(df['team_avg_goal_diff_60'], df['estimated_team_without_mcdavid_60'])):
        ax1.text(i - 0.2, exp + (0.1 if exp >= 0 else -0.1), f'{exp:.1f}', 
                ha='center', va='bottom' if exp >= 0 else 'top', fontsize=9)
        ax1.text(i + 0.2, act + (0.1 if act >= 0 else -0.1), f'{act:.1f}', 
                ha='center', va='bottom' if act >= 0 else 'top', fontsize=9)
    
    # Plot 2: McDavid's individual impact
    bars = ax2.bar(seasons, df['mcdavid_impact_60'], 
                   alpha=0.7, color='purple', label="McDavid's Impact")
    
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Impact per 60 Minutes')
    ax2.set_title("Connor McDavid - Individual Impact Analysis")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Color bars based on positive/negative impact
    for i, bar in enumerate(bars):
        if df.iloc[i]['mcdavid_impact_60'] > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')
    
    # Add value labels
    for i, impact in enumerate(df['mcdavid_impact_60']):
        ax2.text(i, impact + (0.1 if impact >= 0 else -0.1), f'{impact:.1f}', 
                ha='center', va='bottom' if impact >= 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print("\\nConnor McDavid Impact Analysis Summary:")
    print("=" * 50)
    for _, row in df.iterrows():
        season = str(row['season'])[:4] + '-' + str(row['season'])[4:]
        print(f"\\n{season} Season:")
        print(f"  McDavid Goal Diff/60: {row['mcdavid_goal_diff_60']:.2f}")
        print(f"  Team Average Goal Diff/60: {row['team_avg_goal_diff_60']:.2f}")
        print(f"  Team Without McDavid/60: {row['estimated_team_without_mcdavid_60']:.2f}")
        print(f"  McDavid Impact: {row['mcdavid_impact_60']:.2f}")
        print(f"  TOI per Game: {row['toi_per_game']:.1f} minutes")
        print(f"  Games Played: {row['games_played']}")

def compare_elite_players() -> None:
    """
    Compare McDavid's impact with other elite players
    """
    client = bigquery.Client()
    
    elite_players = ["Connor McDavid", "Nathan MacKinnon", "Auston Matthews", "Leon Draisaitl"]
    
    query = f"""
    WITH elite_data AS (
        SELECT 
            p.player_id,
            p.full_name,
            t.tri_code as team_abbr,
            pst.season,
            pst.games_played,
            pst.toi_minutes / pst.games_played as toi_per_game,
            pst.gf60 - pst.ga60 as goal_diff_60,
            pst.cf_pct_corrected,
            ps.points,
            ps.plus_minus
        FROM `fantasy-snipe-ai.nhl_raw.players` p
        JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst ON p.player_id = pst.player_id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        LEFT JOIN `fantasy-snipe-ai.nhl_raw.player_stats` ps ON p.player_id = ps.player_id AND pst.season = ps.season
        WHERE p.full_name IN ({','.join([f"'{name}'" for name in elite_players])})
        AND pst.season >= 20202021
        AND pst.game_type = 2
    ),
    
    team_data AS (
        SELECT 
            t.tri_code as team_abbr,
            pst.season,
            AVG(pst.gf60 - pst.ga60) as team_avg_goal_diff_60
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        WHERE pst.season >= 20202021
        AND pst.game_type = 2
        AND pst.games_played >= 20
        GROUP BY t.tri_code, pst.season
    )
    
    SELECT 
        ed.full_name,
        ed.team_abbr,
        ed.season,
        ed.goal_diff_60,
        ed.toi_per_game,
        ed.points,
        ed.plus_minus,
        td.team_avg_goal_diff_60,
        ed.goal_diff_60 - td.team_avg_goal_diff_60 as impact_vs_team
    FROM elite_data ed
    JOIN team_data td ON ed.team_abbr = td.team_abbr AND ed.season = td.season
    ORDER BY ed.full_name, ed.season
    """
    
    df = client.query(query).to_dataframe()
    
    if not df.empty:
        # Create comparison visualization
        pivot_impact = df.pivot(index='season', columns='full_name', values='impact_vs_team')
        pivot_impact.index = pivot_impact.index.astype(str).str[:4] + '-' + pivot_impact.index.astype(str).str[4:]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        for player in pivot_impact.columns:
            ax.plot(pivot_impact.index, pivot_impact[player], marker='o', linewidth=2, label=player)
        
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.set_xlabel('Season')
        ax.set_ylabel('Impact vs Team Average (Goal Diff/60)')
        ax.set_title('Elite Player Impact Comparison - vs Team Average')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        
        # Show summary
        print("\\nElite Player Impact Summary (2020-21 to 2024-25):")
        print("=" * 60)
        summary = df.groupby('full_name').agg({
            'goal_diff_60': 'mean',
            'impact_vs_team': 'mean',
            'points': 'mean',
            'toi_per_game': 'mean'
        }).round(2)
        summary = summary.sort_values('impact_vs_team', ascending=False)
        print(summary)

def main():
    """
    Main function to run the McDavid impact analysis
    """
    print("Analyzing Connor McDavid's impact on the Edmonton Oilers...")
    print("Replicating the Oilers Nation article analysis")
    print("=" * 60)
    
    # Get McDavid's impact data
    mcdavid_df = get_mcdavid_impact_data()
    
    if not mcdavid_df.empty:
        create_mcdavid_visualization(mcdavid_df)
        
        # Show the data
        print("\\nMcDavid Impact Data:")
        print(mcdavid_df[['season', 'mcdavid_goal_diff_60', 'team_avg_goal_diff_60', 
                         'estimated_team_without_mcdavid_60', 'mcdavid_impact_60']].to_string(index=False))
    
    # Compare with other elite players
    print("\\n" + "="*60)
    print("Comparing McDavid's impact with other elite players...")
    compare_elite_players()

if __name__ == "__main__":
    main()
