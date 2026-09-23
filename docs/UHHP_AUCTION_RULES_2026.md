# UHHP 2026 Auction Rules

Status: **Canonical implementation rules**  
Rules version: **2026.1**  
Machine-readable source: `backend/config/uhhp_auction_rules_2026.json`

This document records the league decisions that govern the UHHP draft-day silent auction. If older specifications or prototype code conflict with this document, this document and the machine-readable rules file take precedence.

## 1. Auction frontend

The canonical frontend is the existing page at:

```text
/draft-room-uhhp
```

The existing page design will be retained, but prototype behavior will be replaced with server-authoritative auction state.

The existing GM Bids area is the canonical location for the GM response circles. The public Controlling Team dropdown in the top navigation will be removed. Team impersonation may exist only as an explicitly marked commissioner/development tool.

## 2. Salary and contracts

- The salary cap target is 100 units.
- GMs may exceed 100 during the draft.
- Going over 100 produces warnings but does not block a nomination or bid.
- Negative cap space must remain visible.
- Rosters must be cap and position compliant by the start of Week 1.
- Salaries use whole-number units.
- A positive auction bid must be at least 2 units.
- A bid of 1 is invalid.
- A bid of 0 is valid.
- Every player acquired during the draft-day auction receives a three-year contract.
- The player's salary is the final winning bid.

Valid bids are therefore:

```text
0, 2, 3, 4, 5, ...
```

## 3. UFA and RFA classification

UFA/RFA classification applies only when a non-rookie player's contract years equal zero.

Age is calculated as of July 1 of the draft year.

- Age 26 or younger on July 1: RFA.
- Age 27 or older on July 1: UFA.

For the 2026 auction:

- Born July 1, 1999 or earlier: UFA.
- Born July 2, 1999 or later: RFA.

Additional rules:

- Contract years greater than zero: protected contract.
- Rookie marker: protected rookie, unless explicitly released or no longer eligible for rookie protection.
- Draft-pick placeholder: draft asset, not a player.
- `z-CAPHIT` placeholder: cap obligation, not a player.
- Missing birthdate: commissioner review; do not silently assume UFA or RFA.
- An RFA retains the team from the pre-auction roster snapshot as its controlling team.
- A UFA has no controlling team or matching rights.
- Classification is stored as a draft-year snapshot so historical auctions do not change later.

## 4. Auction stages

### 4.1 Superstar Round

- One owner-by-owner round.
- Current GM may nominate an eligible UFA or RFA.
- The auction begins immediately after nomination.

### 4.2 UFA Nominations

- Two owner-by-owner rounds.
- Current GM may nominate an eligible UFA.
- The auction begins immediately after nomination.

### 4.3 RFA Poaching

- Continues owner-by-owner until all eligible GMs have passed or the RFA pool is exhausted.
- Current GM may nominate an eligible RFA controlled by another team.
- A GM may choose **Pass Remaining Nominations**.
- After passing, that GM receives no more nomination turns in the RFA Poaching stage.
- A GM who passed may still submit bids on later players.
- A GM who passed may still Match or Pass when one of their controlled RFAs is auctioned.

Only one player auction may be active at a time. Only the current nominating GM may nominate.

## 5. Silent bidding

- Every team's effective bid defaults to 0.
- GMs do not have to respond.
- A GM may explicitly submit a 0 bid.
- A non-response has an effective bid of 0.
- A submitted 0 and non-response remain distinct in the audit history.
- Each GM has one effective bid per player auction.
- Before reveal, a GM may see only their own effective bid.
- Other teams' amounts and the leading team remain hidden.
- The GM response strip may show whether a GM responded, but never the amount before reveal.

### 5.1 Cancellation and replacement

- A GM may cancel their submitted bid before reveal.
- Cancellation changes their effective bid back to 0.
- A GM may submit a replacement bid after cancellation, provided the commissioner has not revealed.
- Submit, cancel, and replacement actions are retained in an append-only audit history.

### 5.2 Closing and reveal

- There is no automatic bidding timer.
- The commissioner decides when to close and reveal.
- All GMs are not required to respond.
- If GMs have not responded, the commissioner receives a warning and may still reveal.
- Reveal atomically locks all bids and cancellations.
- No bid changes are accepted after reveal.
- Reveal and winner calculation are server-authoritative.

## 6. GM response display

The GM response circles belong in the existing GM Bids section.

Before reveal:

- Neutral circle: no response.
- Checkmarked circle: response submitted.
- A submitted 0 looks the same as a submitted positive bid.
- Header displays the response count, such as `8 / 12 responded`.
- Label states that amounts remain hidden until commissioner reveal.

After reveal:

- Show every effective bid amount.
- Explicit 0 may display `$0`.
- Non-response may display `—`, while still being treated as 0.
- Highlight the winning team.
- Highlight tied teams and the team receiving tie-break priority.

## 7. No Sale

If no effective bid is greater than zero when the commissioner reveals:

- The auction concludes as No Sale.
- The player is not awarded.
- No contract is created.
- No tie-break is run.
- For an RFA, no Match/Pass decision is required.
- The player remains available under the applicable ownership/rights status.
- The nomination order advances to the next eligible GM.

## 8. Positive winning bids

If at least one effective bid is positive:

- The highest effective bid wins, subject to the tie-break process.
- For a UFA, the result may finalize immediately.
- For an RFA, the result moves to `rfa_match_pending`.

## 9. Tie-break process

Tie-breaks apply only when multiple teams share the highest positive bid.

1. The initial tie-break priority order comes from the auction nomination order.
2. The tied team highest in the current priority order wins.
3. The winning salary remains the tied high bid.
4. The priority winner moves to the bottom of the tie-break order.
5. The new order is persisted.
6. An audit entry records the auction, tied teams, priority winner, old order, and new order.

There is no tie rebidding round.

## 10. RFA Match or Pass

After a positive RFA auction result is revealed:

- The auction enters `rfa_match_pending`.
- The highest outside bidder and amount are revealed.
- Nothing resolves automatically.
- There is no timer or automatic expiry.
- Only the RFA's controlling GM may decide.
- Available decisions are Match and Pass.
- The commissioner cannot bypass the pending decision through normal finalization.

### Match

- The controlling team retains the player.
- Salary equals the revealed winning bid.
- Contract term is three years.

### Pass

- The highest bidder receives the player.
- Salary equals the revealed winning bid.
- Contract term is three years.

## 11. Data sources

- Current rosters and contracts: `public/fantasy_hockey_rosters_2026_structured.json`
- Skater pool and projections: `public/uhhp-sept-22.csv`
- Goalie pool and projections: `public/goalies.csv`
- Team, abbreviation, GM, and email mapping: local private file `public/gms.md` (template: `public/gms.example.md`)

The real GM directory contains private email addresses and must not be committed or served publicly. Both projection CSVs have a report-title row before the real CSV header and must be imported accordingly. `Avail = W` means waiver/free agent, not winger. Player matching should prefer CBS player ID and otherwise use normalized name, position, and NHL team together.

## 12. Audit and recovery

The server must retain append-only records for:

- Nomination
- Bid submission
- Bid cancellation
- Replacement bid
- Non-response at reveal
- Commissioner reveal
- No Sale
- Tie resolution and priority-order update
- RFA Match/Pass
- Final contract assignment
- Commissioner void or correction

A completed auction must not be silently rewritten. Corrections should be represented by explicit void/correction events.
