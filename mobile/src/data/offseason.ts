// Mock data for the UHHP 2026 Offseason. Replace with Railway API calls later.

import type { SkaterPosition } from "./types";
import { DRAFT_ORDER, MY_DRAFT_TEAM_ID, type DraftTeam } from "./rookieDraft";

// NHL headshots use the official NHL CDN pattern.
const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export type OffseasonStepId =
  | "buyouts"
  | "rookies"
  | "entry-draft"
  | "superstar"
  | "ufa"
  | "rfa"
  | "finalize";

export interface OffseasonStep {
  id: OffseasonStepId;
  label: string;
}

export const OFFSEASON_YEAR = 2026;

/** Buyout deadline — after this, remaining teams auto-flip to No Buyouts. */
export const BUYOUT_DEADLINE = new Date("2026-06-15T23:59:59-04:00");

/** The 12 UHHP franchises. */
export const LEAGUE_TEAMS: DraftTeam[] = DRAFT_ORDER;
/** The signed-in manager's franchise. */
export const MY_TEAM_ID = MY_DRAFT_TEAM_ID;

/**
 * Mock league-wide buyout status. The signed-in GM's team is derived from
 * live state (completed the Buyouts stage) instead of this map.
 */
export const TEAM_BUYOUT_STATUS: Record<string, "done" | "in_progress"> = {
  pylons: "in_progress", // overridden by live state
  basteerds: "done",
  "oilers-nation": "done",
  doomsday: "in_progress",
  "ice-holes": "done",
  slapshot: "done",
  "litter-box": "in_progress",
  "northern-curse": "done",
  misconducts: "done",
  "greasy-mitts": "done",
  "knights-ni": "done",
  "kitten-mittons": "in_progress",
};

/** Per-position player counts + total cap salary for each franchise. */
export interface TeamRosterSnapshot {
  C: number;
  W: number;
  F: number;
  D: number;
  G: number;
  IR: number;
  /** Total cap salary in units (cap = 100). */
  salary: number;
}

export const TEAM_ROSTER_SNAPSHOTS: Record<string, TeamRosterSnapshot> = {
  pylons: { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 94 },
  basteerds: { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 91 },
  "oilers-nation": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 96 },
  doomsday: { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 88 },
  "ice-holes": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 99 },
  slapshot: { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 85 },
  "litter-box": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 93 },
  "northern-curse": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 90 },
  misconducts: { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 97 },
  "greasy-mitts": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 83 },
  "knights-ni": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 98 },
  "kitten-mittons": { C: 2, W: 3, F: 4, D: 6, G: 3, IR: 2, salary: 92 },
};

/** A single buyout submitted by a GM. */
export interface BuyoutSubmission {
  id: string;
  playerName: string;
  position: string;
  salary: number;
  yearsRemaining: number;
  cashCost: number;
  capHit: number;
}

/**
 * Mock buyout submissions per team. The user's own team (pylons) is populated
 * from the in-memory store; the rest are mock data for the admin review tab.
 */
export const TEAM_BUYOUT_SUBMISSIONS: Record<string, BuyoutSubmission[]> = {
  basteerds: [
    { id: "s1", playerName: "John Carlson", position: "D", salary: 8, yearsRemaining: 2, cashCost: 16, capHit: 4 },
    { id: "s2", playerName: "Blake Wheeler", position: "RW", salary: 6, yearsRemaining: 2, cashCost: 12, capHit: 3 },
  ],
  "oilers-nation": [
    { id: "s3", playerName: "Corey Perry", position: "RW", salary: 3, yearsRemaining: 1, cashCost: 3, capHit: 2 },
  ],
  "ice-holes": [
    { id: "s4", playerName: "Brayden Schenn", position: "C", salary: 7, yearsRemaining: 2, cashCost: 14, capHit: 4 },
    { id: "s5", playerName: "Marc-Édouard Vlasic", position: "D", salary: 4, yearsRemaining: 1, cashCost: 4, capHit: 2 },
    { id: "s6", playerName: "Ryan Johansen", position: "C", salary: 5, yearsRemaining: 1, cashCost: 5, capHit: 3 },
  ],
  slapshot: [
    { id: "s7", playerName: "Jonathan Huberdeau", position: "LW", salary: 6, yearsRemaining: 3, cashCost: 18, capHit: 3 },
  ],
  "northern-curse": [
    { id: "s8", playerName: "Matt Duchene", position: "C", salary: 4, yearsRemaining: 2, cashCost: 8, capHit: 2 },
  ],
  misconducts: [
    { id: "s9", playerName: "Ryan Johansen", position: "C", salary: 5, yearsRemaining: 1, cashCost: 5, capHit: 3 },
    { id: "s10", playerName: "Corey Perry", position: "RW", salary: 3, yearsRemaining: 1, cashCost: 3, capHit: 2 },
  ],
  "greasy-mitts": [
    { id: "s11", playerName: "Brayden Schenn", position: "C", salary: 7, yearsRemaining: 2, cashCost: 14, capHit: 4 },
    { id: "s12", playerName: "Marc-Édouard Vlasic", position: "D", salary: 4, yearsRemaining: 1, cashCost: 4, capHit: 2 },
    { id: "s13", playerName: "Blake Wheeler", position: "RW", salary: 6, yearsRemaining: 2, cashCost: 12, capHit: 3 },
  ],
  "knights-ni": [
    { id: "s14", playerName: "Jonathan Huberdeau", position: "LW", salary: 6, yearsRemaining: 3, cashCost: 18, capHit: 3 },
  ],
};

/** Admin warnings about submitted buyouts — shown below the teams list. */
export interface BuyoutWarning {
  teamId: string;
  level: "high" | "info";
  message: string;
}

export const BUYOUT_WARNINGS: BuyoutWarning[] = [
  {
    teamId: "ice-holes",
    level: "high",
    message:
      "3 buyouts ($23 cash) · $9 cap hit next season. Buyout pool at $72 — distribution pending.",
  },
  {
    teamId: "greasy-mitts",
    level: "high",
    message:
      "3 buyouts ($30 cash) · $9 cap hit next season. Buyout pool at $102 — distribution pending.",
  },
  {
    teamId: "knights-ni",
    level: "info",
    message:
      "1 buyout ($18 cash) · Jonathan Huberdeau bought out with 3 years remaining.",
  },
  {
    teamId: "northern-curse",
    level: "info",
    message:
      "1 buyout ($8 cash) · Matt Duchene bought out with 2 years remaining.",
  },
];

export const OFFSEASON_STEPS: OffseasonStep[] = [
  { id: "buyouts", label: "Buyouts" },
  { id: "rookies", label: "Rookie Draft" },
  { id: "entry-draft", label: "Entry Draft" },
  { id: "superstar", label: "Superstar" },
  { id: "ufa", label: "UFA" },
  { id: "rfa", label: "RFA" },
  { id: "finalize", label: "Finalize" },
];

export const BUYOUT_INFO = {
  title: "1. Buyouts",
  subtitle: "Buyout contracted players before the draft.",
  description:
    "There is no limit to the number of players you may buyout. The buyout cost is paid in real cash and a reduced cap hit applies next season.",
  dates: [
    { label: "Buyout Window", value: "Jun 1 – Jun 15, 2026" },
    { label: "Payment Due", value: "Jun 16, 2026" },
    { label: "Next Step", value: "Rookie Decisions" },
  ],
};

export const TEAM_CAP = {
  used: 94,
  total: 100,
  players: 24,
  expiring: 3,
  buyoutCandidates: 2,
};

export type BuyoutPosition = SkaterPosition | "G";
export type BuyoutGroup = "All" | "Forwards" | "Defence" | "Goalies";

export const BUYOUT_GROUPS: BuyoutGroup[] = [
  "All",
  "Forwards",
  "Defence",
  "Goalies",
];

export function groupForPosition(pos: BuyoutPosition): BuyoutGroup {
  if (pos === "G") return "Goalies";
  if (pos === "D") return "Defence";
  return "Forwards";
}

export interface BuyoutCandidate {
  id: string;
  name: string;
  position: BuyoutPosition;
  nhlTeam: string; // abbrev
  nhlTeamName: string;
  age: number;
  salary: number; // units per year
  yearsRemaining: number;
  contractType: string;
  headshotUrl?: string;
}

export const BUYOUT_CANDIDATES: BuyoutCandidate[] = [
  {
    id: "carlson",
    name: "John Carlson",
    position: "D",
    nhlTeam: "WSH",
    nhlTeamName: "Washington Capitals",
    age: 36,
    salary: 8,
    yearsRemaining: 2,
    contractType: "Standard",
    headshotUrl: headshot(8474590),
  },
  {
    id: "schenn",
    name: "Brayden Schenn",
    position: "C",
    nhlTeam: "STL",
    nhlTeamName: "St. Louis Blues",
    age: 34,
    salary: 7,
    yearsRemaining: 2,
    contractType: "Standard",
    headshotUrl: headshot(8475170),
  },
  {
    id: "huberdeau",
    name: "Jonathan Huberdeau",
    position: "LW",
    nhlTeam: "CGY",
    nhlTeamName: "Calgary Flames",
    age: 32,
    salary: 6,
    yearsRemaining: 3,
    contractType: "Standard",
    headshotUrl: headshot(8476456),
  },
  {
    id: "wheeler",
    name: "Blake Wheeler",
    position: "RW",
    nhlTeam: "NYR",
    nhlTeamName: "New York Rangers",
    age: 39,
    salary: 6,
    yearsRemaining: 2,
    contractType: "Standard",
    headshotUrl: headshot(8471218),
  },
  {
    id: "johansen",
    name: "Ryan Johansen",
    position: "C",
    nhlTeam: "COL",
    nhlTeamName: "Colorado Avalanche",
    age: 32,
    salary: 5,
    yearsRemaining: 1,
    contractType: "Standard",
    headshotUrl: headshot(8475793),
  },
  {
    id: "duchene",
    name: "Matt Duchene",
    position: "C",
    nhlTeam: "DAL",
    nhlTeamName: "Dallas Stars",
    age: 33,
    salary: 4,
    yearsRemaining: 2,
    contractType: "Standard",
    headshotUrl: headshot(8475168),
  },
  {
    id: "vlasic",
    name: "Marc-Édouard Vlasic",
    position: "D",
    nhlTeam: "SJS",
    nhlTeamName: "San Jose Sharks",
    age: 39,
    salary: 4,
    yearsRemaining: 1,
    contractType: "Standard",
    headshotUrl: headshot(8471709),
  },
  {
    id: "perry",
    name: "Corey Perry",
    position: "RW",
    nhlTeam: "EDM",
    nhlTeamName: "Edmonton Oilers",
    age: 40,
    salary: 3,
    yearsRemaining: 1,
    contractType: "Standard",
    headshotUrl: headshot(8470621),
  },
];

export interface BuyoutMath {
  cashCost: number; // real money
  capHit: number; // units
  capYears: number;
  capWindow: string; // e.g. "2026–27"
}

/** UHHP buyout formula: cash = salary × years; cap hit = salary ÷ 2 for 1 year. */
export function buyoutMath(p: BuyoutCandidate): BuyoutMath {
  const cashCost = p.salary * p.yearsRemaining;
  const capHit = p.salary / 2;
  return {
    cashCost,
    capHit,
    capYears: 1,
    capWindow: "2026–27",
  };
}

export const BUYOUT_WHATS_NEXT = (p: BuyoutCandidate, m: BuyoutMath) => [
  "Player is released immediately",
  `$${m.cashCost} payment is due by Jun 16, 2026`,
  `${m.capHit} unit cap hit applies for 1 year (${m.capWindow})`,
  "Player becomes a free agent",
];

export const BUYOUT_NEXT_STEPS = [
  "Review your roster for additional buyouts",
  "Proceed to Rookie Decisions",
  "Ensure payment is made by Jun 16, 2026",
];

export const BUYOUT_RULES: string[] = [
  "Buyout window runs Jun 1 – Jun 15, 2026",
  "No limit to the number of players you may buy out",
  "Buyout cost is paid in real cash: salary × years remaining",
  "A reduced cap hit (salary ÷ 2) applies for 1 year",
  "Bought-out players are released immediately and become UFAs",
  "Cash payments fund the league buyout pool for end-of-season payouts",
];

export interface OffseasonStepDetail {
  title: string;
  window: string;
  description: string;
  bullets: string[];
  /** Deep-link to the tool for this stage (shown as a CTA on the step screen). */
  action?: { label: string; route: string };
  /** Secondary "skip" option for the stage (e.g. "No Buyouts this season"). */
  skip?: { label: string };
}

export const OFFSEASON_STEP_DETAILS: Record<string, OffseasonStepDetail> = {
  buyouts: {
    title: "Buyouts",
    window: "Jun 1 – Jun 15, 2026",
    description:
      "Buy out contracted players before the draft. There is no limit to how many you may buy out.",
    bullets: [
      "Buyout cost is real cash: salary × years remaining",
      "Cap hit (salary ÷ 2, rounded up) applies for 1 year",
      "Bought-out players are released and become UFAs",
    ],
    action: { label: "Start Stage", route: "/offseason/buyout-teams" },
  },
  rookies: {
    title: "Rookie Decisions",
    window: "Jun 16 – Jun 20, 2026",
    description:
      "Sign your drafted rookies and decide who moves to the prospect roster or the active roster.",
    bullets: [
      "Sign rookies to entry-level contracts",
      "Move rookies to prospect roster or active roster",
      "Unsigned rookies after 3 years become UFAs",
    ],
    action: { label: "Start Stage", route: "/rookie-draft" },
  },
  "entry-draft": {
    title: "Entry Draft",
    window: "Jun 22, 2026 · 8:00 PM",
    description:
      "The 2026 Entry Draft. Single round, 60 seconds per pick. Only 2026 NHL Entry Draft players are eligible.",
    bullets: [
      "Single round, reverse order of standings",
      "12 total picks",
      "Rookies join your prospect roster",
    ],
    action: { label: "Open Rookie Draft", route: "/rookie-draft" },
  },
  superstar: {
    title: "Superstar Tag",
    window: "Jun 25 – Jun 30, 2026",
    description:
      "Designate one franchise superstar for a contract extension before free agency opens.",
    bullets: [
      "One superstar tag per team",
      "Tagged player can be extended up to 7 years",
      "Tag cannot be used on a player entering UFA",
    ],
  },
  ufa: {
    title: "UFA Auction",
    window: "Jul 1 – Jul 15, 2026",
    description:
      "Unrestricted free agency. Round-robin nominations with open bidding.",
    bullets: [
      "Teams nominate players in round-robin order",
      "Highest bid wins; contract term set at signing",
      "Bids are capped by your available cap room",
    ],
    action: { label: "Open UFA Auction", route: "/auction" },
  },
  rfa: {
    title: "RFA Period",
    window: "Jul 16 – Jul 25, 2026",
    description:
      "Extend qualifying offers and match offer sheets for restricted free agents.",
    bullets: [
      "Qualifying offers due by Jul 16",
      "Match any offer sheet within 48 hours",
      "Unmatched RFAs join the signing team",
    ],
  },
  finalize: {
    title: "Finalize Roster",
    window: "Jul 31, 2026",
    description:
      "Lock your roster, cap, and contracts for the start of the season.",
    bullets: [
      "Rosters lock at 25 players",
      "Cap compliance verified automatically",
      "Season begins Aug 1",
    ],
    action: { label: "View Team Cap", route: "/franchise" },
  },
};
