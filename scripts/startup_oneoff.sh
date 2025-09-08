#!/bin/bash
set -euo pipefail
# Log to both console and a file readable post-boot
exec &> >(tee -a /var/log/startup-oneoff-2022020002.log)

echo "[startup] BEGIN_WORKFLOW $(date -Is)"
# Use a new flag to force this run even if previous one completed
FLAG_FILE="/home/markhenderson/.one_off_extract_psm_2022020002"
APP_USER="markhenderson"

run_as_app_user() {
  su -l "$APP_USER" -c "bash -lc '
    set -euo pipefail
    mkdir -p /home/markhenderson/logs
    cd /home/markhenderson
    export PYTHONPATH=/home/markhenderson:${PYTHONPATH:-}
    echo EXTRACT
    python3 - <<\\'PY\\'
import json
from sqlalchemy.orm import sessionmaker
from src.database.connection import connect_with_connector
from src.database.models import PlayerShiftMetrics

engine = connect_with_connector()
Session = sessionmaker(bind=engine)
s = Session()
try:
    rows = (
        s.query(PlayerShiftMetrics)
         .filter(PlayerShiftMetrics.game_id == 2022020002)
         .order_by(PlayerShiftMetrics.player_id, PlayerShiftMetrics.shift_number)
         .all()
    )
    out_path = "/home/markhenderson/logs/psm_2022020002.jsonl"
    count = 0
    with open(out_path, "w") as f:
        for r in rows:
            obj = {
                "id": r.id,
                "player_id": r.player_id,
                "game_id": r.game_id,
                "team_id": r.team_id,
                "shift_number": r.shift_number,
                "period": r.period,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "duration": r.duration,
                "attempts_for": r.attempts_for,
                "attempts_against": r.attempts_against,
                "unblocked_for": r.unblocked_for,
                "unblocked_against": r.unblocked_against,
                "shots_for": r.shots_for,
                "shots_against": r.shots_against,
                "goals_for": r.goals_for,
                "goals_against": r.goals_against,
                "hits_for": r.hits_for,
                "hits_against": r.hits_against,
                "takeaways_for": r.takeaways_for,
                "takeaways_against": r.takeaways_against,
                "giveaways_for": r.giveaways_for,
                "giveaways_against": r.giveaways_against,
                "blocks_for": r.blocks_for,
                "blocks_against": r.blocks_against,
                "zone_start": r.zone_start,
                "faceoff_won": r.faceoff_won,
                "strength_state": r.strength_state,
                "teammates_on_ice": r.teammates_on_ice,
                "opponents_on_ice": r.opponents_on_ice,
            }
            line = json.dumps(obj, separators=(",", ":"))
            f.write(line + "\n")
            count += 1
            if count <= 150:
                print("[extract]" + line)
    print(f"[extract]WROTE_FILE:/home/markhenderson/logs/psm_2022020002.jsonl COUNT:{count}")
finally:
    s.close()
PY
  '"
}

if [ -f "$FLAG_FILE" ]; then
  echo "[startup] One-off extract already completed; exiting."
else
  run_as_app_user || echo "[startup] extractor encountered errors."
  touch "$FLAG_FILE" || true
fi

echo "[startup] END_WORKFLOW $(date -Is)"
