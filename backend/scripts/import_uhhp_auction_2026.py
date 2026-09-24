#!/usr/bin/env python3
"""Import the canonical UHHP 2026 auction snapshot.

The default mode is a pure-stdlib dry run.  ``--apply`` lazily imports
psycopg2, enriches roster records from the fantasy/NHL databases, and upserts
migration-022 auction state in one transaction.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


EXPECTED_PYTHON = (3, 11)
EXPECTED_TEAM_COUNT = 12
SNAPSHOT_SCHEMA_VERSION = 1
IMPORTER_NAME = "backend/scripts/import_uhhp_auction_2026.py"

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = {
    "gm_directory": Path("public/gms.md"),
    "rosters": Path("public/fantasy_hockey_rosters_2026_structured.json"),
    "skater_projections": Path("public/uhhp-sept-22.csv"),
    "goalie_projections": Path("public/goalies.csv"),
    "rules": Path("backend/config/uhhp_auction_rules_2026.json"),
}

NHL_TEAM_ALIASES = {
    "MON": "MTL",
    "MTL": "MTL",
    "LV": "VGK",
    "VGK": "VGK",
    "SJ": "SJS",
    "SJS": "SJS",
    "CLB": "CBJ",
    "CBJ": "CBJ",
    "WAS": "WSH",
    "WSH": "WSH",
}

CLASSIFICATION_ORDER = (
    "PROTECTED",
    "RFA",
    "UFA",
    "ROOKIE",
    "ASSET",
    "CAP_HIT",
    "REVIEW",
)

PROJECTION_HEADERS = (
    "Avail",
    "Player",
    "GP",
    "G",
    "A",
    "PTS",
    "+/-",
    "PIM",
    "PPG",
    "SHG",
    "SOG",
    "FPTS",
)
PROJECTION_METRIC_KEYS = (
    "gp",
    "goals",
    "assists",
    "points",
    "plus_minus",
    "pim",
    "power_play_goals",
    "short_handed_goals",
    "shots_on_goal",
    "fantasy_points",
)
GOALIE_PROJECTION_HEADERS = (
    "Avail",
    "Player",
    "GGP",
    "W",
    "L",
    "SO",
    "GAA",
    "GA",
    "S",
    "SPct",
    "FPTS",
)
GOALIE_PROJECTION_METRIC_KEYS = (
    "games_played",
    "wins",
    "losses",
    "shutouts",
    "goals_against_average",
    "goals_against",
    "saves",
    "save_percentage",
    "fantasy_points",
)
PLAYER_CELL_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<position>[A-Z]+)\s*\|\s*(?P<team>[A-Z]{2,3})\s*$",
    re.IGNORECASE,
)
DRAFT_PICK_RE = re.compile(r"\bdraft\s+pick\b", re.IGNORECASE)
CAP_HIT_RE = re.compile(r"(?:^|\b)z\s*[-_]?\s*caphit\b|\bcap\s*hit\b", re.IGNORECASE)
TRAILING_ROOKIE_MARK_RE = re.compile(r"\s*\*+\s*$")

REQUIRED_APPLY_TABLES = (
    "public.cbs_leagues",
    "public.cbs_owners",
    "public.cbs_league_owners",
    "public.cbs_teams",
    "public.cbs_players",
    "public.cbs_player_map",
    "public.uhhp_auction_drafts",
    "public.uhhp_auction_draft_teams",
    "public.uhhp_auction_player_pool",
    "public.uhhp_auction_import_runs",
)


class ImporterError(Exception):
    """A safe-to-display importer failure."""


class SourceValidationError(ImporterError):
    """A source file is missing or malformed."""


class ApplyError(ImporterError):
    """The database apply operation could not be completed."""


@dataclass(frozen=True, slots=True)
class RulesConfig:
    raw: dict[str, Any]
    league_slug: str
    draft_year: int
    rules_version: str
    salary_cap: Decimal
    expired_contract_years: int
    cutoff_month: int
    cutoff_day: int
    rfa_max_age: int

    @property
    def cutoff_date(self) -> date:
        return date(self.draft_year, self.cutoff_month, self.cutoff_day)


@dataclass(frozen=True, slots=True)
class GMRecord:
    order: int
    team_name: str
    abbreviation: str
    team_key: str
    manager_name: str
    manager_email: str


@dataclass(frozen=True, slots=True)
class ProjectionRecord:
    source_row: int
    rank: int
    source_availability: str
    is_waiver: bool
    listed_fantasy_team: str | None
    name: str
    normalized_name: str
    position: str
    nhl_team: str
    source_key: str
    metrics: dict[str, float]


@dataclass(slots=True)
class RosterRecord:
    fantasy_team: str
    team_key: str
    section: str
    cbs_player_id: str
    nhl_player_id: int | None
    raw_name: str
    name: str
    normalized_name: str
    roster_position: str
    position: str
    nhl_team: str | None
    source_key: str
    source_status: str | None
    salary: Decimal | None
    years: int | None
    rookie: bool
    birthdate: date | None
    source_metrics: dict[str, float | None] = field(default_factory=dict)

    @property
    def special_kind(self) -> str | None:
        if DRAFT_PICK_RE.search(self.name):
            return "draft_pick"
        if CAP_HIT_RE.search(self.name):
            return "cap_hit"
        return None


@dataclass(frozen=True, slots=True)
class Classification:
    eligibility: str
    entry_type: str
    reason: str
    age_at_cutoff: int | None


@dataclass(frozen=True, slots=True)
class EnrichmentReport:
    attempted: bool = False
    fantasy_players_matched: int = 0
    fantasy_birthdates_used: int = 0
    fantasy_nhl_ids_used: int = 0
    nhl_database_configured: bool = False
    nhl_birthdates_used: int = 0
    birthdates_written_to_fantasy: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "fantasy_players_matched": self.fantasy_players_matched,
            "fantasy_birthdates_used": self.fantasy_birthdates_used,
            "fantasy_nhl_ids_used": self.fantasy_nhl_ids_used,
            "nhl_database_configured": self.nhl_database_configured,
            "nhl_birthdates_used": self.nhl_birthdates_used,
            "birthdates_written_to_fantasy": self.birthdates_written_to_fantasy,
        }


@dataclass(frozen=True, slots=True)
class ApplyResult:
    teams_upserted: int
    player_rows_seen: int
    player_rows_inserted: int
    player_rows_updated: int


# ---------------------------------------------------------------------------
# Normalization and source parsing
# ---------------------------------------------------------------------------


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def clean_display_name(value: str) -> str:
    """Remove CBS's trailing rookie marker while preserving display punctuation."""

    return collapse_whitespace(TRAILING_ROOKIE_MARK_RE.sub("", value.strip()))


def normalize_name(value: str) -> str:
    """Return a matching form that is stable across accents and punctuation."""

    cleaned = clean_display_name(value).replace("’", "'")
    decomposed = unicodedata.normalize("NFKD", cleaned).casefold()
    characters: list[str] = []
    for character in decomposed:
        if unicodedata.combining(character):
            continue
        characters.append(character if character.isalnum() else " ")
    return collapse_whitespace("".join(characters))


def normalize_position(value: str | None) -> str:
    position = collapse_whitespace(str(value or "")).upper()
    if position in {"LW", "RW"}:
        return "W"
    return position


def normalize_nhl_team(value: str | None) -> str | None:
    team = collapse_whitespace(str(value or "")).upper()
    if not team or team in {"-", "--", "N/A", "NA", "FA"}:
        return None
    return NHL_TEAM_ALIASES.get(team, team)


def make_source_key(name: str, position: str, nhl_team: str | None) -> str:
    """Build the migration-022 source key from normalized source identity."""

    normalized = normalize_name(name)
    normalized_position = normalize_position(position)
    normalized_team = normalize_nhl_team(nhl_team) or "-"
    if not normalized or not normalized_position:
        raise SourceValidationError(
            f"Cannot build source key for player with name={name!r} and position={position!r}."
        )
    return f"{normalized}|{normalized_position}|{normalized_team}"


def make_team_key(abbreviation: str) -> str:
    normalized = normalize_name(abbreviation).replace(" ", "")
    if not normalized:
        raise SourceValidationError("A GM abbreviation normalized to an empty team key.")
    return normalized


def parse_iso_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise SourceValidationError(f"Invalid birthdate value {text!r}.") from exc


def decimal_from_value(value: Any, *, field_name: str) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise SourceValidationError(f"{field_name} must be numeric, not boolean.")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise SourceValidationError(f"Invalid numeric {field_name}: {value!r}.") from exc
    if not number.is_finite():
        raise SourceValidationError(f"{field_name} must be finite.")
    return number


def int_from_value(value: Any, *, field_name: str, allow_none: bool = True) -> int | None:
    number = decimal_from_value(value, field_name=field_name)
    if number is None:
        if allow_none:
            return None
        raise SourceValidationError(f"{field_name} is required.")
    if number != number.to_integral_value():
        raise SourceValidationError(f"{field_name} must be a whole number: {value!r}.")
    return int(number)


def json_number(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SourceValidationError(f"Missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceValidationError(
            f"Invalid JSON in {label} at line {exc.lineno}, column {exc.colno}."
        ) from exc
    except OSError as exc:
        raise SourceValidationError(f"Could not read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise SourceValidationError(f"{label} must contain a top-level JSON object.")
    return value


def parse_rules(path: Path) -> RulesConfig:
    raw = read_json_object(path, "auction rules")
    try:
        league_slug = str(raw["league_slug"]).strip()
        draft_year = int(raw["draft_year"])
        rules_version = str(raw["rules_version"]).strip()
        salary_cap = decimal_from_value(raw["money"]["salary_cap"], field_name="salary cap")
        expired_years = int(raw["free_agency"]["expired_contract_years_value"])
        cutoff = raw["free_agency"]["age_cutoff"]
        cutoff_month = int(cutoff["month"])
        cutoff_day = int(cutoff["day"])
        rfa_max_age = int(cutoff["rfa_max_age"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceValidationError("Auction rules JSON is missing required 2026 fields.") from exc

    if league_slug != "uhhp" or draft_year != 2026:
        raise SourceValidationError(
            f"This importer requires league_slug='uhhp' and draft_year=2026; got "
            f"{league_slug!r} and {draft_year!r}."
        )
    if not rules_version:
        raise SourceValidationError("rules_version cannot be empty.")
    if salary_cap is None or salary_cap < 0:
        raise SourceValidationError("salary_cap must be a non-negative number.")
    if expired_years != 0:
        raise SourceValidationError("The 2026 importer expects expired contract years to equal 0.")
    try:
        date(draft_year, cutoff_month, cutoff_day)
    except ValueError as exc:
        raise SourceValidationError("The free-agency age cutoff is not a valid date.") from exc

    return RulesConfig(
        raw=raw,
        league_slug=league_slug,
        draft_year=draft_year,
        rules_version=rules_version,
        salary_cap=salary_cap,
        expired_contract_years=expired_years,
        cutoff_month=cutoff_month,
        cutoff_day=cutoff_day,
        rfa_max_age=rfa_max_age,
    )


def parse_gms(path: Path) -> list[GMRecord]:
    """Parse the heading followed by numbered records with four data lines."""

    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
    except FileNotFoundError as exc:
        raise SourceValidationError(f"Missing GM directory: {path}") from exc
    except OSError as exc:
        raise SourceValidationError(f"Could not read GM directory: {path}") from exc
    lines = [line for line in lines if line]
    if not lines or not lines[0].casefold().startswith("team name"):
        raise SourceValidationError("gms.md must start with its tab-separated heading row.")

    payload = lines[1:]
    if len(payload) % 5 != 0:
        raise SourceValidationError(
            "gms.md must contain a number followed by team, abbreviation, manager, and email."
        )

    records: list[GMRecord] = []
    seen_teams: set[str] = set()
    seen_abbreviations: set[str] = set()
    for offset in range(0, len(payload), 5):
        number_text, team_name, abbreviation, manager_name, manager_email = payload[offset : offset + 5]
        try:
            order = int(number_text)
        except ValueError as exc:
            raise SourceValidationError(f"Invalid GM record number {number_text!r}.") from exc
        expected_order = len(records) + 1
        if order != expected_order:
            raise SourceValidationError(
                f"GM records must be consecutively numbered; expected {expected_order}, got {order}."
            )
        if not all((team_name, abbreviation, manager_name, manager_email)):
            raise SourceValidationError(f"GM record {order} contains an empty required field.")
        if "@" not in manager_email:
            raise SourceValidationError(f"GM record {order} has an invalid manager email.")

        normalized_team = normalize_name(team_name)
        abbreviation_key = make_team_key(abbreviation)
        if normalized_team in seen_teams:
            raise SourceValidationError(f"Duplicate team in gms.md: {team_name}")
        if abbreviation_key in seen_abbreviations:
            raise SourceValidationError(f"Duplicate GM abbreviation in gms.md: {abbreviation}")
        seen_teams.add(normalized_team)
        seen_abbreviations.add(abbreviation_key)
        records.append(
            GMRecord(
                order=order,
                team_name=team_name,
                abbreviation=abbreviation,
                team_key=abbreviation_key,
                manager_name=manager_name,
                manager_email=manager_email,
            )
        )
    return records


def projection_number(value: str, *, row_number: int, column: str) -> float:
    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        raise SourceValidationError(
            f"Projection CSV row {row_number} has invalid {column} value {value!r}."
        ) from exc
    if not number.is_finite():
        raise SourceValidationError(
            f"Projection CSV row {row_number} has non-finite {column} value."
        )
    return float(number)


def is_waiver_availability(value: str) -> bool:
    return bool(re.match(r"^W(?:\s|\(|$)", value.strip(), re.IGNORECASE))


def parse_projection_csv(path: Path) -> list[ProjectionRecord]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
    except FileNotFoundError as exc:
        raise SourceValidationError(f"Missing skater projection CSV: {path}") from exc
    except (OSError, csv.Error) as exc:
        raise SourceValidationError(f"Could not parse skater projection CSV: {path}") from exc

    if len(rows) < 4:
        raise SourceValidationError("Projection CSV is too short to contain title, header, data, and footer.")
    if not rows[0] or "projections" not in rows[0][0].casefold():
        raise SourceValidationError("Projection CSV title row is missing or unexpected.")
    header = [cell.strip() for cell in rows[1]]
    while header and not header[-1]:
        header.pop()
    if tuple(header) != PROJECTION_HEADERS:
        raise SourceValidationError(
            "Projection CSV header is unexpected; refusing to guess column positions."
        )
    if not rows[-1] or not rows[-1][0].strip().casefold().startswith("report updated"):
        raise SourceValidationError("Projection CSV footer is missing; the report may be truncated.")

    records: list[ProjectionRecord] = []
    seen_keys: set[str] = set()
    for rank, row in enumerate(rows[2:-1], start=1):
        row_number = rank + 2
        if len(row) < len(PROJECTION_HEADERS):
            raise SourceValidationError(
                f"Projection CSV row {row_number} has {len(row)} columns; expected 12."
            )
        if any(cell.strip() for cell in row[len(PROJECTION_HEADERS) :]):
            raise SourceValidationError(
                f"Projection CSV row {row_number} has unexpected non-empty trailing columns."
            )

        availability = row[0].strip()
        player_cell = row[1].strip()
        match = PLAYER_CELL_RE.fullmatch(player_cell)
        if match is None:
            raise SourceValidationError(
                f"Projection CSV row {row_number} has invalid Player value {player_cell!r}."
            )
        name = clean_display_name(match.group("name"))
        position = normalize_position(match.group("position"))
        nhl_team = normalize_nhl_team(match.group("team"))
        if nhl_team is None:
            raise SourceValidationError(f"Projection CSV row {row_number} has no NHL team.")
        source_key = make_source_key(name, position, nhl_team)
        if source_key in seen_keys:
            raise SourceValidationError(f"Duplicate projection source key {source_key!r}.")
        seen_keys.add(source_key)

        waiver = is_waiver_availability(availability)
        metrics = {
            metric_key: projection_number(
                row[column_index],
                row_number=row_number,
                column=PROJECTION_HEADERS[column_index],
            )
            for column_index, metric_key in enumerate(PROJECTION_METRIC_KEYS, start=2)
        }
        records.append(
            ProjectionRecord(
                source_row=row_number,
                rank=rank,
                source_availability=availability,
                is_waiver=waiver,
                listed_fantasy_team=None if waiver else availability,
                name=name,
                normalized_name=normalize_name(name),
                position=position,
                nhl_team=nhl_team,
                source_key=source_key,
                metrics=metrics,
            )
        )
    return records


def parse_goalie_projection_csv(path: Path) -> list[ProjectionRecord]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [row for row in csv.reader(handle) if any(cell.strip() for cell in row)]
    except FileNotFoundError as exc:
        raise SourceValidationError(f"Missing goalie projection CSV: {path}") from exc
    except (OSError, csv.Error) as exc:
        raise SourceValidationError(f"Could not parse goalie projection CSV: {path}") from exc

    if len(rows) < 4:
        raise SourceValidationError(
            "Goalie projection CSV is too short to contain title, header, data, and footer."
        )
    if not rows[0] or "goalies" not in rows[0][0].casefold():
        raise SourceValidationError("Goalie projection CSV title row is missing or unexpected.")
    header = [cell.strip() for cell in rows[1]]
    while header and not header[-1]:
        header.pop()
    if tuple(header) != GOALIE_PROJECTION_HEADERS:
        raise SourceValidationError(
            "Goalie projection CSV header is unexpected; refusing to guess column positions."
        )
    if not rows[-1] or not rows[-1][0].strip().casefold().startswith("report updated"):
        raise SourceValidationError(
            "Goalie projection CSV footer is missing; the report may be truncated."
        )

    records: list[ProjectionRecord] = []
    seen_keys: set[str] = set()
    for rank, row in enumerate(rows[2:-1], start=1):
        row_number = rank + 2
        if len(row) < len(GOALIE_PROJECTION_HEADERS):
            raise SourceValidationError(
                f"Goalie projection CSV row {row_number} has {len(row)} columns; expected 11."
            )
        if any(cell.strip() for cell in row[len(GOALIE_PROJECTION_HEADERS) :]):
            raise SourceValidationError(
                f"Goalie projection CSV row {row_number} has unexpected non-empty trailing columns."
            )

        availability = row[0].strip()
        player_cell = row[1].strip()
        match = PLAYER_CELL_RE.fullmatch(player_cell)
        if match is None:
            raise SourceValidationError(
                f"Goalie projection CSV row {row_number} has invalid Player value {player_cell!r}."
            )
        name = clean_display_name(match.group("name"))
        position = normalize_position(match.group("position"))
        if position != "G":
            raise SourceValidationError(
                f"Goalie projection CSV row {row_number} is not a goalie."
            )
        nhl_team = normalize_nhl_team(match.group("team"))
        if nhl_team is None:
            raise SourceValidationError(
                f"Goalie projection CSV row {row_number} has no NHL team."
            )
        source_key = make_source_key(name, position, nhl_team)
        if source_key in seen_keys:
            raise SourceValidationError(f"Duplicate goalie projection source key {source_key!r}.")
        seen_keys.add(source_key)

        waiver = is_waiver_availability(availability)
        metrics = {
            metric_key: projection_number(
                row[column_index],
                row_number=row_number,
                column=GOALIE_PROJECTION_HEADERS[column_index],
            )
            for column_index, metric_key in enumerate(
                GOALIE_PROJECTION_METRIC_KEYS, start=2
            )
        }
        records.append(
            ProjectionRecord(
                source_row=row_number,
                rank=rank,
                source_availability=availability,
                is_waiver=waiver,
                listed_fantasy_team=None if waiver else availability,
                name=name,
                normalized_name=normalize_name(name),
                position=position,
                nhl_team=nhl_team,
                source_key=source_key,
                metrics=metrics,
            )
        )
    return records


def parse_rosters(path: Path, gm_by_name: dict[str, GMRecord], rules: RulesConfig) -> list[RosterRecord]:
    raw = read_json_object(path, "structured roster snapshot")
    if raw.get("year") != rules.draft_year:
        raise SourceValidationError(
            f"Roster JSON year must be {rules.draft_year}; got {raw.get('year')!r}."
        )
    teams = raw.get("teams")
    if not isinstance(teams, list):
        raise SourceValidationError("Roster JSON must contain a teams array.")

    records: list[RosterRecord] = []
    seen_keys: set[str] = set()
    seen_team_names: set[str] = set()
    for team in teams:
        if not isinstance(team, dict):
            raise SourceValidationError("Every roster team must be a JSON object.")
        team_name = collapse_whitespace(str(team.get("team") or ""))
        gm = gm_by_name.get(team_name)
        if gm is None:
            raise SourceValidationError(f"Roster JSON contains unknown team {team_name!r}.")
        if team_name in seen_team_names:
            raise SourceValidationError(f"Roster JSON repeats team {team_name!r}.")
        seen_team_names.add(team_name)

        for section in ("skaters", "goalies"):
            entries = team.get(section)
            if not isinstance(entries, list):
                raise SourceValidationError(f"Roster team {team_name!r} has invalid {section} data.")
            for source in entries:
                if not isinstance(source, dict):
                    raise SourceValidationError(
                        f"Roster team {team_name!r} contains a non-object {section} row."
                    )
                raw_name = collapse_whitespace(str(source.get("name") or ""))
                name = clean_display_name(raw_name)
                position = normalize_position(source.get("position") or source.get("roster_position"))
                roster_position = normalize_position(source.get("roster_position") or position)
                nhl_team = normalize_nhl_team(source.get("nhl_team"))
                cbs_player_id = str(source.get("cbs_player_id") or "").strip()
                if not name or not position or not cbs_player_id:
                    raise SourceValidationError(
                        f"Roster row on {team_name!r} is missing name, position, or CBS ID."
                    )
                source_key = make_source_key(name, position, nhl_team)
                if source_key in seen_keys:
                    raise SourceValidationError(f"Duplicate roster source key {source_key!r}.")
                seen_keys.add(source_key)

                years = int_from_value(source.get("years"), field_name=f"years for {name}")
                if years is not None and years < 0:
                    raise SourceValidationError(f"Contract years cannot be negative for {name}.")
                salary = decimal_from_value(source.get("salary"), field_name=f"salary for {name}")
                if salary is not None and salary < 0:
                    raise SourceValidationError(f"Salary cannot be negative for {name}.")
                rookie = source.get("rookie")
                if not isinstance(rookie, bool):
                    raise SourceValidationError(f"Rookie marker must be boolean for {name}.")
                nhl_player_id = int_from_value(
                    source.get("nhl_player_id"), field_name=f"NHL ID for {name}"
                )
                if nhl_player_id is not None and nhl_player_id <= 0:
                    raise SourceValidationError(f"NHL ID must be positive for {name}.")

                records.append(
                    RosterRecord(
                        fantasy_team=team_name,
                        team_key=gm.team_key,
                        section=section,
                        cbs_player_id=cbs_player_id,
                        nhl_player_id=nhl_player_id,
                        raw_name=raw_name,
                        name=name,
                        normalized_name=normalize_name(name),
                        roster_position=roster_position,
                        position=position,
                        nhl_team=nhl_team,
                        source_key=source_key,
                        source_status=(
                            collapse_whitespace(str(source.get("status")))
                            if source.get("status") is not None
                            else None
                        ),
                        salary=salary,
                        years=years,
                        rookie=rookie,
                        birthdate=parse_iso_date(
                            source.get("birthdate") or source.get("birth_date")
                        ),
                        source_metrics={
                            key: source.get(key)
                            for key in (
                                "rank",
                                "rostered_pct",
                                "start_pct",
                                "fantasy_points_2025",
                                "fantasy_points_3yr_avg",
                                "fantasy_points_proj",
                            )
                        },
                    )
                )
    return records


def source_fingerprints(paths: dict[str, Path]) -> tuple[dict[str, dict[str, str]], str]:
    sources: dict[str, dict[str, str]] = {}
    combined = hashlib.sha256()
    for label in sorted(paths):
        relative_path = paths[label]
        absolute_path = REPO_ROOT / relative_path
        try:
            content = absolute_path.read_bytes()
        except FileNotFoundError as exc:
            raise SourceValidationError(f"Missing source file: {relative_path}") from exc
        except OSError as exc:
            raise SourceValidationError(f"Could not read source file: {relative_path}") from exc
        digest = hashlib.sha256(content).hexdigest()
        sources[label] = {"path": relative_path.as_posix(), "sha256": digest}
        combined.update(label.encode("utf-8"))
        combined.update(b"\0")
        combined.update(relative_path.as_posix().encode("utf-8"))
        combined.update(b"\0")
        combined.update(digest.encode("ascii"))
        combined.update(b"\0")
    return sources, combined.hexdigest()


# ---------------------------------------------------------------------------
# Classification and normalized snapshot
# ---------------------------------------------------------------------------


def age_on_date(birthdate: date, cutoff: date) -> int:
    return cutoff.year - birthdate.year - (
        (cutoff.month, cutoff.day) < (birthdate.month, birthdate.day)
    )


def classify_roster_record(record: RosterRecord, rules: RulesConfig) -> Classification:
    special_kind = record.special_kind
    if special_kind == "draft_pick":
        return Classification("ASSET", "draft_pick", "draft-pick placeholder", None)
    if special_kind == "cap_hit":
        return Classification("CAP_HIT", "cap_hit", "z-CAPHIT cap obligation", None)
    # An expired (0-year) contract is classified RFA/UFA by cutoff age even
    # when the roster row carries the rookie flag. entry_type/is_rookie retain
    # the rookie marker independently for display and roster rules.
    if record.years == rules.expired_contract_years:
        entry_type = "rookie" if record.rookie else "player"
        if record.birthdate is None:
            return Classification(
                "REVIEW", entry_type, "expired contract is missing birthdate", None
            )
        age = age_on_date(record.birthdate, rules.cutoff_date)
        if age < 0 or age > 150:
            return Classification("REVIEW", entry_type, "birthdate produces invalid cutoff age", age)
        if age <= rules.rfa_max_age:
            return Classification("RFA", entry_type, "expired contract and cutoff age <= 26", age)
        return Classification("UFA", entry_type, "expired contract and cutoff age >= 27", age)
    if record.rookie:
        age = age_on_date(record.birthdate, rules.cutoff_date) if record.birthdate else None
        return Classification("ROOKIE", "rookie", "roster rookie marker", age)
    if record.years is not None and record.years > rules.expired_contract_years:
        age = age_on_date(record.birthdate, rules.cutoff_date) if record.birthdate else None
        return Classification("PROTECTED", "player", "contract years greater than zero", age)
    return Classification("REVIEW", "player", "contract years are missing", None)


def roster_projection(record: RosterRecord) -> tuple[dict[str, Any], float | None]:
    projected = record.source_metrics.get("fantasy_points_proj")
    if projected is None:
        return {}, None
    projection = {
        "source": "fantasy_hockey_rosters_2026_structured.json",
        "rank": record.source_metrics.get("rank"),
        "rostered_pct": record.source_metrics.get("rostered_pct"),
        "start_pct": record.source_metrics.get("start_pct"),
        "fantasy_points_2025": record.source_metrics.get("fantasy_points_2025"),
        "fantasy_points_3yr_avg": record.source_metrics.get("fantasy_points_3yr_avg"),
        "fantasy_points": projected,
    }
    numeric_projection = float(projected)
    return projection, numeric_projection


def normalized_player(
    projection: ProjectionRecord | None,
    roster: RosterRecord | None,
    rules: RulesConfig,
) -> dict[str, Any]:
    if projection is None and roster is None:
        raise AssertionError("A normalized player requires a projection or roster source.")

    if roster is not None:
        classification = classify_roster_record(roster, rules)
        name = projection.name if projection is not None else roster.name
        normalized = normalize_name(name)
        position = roster.position
        nhl_team = roster.nhl_team
        source_key = roster.source_key
        projection_data = (
            {
                "source": (
                    "goalies.csv" if projection.position == "G" else "uhhp-sept-22.csv"
                ),
                "rank": projection.rank,
                **projection.metrics,
            }
            if projection is not None
            else roster_projection(roster)[0]
        )
        projected_fantasy_points = (
            projection.metrics["fantasy_points"]
            if projection is not None
            else roster_projection(roster)[1]
        )
        source_availability = (
            projection.source_availability if projection is not None else roster.fantasy_team
        )
        listed_fantasy_team = (
            projection.listed_fantasy_team if projection is not None else roster.fantasy_team
        )
        return {
            "source_key": source_key,
            "name": name,
            "normalized_name": normalized,
            "position": position,
            "nhl_team": nhl_team,
            "cbs_player_id": roster.cbs_player_id,
            "nhl_player_id": roster.nhl_player_id,
            "birthdate": roster.birthdate.isoformat() if roster.birthdate else None,
            "age_cutoff_date": (
                rules.cutoff_date.isoformat()
                if classification.entry_type in {"player", "rookie"}
                else None
            ),
            "age_at_cutoff": classification.age_at_cutoff,
            "entry_type": classification.entry_type,
            "eligibility": classification.eligibility,
            "classification_reason": classification.reason,
            "auction_eligible": classification.eligibility in {"RFA", "UFA"},
            "source_availability": source_availability,
            "listed_fantasy_team": listed_fantasy_team,
            "is_waiver": projection.is_waiver if projection is not None else False,
            "rostered": True,
            "roster_team": roster.fantasy_team,
            "roster_team_key": roster.team_key,
            "controlling_team_key": (
                roster.team_key if classification.eligibility == "RFA" else None
            ),
            "contract": {
                "salary": json_number(roster.salary),
                "years": roster.years,
                "rookie": roster.rookie,
            },
            "source_status": roster.source_status,
            "roster_section": roster.section,
            "projection_row": projection.source_row if projection is not None else None,
            "projection": projection_data,
            "projected_fantasy_points": projected_fantasy_points,
        }

    assert projection is not None
    if projection.is_waiver:
        classification = Classification(
            "UFA", "player", "unrostered waiver/free-agent player", None
        )
    else:
        classification = Classification(
            "REVIEW", "player", "projection assignment has no roster contract", None
        )
    return {
        "source_key": projection.source_key,
        "name": projection.name,
        "normalized_name": projection.normalized_name,
        "position": projection.position,
        "nhl_team": projection.nhl_team,
        "cbs_player_id": None,
        "nhl_player_id": None,
        "birthdate": None,
        "age_cutoff_date": rules.cutoff_date.isoformat(),
        "age_at_cutoff": None,
        "entry_type": classification.entry_type,
        "eligibility": classification.eligibility,
        "classification_reason": classification.reason,
        "auction_eligible": classification.eligibility in {"RFA", "UFA"},
        "source_availability": projection.source_availability,
        "listed_fantasy_team": projection.listed_fantasy_team,
        "is_waiver": projection.is_waiver,
        "rostered": False,
        "roster_team": None,
        "roster_team_key": None,
        "controlling_team_key": None,
        "contract": {"salary": None, "years": None, "rookie": False},
        "source_status": None,
        "roster_section": None,
        "projection_row": projection.source_row,
        "projection": {
            "source": "goalies.csv" if projection.position == "G" else "uhhp-sept-22.csv",
            "rank": projection.rank,
            **projection.metrics,
        },
        "projected_fantasy_points": projection.metrics["fantasy_points"],
    }


def unmatched_roster_detail(record: RosterRecord) -> dict[str, Any]:
    if record.special_kind == "draft_pick":
        reason = "draft_pick_placeholder"
        expected_roster_only = True
    elif record.special_kind == "cap_hit":
        reason = "cap_hit_placeholder"
        expected_roster_only = True
    elif record.position == "G":
        reason = "goalie_not_in_skater_projection"
        expected_roster_only = True
    elif record.rookie:
        reason = "rookie_without_projection"
        expected_roster_only = True
    else:
        reason = "no_projection_match"
        expected_roster_only = False
    return {
        "source_key": record.source_key,
        "team": record.fantasy_team,
        "name": record.raw_name,
        "position": record.position,
        "nhl_team": record.nhl_team,
        "reason": reason,
        "expected_roster_only": expected_roster_only,
    }


def salary_for_statuses(
    players: Sequence[dict[str, Any]], statuses: set[str]
) -> Decimal:
    total = Decimal(0)
    for player in players:
        if player["eligibility"] not in statuses:
            continue
        salary = player["contract"]["salary"]
        if salary is not None:
            total += Decimal(str(salary))
    return total


def cap_summary(
    gms: Sequence[GMRecord], players: Sequence[dict[str, Any]], rules: RulesConfig
) -> list[dict[str, Any]]:
    rostered_by_team: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for player in players:
        team_key = player.get("roster_team_key")
        if team_key:
            rostered_by_team[team_key].append(player)

    summaries: list[dict[str, Any]] = []
    for gm in gms:
        team_players = rostered_by_team.get(gm.team_key, [])
        protected_salary = salary_for_statuses(team_players, {"PROTECTED"})
        cap_hit_salary = salary_for_statuses(team_players, {"CAP_HIT"})
        committed_salary = protected_salary + cap_hit_salary
        expired_or_review_salary = salary_for_statuses(
            team_players, {"RFA", "UFA", "REVIEW"}
        )
        total_roster_salary = salary_for_statuses(
            team_players, set(CLASSIFICATION_ORDER)
        )
        cap_space = rules.salary_cap - committed_salary
        summaries.append(
            {
                "order": gm.order,
                "team": gm.team_name,
                "team_key": gm.team_key,
                "salary_cap": json_number(rules.salary_cap),
                "protected_salary": json_number(protected_salary),
                "cap_hit_salary": json_number(cap_hit_salary),
                "committed_salary": json_number(committed_salary),
                "cap_space": json_number(cap_space),
                "over_cap": cap_space < 0,
                "expired_or_review_salary_excluded": json_number(expired_or_review_salary),
                "total_roster_salary": json_number(total_roster_salary),
                "roster_entries": len(team_players),
            }
        )
    return summaries


def build_snapshot(
    gms: Sequence[GMRecord],
    projections: Sequence[ProjectionRecord],
    rosters: Sequence[RosterRecord],
    rules: RulesConfig,
    sources: dict[str, dict[str, str]],
    source_checksum: str,
    enrichment: EnrichmentReport,
) -> dict[str, Any]:
    gm_by_name = {record.team_name: record for record in gms}
    gm_team_names = set(gm_by_name)
    roster_team_names = {record.fantasy_team for record in rosters}
    projection_team_names = {
        record.listed_fantasy_team
        for record in projections
        if record.listed_fantasy_team is not None
    }

    errors: list[str] = []
    warnings: list[str] = []
    if len(gms) != EXPECTED_TEAM_COUNT:
        errors.append(f"GM directory contains {len(gms)} teams; expected {EXPECTED_TEAM_COUNT}.")
    missing_roster_teams = sorted(gm_team_names - roster_team_names)
    extra_roster_teams = sorted(roster_team_names - gm_team_names)
    if missing_roster_teams or extra_roster_teams:
        errors.append(
            "Roster/GM team mismatch: "
            f"missing={missing_roster_teams!r}, extra={extra_roster_teams!r}."
        )
    unknown_projection_teams = sorted(projection_team_names - gm_team_names)
    if unknown_projection_teams:
        errors.append(
            f"Projection CSV contains unknown fantasy teams: {unknown_projection_teams!r}."
        )

    roster_by_key = {record.source_key: record for record in rosters}
    players: list[dict[str, Any]] = []
    availability_conflicts: list[dict[str, str]] = []
    matched_roster_keys: set[str] = set()
    for projection in projections:
        roster = roster_by_key.get(projection.source_key)
        if roster is not None:
            matched_roster_keys.add(roster.source_key)
            if (
                projection.listed_fantasy_team is not None
                and projection.listed_fantasy_team != roster.fantasy_team
            ):
                availability_conflicts.append(
                    {
                        "source_key": projection.source_key,
                        "csv_team": projection.listed_fantasy_team,
                        "roster_team": roster.fantasy_team,
                    }
                )
        players.append(normalized_player(projection, roster, rules))

    unmatched_records = [record for record in rosters if record.source_key not in matched_roster_keys]
    for roster in unmatched_records:
        players.append(normalized_player(None, roster, rules))
    players.sort(key=lambda player: player["source_key"])

    unmatched_details = [unmatched_roster_detail(record) for record in unmatched_records]
    unmatched_details.sort(key=lambda item: (item["reason"], item["team"], item["name"]))
    unexpected_unmatched = [
        detail for detail in unmatched_details if not detail["expected_roster_only"]
    ]
    if unexpected_unmatched:
        warnings.append(
            f"{len(unexpected_unmatched)} non-goalie roster row(s) did not match a projection key."
        )
    if availability_conflicts:
        warnings.append(
            f"{len(availability_conflicts)} projection/roster fantasy-team assignment conflict(s)."
        )

    classification_counts = collections.Counter(
        player["eligibility"] for player in players
    )
    review_count = classification_counts["REVIEW"]
    if review_count:
        warnings.append(
            f"{review_count} player row(s) require review; apply mode may resolve missing birthdates."
        )

    projection_goalies = sum(record.position == "G" for record in projections)
    waiver_goalies = sum(record.position == "G" and record.is_waiver for record in projections)
    if waiver_goalies == 0:
        warnings.append(
            "No waiver/free-agent goalies were supplied; the goalie auction pool is incomplete."
        )

    real_goalies_by_team = collections.Counter(
        record.fantasy_team
        for record in rosters
        if record.position == "G" and record.special_kind is None
    )
    teams_without_goalies = [
        gm.team_name for gm in gms if real_goalies_by_team[gm.team_name] == 0
    ]
    if teams_without_goalies:
        warnings.append(
            "Roster teams with no real goalie row: " + ", ".join(teams_without_goalies) + "."
        )

    roster_section_counts = collections.Counter(record.section for record in rosters)
    unmatched_reason_counts = collections.Counter(
        detail["reason"] for detail in unmatched_details
    )
    team_rows: list[dict[str, Any]] = []
    for gm in gms:
        team_rosters = [record for record in rosters if record.team_key == gm.team_key]
        team_rows.append(
            {
                "order": gm.order,
                "team_key": gm.team_key,
                "name": gm.team_name,
                "abbreviation": gm.abbreviation,
                "manager": {
                    "name": gm.manager_name,
                    "email": gm.manager_email,
                },
                "roster_counts": {
                    "total": len(team_rosters),
                    "skaters": sum(record.section == "skaters" for record in team_rosters),
                    "goalies": sum(
                        record.position == "G" and record.special_kind is None
                        for record in team_rosters
                    ),
                    "special_entries": sum(
                        record.special_kind is not None for record in team_rosters
                    ),
                },
            }
        )

    validation = {
        "valid": not errors,
        "all_12_teams": (
            len(gms) == EXPECTED_TEAM_COUNT
            and roster_team_names == gm_team_names
            and not unknown_projection_teams
        ),
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "gm_teams": len(gms),
            "roster_teams": len(roster_team_names),
            "projection_teams": len(projection_team_names),
            "projection_rows": len(projections),
            "projection_skater_rows": sum(record.position != "G" for record in projections),
            "projection_goalie_rows": projection_goalies,
            "projection_waiver_rows": sum(record.is_waiver for record in projections),
            "projection_waiver_goalie_rows": waiver_goalies,
            "projection_rostered_rows": sum(not record.is_waiver for record in projections),
            "roster_rows": len(rosters),
            "roster_skaters": roster_section_counts["skaters"],
            "roster_goalies_section": roster_section_counts["goalies"],
            "matched_roster_rows": len(matched_roster_keys),
            "unmatched_roster_rows": len(unmatched_details),
            "unexpected_unmatched_roster_rows": len(unexpected_unmatched),
            "player_pool_rows": len(players),
            "review_rows": review_count,
        },
        "classification_counts": {
            status: classification_counts.get(status, 0) for status in CLASSIFICATION_ORDER
        },
        "unmatched_roster_reason_counts": dict(sorted(unmatched_reason_counts.items())),
        "unmatched_roster_rows": unmatched_details,
        "availability_conflicts": availability_conflicts,
        "teams_without_real_goalies": teams_without_goalies,
        "enrichment": enrichment.as_dict(),
        "cap_summary": cap_summary(gms, players, rules),
    }

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "league": {
            "slug": rules.league_slug,
            "name": "Ultimate Hardcore Hockey Pool",
            "draft_year": rules.draft_year,
            "rules_version": rules.rules_version,
            "salary_cap": json_number(rules.salary_cap),
            "age_cutoff_date": rules.cutoff_date.isoformat(),
            "rfa_max_age": rules.rfa_max_age,
        },
        "source_checksum": source_checksum,
        "sources": sources,
        "rules": rules.raw,
        "teams": team_rows,
        "players": players,
        "validation": validation,
    }


# ---------------------------------------------------------------------------
# Optional database enrichment and apply
# ---------------------------------------------------------------------------


def import_psycopg2() -> tuple[Any, Any]:
    try:
        import psycopg2  # type: ignore[import-not-found]
        import psycopg2.extras  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ApplyError(
            "--apply requires psycopg2 (for example, install psycopg2-binary). "
            "Dry-run mode has no third-party dependencies."
        ) from exc
    return psycopg2, psycopg2.extras


def normalize_postgres_dsn(value: str) -> str:
    # psycopg2 accepts postgresql:// but not SQLAlchemy's driver-qualified form.
    return value.replace("postgresql+psycopg2://", "postgresql://", 1)


def connect_database(psycopg2: Any, dsn: str, label: str) -> Any:
    try:
        return psycopg2.connect(normalize_postgres_dsn(dsn), connect_timeout=10)
    except Exception as exc:
        raise ApplyError(f"Could not connect to the configured {label} database.") from exc


def preflight_apply_schema(connection: Any) -> None:
    missing: list[str] = []
    try:
        with connection.cursor() as cursor:
            for table_name in REQUIRED_APPLY_TABLES:
                cursor.execute("SELECT to_regclass(%s)", (table_name,))
                if cursor.fetchone()[0] is None:
                    missing.append(table_name)
    except Exception as exc:
        raise ApplyError("Could not verify the fantasy database schema.") from exc
    if missing:
        migration_tables = [name for name in missing if ".uhhp_auction_" in name]
        if migration_tables:
            raise ApplyError(
                "Migration 022 auction tables are missing; run "
                "backend/sql/022_uhhp_auction_state.sql before --apply. Missing: "
                + ", ".join(migration_tables)
            )
        raise ApplyError("Required fantasy database tables are missing: " + ", ".join(missing))


def fetch_fantasy_enrichment(
    connection: Any, roster_records: Sequence[RosterRecord]
) -> tuple[dict[str, dict[str, Any]], int, int, int]:
    cbs_ids = sorted({record.cbs_player_id for record in roster_records})
    if not cbs_ids:
        return {}, 0, 0, 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.cbs_player_id,
                       p.birthdate,
                       COALESCE(p.nhl_player_id, m.nhl_player_id) AS nhl_player_id
                  FROM public.cbs_players AS p
                  LEFT JOIN public.cbs_player_map AS m
                    ON m.cbs_player_id = p.cbs_player_id
                 WHERE p.cbs_player_id = ANY(%s)
                """,
                (cbs_ids,),
            )
            rows = cursor.fetchall()
    except Exception as exc:
        raise ApplyError("Could not enrich roster rows from the fantasy database.") from exc

    enrichment: dict[str, dict[str, Any]] = {}
    birthdate_count = 0
    nhl_id_count = 0
    for cbs_player_id, birthdate_value, nhl_player_id in rows:
        parsed_birthdate = parse_iso_date(birthdate_value)
        parsed_nhl_id = int(nhl_player_id) if nhl_player_id is not None else None
        enrichment[str(cbs_player_id)] = {
            "birthdate": parsed_birthdate,
            "nhl_player_id": parsed_nhl_id,
        }
        birthdate_count += parsed_birthdate is not None
        nhl_id_count += parsed_nhl_id is not None
    return enrichment, len(rows), birthdate_count, nhl_id_count


def fetch_nhl_birthdates(psycopg2: Any, dsn: str, nhl_ids: Sequence[int]) -> dict[int, date]:
    if not nhl_ids:
        return {}
    connection = connect_database(psycopg2, dsn, "NHL")
    try:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.id, d.birth_date
                  FROM public.players AS p
                  LEFT JOIN public.player_details AS d
                    ON d.player_id = p.id
                 WHERE p.id = ANY(%s)
                """,
                (list(nhl_ids),),
            )
            result = {
                int(player_id): parsed
                for player_id, birthdate_value in cursor.fetchall()
                if (parsed := parse_iso_date(birthdate_value)) is not None
            }
        connection.rollback()
        return result
    except SourceValidationError:
        raise
    except Exception as exc:
        raise ApplyError("Could not enrich birthdates from the configured NHL database.") from exc
    finally:
        connection.close()


def enrich_rosters_for_apply(
    connection: Any,
    psycopg2: Any,
    extras: Any,
    roster_records: Sequence[RosterRecord],
) -> EnrichmentReport:
    fantasy, matched, fantasy_birthdates, fantasy_nhl_ids = fetch_fantasy_enrichment(
        connection, roster_records
    )
    for record in roster_records:
        found = fantasy.get(record.cbs_player_id)
        if found is None:
            continue
        if record.birthdate is None and found["birthdate"] is not None:
            record.birthdate = found["birthdate"]
        if record.nhl_player_id is None and found["nhl_player_id"] is not None:
            record.nhl_player_id = found["nhl_player_id"]

    nhl_dsn = os.environ.get("NHL_DATABASE_URL")
    missing_nhl_ids = sorted(
        {
            record.nhl_player_id
            for record in roster_records
            if record.birthdate is None and record.nhl_player_id is not None
        }
    )
    nhl_birthdates = (
        fetch_nhl_birthdates(psycopg2, nhl_dsn, missing_nhl_ids) if nhl_dsn else {}
    )
    cbs_updates: list[tuple[date, str]] = []
    nhl_used = 0
    for record in roster_records:
        if record.birthdate is not None or record.nhl_player_id is None:
            continue
        birthdate_value = nhl_birthdates.get(record.nhl_player_id)
        if birthdate_value is None:
            continue
        record.birthdate = birthdate_value
        cbs_updates.append((birthdate_value, record.cbs_player_id))
        nhl_used += 1

    written = 0
    if cbs_updates:
        try:
            with connection.cursor() as cursor:
                extras.execute_batch(
                    cursor,
                    """
                    UPDATE public.cbs_players
                       SET birthdate = %s
                     WHERE cbs_player_id = %s
                       AND birthdate IS NULL
                    """,
                    cbs_updates,
                    page_size=200,
                )
                written = cursor.rowcount if cursor.rowcount and cursor.rowcount > 0 else 0
        except Exception as exc:
            raise ApplyError("Could not persist NHL birthdate enrichment safely.") from exc

    return EnrichmentReport(
        attempted=True,
        fantasy_players_matched=matched,
        fantasy_birthdates_used=fantasy_birthdates,
        fantasy_nhl_ids_used=fantasy_nhl_ids,
        nhl_database_configured=bool(nhl_dsn),
        nhl_birthdates_used=nhl_used,
        birthdates_written_to_fantasy=written,
    )


def stable_owner_id(email: str) -> str:
    digest = hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()[:24]
    return f"uhhp-owner-{digest}"


def upsert_league(cursor: Any, snapshot: dict[str, Any]) -> int:
    league = snapshot["league"]
    cursor.execute(
        """
        INSERT INTO public.cbs_leagues (
          provider_slug, name, domain, sport, league_type, service_level, season
        ) VALUES (%s, %s, %s, 'nhl', 'mgmt', 'gold', %s)
        ON CONFLICT (provider_slug) DO UPDATE
          SET name = EXCLUDED.name,
              domain = EXCLUDED.domain,
              sport = EXCLUDED.sport,
              league_type = EXCLUDED.league_type,
              service_level = EXCLUDED.service_level,
              season = EXCLUDED.season
        RETURNING id
        """,
        (
            league["slug"],
            league["name"],
            "uhhp.hockey.cbssports.com",
            league["draft_year"],
        ),
    )
    return int(cursor.fetchone()[0])


def upsert_cbs_teams(cursor: Any, league_id: int, teams: Sequence[dict[str, Any]]) -> dict[str, str]:
    team_ids: dict[str, str] = {}
    for team in teams:
        manager = team["manager"]
        cursor.execute(
            """
            SELECT owner_id
              FROM public.cbs_owners
             WHERE LOWER(email) = LOWER(%s)
             ORDER BY created_at, owner_id
             LIMIT 1
            """,
            (manager["email"],),
        )
        owner_row = cursor.fetchone()
        owner_id = str(owner_row[0]) if owner_row else stable_owner_id(manager["email"])
        cursor.execute(
            """
            INSERT INTO public.cbs_owners (owner_id, display_name, email)
            VALUES (%s, %s, %s)
            ON CONFLICT (owner_id) DO UPDATE
              SET display_name = EXCLUDED.display_name,
                  email = EXCLUDED.email
            """,
            (owner_id, manager["name"], manager["email"]),
        )
        cursor.execute(
            """
            INSERT INTO public.cbs_league_owners (league_id, owner_id, role)
            VALUES (%s, %s, 'gm')
            ON CONFLICT (league_id, owner_id) DO UPDATE
              SET role = EXCLUDED.role
            """,
            (league_id, owner_id),
        )

        cursor.execute(
            """
            SELECT team_id
              FROM public.cbs_teams
             WHERE league_id = %s
               AND (
                 LOWER(team_name) = LOWER(%s)
                 OR LOWER(COALESCE(abbrev, '')) = LOWER(%s)
               )
             ORDER BY CASE WHEN LOWER(team_name) = LOWER(%s) THEN 0 ELSE 1 END,
                      created_at,
                      team_id
             LIMIT 1
             FOR UPDATE
            """,
            (league_id, team["name"], team["abbreviation"], team["name"]),
        )
        existing = cursor.fetchone()
        team_id = str(existing[0]) if existing else f"uhhp-{team['team_key']}"
        cursor.execute(
            """
            INSERT INTO public.cbs_teams (
              league_id, team_id, team_name, abbrev, owner_id, is_active
            ) VALUES (%s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (league_id, team_id) DO UPDATE
              SET team_name = EXCLUDED.team_name,
                  abbrev = EXCLUDED.abbrev,
                  owner_id = EXCLUDED.owner_id,
                  is_active = TRUE
            """,
            (
                league_id,
                team_id,
                team["name"],
                team["abbreviation"],
                owner_id,
            ),
        )
        team_ids[team["team_key"]] = team_id
    return team_ids


def upsert_draft(cursor: Any, extras: Any, league_id: int, snapshot: dict[str, Any]) -> tuple[Any, str]:
    league = snapshot["league"]
    metadata = {
        "importer": IMPORTER_NAME,
        "source_checksum": snapshot["source_checksum"],
        "snapshot_schema_version": snapshot["schema_version"],
        "source_files": snapshot["sources"],
        "rules": snapshot["rules"],
    }
    cursor.execute(
        """
        INSERT INTO public.uhhp_auction_drafts (
          league_id, draft_year, rules_version, metadata
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (league_id, draft_year) DO UPDATE
          SET rules_version = EXCLUDED.rules_version,
              metadata = public.uhhp_auction_drafts.metadata || EXCLUDED.metadata,
              updated_at = NOW()
        RETURNING id, status
        """,
        (
            league_id,
            league["draft_year"],
            league["rules_version"],
            extras.Json(metadata),
        ),
    )
    draft_id, status = cursor.fetchone()
    return draft_id, str(status)


def begin_import_run(
    cursor: Any,
    extras: Any,
    draft_id: Any,
    league_id: int,
    snapshot: dict[str, Any],
) -> Any:
    idempotency_key = (
        f"uhhp-auction-{snapshot['league']['draft_year']}:"
        f"{snapshot['source_checksum']}"
    )
    source_uri = ",".join(
        source["path"] for _, source in sorted(snapshot["sources"].items())
    )
    metadata = {
        "importer": IMPORTER_NAME,
        "rules_version": snapshot["league"]["rules_version"],
        "source_files": snapshot["sources"],
        "validation": {
            "warnings": snapshot["validation"]["warnings"],
            "classification_counts": snapshot["validation"]["classification_counts"],
            "unmatched_roster_reason_counts": snapshot["validation"][
                "unmatched_roster_reason_counts"
            ],
            "enrichment": snapshot["validation"]["enrichment"],
        },
    }
    cursor.execute(
        """
        INSERT INTO public.uhhp_auction_import_runs (
          draft_id,
          league_id,
          import_type,
          source,
          source_uri,
          source_checksum,
          status,
          idempotency_key,
          rows_seen,
          rows_inserted,
          rows_updated,
          rows_rejected,
          errors,
          metadata,
          started_at,
          finished_at
        ) VALUES (
          %s, %s, 'normalized_snapshot', 'uhhp_auction_2026', %s, %s,
          'running', %s, %s, 0, 0, 0, %s, %s, NOW(), NULL
        )
        ON CONFLICT (draft_id, idempotency_key)
          WHERE idempotency_key IS NOT NULL
        DO UPDATE SET
          league_id = EXCLUDED.league_id,
          import_type = EXCLUDED.import_type,
          source = EXCLUDED.source,
          source_uri = EXCLUDED.source_uri,
          source_checksum = EXCLUDED.source_checksum,
          status = 'running',
          rows_seen = EXCLUDED.rows_seen,
          rows_inserted = 0,
          rows_updated = 0,
          rows_rejected = 0,
          errors = EXCLUDED.errors,
          metadata = EXCLUDED.metadata,
          started_at = NOW(),
          finished_at = NULL,
          updated_at = NOW()
        RETURNING id
        """,
        (
            draft_id,
            league_id,
            source_uri,
            snapshot["source_checksum"],
            idempotency_key,
            len(snapshot["players"]),
            extras.Json([]),
            extras.Json(metadata),
        ),
    )
    return cursor.fetchone()[0]


def upsert_draft_teams(
    cursor: Any,
    draft_id: Any,
    league_id: int,
    teams: Sequence[dict[str, Any]],
    team_ids: dict[str, str],
) -> None:
    for team in teams:
        manager = team["manager"]
        cursor.execute(
            """
            INSERT INTO public.uhhp_auction_draft_teams (
              draft_id,
              league_id,
              team_id,
              canonical_abbrev,
              manager_name,
              manager_email,
              nomination_order,
              tie_break_priority
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (draft_id, league_id, team_id) DO UPDATE
              SET canonical_abbrev = EXCLUDED.canonical_abbrev,
                  manager_name = EXCLUDED.manager_name,
                  manager_email = EXCLUDED.manager_email,
                  updated_at = NOW()
            """,
            (
                draft_id,
                league_id,
                team_ids[team["team_key"]],
                team["abbreviation"],
                manager["name"],
                manager["email"],
                team["order"],
                team["order"],
            ),
        )


def player_pool_values(
    player: dict[str, Any],
    draft_id: Any,
    league_id: int,
    team_ids: dict[str, str],
    extras: Any,
) -> tuple[Any, ...]:
    controlling_key = player.get("controlling_team_key")
    controlling_team_id = team_ids.get(controlling_key) if controlling_key else None
    roster_team_key = player.get("roster_team_key")
    roster_team_id = team_ids.get(roster_team_key) if roster_team_key else None
    metadata = {
        "normalized_name": player["normalized_name"],
        "auction_eligible": player["auction_eligible"],
        "is_waiver": player["is_waiver"],
        "listed_fantasy_team": player["listed_fantasy_team"],
        "rostered": player["rostered"],
        "roster_team": player["roster_team"],
        "roster_team_key": roster_team_key,
        "roster_team_id": roster_team_id,
        "roster_section": player["roster_section"],
        "projection_row": player["projection_row"],
        "classification_reason": player["classification_reason"],
    }
    contract = player["contract"]
    return (
        draft_id,
        league_id,
        player["source_key"],
        player["cbs_player_id"],
        player["nhl_player_id"],
        player["name"],
        [player["position"]],
        player["nhl_team"],
        parse_iso_date(player["birthdate"]),
        parse_iso_date(player["age_cutoff_date"]),
        player["age_at_cutoff"],
        player["source_availability"],
        player["roster_team"] or player["listed_fantasy_team"],
        contract["years"],
        contract["salary"],
        contract["rookie"],
        player["source_status"],
        player["entry_type"],
        player["eligibility"],
        controlling_team_id,
        extras.Json(player["projection"]),
        player["projected_fantasy_points"],
        extras.Json(metadata),
    )


def upsert_player_pool(
    cursor: Any,
    extras: Any,
    draft_id: Any,
    league_id: int,
    players: Sequence[dict[str, Any]],
    team_ids: dict[str, str],
) -> tuple[int, int]:
    cursor.execute(
        """
        SELECT id, source_key, cbs_player_id, nhl_player_id
          FROM public.uhhp_auction_player_pool
         WHERE draft_id = %s
         FOR UPDATE
        """,
        (draft_id,),
    )
    by_source: dict[str, Any] = {}
    by_cbs: dict[str, Any] = {}
    by_nhl: dict[int, Any] = {}
    for row_id, source_key, cbs_player_id, nhl_player_id in cursor.fetchall():
        by_source[str(source_key)] = row_id
        if cbs_player_id is not None:
            by_cbs[str(cbs_player_id)] = row_id
        if nhl_player_id is not None:
            by_nhl[int(nhl_player_id)] = row_id

    update_parameters: list[tuple[Any, ...]] = []
    insert_parameters: list[tuple[Any, ...]] = []
    seen_cbs: dict[str, str] = {}
    seen_nhl: dict[int, str] = {}
    for player in players:
        cbs_player_id = player.get("cbs_player_id")
        nhl_player_id = player.get("nhl_player_id")
        if cbs_player_id:
            prior = seen_cbs.setdefault(str(cbs_player_id), player["source_key"])
            if prior != player["source_key"]:
                raise ApplyError("Two normalized rows resolve to the same CBS player ID.")
        if nhl_player_id is not None:
            prior = seen_nhl.setdefault(int(nhl_player_id), player["source_key"])
            if prior != player["source_key"]:
                raise ApplyError("Two normalized rows resolve to the same NHL player ID.")

        candidate_ids = {
            candidate
            for candidate in (
                by_source.get(player["source_key"]),
                by_cbs.get(str(cbs_player_id)) if cbs_player_id else None,
                by_nhl.get(int(nhl_player_id)) if nhl_player_id is not None else None,
            )
            if candidate is not None
        }
        if len(candidate_ids) > 1:
            raise ApplyError(
                "Existing auction player identities conflict across source/CBS/NHL keys."
            )
        values = player_pool_values(player, draft_id, league_id, team_ids, extras)
        if candidate_ids:
            update_parameters.append(values + (next(iter(candidate_ids)),))
        else:
            insert_parameters.append(values)

    columns = """
      draft_id, league_id, source_key, cbs_player_id, nhl_player_id,
      player_name, positions, nhl_team_abbrev, birthdate, age_cutoff_date,
      age_at_cutoff, source_availability, source_team, contract_years, salary,
      is_rookie, source_status, entry_type, eligibility, controlling_team_id,
      projection, projected_fantasy_points, metadata
    """
    placeholders = ", ".join(["%s"] * 23)
    if insert_parameters:
        extras.execute_batch(
            cursor,
            f"""
            INSERT INTO public.uhhp_auction_player_pool ({columns})
            VALUES ({placeholders})
            """,
            insert_parameters,
            page_size=200,
        )
    if update_parameters:
        extras.execute_batch(
            cursor,
            """
            UPDATE public.uhhp_auction_player_pool
               SET draft_id = %s,
                   league_id = %s,
                   source_key = %s,
                   cbs_player_id = %s,
                   nhl_player_id = %s,
                   player_name = %s,
                   positions = %s,
                   nhl_team_abbrev = %s,
                   birthdate = %s,
                   age_cutoff_date = %s,
                   age_at_cutoff = %s,
                   source_availability = %s,
                   source_team = %s,
                   contract_years = %s,
                   salary = %s,
                   is_rookie = %s,
                   source_status = %s,
                   entry_type = %s,
                   eligibility = %s,
                   controlling_team_id = %s,
                   projection = %s,
                   projected_fantasy_points = %s,
                   metadata = %s,
                   updated_at = NOW()
             WHERE id = %s
            """,
            update_parameters,
            page_size=200,
        )
    return len(insert_parameters), len(update_parameters)


def finish_import_run(
    cursor: Any,
    extras: Any,
    import_run_id: Any,
    inserted: int,
    updated: int,
    snapshot: dict[str, Any],
) -> None:
    result_metadata = {
        "result": {
            "rows_seen": len(snapshot["players"]),
            "rows_inserted": inserted,
            "rows_updated": updated,
            "review_rows": snapshot["validation"]["counts"]["review_rows"],
        }
    }
    cursor.execute(
        """
        UPDATE public.uhhp_auction_import_runs
           SET status = 'completed',
               rows_inserted = %s,
               rows_updated = %s,
               rows_rejected = 0,
               errors = %s,
               metadata = metadata || %s,
               finished_at = NOW(),
               updated_at = NOW()
         WHERE id = %s
        """,
        (inserted, updated, extras.Json([]), extras.Json(result_metadata), import_run_id),
    )


def upsert_current_rosters(
    cursor: Any,
    extras: Any,
    league_id: int,
    players: Sequence[dict[str, Any]],
    team_ids: dict[str, str],
) -> tuple[int, int]:
    """Populate the current-season team rosters in ``cbs_rosters``.

    Only real players and rookies that are rostered in the snapshot are
    written (entry types ``player``/``rookie`` with a roster team). Draft-pick
    assets and cap-hit placeholders are excluded. Auction-created contract
    rows (those with a non-null ``uhhp_auction_nomination_id``) are never
    touched, so re-imports replace only snapshot rows.
    """
    rows: list[tuple[Any, ...]] = []
    for player in players:
        entry_type = str(player.get("entry_type") or "")
        if entry_type not in ("player", "rookie"):
            continue
        roster_team_key = player.get("roster_team_key")
        cbs_player_id = player.get("cbs_player_id")
        if not roster_team_key or not cbs_player_id:
            continue
        roster_team_id = team_ids.get(str(roster_team_key))
        if not roster_team_id:
            continue
        positions = player.get("positions") or player.get("position")
        slot_type = None
        if isinstance(positions, list) and positions:
            slot_type = str(positions[0])
        elif isinstance(positions, str):
            slot_type = positions
        contract = player.get("contract") or {}
        salary = contract.get("salary")
        years = contract.get("years")
        rookie = bool(contract.get("rookie")) or entry_type == "rookie"
        status = player.get("source_status")
        rows.append(
            (
                league_id,
                str(roster_team_id),
                str(cbs_player_id),
                player.get("nhl_player_id"),
                slot_type,
                status,
                salary if salary is not None else 0,
                years if years is not None else 0,
                rookie,
            )
        )

    if not rows:
        return 0, 0

    # Ensure placeholder cbs_players rows exist so the FK is satisfied for any
    # CBS IDs not already present (goalies/rookies imported from the snapshot).
    names: dict[str, str] = {}
    for player in players:
        cid = player.get("cbs_player_id")
        if cid:
            names.setdefault(str(cid), str(player.get("name") or "Unknown"))
    try:
        extras.execute_batch(
            cursor,
            """
            INSERT INTO public.cbs_players (cbs_player_id, full_name)
            VALUES (%s, %s)
            ON CONFLICT (cbs_player_id) DO NOTHING
            """,
            [(cid, names[cid]) for cid in names],
            page_size=200,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise ApplyError(
            f"Could not prepare cbs_players placeholder rows ({type(exc).__name__})."
        ) from exc

    try:
        # Snapshot rows use a managed lifecycle: delete all rows from the
        # previous import, then insert the current snapshot. Auction-created
        # contract rows (uhhp_auction_nomination_id IS NOT NULL) are never
        # deleted. The unique index includes effective_from, so a plain upsert
        # cannot be idempotent across imports; delete-then-insert avoids
        # duplicates while preserving auction rows.
        cursor.execute(
            """
            DELETE FROM public.cbs_rosters
             WHERE league_id = %s
               AND uhhp_auction_nomination_id IS NULL
               AND source_url = 'uhhp-auction-import-2026'
            """,
            (league_id,),
        )
        extras.execute_batch(
            cursor,
            """
            INSERT INTO public.cbs_rosters (
              league_id, team_id, season, cbs_player_id, nhl_player_id,
              slot_type, status, salary, years, rookie,
              effective_from, source_url, uhhp_auction_nomination_id
            ) VALUES (
              %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NOW(),
              'uhhp-auction-import-2026', NULL
            )
            """,
            rows,
            page_size=200,
        )
    except Exception as exc:
        raise ApplyError(
            f"Could not write cbs_rosters snapshot ({type(exc).__name__})."
        ) from exc

    return len(rows), 0


def apply_snapshot(connection: Any, extras: Any, snapshot: dict[str, Any]) -> ApplyResult:
    if not snapshot["validation"]["valid"]:
        raise ApplyError("Refusing to apply a snapshot with validation errors.")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (f"uhhp-auction-import-{snapshot['league']['draft_year']}",),
            )
            league_id = upsert_league(cursor, snapshot)
            team_ids = upsert_cbs_teams(cursor, league_id, snapshot["teams"])
            draft_id, _draft_status = upsert_draft(cursor, extras, league_id, snapshot)
            import_run_id = begin_import_run(
                cursor, extras, draft_id, league_id, snapshot
            )
            upsert_draft_teams(
                cursor, draft_id, league_id, snapshot["teams"], team_ids
            )
            inserted, updated = upsert_player_pool(
                cursor,
                extras,
                draft_id,
                league_id,
                snapshot["players"],
                team_ids,
            )
            roster_inserted, roster_updated = upsert_current_rosters(
                cursor,
                extras,
                league_id,
                snapshot["players"],
                team_ids,
            )
            finish_import_run(
                cursor, extras, import_run_id, inserted, updated, snapshot
            )
            cursor.execute(
                """
                UPDATE public.uhhp_auction_drafts
                   SET metadata = metadata || %s,
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (
                    extras.Json(
                        {
                            "last_import_run_id": str(import_run_id),
                            "last_source_checksum": snapshot["source_checksum"],
                            "last_roster_upsert": {
                                "inserted": roster_inserted,
                                "updated": roster_updated,
                            },
                        }
                    ),
                    draft_id,
                ),
            )
        return ApplyResult(
            teams_upserted=len(snapshot["teams"]),
            player_rows_seen=len(snapshot["players"]),
            player_rows_inserted=inserted,
            player_rows_updated=updated,
        )
    except ImporterError:
        raise
    except Exception as exc:
        raise ApplyError(
            f"Database apply failed ({type(exc).__name__}); no changes were committed."
        ) from exc


# ---------------------------------------------------------------------------
# Reporting, JSON output, and CLI
# ---------------------------------------------------------------------------


def format_money(value: float | None) -> str:
    if value is None:
        return "-"
    number = Decimal(str(value))
    return str(int(number)) if number == number.to_integral_value() else str(number)


def print_validation_report(
    snapshot: dict[str, Any], *, applied: bool, apply_result: ApplyResult | None
) -> None:
    validation = snapshot["validation"]
    counts = validation["counts"]
    mode = "APPLY" if applied else "DRY RUN"
    print(f"UHHP {snapshot['league']['draft_year']} auction import — {mode}")
    print("=" * 54)
    team_marker = "OK" if validation["all_12_teams"] else "ERROR"
    print(
        f"[{team_marker}] Teams: GM directory {counts['gm_teams']}/{EXPECTED_TEAM_COUNT}; "
        f"roster {counts['roster_teams']}/{EXPECTED_TEAM_COUNT}; "
        f"projection assignments {counts['projection_teams']}/{EXPECTED_TEAM_COUNT}"
    )
    print(
        "Sources: "
        f"{counts['projection_rows']} projected players "
        f"({counts['projection_skater_rows']} skaters, "
        f"{counts['projection_goalie_rows']} goalies; "
        f"{counts['projection_waiver_rows']} W/free agents, "
        f"{counts['projection_rostered_rows']} roster-listed); "
        f"{counts['roster_rows']} roster rows "
        f"({counts['roster_skaters']} skaters, "
        f"{counts['roster_goalies_section']} goalie-section rows)"
    )
    print(
        f"Overlay: {counts['matched_roster_rows']} matched roster rows; "
        f"{counts['unmatched_roster_rows']} unmatched; "
        f"{counts['player_pool_rows']} normalized pool rows"
    )

    reasons = validation["unmatched_roster_reason_counts"]
    if reasons:
        reason_text = ", ".join(f"{key}={value}" for key, value in reasons.items())
        print(f"Unmatched roster rows: {counts['unmatched_roster_rows']} ({reason_text})")
        unexpected = [
            row
            for row in validation["unmatched_roster_rows"]
            if not row["expected_roster_only"]
        ]
        for row in unexpected:
            team = row["nhl_team"] or "-"
            print(
                f"  REVIEW MATCH: {row['team']} — {row['name']} "
                f"({row['position']}/{team})"
            )

    classifications = validation["classification_counts"]
    print(
        "Classifications: "
        + ", ".join(f"{status}={classifications[status]}" for status in CLASSIFICATION_ORDER)
    )
    print(f"Review count: {counts['review_rows']}")

    enrichment = validation["enrichment"]
    if enrichment["attempted"]:
        print(
            "Birthdate enrichment: "
            f"fantasy matches={enrichment['fantasy_players_matched']}, "
            f"fantasy birthdates={enrichment['fantasy_birthdates_used']}, "
            f"NHL birthdates={enrichment['nhl_birthdates_used']}"
        )

    print("\nCap summary (PROTECTED + CAP_HIT; expired/review salary excluded)")
    print(f"{'#':>2}  {'Team':<31} {'Prot':>5} {'Hit':>4} {'Used':>5} {'Space':>6}")
    for row in validation["cap_summary"]:
        print(
            f"{row['order']:>2}  {row['team'][:31]:<31} "
            f"{format_money(row['protected_salary']):>5} "
            f"{format_money(row['cap_hit_salary']):>4} "
            f"{format_money(row['committed_salary']):>5} "
            f"{format_money(row['cap_space']):>6}"
        )

    if validation["warnings"]:
        print("\nWarnings:")
        for warning in validation["warnings"]:
            print(f"  WARNING: {warning}")
    if validation["errors"]:
        print("\nValidation errors:")
        for error in validation["errors"]:
            print(f"  ERROR: {error}")

    if apply_result is not None:
        print(
            "\nDatabase apply: "
            f"teams={apply_result.teams_upserted}, "
            f"players seen={apply_result.player_rows_seen}, "
            f"inserted={apply_result.player_rows_inserted}, "
            f"updated={apply_result.player_rows_updated}"
        )
    elif not applied:
        print("\nDry run complete: no database connection was attempted and no data was changed.")


def write_snapshot(path_text: str, snapshot: dict[str, Any], source_paths: Iterable[Path]) -> Path:
    output_path = Path(path_text).expanduser()
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    resolved_output = output_path.resolve()
    protected_paths = {(REPO_ROOT / path).resolve() for path in source_paths}
    protected_paths.add(Path(__file__).resolve())
    if resolved_output in protected_paths:
        raise SourceValidationError("--json-output cannot overwrite an importer source file.")

    temporary_path: Path | None = None
    try:
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=resolved_output.parent,
            prefix=f".{resolved_output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(snapshot, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary_path.chmod(0o600)
        os.replace(temporary_path, resolved_output)
    except OSError as exc:
        try:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            pass
        raise SourceValidationError(f"Could not write JSON snapshot to {output_path}.") from exc
    return resolved_output


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize and validate the UHHP 2026 GM directory, roster contracts, "
            "skater and goalie projection pools, and canonical auction rules. The "
            "default is a database-free dry run."
        ),

        epilog=(
            "Apply mode requires FANTASY_DATABASE_URL and psycopg2. If "
            "NHL_DATABASE_URL is set, mapped NHL IDs are used to fill missing "
            "birthdates. Database URLs and credentials are never printed."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="parse, normalize, classify, and report without connecting to a database",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="transactionally enrich and upsert migration-022 auction tables",
    )
    parser.add_argument(
        "--json-output",
        metavar="PATH",
        help="write the deterministic normalized snapshot to PATH",
    )
    return parser


def load_sources() -> tuple[
    RulesConfig,
    list[GMRecord],
    list[ProjectionRecord],
    list[RosterRecord],
    dict[str, dict[str, str]],
    str,
]:
    absolute = {label: REPO_ROOT / path for label, path in SOURCE_PATHS.items()}
    rules = parse_rules(absolute["rules"])
    gms = parse_gms(absolute["gm_directory"])
    gm_by_name = {record.team_name: record for record in gms}
    skater_projections = parse_projection_csv(absolute["skater_projections"])
    goalie_projections = parse_goalie_projection_csv(absolute["goalie_projections"])
    projections = [*skater_projections, *goalie_projections]
    projection_keys = [record.source_key for record in projections]
    if len(projection_keys) != len(set(projection_keys)):
        raise SourceValidationError(
            "Skater and goalie projection files contain a duplicate player source key."
        )
    rosters = parse_rosters(absolute["rosters"], gm_by_name, rules)
    sources, checksum = source_fingerprints(SOURCE_PATHS)
    return rules, gms, projections, rosters, sources, checksum


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if sys.version_info < EXPECTED_PYTHON:
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2

    fantasy_connection: Any | None = None
    try:
        rules, gms, projections, rosters, sources, checksum = load_sources()
        enrichment = EnrichmentReport()
        snapshot = build_snapshot(
            gms, projections, rosters, rules, sources, checksum, enrichment
        )
        apply_result: ApplyResult | None = None

        if args.apply:
            if not snapshot["validation"]["valid"]:
                print_validation_report(snapshot, applied=False, apply_result=None)
                return 1
            fantasy_dsn = os.environ.get("FANTASY_DATABASE_URL")
            if not fantasy_dsn:
                raise ApplyError("--apply requires FANTASY_DATABASE_URL to be set.")
            psycopg2, extras = import_psycopg2()
            connection = connect_database(psycopg2, fantasy_dsn, "fantasy")
            fantasy_connection = connection
            connection.autocommit = False
            preflight_apply_schema(connection)
            enrichment = enrich_rosters_for_apply(
                connection, psycopg2, extras, rosters
            )
            snapshot = build_snapshot(
                gms, projections, rosters, rules, sources, checksum, enrichment
            )
            if not snapshot["validation"]["valid"]:
                raise ApplyError("Enriched snapshot failed validation; no changes were committed.")
            apply_result = apply_snapshot(connection, extras, snapshot)
            connection.commit()

        print_validation_report(snapshot, applied=args.apply, apply_result=apply_result)
        if args.json_output:
            output_path = write_snapshot(args.json_output, snapshot, SOURCE_PATHS.values())
            print(f"Normalized JSON snapshot: {output_path}")
        return 0 if snapshot["validation"]["valid"] else 1
    except ImporterError as exc:
        if fantasy_connection is not None:
            try:
                fantasy_connection.rollback()
            except Exception:
                pass
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if fantasy_connection is not None:
            try:
                fantasy_connection.rollback()
            except Exception:
                pass
        # Deliberately do not print arbitrary DB exception text; it can contain DSNs.
        print(
            f"ERROR: Unexpected importer failure ({type(exc).__name__}); no secrets were printed.",
            file=sys.stderr,
        )
        return 2
    finally:
        if fantasy_connection is not None:
            try:
                fantasy_connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
