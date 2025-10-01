import argparse
from google.cloud import bigquery


def ensure_tables(client: bigquery.Client) -> None:
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_processed`").result()
    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics` (
          player_id INT64,
          game_id INT64,
          team_id INT64,
          season INT64,
          game_type INT64,
          summary STRING
        )
        """
    ).result()


def run_compute(client: bigquery.Client, season: int | None, game_type: int | None, game_id: int | None) -> None:
    ensure_tables(client)
    w = []
    if game_id is not None:
        w.append(f"game_id={int(game_id)}")
    if season is not None:
        w.append(f"season={int(season)}")
    if game_type is not None:
        w.append(f"game_type={int(game_type)}")
    where = ("WHERE " + " AND ".join(w)) if w else ""

    query = f"""
    MERGE `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics` T
    USING (
      WITH flat AS (
        SELECT * FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
        {where}
      ), agg AS (
        SELECT
          player_id,
          game_id,
          ANY_VALUE(team_id) AS team_id,
          ANY_VALUE(season) AS season,
          ANY_VALUE(game_type) AS game_type,
          SUM(CF) AS CF,
          SUM(CA) AS CA,
          SUM(FF) AS FF,
          SUM(FA) AS FA,
          SUM(SF) AS SF,
          SUM(SA) AS SA,
          SUM(GF) AS GF,
          SUM(GA) AS GA,
          SUM(TOI_seconds) AS TOI_seconds,
          SUM(shifts) AS shifts
        FROM flat
        GROUP BY player_id, game_id
      )
      SELECT
        player_id, game_id, team_id, season, game_type,
        TO_JSON_STRING(STRUCT(
          STRUCT(
            CF, CA, FF, FA, SF, SA, GF, GA,
            SAFE_DIVIDE(CF, NULLIF(CF+CA,0)) * 100 AS CF_pct,
            SAFE_DIVIDE(FF, NULLIF(FF+FA,0)) * 100 AS FF_pct,
            SAFE_DIVIDE(SF, NULLIF(SF+SA,0)) * 100 AS SF_pct,
            SAFE_DIVIDE(GF, NULLIF(GF+GA,0)) * 100 AS GF_pct,
            SAFE_DIVIDE(CF, NULLIF(TOI_seconds,0)) * 3600 AS CF60,
            SAFE_DIVIDE(FF, NULLIF(TOI_seconds,0)) * 3600 AS FF60,
            SAFE_DIVIDE(SF, NULLIF(TOI_seconds,0)) * 3600 AS SF60,
            SAFE_DIVIDE(GF, NULLIF(TOI_seconds,0)) * 3600 AS GF60,
            NULL AS PDO,
            TOI_seconds, shifts
          ) AS totals
        )) AS summary
      FROM agg
    ) S
    ON T.player_id=S.player_id AND T.game_id=S.game_id
    WHEN MATCHED THEN UPDATE SET
      team_id=S.team_id, season=S.season, game_type=S.game_type, summary=S.summary
    WHEN NOT MATCHED THEN INSERT (player_id, game_id, team_id, season, game_type, summary)
    VALUES (S.player_id, S.game_id, S.team_id, S.season, S.game_type, S.summary)
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
    print("Completed BigQuery player_game_advanced_metrics compute.")


if __name__ == "__main__":
    main()


