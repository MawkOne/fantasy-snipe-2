"""Dependency-free UHHP auction domain rules for the canonical 2026 draft."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple, Union

DRAFT_YEAR = 2026
AGE_CUTOFF_MONTH = 7
AGE_CUTOFF_DAY = 1
RFA_MAX_AGE = 26
UFA_MIN_AGE = 27
MIN_POSITIVE_BID = 2
SALARY_CAP = 100
RFA_CONTRACT_YEARS = 3


class RosterStatus(str, Enum):
    """Auction-relevant classification for a roster entry."""

    PROTECTED = "PROTECTED"
    ROOKIE = "ROOKIE"
    ASSET = "ASSET"
    CAP_HIT = "CAP_HIT"
    RFA = "RFA"
    UFA = "UFA"
    REVIEW = "REVIEW"


RosterClassification = RosterStatus


class SpecialRosterEntry(str, Enum):
    """Non-player roster entries described by the canonical rules."""

    ASSET = "asset"
    CAP_HIT = "cap_hit"


def _validate_draft_year(draft_year: int) -> int:
    if isinstance(draft_year, bool) or not isinstance(draft_year, int):
        raise TypeError("draft_year must be an integer")
    if not 1 <= draft_year <= 9999:
        raise ValueError("draft_year must be between 1 and 9999")
    return draft_year


def age_on_cutoff(birthdate: date, draft_year: int = DRAFT_YEAR) -> int:
    """Return age on July 1 of ``draft_year`` using date-only arithmetic."""

    year = _validate_draft_year(draft_year)
    if not isinstance(birthdate, date) or isinstance(birthdate, datetime):
        raise TypeError("birthdate must be a datetime.date (not datetime)")

    cutoff = date(year, AGE_CUTOFF_MONTH, AGE_CUTOFF_DAY)
    if birthdate > cutoff:
        raise ValueError("birthdate cannot be after the draft-year cutoff")

    birthday_has_occurred = (birthdate.month, birthdate.day) <= (
        AGE_CUTOFF_MONTH,
        AGE_CUTOFF_DAY,
    )
    return year - birthdate.year - (0 if birthday_has_occurred else 1)


def _coerce_special_entry(
    special: Union[SpecialRosterEntry, str],
) -> SpecialRosterEntry:
    if isinstance(special, SpecialRosterEntry):
        return special
    if not isinstance(special, str):
        raise TypeError("special must be a SpecialRosterEntry or string")

    normalized = special.strip().lower().replace("-", "_")
    aliases = {
        "asset": SpecialRosterEntry.ASSET,
        "draft_pick": SpecialRosterEntry.ASSET,
        "draft_pick_placeholder": SpecialRosterEntry.ASSET,
        "cap_hit": SpecialRosterEntry.CAP_HIT,
        "cap_hit_placeholder": SpecialRosterEntry.CAP_HIT,
        "caphit": SpecialRosterEntry.CAP_HIT,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("special must identify an asset or cap-hit entry") from exc


def classify_roster_entry(
    years: int,
    birthdate: Optional[date] = None,
    draft_year: int = DRAFT_YEAR,
    *,
    rookie: bool = False,
    special: Optional[Union[SpecialRosterEntry, str]] = None,
) -> RosterStatus:
    """Classify a roster entry under the UHHP July 1 draft-year rules.

    Positive contract years are protected. For expired contracts, rookies and
    special placeholders are classified without requiring a birthdate; other
    players are RFA through age 26, UFA from age 27, or REVIEW when birthdate is
    unavailable.
    """

    if isinstance(years, bool) or not isinstance(years, int):
        raise TypeError("years must be an integer")
    if years < 0:
        raise ValueError("years cannot be negative")
    if not isinstance(rookie, bool):
        raise TypeError("rookie must be a boolean")
    _validate_draft_year(draft_year)
    special_entry = None if special is None else _coerce_special_entry(special)

    if years > 0:
        return RosterStatus.PROTECTED
    if rookie:
        return RosterStatus.ROOKIE
    if special_entry is SpecialRosterEntry.ASSET:
        return RosterStatus.ASSET
    if special_entry is SpecialRosterEntry.CAP_HIT:
        return RosterStatus.CAP_HIT
    if birthdate is None:
        return RosterStatus.REVIEW

    age = age_on_cutoff(birthdate, draft_year)
    if age <= RFA_MAX_AGE:
        return RosterStatus.RFA
    return RosterStatus.UFA


class BidValidationError(ValueError):
    """Raised when a value is not a legal UHHP sealed bid."""


def validate_bid(value: object) -> int:
    """Validate and return a bid: exactly an integer, either zero or at least 2."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise BidValidationError("bid must be an integer (booleans are not bids)")
    if value == 0 or value >= MIN_POSITIVE_BID:
        return value
    raise BidValidationError("bid must be zero or at least 2")


validate_bid_value = validate_bid


class BidEventType(str, Enum):
    SUBMIT = "submit"
    REPLACEMENT = "replacement"
    CANCEL = "cancel"


BidEventKind = BidEventType


def _coerce_bid_event_type(value: Union[BidEventType, str]) -> BidEventType:
    if isinstance(value, BidEventType):
        return value
    if not isinstance(value, str):
        raise TypeError("bid event kind must be a BidEventType or string")
    try:
        return BidEventType(value.strip().lower())
    except ValueError as exc:
        raise ValueError("unknown bid event kind: {!r}".format(value)) from exc


@dataclass(frozen=True)
class BidEvent:
    """One event in a team's ordered pre-reveal bid history."""

    kind: Union[BidEventType, str]
    amount: Optional[int] = None

    def __post_init__(self) -> None:
        kind = _coerce_bid_event_type(self.kind)
        object.__setattr__(self, "kind", kind)

        if kind is BidEventType.CANCEL:
            if self.amount is not None:
                raise BidValidationError("cancel events cannot include an amount")
            return
        if self.amount is None:
            raise BidValidationError("submit and replacement events require an amount")
        object.__setattr__(self, "amount", validate_bid(self.amount))

    @property
    def event_type(self) -> BidEventType:
        return self.kind  # type: ignore[return-value]

    @classmethod
    def submit(cls, amount: int) -> "BidEvent":
        return cls(BidEventType.SUBMIT, amount)

    @classmethod
    def replacement(cls, amount: int) -> "BidEvent":
        return cls(BidEventType.REPLACEMENT, amount)

    @classmethod
    def cancel(cls) -> "BidEvent":
        return cls(BidEventType.CANCEL)


def compute_effective_bid(events: Iterable[BidEvent]) -> int:
    """Fold ordered submit/replacement/cancel events into one effective bid."""

    effective = 0
    for event in events:
        if not isinstance(event, BidEvent):
            raise TypeError("events must contain BidEvent instances")
        if event.kind is BidEventType.CANCEL:
            effective = 0
        else:
            # BidEvent validates this invariant during construction.
            assert event.amount is not None
            effective = event.amount
    return effective


effective_bid = compute_effective_bid


class BidResponseStatus(str, Enum):
    NON_RESPONSE = "non_response"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class RevealStatus(str, Enum):
    NO_SALE = "no_sale"
    SOLD = "sold"
    AWARDED = "sold"


@dataclass(frozen=True)
class TeamBidAudit:
    team_id: str
    response_status: BidResponseStatus
    effective_bid: int
    events: Tuple[BidEvent, ...]

    @property
    def responded(self) -> bool:
        return self.response_status is not BidResponseStatus.NON_RESPONSE

    @property
    def last_event(self) -> Optional[BidEventType]:
        return None if not self.events else self.events[-1].event_type


@dataclass(frozen=True)
class TieBreakAudit:
    applied: bool
    highest_bid: int
    tied_teams: Tuple[str, ...]
    order_before: Tuple[str, ...]
    order_after: Tuple[str, ...]
    winner: Optional[str]


@dataclass(frozen=True)
class RevealAudit:
    team_bids: Tuple[TeamBidAudit, ...]
    tie_break: TieBreakAudit

    def for_team(self, team_id: str) -> TeamBidAudit:
        for team_bid in self.team_bids:
            if team_bid.team_id == team_id:
                return team_bid
        raise KeyError(team_id)


@dataclass(frozen=True)
class RevealResult:
    status: RevealStatus
    winner: Optional[str]
    winning_bid: int
    audit: RevealAudit

    @property
    def effective_bids(self) -> Dict[str, int]:
        return {
            team_bid.team_id: team_bid.effective_bid
            for team_bid in self.audit.team_bids
        }

    @property
    def tie_order(self) -> Tuple[str, ...]:
        return self.audit.tie_break.order_after

    @property
    def updated_tie_order(self) -> Tuple[str, ...]:
        return self.audit.tie_break.order_after

    @property
    def tie_was_resolved(self) -> bool:
        return self.audit.tie_break.applied


def _validate_team_id(team_id: object, field_name: str) -> str:
    if not isinstance(team_id, str) or not team_id.strip():
        raise ValueError("{} must contain non-empty string team IDs".format(field_name))
    return team_id


def resolve_reveal(
    events_by_team: Mapping[str, Optional[Iterable[BidEvent]]],
    tie_order: Sequence[str],
) -> RevealResult:
    """Reveal effective bids and resolve a positive tie by rotating priority.

    ``tie_order`` is also the complete set of participating teams. A missing
    team, an explicit ``None``, or an empty event history is a nonresponse and
    therefore has an effective bid of zero. The winner of a positive high-bid
    tie is the earliest tied team in ``tie_order`` and is moved to its bottom.
    """

    if not isinstance(events_by_team, Mapping):
        raise TypeError("events_by_team must be a mapping")
    if isinstance(tie_order, (str, bytes)):
        raise TypeError("tie_order must be a sequence of team IDs")

    order = tuple(_validate_team_id(team, "tie_order") for team in tie_order)
    if not order:
        raise ValueError("tie_order cannot be empty")
    if len(set(order)) != len(order):
        raise ValueError("tie_order cannot contain duplicate teams")

    supplied_teams = tuple(
        _validate_team_id(team, "events_by_team") for team in events_by_team
    )
    unknown_teams = set(supplied_teams).difference(order)
    if unknown_teams:
        raise ValueError(
            "events supplied for teams outside tie_order: {}".format(
                ", ".join(sorted(unknown_teams))
            )
        )

    team_audits = []
    for team in order:
        raw_events = events_by_team.get(team)
        events = () if raw_events is None else tuple(raw_events)
        if not events:
            response_status = BidResponseStatus.NON_RESPONSE
            effective = 0
        else:
            effective = compute_effective_bid(events)
            response_status = (
                BidResponseStatus.CANCELLED
                if events[-1].kind is BidEventType.CANCEL
                else BidResponseStatus.SUBMITTED
            )
        team_audits.append(
            TeamBidAudit(
                team_id=team,
                response_status=response_status,
                effective_bid=effective,
                events=events,
            )
        )

    highest_bid = max(team_bid.effective_bid for team_bid in team_audits)
    order_after = order
    tied_teams: Tuple[str, ...] = ()
    tie_winner: Optional[str] = None
    tie_applied = False

    if highest_bid == 0:
        status = RevealStatus.NO_SALE
        winner = None
    else:
        high_teams = tuple(
            team_bid.team_id
            for team_bid in team_audits
            if team_bid.effective_bid == highest_bid
        )
        winner = high_teams[0]
        status = RevealStatus.SOLD
        if len(high_teams) > 1:
            tie_applied = True
            tied_teams = high_teams
            tie_winner = winner
            order_after = tuple(team for team in order if team != winner) + (winner,)

    tie_audit = TieBreakAudit(
        applied=tie_applied,
        highest_bid=highest_bid,
        tied_teams=tied_teams,
        order_before=order,
        order_after=order_after,
        winner=tie_winner,
    )
    return RevealResult(
        status=status,
        winner=winner,
        winning_bid=highest_bid,
        audit=RevealAudit(tuple(team_audits), tie_audit),
    )


class RFADecision(str, Enum):
    MATCH = "match"
    PASS = "pass"


class RFAStatus(str, Enum):
    NO_SALE = "no_sale"
    PENDING = "rfa_match_pending"
    MATCHED = "matched"
    PASSED = "passed"


@dataclass(frozen=True)
class RFAOutcome:
    status: RFAStatus
    owner: Optional[str]
    winning_bid: int
    salary: Optional[int]
    contract_years: Optional[int]
    controlling_team: str
    highest_bidder: Optional[str]
    decision: Optional[RFADecision]

    @property
    def pending(self) -> bool:
        return self.status is RFAStatus.PENDING


def _coerce_rfa_decision(
    decision: Union[RFADecision, str],
) -> RFADecision:
    if isinstance(decision, RFADecision):
        return decision
    if not isinstance(decision, str):
        raise TypeError("decision must be RFADecision.MATCH or RFADecision.PASS")
    try:
        return RFADecision(decision.strip().lower())
    except ValueError as exc:
        raise ValueError("RFA decision must be 'match' or 'pass'") from exc


def resolve_rfa_outcome(
    winning_bid: object,
    controlling_team: str,
    highest_bidder: Optional[str],
    decision: Optional[Union[RFADecision, str]] = None,
) -> RFAOutcome:
    """Resolve a revealed RFA bid into no-sale, pending, match, or pass."""

    amount = validate_bid(winning_bid)
    controlling = _validate_team_id(controlling_team, "controlling_team")
    resolved_decision = None if decision is None else _coerce_rfa_decision(decision)

    if amount == 0:
        if resolved_decision is not None:
            raise ValueError("an RFA decision cannot be made on a zero bid")
        return RFAOutcome(
            status=RFAStatus.NO_SALE,
            owner=None,
            winning_bid=0,
            salary=None,
            contract_years=None,
            controlling_team=controlling,
            highest_bidder=None,
            decision=None,
        )

    bidder = _validate_team_id(highest_bidder, "highest_bidder")
    if resolved_decision is None:
        status = RFAStatus.PENDING
        owner = None
    elif resolved_decision is RFADecision.MATCH:
        status = RFAStatus.MATCHED
        owner = controlling
    else:
        status = RFAStatus.PASSED
        owner = bidder

    return RFAOutcome(
        status=status,
        owner=owner,
        winning_bid=amount,
        salary=amount,
        contract_years=RFA_CONTRACT_YEARS,
        controlling_team=controlling,
        highest_bidder=bidder,
        decision=resolved_decision,
    )


@dataclass(frozen=True)
class CapWarning:
    projected_total: int
    salary_cap: int
    allowed: bool
    warning: bool
    over_by: int
    cap_space: int


def _validate_nonnegative_whole_units(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{} must be an integer".format(field_name))
    if value < 0:
        raise ValueError("{} cannot be negative".format(field_name))
    return value


def cap_warning(
    projected_total: object,
    salary_cap: object = SALARY_CAP,
) -> CapWarning:
    """Return warning-only cap information; even an over-cap total is allowed."""

    total = _validate_nonnegative_whole_units(projected_total, "projected_total")
    cap = _validate_nonnegative_whole_units(salary_cap, "salary_cap")
    cap_space = cap - total
    over_by = max(-cap_space, 0)
    return CapWarning(
        projected_total=total,
        salary_cap=cap,
        allowed=True,
        warning=over_by > 0,
        over_by=over_by,
        cap_space=cap_space,
    )


check_cap_warning = cap_warning


__all__ = [
    "AGE_CUTOFF_DAY",
    "AGE_CUTOFF_MONTH",
    "BidEvent",
    "BidEventKind",
    "BidEventType",
    "BidResponseStatus",
    "BidValidationError",
    "CapWarning",
    "DRAFT_YEAR",
    "MIN_POSITIVE_BID",
    "RFA_CONTRACT_YEARS",
    "RFADecision",
    "RFAOutcome",
    "RFAStatus",
    "RFA_MAX_AGE",
    "RevealAudit",
    "RevealResult",
    "RevealStatus",
    "RosterClassification",
    "RosterStatus",
    "SALARY_CAP",
    "SpecialRosterEntry",
    "TeamBidAudit",
    "TieBreakAudit",
    "UFA_MIN_AGE",
    "age_on_cutoff",
    "cap_warning",
    "check_cap_warning",
    "classify_roster_entry",
    "compute_effective_bid",
    "effective_bid",
    "resolve_reveal",
    "resolve_rfa_outcome",
    "validate_bid",
    "validate_bid_value",
]
