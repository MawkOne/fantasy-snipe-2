import argparse
from typing import Optional, List

from google.cloud import bigquery


def ensure_processed_tables(client: bigquery.Client) -> None:
    client.query("CREATE SCHEMA IF NOT EXISTS `fantasy-snipe-ai.nhl_processed`").result()
    client.query(
        """
        CREATE TABLE IF NOT EXISTS `fantasy-snipe-ai.nhl_processed.player_shift_metrics` (
          player_id INT64,
          game_id INT64,
          team_id INT64,
          shift_number INT64,
          period INT64,
          start_time STRING,
          end_time STRING,
          duration STRING,
          attempts_for INT64,
          attempts_against INT64,
          unblocked_for INT64,
          unblocked_against INT64,
          shots_for INT64,
          shots_against INT64,
          goals_for INT64,
          goals_against INT64,
          hits_for INT64,
          hits_against INT64,
          takeaways_for INT64,
          takeaways_against INT64,
          giveaways_for INT64,
          giveaways_against INT64,
          blocks_for INT64,
          blocks_against INT64,
          zone_start STRING,
          faceoff_won BOOL,
          strength_state STRING,
          teammates_on_ice INT64,
          opponents_on_ice INT64,
          teammates_on_ice_ids ARRAY<INT64>,
          opponents_on_ice_ids ARRAY<INT64>
        )
        """
    ).result()


def build_filters(season: Optional[int], game_type: Optional[int], game_id: Optional[int]) -> List[str]:
    filters: List[str] = []
    if game_id is not None:
        filters.append(f"g.id = {int(game_id)}")
    else:
        if season is not None:
            filters.append(f"g.season = {int(season)}")
        if game_type is not None:
            filters.append(f"g.game_type = {int(game_type)}")
    return filters


def run_compute(client: bigquery.Client, season: Optional[int], game_type: Optional[int], game_id: Optional[int]) -> None:
    ensure_processed_tables(client)
    where = build_filters(season, game_type, game_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    query = f"""
    MERGE `fantasy-snipe-ai.nhl_processed.player_shift_metrics` T
    USING (
      WITH shifts AS (
        SELECT s.player_id, s.game_id, g.season, g.game_type, s.team_id, s.shift_number, s.period,
               s.start_time, s.end_time, s.duration,
               SAFE_CAST(SPLIT(s.start_time, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(s.start_time, ':')[SAFE_OFFSET(1)] AS INT64) AS start_s,
               SAFE_CAST(SPLIT(s.end_time, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(s.end_time, ':')[SAFE_OFFSET(1)] AS INT64) AS end_s
        FROM `fantasy-snipe-ai.nhl_raw.player_shifts` s
        JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = s.game_id
        {where_sql}
      ), ev AS (
        SELECT * FROM (
          SELECT e.game_id, e.period, e.event_idx,
                 SAFE_CAST(SPLIT(e.period_time, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(e.period_time, ':')[SAFE_OFFSET(1)] AS INT64) AS tsec,
                 e.team_id,
                 CAST(e.coordinates_x AS FLOAT64) AS x,
                 CASE
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) IN ('SHOT','SHOT_ON_GOAL','SHOT-ON-GOAL') THEN 'SHOT'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) IN ('MISSED_SHOT','MISSED-SHOT','MISS') THEN 'MISSED_SHOT'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) IN ('BLOCKED_SHOT','BLOCKED-SHOT','BLOCK') THEN 'BLOCKED_SHOT'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) = 'GOAL' THEN 'GOAL'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) = 'FACEOFF' THEN 'FACEOFF'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) = 'HIT' THEN 'HIT'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) IN ('TAKEAWAY','TAKE') THEN 'TAKEAWAY'
                   WHEN UPPER(COALESCE(e.event_type_id, e.event_type)) IN ('GIVEAWAY','GIVE') THEN 'GIVEAWAY'
                   ELSE UPPER(COALESCE(e.event_type_id, e.event_type))
                 END AS ev_type
          FROM `fantasy-snipe-ai.nhl_raw.game_events` e
          JOIN `fantasy-snipe-ai.nhl_raw.games` g ON g.id = e.game_id
          {where_sql}
        )
        QUALIFY ROW_NUMBER() OVER (PARTITION BY game_id, period, event_idx ORDER BY event_idx) = 1
      ), ev_join AS (
        SELECT s.player_id, s.game_id, s.team_id, s.shift_number, s.period,
               s.start_time, s.end_time, s.duration, s.start_s, s.end_s,
               ev.ev_type, ev.team_id AS ev_team_id
        FROM shifts s
        LEFT JOIN ev
          ON ev.game_id = s.game_id
         AND ev.period = s.period
         AND ev.tsec BETWEEN s.start_s - 1 AND s.end_s + 1
      ), attempts_agg AS (
        SELECT
          player_id, game_id, team_id, shift_number, period, start_time, end_time, duration, start_s
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL','MISSED_SHOT','BLOCKED_SHOT') AND ev_team_id = team_id THEN 1 ELSE 0 END) AS attempts_for
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL','MISSED_SHOT','BLOCKED_SHOT') AND ev_team_id != team_id THEN 1 ELSE 0 END) AS attempts_against
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL','MISSED_SHOT') AND ev_team_id = team_id THEN 1 ELSE 0 END) AS unblocked_for
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL','MISSED_SHOT') AND ev_team_id != team_id THEN 1 ELSE 0 END) AS unblocked_against
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL') AND ev_team_id = team_id THEN 1 ELSE 0 END) AS shots_for
        , SUM(CASE WHEN ev_type IN ('SHOT','GOAL') AND ev_team_id != team_id THEN 1 ELSE 0 END) AS shots_against
        , SUM(CASE WHEN ev_type = 'GOAL' AND ev_team_id = team_id THEN 1 ELSE 0 END) AS goals_for
        , SUM(CASE WHEN ev_type = 'GOAL' AND ev_team_id != team_id THEN 1 ELSE 0 END) AS goals_against
        , SUM(CASE WHEN ev_type = 'HIT' AND ev_team_id = team_id THEN 1 ELSE 0 END) AS hits_for
        , SUM(CASE WHEN ev_type = 'HIT' AND ev_team_id != team_id THEN 1 ELSE 0 END) AS hits_against
        , SUM(CASE WHEN ev_type = 'TAKEAWAY' AND ev_team_id = team_id THEN 1 ELSE 0 END) AS takeaways_for
        , SUM(CASE WHEN ev_type = 'TAKEAWAY' AND ev_team_id != team_id THEN 1 ELSE 0 END) AS takeaways_against
        , SUM(CASE WHEN ev_type = 'GIVEAWAY' AND ev_team_id = team_id THEN 1 ELSE 0 END) AS giveaways_for
        , SUM(CASE WHEN ev_type = 'GIVEAWAY' AND ev_team_id != team_id THEN 1 ELSE 0 END) AS giveaways_against
        , SUM(CASE WHEN ev_type = 'BLOCKED_SHOT' AND ev_team_id = team_id THEN 1 ELSE 0 END) AS blocks_for
        , SUM(CASE WHEN ev_type = 'BLOCKED_SHOT' AND ev_team_id != team_id THEN 1 ELSE 0 END) AS blocks_against
        FROM ev_join
        GROUP BY player_id, game_id, team_id, shift_number, period, start_time, end_time, duration, start_s
      ), faceoff_near AS (
        SELECT s.player_id, s.game_id, s.shift_number,
               fe.x, fe.team_id AS fo_team_id,
               ROW_NUMBER() OVER (PARTITION BY s.player_id, s.game_id, s.shift_number ORDER BY ABS(fe.tsec - s.start_s)) AS rn
        FROM shifts s
        JOIN ev fe
          ON fe.game_id = s.game_id AND fe.period = s.period AND fe.ev_type = 'FACEOFF'
         AND ABS(fe.tsec - s.start_s) <= 3
      ), faceoff_pick AS (
        SELECT s.player_id, s.game_id, s.shift_number,
               CASE
                 WHEN fn.x IS NULL THEN NULL
                 WHEN fn.fo_team_id = s.team_id THEN CASE WHEN fn.x > 25 THEN 'O' WHEN fn.x < -25 THEN 'D' ELSE 'N' END
                 ELSE CASE WHEN fn.x > 25 THEN 'D' WHEN fn.x < -25 THEN 'O' ELSE 'N' END
               END AS zone_start,
               CASE WHEN fn.fo_team_id IS NULL THEN NULL ELSE (fn.fo_team_id = s.team_id) END AS faceoff_won
        FROM shifts s
        LEFT JOIN faceoff_near fn
          ON fn.player_id = s.player_id AND fn.game_id = s.game_id AND fn.shift_number = s.shift_number AND fn.rn = 1
      ), on_ice AS (
        SELECT s.player_id, s.game_id, s.shift_number,
               COUNTIF(ps.team_id = s.team_id) AS teammates_on_ice,
               COUNTIF(ps.team_id != s.team_id) AS opponents_on_ice,
               ARRAY_AGG(IF(ps.team_id = s.team_id, CAST(ps.player_id AS INT64), NULL) IGNORE NULLS ORDER BY ps.player_id) AS teammates_on_ice_ids,
               ARRAY_AGG(IF(ps.team_id != s.team_id, CAST(ps.player_id AS INT64), NULL) IGNORE NULLS ORDER BY ps.player_id) AS opponents_on_ice_ids
        FROM shifts s
        JOIN `fantasy-snipe-ai.nhl_raw.player_shifts` ps
          ON ps.game_id = s.game_id AND ps.period = s.period
         AND (SAFE_CAST(SPLIT(ps.start_time, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(ps.start_time, ':')[SAFE_OFFSET(1)] AS INT64)) <= s.start_s
         AND s.start_s < (SAFE_CAST(SPLIT(ps.end_time, ':')[SAFE_OFFSET(0)] AS INT64)*60 + SAFE_CAST(SPLIT(ps.end_time, ':')[SAFE_OFFSET(1)] AS INT64))
        GROUP BY s.player_id, s.game_id, s.shift_number
      )
      , src AS (
        SELECT
          a.player_id, a.game_id, a.shift_number,
          ANY_VALUE(a.team_id) AS team_id,
          ANY_VALUE(a.period) AS period,
          ANY_VALUE(a.start_time) AS start_time,
          ANY_VALUE(a.end_time) AS end_time,
          ANY_VALUE(a.duration) AS duration,
          SUM(a.attempts_for) AS attempts_for,
          SUM(a.attempts_against) AS attempts_against,
          SUM(a.unblocked_for) AS unblocked_for,
          SUM(a.unblocked_against) AS unblocked_against,
          SUM(a.shots_for) AS shots_for,
          SUM(a.shots_against) AS shots_against,
          SUM(a.goals_for) AS goals_for,
          SUM(a.goals_against) AS goals_against,
          SUM(a.hits_for) AS hits_for,
          SUM(a.hits_against) AS hits_against,
          SUM(a.takeaways_for) AS takeaways_for,
          SUM(a.takeaways_against) AS takeaways_against,
          SUM(a.giveaways_for) AS giveaways_for,
          SUM(a.giveaways_against) AS giveaways_against,
          SUM(a.blocks_for) AS blocks_for,
          SUM(a.blocks_against) AS blocks_against,
          ANY_VALUE(fp.zone_start) AS zone_start,
          ANY_VALUE(fp.faceoff_won) AS faceoff_won,
          ANY_VALUE(CASE
            WHEN oi.teammates_on_ice > oi.opponents_on_ice THEN 'PP'
            WHEN oi.teammates_on_ice < oi.opponents_on_ice THEN 'SH'
            ELSE 'EV'
          END) AS strength_state,
          ANY_VALUE(oi.teammates_on_ice) AS teammates_on_ice,
          ANY_VALUE(oi.opponents_on_ice) AS opponents_on_ice,
          ANY_VALUE(oi.teammates_on_ice_ids) AS teammates_on_ice_ids,
          ANY_VALUE(oi.opponents_on_ice_ids) AS opponents_on_ice_ids
        FROM attempts_agg a
        LEFT JOIN faceoff_pick fp
          ON fp.player_id = a.player_id AND fp.game_id = a.game_id AND fp.shift_number = a.shift_number
        LEFT JOIN on_ice oi
          ON oi.player_id = a.player_id AND oi.game_id = a.game_id AND oi.shift_number = a.shift_number
        GROUP BY a.player_id, a.game_id, a.shift_number
      )
      SELECT * FROM src
    ) S
    ON T.player_id = S.player_id AND T.game_id = S.game_id AND T.shift_number = S.shift_number
    WHEN MATCHED THEN UPDATE SET
      team_id = S.team_id,
      period = S.period,
      start_time = S.start_time,
      end_time = S.end_time,
      duration = S.duration,
      attempts_for = S.attempts_for,
      attempts_against = S.attempts_against,
      unblocked_for = S.unblocked_for,
      unblocked_against = S.unblocked_against,
      shots_for = S.shots_for,
      shots_against = S.shots_against,
      goals_for = S.goals_for,
      goals_against = S.goals_against,
      hits_for = S.hits_for,
      hits_against = S.hits_against,
      takeaways_for = S.takeaways_for,
      takeaways_against = S.takeaways_against,
      giveaways_for = S.giveaways_for,
      giveaways_against = S.giveaways_against,
      blocks_for = S.blocks_for,
      blocks_against = S.blocks_against,
      zone_start = S.zone_start,
      faceoff_won = S.faceoff_won,
      strength_state = S.strength_state,
      teammates_on_ice = S.teammates_on_ice,
      opponents_on_ice = S.opponents_on_ice,
      teammates_on_ice_ids = S.teammates_on_ice_ids,
      opponents_on_ice_ids = S.opponents_on_ice_ids
    WHEN NOT MATCHED THEN INSERT (
      player_id, game_id, team_id, shift_number, period, start_time, end_time, duration,
      attempts_for, attempts_against, unblocked_for, unblocked_against, shots_for, shots_against,
      goals_for, goals_against, hits_for, hits_against, takeaways_for, takeaways_against,
      giveaways_for, giveaways_against, blocks_for, blocks_against,
      zone_start, faceoff_won, strength_state, teammates_on_ice, opponents_on_ice,
      teammates_on_ice_ids, opponents_on_ice_ids
    ) VALUES (
      S.player_id, S.game_id, S.team_id, S.shift_number, S.period, S.start_time, S.end_time, S.duration,
      S.attempts_for, S.attempts_against, S.unblocked_for, S.unblocked_against, S.shots_for, S.shots_against,
      S.goals_for, S.goals_against, S.hits_for, S.hits_against, S.takeaways_for, S.takeaways_against,
      S.giveaways_for, S.giveaways_against, S.blocks_for, S.blocks_against,
      S.zone_start, S.faceoff_won, S.strength_state, S.teammates_on_ice, S.opponents_on_ice,
      S.teammates_on_ice_ids, S.opponents_on_ice_ids
    )
    """
    client.query(query).result()


def main() -> None:
    p = argparse.ArgumentParser(description="Compute player_shift_metrics into nhl_processed from nhl_raw in BigQuery")
    p.add_argument("--season", type=int, default=None)
    p.add_argument("--game-type", type=int, default=None)
    p.add_argument("--game-id", type=int, default=None)
    args = p.parse_args()
    client = bigquery.Client()
    run_compute(client, args.season, args.game_type, args.game_id)
    print("Completed BigQuery player_shift_metrics compute.")


if __name__ == "__main__":
    main()


