#!/usr/bin/env python3

from google.cloud import bigquery
import pandas as pd

def filter_roster_quality():
    """Filter out low-quality players not worth forecasting"""
    
    client = bigquery.Client()
    
    print("="*80)
    print("FILTERING ROSTER QUALITY - REMOVING PLAYERS NOT WORTH FORECASTING")
    print("="*80)
    
    # Check the distribution of players in our projected rosters
    query = """
    SELECT 
        COUNT(*) as total_players,
        COUNT(CASE WHEN toi_tier = "Elite" THEN 1 END) as elite_players,
        COUNT(CASE WHEN toi_tier = "Top Line" THEN 1 END) as top_line_players,
        COUNT(CASE WHEN toi_tier = "Middle 6" THEN 1 END) as middle_6_players,
        COUNT(CASE WHEN toi_tier = "Bottom 6" THEN 1 END) as bottom_6_players,
        COUNT(CASE WHEN toi_tier = "Depth" THEN 1 END) as depth_players
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    """
    
    results = client.query(query).to_dataframe()
    
    print('Current projected rosters distribution:')
    print('=' * 50)
    for col in results.columns:
        print(f'{col:20}: {results[col].iloc[0]}')
    
    total_players = results['total_players'].iloc[0]
    depth_players = results['depth_players'].iloc[0]
    
    print(f'\nTotal players: {total_players}')
    print(f'Depth players (likely not worth forecasting): {depth_players}')
    print(f'Percentage that are depth: {depth_players / total_players * 100:.1f}%')
    
    # Get players by TOI tier to see what we're working with
    query2 = """
    SELECT 
        toi_tier,
        COUNT(*) as player_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    GROUP BY toi_tier
    ORDER BY 
        CASE toi_tier
            WHEN 'Elite' THEN 1
            WHEN 'Top Line' THEN 2
            WHEN 'Middle 6' THEN 3
            WHEN 'Bottom 6' THEN 4
            WHEN 'Depth' THEN 5
            ELSE 6
        END
    """
    
    results2 = client.query(query2).to_dataframe()
    
    print('\nTOI Tier Distribution:')
    print('=' * 30)
    for _, row in results2.iterrows():
        print(f'{row.toi_tier:10}: {row.player_count:4} players ({row.percentage:5.1f}%)')
    
    # Check what the CBS projections file looks like
    print('\nChecking CBS projections file...')
    try:
        cbs_data = pd.read_csv('/Users/markhenderson/Cursor Projects/NHL-API/docs/CBS/post_draft/projections.csv')
        print(f'CBS projections file has {len(cbs_data)} players')
        
        # Check if there's a ranking column
        print('CBS file columns:', list(cbs_data.columns))
        
        # Look for ranking or similar columns
        rank_cols = [col for col in cbs_data.columns if 'rank' in col.lower() or 'overall' in col.lower()]
        if rank_cols:
            print(f'Potential ranking columns: {rank_cols}')
            # Show some sample data
            print('\nSample CBS data:')
            print(cbs_data[rank_cols].head(10))
        
    except Exception as e:
        print(f'Error reading CBS file: {e}')
    
    # Create a filtered roster that excludes depth players
    print('\nCreating filtered roster (excluding depth players)...')
    
    filtered_query = """
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    WHERE toi_tier != 'Depth'
    ORDER BY team_abbr, 
        CASE toi_tier
            WHEN 'Elite' THEN 1
            WHEN 'Top Line' THEN 2
            WHEN 'Middle 6' THEN 3
            WHEN 'Bottom 6' THEN 4
            ELSE 5
        END,
        player_name
    """
    
    filtered_results = client.query(filtered_query).to_dataframe()
    
    print(f'Filtered roster: {len(filtered_results)} players (removed {total_players - len(filtered_results)} depth players)')
    
    # Show distribution by team
    team_counts = filtered_results.groupby('team_abbr').size().sort_values(ascending=False)
    
    print('\nPlayers per team (filtered):')
    print('=' * 30)
    for team, count in team_counts.items():
        print(f'{team:4}: {count:2} players')
    
    print(f'\nAverage players per team: {len(filtered_results) / 32:.1f}')
    print(f'Range: {team_counts.min()} - {team_counts.max()} players per team')
    
    # Show some examples of what we're filtering out
    depth_query = """
    SELECT 
        team_abbr,
        player_name,
        position_type,
        toi_tier
    FROM `fantasy-snipe-ai.nhl_projections.projected_rosters_2025_26`
    WHERE toi_tier = 'Depth'
    ORDER BY team_abbr, player_name
    LIMIT 20
    """
    
    depth_results = client.query(depth_query).to_dataframe()
    
    print('\nExamples of depth players being filtered out:')
    print('=' * 50)
    for _, row in depth_results.iterrows():
        print(f'{row.team_abbr:4} | {row.player_name:25} | {row.position_type:8}')
    
    if len(depth_results) > 20:
        print(f'... and {len(depth_results) - 20} more depth players')
    
    print(f'\n✅ Analysis complete!')
    print(f'Recommendation: Use filtered roster with {len(filtered_results)} players')
    print(f'This removes {total_players - len(filtered_results)} depth players not worth forecasting')

if __name__ == "__main__":
    filter_roster_quality()
