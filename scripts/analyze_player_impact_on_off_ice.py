#!/usr/bin/env python3
"""
Analyze player impact using on-ice vs off-ice goal differential analysis
Similar to the McDavid analysis showing expected vs actual goal differential
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import numpy as np

def get_player_impact_data(player_name: str, seasons: List[int] = None) -> pd.DataFrame:
    """
    Get on-ice and off-ice goal differential data for a specific player
    """
    if seasons is None:
        seasons = [20202021, 20212022, 20222023, 20232024, 20242025]
    
    client = bigquery.Client()
    
    # Query to get team performance with and without the player on ice
    query = f"""
    WITH player_teams AS (
        SELECT DISTINCT 
            p.player_id,
            p.full_name,
            t.tri_code as team_abbr,
            pst.season
        FROM `fantasy-snipe-ai.nhl_raw.players` p
        JOIN `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst ON p.player_id = pst.player_id
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        WHERE p.full_name LIKE '%{player_name}%'
        AND pst.season IN ({','.join(map(str, seasons))})
    ),
    
    -- Get shift-level data for the player
    player_shifts AS (
        SELECT 
            psm.player_id,
            psm.game_id,
            psm.team_id,
            psm.goals_for,
            psm.goals_against,
            psm.shots_for,
            psm.shots_against,
            psm.attempts_for,
            psm.attempts_against,
            psm.duration,
            g.season,
            g.game_type
        FROM `fantasy-snipe-ai.nhl_raw.player_shift_metrics` psm
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON psm.game_id = g.id
        JOIN player_teams pt ON psm.player_id = pt.player_id AND g.season = pt.season
        WHERE g.game_type = 2  -- Regular season only
    ),
    
    -- Calculate team performance when player is on ice
    on_ice_performance AS (
        SELECT 
            player_id,
            season,
            SUM(goals_for) as on_ice_gf,
            SUM(goals_against) as on_ice_ga,
            SUM(shots_for) as on_ice_sf,
            SUM(shots_against) as on_ice_sa,
            SUM(attempts_for) as on_ice_cf,
            SUM(attempts_against) as on_ice_ca,
            SUM(duration) as on_ice_toi_seconds
        FROM player_shifts
        GROUP BY player_id, season
    ),
    
    -- Calculate team performance when player is off ice
    -- This is more complex - we need to get team totals and subtract on-ice
    team_totals AS (
        SELECT 
            ps.player_id,
            ps.season,
            SUM(ps.goals_for) as team_gf,
            SUM(ps.goals_against) as team_ga,
            SUM(ps.shots_for) as team_sf,
            SUM(ps.shots_against) as team_sa,
            SUM(ps.attempts_for) as team_cf,
            SUM(ps.attempts_against) as team_ca,
            SUM(ps.duration) as team_toi_seconds
        FROM player_shifts ps
        GROUP BY ps.player_id, ps.season
    ),
    
    -- Calculate off-ice performance (team totals - on-ice)
    off_ice_performance AS (
        SELECT 
            oi.player_id,
            oi.season,
            tt.team_gf - oi.on_ice_gf as off_ice_gf,
            tt.team_ga - oi.on_ice_ga as off_ice_ga,
            tt.team_sf - oi.on_ice_sf as off_ice_sf,
            tt.team_sa - oi.on_ice_sa as off_ice_sa,
            tt.team_cf - oi.on_ice_cf as off_ice_cf,
            tt.team_ca - oi.on_ice_ca as off_ice_ca,
            tt.team_toi_seconds - oi.on_ice_toi_seconds as off_ice_toi_seconds
        FROM on_ice_performance oi
        JOIN team_totals tt ON oi.player_id = tt.player_id AND oi.season = tt.season
    )
    
    SELECT 
        pt.full_name,
        pt.team_abbr,
        oi.season,
        -- On-ice metrics
        oi.on_ice_gf,
        oi.on_ice_ga,
        oi.on_ice_gf - oi.on_ice_ga as on_ice_goal_diff,
        oi.on_ice_sf,
        oi.on_ice_sa,
        oi.on_ice_sf - oi.on_ice_sa as on_ice_shot_diff,
        oi.on_ice_cf,
        oi.on_ice_ca,
        oi.on_ice_cf - oi.on_ice_ca as on_ice_corsi_diff,
        oi.on_ice_toi_seconds / 3600.0 as on_ice_toi_hours,
        -- Off-ice metrics
        oof.off_ice_gf,
        oof.off_ice_ga,
        oof.off_ice_gf - oof.off_ice_ga as off_ice_goal_diff,
        oof.off_ice_sf,
        oof.off_ice_sa,
        oof.off_ice_sf - oof.off_ice_sa as off_ice_shot_diff,
        oof.off_ice_cf,
        oof.off_ice_ca,
        oof.off_ice_cf - oof.off_ice_ca as off_ice_corsi_diff,
        oof.off_ice_toi_seconds / 3600.0 as off_ice_toi_hours,
        -- Per 60 minute rates
        (oi.on_ice_gf - oi.on_ice_ga) / (oi.on_ice_toi_seconds / 3600.0) as on_ice_goal_diff_per_60,
        (oof.off_ice_gf - oof.off_ice_ga) / (oof.off_ice_toi_seconds / 3600.0) as off_ice_goal_diff_per_60,
        -- Expected goals (using shot differential as proxy)
        (oi.on_ice_sf - oi.on_ice_sa) / (oi.on_ice_toi_seconds / 3600.0) as on_ice_expected_goal_diff_per_60,
        (oof.off_ice_sf - oof.off_ice_sa) / (oof.off_ice_toi_seconds / 3600.0) as off_ice_expected_goal_diff_per_60
    FROM on_ice_performance oi
    JOIN off_ice_performance oof ON oi.player_id = oof.player_id AND oi.season = oof.season
    JOIN player_teams pt ON oi.player_id = pt.player_id AND oi.season = pt.season
    ORDER BY oi.season
    """
    
    return client.query(query).to_dataframe()

def create_impact_visualization(df: pd.DataFrame, player_name: str) -> None:
    """
    Create a visualization similar to the McDavid article showing on-ice vs off-ice impact
    """
    if df.empty:
        print(f"No data found for {player_name}")
        return
    
    # Prepare data for visualization
    seasons = df['season'].astype(str).str[:4] + '-' + df['season'].astype(str).str[4:]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot off-ice expected goal differential (orange bars)
    bars1 = ax.bar(seasons, df['off_ice_expected_goal_diff_per_60'], 
                   alpha=0.7, color='orange', label='Expected Goal Diff (Off-Ice)', width=0.35)
    
    # Plot off-ice actual goal differential (blue bars)
    bars2 = ax.bar([x + 0.35 for x in range(len(seasons))], df['off_ice_goal_diff_per_60'], 
                   alpha=0.7, color='blue', label='Actual Goal Diff (Off-Ice)', width=0.35)
    
    # Add zero line
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Customize the plot
    ax.set_xlabel('Season')
    ax.set_ylabel('Goal Differential per 60 Minutes')
    ax.set_title(f'{player_name} - Team Performance Without Player On Ice\\nExpected vs Actual Goal Differential')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (exp, act) in enumerate(zip(df['off_ice_expected_goal_diff_per_60'], df['off_ice_goal_diff_per_60'])):
        ax.text(i, exp + (0.1 if exp >= 0 else -0.1), f'{exp:.1f}', 
                ha='center', va='bottom' if exp >= 0 else 'top', fontsize=9)
        ax.text(i + 0.35, act + (0.1 if act >= 0 else -0.1), f'{act:.1f}', 
                ha='center', va='bottom' if act >= 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print(f"\\n{player_name} Impact Analysis Summary:")
    print("=" * 50)
    for _, row in df.iterrows():
        season = str(row['season'])[:4] + '-' + str(row['season'])[4:]
        print(f"\\n{season} Season:")
        print(f"  On-Ice Goal Diff/60: {row['on_ice_goal_diff_per_60']:.2f}")
        print(f"  Off-Ice Goal Diff/60: {row['off_ice_goal_diff_per_60']:.2f}")
        print(f"  Impact: {row['on_ice_goal_diff_per_60'] - row['off_ice_goal_diff_per_60']:.2f}")
        print(f"  On-Ice TOI: {row['on_ice_toi_hours']:.1f} hours")
        print(f"  Off-Ice TOI: {row['off_ice_toi_hours']:.1f} hours")

def analyze_multiple_players(player_names: List[str], seasons: List[int] = None) -> pd.DataFrame:
    """
    Analyze impact for multiple players and compare
    """
    all_data = []
    
    for player_name in player_names:
        df = get_player_impact_data(player_name, seasons)
        if not df.empty:
            df['player'] = player_name
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def create_comparison_visualization(df: pd.DataFrame) -> None:
    """
    Create a comparison visualization for multiple players
    """
    if df.empty:
        print("No data available for comparison")
        return
    
    # Create a pivot table for easier plotting
    pivot_impact = df.pivot(index='season', columns='player', values='on_ice_goal_diff_per_60')
    pivot_impact.index = pivot_impact.index.astype(str).str[:4] + '-' + pivot_impact.index.astype(str).str[4:]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each player's impact
    for player in pivot_impact.columns:
        ax.plot(pivot_impact.index, pivot_impact[player], marker='o', linewidth=2, label=player)
    
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_xlabel('Season')
    ax.set_ylabel('On-Ice Goal Differential per 60 Minutes')
    ax.set_title('Player Impact Comparison - On-Ice Goal Differential')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    """
    Main function to run the analysis
    """
    # Analyze Connor McDavid (as in the article)
    print("Analyzing Connor McDavid's impact...")
    mcdavid_df = get_player_impact_data("Connor McDavid")
    
    if not mcdavid_df.empty:
        create_impact_visualization(mcdavid_df, "Connor McDavid")
        
        # Show the data
        print("\\nMcDavid Impact Data:")
        print(mcdavid_df[['season', 'on_ice_goal_diff_per_60', 'off_ice_goal_diff_per_60', 
                         'on_ice_expected_goal_diff_per_60', 'off_ice_expected_goal_diff_per_60']].to_string(index=False))
    
    # Compare with other elite players
    print("\\n" + "="*60)
    print("Comparing with other elite players...")
    
    elite_players = ["Connor McDavid", "Nathan MacKinnon", "Auston Matthews", "Leon Draisaitl"]
    comparison_df = analyze_multiple_players(elite_players)
    
    if not comparison_df.empty:
        create_comparison_visualization(comparison_df)
        
        # Show comparison summary
        print("\\nElite Player Impact Comparison:")
        summary = comparison_df.groupby('player').agg({
            'on_ice_goal_diff_per_60': 'mean',
            'off_ice_goal_diff_per_60': 'mean'
        }).round(2)
        summary['impact'] = summary['on_ice_goal_diff_per_60'] - summary['off_ice_goal_diff_per_60']
        print(summary)

if __name__ == "__main__":
    main()
