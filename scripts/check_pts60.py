from google.cloud import bigquery

def check_pts60():
    client = bigquery.Client()

    # Check pts60 values
    query = """
    SELECT 
      player_id, 
      full_name, 
      season, 
      pts60, 
      CF60, 
      GF60,
      TOI_seconds
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
    WHERE game_type = 2
    AND pts60 IS NOT NULL
    AND pts60 > 0
    ORDER BY pts60 DESC
    LIMIT 10
    """

    print("Top 10 players by PTS60:")
    for row in client.query(query).result():
        print(f"  {row['full_name']} - Season: {row['season']} - PTS60: {row['pts60']:.2f} - TOI: {row['TOI_seconds']}")

    # Check if pts60 is mostly null/zero
    query2 = """
    SELECT 
      COUNT(*) as total,
      COUNT(CASE WHEN pts60 IS NULL THEN 1 END) as null_pts60,
      COUNT(CASE WHEN pts60 = 0 THEN 1 END) as zero_pts60,
      COUNT(CASE WHEN pts60 > 0 THEN 1 END) as positive_pts60
    FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
    WHERE game_type = 2
    """

    result = list(client.query(query2).result())[0]
    print(f"\nPTS60 distribution:")
    print(f"  Total records: {result['total']}")
    print(f"  NULL pts60: {result['null_pts60']}")
    print(f"  Zero pts60: {result['zero_pts60']}")
    print(f"  Positive pts60: {result['positive_pts60']}")

if __name__ == "__main__":
    check_pts60()
