## Game event raw JSON: fields and suggested columns

This document enumerates commonly present fields in the NHL event payloads we store in `game_events.raw`, and how they map to normalized columns in `game_events`. Use it when backfilling or expanding the schema.


### Current normalized columns in `game_events`
- id: int (PK)
- game_id: int
- event_idx: int (sequential index if provided)
- period: int
- period_time: string
- period_time_remaining: string
- event_type: string (raw type)
- secondary_type: string
- description: string
- team_id: int
- coordinates_x: float
- coordinates_y: float
- primary_player_id: int (proposed/added; main actor per event)
- raw: JSON (full payload)

### Potential normalized columns from raw (comprehensive)
- event_code (string) — from `result.eventCode`
- event_type_id (string) — from `result.eventTypeId`
- period_type (string) — from `about.periodType`
- event_datetime (string/ts) — from `about.dateTime`
- score_away_at_event (int) — from `about.goals.away`
- score_home_at_event (int) — from `about.goals.home`
- team_tricode_at_event (string) — from `about.team.triCode` or `team.triCode`
- event_owner_team_id (int) — from `details.eventOwnerTeamId`
- zone_code (string) — from `details.zoneCode` (O/D/N)
- strength_code (string) — from `result.strength.code`
- strength_name (string) — from `result.strength.name`
- empty_net (bool) — from `result.emptyNet` or `details.isEmptyNet`
- game_winning_goal (bool) — from `result.gameWinningGoal`

- primary_player_id (int) — main actor by event type
- secondary_player_id (int) — opposing/secondary actor where applicable
- goalie_id (int) — goalie on ice for shots/goals
- faceoff_winner_id (int)
- faceoff_loser_id (int)
- assister1_id (int)
- assister2_id (int)
- shooter_id (int)
- blocker_id (int)
- hitter_id (int)
- hittee_id (int)
- taker_id (int)
- victim_id (int)
- giver_id (int)
- recipient_id (int)
- penalty_on_id (int)
- drawn_by_id (int)
- served_by_id (int)

- penalty_severity (string)
- penalty_minutes (int)
- penalty_reason (string)
- penalty_type (string)

- shot_type (string)
- goalie_in_net_id (int)

- shot_distance_ft (float, derived)
- shot_angle_deg (float, derived)
- distance_to_nearest_net_ft (float, derived)
- canonicalized_coordinates_x (float, derived)
- canonicalized_coordinates_y (float, derived)



