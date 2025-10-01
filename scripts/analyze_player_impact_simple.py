#!/usr/bin/env python3
"""
Analyze player impact using on-ice vs off-ice goal differential analysis
Using available data from player_game_stats and player_shifts
"""

import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import numpy as np

def get_player_impact_data_simple(player_name: str, seasons: List[int] = None) -> pd.DataFrame:
    """
    Get on-ice and off-ice goal differential data for a specific player using available data
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
    
    -- Get game-level data for the player
    player_games AS (
        SELECT 
            pgs.player_id,
            pgs.game_id,
            pgs.team_id,
            pgs.goals,
            pgs.assists,
            pgs.plus_minus,
            pgs.time_on_ice_seconds,
            g.season,
            g.game_type,
            g.home_team_id,
            g.away_team_id,
            g.home_score,
            g.away_score
        FROM `fantasy-snipe-ai.nhl_raw.player_game_stats` pgs
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON pgs.game_id = g.id
        JOIN player_teams pt ON pgs.player_id = pt.player_id AND g.season = pt.season
        WHERE g.game_type = 2  -- Regular season only
        AND pgs.time_on_ice_seconds > 0
    ),
    
    -- Calculate team performance when player is on ice (using plus/minus as proxy)
    on_ice_performance AS (
        SELECT 
            player_id,
            season,
            COUNT(*) as games_played,
            SUM(plus_minus) as on_ice_plus_minus,
            SUM(time_on_ice_seconds) as on_ice_toi_seconds,
            AVG(plus_minus) as avg_plus_minus_per_game
        FROM player_games
        GROUP BY player_id, season
    ),
    
    -- Get team totals for the season
    team_season_totals AS (
        SELECT 
            pgs.team_id,
            g.season,
            COUNT(DISTINCT g.id) as team_games,
            SUM(CASE WHEN pgs.team_id = g.home_team_id THEN g.home_score ELSE g.away_score END) as team_gf,
            SUM(CASE WHEN pgs.team_id = g.home_team_id THEN g.away_score ELSE g.home_score END) as team_ga
        FROM `fantasy-snipe-ai.nhl_raw.player_game_stats` pgs
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON pgs.game_id = g.id
        WHERE g.game_type = 2
        GROUP BY pgs.team_id, g.season
    ),
    
    -- Calculate team performance per game
    team_per_game AS (
        SELECT 
            team_id,
            season,
            team_gf / team_games as team_gf_per_game,
            team_ga / team_games as team_ga_per_game,
            (team_gf - team_ga) / team_games as team_goal_diff_per_game
        FROM team_season_totals
    )
    
    SELECT 
        pt.full_name,
        pt.team_abbr,
        oi.season,
        oi.games_played,
        oi.on_ice_plus_minus,
        oi.avg_plus_minus_per_game,
        oi.on_ice_toi_seconds / 3600.0 as on_ice_toi_hours,
        tpg.team_gf_per_game,
        tpg.team_ga_per_game,
        tpg.team_goal_diff_per_game,
        -- Estimate off-ice performance (team total - player contribution)
        tpg.team_goal_diff_per_game - oi.avg_plus_minus_per_game as estimated_off_ice_goal_diff_per_game,
        -- Per 60 minute rates (using TOI)
        (oi.on_ice_plus_minus / (oi.on_ice_toi_seconds / 3600.0)) as on_ice_goal_diff_per_60,
        ((tpg.team_goal_diff_per_game - oi.avg_plus_minus_per_game) * 60 / (60 - (oi.on_ice_toi_seconds / 3600.0 / oi.games_played))) as estimated_off_ice_goal_diff_per_60
    FROM on_ice_performance oi
    JOIN player_teams pt ON oi.player_id = pt.player_id AND oi.season = pt.season
    JOIN team_per_game tpg ON pt.team_abbr = (
        SELECT tri_code FROM `fantasy-snipe-ai.nhl_raw.teams` WHERE id = oi.player_id
    ) AND oi.season = tpg.season
    ORDER BY oi.season
    """
    
    return client.query(query).to_dataframe()

def get_player_impact_data_advanced(player_name: str, seasons: List[int] = None) -> pd.DataFrame:
    """
    More advanced analysis using shift data if available
    """
    if seasons is None:
        seasons = [20202021, 20212022, 20222023, 20232024, 20242025]
    
    client = bigquery.Client()
    
    # Simpler query using available data
    query = f"""
    WITH player_data AS (
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
        WHERE p.full_name LIKE '%{player_name}%'
        AND pst.season IN ({','.join(map(str, seasons))})
        AND pst.game_type = 2
    ),
    
    team_data AS (
        SELECT 
            t.tri_code as team_abbr,
            pst.season,
            AVG(pst.gf60) as team_avg_gf60,
            AVG(pst.ga60) as team_avg_ga60,
            AVG(pst.gf60 - pst.ga60) as team_avg_goal_diff_60,
            AVG(pst.cf_pct_corrected) as team_avg_cf_pct
        FROM `fantasy-snipe-ai.nhl_processed.player_season_totals_corrected` pst
        JOIN `fantasy-snipe-ai.nhl_raw.teams` t ON pst.team_id = t.id
        WHERE pst.season IN ({','.join(map(str, seasons))})
        AND pst.game_type = 2
        AND pst.games_played >= 20
        GROUP BY t.tri_code, pst.season
    )
    
    SELECT 
        pd.full_name,
        pd.team_abbr,
        pd.season,
        pd.games_played,
        pd.toi_per_game,
        pd.goal_diff_60 as on_ice_goal_diff_60,
        pd.gf60 as on_ice_gf60,
        pd.ga60 as on_ice_ga60,
        pd.cf_pct_corrected as on_ice_cf_pct,
        td.team_avg_goal_diff_60,
        td.team_avg_gf60,
        td.team_avg_ga60,
        td.team_avg_cf_pct,
        -- Estimate off-ice performance (team average - player contribution)
        td.team_avg_goal_diff_60 - pd.goal_diff_60 as estimated_off_ice_goal_diff_60,
        -- Player impact (on-ice - off-ice)
        pd.goal_diff_60 - (td.team_avg_goal_diff_60 - pd.goal_diff_60) as player_impact_60
    FROM player_data pd
    JOIN team_data td ON pd.team_abbr = td.team_abbr AND pd.season = td.season
    ORDER BY pd.season
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
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: On-ice vs Off-ice Goal Differential
    ax1.bar([x - 0.2 for x in range(len(seasons))], df['on_ice_goal_diff_60'], 
            alpha=0.7, color='green', label='On-Ice Goal Diff/60', width=0.4)
    ax1.bar([x + 0.2 for x in range(len(seasons))], df['estimated_off_ice_goal_diff_60'], 
            alpha=0.7, color='red', label='Off-Ice Goal Diff/60', width=0.4)
    
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.set_xlabel('Season')
    ax1.set_ylabel('Goal Differential per 60 Minutes')
    ax1.set_title(f'{player_name} - On-Ice vs Off-Ice Goal Differential')
    ax1.set_xticks(range(len(seasons)))
    ax1.set_xticklabels(seasons)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Player Impact (On-Ice - Off-Ice)
    bars = ax2.bar(seasons, df['player_impact_60'], 
                   alpha=0.7, color='purple', label='Player Impact (On-Ice - Off-Ice)')
    
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Season')
    ax2.set_ylabel('Impact per 60 Minutes')
    ax2.set_title(f'{player_name} - Player Impact Analysis')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Color bars based on positive/negative impact
    for i, bar in enumerate(bars):
        if df.iloc[i]['player_impact_60'] > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')
    
    plt.tight_layout()
    plt.show()
    
    # Print summary statistics
    print(f"\\n{player_name} Impact Analysis Summary:")
    print("=" * 50)
    for _, row in df.iterrows():
        season = str(row['season'])[:4] + '-' + str(row['season'])[4:]
        print(f"\\n{season} Season:")
        print(f"  On-Ice Goal Diff/60: {row['on_ice_goal_diff_60']:.2f}")
        print(f"  Off-Ice Goal Diff/60: {row['estimated_off_ice_goal_diff_60']:.2f}")
        print(f"  Player Impact: {row['player_impact_60']:.2f}")
        print(f"  TOI per Game: {row['toi_per_game']:.1f} minutes")
        print(f"  Games Played: {row['games_played']}")

def analyze_multiple_players(player_names: List[str], seasons: List[int] = None) -> pd.DataFrame:
    """
    Analyze impact for multiple players and compare
    """
    all_data = []
    
    for player_name in player_names:
        df = get_player_impact_data_advanced(player_name, seasons)
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
    pivot_impact = df.pivot(index='season', columns='player', values='player_impact_60')
    pivot_impact.index = pivot_impact.index.astype(str).str[:4] + '-' + pivot_impact.index.astype(str).str[4:]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each player's impact
    for player in pivot_impact.columns:
        ax.plot(pivot_impact.index, pivot_impact[player], marker='o', linewidth=2, label=player)
    
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_xlabel('Season')
    ax.set_ylabel('Player Impact (Goal Diff/60)')
    ax.set_title('Elite Player Impact Comparison')
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
    mcdavid_df = get_player_impact_data_advanced("Connor McDavid")
    
    if not mcdavid_df.empty:
        create_impact_visualization(mcdavid_df, "Connor McDavid")
        
        # Show the data
        print("\\nMcDavid Impact Data:")
        print(mcdavid_df[['season', 'on_ice_goal_diff_60', 'estimated_off_ice_goal_diff_60', 
                         'player_impact_60', 'toi_per_game']].to_string(index=False))
    
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
            'on_ice_goal_diff_60': 'mean',
            'estimated_off_ice_goal_diff_60': 'mean',
            'player_impact_60': 'mean'
        }).round(2)
        print(summary)

if __name__ == "__main__":
    main()
