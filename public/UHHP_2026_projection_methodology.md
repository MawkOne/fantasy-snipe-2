# UHHP 2026 Projection & Auction Valuation Methodology

## Purpose

This methodology converts season-long player projections into a
UHHP-specific fantasy-point projection, then converts those projections
into **Value Over Replacement Player (VORP)** and an auction-value
reference.

The primary goal is not to predict the exact auction price of every
player. It is to answer three different questions:

1.  **How many UHHP fantasy points is the player projected to produce?**
2.  **How much production does that player add relative to a
    replacement-level player at his position?**
3.  **How much should that production matter when constructing a \$100
    UHHP roster?**

For roster construction, the final optimization metric is **projected
active-roster fantasy points**, not total points sitting on the full
roster.

------------------------------------------------------------------------

## 1. Source Projection Data

The projection input contains season projections for skaters and
goalies. The skater fields include:

-   Games played (`GP`)
-   Goals (`G`)
-   Assists (`A`)
-   Plus/minus (`+/-`)
-   Penalty minutes (`PIM`)
-   Power-play goals (`PPG`)
-   Short-handed goals (`SHG`)
-   Shots on goal (`SOG`)

The newer projection source also contains additional rate statistics
such as TOI, PPP, SHP, blocks, hits and faceoffs. These are retained in
the source data, but only statistics represented in the UHHP scoring
rules should contribute to UHHP fantasy points.

Goalie projections are handled separately because UHHP uses
goalie-specific scoring categories.

------------------------------------------------------------------------

## 2. UHHP Scoring Conversion

Projected NHL statistics are converted into UHHP fantasy points using
the league's scoring system.

The league snapshot identifies UHHP as a **Head-to-Head Points** league
and records scoring values including:

### Skaters

  Statistic                   UHHP Points
  ------------------------- -------------
  Goal                                  3
  Assist                                2
  Defenseman Goal bonus                +2
  Defenseman Assist bonus              +1
  Plus/Minus                         0.25
  Shot on Goal                       0.20
  Short-Handed Goal                    +2
  Penalty Minute                        0

This means a forward goal is worth 3 points, while a defenseman goal is
effectively worth 5 points once the defenseman bonus is included.

Likewise, a forward assist is worth 2 points while a defenseman assist
is effectively worth 3.

### Goalies

Relevant goalie scoring includes:

  Statistic         UHHP Points
  --------------- -------------
  Win                         2
  Save                     0.20
  Goal Against            -1.25
  Shutout                    +1
  Overtime Loss              +1
  Shootout Loss              +1

The projection model applies the UHHP scoring weights to the projected
statistical totals to calculate each player's projected season fantasy
points.

------------------------------------------------------------------------

## 3. Position Normalization

For auction analysis, skaters are normalized into three valuation
groups:

-   **F** --- forwards (C/W and multi-position forward combinations)
-   **D** --- defensemen
-   **G** --- goalies

This matters because replacement value is position-specific.

A 150-point defenseman is substantially more valuable than a 150-point
forward because quality defensemen are scarcer.

------------------------------------------------------------------------

## 4. Active-Lineup Assumption

The current model uses the UHHP active lineup structure:

-   **9 forwards**
-   **4 defensemen**
-   **2 goalies**

That creates:

**15 active players per team**

Across 12 UHHP teams:

-   108 active forwards
-   48 active defensemen
-   24 active goalies

These active-player counts establish the replacement level at each
position.

------------------------------------------------------------------------

## 5. Replacement-Level Calculation

Replacement level is defined as the projected fantasy points of the
final player required to fill all active positions across the league.

For the current 2026 projection set:

  Position     League Active Slots   Replacement FPTS
  ---------- --------------------- ------------------
  Forward                      108         **149.51**
  Defense                       48          **93.98**
  Goalie                        24         **120.34**

These values should be recalculated whenever the underlying projection
dataset materially changes.

They are not arbitrary thresholds. They represent the approximate
production available from the last player required to fill every active
lineup in the league.

------------------------------------------------------------------------

## 6. VORP Calculation

For each player:

**VORP = Projected UHHP FPTS − Position Replacement FPTS**

Examples:

A forward projected for 200 FPTS:

`200 − 149.51 = +50.49 VORP`

A defenseman projected for 150 FPTS:

`150 − 93.98 = +56.02 VORP`

A goalie projected for 150 FPTS:

`150 − 120.34 = +29.66 VORP`

Negative VORP means the player's projection is below the league-wide
active replacement level at his position.

------------------------------------------------------------------------

## 7. Converting VORP Into Auction Dollars

UHHP has:

-   12 teams
-   \$100 salary cap per team
-   \$1,200 total league salary capacity

With 15 active players per team and a \$2 minimum positive auction
salary:

`12 × 15 × $2 = $360`

of the league's salary capacity represents minimum active-roster
spending.

That leaves:

`$1,200 − $360 = $840`

of discretionary salary to allocate toward production above replacement.

The current projection pool produces an approximate conversion rate of:

**\$0.10791 per VORP point**

The theoretical VORP auction value is therefore:

`VORP$ = max($2, $2 + positive VORP × 0.10791)`

Values are rounded to whole dollars because UHHP auction salaries use
whole-dollar units.

### Important

**VORP\$ is a theoretical production value, not a prediction of the
player's actual winning bid.**

Actual auction prices are affected by nomination timing, cap space,
positional needs, RFAs, owner behavior and scarcity.

------------------------------------------------------------------------

## 8. Historical Auction Price Model

To estimate likely clearing prices, the VORP model is combined with UHHP
historical auction behavior.

The current market anchor uses:

`Market Anchor = 70% current VORP$ + 30% historical median winning price`

Historical prices are segmented by auction context/position where
appropriate.

This creates three separate numbers:

-   **VORP\$** --- theoretical production value
-   **Expected Clearing Price** --- estimated market price
-   **Maximum/Target Bid** --- roster-specific amount worth paying

These should not be treated as interchangeable.

------------------------------------------------------------------------

## 9. Historical GM Behaviour

Historical UHHP bid sheets are also used to estimate how aggressively
individual GMs bid when they participate.

For example, New Oilers Nation historically does not bid on every
player, but when participating has tended to bid more aggressively than
the room median.

Opponent bidding behavior helps estimate:

-   likely competing bid
-   aggressive competing bid
-   probability a nominally cheap player actually remains cheap

This layer is particularly important in a silent auction because the
winning bid is determined by what competing GMs submit rather than by an
open ascending auction.

------------------------------------------------------------------------

## 10. RFA Treatment

For the current auction analysis, the operational rule supplied for the
2026 roster is:

-   `years > 0` = committed/protected contract
-   `years = 0` = RFA whose displayed salary is **not committed**
-   An RFA that is nominated enters the auction process
-   The controlling team can match the winning outside bid
-   An un-nominated RFA can be retained by the controlling team at **\$2
    for 3 years**
-   The controlling team is not required to retain its RFAs

Therefore, RFAs should not be counted as committed salary or guaranteed
roster players when optimizing the pre-auction roster.

------------------------------------------------------------------------

## 11. Newly Released Players

When a contracted player is dropped before the auction, he is moved from
the team roster into the available auction pool.

His projection is then recalculated using the same positional
replacement level and VORP formula as every other available player.

Cap-hit placeholders such as `z-CAPHIT` are salary obligations and are
**not treated as playable auction assets**.

------------------------------------------------------------------------

## 12. Roster-Specific Marginal Value

League-wide VORP alone is not sufficient for making bids.

For a specific team, the more useful measure is:

**Active FPTS Added = New Active-Lineup Projection − Current
Active-Lineup Projection**

For example, if a team is starting a 130-point forward and buys a
180-point forward:

`180 − 130 = +50 active FPTS`

The player's 180 projected points are not the relevant roster gain. The
relevant gain is the **50 points he adds by replacing the existing
starter**.

This calculation must be performed sequentially because each acquisition
raises the team's replacement floor.

------------------------------------------------------------------------

## 13. Why Sequential Marginal Value Matters

Suppose a team needs three forwards and buys players projected for:

-   200
-   190
-   180

Those players should not all be compared against the same existing
starter.

The first acquisition replaces the weakest active forward.

The second replaces the next weakest.

The third replaces the next weakest.

Therefore, the marginal benefit declines as the active roster improves.

This prevents the model from overstating the value of buying several
similar mid-tier players.

------------------------------------------------------------------------

## 14. Final Roster Optimization

The auction optimizer should maximize:

**Projected FPTS of the legal active lineup**

subject to:

-   salary cap
-   roster-size requirements
-   active-position requirements
-   minimum auction salaries
-   already committed contracts
-   player availability
-   RFA matching risk
-   whole-dollar bids

Bench production is useful for depth, injuries and scheduling, but it
should not be counted equally with active-lineup production when
evaluating the immediate strength of the roster.

------------------------------------------------------------------------

## 15. New Oilers Nation Application

For New Oilers Nation, the current pre-auction framework is:

-   **\$70 committed salary**
-   **\$30 available**
-   existing contracted core retained
-   RFAs are optional rather than committed
-   goalie position is already relatively strong
-   the largest opportunity to increase active FPTS is primarily at
    forward, with selective defense upgrades

If seven roster positions must be filled, seven \$2 players require \$14
of the remaining \$30.

That leaves only:

**\$16 of discretionary spending above minimum salaries**

This is why auction-price efficiency matters considerably more than
simply identifying the highest-projected player.

------------------------------------------------------------------------

## 16. Balanced vs. Superstar Strategy

A superstar should be evaluated against the **best complete roster that
could be built without him**.

For example, the correct Kucherov question is not:

> Is Kucherov worth \$18?

It is:

> Does the best legal roster containing Kucherov at \$18 project for
> more active FPTS than the best legal roster that spends that \$18
> across multiple players?

This creates a roster-specific **break-even price** for every premium
player.

If the best roster without the player produces more active FPTS, the
superstar is too expensive for that particular team's roster
construction even if his standalone VORP is excellent.

------------------------------------------------------------------------

## 17. Auction Decision Metrics

For each available player, the useful auction board should ultimately
display:

  -----------------------------------------------------------------------
  Metric                              Meaning
  ----------------------------------- -----------------------------------
  Projected FPTS                      Raw UHHP season projection

  VORP                                Production above positional
                                      replacement

  VORP\$                              Theoretical league-wide dollar
                                      value

  Expected Price                      Historical-market estimate

  Active FPTS Added                   Improvement to this team's starting
                                      lineup

  FPTS Added / \$                     Roster-specific auction efficiency

  Maximum Bid                         Highest price before an alternative
                                      roster path becomes better

  RFA Risk                            Probability/value risk from
                                      incumbent matching
  -----------------------------------------------------------------------

The most important metric during the auction is **Active FPTS Added per
incremental dollar**, not raw projected points.

------------------------------------------------------------------------

## 18. Team Strength / Championship Target

Team comparisons should use the sum of the legal active lineup:

**9 F + 4 D + 2 G**

not the total projected points of every player on the roster.

The current working target for New Oilers Nation is approximately:

-   **2,600 active FPTS:** contender range
-   **2,650 active FPTS:** strong contender
-   **2,700 active FPTS:** target
-   **2,750+ active FPTS:** exceptional projection

These are working strategic thresholds, not guarantees of standings or
playoff outcomes. They should be updated as the auction progresses
because every acquisition changes the projected strength of competing
teams.

------------------------------------------------------------------------

## 19. Live Auction Updating

After every auction result, the model should update:

1.  Winning player and salary
2.  New owner's committed cap
3.  Remaining roster spots
4.  Remaining available player pool
5.  Active lineup projection
6.  Active FPTS gained from the purchase
7.  Replacement level if the available pool materially changes
8.  Expected prices based on remaining league cap
9.  Opponent needs and purchasing power
10. New optimal roster path for New Oilers Nation

The target should therefore be dynamic rather than a static pre-auction
shopping list.

------------------------------------------------------------------------

## 20. Core Principle

The model ultimately optimizes one thing:

> **Build the highest-projected legal active roster possible with the
> available salary cap.**

VORP identifies scarcity.

Historical prices identify market behaviour.

Opponent models identify competition.

But **active-roster FPTS determines whether an acquisition actually
makes the team stronger.**
