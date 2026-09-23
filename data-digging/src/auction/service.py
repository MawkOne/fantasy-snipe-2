"""Transaction service for the canonical UHHP 2026 silent auction.

Every function here operates on an already-open SQLAlchemy session (the route
layer owns commit/rollback via ``get_fantasy_session``). Service functions are
responsible for row locks, conditional state transitions, append-only events,
and enforcing the rules in :mod:`src.auction.rules`.

Mutation endpoints in :mod:`src.api.uhhp_auction_routes` call these functions
after authenticating the user and resolving their team/role.
"""

from __future__ import annotations

import json
import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from src.auction.rules import (
    RFADecision,
    BidEvent,
    BidValidationError,
    compute_effective_bid,
    resolve_reveal,
    resolve_rfa_outcome,
    validate_bid,
)

logger = logging.getLogger(__name__)

ACTIVE_NOMINATION_STATUSES = (
    "awaiting_nomination",
    "sealed_bidding",
    "revealed",
    "rfa_match_pending",
)
DRAFT_STATUS_ACTIVE = "active"
COMPLETED_STAGE = "completed"

STAGE_ORDER = ("superstar", "ufa", "rfa_poaching")


class AuctionServiceError(Exception):
    """A safe-to-display auction service failure."""

    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.http_status = http_status


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _seq_str(value: Any) -> str:
    return str(value or "")


def _int_amount(value: Any) -> int:
    if value is None:
        return 0
    return int(Decimal(str(value)))


def _require(value: Any, message: str) -> Any:
    if value is None:
        raise AuctionServiceError(message, 400)
    return value


def _load_draft(session: Any, draft_id: str, *, for_update: bool = True) -> Any:
    row = session.execute(
        text(
            """
            SELECT id, league_id, draft_year, rules_version, status, stage,
                   stage_round, nomination_cursor, version, metadata,
                   started_at, completed_at
              FROM uhhp_auction_drafts
             WHERE id = :draft_id
             """
            + (" FOR UPDATE" if for_update else "")
        ),
        {"draft_id": str(draft_id)},
    ).fetchone()
    if row is None:
        raise AuctionServiceError("Draft not found", 404)
    return row


def _load_active_nomination(session: Any, draft_id: str, *, for_update: bool = True) -> Optional[Any]:
    row = session.execute(
        text(
            """
            SELECT id, draft_id, league_id, status, stage, stage_round,
                   sequence_no, nominator_team_id, player_pool_id,
                   player_snapshot, high_bid_team_id, high_bid_amount,
                   winning_team_id, winning_bid_amount, contract_years,
                   outcome, version, nominated_at, bidding_opened_at,
                   revealed_at, finalized_at
              FROM uhhp_auction_nominations
             WHERE draft_id = :draft_id
               AND status IN ('awaiting_nomination','sealed_bidding','revealed','rfa_match_pending')
             ORDER BY created_at DESC
             LIMIT 1
             """
            + (" FOR UPDATE" if for_update else "")
        ),
        {"draft_id": str(draft_id)},
    ).fetchone()
    return row


def _load_nomination(session: Any, nomination_id: str, *, for_update: bool = True) -> Any:
    row = session.execute(
        text(
            """
            SELECT id, draft_id, league_id, status, stage, stage_round,
                   sequence_no, nominator_team_id, player_pool_id,
                   player_snapshot, high_bid_team_id, high_bid_amount,
                   winning_team_id, winning_bid_amount, contract_years,
                   outcome, version, nominated_at, bidding_opened_at,
                   revealed_at, finalized_at
              FROM uhhp_auction_nominations
             WHERE id = :nomination_id
             """
            + (" FOR UPDATE" if for_update else "")
        ),
        {"nomination_id": str(nomination_id)},
    ).fetchone()
    if row is None:
        raise AuctionServiceError("Nomination not found", 404)
    return row


def _load_player(session: Any, draft_id: str, pool_id: Optional[str]) -> Optional[Any]:
    if not pool_id:
        return None
    return session.execute(
        text(
            """
            SELECT id, cbs_player_id, nhl_player_id, player_name, positions,
                   nhl_team_abbrev, birthdate, eligibility,
                   controlling_team_id, projected_fantasy_points, projection
              FROM uhhp_auction_player_pool
             WHERE id = :pool_id AND draft_id = :draft_id
            """
        ),
        {"pool_id": str(pool_id), "draft_id": str(draft_id)},
    ).fetchone()


def _ordered_teams(session: Any, draft_id: str) -> List[Dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT team_id, canonical_abbrev, nomination_order,
                   tie_break_priority, rfa_nominations_active,
                   rfa_nominations_passed_at
              FROM uhhp_auction_draft_teams
             WHERE draft_id = :draft_id
             ORDER BY nomination_order ASC
            """
        ),
        {"draft_id": str(draft_id)},
    ).fetchall()
    teams: List[Dict[str, Any]] = []
    for row in rows:
        teams.append(
            {
                "team_id": str(row.team_id),
                "canonical_abbrev": str(row.canonical_abbrev),
                "nomination_order": int(row.nomination_order),
                "tie_break_priority": int(row.tie_break_priority),
                "rfa_nominations_active": bool(row.rfa_nominations_active),
                "rfa_nominations_passed_at": _iso(row.rfa_nominations_passed_at),
            }
        )
    teams.sort(key=lambda t: t["nomination_order"])
    return teams


def _current_nominator(session: Any, draft: Any) -> Optional[Dict[str, Any]]:
    """Return the team whose turn it is to nominate, skipping passed RFA teams."""
    teams = _ordered_teams(session, str(draft.id))
    if not teams:
        return None
    if draft.stage != "rfa_poaching":
        ordered = teams
    else:
        ordered = [t for t in teams if t["rfa_nominations_active"]]
        if not ordered:
            return None
    cursor = int(draft.nomination_cursor or 0)
    if not ordered:
        return None
    index = cursor % len(ordered)
    return ordered[index]


def _append_event(
    session: Any,
    draft_id: str,
    league_id: int,
    event_type: str,
    *,
    nomination_id: Optional[str] = None,
    team_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> None:
    try:
        session.execute(
            text(
                """
                INSERT INTO uhhp_auction_events (
                  draft_id, league_id, nomination_id, team_id, event_type,
                  actor_type, actor_id, idempotency_key, payload
                ) VALUES (
                  :draft_id, :league_id, :nomination_id, :team_id, :event_type,
                  :actor_type, :actor_id, :idempotency_key, CAST(:payload AS JSONB)
                )
                """
            ),
            {
                "draft_id": str(draft_id),
                "league_id": int(league_id),
                "nomination_id": nomination_id,
                "team_id": team_id,
                "event_type": str(event_type),
                "actor_type": actor_type,
                "actor_id": actor_id,
                "idempotency_key": idempotency_key,
                "payload": json.dumps(metadata or {}),
            },
        )
    except Exception as exc:  # pragma: no cover - defensive only
        logger.warning("Failed to append auction event %s: %s", event_type, type(exc).__name__)


def _nomination_count_for_round(session: Any, draft_id: str, stage: str, stage_round: int) -> int:
    row = session.execute(
        text(
            """
            SELECT COUNT(*) AS n
              FROM uhhp_auction_nominations
             WHERE draft_id = :draft_id AND stage = :stage AND stage_round = :stage_round
            """
        ),
        {"draft_id": str(draft_id), "stage": stage, "stage_round": int(stage_round)},
    ).fetchone()
    return int(row.n if row else 0)


def _stage_advancement(session: Any, draft: Any, teams: List[Dict[str, Any]]) -> Tuple[str, int, bool]:
    """Return the next stage/round after a nomination concludes, plus whether draft is complete."""
    stage = str(draft.stage)
    stage_round = int(draft.stage_round)
    team_count = max(len(teams), 1)
    completed_count = _nomination_count_for_round(session, str(draft.id), stage, stage_round)

    if stage == "superstar":
        if completed_count >= team_count:
            return "ufa", 1, False
        return stage, stage_round, False
    if stage == "ufa":
        if stage_round == 1 and completed_count >= team_count:
            return "ufa", 2, False
        if stage_round == 2 and completed_count >= team_count:
            return "rfa_poaching", 1, False
        return stage, stage_round, False
    if stage == "rfa_poaching":
        active = [t for t in teams if t["rfa_nominations_active"]]
        if not active:
            return COMPLETED_STAGE, 1, True
        return stage, stage_round, False
    return COMPLETED_STAGE, stage_round, True


def _set_draft_stage(session: Any, draft_id: str, league_id: int, stage: str, stage_round: int, *, completed: bool = False) -> None:
    if completed:
        session.execute(
            text(
                """
                UPDATE uhhp_auction_drafts
                   SET stage = :stage, stage_round = :stage_round,
                       status = 'completed', completed_at = :completed_at,
                       nomination_cursor = 0, version = version + 1,
                       updated_at = NOW()
                 WHERE id = :draft_id
                """
            ),
            {
                "stage": stage,
                "stage_round": int(stage_round),
                "completed_at": _now(),
                "draft_id": str(draft_id),
            },
        )
        _append_event(
            session,
            draft_id,
            league_id,
            "draft_completed",
            metadata={"stage": stage},
        )
    else:
        session.execute(
            text(
                """
                UPDATE uhhp_auction_drafts
                   SET stage = :stage, stage_round = :stage_round,
                       nomination_cursor = 0, version = version + 1,
                       updated_at = NOW()
                 WHERE id = :draft_id
                """
            ),
            {"stage": stage, "stage_round": int(stage_round), "draft_id": str(draft_id)},
        )
        _append_event(
            session,
            draft_id,
            league_id,
            "stage_changed",
            metadata={"stage": stage, "stage_round": int(stage_round)},
        )


def _advance_cursor(session: Any, draft_id: str, league_id: int) -> None:
    """Advance the nomination cursor to the next eligible nominator."""
    session.execute(
        text(
            """
            UPDATE uhhp_auction_drafts
               SET nomination_cursor = nomination_cursor + 1,
                   version = version + 1,
                   updated_at = NOW()
             WHERE id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    )
    _append_event(session, draft_id, league_id, "cursor_advanced")


def _create_contract_roster(
    session: Any,
    *,
    league_id: int,
    draft_id: str,
    nomination_id: str,
    team_id: str,
    player: Any,
    salary: int,
) -> dict[str, Any]:
    cbs_player_id = _seq_str(player.cbs_player_id) if player and player.cbs_player_id else None
    nhl_player_id = int(player.nhl_player_id) if player and player.nhl_player_id else None
    player_name = player.player_name if player else "Unknown player"
    positions = list(player.positions or []) if player else []
    position = positions[0] if positions else "F"

    # All draft-day acquisitions are 3-year contracts at the winning bid.
    row = session.execute(
        text(
            """
            SELECT draft_year
              FROM uhhp_auction_drafts
             WHERE id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    ).fetchone()
    season = int(row.draft_year) if row else None

    inserted = session.execute(
        text(
            """
            INSERT INTO cbs_rosters (
              league_id, team_id, season, cbs_player_id, nhl_player_id,
              slot_type, status, salary, years, rookie,
              uhhp_auction_nomination_id, effective_from, source_url
            ) VALUES (
              :league_id, :team_id, :season, :cbs_player_id, :nhl_player_id,
              'A', 'signed', :salary, 3, FALSE,
              :nomination_id, NOW(), 'uhhp-auction-2026'
            )
            ON CONFLICT (uhhp_auction_nomination_id)
              WHERE uhhp_auction_nomination_id IS NOT NULL
            DO UPDATE SET
              league_id = EXCLUDED.league_id,
              team_id = EXCLUDED.team_id,
              cbs_player_id = EXCLUDED.cbs_player_id,
              nhl_player_id = EXCLUDED.nhl_player_id,
              slot_type = EXCLUDED.slot_type,
              status = EXCLUDED.status,
              salary = EXCLUDED.salary,
              years = EXCLUDED.years,
              effective_from = EXCLUDED.effective_from
            RETURNING id
            """
        ),
        {
            "league_id": int(league_id),
            "team_id": str(team_id),
            "season": season,
            "cbs_player_id": cbs_player_id,
            "nhl_player_id": nhl_player_id,
            "salary": int(salary),
            "nomination_id": str(nomination_id),
        },
    ).fetchone()

    return {
        "roster_id": str(inserted[0]) if inserted else None,
        "team_id": str(team_id),
        "player_name": player_name,
        "position": position,
        "salary": int(salary),
        "years": 3,
        "cbs_player_id": cbs_player_id,
        "nhl_player_id": nhl_player_id,
    }


def _finalize_nomination(
    session: Any,
    *,
    nomination_id: str,
    draft_id: str,
    league_id: int,
    winning_team_id: str,
    winning_bid: int,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    nomination = _load_nomination(session, nomination_id, for_update=True)
    player = _load_player(session, draft_id, _seq_str(nomination.player_pool_id))
    contract = _create_contract_roster(
        session,
        league_id=league_id,
        draft_id=draft_id,
        nomination_id=nomination_id,
        team_id=winning_team_id,
        player=player,
        salary=winning_bid,
    )
    session.execute(
        text(
            """
            UPDATE uhhp_auction_nominations
               SET status = 'finalized',
                   winning_team_id = :winning_team_id,
                   winning_bid_amount = :winning_bid,
                   contract_years = 3,
                   outcome = CAST(:outcome AS JSONB),
                   finalized_at = :finalized_at,
                   version = version + 1,
                   updated_at = NOW()
             WHERE id = :nomination_id
            """
        ),
        {
            "winning_team_id": str(winning_team_id),
            "winning_bid": int(winning_bid),
            "outcome": json.dumps(outcome),
            "finalized_at": _now(),
            "nomination_id": str(nomination_id),
        },
    )
    _append_event(
        session,
        draft_id,
        league_id,
        "nomination_finalized",
        nomination_id=nomination_id,
        team_id=winning_team_id,
        metadata={"winning_bid": int(winning_bid), "roster_id": contract["roster_id"]},
    )
    return contract


def activate_draft(session: Any, draft_id: str, *, actor_role: str) -> dict[str, Any]:
    """Set a setup draft to active. Commissioner only."""
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can activate the draft", 403)
    draft = _load_draft(session, draft_id)
    if draft.status == DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is already active", 409)
    session.execute(
        text(
            """
            UPDATE uhhp_auction_drafts
               SET status = 'active', started_at = :started_at,
                   version = version + 1, updated_at = NOW()
             WHERE id = :draft_id
            """
        ),
        {"started_at": _now(), "draft_id": str(draft_id)},
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "draft_activated",
        actor_type="user",
        actor_id=str(actor_role),
    )
    return {"ok": True, "status": "active"}


def nominate_player(
    session: Any,
    *,
    draft_id: str,
    actor_team_id: str,
    actor_role: str,
    player_pool_id: str,
) -> dict[str, Any]:
    """Open a sealed-bid auction for a player. Current nominator only."""
    draft = _load_draft(session, draft_id)
    if draft.status != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
    if draft.stage == COMPLETED_STAGE:
        raise AuctionServiceError("Draft is completed", 409)

    current = _current_nominator(session, draft)
    if current is None or current["team_id"] != actor_team_id:
        raise AuctionServiceError(
            "It is not this team's turn to nominate", 403
        )

    # One active nomination enforced both here and by a partial unique index.
    active = _load_active_nomination(session, str(draft_id))
    if active is not None:
        raise AuctionServiceError("An auction is already active", 409)

    player = _load_player(session, str(draft_id), player_pool_id)
    if player is None:
        raise AuctionServiceError("Player not found in the auction pool", 404)

    eligibility = str(player.eligibility)
    if draft.stage in ("superstar", "rfa_poaching"):
        expected = "RFA" if draft.stage == "rfa_poaching" else None
        if expected and eligibility != expected:
            raise AuctionServiceError("Only RFA players may be nominated during RFA Poaching", 400)
    elif draft.stage == "ufa" and eligibility != "UFA":
        raise AuctionServiceError("Only UFA players may be nominated during UFA rounds", 400)

    stage_round = int(draft.stage_round or 1)
    sequence_no = _nomination_count_for_round(session, str(draft_id), str(draft.stage), stage_round) + 1

    snapshot = {
        "pool_id": str(player.id),
        "name": player.player_name,
        "position": (list(player.positions or []) or ["F"])[0],
        "nhl_team": player.nhl_team_abbrev,
        "eligibility": eligibility,
        "controlling_team_id": _seq_str(player.controlling_team_id) if player.controlling_team_id else None,
        "projected_fantasy_points": (
            float(player.projected_fantasy_points)
            if player.projected_fantasy_points is not None
            else None
        ),
    }

    nomination_id = str(uuid_mod.uuid4())
    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_nominations (
              id, draft_id, league_id, status, stage, stage_round,
              sequence_no, nominator_team_id, player_pool_id,
              player_snapshot, bidding_opened_at, created_at, updated_at
            ) VALUES (
              :id, :draft_id, :league_id, 'sealed_bidding', :stage,
              :stage_round, :sequence_no, :nominator_team_id,
              :player_pool_id, CAST(:snapshot AS JSONB), :bidding_opened_at,
              NOW(), NOW()
            )
            """
        ),
        {
            "id": nomination_id,
            "draft_id": str(draft_id),
            "league_id": int(draft.league_id),
            "stage": str(draft.stage),
            "stage_round": stage_round,
            "sequence_no": sequence_no,
            "nominator_team_id": str(actor_team_id),
            "player_pool_id": str(player.id),
            "snapshot": json.dumps(snapshot),
            "bidding_opened_at": _now(),
        },
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "player_nominated",
        nomination_id=nomination_id,
        team_id=str(actor_team_id),
        metadata={"player_pool_id": str(player.id), "stage": str(draft.stage)},
    )
    return {"ok": True, "nomination_id": nomination_id, "status": "sealed_bidding"}


def _bid_target_exists(session: Any, nomination_id: str, team_id: str) -> Optional[Any]:
    return session.execute(
        text(
            """
            SELECT id
              FROM uhhp_auction_bid_events
             WHERE nomination_id = :nomination_id AND team_id = :team_id
             ORDER BY event_sequence DESC
             LIMIT 1
            """
        ),
        {"nomination_id": str(nomination_id), "team_id": str(team_id)},
    ).fetchone()


def submit_bid(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_team_id: str,
    amount: Any,
    idempotency_key: str,
) -> dict[str, Any]:
    """Submit an initial sealed bid ($0 or whole units >= 2)."""
    draft = _load_draft(session, draft_id)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "sealed_bidding":
        raise AuctionServiceError("Bidding is not open for this nomination", 409)

    try:
        validated = validate_bid(int(amount)) if isinstance(amount, (int, float, str)) else validate_bid(amount)
    except (BidValidationError, TypeError, ValueError) as exc:
        raise AuctionServiceError("Invalid bid amount: " + str(exc), 400) from exc

    prior = _bid_target_exists(session, nomination_id, actor_team_id)
    if prior is not None:
        raise AuctionServiceError("A bid already exists; use replacement or cancel first", 409)

    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_bid_events (
              nomination_id, draft_id, league_id, team_id, event_type,
              amount, idempotency_key, actor_id
            ) VALUES (
              :nomination_id, :draft_id, :league_id, :team_id, 'submit',
              :amount, :idempotency_key, :actor_id
            )
            """
        ),
        {
            "nomination_id": str(nomination_id),
            "draft_id": str(draft_id),
            "league_id": int(draft.league_id),
            "team_id": str(actor_team_id),
            "amount": validated,
            "idempotency_key": str(idempotency_key),
            "actor_id": str(actor_team_id),
        },
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "bid_submitted",
        nomination_id=str(nomination_id),
        team_id=str(actor_team_id),
        actor_type="team",
        actor_id=str(actor_team_id),
        idempotency_key=str(idempotency_key),
        metadata={"amount": validated},
    )
    return {"ok": True, "status": "submitted", "effective_bid": validated, "submitted_amount": validated, "responded": True}


def replace_bid(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_team_id: str,
    amount: Any,
    idempotency_key: str,
) -> dict[str, Any]:
    """Replace an existing sealed bid (allowed any time before reveal)."""
    draft = _load_draft(session, draft_id)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "sealed_bidding":
        raise AuctionServiceError("Bidding is not open for this nomination", 409)
    try:
        validated = validate_bid(int(amount)) if isinstance(amount, (int, float, str)) else validate_bid(amount)
    except (BidValidationError, TypeError, ValueError) as exc:
        raise AuctionServiceError("Invalid bid amount: " + str(exc), 400) from exc
    prior = _bid_target_exists(session, nomination_id, actor_team_id)
    if prior is None:
        raise AuctionServiceError("No bid exists to replace; submit an initial bid instead", 409)

    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_bid_events (
              nomination_id, draft_id, league_id, team_id, event_type,
              amount, supersedes_bid_event_id, idempotency_key, actor_id
            ) VALUES (
              :nomination_id, :draft_id, :league_id, :team_id, 'replacement',
              :amount, :supersedes, :idempotency_key, :actor_id
            )
            """
        ),
        {
            "nomination_id": str(nomination_id),
            "draft_id": str(draft_id),
            "league_id": int(draft.league_id),
            "team_id": str(actor_team_id),
            "amount": validated,
            "supersedes": str(prior.id),
            "idempotency_key": str(idempotency_key),
            "actor_id": str(actor_team_id),
        },
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "bid_replaced",
        nomination_id=str(nomination_id),
        team_id=str(actor_team_id),
        actor_type="team",
        actor_id=str(actor_team_id),
        idempotency_key=str(idempotency_key),
        metadata={"amount": validated},
    )
    return {"ok": True, "status": "replaced", "effective_bid": 0, "submitted_amount": validated, "responded": True}


def cancel_bid(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_team_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Cancel the team's effective bid; returns it to $0. Allowed before reveal."""
    draft = _load_draft(session, draft_id)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "sealed_bidding":
        raise AuctionServiceError("Bidding is not open for this nomination", 409)
    prior = _bid_target_exists(session, nomination_id, actor_team_id)
    if prior is None:
        raise AuctionServiceError("No bid exists to cancel", 409)

    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_bid_events (
              nomination_id, draft_id, league_id, team_id, event_type,
              supersedes_bid_event_id, idempotency_key, actor_id
            ) VALUES (
              :nomination_id, :draft_id, :league_id, :team_id, 'cancel',
              :supersedes, :idempotency_key, :actor_id
            )
            """
        ),
        {
            "nomination_id": str(nomination_id),
            "draft_id": str(draft_id),
            "league_id": int(draft.league_id),
            "team_id": str(actor_team_id),
            "supersedes": str(prior.id),
            "idempotency_key": str(idempotency_key),
            "actor_id": str(actor_team_id),
        },
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "bid_cancelled",
        nomination_id=str(nomination_id),
        team_id=str(actor_team_id),
        actor_type="team",
        actor_id=str(actor_team_id),
        idempotency_key=str(idempotency_key),
    )
    return {"ok": True, "status": "cancelled", "effective_bid": 0, "responded": True}


def reveal_nomination(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_role: str,
    confirm_nonresponses: bool = False,
) -> dict[str, Any]:
    """Commissioner reveals sealed bids and resolves a winner or No Sale.

    For a positive UFA result the winner is finalized immediately into a
    three-year roster contract. For a positive RFA result the auction enters
    ``rfa_match_pending`` and only the controlling team may then match/pass.
    If every effective bid is zero the auction is a No Sale.
    Positive ties are resolved with the rotating tie-break priority and the
    winner is moved to the bottom of that order.
    """
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can reveal", 403)
    draft = _load_draft(session, draft_id)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "sealed_bidding":
        raise AuctionServiceError("This nomination is not accepting reveal", 409)

    teams = _ordered_teams(session, str(draft_id))
    tie_order = [t["team_id"] for t in sorted(teams, key=lambda t: t["tie_break_priority"])]

    # Load each team's ordered bid events.
    bid_rows = session.execute(
        text(
            """
            SELECT team_id, event_type, amount
              FROM uhhp_auction_bid_events
             WHERE nomination_id = :nomination_id
             ORDER BY event_sequence ASC
            """
        ),
        {"nomination_id": str(nomination_id)},
    ).fetchall()
    events_by_team: Dict[str, List[BidEvent]] = {}
    for row in bid_rows:
        tid = str(row.team_id)
        if row.event_type == "cancel":
            events_by_team.setdefault(tid, []).append(BidEvent.cancel())
        else:
            events_by_team.setdefault(tid, []).append(
                BidEvent.submit(int(row.amount)) if row.event_type == "submit" else BidEvent.replacement(int(row.amount))
            )

    result = resolve_reveal(events_by_team, tie_order)

    # Record revealed amount / high bidder (viewer-safe API still hides until reveal).
    high_bid = int(result.winning_bid)
    high_bid_team = result.winner if high_bid > 0 else None

    # Persist tie-break rotation and audit when a positive tie was resolved.
    if result.tie_was_resolved and result.winner is not None:
        winner = result.winner
        order_before = list(tie_order)
        order_after = list(result.updated_tie_order)
        session.execute(
            text(
                """
                INSERT INTO uhhp_auction_tie_audits (
                  nomination_id, draft_id, league_id, tied_amount,
                  tied_team_ids, winning_team_id,
                  old_tie_break_order, new_tie_break_order
                ) VALUES (
                  :nomination_id, :draft_id, :league_id, :tied_amount,
                  :tied_team_ids, :winning_team_id,
                  :old_order, :new_order
                )
                """
            ),
            {
                "nomination_id": str(nomination_id),
                "draft_id": str(draft_id),
                "league_id": int(draft.league_id),
                "tied_amount": int(high_bid),
                "tied_team_ids": list(result.audit.tie_break.tied_teams),
                "winning_team_id": str(winner),
                "old_order": order_before,
                "new_order": order_after,
            },
        )
        # Rotate priority: winner to bottom.
        for priority, tid in enumerate(order_after, start=1):
            session.execute(
                text(
                    """
                    UPDATE uhhp_auction_draft_teams
                       SET tie_break_priority = :priority, updated_at = NOW()
                     WHERE draft_id = :draft_id AND team_id = :team_id
                    """
                ),
                {"priority": priority, "draft_id": str(draft_id), "team_id": str(tid)},
            )

    player = _load_player(session, str(draft_id), _seq_str(nomination.player_pool_id))
    is_rfa = player is not None and str(player.eligibility) == "RFA"

    # Update nomination outcome row.
    if high_bid == 0:
        status = "no_sale"
        session.execute(
            text(
                """
                UPDATE uhhp_auction_nominations
                   SET status = 'no_sale', revealed_at = :revealed_at,
                       high_bid_amount = 0, high_bid_team_id = NULL,
                       winning_team_id = NULL, winning_bid_amount = 0,
                       outcome = CAST(:outcome AS JSONB),
                       version = version + 1, updated_at = NOW()
                 WHERE id = :nomination_id
                """
            ),
            {
                "revealed_at": _now(),
                "outcome": json.dumps({"result": "no_sale"}),
                "nomination_id": str(nomination_id),
            },
        )
        _append_event(
            session,
            str(draft_id),
            int(draft.league_id),
            "nomination_no_sale",
            nomination_id=str(nomination_id),
            metadata={"revealed": True},
        )
        # Advance stage/cursor after No Sale.
        _advance_or_transition(session, draft, teams)
        return {
            "ok": True,
            "result": "no_sale",
            "nomination_id": str(nomination_id),
            "winner": None,
            "winning_bid": 0,
            "status": "no_sale",
        }

    # Positive bid: RFA goes pending, UFA finalizes.
    if is_rfa:
        status = "rfa_match_pending"
        session.execute(
            text(
                """
                UPDATE uhhp_auction_nominations
                   SET status = 'rfa_match_pending', revealed_at = :revealed_at,
                       high_bid_team_id = :high_bid_team_id,
                       high_bid_amount = :high_bid_amount,
                       winning_team_id = NULL, winning_bid_amount = NULL,
                       contract_years = 3,
                       outcome = CAST(:outcome AS JSONB),
                       version = version + 1, updated_at = NOW()
                 WHERE id = :nomination_id
                """
            ),
            {
                "revealed_at": _now(),
                "high_bid_team_id": str(high_bid_team),
                "high_bid_amount": high_bid,
                "outcome": json.dumps(
                    {
                        "result": "rfa_match_pending",
                        "high_bid_team_id": str(high_bid_team),
                        "high_bid_amount": high_bid,
                        "controlling_team_id": _seq_str(
                            player.controlling_team_id if player else None
                        ),
                    }
                ),
                "nomination_id": str(nomination_id),
            },
        )
        _append_event(
            session,
            str(draft_id),
            int(draft.league_id),
            "nomination_revealed",
            nomination_id=str(nomination_id),
            team_id=str(high_bid_team),
            metadata={"rfa_match_pending": True, "high_bid": high_bid},
        )
        return {
            "ok": True,
            "result": "rfa_match_pending",
            "nomination_id": str(nomination_id),
            "winner": None,
            "winning_bid": high_bid,
            "status": "rfa_match_pending",
            "high_bid_team_id": str(high_bid_team),
        }

    # UFA: finalize immediately.
    contract = _finalize_nomination(
        session,
        nomination_id=str(nomination_id),
        draft_id=str(draft_id),
        league_id=int(draft.league_id),
        winning_team_id=str(high_bid_team),
        winning_bid=high_bid,
        outcome={"result": "sold", "revealed": True, "tie_break_applied": bool(result.tie_was_resolved)},
    )
    _advance_or_transition(session, draft, teams)
    return {
        "ok": True,
        "result": "sold",
        "nomination_id": str(nomination_id),
        "winner": str(high_bid_team),
        "winning_bid": high_bid,
        "status": "finalized",
        "contract": contract,
    }


def _advance_or_transition(session: Any, draft: Any, teams: List[Dict[str, Any]]) -> None:
    """After a nomination concludes, transition stages or advance the cursor."""
    next_stage, next_round, completed = _stage_advancement(session, draft, teams)
    if completed or next_stage != str(draft.stage) or next_round != int(draft.stage_round):
        _set_draft_stage(
            session,
            str(draft.id),
            int(draft.league_id),
            next_stage,
            next_round,
            completed=completed,
        )
        return
    # Same stage/round: advance the nominator cursor.
    _advance_cursor(session, str(draft.id), int(draft.league_id))


def pass_remaining_nominations(
    session: Any, *, draft_id: str, actor_team_id: str
) -> dict[str, Any]:
    """Permanently remove a team from the RFA Poaching nomination rotation."""
    draft = _load_draft(session, draft_id)
    if draft.stage != "rfa_poaching":
        raise AuctionServiceError("Can only pass remaining nominations during RFA Poaching", 400)

    row = session.execute(
        text(
            """
            UPDATE uhhp_auction_draft_teams
               SET rfa_nominations_active = FALSE,
                   rfa_nominations_passed_at = :passed_at,
                   updated_at = NOW()
             WHERE draft_id = :draft_id AND team_id = :team_id
               AND rfa_nominations_active = TRUE
            RETURNING team_id
            """
        ),
        {"passed_at": _now(), "draft_id": str(draft_id), "team_id": str(actor_team_id)},
    ).fetchone()
    if row is None:
        raise AuctionServiceError("This team has already passed or is not in this draft", 409)

    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "rfa_nominations_passed",
        team_id=str(actor_team_id),
        actor_type="team",
        actor_id=str(actor_team_id),
        metadata={"stage": "rfa_poaching"},
    )
    # If no one remains active, mark the draft completed.
    teams = _ordered_teams(session, str(draft_id))
    active = [t for t in teams if t["rfa_nominations_active"]]
    if not active:
        _set_draft_stage(session, str(draft_id), int(draft.league_id), COMPLETED_STAGE, 1, completed=True)
    return {"ok": True, "draft_complete": not active}


def resolve_rfa(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_team_id: str,
    decision: str,
) -> dict[str, Any]:
    """Controlling team matches or passes on a revealed RFA bid."""
    draft = _load_draft(session, draft_id)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "rfa_match_pending":
        raise AuctionServiceError("This nomination is not awaiting an RFA decision", 409)

    player = _load_player(session, str(draft_id), _seq_str(nomination.player_pool_id))
    controlling_team_id = _seq_str(player.controlling_team_id if player else None)
    if not controlling_team_id or controlling_team_id != actor_team_id:
        raise AuctionServiceError("Only the RFA controlling team may decide", 403)

    decision_enum = decision.strip().lower()
    if decision_enum not in ("match", "pass"):
        raise AuctionServiceError("Decision must be 'match' or 'pass'", 400)

    high_bid_team_id = _seq_str(nomination.high_bid_team_id) if nomination.high_bid_team_id else None
    high_bid = _int_amount(nomination.high_bid_amount)

    if not high_bid_team_id or high_bid <= 0:
        raise AuctionServiceError("This nomination has no positive winning bid", 409)

    # Record the decision.
    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_rfa_decisions (
              nomination_id, draft_id, league_id, controlling_team_id,
              high_bid_team_id, high_bid_amount, decision, decided_by
            ) VALUES (
              :nomination_id, :draft_id, :league_id, :controlling_team_id,
              :high_bid_team_id, :high_bid_amount, :decision, :decided_by
            )
            ON CONFLICT (nomination_id) DO UPDATE SET
              decision = EXCLUDED.decision,
              decided_by = EXCLUDED.decided_by,
              decided_at = NOW()
            """
        ),
        {
            "nomination_id": str(nomination_id),
            "draft_id": str(draft_id),
            "league_id": int(draft.league_id),
            "controlling_team_id": controlling_team_id,
            "high_bid_team_id": high_bid_team_id,
            "high_bid_amount": high_bid,
            "decision": decision_enum,
            "decided_by": str(actor_team_id),
        },
    )

    outcome = resolve_rfa_outcome(
        high_bid,
        controlling_team_id,
        high_bid_team_id,
        decision_enum,
    )
    winning_team_id = str(outcome.owner) if outcome.owner else controlling_team_id

    # Assign the winner and create the 3-year contract.
    contract = _finalize_nomination(
        session,
        nomination_id=str(nomination_id),
        draft_id=str(draft_id),
        league_id=int(draft.league_id),
        winning_team_id=winning_team_id,
        winning_bid=high_bid,
        outcome={
            "result": "rfa_" + decision_enum,
            "controlling_team_id": controlling_team_id,
            "high_bid_team_id": high_bid_team_id,
            "high_bid_amount": high_bid,
        },
    )
    teams = _ordered_teams(session, str(draft_id))
    _advance_or_transition(session, draft, teams)

    return {
        "ok": True,
        "result": "rfa_" + decision_enum,
        "nomination_id": str(nomination_id),
        "winner": winning_team_id,
        "winning_bid": high_bid,
        "contract": contract,
    }


__all__ = [
    "AuctionServiceError",
    "activate_draft",
    "nominate_player",
    "submit_bid",
    "replace_bid",
    "cancel_bid",
    "reveal_nomination",
    "pass_remaining_nominations",
    "resolve_rfa",
]