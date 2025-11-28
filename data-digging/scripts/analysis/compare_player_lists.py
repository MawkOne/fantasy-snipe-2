from google.cloud import bigquery
import pandas as pd

def compare_player_lists():
    client = bigquery.Client()

    print("=== PLAYER LIST COMPARISON ===")
    print()

    # 1. Get players from shift metrics
    shift_query = """
    SELECT DISTINCT player_id
    FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics`
    ORDER BY player_id
    """
    shift_players = set(row.player_id for row in client.query(shift_query).result())
    print(f"1. Players in shift_metrics: {len(shift_players)}")

    # 2. Get players from players table
    players_query = """
    SELECT DISTINCT player_id
    FROM `fantasy-snipe-ai.nhl_raw.players`
    ORDER BY player_id
    """
    players_table = set(row.player_id for row in client.query(players_query).result())
    print(f"2. Players in players table: {len(players_table)}")

    # 3. Find differences
    in_shift_not_players = shift_players - players_table
    in_players_not_shift = players_table - shift_players
    common_players = shift_players & players_table

    print(f"3. Comparison:")
    print(f"   - Players in BOTH tables: {len(common_players)}")
    print(f"   - Players in shift_metrics but NOT in players: {len(in_shift_not_players)}")
    print(f"   - Players in players but NOT in shift_metrics: {len(in_players_not_shift)}")

    # 4. Show players missing from players table
    if in_shift_not_players:
        print(f"4. Players in shift_metrics but missing from players table:")
        missing_sample = sorted(list(in_shift_not_players))[:20]  # Show first 20
        for player_id in missing_sample:
            print(f"   - Player ID: {player_id}")
        if len(in_shift_not_players) > 20:
            print(f"   ... and {len(in_shift_not_players) - 20} more")

    # 5. Show players missing from shift_metrics
    if in_players_not_shift:
        print(f"5. Players in players table but missing from shift_metrics:")
        missing_sample = sorted(list(in_players_not_shift))[:20]  # Show first 20
        for player_id in missing_sample:
            print(f"   - Player ID: {player_id}")
        if len(in_players_not_shift) > 20:
            print(f"   ... and {len(in_players_not_shift) - 20} more")

    # 6. Check coverage by season
    print(f"6. Coverage by season:")
    season_query = """
    SELECT 
      g.season,
      COUNT(DISTINCT psm.player_id) as shift_players,
      COUNT(DISTINCT p.player_id) as players_table_count
    FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm
    JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = psm.game_id
    LEFT JOIN `fantasy-snipe-ai.nhl_raw.players` p ON p.player_id = psm.player_id
    GROUP BY g.season
    ORDER BY g.season DESC
    """
    for row in client.query(season_query).result():
        season = str(row['season'])
        season_formatted = f"{season[:4]}-{season[4:]}"
        print(f"   - {season_formatted}: {row['shift_players']} shift players, {row['players_table_count']} with details")

    # 7. Check specific high-profile players
    print(f"7. High-profile players check:")
    high_profile_query = """
    SELECT 
      p.player_id,
      p.full_name,
      CASE WHEN psm.player_id IS NOT NULL THEN 'YES' ELSE 'NO' END as in_shift_metrics,
      CASE WHEN p.player_id IS NOT NULL THEN 'YES' ELSE 'NO' END as in_players_table
    FROM `fantasy-snipe-ai.nhl_raw.players` p
    LEFT JOIN `fantasy-snipe-ai.nhl_processed.player_shift_metrics` psm ON psm.player_id = p.player_id
    WHERE p.full_name IN ('Connor McDavid', 'Leon Draisaitl', 'Sidney Crosby', 'Alexander Ovechkin', 'Nathan MacKinnon')
    GROUP BY p.player_id, p.full_name, psm.player_id
    ORDER BY p.full_name
    """
    for row in client.query(high_profile_query).result():
        print(f"   - {row['full_name']}: Shift metrics={row['in_shift_metrics']}, Players table={row['in_players_table']}")

    # 8. Calculate overlap percentage
    if shift_players:
        overlap_pct = (len(common_players) / len(shift_players)) * 100
        print(f"8. Overlap: {overlap_pct:.1f}% of shift_metrics players have details in players table")

    print()
    print("=== COMPARISON COMPLETE ===")

if __name__ == "__main__":
    compare_player_lists()
