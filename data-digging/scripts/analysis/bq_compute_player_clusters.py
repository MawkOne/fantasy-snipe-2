import argparse
from google.cloud import bigquery


def ensure_tables(client: bigquery.Client) -> None:
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_processed`").result()
    # Cluster keys (id -> label for each dimension)
    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_processed.player_cluster_keys` (
          dim STRING,  -- 'line_role' | 'style' | 'position_group'
          id INT64,
          label STRING
        )
        """
    ).result()
    # Upsert default keys
    client.query(
        """
        MERGE `fantasy-snipe-ai.nhl_processed.player_cluster_keys` T
        USING (
          SELECT * FROM UNNEST([
            STRUCT('line_role' AS dim, 1 AS id, '1st line' AS label),
            STRUCT('line_role', 2, '2nd line'),
            STRUCT('line_role', 3, 'bottom 6'),
            STRUCT('style', 0, 'Elite'),
            STRUCT('style', 1, 'Playmaker'),
            STRUCT('style', 2, 'Sniper'),
            STRUCT('style', 3, 'Power Forward'),
            STRUCT('style', 4, 'Forechecker'),
            STRUCT('style', 5, 'Off Defence'),
            STRUCT('style', 6, 'Def Defence'),
            STRUCT('position_group', 1, 'Center'),
            STRUCT('position_group', 2, 'Wing'),
            STRUCT('position_group', 3, 'Defence')
          ])
        ) S
        ON T.dim=S.dim AND T.id=S.id
        WHEN MATCHED THEN UPDATE SET label=S.label
        WHEN NOT MATCHED THEN INSERT (dim,id,label) VALUES (S.dim,S.id,S.label)
        """
    ).result()

    # Output clusters table
    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_processed.player_season_clusters` (
          player_id INT64,
          season INT64,
          position_group STRING,
          line_role STRING,
          style STRING,
          games INT64,
          avg_toi_seconds FLOAT64,
          gf60 FLOAT64,
          sf60 FLOAT64,
          cf_pct FLOAT64,
          hits_per60 FLOAT64,
          blocks_per60 FLOAT64,
          s60 FLOAT64,
          g60 FLOAT64,
          a60 FLOAT64,
          a_share FLOAT64,
          shooting_pct FLOAT64
        )
        """
    ).result()
    # Add new feature columns if missing
    for col, typ in [
        ("s60", "FLOAT64"),
        ("g60", "FLOAT64"),
        ("a60", "FLOAT64"),
        ("a_share", "FLOAT64"),
        ("shooting_pct", "FLOAT64"),
    ]:
        try:
            client.query(f"ALTER TABLE `fantasy-snipe-ai.nhl_processed.player_season_clusters` ADD COLUMN IF NOT EXISTS {col} {typ}").result()
        except Exception:
            pass


def run_compute(client: bigquery.Client, season: int | None) -> None:
    ensure_tables(client)
    where_season = f"WHERE g.season={int(season)}" if season is not None else ""

    # Aggregate per-player-season features
    q = f"""
    MERGE `fantasy-snipe-ai.nhl_processed.player_season_clusters` T
    USING (
      WITH pos AS (
        SELECT id AS player_id,
               CASE position_code
                 WHEN 'C' THEN 'Center'
                 WHEN 'L' THEN 'Wing'
                 WHEN 'R' THEN 'Wing'
                 WHEN 'D' THEN 'Defence'
                 ELSE NULL
               END AS position_group
        FROM `fantasy-snipe-ai.nhl_raw.players`
      ), flat AS (
        SELECT pf.player_id, g.season,
               SUM(pf.TOI_seconds) AS toi_s,
               COUNT(*) AS games,
               SUM(pf.GF) AS GF,
               SUM(pf.SF) AS SF,
               AVG(pf.CF_pct) AS cf_pct,
               SAFE_DIVIDE(SUM(pf.GF), NULLIF(SUM(pf.TOI_seconds),0)) * 3600 AS gf60,
               SAFE_DIVIDE(SUM(pf.SF), NULLIF(SUM(pf.TOI_seconds),0)) * 3600 AS sf60
        FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat` pf
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = pf.game_id
        {where_season}
        GROUP BY pf.player_id, g.season
      ), hits_blocks AS (
        SELECT m.player_id, g.season,
               SAFE_DIVIDE(SUM(m.hits_for), NULLIF(SUM(SAFE_CAST(SPLIT(m.duration, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(m.duration, ':')[SAFE_OFFSET(1)] AS INT64)),0)) * 3600 AS hits_per60,
               SAFE_DIVIDE(SUM(m.blocks_for), NULLIF(SUM(SAFE_CAST(SPLIT(m.duration, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(m.duration, ':')[SAFE_OFFSET(1)] AS INT64)),0)) * 3600 AS blocks_per60
        FROM `fantasy-snipe-ai.nhl_processed.player_shift_metrics` m
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = m.game_id
        {where_season}
        GROUP BY m.player_id, g.season
      ), rates AS (
        SELECT s.player_id, g.season,
               SUM(s.goals) AS goals,
               SUM(s.assists) AS assists,
               SUM(s.shots) AS shots,
               SUM(SAFE_CAST(SPLIT(s.toi, ':' )[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(s.toi, ':' )[SAFE_OFFSET(1)] AS INT64)) AS toi_s
        FROM `fantasy-snipe-ai.nhl_raw.player_game_stats` s
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id=s.game_id
        {where_season}
        GROUP BY s.player_id, g.season
      ), feat AS (
        SELECT f.player_id, f.season, p.position_group,
               f.games,
               SAFE_DIVIDE(f.toi_s, NULLIF(f.games,0)) AS avg_toi_seconds,
               f.gf60, f.sf60, f.cf_pct,
               hb.hits_per60, hb.blocks_per60,
               SAFE_DIVIDE(r.shots, NULLIF(r.toi_s,0))*3600 AS s60,
               SAFE_DIVIDE(r.goals, NULLIF(r.toi_s,0))*3600 AS g60,
               SAFE_DIVIDE(r.assists, NULLIF(r.toi_s,0))*3600 AS a60,
               SAFE_DIVIDE(r.goals + r.assists, NULLIF(r.toi_s,0))*3600 AS pts60,
               SAFE_DIVIDE(SAFE_DIVIDE(r.assists, NULLIF(r.toi_s,0))*3600,
                          NULLIF(SAFE_DIVIDE(r.assists, NULLIF(r.toi_s,0))*3600 + SAFE_DIVIDE(r.goals, NULLIF(r.toi_s,0))*3600, 0)) AS a_share,
               SAFE_MULTIPLY(SAFE_DIVIDE(r.goals, NULLIF(r.shots,0)), 100.0) AS shooting_pct
        FROM flat f
        LEFT JOIN hits_blocks hb USING (player_id, season)
        LEFT JOIN rates r USING (player_id, season)
        LEFT JOIN pos p ON p.player_id = f.player_id
        WHERE p.position_group IS NOT NULL
      ), cuts AS (
        SELECT season,
               APPROX_QUANTILES(s60, 100)[OFFSET(85)] AS s60_p85,
               APPROX_QUANTILES(a60, 100)[OFFSET(85)] AS a60_p85,
               APPROX_QUANTILES(shooting_pct, 100)[OFFSET(55)] AS sh_pct_p55,
               APPROX_QUANTILES(a_share, 100)[OFFSET(45)] AS a_share_p45,
               APPROX_QUANTILES(hits_per60, 100)[OFFSET(90)] AS hits_p90,
               APPROX_QUANTILES(blocks_per60, 100)[OFFSET(75)] AS blocks_p75,
               APPROX_QUANTILES(cf_pct, 100)[OFFSET(50)] AS cf_med
        FROM feat
        GROUP BY season
      ), labeled AS (
        SELECT
          f.player_id, f.season, f.position_group, f.games,
          f.avg_toi_seconds, f.gf60, f.sf60, f.cf_pct, f.hits_per60, f.blocks_per60,
          f.s60, f.g60, f.a60, f.a_share, f.shooting_pct,
          -- Line role thresholds by position
          CASE
            WHEN f.position_group IN ('Center','Wing') AND f.avg_toi_seconds >= 18*60 THEN '1st line'
            WHEN f.position_group IN ('Center','Wing') AND f.avg_toi_seconds >= 14*60 THEN '2nd line'
            WHEN f.position_group IN ('Center','Wing') THEN 'bottom 6'
            WHEN f.position_group = 'Defence' AND f.avg_toi_seconds >= 22*60 THEN '1st line'
            WHEN f.position_group = 'Defence' AND f.avg_toi_seconds >= 19*60 THEN '2nd line'
            ELSE 'bottom 6'
          END AS line_role,
          -- Style rules: Elite = possession dominance + goal generation + high usage + elite scoring, then specific roles
          CASE
            WHEN f.position_group IN ('Center','Wing') AND f.cf_pct >= 55.0 AND f.gf60 >= 24.0 AND f.avg_toi_seconds >= 1200 THEN 'Elite'
            WHEN f.position_group IN ('Center','Wing') AND f.s60 >= c.s60_p85 AND f.shooting_pct >= c.sh_pct_p55 THEN 'Sniper'
            WHEN f.position_group IN ('Center','Wing') AND f.a60 >= c.a60_p85 AND f.a_share >= c.a_share_p45 AND f.cf_pct >= c.cf_med THEN 'Playmaker'
            WHEN f.position_group IN ('Center','Wing') AND f.hits_per60 >= c.hits_p90 THEN 'Power Forward'
            WHEN f.position_group = 'Defence' AND f.cf_pct >= c.cf_med THEN 'Off Defence'
            WHEN f.position_group = 'Defence' AND f.blocks_per60 >= c.blocks_p75 AND f.cf_pct < c.cf_med THEN 'Def Defence'
            WHEN f.position_group IN ('Center','Wing') THEN 'Forechecker'
            ELSE 'Off Defence'
          END AS style
        FROM feat f
        JOIN cuts c USING (season)
      )
      SELECT player_id, season, position_group, line_role, style, games,
             avg_toi_seconds, gf60, sf60, cf_pct, hits_per60, blocks_per60,
             s60, g60, a60, a_share, shooting_pct
      FROM labeled
    ) S
    ON T.player_id=S.player_id AND T.season=S.season
    WHEN MATCHED THEN UPDATE SET
      position_group=S.position_group,
      line_role=S.line_role,
      style=S.style,
      games=S.games,
      avg_toi_seconds=S.avg_toi_seconds,
      gf60=S.gf60,
      sf60=S.sf60,
      cf_pct=S.cf_pct,
      hits_per60=S.hits_per60,
      blocks_per60=S.blocks_per60,
      s60=S.s60,
      g60=S.g60,
      a60=S.a60,
      a_share=S.a_share,
      shooting_pct=S.shooting_pct
    WHEN NOT MATCHED THEN INSERT (
      player_id, season, position_group, line_role, style, games, avg_toi_seconds,
      gf60, sf60, cf_pct, hits_per60, blocks_per60, s60, g60, a60, a_share, shooting_pct
    ) VALUES (
      S.player_id, S.season, S.position_group, S.line_role, S.style, S.games, S.avg_toi_seconds,
      S.gf60, S.sf60, S.cf_pct, S.hits_per60, S.blocks_per60, S.s60, S.g60, S.a60, S.a_share, S.shooting_pct
    )
    """
    client.query(q).result()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=None)
    args = ap.parse_args()
    client = bigquery.Client()
    run_compute(client, args.season)
    print("Completed player clusters compute.")


if __name__ == "__main__":
    main()


