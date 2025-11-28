import argparse
from google.cloud import bigquery


def ensure_tables(client: bigquery.Client) -> None:
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_processed`").result()
    
    # Check if pts60 column exists, if not recreate table
    try:
        # Try to query the table to see if pts60 exists
        client.query("SELECT pts60 FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` LIMIT 1").result()
        print("pts60 column already exists")
    except Exception:
        print("pts60 column does not exist, recreating table...")
        # Drop and recreate table with pts60 column
        client.query("DROP TABLE IF EXISTS `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`").result()
        client.query(
            """
            CREATE TABLE `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` (
              player_id INT64,
              game_id INT64,
              team_id INT64,
              season INT64,
              game_type INT64,
              CF INT64, CA INT64, FF INT64, FA INT64, SF INT64, SA INT64,
              GF INT64, GA INT64,
              CF_pct FLOAT64, FF_pct FLOAT64, SF_pct FLOAT64, GF_pct FLOAT64,
              CF60 FLOAT64, FF60 FLOAT64, SF60 FLOAT64, GF60 FLOAT64,
              PDO FLOAT64,
              TOI_seconds INT64,
              shifts INT64,
              pts60 FLOAT64
            )
            """
        ).result()
        print("Table recreated with pts60 column")


def run_compute(client: bigquery.Client, season: int | None, game_type: int | None, game_id: int | None) -> None:
    ensure_tables(client)
    w = []
    if game_id is not None:
        w.append(f"g.id={int(game_id)}")
    else:
        if season is not None:
            w.append(f"g.season={int(season)}")
        if game_type is not None:
            w.append(f"g.game_type={int(game_type)}")
    where = ("WHERE " + " AND ".join(w)) if w else ""

    # Derive flat per-game metrics from processed shift metrics
    query = f"""
    MERGE `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` T
    USING (
      WITH psm AS (
        SELECT m.*, g.season, g.game_type
        FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` m
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = m.game_id
        {where}
      ), pgs AS (
        SELECT pgs.player_id, pgs.game_id, pgs.goals, pgs.assists
        FROM `fantasy-snipe-ai.nhl_raw.player_game_stats` pgs
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = pgs.game_id
        {where}
      ), agg AS (
        SELECT
          psm.player_id,
          psm.game_id,
          ANY_VALUE(psm.team_id) AS team_id,
          ANY_VALUE(psm.season) AS season,
          ANY_VALUE(psm.game_type) AS game_type,
          SUM(psm.attempts_for) AS CF,
          SUM(psm.attempts_against) AS CA,
          SUM(psm.unblocked_for) AS FF,
          SUM(psm.unblocked_against) AS FA,
          SUM(psm.shots_for) AS SF,
          SUM(psm.shots_against) AS SA,
          SUM(psm.goals_for) AS GF,
          SUM(psm.goals_against) AS GA,
          SUM(
            SAFE_CAST(SPLIT(psm.duration, ':')[SAFE_OFFSET(0)] AS INT64) * 60 +
            SAFE_CAST(SPLIT(psm.duration, ':')[SAFE_OFFSET(1)] AS INT64)
          ) AS TOI_seconds,
          COUNT(*) AS shifts,
          ANY_VALUE(pgs.goals) AS goals,
          ANY_VALUE(pgs.assists) AS assists
        FROM psm
        LEFT JOIN pgs ON pgs.player_id = psm.player_id AND pgs.game_id = psm.game_id
        GROUP BY psm.player_id, psm.game_id
      )
      SELECT
        player_id, game_id, team_id, season, game_type,
        CF, CA, FF, FA, SF, SA, GF, GA,
        SAFE_DIVIDE(CF, NULLIF(CF+CA,0)) * 100 AS CF_pct,
        SAFE_DIVIDE(FF, NULLIF(FF+FA,0)) * 100 AS FF_pct,
        SAFE_DIVIDE(SF, NULLIF(SF+SA,0)) * 100 AS SF_pct,
        SAFE_DIVIDE(GF, NULLIF(GF+GA,0)) * 100 AS GF_pct,
        SAFE_DIVIDE(CF, NULLIF(TOI_seconds,0)) * 3600 AS CF60,
        SAFE_DIVIDE(FF, NULLIF(TOI_seconds,0)) * 3600 AS FF60,
        SAFE_DIVIDE(SF, NULLIF(TOI_seconds,0)) * 3600 AS SF60,
        SAFE_DIVIDE(GF, NULLIF(TOI_seconds,0)) * 3600 AS GF60,
        (SAFE_DIVIDE(GF, NULLIF(SF,0)) + (1 - SAFE_DIVIDE(GA, NULLIF(SA,0)))) * 1000 AS PDO,
        TOI_seconds,
        shifts,
        SAFE_DIVIDE(goals + assists, NULLIF(TOI_seconds,0)) * 3600 AS pts60
      FROM agg
    ) S
    ON T.player_id=S.player_id AND T.game_id=S.game_id
    WHEN MATCHED THEN UPDATE SET
      team_id=S.team_id, season=S.season, game_type=S.game_type,
      CF=S.CF, CA=S.CA, FF=S.FF, FA=S.FA, SF=S.SF, SA=S.SA,
      GF=S.GF, GA=S.GA,
      CF_pct=S.CF_pct, FF_pct=S.FF_pct, SF_pct=S.SF_pct, GF_pct=S.GF_pct,
      CF60=S.CF60, FF60=S.FF60, SF60=S.SF60, GF60=S.GF60,
      PDO=S.PDO, TOI_seconds=S.TOI_seconds, shifts=S.shifts, pts60=S.pts60
    WHEN NOT MATCHED THEN INSERT (
      player_id, game_id, team_id, season, game_type,
      CF, CA, FF, FA, SF, SA, GF, GA,
      CF_pct, FF_pct, SF_pct, GF_pct,
      CF60, FF60, SF60, GF60,
      PDO, TOI_seconds, shifts, pts60
    ) VALUES (
      S.player_id, S.game_id, S.team_id, S.season, S.game_type,
      S.CF, S.CA, S.FF, S.FA, S.SF, S.SA, S.GF, S.GA,
      S.CF_pct, S.FF_pct, S.SF_pct, S.GF_pct,
      S.CF60, S.FF60, S.SF60, S.GF60,
      S.PDO, S.TOI_seconds, S.shifts, S.pts60
    )
    """
    client.query(query).result()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=None)
    ap.add_argument("--game-type", type=int, default=None)
    ap.add_argument("--game-id", type=int, default=None)
    args = ap.parse_args()
    client = bigquery.Client()
    run_compute(client, args.season, args.game_type, args.game_id)
    print("Completed BigQuery player_game_advanced_metrics_flat compute.")


if __name__ == "__main__":
    main()


