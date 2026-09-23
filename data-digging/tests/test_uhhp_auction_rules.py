"""Tests for the dependency-free UHHP 2026 auction domain rules."""

from __future__ import annotations

import math
import sys
import unittest
from datetime import date, datetime
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auction import (  # noqa: E402
    BidEvent,
    BidEventType,
    BidResponseStatus,
    BidValidationError,
    RFADecision,
    RFAStatus,
    RevealStatus,
    RosterStatus,
    SpecialRosterEntry,
    age_on_cutoff,
    cap_warning,
    classify_roster_entry,
    compute_effective_bid,
    resolve_reveal,
    resolve_rfa_outcome,
    validate_bid,
)


class AgeOnCutoffTests(unittest.TestCase):
    def test_july_first_boundary_uses_draft_year(self) -> None:
        self.assertEqual(age_on_cutoff(date(2000, 7, 1), 2026), 26)
        self.assertEqual(age_on_cutoff(date(2000, 6, 30), 2026), 26)
        self.assertEqual(age_on_cutoff(date(2000, 7, 2), 2026), 25)

    def test_leap_day_birthdate(self) -> None:
        self.assertEqual(age_on_cutoff(date(2000, 2, 29), 2026), 26)

    def test_rejects_non_date_and_future_birthdate(self) -> None:
        with self.assertRaises(TypeError):
            age_on_cutoff("2000-01-01", 2026)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            age_on_cutoff(datetime(2000, 1, 1), 2026)
        with self.assertRaises(ValueError):
            age_on_cutoff(date(2026, 7, 2), 2026)


class RosterClassificationTests(unittest.TestCase):
    def test_positive_contract_years_are_protected(self) -> None:
        self.assertEqual(classify_roster_entry(1), RosterStatus.PROTECTED)
        self.assertEqual(
            classify_roster_entry(3, date(1980, 1, 1), rookie=True),
            RosterStatus.PROTECTED,
        )

    def test_expired_rookie_and_special_entries_do_not_need_birthdates(self) -> None:
        self.assertEqual(
            classify_roster_entry(0, rookie=True),
            RosterStatus.ROOKIE,
        )
        self.assertEqual(
            classify_roster_entry(0, special=SpecialRosterEntry.ASSET),
            RosterStatus.ASSET,
        )
        self.assertEqual(
            classify_roster_entry(0, special="draft_pick_placeholder"),
            RosterStatus.ASSET,
        )
        self.assertEqual(
            classify_roster_entry(0, special="cap-hit"),
            RosterStatus.CAP_HIT,
        )

    def test_expired_player_is_rfa_through_age_26(self) -> None:
        self.assertEqual(
            classify_roster_entry(0, date(2000, 7, 1), 2026),
            RosterStatus.RFA,
        )
        self.assertEqual(
            classify_roster_entry(0, date(1999, 7, 2), 2026),
            RosterStatus.RFA,
        )

    def test_expired_player_is_ufa_from_age_27(self) -> None:
        self.assertEqual(
            classify_roster_entry(0, date(1999, 7, 1), 2026),
            RosterStatus.UFA,
        )

    def test_missing_birthdate_requires_review(self) -> None:
        self.assertEqual(classify_roster_entry(0), RosterStatus.REVIEW)

    def test_rejects_invalid_contract_years(self) -> None:
        for value in (-1, 1.5, True):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                classify_roster_entry(value)  # type: ignore[arg-type]


class BidValidationTests(unittest.TestCase):
    def test_accepts_zero_and_integer_bids_of_at_least_two(self) -> None:
        for value in (0, 2, 3, 100):
            with self.subTest(value=value):
                self.assertEqual(validate_bid(value), value)

    def test_rejects_disallowed_or_non_integer_values(self) -> None:
        invalid_values = (
            False,
            True,
            1,
            -1,
            0.0,
            2.0,
            2.5,
            math.nan,
            Fraction(2, 1),
            "2",
            None,
        )
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(BidValidationError):
                validate_bid(value)


class EffectiveBidTests(unittest.TestCase):
    def test_empty_or_cancelled_history_has_zero_effective_bid(self) -> None:
        self.assertEqual(compute_effective_bid([]), 0)
        self.assertEqual(
            compute_effective_bid([BidEvent.submit(8), BidEvent.cancel()]),
            0,
        )

    def test_replacement_overwrites_and_can_follow_cancel(self) -> None:
        events = [
            BidEvent.submit(3),
            BidEvent.replacement(7),
            BidEvent.cancel(),
            BidEvent.replacement(4),
        ]
        self.assertEqual(compute_effective_bid(events), 4)

    def test_explicit_zero_is_a_valid_submission(self) -> None:
        self.assertEqual(compute_effective_bid([BidEvent.submit(0)]), 0)

    def test_event_validation(self) -> None:
        with self.assertRaises(BidValidationError):
            BidEvent(BidEventType.SUBMIT, 1)
        with self.assertRaises(BidValidationError):
            BidEvent(BidEventType.CANCEL, 2)
        with self.assertRaises(BidValidationError):
            BidEvent(BidEventType.REPLACEMENT)
        with self.assertRaises(TypeError):
            compute_effective_bid(["submit"])  # type: ignore[list-item]


class RevealResolutionTests(unittest.TestCase):
    def test_all_zero_is_no_sale_without_tie_and_audits_response_types(self) -> None:
        result = resolve_reveal(
            {
                "alpha": [BidEvent.submit(0)],
                "charlie": [BidEvent.submit(6), BidEvent.cancel()],
            },
            ["alpha", "bravo", "charlie"],
        )

        self.assertEqual(result.status, RevealStatus.NO_SALE)
        self.assertIsNone(result.winner)
        self.assertEqual(result.winning_bid, 0)
        self.assertFalse(result.tie_was_resolved)
        self.assertEqual(result.audit.tie_break.tied_teams, ())
        self.assertEqual(result.tie_order, ("alpha", "bravo", "charlie"))
        self.assertEqual(
            result.effective_bids,
            {"alpha": 0, "bravo": 0, "charlie": 0},
        )
        self.assertEqual(
            result.audit.for_team("alpha").response_status,
            BidResponseStatus.SUBMITTED,
        )
        self.assertEqual(
            result.audit.for_team("bravo").response_status,
            BidResponseStatus.NON_RESPONSE,
        )
        self.assertEqual(
            result.audit.for_team("charlie").response_status,
            BidResponseStatus.CANCELLED,
        )

    def test_unique_positive_winner_does_not_rotate_tie_order(self) -> None:
        result = resolve_reveal(
            {
                "alpha": [BidEvent.submit(4)],
                "bravo": [BidEvent.submit(7)],
                "charlie": [BidEvent.submit(9), BidEvent.cancel()],
            },
            ["charlie", "alpha", "bravo"],
        )

        self.assertEqual(result.status, RevealStatus.SOLD)
        self.assertEqual(result.winner, "bravo")
        self.assertEqual(result.winning_bid, 7)
        self.assertFalse(result.tie_was_resolved)
        self.assertEqual(result.tie_order, ("charlie", "alpha", "bravo"))

    def test_positive_tie_uses_priority_and_moves_winner_to_bottom(self) -> None:
        result = resolve_reveal(
            {
                "alpha": [BidEvent.submit(8)],
                "bravo": [BidEvent.submit(8)],
                "charlie": [BidEvent.submit(3)],
            },
            ["charlie", "bravo", "alpha", "delta"],
        )

        self.assertEqual(result.winner, "bravo")
        self.assertEqual(result.winning_bid, 8)
        self.assertTrue(result.tie_was_resolved)
        self.assertEqual(result.audit.tie_break.tied_teams, ("bravo", "alpha"))
        self.assertEqual(
            result.audit.tie_break.order_before,
            ("charlie", "bravo", "alpha", "delta"),
        )
        self.assertEqual(
            result.updated_tie_order,
            ("charlie", "alpha", "delta", "bravo"),
        )
        self.assertEqual(result.audit.tie_break.winner, "bravo")

    def test_rejects_ambiguous_or_unknown_tie_order_teams(self) -> None:
        with self.assertRaises(ValueError):
            resolve_reveal({}, ["alpha", "alpha"])
        with self.assertRaises(ValueError):
            resolve_reveal({"outside": [BidEvent.submit(2)]}, ["alpha"])
        with self.assertRaises(ValueError):
            resolve_reveal({}, [])


class RFAOutcomeTests(unittest.TestCase):
    def test_zero_bid_is_no_sale(self) -> None:
        result = resolve_rfa_outcome(0, "rights-holder", None)
        self.assertEqual(result.status, RFAStatus.NO_SALE)
        self.assertIsNone(result.owner)
        self.assertIsNone(result.salary)
        self.assertIsNone(result.contract_years)

    def test_positive_bid_without_decision_is_pending(self) -> None:
        result = resolve_rfa_outcome(6, "rights-holder", "high-bidder")
        self.assertEqual(result.status, RFAStatus.PENDING)
        self.assertTrue(result.pending)
        self.assertIsNone(result.owner)
        self.assertEqual(result.salary, 6)
        self.assertEqual(result.contract_years, 3)
        self.assertEqual(result.controlling_team, "rights-holder")

    def test_match_keeps_player_with_controlling_team(self) -> None:
        result = resolve_rfa_outcome(
            6,
            "rights-holder",
            "high-bidder",
            RFADecision.MATCH,
        )
        self.assertEqual(result.status, RFAStatus.MATCHED)
        self.assertEqual(result.owner, "rights-holder")
        self.assertEqual(result.salary, 6)

    def test_pass_awards_player_to_highest_bidder(self) -> None:
        result = resolve_rfa_outcome(6, "rights-holder", "high-bidder", "pass")
        self.assertEqual(result.status, RFAStatus.PASSED)
        self.assertEqual(result.owner, "high-bidder")
        self.assertEqual(result.decision, RFADecision.PASS)

    def test_decision_is_invalid_for_zero_bid(self) -> None:
        with self.assertRaises(ValueError):
            resolve_rfa_outcome(0, "rights-holder", None, "match")


class CapWarningTests(unittest.TestCase):
    def test_at_or_under_cap_has_no_warning(self) -> None:
        below = cap_warning(95)
        self.assertTrue(below.allowed)
        self.assertFalse(below.warning)
        self.assertEqual(below.over_by, 0)
        self.assertEqual(below.cap_space, 5)

        at_cap = cap_warning(100)
        self.assertTrue(at_cap.allowed)
        self.assertFalse(at_cap.warning)
        self.assertEqual(at_cap.over_by, 0)
        self.assertEqual(at_cap.cap_space, 0)

    def test_over_cap_is_allowed_and_reports_overage(self) -> None:
        result = cap_warning(108)
        self.assertTrue(result.allowed)
        self.assertTrue(result.warning)
        self.assertEqual(result.over_by, 8)
        self.assertEqual(result.cap_space, -8)

    def test_custom_cap_and_invalid_values(self) -> None:
        self.assertEqual(cap_warning(60, 50).over_by, 10)
        for value in (-1, 100.0, True):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                cap_warning(value)


if __name__ == "__main__":
    unittest.main()
