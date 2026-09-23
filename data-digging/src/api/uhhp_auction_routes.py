"""Secure, viewer-safe API surface for the canonical UHHP 2026 silent auction."""

from __future__ import annotations

import logging
import uuid as uuid_mod
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from src.auction.service import (
    activate_draft,
    cancel_bid,
    nominate_player,
    pass_remaining_nominations,
    pause_draft,
    replace_bid,
    resolve_rfa,
    resume_draft,
    reveal_nomination,
    submit_bid,
    submit_tiebreak_bid,
    void_nomination,
)
from src.database.fantasy_connection import get_fantasy_session

logger = logging.getLogger(__name__)

ACTIVE_NOMINATION_STATUSES = (
    "awaiting_nomination",
    "sealed_bidding",
    "tie_break_bidding",
    "revealed",
    "rfa_match_pending",
)
REVEALED_NOMINATION_STATUSES = (
    "tie_break_bidding",
    "revealed",
    "rfa_match_pending",
    "finalized",
    "no_sale",
)
COMMISSIONER_ROLES = {"admin", "commissioner"}


def _as_iso(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None else None


def _user_value(user: Any, field: str, default: Any = None) -> Any:
    if isinstance(user, dict):
        return user.get(field, default)
    return getattr(user, field, default)


def _schema_ready(session: Any) -> bool:
    row = session.execute(
        text("SELECT to_regclass('public.uhhp_auction_drafts') AS table_name")
    ).fetchone()
    return bool(row and row.table_name)


def _resolve_membership(session: Any, league_id: int, user: Any) -> Dict[str, Any]:
    subject = str(_user_value(user, "external_auth_id", "") or "").strip()
    email = str(_user_value(user, "email", "") or "").strip().lower()
    global_role = str(_user_value(user, "role", "user") or "user").strip().lower()

    membership = None
    if subject or email:
        membership = session.execute(
            text(
                """
                SELECT team_id, COALESCE(role, 'member') AS role
                  FROM cbs_user_memberships
                 WHERE league_id = :league_id
                   AND (
                     (:subject <> '' AND user_subject = :subject)
                     OR (:email <> '' AND LOWER(COALESCE(user_email, '')) = :email)
                   )
                 ORDER BY CASE
                            WHEN LOWER(COALESCE(role, '')) IN ('admin', 'commissioner') THEN 0
                            ELSE 1
                          END,
                          id
                 LIMIT 1
                """
            ),
            {"league_id": league_id, "subject": subject, "email": email},
        ).fetchone()

    team_id = str(membership.team_id) if membership and membership.team_id else None
    membership_role = (
        str(membership.role or "member").lower() if membership else "member"
    )

    # The canonical GM directory is imported into cbs_owners/cbs_teams. This
    # fallback lets an invited GM be recognized by email before a membership
    # backfill is complete, without trusting any client-supplied team ID.
    if not team_id and email:
        owner_team = session.execute(
            text(
                """
                SELECT team.team_id
                  FROM cbs_teams AS team
                  JOIN cbs_owners AS owner ON owner.owner_id = team.owner_id
                 WHERE team.league_id = :league_id
                   AND LOWER(COALESCE(owner.email, '')) = :email
                   AND COALESCE(team.is_active, TRUE) = TRUE
                 ORDER BY team.created_at, team.team_id
                 LIMIT 1
                """
            ),
            {"league_id": league_id, "email": email},
        ).fetchone()
        if owner_team:
            team_id = str(owner_team.team_id)

    is_commissioner = (
        global_role in COMMISSIONER_ROLES or membership_role in COMMISSIONER_ROLES
    )
    if not team_id and not is_commissioner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No UHHP team membership is attached to this account",
        )

    return {
        "team_id": team_id,
        "role": "commissioner" if is_commissioner else membership_role,
        "is_commissioner": is_commissioner,
        "subject": subject,
        "email": email,
    }


def _serialize_team_bid(
    row: Any,
    *,
    viewer_team_id: Optional[str],
    amounts_revealed: bool,
) -> Dict[str, Any]:
    team_id = str(row.team_id)
    can_view_amount = amounts_revealed or (
        viewer_team_id is not None and team_id == viewer_team_id
    )
    response = {
        "team_id": team_id,
        "canonical_abbrev": str(row.canonical_abbrev),
        "team_name": str(row.team_name),
        "manager_name": str(row.manager_name),
        "responded": bool(row.responded),
        "canceled": bool(row.canceled),
        "latest_event_type": str(row.latest_event_type) if row.latest_event_type else None,
        "latest_event_at": _as_iso(row.latest_event_at),
    }
    if can_view_amount:
        response["effective_bid"] = int(row.effective_amount or 0)
        response["submitted_amount"] = (
            int(row.submitted_amount) if row.submitted_amount is not None else None
        )
    return response


def build_uhhp_auction_router(
    current_user_dependency: Callable[..., Any],
    broadcast: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    """Build the router without creating a circular import with ``main.py``.

    ``broadcast(slug, message)`` is an optional async WebSocket fan-out hook;
    the live room ignores it when not provided (e.g. in tests).
    """

    router = APIRouter(
        prefix="/api/cbs/league/{slug}/auction-2026",
        tags=["UHHP 2026 Auction"],
    )

    async def _emit(slug: str, event: str, **extra: Any) -> None:
        if broadcast is None:
            return
        try:
            await broadcast(slug, {"event": event, **extra})
        except Exception:
            logger.warning("WS broadcast failed for %s", event, exc_info=True)

    @router.get("/state", response_model=dict)
    async def get_viewer_safe_state(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Return auction state with sealed amounts redacted before reveal."""

        with get_fantasy_session() as session:
            if not _schema_ready(session):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="UHHP auction schema is not installed",
                )

            league = session.execute(
                text(
                    """
                    SELECT id, provider_slug, name
                      FROM cbs_leagues
                     WHERE provider_slug = :slug
                     LIMIT 1
                    """
                ),
                {"slug": slug},
            ).fetchone()
            if not league:
                raise HTTPException(status_code=404, detail="League not found")

            membership = _resolve_membership(session, int(league.id), current_user)
            draft = session.execute(
                text(
                    """
                    SELECT id, league_id, draft_year, rules_version, status, stage,
                           stage_round, nomination_cursor, version, metadata,
                           started_at, completed_at, created_at, updated_at
                      FROM uhhp_auction_drafts
                     WHERE league_id = :league_id AND draft_year = :draft_year
                     LIMIT 1
                    """
                ),
                {"league_id": int(league.id), "draft_year": int(draft_year)},
            ).fetchone()
            if not draft:
                raise HTTPException(
                    status_code=404,
                    detail="UHHP auction draft has not been initialized for this year",
                )

            teams = session.execute(
                text(
                    """
                    SELECT draft_team.team_id,
                           team.team_name,
                           draft_team.canonical_abbrev,
                           draft_team.manager_name,
                           team.logo_url,
                           draft_team.nomination_order,
                           draft_team.tie_break_priority,
                           draft_team.rfa_nominations_active,
                           draft_team.rfa_nominations_passed_at
                      FROM uhhp_auction_draft_teams AS draft_team
                      JOIN cbs_teams AS team
                        ON team.league_id = draft_team.league_id
                       AND team.team_id = draft_team.team_id
                     WHERE draft_team.draft_id = :draft_id
                     ORDER BY draft_team.nomination_order
                    """
                ),
                {"draft_id": draft.id},
            ).fetchall()

            active_nomination = session.execute(
                text(
                    """
                    SELECT nomination.id, nomination.status, nomination.stage,
                           nomination.stage_round, nomination.sequence_no,
                           nomination.nominator_team_id, nomination.player_pool_id,
                           nomination.player_snapshot, nomination.high_bid_team_id,
                           nomination.high_bid_amount, nomination.winning_team_id,
                           nomination.winning_bid_amount, nomination.contract_years,
                           nomination.outcome, nomination.version,
                           nomination.nominated_at, nomination.bidding_opened_at,
                           nomination.revealed_at, nomination.finalized_at,
                           pool.player_name, pool.positions, pool.nhl_team_abbrev,
                           pool.eligibility, pool.controlling_team_id,
                           pool.projected_fantasy_points
                      FROM uhhp_auction_nominations AS nomination
                      LEFT JOIN uhhp_auction_player_pool AS pool
                        ON pool.id = nomination.player_pool_id
                     WHERE nomination.draft_id = :draft_id
                       AND nomination.status IN (
                         'awaiting_nomination',
                         'sealed_bidding',
                         'revealed',
                         'rfa_match_pending'
                       )
                     ORDER BY nomination.created_at DESC
                     LIMIT 1
                    """
                ),
                {"draft_id": draft.id},
            ).fetchone()

            cap_rows = session.execute(
                text(
                    """
                    SELECT metadata ->> 'roster_team_id' AS team_id,
                           COALESCE(SUM(salary) FILTER (
                             WHERE eligibility IN ('PROTECTED', 'CAP_HIT')
                           ), 0) AS committed_salary,
                           COUNT(*) FILTER (WHERE eligibility = 'PROTECTED') AS protected_count,
                           COUNT(*) FILTER (WHERE eligibility = 'RFA') AS rfa_count,
                           COUNT(*) FILTER (WHERE eligibility = 'UFA') AS expired_ufa_count,
                           COUNT(*) FILTER (WHERE eligibility = 'REVIEW') AS review_count
                      FROM uhhp_auction_player_pool
                     WHERE draft_id = :draft_id
                       AND metadata ? 'roster_team_id'
                       AND COALESCE(metadata ->> 'roster_team_id', '') <> ''
                     GROUP BY metadata ->> 'roster_team_id'
                    """
                ),
                {"draft_id": draft.id},
            ).fetchall()
            cap_by_team = {str(row.team_id): row for row in cap_rows}

            team_rows = []
            for team in teams:
                team_id = str(team.team_id)
                cap = cap_by_team.get(team_id)
                committed_salary = int(cap.committed_salary or 0) if cap else 0
                team_rows.append({
                    "team_id": team_id,
                    "team_name": str(team.team_name),
                    "canonical_abbrev": str(team.canonical_abbrev),
                    "manager_name": str(team.manager_name),
                    "logo_url": str(team.logo_url) if team.logo_url else None,
                    "nomination_order": int(team.nomination_order),
                    "tie_break_priority": int(team.tie_break_priority),
                    "rfa_nominations_active": bool(team.rfa_nominations_active),
                    "rfa_nominations_passed_at": _as_iso(
                        team.rfa_nominations_passed_at
                    ),
                    "cap": {
                        "salary_cap": 100,
                        "committed_salary": committed_salary,
                        "cap_space": 100 - committed_salary,
                        "over_cap": committed_salary > 100,
                    },
                    "roster_summary": {
                        "protected": int(cap.protected_count or 0) if cap else 0,
                        "rfa": int(cap.rfa_count or 0) if cap else 0,
                        "expired_ufa": int(cap.expired_ufa_count or 0) if cap else 0,
                        "review": int(cap.review_count or 0) if cap else 0,
                    },
                })

            current_nominator = None
            active_nomination_teams = [
                team for team in team_rows
                if draft.stage != "rfa_poaching" or team["rfa_nominations_active"]
            ]
            if active_nomination_teams:
                cursor = int(draft.nomination_cursor) % len(active_nomination_teams)
                current_nominator = active_nomination_teams[cursor]

            nomination_payload = None
            bid_responses = []
            amounts_revealed = False
            if active_nomination:
                amounts_revealed = active_nomination.status in REVEALED_NOMINATION_STATUSES
                bid_rows = session.execute(
                    text(
                        """
                        SELECT effective.team_id, effective.canonical_abbrev,
                               team.team_name, draft_team.manager_name,
                               effective.responded, effective.canceled,
                               effective.latest_event_type, effective.latest_event_at,
                               effective.effective_amount, effective.submitted_amount
                          FROM uhhp_auction_latest_effective_bids AS effective
                          JOIN cbs_teams AS team
                            ON team.league_id = effective.league_id
                           AND team.team_id = effective.team_id
                          JOIN uhhp_auction_draft_teams AS draft_team
                            ON draft_team.draft_id = effective.draft_id
                           AND draft_team.league_id = effective.league_id
                           AND draft_team.team_id = effective.team_id
                         WHERE effective.nomination_id = :nomination_id
                         ORDER BY draft_team.nomination_order
                        """
                    ),
                    {"nomination_id": active_nomination.id},
                ).fetchall()
                bid_responses = [
                    _serialize_team_bid(
                        bid,
                        viewer_team_id=membership["team_id"],
                        amounts_revealed=amounts_revealed,
                    )
                    for bid in bid_rows
                ]

                nomination_payload = {
                    "id": str(active_nomination.id),
                    "status": str(active_nomination.status),
                    "stage": str(active_nomination.stage),
                    "stage_round": int(active_nomination.stage_round),
                    "sequence_no": int(active_nomination.sequence_no),
                    "nominator_team_id": str(active_nomination.nominator_team_id),
                    "version": int(active_nomination.version),
                    "nominated_at": _as_iso(active_nomination.nominated_at),
                    "bidding_opened_at": _as_iso(
                        active_nomination.bidding_opened_at
                    ),
                    "revealed_at": _as_iso(active_nomination.revealed_at),
                    "finalized_at": _as_iso(active_nomination.finalized_at),
                    "amounts_revealed": amounts_revealed,
                    "player": {
                        "pool_id": (
                            str(active_nomination.player_pool_id)
                            if active_nomination.player_pool_id
                            else None
                        ),
                        "name": active_nomination.player_name,
                        "positions": list(active_nomination.positions or []),
                        "nhl_team": active_nomination.nhl_team_abbrev,
                        "eligibility": active_nomination.eligibility,
                        "controlling_team_id": active_nomination.controlling_team_id,
                        "projected_fantasy_points": (
                            float(active_nomination.projected_fantasy_points)
                            if active_nomination.projected_fantasy_points is not None
                            else None
                        ),
                        "snapshot": active_nomination.player_snapshot or {},
                    },
                    "result": (
                        {
                            "high_bid_team_id": active_nomination.high_bid_team_id,
                            "high_bid_amount": (
                                int(active_nomination.high_bid_amount or 0)
                            ),
                            "winning_team_id": active_nomination.winning_team_id,
                            "winning_bid_amount": (
                                int(active_nomination.winning_bid_amount or 0)
                            ),
                            "contract_years": active_nomination.contract_years,
                            "outcome": active_nomination.outcome or {},
                        }
                        if amounts_revealed
                        else None
                    ),
                    "responses": bid_responses,
                    "response_count": sum(
                        1 for response in bid_responses if response["responded"]
                    ),
                    "team_count": len(bid_responses),
                    "tie_break": (
                        {
                            "tied_team_ids": list(
                                ((active_nomination.outcome or {}).get("tie_break") or {}).get("team_ids") or []
                            ),
                            "amount": int(
                                ((active_nomination.outcome or {}).get("tie_break") or {}).get("amount") or 0
                            ),
                        }
                        if active_nomination.status == "tie_break_bidding"
                        else None
                    ),
                }

            viewer_team_id = membership["team_id"]
            can_nominate = bool(
                viewer_team_id
                and current_nominator
                and viewer_team_id == current_nominator["team_id"]
                and not active_nomination
                and draft.status == "active"
                and draft.stage != "completed"
            )
            can_reveal = bool(
                membership["is_commissioner"]
                and active_nomination
                and active_nomination.status in ("sealed_bidding", "tie_break_bidding")
            )
            can_decide_rfa = bool(
                viewer_team_id
                and active_nomination
                and active_nomination.status == "rfa_match_pending"
                and str(active_nomination.controlling_team_id or "")
                == viewer_team_id
            )

            return {
                "league": {
                    "id": int(league.id),
                    "slug": str(league.provider_slug),
                    "name": str(league.name),
                },
                "draft": {
                    "id": str(draft.id),
                    "draft_year": int(draft.draft_year),
                    "rules_version": str(draft.rules_version),
                    "status": str(draft.status),
                    "stage": str(draft.stage),
                    "stage_round": int(draft.stage_round),
                    "nomination_cursor": int(draft.nomination_cursor),
                    "version": int(draft.version),
                    "started_at": _as_iso(draft.started_at),
                    "completed_at": _as_iso(draft.completed_at),
                    "updated_at": _as_iso(draft.updated_at),
                },
                "viewer": {
                    "team_id": viewer_team_id,
                    "role": membership["role"],
                    "is_commissioner": membership["is_commissioner"],
                },
                "current_nominator": current_nominator,
                "teams": team_rows,
                "active_nomination": nomination_payload,
                "actions": {
                    "can_nominate": can_nominate,
                    "can_reveal": can_reveal,
                    "can_decide_rfa": can_decide_rfa,
                },
            }

    @router.get("/players", response_model=dict)
    async def list_auction_players(
        slug: str,
        draft_year: int = 2026,
        eligibility: str = "stage",
        position: str = "",
        query: str = "",
        limit: int = 300,
        offset: int = 0,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """List the authenticated viewer's stage-eligible auction player pool."""

        requested_eligibility = eligibility.strip().upper()
        requested_position = position.strip().upper()
        if requested_position in {"LW", "RW"}:
            requested_position = "W"
        if requested_position and requested_position not in {"C", "W", "F", "D", "G"}:
            raise HTTPException(status_code=400, detail="Invalid position filter")
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        with get_fantasy_session() as session:
            if not _schema_ready(session):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="UHHP auction schema is not installed",
                )
            league = session.execute(
                text("SELECT id, provider_slug FROM cbs_leagues WHERE provider_slug = :slug LIMIT 1"),
                {"slug": slug},
            ).fetchone()
            if not league:
                raise HTTPException(status_code=404, detail="League not found")
            membership = _resolve_membership(session, int(league.id), current_user)
            draft = session.execute(
                text(
                    """
                    SELECT id, stage, stage_round, status
                      FROM uhhp_auction_drafts
                     WHERE league_id = :league_id AND draft_year = :draft_year
                     LIMIT 1
                    """
                ),
                {"league_id": int(league.id), "draft_year": int(draft_year)},
            ).fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Auction draft not initialized")

            if requested_eligibility in {"", "STAGE"}:
                allowed = (
                    ("UFA", "RFA")
                    if draft.stage == "superstar"
                    else (("RFA",) if draft.stage == "rfa_poaching" else ("UFA",))
                )
            elif requested_eligibility == "AVAILABLE":
                allowed = ("UFA", "RFA")
            elif requested_eligibility in {"UFA", "RFA"}:
                allowed = (requested_eligibility,)
            elif requested_eligibility == "ALL" and membership["is_commissioner"]:
                allowed = (
                    "PROTECTED", "RFA", "UFA", "ROOKIE", "ASSET", "CAP_HIT", "REVIEW"
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid eligibility filter")

            params: Dict[str, Any] = {
                "draft_id": draft.id,
                "query": f"%{query.strip()}%",
                "position": requested_position,
                "limit": limit,
                "offset": offset,
            }
            eligibility_names = []
            for index, value in enumerate(allowed):
                name = f"eligibility_{index}"
                params[name] = value
                eligibility_names.append(f":{name}")
            eligibility_sql = ", ".join(eligibility_names)

            rows = session.execute(
                text(
                    f"""
                    SELECT pool.id, pool.cbs_player_id, pool.nhl_player_id,
                           pool.player_name, pool.positions, pool.nhl_team_abbrev,
                           pool.birthdate, pool.age_at_cutoff, pool.eligibility,
                           pool.controlling_team_id, controller.team_name AS controlling_team_name,
                           controller.abbrev AS controlling_team_abbrev,
                           pool.projected_fantasy_points, pool.projection,
                           pool.source_availability,
                           COUNT(*) OVER() AS total_count
                      FROM uhhp_auction_player_pool AS pool
                      LEFT JOIN cbs_teams AS controller
                        ON controller.league_id = pool.league_id
                       AND controller.team_id = pool.controlling_team_id
                     WHERE pool.draft_id = :draft_id
                       AND pool.eligibility IN ({eligibility_sql})
                       AND (
                         :position = ''
                         OR :position = ANY(pool.positions)
                         OR (:position = 'F' AND pool.positions && ARRAY['C', 'W']::TEXT[])
                       )
                       AND (
                         :query = '%%'
                         OR pool.player_name ILIKE :query
                         OR COALESCE(pool.nhl_team_abbrev, '') ILIKE :query
                       )
                     ORDER BY pool.projected_fantasy_points DESC NULLS LAST,
                              pool.player_name
                     LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            ).fetchall()
            total = int(rows[0].total_count) if rows else 0
            players = [
                {
                    "id": str(row.id),
                    "cbs_player_id": row.cbs_player_id,
                    "nhl_player_id": row.nhl_player_id,
                    "name": str(row.player_name),
                    "positions": list(row.positions or []),
                    "nhl_team": row.nhl_team_abbrev,
                    "birthdate": _as_iso(row.birthdate),
                    "age_on_july_1": row.age_at_cutoff,
                    "eligibility": str(row.eligibility),
                    "controlling_team": (
                        {
                            "team_id": str(row.controlling_team_id),
                            "team_name": str(row.controlling_team_name),
                            "abbrev": row.controlling_team_abbrev,
                        }
                        if row.controlling_team_id
                        else None
                    ),
                    "projected_fantasy_points": (
                        float(row.projected_fantasy_points)
                        if row.projected_fantasy_points is not None
                        else None
                    ),
                    "projection": row.projection or {},
                    "source_availability": row.source_availability,
                }
                for row in rows
            ]
            return {
                "draft_id": str(draft.id),
                "stage": str(draft.stage),
                "stage_round": int(draft.stage_round),
                "eligibility": list(allowed),
                "total": total,
                "limit": limit,
                "offset": offset,
                "players": players,
            }

    @router.get("/history", response_model=dict)
    async def get_auction_history(
        slug: str,
        draft_year: int = 2026,
        limit: int = 50,
        offset: int = 0,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Return finalized auction results for the current draft."""
        with get_fantasy_session() as session:
            if not _schema_ready(session):
                raise HTTPException(503, "UHHP auction schema is not installed")
            league = session.execute(
                text(
                    "SELECT id, provider_slug, name FROM cbs_leagues WHERE provider_slug = :slug LIMIT 1"
                ),
                {"slug": slug},
            ).fetchone()
            if not league:
                raise HTTPException(404, "League not found")
            membership = _resolve_membership(session, int(league.id), current_user)
            draft = session.execute(
                text(
                    """
                    SELECT id, draft_year, stage, stage_round, status
                      FROM uhhp_auction_drafts
                     WHERE league_id = :league_id AND draft_year = :draft_year
                     LIMIT 1
                    """
                ),
                {"league_id": int(league.id), "draft_year": int(draft_year)},
            ).fetchone()
            if not draft:
                raise HTTPException(404, "Auction draft not initialized")

            limit = max(1, min(int(limit), 100))
            offset = max(0, int(offset))

            rows = session.execute(
                text(
                    """
                    SELECT nomination.id,
                           nomination.status,
                           nomination.nominator_team_id,
                           nominator.team_name AS nominator_team_name,
                           nomination.winning_team_id,
                           team.team_name AS winning_team_name,
                           team.abbrev AS winning_team_abbrev,
                           nomination.winning_bid_amount,
                           nomination.contract_years,
                           nomination.outcome,
                           pool.player_name,
                           pool.positions,
                           pool.nhl_team_abbrev,
                           tie.tied_amount,
                           tie.tied_team_ids,
                           tie.old_tie_break_order,
                           tie.new_tie_break_order,
                           nomination.nominated_at,
                           nomination.revealed_at,
                           nomination.finalized_at
                      FROM uhhp_auction_nominations AS nomination
                      LEFT JOIN uhhp_auction_player_pool AS pool
                        ON pool.id = nomination.player_pool_id
                      LEFT JOIN cbs_teams AS team
                        ON team.league_id = nomination.league_id
                       AND team.team_id = nomination.winning_team_id
                      LEFT JOIN cbs_teams AS nominator
                        ON nominator.league_id = nomination.league_id
                       AND nominator.team_id = nomination.nominator_team_id
                      LEFT JOIN uhhp_auction_tie_audits AS tie
                        ON tie.nomination_id = nomination.id
                     WHERE nomination.draft_id = :draft_id
                       AND nomination.status IN ('finalized', 'no_sale')
                     ORDER BY nomination.nominated_at ASC NULLS FIRST,
                              nomination.created_at ASC
                     LIMIT :limit OFFSET :offset
                    """
                ),
                {"draft_id": draft.id, "limit": limit, "offset": offset},
            ).fetchall()

            # Per-nomination, per-team effective bids for the ledger display.
            bid_rows = session.execute(
                text(
                    """
                    SELECT nomination_id, team_id, effective_amount, responded
                      FROM uhhp_auction_latest_effective_bids
                     WHERE draft_id = :draft_id
                    """
                ),
                {"draft_id": draft.id},
            ).fetchall()
            bids_by_nomination: Dict[str, list] = {}
            for b in bid_rows:
                bids_by_nomination.setdefault(str(b.nomination_id), []).append({
                    "team_id": str(b.team_id),
                    "bid": int(b.effective_amount) if b.effective_amount is not None else None,
                    "responded": bool(b.responded),
                })

            results = []
            for row in rows:
                result_entry: Dict[str, Any] = {
                    "status": str(row.status),
                    "nominator_team_id": row.nominator_team_id,
                    "nominator_team_name": row.nominator_team_name,
                    "winning_team_id": row.winning_team_id,
                    "winning_team_name": row.winning_team_name,
                    "winning_team_abbrev": row.winning_team_abbrev,
                    "winning_bid": float(row.winning_bid_amount) if row.winning_bid_amount is not None else None,
                    "contract_years": row.contract_years,
                    "player_name": row.player_name,
                    "positions": list(row.positions or []),
                    "nhl_team_abbrev": row.nhl_team_abbrev,
                    "tie_break": None,
                    "nominated_at": _as_iso(row.nominated_at),
                    "revealed_at": _as_iso(row.revealed_at),
                    "finalized_at": _as_iso(row.finalized_at),
                }
                if row.tied_amount is not None:
                    result_entry["tie_break"] = {
                        "tied_amount": int(row.tied_amount),
                        "tied_team_ids": list(row.tied_team_ids or []),
                        "old_order": list(row.old_tie_break_order or []),
                        "new_order": list(row.new_tie_break_order or []),
                    }
                # Per-team sealed bids for the ledger
                result_entry["bids"] = bids_by_nomination.get(str(row.id), [])
                results.append(result_entry)

            return {
                "draft_id": str(draft.id),
                "stage": str(draft.stage),
                "stage_round": int(draft.stage_round),
                "results": results,
                "total": len(results),
            }

    @router.get("/rosters", response_model=dict)
    async def get_team_rosters(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Return each league team's current CBS roster (My Team / Cap Summary).

        Rows come from ``cbs_rosters`` (the imported 2026 snapshot plus any
        auction-created contracts), enriched with positions, NHL team, birthdate
        and UFA/RFA eligibility from ``uhhp_auction_player_pool`` / ``cbs_players``.
        """

        with get_fantasy_session() as session:
            if not _schema_ready(session):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="UHHP auction schema is not installed",
                )

            league = session.execute(
                text(
                    "SELECT id, provider_slug, name FROM cbs_leagues WHERE provider_slug = :slug LIMIT 1"
                ),
                {"slug": slug},
            ).fetchone()
            if not league:
                raise HTTPException(status_code=404, detail="League not found")
            membership = _resolve_membership(session, int(league.id), current_user)

            draft = session.execute(
                text(
                    """
                    SELECT id, draft_year, stage, stage_round, status, rules_version
                      FROM uhhp_auction_drafts
                     WHERE league_id = :league_id AND draft_year = :draft_year
                     LIMIT 1
                    """
                ),
                {"league_id": int(league.id), "draft_year": int(draft_year)},
            ).fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Auction draft not initialized")

            team_rows = session.execute(
                text(
                    """
                    SELECT team.team_id, team.team_name, team.abbrev, team.logo_url,
                           owner.display_name AS manager_name,
                           draft_team.nomination_order
                      FROM cbs_teams AS team
                      LEFT JOIN cbs_owners AS owner
                        ON owner.owner_id = team.owner_id
                      LEFT JOIN uhhp_auction_draft_teams AS draft_team
                        ON draft_team.draft_id = :draft_id
                       AND draft_team.league_id = team.league_id
                       AND draft_team.team_id = team.team_id
                     WHERE team.league_id = :league_id
                       AND COALESCE(team.is_active, TRUE) = TRUE
                     ORDER BY draft_team.nomination_order NULLS LAST, team.team_name
                    """
                ),
                {"league_id": int(league.id), "draft_id": draft.id},
            ).fetchall()

            # The roster snapshot stores the CBS roster position in slot_type
            # (C/W/D/G) and CBS status ('active'/'reserve'/'injured'); auction
            # contracts use slot_type 'A' / status 'signed'. Dedupe on
            # (team, player), preferring auction rows then the newest snapshot.
            roster_rows = session.execute(
                text(
                    """
                    SELECT DISTINCT ON (roster.team_id, roster.cbs_player_id)
                           roster.team_id,
                           roster.cbs_player_id,
                           roster.nhl_player_id,
                           roster.slot_type,
                           roster.salary,
                           roster.years,
                           roster.rookie,
                           roster.roster_order,
                           roster.future_fa,
                           roster.status AS roster_status,
                           (roster.uhhp_auction_nomination_id IS NOT NULL) AS auction_contract,
                           pool.id AS pool_id,
                           COALESCE(player.full_name, pool.player_name, roster.cbs_player_id) AS player_name,
                           COALESCE(
                             pool.positions,
                             ARRAY[
                               NULLIF(player.pos_primary, '')
                             ]::TEXT[]
                           ) AS positions,
                           COALESCE(pool.nhl_team_abbrev, player.nhl_team_abbr) AS nhl_team_abbr,
                           COALESCE(pool.birthdate, player.birthdate) AS birthdate,
                           pool.eligibility AS pool_eligibility,
                           pool.projected_fantasy_points,
                           pool.projection ->> 'vorp' AS vorp,
                           pool.projection ->> 'vorp_salary' AS vorp_salary,
                           CASE
                             WHEN roster.years IN (1, 2, 3) THEN NULL
                             WHEN roster.rookie THEN 'RFA'
                             WHEN pool.eligibility IN ('UFA', 'RFA') THEN pool.eligibility
                             WHEN COALESCE(pool.birthdate, player.birthdate) IS NOT NULL THEN
                               CASE
                                 WHEN EXTRACT(YEAR FROM AGE(
                                   MAKE_DATE(:year, 7, 1),
                                   COALESCE(pool.birthdate, player.birthdate)
                                 )) >= 27 THEN 'UFA'
                                 ELSE 'RFA'
                               END
                             WHEN roster.uhhp_auction_nomination_id IS NOT NULL THEN NULL
                             ELSE 'REVIEW'
                           END AS status
                      FROM cbs_rosters AS roster
                      LEFT JOIN cbs_players AS player
                        ON player.cbs_player_id = roster.cbs_player_id
                      LEFT JOIN uhhp_auction_player_pool AS pool
                        ON pool.draft_id = :draft_id
                       AND pool.league_id = roster.league_id
                       AND pool.cbs_player_id = roster.cbs_player_id
                     WHERE roster.league_id = :league_id
                       AND (
                         roster.uhhp_auction_nomination_id IS NOT NULL
                         OR roster.status IN ('active', 'reserve', 'injured', 'signed')
                       )
                     ORDER BY roster.team_id, roster.cbs_player_id,
                              CASE WHEN roster.uhhp_auction_nomination_id IS NOT NULL THEN 0 ELSE 1 END,
                              roster.effective_from DESC NULLS LAST,
                              roster.id DESC
                    """
                ),
                {"league_id": int(league.id), "draft_id": draft.id, "year": int(draft_year)},
            ).fetchall()

            cap_rows = session.execute(
                text(
                    """
                    SELECT metadata ->> 'roster_team_id' AS team_id,
                           COALESCE(SUM(salary) FILTER (
                             WHERE eligibility IN ('PROTECTED', 'CAP_HIT')
                           ), 0) AS committed_salary,
                           COUNT(*) FILTER (WHERE eligibility = 'PROTECTED') AS protected_count,
                           COUNT(*) FILTER (WHERE eligibility = 'RFA') AS rfa_count,
                           COUNT(*) FILTER (WHERE eligibility = 'UFA') AS ufa_count,
                           COUNT(*) FILTER (WHERE eligibility = 'REVIEW') AS review_count
                      FROM uhhp_auction_player_pool
                     WHERE draft_id = :draft_id
                       AND metadata ? 'roster_team_id'
                       AND COALESCE(metadata ->> 'roster_team_id', '') <> ''
                     GROUP BY metadata ->> 'roster_team_id'
                    """
                ),
                {"draft_id": draft.id},
            ).fetchall()
            cap_by_team = {str(row.team_id): row for row in cap_rows}

            players_by_team: Dict[str, list] = {}
            for row in roster_rows:
                team_id = str(row.team_id)
                if team_id not in players_by_team:
                    players_by_team[team_id] = []
                positions = list(row.positions or [])
                primary_position = ""
                if positions:
                    primary_position = str(positions[0]).upper()
                if primary_position in {"LW", "RW"}:
                    primary_position = "W"
                players_by_team[team_id].append({
                    "pool_id": str(row.pool_id) if row.pool_id else None,
                    "cbs_player_id": str(row.cbs_player_id),
                    "nhl_player_id": row.nhl_player_id,
                    "player_name": str(row.player_name),
                    "position": primary_position,
                    "positions": positions,
                    "nhl_team_abbr": row.nhl_team_abbr,
                    "birthdate": _as_iso(row.birthdate),
                    "salary": float(row.salary) if row.salary is not None else None,
                    "years": row.years,
                    "rookie": bool(row.rookie) if row.rookie is not None else None,
                    "future_fa": row.future_fa,
                    "slot_type": row.slot_type,
                    "status": row.status,
                    "eligibility": row.pool_eligibility,
                    "projected_fantasy_points": (
                        float(row.projected_fantasy_points)
                        if row.projected_fantasy_points is not None
                        else None
                    ),
                    "vorp": float(row.vorp) if row.vorp is not None else None,
                    "vorp_salary": float(row.vorp_salary) if row.vorp_salary is not None else None,
                    "auction_contract": bool(row.auction_contract),
                })

            teams = []
            for team in team_rows:
                team_id = str(team.team_id)
                cap = cap_by_team.get(team_id)
                committed_salary = int(cap.committed_salary or 0) if cap else 0
                teams.append({
                    "team_id": team_id,
                    "team_name": str(team.team_name),
                    "abbrev": str(team.abbrev) if team.abbrev else None,
                    "logo_url": str(team.logo_url) if team.logo_url else None,
                    "manager_name": (
                        str(team.manager_name) if team.manager_name else None
                    ),
                    "nomination_order": (
                        int(team.nomination_order)
                        if team.nomination_order is not None
                        else None
                    ),
                    "cap": {
                        "salary_cap": 100,
                        "committed_salary": committed_salary,
                        "cap_space": max(0, 100 - committed_salary),
                    },
                    "roster_summary": {
                        "protected": int(cap.protected_count or 0) if cap else 0,
                        "rfa": int(cap.rfa_count or 0) if cap else 0,
                        "ufa": int(cap.ufa_count or 0) if cap else 0,
                        "review": int(cap.review_count or 0) if cap else 0,
                    },
                    "players": players_by_team.get(team_id, []),
                })

            return {
                "league": {
                    "id": int(league.id),
                    "slug": str(league.provider_slug),
                    "name": str(league.name),
                },
                "draft": {
                    "id": str(draft.id),
                    "draft_year": int(draft.draft_year),
                    "rules_version": str(draft.rules_version),
                    "stage": str(draft.stage),
                    "stage_round": int(draft.stage_round),
                    "status": str(draft.status),
                },
                "viewer": {
                    "team_id": membership["team_id"],
                    "role": membership["role"],
                    "is_commissioner": membership["is_commissioner"],
                },
                "teams": teams,
            }

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    @router.post("/activate", response_model=dict)
    async def activate_draft_endpoint(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Commissioner activates the draft for the season."""
        result = _run_mutation(slug, draft_year, current_user, lambda session, draft, membership: (
            activate_draft(session, str(draft.id), actor_role=membership["role"])
        ))
        await _emit(slug, "draft_activated")
        return result

    @router.post("/pause", response_model=dict)
    async def pause_draft_endpoint(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Commissioner pauses an active draft (blocks nominations and bids)."""
        result = _run_mutation(slug, draft_year, current_user, lambda session, draft, membership: (
            pause_draft(session, str(draft.id), actor_role=membership["role"])
        ))
        await _emit(slug, "draft_paused")
        return result

    @router.post("/resume", response_model=dict)
    async def resume_draft_endpoint(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Commissioner resumes a paused draft."""
        result = _run_mutation(slug, draft_year, current_user, lambda session, draft, membership: (
            resume_draft(session, str(draft.id), actor_role=membership["role"])
        ))
        await _emit(slug, "draft_resumed")
        return result

    @router.post("/nominate", response_model=dict)
    async def nominate_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        player_pool_id = str(_require_value(payload, "player_pool_id"))
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: nominate_player(
                session,
                draft_id=str(draft.id),
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                actor_role=membership["role"],
                player_pool_id=player_pool_id,
            ),
        )
        await _emit(slug, "auction_nominated", player_pool_id=player_pool_id)
        return result

    @router.post("/bids", response_model=dict)
    async def submit_bid_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        amount = payload.get("amount", 0)
        idempotency_key = str(payload.get("idempotency_key") or "")
        if not idempotency_key:
            idempotency_key = str(uuid_mod.uuid4().hex)
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: submit_bid(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                amount=amount,
                idempotency_key=idempotency_key,
            ),
        )
        await _emit(slug, "bid_placed", nomination_id=nomination_id)
        return result

    @router.post("/bids/replace", response_model=dict)
    async def replace_bid_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        amount = payload.get("amount", 0)
        idempotency_key = str(payload.get("idempotency_key") or "")
        if not idempotency_key:
            idempotency_key = str(uuid_mod.uuid4().hex)
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: replace_bid(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                amount=amount,
                idempotency_key=idempotency_key,
            ),
        )
        await _emit(slug, "bid_replaced", nomination_id=nomination_id)
        return result

    @router.post("/bids/tiebreak", response_model=dict)
    async def submit_tiebreak_bid_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        amount = payload.get("amount", 0)
        idempotency_key = str(payload.get("idempotency_key") or "")
        if not idempotency_key:
            idempotency_key = str(uuid_mod.uuid4().hex)
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: submit_tiebreak_bid(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                amount=amount,
                idempotency_key=idempotency_key,
            ),
        )
        await _emit(slug, "tiebreak_bid_placed", nomination_id=nomination_id)
        return result

    @router.post("/bids/cancel", response_model=dict)
    async def cancel_bid_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        idempotency_key = str(payload.get("idempotency_key") or "")
        if not idempotency_key:
            idempotency_key = str(uuid_mod.uuid4().hex)
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: cancel_bid(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                idempotency_key=idempotency_key,
            ),
        )
        await _emit(slug, "bid_cancelled", nomination_id=nomination_id)
        return result

    @router.post("/reveal", response_model=dict)
    async def reveal_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        confirm_nonresponses = bool(payload.get("confirm_nonresponses", False))
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: reveal_nomination(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_role=membership["role"],
                confirm_nonresponses=confirm_nonresponses,
            ),
        )
        await _emit(slug, "auction_revealed", nomination_id=nomination_id)
        return result

    @router.post("/void", response_model=dict)
    async def void_nomination_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        """Commissioner voids the current nomination entirely (mistake recovery)."""
        nomination_id = str(_require_value(payload, "nomination_id"))
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: void_nomination(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_role=membership["role"],
            ),
        )
        await _emit(slug, "nomination_voided", nomination_id=nomination_id)
        return result

    @router.post("/pass-remaining", response_model=dict)
    async def pass_remaining_endpoint(
        slug: str,
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        return _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: pass_remaining_nominations(
                session,
                draft_id=str(draft.id),
                actor_team_id=membership["team_id"],
            ),
        )

    @router.post("/rfa-decision", response_model=dict)
    async def rfa_decision_endpoint(
        slug: str,
        payload: Dict[str, Any],
        draft_year: int = 2026,
        current_user: Any = Depends(current_user_dependency),
    ) -> Dict[str, Any]:
        nomination_id = str(_require_value(payload, "nomination_id"))
        decision = str(_require_value(payload, "decision"))
        result = _run_mutation(
            slug, draft_year, current_user,
            lambda session, draft, membership: resolve_rfa(
                session,
                draft_id=str(draft.id),
                nomination_id=nomination_id,
                actor_team_id=_actor_team(membership, payload.get("team_id")),
                decision=decision,
            ),
        )
        await _emit(slug, "rfa_decided", nomination_id=nomination_id, decision=decision)
        return result

    return router


def _require_value(payload: Dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or str(value).strip() == "":
        raise HTTPException(status_code=400, detail=f"{key} is required")
    return value


def _actor_team(membership: Dict[str, Any], override: Any = None) -> str:
    """Resolve the acting team: commissioners may act on behalf of any team."""
    candidate = str(override or "").strip() if override is not None else ""
    if candidate and membership.get("is_commissioner"):
        return candidate
    return str(membership.get("team_id") or "")


def _run_mutation(slug: str, draft_year: int, current_user: Any, fn: Any) -> Dict[str, Any]:
    """Resolve league/draft/membership, then run a mutation handler."""
    from src.auction.service import AuctionServiceError
    with get_fantasy_session() as session:
        if not _schema_ready(session):
            raise HTTPException(status_code=503, detail="UHHP auction schema is not installed")
        league = session.execute(
            text("SELECT id FROM cbs_leagues WHERE provider_slug = :slug LIMIT 1"),
            {"slug": slug},
        ).fetchone()
        if not league:
            raise HTTPException(status_code=404, detail="League not found")
        draft = session.execute(
            text(
                """
                SELECT id, league_id, draft_year, status, stage, stage_round, version
                  FROM uhhp_auction_drafts
                 WHERE league_id = :league_id AND draft_year = :draft_year
                 LIMIT 1
                """
            ),
            {"league_id": int(league.id), "draft_year": int(draft_year)},
        ).fetchone()
        if not draft:
            raise HTTPException(status_code=404, detail="Auction draft not initialized")
        membership = _resolve_membership(session, int(league.id), current_user)
        try:
            return fn(session, draft, membership)
        except AuctionServiceError as exc:
            raise HTTPException(status_code=exc.http_status, detail=str(exc)) from exc
