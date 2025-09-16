#!/usr/bin/env python3
"""
Parse docs/roster-overview-all-1-20251007.csv to extract goalie salaries/years
per team and emit SQL UPDATE statements that sync cbs_rosters for the UHHP league.

Usage:
  python3 scripts/update_goalie_contracts_from_overview.py \
      --csv "docs/roster-overview-all-1-20251007.csv" \
      --out "scripts/_goalie_updates.sql"

The generated SQL can then be applied with psql, e.g.:
  PGPASSWORD=... psql -h ... -p ... -U ... -d ... -v ON_ERROR_STOP=1 -f scripts/_goalie_updates.sql
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def parse_goalie_contracts(csv_path: Path) -> list[tuple[str, str, int | None, int | None]]:
    """Return list of (team_name, player_name, salary, years) tuples for all goalies."""
    rows: list[list[str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    updates: list[tuple[str, str, int | None, int | None]] = []
    team: str | None = None
    in_goalies = False
    header: list[str] | None = None

    for row in rows:
        # Section headers are single-cell rows
        if len(row) == 1:
            label = (row[0] or "").strip()
            if label.endswith("Goalies"):
                team = label[:-8].strip()
                in_goalies = True
                header = None
                continue
            if label.endswith("Skaters"):
                in_goalies = False
                header = None
                continue

        if not in_goalies:
            continue

        if row and (row[0] or "").strip() == "Pos":
            header = row[:]
            continue

        if header is None:
            continue

        if len(row) == 1 and (row[0] or "").strip() in ("Reserves", "Injured"):
            # still in section, but skip markers
            continue

        # Map expected columns
        def col(name: str, default: int | None) -> int | None:
            try:
                return header.index(name)  # type: ignore[arg-type]
            except ValueError:
                return default

        idx_pos = col("Pos", 0)
        idx_players = col("Players, First Game", 1)
        # Positions of these columns in this export typically land at 7/8
        idx_salary = col("salary", 7)
        idx_years = col("Years", 8)

        if idx_pos is None or idx_pos >= len(row):
            continue
        if (row[idx_pos] or "").strip() != "G":
            # Only consume goalie rows inside the Goalies section
            continue

        players_cell = row[idx_players] if (idx_players is not None and idx_players < len(row)) else ""
        # Extract player name before " G |"
        m = re.match(r"\s*([^|]+?)\s+G\s*\|", players_cell)
        if m:
            name = m.group(1).strip()
        else:
            name = players_cell.split(" | ", 1)[0].strip()

        def to_int(val: str | None) -> int | None:
            s = (val or "").strip()
            if s == "":
                return None
            try:
                return int(float(s))
            except Exception:
                return None

        salary = to_int(row[idx_salary] if (idx_salary is not None and idx_salary < len(row)) else None)
        years = to_int(row[idx_years] if (idx_years is not None and idx_years < len(row)) else None)

        if team and name and (salary is not None or years is not None):
            updates.append((team, name, salary, years))

    return updates


def emit_sql(updates: list[tuple[str, str, int | None, int | None]]) -> str:
    """Generate SQL UPDATE statements for UHHP league for provided tuples."""
    stmts: list[str] = []
    for team, name, salary, years in updates:
        sets: list[str] = []
        if salary is not None:
            sets.append(f"salary={salary}")
        if years is not None:
            sets.append(f"years={years}")
        team_q = team.replace("'", "''")
        name_q = name.replace("'", "''")
        stmts.append(
            "UPDATE cbs_rosters r SET "
            + ", ".join(sets)
            + " FROM cbs_players p, cbs_teams t, cbs_leagues l"
            + " WHERE p.cbs_player_id=r.cbs_player_id AND t.team_id=r.team_id"
            + " AND l.id=t.league_id AND l.provider_slug='uhhp'"
            + f" AND t.team_name='{team_q}' AND p.full_name='{name_q}' AND p.pos_primary='G';"
        )
    return "\n".join(stmts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="docs/roster-overview-all-1-20251007.csv")
    ap.add_argument("--out", default="scripts/_goalie_updates.sql")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    updates = parse_goalie_contracts(csv_path)
    sql = emit_sql(updates)

    out_path = Path(args.out)
    out_path.write_text(sql, encoding="utf-8")
    print(f"Wrote {len(updates)} goalie contract updates to {out_path}")


if __name__ == "__main__":
    main()


