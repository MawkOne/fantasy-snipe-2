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
    "tie_break_bidding",
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

    # The CBS roster schema requires a non-null cbs_player_id. Pool rows imported
    # from projections may lack one, so synthesize a stable key and ensure the
    # linked cbs_players row exists for the foreign key.
    if not cbs_player_id:
        cbs_player_id = "uhhp-auction-" + str(nomination_id)[:12]
        try:
            session.execute(
                text(
                    """
                    INSERT INTO cbs_players (cbs_player_id, full_name, pos_primary)
                    VALUES (:cid, :full_name, :pos)
                    ON CONFLICT (cbs_player_id) DO NOTHING
                    """
                ),
                {"cid": cbs_player_id, "full_name": player_name, "pos": position},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Placeholder cbs_players insert failed: %s", type(exc).__name__)

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


def pause_draft(session: Any, draft_id: str, *, actor_role: str) -> dict[str, Any]:
    """Pause an active draft. Commissioner only; blocks nominations and bids."""
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can pause the draft", 403)
    draft = _load_draft(session, draft_id)
    if draft.status != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Only an active draft can be paused", 409)
    session.execute(
        text(
            """
            UPDATE uhhp_auction_drafts
               SET status = 'paused', version = version + 1, updated_at = NOW()
             WHERE id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "draft_paused",
        actor_type="user",
        actor_id=str(actor_role),
    )
    return {"ok": True, "status": "paused"}


def void_nomination(session: Any, draft_id: str, nomination_id: str, *, actor_role: str) -> dict[str, Any]:
    """Void a nomination that hasn't been revealed yet. Commissioner only."""
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can void a nomination", 403)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status not in ("awaiting_nomination", "sealed_bidding"):
        raise AuctionServiceError(
            "Can only void nominations that have not been revealed", 409
        )
    session.execute(
        text(
            """
            UPDATE uhhp_auction_nominations
               SET status = 'void', version = version + 1, updated_at = NOW()
             WHERE id = :nomination_id
            """
        ),
        {"nomination_id": str(nomination_id)},
    )
    _append_event(
        session,
        str(draft_id),
        int(nomination.league_id),
        "nomination_voided",
        nomination_id=str(nomination_id),
        actor_type="user",
        actor_id=str(actor_role),
    )
    return {"ok": True, "status": "voided"}


def reset_draft(session: Any, draft_id: str, *, actor_role: str) -> dict[str, Any]:
    """Wipe all test auction data and reset the draft to its initial setup state.

    Commissioner only. Removes all nominations, bids, events, contracts, and
    restores the draft status/teams to "setup" / fresh tie-break order.
    """
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can reset the draft", 403)
    draft = _load_draft(session, draft_id)
    if str(draft.status) == "setup":
        raise AuctionServiceError("Draft is already in initial state", 409)

    # The bid/event tables use append-only triggers; disable for this transaction.
    session.execute(text("SET LOCAL session_replication_role = replica"))

    # Order matters for FK constraints.
    session.execute(
        text("DELETE FROM uhhp_auction_tiebreak_bids WHERE draft_id = :draft_id"),
        {"draft_id": str(draft_id)},
    )
    session.execute(
        text(
            """
            DELETE FROM uhhp_auction_tie_audits
             WHERE nomination_id IN (SELECT id FROM uhhp_auction_nominations WHERE draft_id = :draft_id)
            """
        ),
        {"draft_id": str(draft_id)},
    )
    session.execute(
        text(
            """
            DELETE FROM uhhp_auction_rfa_decisions
             WHERE nomination_id IN (SELECT id FROM uhhp_auction_nominations WHERE draft_id = :draft_id)
            """
        ),
        {"draft_id": str(draft_id)},
    )
    session.execute(
        text("DELETE FROM uhhp_auction_events WHERE draft_id = :draft_id"),
        {"draft_id": str(draft_id)},
    )
    session.execute(
        text("DELETE FROM uhhp_auction_bid_events WHERE draft_id = :draft_id"),
        {"draft_id": str(draft_id)},
    )
    # Remove auction-created synthetic player rows; FK cascade removes roster contracts.
    session.execute(
        text(
            "DELETE FROM cbs_players WHERE cbs_player_id LIKE 'uhhp-auction-%%'"
        ),
    )
    session.execute(
        text("DELETE FROM uhhp_auction_nominations WHERE draft_id = :draft_id"),
        {"draft_id": str(draft_id)},
    )
    # Reset each team's tie-break priority to its nomination order (1-to-1).
    session.execute(
        text(
            """
            UPDATE uhhp_auction_draft_teams
               SET tie_break_priority = nomination_order,
                   rfa_nominations_active = TRUE,
                   rfa_nominations_passed_at = NULL,
                   updated_at = NOW()
             WHERE draft_id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    )
    _append_event(
        session, str(draft_id), int(draft.league_id),
        "draft_reset", actor_type="user", actor_id=str(actor_role),
    )
    return {"ok": True, "status": "setup"}
def resume_draft(session: Any, draft_id: str, *, actor_role: str) -> dict[str, Any]:
    """Resume a paused draft. Commissioner only."""
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can resume the draft", 403)
    draft = _load_draft(session, draft_id)
    if draft.status != "paused":
        raise AuctionServiceError("Only a paused draft can be resumed", 409)
    session.execute(
        text(
            """
            UPDATE uhhp_auction_drafts
               SET status = 'active', version = version + 1, updated_at = NOW()
             WHERE id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    )
    _append_event(
        session,
        str(draft_id),
        int(draft.league_id),
        "draft_resumed",
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
    """Open a sealed-bid auction for a player. Current nominator (or commissioner) only."""
    draft = _load_draft(session, draft_id)
    if draft.status != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
    if draft.stage == COMPLETED_STAGE:
        raise AuctionServiceError("Draft is completed", 409)

    current = _current_nominator(session, draft)
    if not (current is not None and current["team_id"] == actor_team_id):
        if actor_role not in ("admin", "commissioner"):
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
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
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
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
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
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
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


def _rotate_priority_winner(
    session: Any,
    draft_id: str,
    league_id: int,
    nomination_id: str,
    winner: str,
    *,
    tied_teams: Sequence[str],
    order_before: Sequence[str],
    audit_amount: Optional[int],
) -> None:
    """Move the winner to the bottom of the tie-break order and persist it.

    The winner always moves to the last position. A tie-audit row is written
    only when an actual tie was resolved (>= 2 tied teams).
    """
    order_after = [t for t in order_before if t != winner] + [winner]
    if audit_amount is not None and len(tied_teams) >= 2 and winner in tied_teams:
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
                "league_id": int(league_id),
                "tied_amount": int(audit_amount),
                "tied_team_ids": list(tied_teams),
                "winning_team_id": str(winner),
                "old_order": list(order_before),
                "new_order": order_after,
            },
        )
    # Two-phase update so the unique (draft_id, tie_break_priority) index is
    # never transiently violated while teams swap priorities.
    session.execute(
        text(
            """
            UPDATE uhhp_auction_draft_teams
               SET tie_break_priority = tie_break_priority + 1000,
                   updated_at = NOW()
             WHERE draft_id = :draft_id
            """
        ),
        {"draft_id": str(draft_id)},
    )
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


def _resolve_tie_break_round(
    session: Any,
    draft: Any,
    nomination: Any,
    teams: List[Dict[str, Any]],
    tie_order: Sequence[str],
) -> dict[str, Any]:
    """Second reveal: resolve the tie-break re-bid round.

    The highest re-bid above the tied amount wins; if nobody raised, the
    rotating tie-break order decides among the tied teams. The winner always
    moves to the bottom of the order.
    """
    draft_id = str(draft.id)
    nomination_id = str(nomination.id)
    outcome = nomination.outcome or {}
    tb = outcome.get("tie_break") or {}
    tie_amount = int(tb.get("amount") or 0)
    tied_ids = [str(t) for t in (tb.get("team_ids") or [])]
    if tie_amount <= 0 or len(tied_ids) < 2:
        raise AuctionServiceError("Tie-break state is inconsistent", 409)

    rows = session.execute(
        text(
            """
            SELECT team_id, amount
              FROM uhhp_auction_tiebreak_bids
             WHERE nomination_id = :nomination_id
            """
        ),
        {"nomination_id": nomination_id},
    ).fetchall()
    rebids = {str(r.team_id): int(r.amount) for r in rows}
    max_rebid = max(rebids.values()) if rebids else 0

    if max_rebid > tie_amount:
        leaders = [tid for tid in tied_ids if rebids.get(tid, 0) == max_rebid]
        winner = min(leaders, key=lambda t: tie_order.index(t))
        winning_bid = max_rebid
    else:
        winner = min(tied_ids, key=lambda t: tie_order.index(t))
        winning_bid = tie_amount

    _rotate_priority_winner(
        session,
        draft_id,
        int(draft.league_id),
        nomination_id,
        winner,
        tied_teams=tuple(tied_ids),
        order_before=list(tie_order),
        audit_amount=tie_amount,
    )

    player = _load_player(session, draft_id, _seq_str(nomination.player_pool_id))
    is_rfa = player is not None and str(player.eligibility) == "RFA"
    bids_payload = [
        {
            "team_id": tid,
            "effective_bid": rebids.get(tid),
            "responded": tid in rebids,
            "canceled": False,
        }
        for tid in tied_ids
    ]

    if is_rfa:
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
                "high_bid_team_id": str(winner),
                "high_bid_amount": int(winning_bid),
                "outcome": json.dumps(
                    {
                        "result": "rfa_match_pending",
                        "high_bid_team_id": str(winner),
                        "high_bid_amount": int(winning_bid),
                        "tie_break_applied": True,
                        "controlling_team_id": _seq_str(
                            player.controlling_team_id if player else None
                        ),
                    }
                ),
                "nomination_id": nomination_id,
            },
        )
        _append_event(
            session,
            draft_id,
            int(draft.league_id),
            "nomination_revealed",
            nomination_id=nomination_id,
            team_id=winner,
            metadata={"rfa_match_pending": True, "high_bid": int(winning_bid), "tie_break": True},
        )
        _advance_or_transition(session, draft, teams)
        return {
            "ok": True,
            "result": "rfa_match_pending",
            "nomination_id": nomination_id,
            "winner": None,
            "winning_bid": int(winning_bid),
            "status": "rfa_match_pending",
            "high_bid_team_id": winner,
            "tie_break": {"winner": winner, "amount": int(winning_bid), "tied_teams": tied_ids},
            "bids": bids_payload,
        }

    contract = _finalize_nomination(
        session,
        nomination_id=nomination_id,
        draft_id=draft_id,
        league_id=int(draft.league_id),
        winning_team_id=winner,
        winning_bid=int(winning_bid),
        outcome={"result": "sold", "revealed": True, "tie_break_applied": True},
    )
    _advance_or_transition(session, draft, teams)
    return {
        "ok": True,
        "result": "sold",
        "nomination_id": nomination_id,
        "winner": winner,
        "winning_bid": int(winning_bid),
        "status": "finalized",
        "contract": contract,
        "tie_break": {"winner": winner, "amount": int(winning_bid), "tied_teams": tied_ids},
        "bids": bids_payload,
    }


def submit_tiebreak_bid(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_team_id: str,
    amount: Any,
    idempotency_key: str,
) -> dict[str, Any]:
    """Submit (or replace) a tied team's one sealed re-bid."""
    draft = _load_draft(session, draft_id)
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
    nomination = _load_nomination(session, nomination_id)
    if nomination.status != "tie_break_bidding":
        raise AuctionServiceError("Tie-break round is not open", 409)
    tb = (nomination.outcome or {}).get("tie_break") or {}
    tied = [str(t) for t in (tb.get("team_ids") or [])]
    if actor_team_id not in tied:
        raise AuctionServiceError("Only teams in the tie may submit a tie-break bid", 403)
    try:
        validated = validate_bid(int(amount)) if isinstance(amount, (int, float, str)) else validate_bid(amount)
    except (BidValidationError, TypeError, ValueError) as exc:
        raise AuctionServiceError("Invalid bid amount: " + str(exc), 400) from exc
    session.execute(
        text(
            """
            INSERT INTO uhhp_auction_tiebreak_bids (
              nomination_id, draft_id, league_id, team_id, amount,
              idempotency_key, actor_id
            ) VALUES (
              :nomination_id, :draft_id, :league_id, :team_id, :amount,
              :idempotency_key, :actor_id
            )
            ON CONFLICT (nomination_id, team_id) DO UPDATE SET
              amount = EXCLUDED.amount,
              idempotency_key = EXCLUDED.idempotency_key,
              actor_id = EXCLUDED.actor_id,
              updated_at = NOW()
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
        "tiebreak_bid_submitted",
        nomination_id=str(nomination_id),
        team_id=str(actor_team_id),
        actor_type="team",
        actor_id=str(actor_team_id),
        idempotency_key=str(idempotency_key),
        metadata={"amount": validated},
    )
    return {"ok": True, "status": "submitted", "effective_bid": validated, "responded": True}
def reveal_nomination(
    session: Any,
    *,
    draft_id: str,
    nomination_id: str,
    actor_role: str,
    confirm_nonresponses: bool = False,
) -> dict[str, Any]:
    """Commissioner reveals sealed bids and resolves the auction.

    Phase 1 (sealed_bidding): if the top bids tie, the nomination enters a
    tie-break re-bid round; otherwise the winner is finalized immediately.
    Phase 2 (tie_break_bidding): the tie-break round is resolved - the
    highest raise wins, otherwise the rotating tie-break order decides.
    Every positive winner moves to the bottom of the tie-break order.
    """
    if actor_role not in ("admin", "commissioner"):
        raise AuctionServiceError("Only a commissioner can reveal", 403)
    draft = _load_draft(session, draft_id)
    if str(draft.status) not in (DRAFT_STATUS_ACTIVE, "paused"):
        raise AuctionServiceError("Draft is not active", 409)
    nomination = _load_nomination(session, nomination_id)

    teams = _ordered_teams(session, str(draft_id))
    tie_order = [t["team_id"] for t in sorted(teams, key=lambda t: t["tie_break_priority"])]

    # Phase 2: resolve the tie-break re-bid round.
    if nomination.status == "tie_break_bidding":
        return _resolve_tie_break_round(session, draft, nomination, teams, tie_order)

    if nomination.status != "sealed_bidding":
        raise AuctionServiceError("This nomination is not accepting reveal", 409)

    # Load each team's ordered bid events (Phase 1).
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

    # Per-team effective bids for the reveal display (all draft teams).
    bid_summary = session.execute(
        text(
            """
            SELECT team_id, effective_amount, responded, canceled
              FROM uhhp_auction_latest_effective_bids
             WHERE nomination_id = :nomination_id
             ORDER BY team_id
            """
        ),
        {"nomination_id": str(nomination_id)},
    ).fetchall()
    bids_payload = [
        {
            "team_id": str(row.team_id),
            "effective_bid": (
                int(row.effective_amount)
                if row.effective_amount is not None
                else None
            ),
            "responded": bool(row.responded),
            "canceled": bool(row.canceled),
        }
        for row in bid_summary
    ]

    # Record revealed amount / high bidder (viewer-safe API still hides until reveal).
    high_bid = int(result.winning_bid)
    high_bid_team = result.winner if high_bid > 0 else None

    # A positive tie starts the tie-break re-bid round; nothing concludes yet.
    if result.tie_was_resolved and result.winner is not None:
        tied_ids = [str(t) for t in result.audit.tie_break.tied_teams]
        # high_bid_amount/team stay NULL (the DB requires a team when amount
        # is non-zero); the tied amount lives in the outcome JSON instead.
        session.execute(
            text(
                """
                UPDATE uhhp_auction_nominations
                   SET status = 'tie_break_bidding', revealed_at = :revealed_at,
                       high_bid_team_id = NULL, high_bid_amount = NULL,
                       winning_team_id = NULL, winning_bid_amount = NULL,
                       outcome = CAST(:outcome AS JSONB),
                       version = version + 1, updated_at = NOW()
                 WHERE id = :nomination_id
                """
            ),
            {
                "revealed_at": _now(),
                "outcome": json.dumps({
                    "result": "tie_break_bidding",
                    "tie_break": {"amount": int(high_bid), "team_ids": tied_ids, "round": 1},
                }),
                "nomination_id": str(nomination_id),
            },
        )
        _append_event(
            session,
            str(draft_id),
            int(draft.league_id),
            "nomination_tie_break",
            nomination_id=str(nomination_id),
            metadata={"amount": int(high_bid), "team_ids": tied_ids},
        )
        return {
            "ok": True,
            "result": "tie_break_bidding",
            "nomination_id": str(nomination_id),
            "winner": None,
            "winning_bid": int(high_bid),
            "status": "tie_break_bidding",
            "tied_teams": tied_ids,
            "tied_amount": int(high_bid),
            "bids": bids_payload,
        }

    # Positive, no tie: conclude immediately; the winner moves to the bottom
    # of the tie-break order.
    _rotate_priority_winner(
        session,
        str(draft_id),
        int(draft.league_id),
        str(nomination_id),
        str(high_bid_team),
        tied_teams=(),
        order_before=list(tie_order),
        audit_amount=None,
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
            "bids": bids_payload,
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
            "bids": bids_payload,
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
        "bids": bids_payload,
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
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
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
    if str(draft.status) != DRAFT_STATUS_ACTIVE:
        raise AuctionServiceError("Draft is not active", 409)
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