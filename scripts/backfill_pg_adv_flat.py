#!/usr/bin/env python3
import os
import sys

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('.')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from src.database.connection import connect_with_connector
from src.database.models import (
    create_tables,
    PlayerGameAdvancedMetrics,
    PlayerGameAdvancedMetricsFlat,
)

def main():
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        try:
            create_tables()
        except Exception:
            pass

        total = 0
        last_id = 0
        batch_size = int(os.environ.get("FLAT_BATCH", "5000"))
        while True:
            rows = (
                session.query(PlayerGameAdvancedMetrics)
                .filter(PlayerGameAdvancedMetrics.id > last_id)
                .order_by(PlayerGameAdvancedMetrics.id)
                .limit(batch_size)
                .all()
            )
            if not rows:
                break
            last_id = rows[-1].id

            inserts = []
            for r in rows:
                s = r.summary or {}
                totals = s.get("totals", {})
                percs = s.get("percentages", {})
                per60 = s.get("per60", {})
                TOI_seconds = int(totals.get("TOI_seconds", 0) or 0)
                # Shifts were stored under key "Shifts" in the report
                shifts = int(totals.get("Shifts", totals.get("shifts", 0) or 0) or 0)
                CF = int(totals.get("CF", 0) or 0)
                CA = int(totals.get("CA", 0) or 0)
                FF = int(totals.get("FF", 0) or 0)
                FA = int(totals.get("FA", 0) or 0)
                SF = int(totals.get("SF", 0) or 0)
                SA = int(totals.get("SA", 0) or 0)
                GF = int(totals.get("GF", 0) or 0)
                GA = int(totals.get("GA", 0) or 0)
                CF_pct = float(percs.get("CF%", 0) or 0)
                FF_pct = float(percs.get("FF%", 0) or 0)
                SF_pct = float(percs.get("SF%", 0) or 0)
                GF_pct = float(percs.get("GF%", 0) or 0)
                CF60 = float(per60.get("CF60", 0) or 0)
                FF60 = float(per60.get("FF60", 0) or 0)
                SF60 = float(per60.get("SF60", 0) or 0)
                GF60 = float(per60.get("GF60", 0) or 0)
                PDO = float(percs.get("PDO", 0) or 0)

                inserts.append({
                    "player_id": r.player_id,
                    "game_id": r.game_id,
                    "team_id": r.team_id,
                    "season": r.season,
                    "game_type": r.game_type,
                    "CF": CF, "CA": CA, "FF": FF, "FA": FA, "SF": SF, "SA": SA, "GF": GF, "GA": GA,
                    "CF_pct": CF_pct, "FF_pct": FF_pct, "SF_pct": SF_pct, "GF_pct": GF_pct,
                    "CF60": CF60, "FF60": FF60, "SF60": SF60, "GF60": GF60, "PDO": PDO,
                    "TOI_seconds": TOI_seconds, "shifts": shifts,
                })

            from sqlalchemy.dialects.postgresql import insert as pg_insert
            if inserts:
                stmt = pg_insert(PlayerGameAdvancedMetricsFlat.__table__).values(inserts)
                update_cols = {k: stmt.excluded[k] for k in inserts[0].keys() if k not in ("player_id","game_id")}
                stmt = stmt.on_conflict_do_update(index_elements=["player_id","game_id"], set_=update_cols)
                session.execute(stmt)
                session.commit()
                total += len(inserts)
                print(f"flattened_batch: {len(inserts)} total: {total}")

    finally:
        session.close()

if __name__ == "__main__":
    main()

