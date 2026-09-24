"""Build authoritative July 1, 2026 RFA/UFA classifications for rostered players.

Reads the canonical roster JSON, resolves every real player with ``years == 0``
against NHL search/landing APIs, and writes a reviewable JSON artifact. No DB
writes are performed by this script.
"""

from __future__ import annotations

import json
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROSTER_PATH = ROOT / "public" / "fantasy_hockey_rosters_2026_updated_2026-09-23.json"
OUTPUT_PATH = ROOT / "public" / "uhhp_roster_free_agent_status_2026.json"
CUTOFF = date(2026, 7, 1)
SEARCH_ALIASES = {
    "dmitriy simashev": "Dmitri Simashev",
    "matthew savoie": "Matt Savoie",
}


def normalize(value: Any) -> str:
    text = " ".join(str(value or "").replace("*", "").replace("’", "'").split())
    decomposed = unicodedata.normalize("NFKD", text).casefold()
    return " ".join("".join(ch if ch.isalnum() else " " for ch in decomposed if not unicodedata.combining(ch)).split())


def position_group(value: Any) -> str:
    positions = {part.strip().upper() for part in str(value or "").replace("/", ",").split(",")}
    if "G" in positions:
        return "G"
    if "D" in positions:
        return "D"
    if "C" in positions:
        return "C"
    return "W"


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "FantasySnipe-UHHP/2026"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except Exception as exc:  # pragma: no cover - network retry
            last_error = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def age_on(birthdate: date, cutoff: date) -> int:
    return cutoff.year - birthdate.year - ((cutoff.month, cutoff.day) < (birthdate.month, birthdate.day))


def main() -> int:
    source = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    expired: list[dict[str, Any]] = []
    for team in source.get("teams", []):
        for player in list(team.get("skaters", [])) + list(team.get("goalies", [])):
            name = str(player.get("name") or "")
            if player.get("years") != 0 or "draft pick" in name.casefold() or name.casefold().startswith("z-caphit"):
                continue
            expired.append({"fantasy_team": team.get("team"), **player})

    records: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for index, player in enumerate(expired, start=1):
        display_name = " ".join(str(player.get("name") or "").replace("*", "").split())
        search_name = SEARCH_ALIASES.get(normalize(display_name), display_name)
        query = urllib.parse.quote(search_name)
        search_url = f"https://search.d3.nhle.com/api/v1/search/player?culture=en-us&limit=25&q={query}"
        results = fetch_json(search_url)
        exact = [item for item in results if normalize(item.get("name")) == normalize(search_name)]
        wanted_position = position_group(player.get("position") or player.get("roster_position"))
        position_matches = [item for item in exact if position_group(item.get("positionCode")) == wanted_position]
        candidates = position_matches or exact
        if not candidates:
            unresolved.append({"name": display_name, "team": player.get("nhl_team"), "reason": "no_exact_nhl_match"})
            continue
        match = candidates[0]
        landing = fetch_json(f"https://api-web.nhle.com/v1/player/{match['playerId']}/landing")
        birth_raw = landing.get("birthDate")
        if not birth_raw:
            unresolved.append({"name": display_name, "nhl_player_id": match.get("playerId"), "reason": "missing_birthdate"})
            continue
        birthdate = date.fromisoformat(str(birth_raw))
        age = age_on(birthdate, CUTOFF)
        records.append(
            {
                "fantasy_team": player.get("fantasy_team"),
                "cbs_player_id": str(player.get("cbs_player_id")),
                "player_name": display_name,
                "position": player.get("position") or player.get("roster_position"),
                "nhl_team": player.get("nhl_team"),
                "nhl_player_id": int(match["playerId"]),
                "birthdate": birthdate.isoformat(),
                "age_at_cutoff": age,
                "age_cutoff_date": CUTOFF.isoformat(),
                "free_agent_status": "RFA" if age <= 26 else "UFA",
                "source": "NHL API landing",
            }
        )
        print(f"[{index:02d}/{len(expired)}] {display_name}: {birthdate} age={age} {records[-1]['free_agent_status']}")
        time.sleep(0.05)

    payload = {
        "draft_year": 2026,
        "cutoff_date": CUTOFF.isoformat(),
        "rule": {"rfa_max_age": 26, "ufa_min_age": 27, "requires_contract_years": 0},
        "source": "NHL API player search + landing",
        "players": records,
        "unresolved": unresolved,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} players to {OUTPUT_PATH}; unresolved={len(unresolved)}")
    return 0 if not unresolved and len(records) == len(expired) else 1


if __name__ == "__main__":
    raise SystemExit(main())
