# Scribner Draft — Product and UX Requirements

## 1. Product Goal

Create a responsive web application for running a private fantasy hockey draft using the **Scribner draft format**. It must work well on both phones and laptops and be simple enough to use for a live weekend draft without training.

The application must support one commissioner/admin who also participates as a GM, plus invited GMs who join through private team-specific links.

## 2. Scribner Draft Rules

1. The draft contains a configurable number of rounds.
2. At the start of each round, every participating GM privately selects one available player.
3. Picks remain sealed until the admin reveals the round.
4. Multiple GMs may select the same player in the same round.
5. At reveal, every GM receives the player they selected, including duplicate selections.
6. After reveal, the unique set of players selected in that round is removed from the available-player pool.
7. A player selected in a previous round cannot be selected in any later round.
8. Each team may submit only one pick per round.
9. There is no countdown clock for the weekend MVP.
10. The admin explicitly starts each round and explicitly reveals each round.
11. After reveal, the admin explicitly starts the next round.
12. The draft ends after the configured number of rounds or when the admin chooses to finish it.

## 3. User Roles

### 3.1 Admin / Commissioner

The admin can:

- Create and name a draft.
- Configure teams and invite each team owner.
- Select which team belongs to the admin.
- Configure the number of rounds.
- Configure roster requirements.
- Enable or disable scoring categories.
- Set the point value for every enabled scoring category.
- Save draft configuration before starting.
- Start a round.
- Submit a sealed pick for the admin's own team using the same picking experience as every other GM.
- See which teams have submitted, but not their selected players before reveal.
- Reveal all submitted picks simultaneously.
- Start the next round.
- Finish the draft.
- View final rosters and projected point totals.

### 3.2 Team Owner / GM

A GM can:

- Open a private team-specific invite link on phone or laptop.
- See the draft name and their assigned team name.
- Enter the room without creating an account for the weekend MVP.
- See whether a round is waiting, open for picks, submitted, or revealed.
- Browse, search, filter, and sort available players.
- View player projections and projected fantasy points.
- Select one player and review the selection before submitting.
- Submit one sealed pick per round.
- See confirmation that the pick is sealed.
- Change the pick only if the product explicitly supports it before reveal. For the MVP, submitted picks are final unless the admin resets them.
- See all teams' selections after reveal.
- See their updated roster after reveal.
- Leave the room using an explicit Leave Room action.
- Reopen the invite link and return to the same assigned team.

## 4. Draft Creation and Setup

### 4.1 Create Draft Screen

Required fields:

- Draft name.

Primary action:

- `Create Draft`

Validation:

- Draft name is required.
- Draft name must be 1–80 characters after trimming.

After creation, navigate directly to the draft setup screen.

### 4.2 Draft Setup Screen

The setup screen must be organized into clear sections rather than one long undifferentiated form.

#### Section A — Draft Identity

Display:

- Draft name.
- Room code.
- Draft status: `Setup`.

Allow:

- Editing the draft name before the draft begins.

#### Section B — Teams and Invitations

For each team, admin can enter:

- Team name.
- Owner email.
- Whether this is the admin's team.

Each team row must display:

- Team name.
- Owner email.
- Invite state: `Not sent`, `Sent`, or `Joined`.
- `Copy Invite Link` action.
- `Send Invite` action when email delivery is configured.
- Edit action.
- Remove action before the draft begins.

Rules:

- Every team receives a unique, private invite token.
- Exactly one team should be designated as the admin's team before the draft starts.
- A copied invite link must always reopen the same team assignment.
- Team owners do not choose their own team name when joining; the admin has already assigned it.

#### Section C — Draft Format

Admin configures:

- Number of rounds.

Rules:

- Minimum: 1 round.
- Maximum for MVP: 30 rounds.
- One pick per team per round.
- No pick timer.
- Duplicate selections are allowed within the same round.

#### Section D — Roster Requirements

Admin configures minimum or target counts for:

- Centres (`C`).
- Wingers (`W`).
- Flex forwards (`F`).
- Defence (`D`).
- Goalies (`G`).

Requirements:

- Each value is an integer of 0 or greater.
- Display the calculated total roster target.
- Explain that `F` is a flex forward slot filled by a centre or winger.
- Roster requirements guide GM decision-making and display warnings; they do not silently block a pick unless the admin enables strict roster enforcement in a future version.

#### Section E — Scoring Configuration

Scoring categories are grouped into:

- Skaters.
- Defence bonuses.
- Goalies.

For every category, admin can:

- Enable or disable the category.
- Edit its point value.
- Save the configuration.

Initial categories:

##### Skaters

- Goals (`G`).
- Assists (`A`).
- Plus/minus (`+/-`).
- Penalty minutes (`PIM`).
- Short-handed goals (`SHG`).
- Shootout goals (`SHOG`).

##### Defence Bonus

- Defence goals bonus (`DG`).
- Defence assists bonus (`DA`).

##### Goalies

- Wins (`W`).
- Goals against (`GA`).
- Saves (`S`).
- Overtime losses (`OL`).
- Shootout losses (`SHOL`).
- Shutouts (`SO`).

Requirements:

- Values may be positive, zero, negative, or decimal.
- Disabled categories contribute zero projected points.
- Player projected fantasy points must recalculate using the saved scoring configuration.
- `Save Scoring` must provide visible success feedback.
- Unsaved changes must be indicated.
- Starting the draft must save all valid setup changes first.

### 4.3 Setup Completion

Primary action:

- `Review Draft Setup`

Review screen summarizes:

- Draft name.
- Teams and invitation status.
- Admin's assigned team.
- Number of rounds.
- Roster requirements.
- Enabled scoring categories and values.

Final action:

- `Start Draft`

Start confirmation must warn that team structure and scoring cannot be changed during the MVP draft.

## 5. Shared Draft Room Shell

Admin and GM draft rooms must share the same core visual structure.

### Header

Display:

- Back/leave control.
- Draft name.
- Team name or `Admin` role.
- Room code as secondary information.
- Current draft status.

### Draft Summary

Display:

- Current round and total rounds.
- Current phase: `Waiting`, `Picking`, or `Revealed`.
- Teams submitted count.
- Players remaining count.

### Navigation

Provide tabs or clearly separated views for:

- `Draft` — current round and player selection.
- `My Roster` — drafted players and roster requirements.
- `Results` — prior revealed rounds.

On small screens these must remain easy to reach without horizontal overflow.

## 6. GM Player Selection Experience

### 6.1 Waiting for Round

Before admin starts a round, display:

- `Waiting for the commissioner to start Round X`.
- Current roster summary.
- Previous round results when available.

Do not show an active Submit button.

### 6.2 Open Round

When the round opens, display:

- Clear `Round X is open` status.
- Search input.
- Position filters: `All`, `C`, `LW`, `RW`, `D`, `G`.
- Sort controls: projected points, player name, NHL team, position.
- Available player count.

Each player row/card must show:

- Headshot.
- Player name.
- NHL team.
- Position.
- Relevant projected stat line.
- Calculated projected fantasy points using room scoring.
- Selected state.

### 6.3 Selection Review

Selecting a player must not immediately submit the pick.

Display a persistent review panel or bottom sheet containing:

- Selected player's headshot.
- Name, NHL team, and position.
- Projected fantasy points.
- Key projected stats.
- Impact on roster requirements.
- `Change Selection` action.
- `Submit Sealed Pick` action.

### 6.4 Submitted State

After submit:

- Hide or lock the player browser.
- Display `Pick sealed` confirmation.
- Display the selected player only to that GM and the admin's own GM view.
- Other GMs and the admin commissioner status list must not see the player before reveal.
- Show which teams have submitted only as status—not pick values.

## 7. Admin Draft Experience

The admin must not have to use a separate, inferior picking control.

### 7.1 Admin Dual Role

The admin room contains:

- Commissioner controls.
- The same GM Draft, My Roster, and Results views used by invited GMs.
- The admin's assigned team and sealed-pick flow.

Admin's own pick follows the same round rules and secrecy as every other team's pick.

### 7.2 Commissioner Round Controls

Before a round:

- `Start Round X` action.

During submission:

- Team list with `Waiting` or `Submitted` statuses.
- Submitted count.
- Admin's own team indicated with `You`.
- `Reveal Picks` action.

Reveal behavior:

- If not every team has submitted, opening Reveal must show a confirmation warning naming the missing teams.
- Reveal must make every submitted pick visible simultaneously.
- Teams with no pick receive no player that round.

After reveal:

- Results grouped by team.
- Duplicate player selections clearly supported and displayed.
- Unique set of selected players removed from next round's available pool.
- `Start Next Round` action.
- If the configured final round is complete, show `Finish Draft` instead.

## 8. Reveal and Results Experience

A revealed round must display:

- Round number.
- Each team and selected player.
- Headshot, position, NHL team, and projected fantasy points.
- Duplicate selections without treating them as errors.
- Teams that did not submit marked `No Pick`.

After reveal:

- Every team's roster updates.
- Every selected player becomes unavailable in future rounds.
- Previous round results remain accessible.

## 9. Roster Experience

For each team, display:

- Drafted player list.
- Projected total fantasy points.
- Position counts versus configured requirements.
- Requirement states: unmet, met, or exceeded.

The UI should provide guidance such as:

- `Need 1 more goalie`.
- `Winger requirement complete`.

Do not misrepresent LW and RW as each separately requiring the combined W value. Winger requirement must use `LW + RW`.

## 10. Leave and Re-entry UX

Every draft screen must include `Leave Room`.

Behavior:

- GM Leave Room navigates to a simple landing state explaining that the invite link can be reopened.
- Admin Leave Room navigates to the draft setup/home screen without deleting the draft.
- Leaving must not erase team assignment, picks, or draft progress.
- Reopening the invite link restores the correct team.

## 11. Persistence and Real-Time Requirements

For the weekend MVP:

- Draft state must be stored on the server, not only in browser state.
- Draft data must survive page reloads and server restarts.
- Multiple devices must see shared state updates.
- Polling every 2–3 seconds is acceptable for the MVP.

Persist:

- Draft name.
- Room and admin tokens.
- Team names, emails, and invite tokens.
- Admin team assignment.
- Draft configuration.
- Roster requirements.
- Scoring configuration.
- Rounds and phase status.
- Sealed picks.
- Revealed picks.
- Final rosters.

Deployment requirement:

- Production persistence must use a durable shared database. Local JSON persistence is development-only and is not safe for serverless or multi-instance deployment.

Recommended MVP production architecture:

- Next.js UI and API.
- Existing Railway PostgreSQL database for durable draft state.
- Polling for shared-state refresh.
- Email delivery through a transactional provider such as Resend, with copy-link fallback.

## 12. Privacy and Security Requirements

- Team invite tokens must be unguessable.
- Admin token must never be exposed in GM responses.
- A GM token must only grant access to its assigned team.
- Before reveal, one GM cannot retrieve another team's selected player.
- Admin status responses may indicate submission state before reveal, but must not include sealed player IDs or names.
- Mutating setup and commissioner actions require the admin token.
- Pick submission requires the team's invite/session token.

## 13. Responsive Design Requirements

### Mobile

- Single-column layout.
- Sticky or easily reachable primary action.
- Selection review uses a bottom sheet or sticky panel.
- Player rows remain compact and readable.
- Touch targets are at least 44px.

### Desktop / Laptop

- Two-column draft workspace:
  - Main area: player browser and round results.
  - Side rail: selected player, roster status, and commissioner controls.
- Maximum readable content width while allowing dense player tables.
- No stretched phone layout centered on a large blank desktop screen.

## 14. Visual Requirements

Follow the FantasySnipe visual language:

- Deep navy background.
- Elevated blue-black cards.
- Cyan primary accent.
- Green success, amber warning, and red destructive states.
- Compact data-dense player rows.
- Player headshots and position badges.
- Strong numeric hierarchy for projections and scoring.
- Consistent 14px card radius.
- Clear status pills.
- Avoid oversized empty cards and unnecessary whitespace.

## 15. MVP Non-Goals

Not required for the weekend MVP:

- Full user accounts/password authentication.
- Chat.
- Trades.
- Automated roster optimization.
- Auction bidding.
- Pick clock.
- Push notifications.
- Commissioner override/edit history beyond basic round controls.

## 16. Acceptance Criteria

The MVP is acceptable when:

1. Admin creates a named draft.
2. Admin creates all teams and designates their own team.
3. Every team has a unique invite link.
4. A GM opens their link and reaches the correct assigned team on mobile or laptop.
5. Admin configures rounds, roster requirements, and scoring.
6. Admin starts a round.
7. Every GM and the admin can select and submit one sealed player.
8. Two or more teams can select the same player in the same round.
9. Before reveal, nobody can see another team's selected player.
10. Admin sees which teams have submitted.
11. Admin reveals the round.
12. Every submitted team receives its selected player.
13. Revealed selected players disappear from the next round's player pool.
14. Admin starts the next round.
15. All users can view roster requirements, projections, and prior results.
16. Users can leave and re-enter without losing state.
17. State survives browser refresh and server restart.
18. The experience is usable on both phone and laptop.
