# UHHP Season Simulation Design (Monte Carlo)

## Goal
Build a forward‑looking simulator for the UHHP league that models the entire season life‑cycle and supports Monte Carlo experiments to forecast outcomes (PF, wins, standings, playoff odds) and decision support (auction pricing, budget allocation, waiver/trade strategy).

## Data sources
- UHHP league history (local DB)
  - Weekly matchups and PF: `cbs_weekly_matchups`, standings
  - Roster/contracts: `cbs_team_rosters` (salary, years, position, status)
  - Transactions: `cbs_transactions` (adds/drops, timing, prices)
  - Auction archives: `23_24 UHHP AUCTION TRACKER - Bids.csv`, `24_25 UHHP AUCTION TRACKER - Bids.csv`
- NHL stats DB (external Postgres)
  - Skater: `player_game_stats`, `player_game_advanced_metrics_flat`
  - Goalie: `goalie_game_stats`
  - Games: `games` (season codes, game_type)
  - Player attributes: `players`, `player_details` (birthdates)
- Forecasts used by GMs (CSV)
  - Current-season sources to average: `docs/Forecasts/Athletric 20232024.csv`, `docs/Forecasts/Dobber 20232024.csv`, `docs/Forecasts/Edraft 20232024.csv` (swap to 2024/25 when available)
  - Prior-season forecast vintages (for ex‑ante price calibration):
    - `docs/Forecasts/NHL 21_22 Forecasts - Athletic 2021_22.csv`
    - `docs/Forecasts/NHL 21_22 Forecasts - Dobber 21_22.csv`
    - `docs/Forecasts/NHL 21_22 Forecasts - Edraft 21_22.csv`
- League rules (reference)
  - `League_format.md`
  - `uhhp_simulations/simulation_rules.md`

## High‑level pipeline (per simulation trial)
1) Pre‑auction roster roll‑forward (contracts, RFA/UFA tagging)
2) Pre‑draft buyouts (optional, probabilistic)
3) Rookie draft (rights only, $0, non‑active)
4) Auction draft (3 rounds per UHHP flow) with competitive bidding and RFA matches
5) Waiver week (preseason churn and compliance)
6) Regular season (Weeks 1–22): weekly lineups, injuries, waivers, trades
7) Playoffs (seeding, brackets, finals) and outcomes

Each stage consumes the prior stage’s state and emits updated cap, rosters, and event logs.

## Stage models

### 1) Pre‑auction roster roll‑forward
- Inputs: `cbs_team_rosters` (season t), player ages from `player_details.birth_date`.
- Logic:
  - Decrement `years` by 1; any contract reaching 0 becomes free agent for season t+1.
  - RFA if age < 27 on Jul 1 of draft year; UFA if age ≥ 27.
  - Compute carryover salary commitments and initial cap space per team.
- Outputs: season t+1 cap table, FA pool (RFA/UFA), RFA rights map.

### 2) Pre‑draft buyouts (optional)
- Data: If historical buyouts are limited, use priors per team (low frequency).
- Logic:
  - Probabilistic buyout for negative‑value contracts (e.g., salary >> projected value).
  - Cap hits per league rule:
    - If 1 year left: $0 cap hit.
    - If 2 years left: 1‑year cap hit at ceil(0.5 × salary).
    - If 3 years left: 2 years of cap hit at ceil(0.5 × salary).
  - Represent hits as z‑CAP elements on roster for simulation bookkeeping.
- Outputs: adjusted caps, cap hit placeholders (immutable for auction stage).

### 3) Rookie draft
- Logic: draft picks generate rights at $0 for up to 3 years; rights are non‑active (no lineup PF in same season).
- Simplification: unless you want to simulate rights trading, treat rookies as future assets only.

### 4) Auction draft (3 rounds)
- Nomination order (given):
  1. Dook
  2. SoCal
  3. NoN
  4. Hawt
  5. degeneration x
  6. 3Sheets
  7. Shazam
  8. CinStars
  9. G Stars
  10. Pylons
  11. Lips
  12. Basteeerds

- Rounds and eligibility:
  - Round 1: RFA and UFA
  - Round 2: UFA only
  - Round 3: RFA only until all pass once

- Player projections and value:
  - Average the three forecast sources to expected FP by player.
  - Convert to UHHP fantasy FP using league scoring rules.
  - Estimate position replacement FP under UHHP lineup constraints (2 G, 2 C, 3 W, 4 F→ allocate 2 C, 2 W, 4 D).
  - VORP = E[FP] − replacement.
  - Include uncertainty: per‑position variance from past forecast errors (σ_pos), used in Monte Carlo draws.
  - Forecast vintage influence: when simulating historical auctions (for calibration/backtest), use the forecasts contemporaneous to that auction (e.g., 2021/22 forecast CSVs for the 2021/22 auction) to model GM ex‑ante inputs.

- GM private valuations (per team, per player):
  - value = α_pos × VORP × team_need_weight × risk_adjustment + ε
    - α_pos: price sensitivity per position (learned from 2023/24 auctions $/VORP using ex‑ante forecasts)
    - team_need_weight: increases for positions where roster depth is low
    - risk_adjustment: penalize high‑variance or injury‑prone assets
    - ε: idiosyncratic taste noise (N(0, σ_bid,pos))
  - GM priors (per team): aggressiveness, RFA‑pressure tendency, target auction reserve ($6–$10), position preference vector; calibrated from 2023/24 behavior or set defaults.

- Bidding mechanism:
  - English auction with $1 increments among GMs whose private value ≥ current price and who have sufficient budget (respecting min $2 per remaining slot).
  - Price‑drop modeling: after league cumulative spend hits a threshold (estimated from 2024 price curve), reduce active bidder set and/or scale α_pos temporarily to produce the observed mid‑draft discount regime.

- RFA match rule:
  - If a non‑owner wins an RFA, the owning GM can match at the clearing price if price ≤ θ × owner_value and sufficient cap remains. θ ~ U[0.9,1.1] to capture hesitation.
  - If matched, asset stays; else it transfers.

- Constraints:
  - Whole‑dollar bids, min $2, auction cap ≤ $98 per team; savings for waivers allowed.

- Outputs: auction log (nominations, bidders, clearing prices, RFA outcomes), updated rosters and caps.

### 5) Waiver week (preseason)
- Model: daily sealed bids; per‑team signing counts drawn from historical 2024 distribution; average price by team aligned to historical means (lower average price correlates with better outcomes in 2024).
- Objective: reach Week 1 compliance (roster minimums) with total roster cap exactly $100 for every team. No cap savings are permitted.

### 6) Regular season (Weeks 1–22)
- Player season simulation:
  - For each player, draw season FP from N(E[FP], σ_pos^2), apply injury model (position/age‑based rates, missed games), and goalie start‑share.
- Weekly lineups:
  - Pick best available by FP for each slot (2 G, 2 C, 3 W, 4 F, 4 D); introduce small sit/start error rate to reflect real behavior.
- In‑season waivers:
  - Weekly churn per team based on 2024 transaction rates; small bids, PF‑driven targeting.
- Trades:
  - Buyers/sellers switch‑point sampled from historical timing distribution; buyers convert surplus W/D to C/G; sellers acquire RFAs/term and picks.
  - Accept trades if both sides’ surplus (based on private values) is positive; add friction/noise.
- Outputs: weekly PF, wins/losses, standings.

### 7) Playoffs
- Seed per simulated standings; run bracket per UHHP (top 6) with two‑week final; draw weekly PF with variance.

## Calibration

### Forecasts and uncertainty
- Average Athletic/Dobber/Edraft projections.
- Measure forecast errors vs actuals (e.g., 2023/24) by position to estimate σ_pos.
- Optional shrinkage: blend with prior season actuals to stabilize.
- Forecast vintages for price calibration: for historical seasons, use their contemporary forecasts (e.g., 2021/22 CSVs) to fit the mapping from expected VORP to auction price (by position), minimizing bias from ex‑post outcomes.

### Replacement FP
- Compute using the projected pool and UHHP lineup slot counts across 12 teams.

### Auction pricing
- From UHHP auctions (e.g., 2023/24), with ex‑ante forecasts for those seasons:
  - Estimate $/expected‑VORP by position (medians or quantiles) to set α_pos.
  - Derive price curves by nomination index to locate the “price‑drop” threshold.
  - Infer GM priors: spend aggressiveness, RFA nomination frequency, cap reserve habits, position mix.

### Transactions
- Preseason/in‑season signing count distribution per team and average bid sizes; timing curves.
- Trade volume and timing; asset types exchanged (UFA‑for‑RFA/picks).

## Monte Carlo engine
- Inputs per trial:
  - Forecast means and σ_pos, initial rosters/contracts, team caps, GM priors.
- Random draws per trial:
  - Player FP deviations; injuries; bidding ε; match thresholds; price‑drop onset; waiver signings; trade timing/acceptance.
- Outputs per trial:
  - Auction log and prices; rosters and cap states; preseason/in‑season signings; trades; weekly PF and standings; playoff results.
- Aggregations:
  - Team win/Top‑3/Playoff/Title probabilities; expected PF; expected spend and price tiers by position; sensitivity to GM heuristics.

## Implementation outline
- Package: `uhhp_sim/`
  - `loaders.py`: rosters/contracts, UHHP weekly, auctions, transactions, forecasts, NHL DB link; supports forecast vintages per season
  - `projections.py`: forecast averaging, scoring conversion, σ_pos calibration, replacement FP
  - `calibration.py`: fit $/expected‑VORP by position using prior‑year forecast vintages and historical auctions; estimate price‑drop trigger
  - `auction.py`: GM valuations, nomination policy, English auction, RFA match, price‑drop, constraints
  - `waivers.py`: preseason churn and bids; in‑season churn model
  - `season.py`: weekly FP draws, injuries, lineups, standings
  - `trades.py`: buyers/sellers model and trade execution
  - `playoffs.py`: bracket simulation
  - `monte_carlo.py`: run N trials, manage seeds, collect outputs
  - `config.yaml`: GM priors (aggressiveness, RFA tactics, cap reserve, pos prefs), toggles

- Artifacts
  - JSON/CSV logs per trial (auction events, roster states), plus roll‑ups for dashboards

## Validation & backtesting
- Replay historical seasons (e.g., 2021/22, 2023/24) with their ex‑ante forecast vintages to compare simulated auction prices vs actuals (MAE, correlation) and reduce ex‑post bias.
- Compare simulated PF distributions to observed PF (by team, by position contribution).
- Sanity checks: price‑drop occurrence, RFA match rates, waiver signing volumes, trade timing.

## Next steps
1) Wire forecast averaging to current‑season inputs and compute σ_pos by backtesting 2023/24; ingest prior‑year forecast vintages for price calibration.
2) Implement auction module with competitive bidding + RFA match + price‑drop dynamics.
3) Calibrate GM priors from 2023/24 (or set initial heuristics) and validate on 2024.
4) Add preseason/in‑season waiver models and basic trade model.
5) Run 1,000‑trial Monte Carlo; produce summary dashboards.
6) Iterate calibration on observed deltas.
