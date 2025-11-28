from google.cloud import bigquery

def debug_age_curves():
    client = bigquery.Client()

    print("=== DEBUGGING AGE CURVE QUERY ===")

    # 1. Check if we have data in player_game_advanced_metrics_flat
    query1 = "SELECT COUNT(*) as count FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`"
    result1 = list(client.query(query1).result())
    print(f"1. player_game_advanced_metrics_flat records: {result1[0]['count']}")

    # 2. Check if we have data in players table
    query2 = "SELECT COUNT(*) as count FROM `fantasy-snipe-ai.nhl_raw.players`"
    result2 = list(client.query(query2).result())
    print(f"2. players table records: {result2[0]['count']}")

    # 3. Check the join between them
    query3 = """
    SELECT COUNT(*) as count
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON p.player_id = pgm.player_id
    WHERE pgm.game_type = 2
    """
    result3 = list(client.query(query3).result())
    print(f"3. Joined records (game_type=2): {result3[0]['count']}")

    # 4. Check a sample of the data
    query4 = """
    SELECT pgm.player_id, p.full_name, p.birth_date, pgm.season, pgm.pts60
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pgm
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON p.player_id = pgm.player_id
    WHERE pgm.game_type = 2
    LIMIT 5
    """
    print("4. Sample data:")
    for row in client.query(query4).result():
        print(f"   - {row['player_id']}: {row['full_name']} - {row['birth_date']} - Season: {row['season']} - PTS60: {row['pts60']}")

    # 5. Check if we have the right columns
    query5 = """
    SELECT column_name, data_type
    FROM `fantasy-snipe-ai.nhl_processed.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'player_game_advanced_metrics_flat'
    ORDER BY ordinal_position
    """
    print("5. player_game_advanced_metrics_flat columns:")
    for row in client.query(query5).result():
        print(f"   - {row['column_name']}: {row['data_type']}")

    # 6. Check if we have the right columns in players table
    query6 = """
    SELECT column_name, data_type
    FROM `fantasy-snipe-ai.nhl_raw.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'players'
    ORDER BY ordinal_position
    """
    print("6. players table columns:")
    for row in client.query(query6).result():
        print(f"   - {row['column_name']}: {row['data_type']}")

if __name__ == "__main__":
    debug_age_curves()
