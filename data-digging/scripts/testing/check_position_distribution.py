from google.cloud import bigquery

def check_position_distribution():
    client = bigquery.Client()

    # Simple query to check position distribution
    query = """
    SELECT 
      p.position,
      CASE 
        WHEN p.position IN ('C', 'L', 'R') THEN 'Forward'
        WHEN p.position = 'D' THEN 'Defence'
        WHEN p.position = 'G' THEN 'Goalie'
        ELSE 'Other'
      END as position_group,
      COUNT(*) as count,
      AVG(pgm.avg_pts60) as avg_pts60,
      MIN(pgm.avg_pts60) as min_pts60,
      MAX(pgm.avg_pts60) as max_pts60
    FROM (
      SELECT 
        player_id,
        season,
        AVG(pts60) as avg_pts60
      FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
      WHERE game_type = 2
      AND pts60 IS NOT NULL
      AND pts60 > 0
      GROUP BY player_id, season
      HAVING COUNT(*) >= 20
    ) pgm
    JOIN `fantasy-snipe-ai.nhl_raw.players` p ON p.player_id = pgm.player_id
    GROUP BY p.position, position_group
    ORDER BY count DESC
    """

    print("Position distribution in PTS/60 analysis:")
    for row in client.query(query).result():
        print(f"  {row['position']} ({row['position_group']}): {row['count']} records")
        print(f"    - Avg PTS/60: {row['avg_pts60']:.2f}")
        print(f"    - Range: {row['min_pts60']:.2f} - {row['max_pts60']:.2f}")
        print()

if __name__ == "__main__":
    check_position_distribution()
