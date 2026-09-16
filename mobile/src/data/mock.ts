// Mock data matching the design mocks. Replace with Railway API calls later.

import type { League, LineupSummary, Player, Position, RosterSlot } from "./types";

// NHL headshots use the official NHL CDN pattern.
const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export const MY_LEAGUE: League = {
  id: "tacocorp",
  name: "TacoCorp",
  sport: "Dynasty Hockey",
  myTeam: {
    id: "harbour-ice",
    name: "Harbour Ice",
    abbrev: "HAR",
    record: { w: 0, l: 0 },
    division: "Silver Division",
  },
};

export const WEEK_DAYS = [
  { label: "Mon", date: "Oct 7" },
  { label: "Tue", date: "Oct 8" },
  { label: "Wed", date: "Oct 9" },
  { label: "Thu", date: "Oct 10" },
  { label: "Fri", date: "Oct 11" },
  { label: "Sat", date: "Oct 12" },
  { label: "Sun", date: "Oct 13" },
];

export const LINEUP_SUMMARY: LineupSummary = {
  scheduledStarts: 31,
  benchConflicts: 2,
  emptyOpportunities: 3,
};

const skaters: Player[] = [
  { id: "mcdavid", name: "C. McDavid", team: "EDM", position: "C", headshotUrl: headshot(8478402), opponent: "vs VAN", projectedPoints: 18.4, gameDays: [1, 3, 5], capHit: "$12.5M", contractYears: 3, contractType: "UFA", goals: 12, assists: 28, points: 40, plusMinus: 15, sog: 98, hits: 22, blk: 8 },
  { id: "matthews", name: "A. Matthews", team: "TOR", position: "C", headshotUrl: headshot(8479318), opponent: "vs MTL", projectedPoints: 17.2, gameDays: [0, 2, 4, 6], capHit: "$11.6M", contractYears: 2, contractType: "UFA", goals: 18, assists: 14, points: 32, plusMinus: 8, sog: 112, hits: 18, blk: 5 },
  { id: "kaprizov", name: "K. Kaprizov", team: "MIN", position: "LW", headshotUrl: headshot(8478864), opponent: "@ COL", projectedPoints: 15.6, gameDays: [1, 4, 6], capHit: "$9.0M", contractYears: 4, contractType: "UFA", goals: 10, assists: 20, points: 30, plusMinus: 12, sog: 85, hits: 15, blk: 6 },
  { id: "tkachuk", name: "B. Tkachuk", team: "OTT", position: "LW", headshotUrl: headshot(8480801), opponent: "@ BOS", projectedPoints: 14.1, gameDays: [0, 3, 5], capHit: "$8.2M", contractYears: 5, contractType: "UFA", goals: 8, assists: 16, points: 24, plusMinus: 6, sog: 72, hits: 68, blk: 4 },
  { id: "kucherov", name: "N. Kucherov", team: "TB", position: "RW", headshotUrl: headshot(8476453), opponent: "vs FLA", projectedPoints: 16.8, gameDays: [1, 3, 5], capHit: "$9.5M", contractYears: 3, contractType: "UFA", goals: 11, assists: 24, points: 35, plusMinus: 10, sog: 78, hits: 12, blk: 3 },
  { id: "rantanen", name: "M. Rantanen", team: "COL", position: "RW", headshotUrl: headshot(8478420), opponent: "vs MIN", projectedPoints: 15.3, gameDays: [0, 2, 5], capHit: "$9.3M", contractYears: 2, contractType: "UFA", goals: 9, assists: 19, points: 28, plusMinus: 11, sog: 82, hits: 20, blk: 5 },
  { id: "hughes", name: "Q. Hughes", team: "VAN", position: "D", headshotUrl: headshot(8480800), opponent: "@ EDM", projectedPoints: 13.6, gameDays: [1, 3, 5], capHit: "$7.9M", contractYears: 4, contractType: "UFA", goals: 3, assists: 22, points: 25, plusMinus: 14, sog: 65, hits: 8, blk: 18 },
  { id: "makar", name: "D. Makar", team: "COL", position: "D", headshotUrl: headshot(8480069), opponent: "vs MIN", projectedPoints: 14.9, gameDays: [0, 2, 5], capHit: "$9.0M", contractYears: 3, contractType: "UFA", goals: 5, assists: 20, points: 25, plusMinus: 13, sog: 70, hits: 10, blk: 22 },
];

const goalies: Player[] = [
  { id: "bobrovsky", name: "S. Bobrovsky", team: "FLA", position: "G", headshotUrl: headshot(8475683), opponent: "vs TB", projectedPoints: 16.9, gameDays: [1, 3, 5], goalieDays: ["start", "sit", "start"], projectedStarts: 2, startProbability: 92, capHit: "$10.0M", contractYears: 2, contractType: "UFA", wins: 8, gaa: 2.35, svPct: 0.918 },
  { id: "oettinger", name: "J. Oettinger", team: "DAL", position: "G", headshotUrl: headshot(8479979), opponent: "@ NSH", projectedPoints: 15.4, gameDays: [0, 2, 4], goalieDays: ["sit", "start", "sit"], projectedStarts: 1, startProbability: 78, capHit: "$8.3M", contractYears: 5, contractType: "UFA", wins: 6, gaa: 2.52, svPct: 0.912 },
];

const bench: Player[] = [
  { id: "point", name: "B. Point", team: "TB", position: "BN", headshotUrl: headshot(8478010), opponent: "vs FLA", projectedPoints: 13.8, gameDays: [1, 3, 5], capHit: "$9.5M", contractYears: 3, contractType: "UFA", goals: 7, assists: 15, points: 22, plusMinus: 5, sog: 58, hits: 14, blk: 6 },
];

export interface RosterGroups {
  skaters: RosterSlot[];
  goalies: RosterSlot[];
  bench: RosterSlot[];
}

export const ROSTER: RosterGroups = {
  skaters: skaters.map((p) => ({ slot: p.position, player: p })),
  goalies: goalies.map((p, i) => ({ slot: `G${i + 1}` as Player["position"], player: p })),
  bench: bench.map((p) => ({ slot: "BN" as const, player: p })),
};

// --- Players / waiver wire ---
export interface AvailablePlayer {
  id: string;
  name: string;
  team: string;
  position: Position;
  headshotUrl?: string;
  opponent?: string;
  gameTime?: string;
  projectedPoints: number;
  rosteredPct: number;
  trendPct?: number; // e.g. +14
  playingToday?: boolean;
  status?: "available" | "waivers";
}

export const WAIVER_INFO = {
  /** ISO timestamp of when waivers clear (UTC) */
  clearsAt: "2025-10-09T04:05:00Z",
  faabRemaining: 37,
  faabBudget: 100,
  waiverPriority: 4,
  waiverPriorityTotal: 8,
};

export const AVAILABLE_PLAYERS: AvailablePlayer[] = [
  { id: "bedard", name: "Connor Bedard", team: "CHI", position: "C", headshotUrl: headshot(8484145), opponent: "vs BUF", gameTime: "5:00 PM", projectedPoints: 16.8, rosteredPct: 34, playingToday: true, status: "available" },
  { id: "mtkachuk", name: "Matthew Tkachuk", team: "FLA", position: "LW", headshotUrl: headshot(8479314), opponent: "vs TB", gameTime: "4:00 PM", projectedPoints: 15.2, rosteredPct: 42, playingToday: true, status: "available" },
  { id: "mikko", name: "Mikko Rantanen", team: "COL", position: "RW", headshotUrl: headshot(8478420), opponent: "@ MIN", gameTime: "5:00 PM", projectedPoints: 14.7, rosteredPct: 38, playingToday: true, status: "available" },
  { id: "qhughes", name: "Quinn Hughes", team: "VAN", position: "D", headshotUrl: headshot(8480800), opponent: "@ EDM", gameTime: "7:00 PM", projectedPoints: 16.4, rosteredPct: 28, playingToday: true, status: "available" },
  { id: "montembeault", name: "Samuel Montembeault", team: "MTL", position: "G", headshotUrl: headshot(8478470), opponent: "vs TOR", gameTime: "4:00 PM", projectedPoints: 13.1, rosteredPct: 27, playingToday: true, status: "waivers" },
  { id: "sorokin", name: "Ilya Sorokin", team: "NYI", position: "G", headshotUrl: headshot(8479360), opponent: "@ PIT", gameTime: "4:00 PM", projectedPoints: 12.8, rosteredPct: 31, playingToday: true, status: "waivers" },
  { id: "boldy", name: "Matt Boldy", team: "MIN", position: "LW", headshotUrl: headshot(8481557), opponent: "vs COL", gameTime: "5:00 PM", projectedPoints: 14.1, rosteredPct: 42, trendPct: 8, playingToday: true, status: "available" },
  { id: "vlasic", name: "Alex Vlasic", team: "CHI", position: "D", headshotUrl: headshot(8481563), opponent: "vs BUF", gameTime: "5:00 PM", projectedPoints: 11.8, rosteredPct: 36, trendPct: 10, playingToday: true, status: "available" },
  { id: "jarry", name: "Tristan Jarry", team: "PIT", position: "G", headshotUrl: headshot(8477465), opponent: "vs NYI", gameTime: "4:00 PM", projectedPoints: 10.6, rosteredPct: 24, trendPct: 5, playingToday: true, status: "waivers" },
];

// --- Submitted waiver claims ---

export interface SubmittedClaim {
  id: string;
  player: AvailablePlayer;
  bidAmount: number;
  dropPlayer?: AvailablePlayer;
  submittedAt: string; // ISO timestamp
  status: "pending" | "won" | "lost";
}

export const SUBMITTED_CLAIMS: SubmittedClaim[] = [
  {
    id: "sc1",
    player: { id: "montembeault", name: "Samuel Montembeault", team: "MTL", position: "G", headshotUrl: headshot(8478470), projectedPoints: 13.1, rosteredPct: 27, playingToday: true, status: "waivers" },
    bidAmount: 12,
    dropPlayer: { id: "thompson", name: "Logan Thompson", team: "WSH", position: "G", headshotUrl: headshot(8480312), projectedPoints: 11.9, rosteredPct: 100, status: "available" },
    submittedAt: "2025-10-07T18:30:00Z",
    status: "pending",
  },
  {
    id: "sc2",
    player: { id: "boldy", name: "Matt Boldy", team: "MIN", position: "LW", headshotUrl: headshot(8481557), projectedPoints: 14.1, rosteredPct: 42, playingToday: true, status: "available" },
    bidAmount: 5,
    submittedAt: "2025-10-06T14:20:00Z",
    status: "pending",
  },
];

// --- Add/Drop flow ---
/** My current roster players eligible to drop (skaters + goalies + bench). */
export const DROPPABLE_PLAYERS: AvailablePlayer[] = [
  { id: "barkov", name: "Aleksander Barkov", team: "FLA", position: "C", headshotUrl: headshot(8477492), projectedPoints: 18.2, rosteredPct: 100, status: "available" },
  { id: "guentzel", name: "Jake Guentzel", team: "TB", position: "LW", headshotUrl: headshot(8477404), projectedPoints: 14.6, rosteredPct: 100, status: "available" },
  { id: "pastrnak", name: "David Pastrnak", team: "BOS", position: "RW", headshotUrl: headshot(8477956), projectedPoints: 17.1, rosteredPct: 100, status: "available" },
  { id: "dahlin", name: "Rasmus Dahlin", team: "BUF", position: "D", headshotUrl: headshot(8480839), projectedPoints: 16.8, rosteredPct: 100, status: "available" },
  { id: "thompson", name: "Logan Thompson", team: "WSH", position: "G", headshotUrl: headshot(8480312), projectedPoints: 11.9, rosteredPct: 100, status: "available" },
];

// --- Player Detail ---
export interface GoalieOutlook {
  expectedStarter: string;
  confirmed: string;
  backToBack: string;
  oppGoalRank: string;
  oppXg: string;
  gameTotal: string;
  projectionFp: string;
}

export interface RecentGoalieStart {
  date: string;
  opp: string;
  result: string;
  ga: number;
  sog: number;
  sv: number;
  svPct: string;
  fp: number;
}

export interface RecentSkaterGame {
  date: string;
  opp: string;
  g: number;
  a: number;
  plusMinus: string;
  sog: number;
  hits: number;
  blk: number;
  fp: number;
}

export interface ScheduleGame {
  day: string;
  date: string;
  opp: string;
  status?: "likely" | "expected" | "tbd";
}

export interface StatCell {
  label: string;
  value: string;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  ago: string;
  imageUrl?: string;
}

export interface PlayerDetail {
  id: string;
  kind: "skater" | "goalie";
  name: string;
  team: string;
  position: string;
  number: number;
  headshotUrl?: string;
  rosteredPct: number;
  startedPct: number;
  // game card
  gameLabel: string; // "Today's Game" | "Next Game"
  gameDate: string;
  gameTime: string;
  homeAway: "@" | "vs";
  oppTeam: string;
  oppRecord: string;
  myRecord: string;
  projPoints: number;
  // skater-only matchup ranks
  matchupRanks?: { label: string; value: string; bad?: boolean }[];
  // goalie-only
  startProbability?: number; // 0-100
  startStatusPill?: "Likely Start" | "Expected" | "TBD";
  goalieOutlook?: GoalieOutlook;
  // skater-only line role
  lineRole?: { label: string; value: string }[];
  // shared
  weekGames: ScheduleGame[];
  recentGoalieStarts?: RecentGoalieStart[];
  recentSkaterGames?: RecentSkaterGame[];
  seasonStats: StatCell[];
  news: NewsItem[];
}

const TSN = "https://a.espncdn.com/i/teamlogos/nhl/500/tor.png";

export const PLAYER_DETAILS: Record<string, PlayerDetail> = {
  bedard: {
    id: "bedard",
    kind: "skater",
    name: "Connor Bedard",
    team: "CHI",
    position: "C",
    number: 98,
    headshotUrl: headshot(8484145),
    rosteredPct: 34,
    startedPct: 22,
    gameLabel: "Today's Game",
    gameDate: "Tue, Oct 8",
    gameTime: "5:00 PM",
    homeAway: "vs",
    oppTeam: "BUF",
    oppRecord: "(1-2-0)",
    myRecord: "(1-2-0)",
    projPoints: 4.8,
    matchupRanks: [
      { label: "GAA", value: "18th", bad: false },
      { label: "PK", value: "22nd", bad: true },
      { label: "GF", value: "20th", bad: true },
    ],
    lineRole: [
      { label: "Line", value: "L1 Center" },
      { label: "LW", value: "T. Bertuzzi" },
      { label: "RW", value: "R. Donato" },
      { label: "Power Play", value: "PP1 (Center)" },
    ],
    weekGames: [
      { day: "Tue", date: "Oct 8", opp: "vs BUF" },
      { day: "Thu", date: "Oct 10", opp: "@ STL" },
      { day: "Sat", date: "Oct 12", opp: "vs WPG" },
    ],
    recentSkaterGames: [
      { date: "Oct 5", opp: "vs NSH", g: 1, a: 1, plusMinus: "+1", sog: 4, hits: 0, blk: 0, fp: 6.8 },
      { date: "Oct 3", opp: "@ COL", g: 0, a: 2, plusMinus: "0", sog: 3, hits: 1, blk: 0, fp: 5.1 },
      { date: "Oct 1", opp: "vs MIN", g: 1, a: 0, plusMinus: "-1", sog: 5, hits: 0, blk: 1, fp: 5.4 },
      { date: "Sep 28", opp: "@ DAL", g: 0, a: 1, plusMinus: "+2", sog: 2, hits: 1, blk: 0, fp: 4.2 },
    ],
    seasonStats: [
      { label: "GP", value: "68" },
      { label: "G", value: "22" },
      { label: "A", value: "39" },
      { label: "+/-", value: "-8" },
      { label: "SOG", value: "204" },
      { label: "PPP", value: "18" },
      { label: "FP/G", value: "4.1" },
    ],
    news: [
      { id: "n1", title: "Bedard building chemistry with new linemates", source: "The Athletic", ago: "4h ago", imageUrl: TSN },
      { id: "n2", title: "Blackhawks lean on Bedard for offensive spark", source: "TSN", ago: "1d ago", imageUrl: TSN },
    ],
  },
  matthews: {
    id: "matthews",
    kind: "skater",
    name: "Auston Matthews",
    team: "TOR",
    position: "C",
    number: 34,
    headshotUrl: headshot(8479318),
    rosteredPct: 100,
    startedPct: 98,
    gameLabel: "Today's Game",
    gameDate: "Tue, Oct 8",
    gameTime: "7:00 PM",
    homeAway: "@",
    oppTeam: "FLA",
    oppRecord: "(3-0-0)",
    myRecord: "(2-1-0)",
    projPoints: 5.2,
    matchupRanks: [
      { label: "GAA", value: "28th", bad: true },
      { label: "PK", value: "30th", bad: true },
      { label: "GF", value: "26th", bad: true },
    ],
    lineRole: [
      { label: "Line", value: "L1 Center" },
      { label: "LW", value: "M. Marner" },
      { label: "RW", value: "W. Nylander" },
      { label: "Power Play", value: "PP1 (Center)" },
    ],
    weekGames: [
      { day: "Tue", date: "Oct 8", opp: "@ FLA" },
      { day: "Thu", date: "Oct 10", opp: "vs CBJ" },
      { day: "Sat", date: "Oct 12", opp: "vs DET" },
      { day: "Mon", date: "Oct 14", opp: "@ TBL" },
    ],
    recentSkaterGames: [
      { date: "Oct 5", opp: "vs MTL", g: 1, a: 1, plusMinus: "+2", sog: 5, hits: 1, blk: 0, fp: 7.8 },
      { date: "Oct 3", opp: "vs OTT", g: 0, a: 2, plusMinus: "+1", sog: 4, hits: 0, blk: 1, fp: 6.1 },
      { date: "Oct 1", opp: "@ BUF", g: 1, a: 0, plusMinus: "+1", sog: 6, hits: 2, blk: 0, fp: 6.4 },
      { date: "Sep 28", opp: "@ DET", g: 0, a: 1, plusMinus: "0", sog: 3, hits: 1, blk: 1, fp: 4.2 },
      { date: "Sep 26", opp: "vs BOS", g: 2, a: 0, plusMinus: "+1", sog: 7, hits: 0, blk: 0, fp: 8.1 },
    ],
    seasonStats: [
      { label: "GP", value: "82" },
      { label: "G", value: "69" },
      { label: "A", value: "38" },
      { label: "+/-", value: "+24" },
      { label: "SOG", value: "363" },
      { label: "PPP", value: "32" },
      { label: "FP/G", value: "5.8" },
    ],
    news: [
      { id: "n1", title: "Matthews ready for strong start after offseason training focus", source: "The Athletic", ago: "6h ago", imageUrl: TSN },
      { id: "n2", title: "Maple Leafs confident in Matthews' leadership this season", source: "TSN", ago: "1d ago", imageUrl: TSN },
    ],
  },
  bobrovsky: {
    id: "bobrovsky",
    kind: "goalie",
    name: "Sergei Bobrovsky",
    team: "FLA",
    position: "G",
    number: 72,
    headshotUrl: headshot(8475683),
    rosteredPct: 95,
    startedPct: 78,
    gameLabel: "Today's Game",
    gameDate: "Tue, Oct 8",
    gameTime: "10:00 PM",
    homeAway: "vs",
    oppTeam: "TB",
    oppRecord: "(2-1-0)",
    myRecord: "(3-0-0)",
    projPoints: 13.1,
    startProbability: 92,
    startStatusPill: "Likely Start",
    goalieOutlook: {
      expectedStarter: "Yes",
      confirmed: "Yes",
      backToBack: "No",
      oppGoalRank: "8th",
      oppXg: "2.8",
      gameTotal: "5.5",
      projectionFp: "13.1 FP",
    },
    weekGames: [
      { day: "Tue", date: "Oct 8", opp: "vs TB", status: "likely" },
      { day: "Thu", date: "Oct 10", opp: "@ BOS", status: "expected" },
      { day: "Sat", date: "Oct 12", opp: "vs MTL", status: "expected" },
    ],
    recentGoalieStarts: [
      { date: "Oct 5", opp: "vs CAR", result: "W 3-1", ga: 1, sog: 29, sv: 28, svPct: ".966", fp: 16.2 },
      { date: "Oct 3", opp: "@ NYR", result: "W 4-2", ga: 2, sog: 31, sv: 29, svPct: ".935", fp: 13.8 },
      { date: "Oct 1", opp: "vs DET", result: "L 3-2", ga: 3, sog: 27, sv: 24, svPct: ".889", fp: 7.8 },
    ],
    seasonStats: [
      { label: "GP", value: "58" },
      { label: "W", value: "36" },
      { label: "L", value: "17" },
      { label: "OTL", value: "4" },
      { label: "GAA", value: "2.37" },
      { label: "SV%", value: ".915" },
      { label: "SO", value: "6" },
      { label: "FP/G", value: "12.4" },
    ],
    news: [
      { id: "n1", title: "Bobrovsky confirmed starter vs. Lightning", source: "TSN", ago: "2h ago", imageUrl: TSN },
    ],
  },
  oettinger: {
    id: "oettinger",
    kind: "goalie",
    name: "Jake Oettinger",
    team: "DAL",
    position: "G",
    number: 29,
    headshotUrl: headshot(8479979),
    rosteredPct: 91,
    startedPct: 70,
    gameLabel: "Today's Game",
    gameDate: "Tue, Oct 8",
    gameTime: "8:30 PM",
    homeAway: "@",
    oppTeam: "NSH",
    oppRecord: "(1-2-0)",
    myRecord: "(2-1-0)",
    projPoints: 12.4,
    startProbability: 78,
    startStatusPill: "Likely Start",
    goalieOutlook: {
      expectedStarter: "Yes",
      confirmed: "—",
      backToBack: "No",
      oppGoalRank: "15th",
      oppXg: "2.9",
      gameTotal: "6.0",
      projectionFp: "12.4 FP",
    },
    weekGames: [
      { day: "Mon", date: "Oct 7", opp: "@ NSH", status: "tbd" },
      { day: "Wed", date: "Oct 9", opp: "vs CHI", status: "likely" },
      { day: "Fri", date: "Oct 11", opp: "@ WPG", status: "expected" },
    ],
    recentGoalieStarts: [
      { date: "Oct 5", opp: "vs STL", result: "W 4-1", ga: 1, sog: 26, sv: 25, svPct: ".962", fp: 15.4 },
      { date: "Oct 3", opp: "@ MIN", result: "L 3-2", ga: 3, sog: 30, sv: 27, svPct: ".900", fp: 8.9 },
    ],
    seasonStats: [
      { label: "GP", value: "54" },
      { label: "W", value: "31" },
      { label: "L", value: "15" },
      { label: "OTL", value: "6" },
      { label: "GAA", value: "2.52" },
      { label: "SV%", value: ".912" },
      { label: "SO", value: "3" },
      { label: "FP/G", value: "11.8" },
    ],
    news: [
      { id: "n1", title: "Oettinger likely to get the nod in Nashville", source: "The Athletic", ago: "5h ago", imageUrl: TSN },
    ],
  },
  demko: {
    id: "demko",
    kind: "goalie",
    name: "Thatcher Demko",
    team: "VAN",
    position: "G",
    number: 35,
    headshotUrl: headshot(8477967),
    rosteredPct: 87,
    startedPct: 64,
    gameLabel: "Next Game",
    gameDate: "Tue, Oct 8",
    gameTime: "7:00 PM",
    homeAway: "@",
    oppTeam: "EDM",
    oppRecord: "(1-2-0)",
    myRecord: "(2-1-0)",
    projPoints: 12.6,
    startProbability: 78,
    startStatusPill: "Likely Start",
    goalieOutlook: {
      expectedStarter: "Yes",
      confirmed: "—",
      backToBack: "No",
      oppGoalRank: "12th",
      oppXg: "3.1",
      gameTotal: "6.0",
      projectionFp: "12.6 FP",
    },
    weekGames: [
      { day: "Tue", date: "Oct 8", opp: "@ EDM", status: "likely" },
      { day: "Thu", date: "Oct 10", opp: "vs CGY", status: "expected" },
      { day: "Sat", date: "Oct 12", opp: "@ SEA", status: "tbd" },
      { day: "Sun", date: "Oct 13", opp: "vs ANA", status: "expected" },
    ],
    recentGoalieStarts: [
      { date: "Oct 5", opp: "vs CGY", result: "W 4-2", ga: 2, sog: 28, sv: 26, svPct: ".929", fp: 14.2 },
      { date: "Oct 3", opp: "@ WPG", result: "L 3-2", ga: 3, sog: 32, sv: 29, svPct: ".906", fp: 9.8 },
      { date: "Oct 1", opp: "vs SEA", result: "W 3-1", ga: 1, sog: 27, sv: 26, svPct: ".963", fp: 16.6 },
      { date: "Sep 28", opp: "@ EDM", result: "L 4-1", ga: 4, sog: 34, sv: 30, svPct: ".882", fp: 6.1 },
      { date: "Sep 25", opp: "vs SJS", result: "W 5-2", ga: 2, sog: 31, sv: 29, svPct: ".935", fp: 13.4 },
    ],
    seasonStats: [
      { label: "GP", value: "52" },
      { label: "W", value: "28" },
      { label: "L", value: "18" },
      { label: "OTL", value: "6" },
      { label: "GAA", value: "2.48" },
      { label: "SV%", value: ".918" },
      { label: "SO", value: "4" },
      { label: "FP/G", value: "11.6" },
    ],
    news: [
      { id: "n1", title: "Demko expected to start Tuesday vs. Oilers", source: "TSN", ago: "3h ago", imageUrl: TSN },
      { id: "n2", title: "Demko looks sharp in return to form", source: "The Athletic", ago: "1d ago", imageUrl: TSN },
    ],
  },
};

// --- Matchup scoring detail (live) ---
export interface MatchupPlayerCell {
  name: string;
  teamPos: string;
  liveStatus?: string;
  isLive?: boolean;
  points: number;
  headshotId: number;
}

export interface MatchupSlotRow {
  slot: string;
  mine: MatchupPlayerCell;
  theirs: MatchupPlayerCell;
}

export interface TodayGameChip {
  id: string;
  away: string;
  home: string;
  time?: string;
  liveStatus?: string;
  isLive?: boolean;
  awayScore?: number;
  homeScore?: number;
}

export const MATCHUP_DETAIL = {
  mine: {
    name: "Harbour Ice",
    logoEmoji: "🐻‍❄️",
    record: "2-0-0",
    rank: "1st",
    score: 78.4,
    proj: 112.6,
    gamesRemaining: 12,
    gamesTotal: 16,
  },
  theirs: {
    name: "Puck Pirates",
    logoEmoji: "🏴‍☠️",
    record: "1-1-0",
    rank: "5th",
    score: 64.1,
    proj: 96.3,
    gamesRemaining: 9,
    gamesTotal: 16,
  },
  winProbability: 72,
};

export const TODAY_GAME_CHIPS: TodayGameChip[] = [
  { id: "g1", away: "TOR", home: "FLA", time: "7:00 PM" },
  { id: "g2", away: "EDM", home: "VAN", time: "10:00 PM" },
  { id: "g3", away: "BOS", home: "MTL", time: "7:00 PM" },
  { id: "g4", away: "COL", home: "DAL", time: "8:30 PM" },
  { id: "g5", away: "NYR", home: "OTT", liveStatus: "2nd 8:14", isLive: true, awayScore: 3, homeScore: 1 },
];

export const MATCHUP_SLOTS: MatchupSlotRow[] = [
  { slot: "F", mine: { name: "A. Matthews", teamPos: "TOR · C", liveStatus: "@ FLA 2nd 8:14", isLive: true, points: 12.4, headshotId: 8479318 }, theirs: { name: "C. McDavid", teamPos: "EDM · C", liveStatus: "@ VAN 10:00 PM", points: 6.2, headshotId: 8478402 } },
  { slot: "F", mine: { name: "M. Tkachuk", teamPos: "FLA · LW", liveStatus: "vs TOR 2nd 8:14", isLive: true, points: 8.1, headshotId: 8479314 }, theirs: { name: "K. Kaprizov", teamPos: "MIN · LW", liveStatus: "vs STL 8:00 PM", points: 9.6, headshotId: 8478864 } },
  { slot: "F", mine: { name: "N. Kucherov", teamPos: "TB · RW", liveStatus: "@ CAR 1st 12:01", isLive: true, points: 6.7, headshotId: 8476453 }, theirs: { name: "W. Nylander", teamPos: "TOR · RW", liveStatus: "@ FLA 2nd 8:14", isLive: true, points: 4.1, headshotId: 8481556 } },
  { slot: "F", mine: { name: "J. Eichel", teamPos: "VGK · C", liveStatus: "@ LA 9:30 PM", points: 3.2, headshotId: 8478403 }, theirs: { name: "B. Konecny", teamPos: "PHI · RW", liveStatus: "@ NJ Final", points: 2.8, headshotId: 8478439 } },
  { slot: "F", mine: { name: "B. Point", teamPos: "TB · C", liveStatus: "@ CAR 1st 12:01", isLive: true, points: 4.6, headshotId: 8478010 }, theirs: { name: "S. Aho", teamPos: "CAR · C", liveStatus: "vs TB 1st 12:01", isLive: true, points: 6.0, headshotId: 8478427 } },
  { slot: "F", mine: { name: "T. Meier", teamPos: "NJ · RW", liveStatus: "vs PHI Final", points: 7.1, headshotId: 8480033 }, theirs: { name: "A. Svechnikov", teamPos: "CAR · RW", liveStatus: "vs TB 1st 12:01", isLive: true, points: 5.5, headshotId: 8480830 } },
  { slot: "F", mine: { name: "J. Guentzel", teamPos: "UTA · LW", liveStatus: "vs WPG 9:00 PM", points: 5.8, headshotId: 8477404 }, theirs: { name: "T. Teravainen", teamPos: "CAR · LW", liveStatus: "vs TB 1st 12:01", isLive: true, points: 3.9, headshotId: 8477493 } },
  { slot: "F", mine: { name: "M. Necas", teamPos: "COL · C", liveStatus: "@ DAL 8:30 PM", points: 6.3, headshotId: 8480039 }, theirs: { name: "J. Robertson", teamPos: "DAL · LW", liveStatus: "vs COL 8:30 PM", points: 5.0, headshotId: 8481586 } },
  { slot: "F", mine: { name: "S. Reinhart", teamPos: "FLA · RW", liveStatus: "vs TOR 2nd 8:14", isLive: true, points: 5.1, headshotId: 8477933 }, theirs: { name: "M. Barzal", teamPos: "NYI · C", liveStatus: "vs DET 7:30 PM", points: 4.2, headshotId: 8478445 } },
  { slot: "UTIL", mine: { name: "C. Verhaeghe", teamPos: "FLA · UTIL", liveStatus: "vs TOR 2nd 8:14", isLive: true, points: 4.0, headshotId: 8477409 }, theirs: { name: "M. Stone", teamPos: "VGK · UTIL", liveStatus: "@ LA 9:30 PM", points: 2.8, headshotId: 8475913 } },
  { slot: "D", mine: { name: "Q. Hughes", teamPos: "VAN · D", liveStatus: "vs EDM 10:00 PM", points: 7.2, headshotId: 8480800 }, theirs: { name: "A. Pietrangelo", teamPos: "VGK · D", liveStatus: "@ LA 9:30 PM", points: 3.8, headshotId: 8477447 } },
  { slot: "D", mine: { name: "C. Makar", teamPos: "COL · D", liveStatus: "@ DAL 8:30 PM", points: 6.9, headshotId: 8480069 }, theirs: { name: "E. Karlsson", teamPos: "PIT · D", liveStatus: "vs BUF 7:00 PM", points: 5.1, headshotId: 8474578 } },
  { slot: "D", mine: { name: "M. Rielly", teamPos: "TOR · D", liveStatus: "@ FLA 2nd 8:14", isLive: true, points: 3.4, headshotId: 8476853 }, theirs: { name: "B. Montour", teamPos: "SEA · D", liveStatus: "vs CGY 10:00 PM", points: 2.9, headshotId: 8477986 } },
  { slot: "D", mine: { name: "D. Toews", teamPos: "COL · D", liveStatus: "@ DAL 8:30 PM", points: 4.8, headshotId: 8478038 }, theirs: { name: "J. Spurgeon", teamPos: "MIN · D", liveStatus: "vs STL 8:00 PM", points: 4.2, headshotId: 8477380 } },
  { slot: "G", mine: { name: "T. Demko", teamPos: "VAN · G", liveStatus: "vs EDM 10:00 PM", points: 10.1, headshotId: 8477967 }, theirs: { name: "S. Bobrovsky", teamPos: "FLA · G", liveStatus: "vs TOR 2nd 8:14", isLive: true, points: 8.3, headshotId: 8475683 } },
  { slot: "G", mine: { name: "J. Oettinger", teamPos: "DAL · G", liveStatus: "vs COL 8:30 PM", points: 6.0, headshotId: 8479979 }, theirs: { name: "I. Sorokin", teamPos: "NYI · G", liveStatus: "vs DET 7:30 PM", points: 3.1, headshotId: 8479360 } },
];

// --- Matchups ---
export interface MatchupTeamInfo {
  id: string;
  name: string;
  logoEmoji: string;
  record: string;
  division: string;
  score: number;
  proj: number;
  gamesRemaining: number;
  gamesTotal: number;
}

export interface LeagueMatchupSummary {
  id: string;
  homeEmoji: string;
  awayEmoji: string;
  homeName: string;
  awayName: string;
  homeScore: number;
  awayScore: number;
}

export interface TopPerformance {
  id: string;
  mine: { name: string; teamPos: string; statLine: string; fp: number; headshotId: number };
  theirs: { name: string; teamPos: string; statLine: string; fp: number; headshotId: number };
  slot: string;
}

export interface CategoryRow {
  label: string;
  mine: number;
  theirs: number;
  mineDisplay: string;
  theirsDisplay: string;
}

export const MY_MATCHUP = {
  mine: {
    id: "tacocorp",
    name: "TacoCorp",
    logoEmoji: "🐻‍❄️",
    record: "0 - 0",
    division: "Silver Division",
    score: 78.4,
    proj: 96.7,
    gamesRemaining: 3,
    gamesTotal: 8,
  } as MatchupTeamInfo,
  theirs: {
    id: "jeremy",
    name: "Jeremy",
    logoEmoji: "🏴‍☠️",
    record: "0 - 0",
    division: "Silver Division",
    score: 62.1,
    proj: 83.2,
    gamesRemaining: 5,
    gamesTotal: 8,
  } as MatchupTeamInfo,
  live: true,
};

export const LEAGUE_MATCHUPS: LeagueMatchupSummary[] = [
  { id: "m1", homeEmoji: "🐻‍❄️", awayEmoji: "🏴‍☠️", homeName: "TacoCorp", awayName: "Jeremy", homeScore: 78.4, awayScore: 62.1 },
  { id: "m2", homeEmoji: "🐙", awayEmoji: "🍔", homeName: "Kraken", awayName: "Burgers", homeScore: 112.3, awayScore: 91.7 },
  { id: "m3", homeEmoji: "🐋", awayEmoji: "🤡", homeName: "Whalers", awayName: "Snipe", homeScore: 68.5, awayScore: 75.9 },
  { id: "m4", homeEmoji: "🍺", awayEmoji: "🧊", homeName: "Drunks", awayName: "Ice", homeScore: 84.2, awayScore: 79.0 },
];

export const TOP_PERFORMANCES: TopPerformance[] = [
  { id: "t1", slot: "C", mine: { name: "C. McDavid", teamPos: "EDM | C", statLine: "2 G, 3 A, 6 SOG, 1 PPP", fp: 11.6, headshotId: 8478402 }, theirs: { name: "A. Matthews", teamPos: "TOR | C", statLine: "1 G, 2 A, 5 SOG, 1 PPP", fp: 8.4, headshotId: 8479318 } },
  { id: "t2", slot: "F", mine: { name: "K. Kaprizov", teamPos: "MIN | LW", statLine: "1 G, 1 A, 4 SOG, 2 PPP", fp: 7.2, headshotId: 8478864 }, theirs: { name: "B. Tkachuk", teamPos: "OTT | LW", statLine: "1 G, 1 A, 5 SOG, 1 PPP", fp: 6.8, headshotId: 8480801 } },
  { id: "t3", slot: "F", mine: { name: "N. Kucherov", teamPos: "TB | RW", statLine: "0 G, 2 A, 7 SOG, 1 PPP", fp: 6.1, headshotId: 8476453 }, theirs: { name: "M. Rantanen", teamPos: "COL | RW", statLine: "1 A, 3 SOG, 1 PPP", fp: 4.3, headshotId: 8478420 } },
  { id: "t4", slot: "D", mine: { name: "Q. Hughes", teamPos: "VAN | D", statLine: "0 G, 2 A, 4 SOG, 1 PPP", fp: 5.4, headshotId: 8480800 }, theirs: { name: "D. Makar", teamPos: "COL | D", statLine: "0 G, 1 A, 3 SOG, 1 PPP", fp: 3.9, headshotId: 8480069 } },
  { id: "t5", slot: "G", mine: { name: "J. Oettinger", teamPos: "DAL | G", statLine: "1 W, .931 SV%, 1 SO", fp: 10.4, headshotId: 8479979 }, theirs: { name: "S. Bobrovsky", teamPos: "FLA | G", statLine: "1 W, .915 SV%, 0 SO", fp: 7.6, headshotId: 8475683 } },
];

export const CATEGORY_BREAKDOWN: CategoryRow[] = [
  { label: "G", mine: 12, theirs: 9, mineDisplay: "12", theirsDisplay: "9" },
  { label: "A", mine: 18, theirs: 14, mineDisplay: "18", theirsDisplay: "14" },
  { label: "PPP", mine: 27, theirs: 20, mineDisplay: "27", theirsDisplay: "20" },
  { label: "SOG", mine: 89, theirs: 76, mineDisplay: "89", theirsDisplay: "76" },
  { label: "W", mine: 3, theirs: 2, mineDisplay: "3", theirsDisplay: "2" },
  { label: "SV%", mine: 0.926, theirs: 0.912, mineDisplay: ".926", theirsDisplay: ".912" },
  { label: "SO", mine: 1, theirs: 0, mineDisplay: "1", theirsDisplay: "0" },
];

// --- Today view data ---
export interface TodayGame {
  playerId: string;
  gameTime?: string;
  liveStatus?: string;
  isLive?: boolean;
}

export const TODAY_GAMES: Record<string, TodayGame> = {
  mcdavid: { playerId: "mcdavid", gameTime: "10:00 PM" },
  matthews: { playerId: "matthews", liveStatus: "2nd 8:14", isLive: true },
  kaprizov: { playerId: "kaprizov", gameTime: "8:00 PM" },
  tkachuk: { playerId: "tkachuk", liveStatus: "2nd 8:14", isLive: true },
  kucherov: { playerId: "kucherov", liveStatus: "1st 12:01", isLive: true },
  rantanen: { playerId: "rantanen", gameTime: "10:30 PM" },
  hughes: { playerId: "hughes", gameTime: "10:00 PM" },
  makar: { playerId: "makar", gameTime: "10:30 PM" },
  bobrovsky: { playerId: "bobrovsky", gameTime: "10:00 PM" },
  oettinger: { playerId: "oettinger", gameTime: "8:30 PM" },
  point: { playerId: "point", gameTime: "10:00 PM" },
};

// --- Trades ---

export type TradeStrategy = "Win Now" | "Rebuild" | "Retool" | "Compete Next Year";

export interface TradeAsset {
  id: string;
  kind: "player" | "pick";
  name: string;
  /** e.g. "G · DAL" or "Draft Pick" */
  detail: string;
  headshotUrl?: string;
}

export interface TradeMessage {
  id: string;
  author: string;
  time: string;
  text: string;
  mine: boolean;
}

export interface TradeTeamMeta {
  id: string;
  name: string;
  manager: string;
  strategy: TradeStrategy;
  logoEmoji: string;
  goals: string[];
}

export interface ImpactRow {
  label: string;
  mine: string;
  theirs: string;
  mineGood: boolean | null; // null = neutral
  theirsGood: boolean | null;
}

export interface ValidationItem {
  label: string;
  status: string;
}

export interface Trade {
  id: string;
  mine: TradeTeamMeta;
  theirs: TradeTeamMeta;
  youReceive: TradeAsset[];
  theyReceive: TradeAsset[];
  chat: TradeMessage[];
  participantCount: number;
  waitingOn: string;
  steps: string[];
  currentStep: number; // 0-based index into steps
  impactTabs: string[];
  impact: ImpactRow[];
  validationMine: ValidationItem[];
  validationTheirs: ValidationItem[];
}

export const ACTIVE_TRADE: Trade = {
  id: "t1",
  mine: {
    id: "harbour-ice",
    name: "Harbour Ice",
    manager: "Mark",
    strategy: "Win Now",
    logoEmoji: "🐻‍❄️",
    goals: ["Win Now", "Add Scoring", "G Depth"],
  },
  theirs: {
    id: "puck-pirates",
    name: "Puck Pirates",
    manager: "Jamie",
    strategy: "Rebuild",
    logoEmoji: "🏴‍☠️",
    goals: ["Future Picks", "Young Talent", "Build Depth"],
  },
  youReceive: [
    {
      id: "a1",
      kind: "player",
      name: "Jake Oettinger",
      detail: "G · DAL",
      headshotUrl: headshot(8479979),
    },
    { id: "a2", kind: "pick", name: "2027 3rd Round", detail: "Draft Pick" },
    {
      id: "a3",
      kind: "player",
      name: "Logan Stankoven",
      detail: "F · DAL (Prospect)",
      headshotUrl: headshot(8481583),
    },
  ],
  theyReceive: [
    {
      id: "b1",
      kind: "player",
      name: "Nikita Kucherov",
      detail: "RW · TB",
      headshotUrl: headshot(8476453),
    },
    {
      id: "b2",
      kind: "player",
      name: "Evan Bouchard",
      detail: "D · EDM",
      headshotUrl: headshot(8480803),
    },
  ],
  chat: [
    { id: "c1", author: "Mark", time: "10:14 AM", text: "Would you do Oettinger for Kucherov straight up?", mine: true },
    { id: "c2", author: "Jamie", time: "10:16 AM", text: "Good start. I'd need something younger coming back.", mine: false },
    { id: "c3", author: "Mark", time: "10:18 AM", text: "What if I add Bouchard?", mine: true },
    { id: "c4", author: "Jamie", time: "10:20 AM", text: "Add your 2027 2nd and I think we're close.", mine: false },
    { id: "c5", author: "Mark", time: "10:22 AM", text: "Okay I added Stankoven. How does that look?", mine: true },
    { id: "c6", author: "Jamie", time: "10:23 AM", text: "That works for me. Ready to finalize?", mine: false },
  ],
  participantCount: 2,
  waitingOn: "Jamie",
  steps: ["Discussion", "Both Ready", "Review", "Submit"],
  currentStep: 2,
  impactTabs: ["This Season", "Next Season", "Long Term"],
  impact: [
    { label: "Projected Points", mine: "+8.2", theirs: "-6.1", mineGood: true, theirsGood: false },
    { label: "Goalie Starts", mine: "+1.9", theirs: "-0.8", mineGood: true, theirsGood: false },
    { label: "Depth", mine: "Stronger", theirs: "Stronger", mineGood: true, theirsGood: true },
    { label: "Average Age", mine: "+0.4", theirs: "-2.3", mineGood: null, theirsGood: null },
    { label: "Future Value", mine: "-12%", theirs: "+28%", mineGood: false, theirsGood: true },
  ],
  validationMine: [
    { label: "Roster rules", status: "Valid" },
    { label: "Trade deadline", status: "Open" },
  ],
  validationTheirs: [
    { label: "Position requirements", status: "Valid" },
    { label: "Keeper/dynasty rules", status: "Valid" },
  ],
};

// --- Trade Room data ---

export interface ManagerOption {
  id: string;
  name: string;
  emoji: string;
  manager: string;
  record: string;
  strategy: string;
}

export const MANAGERS: ManagerOption[] = [
  { id: "jeremy", name: "Puck Pirates", emoji: "🏴‍☠️", manager: "Jamie", record: "5-4-1", strategy: "Rebuild" },
  { id: "kraken", name: "Kraken", emoji: "🐙", manager: "Alex", record: "8-2-0", strategy: "Win Now" },
  { id: "whalers", name: "Whalers", emoji: "🐋", manager: "Chris", record: "6-4-0", strategy: "Retool" },
  { id: "burgers", name: "Burgers", emoji: "🍔", manager: "Sam", record: "5-5-0", strategy: "Compete Next Year" },
  { id: "drunks", name: "Drunks", emoji: "🍺", manager: "Pat", record: "4-5-1", strategy: "Rebuild" },
  { id: "snipe", name: "Snipe", emoji: "🤡", manager: "Jordan", record: "3-7-0", strategy: "Rebuild" },
  { id: "ice", name: "Ice", emoji: "🧊", manager: "Taylor", record: "2-8-0", strategy: "Rebuild" },
];

export interface AvailableTradeAsset {
  id: string;
  kind: "player" | "pick";
  name: string;
  detail: string;
  headshotUrl?: string;
  position?: string;
  team?: string;
  projectedPoints?: number;
}

/** Harbour Ice roster assets available to add to a trade */
export const MY_AVAILABLE_ASSETS: AvailableTradeAsset[] = [
  { id: "ma1", kind: "player", name: "C. McDavid", detail: "C · EDM", headshotUrl: headshot(8478402), position: "C", team: "EDM", projectedPoints: 18.4 },
  { id: "ma2", kind: "player", name: "A. Matthews", detail: "C · TOR", headshotUrl: headshot(8479318), position: "C", team: "TOR", projectedPoints: 17.2 },
  { id: "ma3", kind: "player", name: "K. Kaprizov", detail: "LW · MIN", headshotUrl: headshot(8478864), position: "LW", team: "MIN", projectedPoints: 15.6 },
  { id: "ma4", kind: "player", name: "B. Tkachuk", detail: "LW · OTT", headshotUrl: headshot(8480801), position: "LW", team: "OTT", projectedPoints: 14.1 },
  { id: "ma5", kind: "player", name: "M. Rantanen", detail: "RW · COL", headshotUrl: headshot(8478420), position: "RW", team: "COL", projectedPoints: 15.3 },
  { id: "ma6", kind: "player", name: "Q. Hughes", detail: "D · VAN", headshotUrl: headshot(8480800), position: "D", team: "VAN", projectedPoints: 13.6 },
  { id: "ma7", kind: "player", name: "D. Makar", detail: "D · COL", headshotUrl: headshot(8480069), position: "D", team: "COL", projectedPoints: 14.9 },
  { id: "ma8", kind: "player", name: "S. Bobrovsky", detail: "G · FLA", headshotUrl: headshot(8475683), position: "G", team: "FLA", projectedPoints: 16.9 },
  { id: "ma9", kind: "player", name: "B. Point", detail: "BN · TB", headshotUrl: headshot(8478010), position: "BN", team: "TB", projectedPoints: 13.8 },
  { id: "ma10", kind: "pick", name: "2026 1st Round", detail: "Draft Pick" },
  { id: "ma11", kind: "pick", name: "2026 2nd Round", detail: "Draft Pick" },
  { id: "ma12", kind: "pick", name: "2026 3rd Round", detail: "Draft Pick" },
  { id: "ma13", kind: "pick", name: "2027 1st Round", detail: "Draft Pick" },
  { id: "ma14", kind: "pick", name: "2027 3rd Round", detail: "Draft Pick" },
];

/** Puck Pirates roster assets available to add to a trade */
export const THEIR_AVAILABLE_ASSETS: AvailableTradeAsset[] = [
  { id: "ta1", kind: "player", name: "T. Thompson", detail: "C · BUF", headshotUrl: headshot(8479420), position: "C", team: "BUF", projectedPoints: 14.2 },
  { id: "ta2", kind: "player", name: "M. Heiskanen", detail: "D · DAL", headshotUrl: headshot(8480036), position: "D", team: "DAL", projectedPoints: 13.1 },
  { id: "ta3", kind: "player", name: "R. Dahlin", detail: "D · BUF", headshotUrl: headshot(8480839), position: "D", team: "BUF", projectedPoints: 12.8 },
  { id: "ta4", kind: "player", name: "J. Guenther", detail: "RW · UTA", headshotUrl: headshot(8481585), position: "RW", team: "UTA", projectedPoints: 12.4 },
  { id: "ta5", kind: "player", name: "B. Boeser", detail: "RW · VAN", headshotUrl: headshot(8478444), position: "RW", team: "VAN", projectedPoints: 11.2 },
  { id: "ta6", kind: "player", name: "J. Skinner", detail: "LW · EDM", headshotUrl: headshot(8477498), position: "LW", team: "EDM", projectedPoints: 10.6 },
  { id: "ta7", kind: "player", name: "P. Kane", detail: "RW · DET", headshotUrl: headshot(8474141), position: "RW", team: "DET", projectedPoints: 10.1 },
  { id: "ta8", kind: "player", name: "T. Demko", detail: "G · VAN", headshotUrl: headshot(8477967), position: "G", team: "VAN", projectedPoints: 14.8 },
  { id: "ta9", kind: "player", name: "C. Hellebuyck", detail: "G · WPG", headshotUrl: headshot(8476945), position: "G", team: "WPG", projectedPoints: 15.2 },
  { id: "ta10", kind: "pick", name: "2026 1st Round", detail: "Draft Pick" },
  { id: "ta11", kind: "pick", name: "2026 2nd Round", detail: "Draft Pick" },
  { id: "ta12", kind: "pick", name: "2027 1st Round", detail: "Draft Pick" },
  { id: "ta13", kind: "pick", name: "2027 2nd Round", detail: "Draft Pick" },
  { id: "ta14", kind: "pick", name: "2027 3rd Round", detail: "Draft Pick" },
];

/* ---------------- Trade Conversations (screen 17) ---------------- */

export type ConversationStatus = "Active" | "Waiting" | "Closed";

export interface TradeConversation {
  id: string;
  manager: string;
  teamName: string;
  emoji: string;
  playerFocus: string;
  preview: string;
  ago: string;
  status: ConversationStatus;
}

export const TRADE_CONVERSATIONS: TradeConversation[] = [
  { id: "cv1", manager: "Jamie", teamName: "Puck Pirates", emoji: "🏴‍☠️", playerFocus: "Oettinger", preview: "Yeah I'm open to moving him. Looking for a top 6 winger or a 1st.", ago: "12m", status: "Active" },
  { id: "cv2", manager: "Taylor", teamName: "Offside Wieners", emoji: "🌭", playerFocus: "B. Tkachuk", preview: "Interesting. Would you consider adding a pick?", ago: "2h", status: "Active" },
  { id: "cv3", manager: "Chris", teamName: "Slapshot City", emoji: "🐙", playerFocus: "Makar", preview: "I'm listening. He's a core piece though.", ago: "5h", status: "Active" },
  { id: "cv4", manager: "Alex", teamName: "Ice Cold Takes", emoji: "🥅", playerFocus: "Kucherov", preview: "Are you open to moving him? Looking for picks/prospects.", ago: "1d", status: "Waiting" },
  { id: "cv5", manager: "Sam", teamName: "Net Results", emoji: "🧊", playerFocus: "Demko", preview: "No longer available.", ago: "2d", status: "Closed" },
];

/* ---------------- Dynasty Trade Market (screen 18) ---------------- */

export type MarketTag = "Available" | "Listening" | "Rental" | "Core" | "Rebuild";
export type MarketStrategy = "Win Now" | "Rebuild" | "Retool";

export interface MarketTarget {
  id: string;
  playerName: string;
  position: string;
  team: string;
  headshotUrl?: string;
  statusTag: MarketTag;
  ownerTag: MarketTag;
  ownerTeam: string;
  ownerEmoji: string;
  ownerStrategy: MarketStrategy;
  lookingFor: string;
}

export const MARKET_TARGETS: MarketTarget[] = [
  { id: "mt1", playerName: "Jake Oettinger", position: "G", team: "DAL", headshotUrl: headshot(8479979), statusTag: "Available", ownerTag: "Rental", ownerTeam: "Puck Pirates", ownerEmoji: "🏴‍☠️", ownerStrategy: "Rebuild", lookingFor: "Picks, Prospects, RW" },
  { id: "mt2", playerName: "Nikita Kucherov", position: "RW", team: "TB", headshotUrl: headshot(8476453), statusTag: "Listening", ownerTag: "Core", ownerTeam: "Ice Cold Takes", ownerEmoji: "🥅", ownerStrategy: "Win Now", lookingFor: "G, D, Young Players" },
  { id: "mt3", playerName: "Cale Makar", position: "D", team: "COL", headshotUrl: headshot(8480069), statusTag: "Available", ownerTag: "Core", ownerTeam: "Slapshot City", ownerEmoji: "🐙", ownerStrategy: "Retool", lookingFor: "Picks, Top 6 Forward" },
  { id: "mt4", playerName: "Brayden Point", position: "C", team: "TB", headshotUrl: headshot(8478010), statusTag: "Available", ownerTag: "Rebuild", ownerTeam: "Offside Wieners", ownerEmoji: "🌭", ownerStrategy: "Rebuild", lookingFor: "Picks, Prospects" },
  { id: "mt5", playerName: "Jacob Demko", position: "G", team: "VAN", headshotUrl: headshot(8477967), statusTag: "Available", ownerTag: "Rebuild", ownerTeam: "Net Results", ownerEmoji: "🧊", ownerStrategy: "Rebuild", lookingFor: "Picks, Young G" },
];

export interface MarketPick {
  id: string;
  label: string;
  ownerTeam: string;
  statusTag: MarketTag;
  lookingFor: string;
}

export const MARKET_PICKS: MarketPick[] = [
  { id: "mp1", label: "2027 1st Round", ownerTeam: "Puck Pirates", statusTag: "Available", lookingFor: "Win-now players" },
  { id: "mp2", label: "2026 2nd Round", ownerTeam: "Offside Wieners", statusTag: "Available", lookingFor: "Goaltending" },
  { id: "mp3", label: "2027 3rd Round", ownerTeam: "Slapshot City", statusTag: "Available", lookingFor: "Depth" },
];

/* ---------------- Team Needs (trades) ---------------- */

export interface TeamNeeds {
  id: string;
  team: string;
  emoji: string;
  strategy: MarketStrategy;
  lookingFor: string;
  offering: string;
}

export const MY_TEAM_NEEDS = {
  lookingFor: ["Starting G depth", "Top-6 winger"],
  offering: ["2027 picks", "Prospects", "Roster D"],
};

export const TEAM_NEEDS: TeamNeeds[] = [
  { id: "tn1", team: "Puck Pirates", emoji: "🏴‍☠️", strategy: "Rebuild", lookingFor: "Picks, Prospects, RW", offering: "J. Oettinger (rental)" },
  { id: "tn2", team: "Ice Cold Takes", emoji: "🥅", strategy: "Win Now", lookingFor: "G, D, Young Players", offering: "N. Kucherov (listening)" },
  { id: "tn3", team: "Slapshot City", emoji: "🐙", strategy: "Retool", lookingFor: "Picks, Top 6 Forward", offering: "C. Makar (core)" },
  { id: "tn4", team: "Offside Wieners", emoji: "🌭", strategy: "Rebuild", lookingFor: "Picks, Prospects", offering: "B. Point" },
  { id: "tn5", team: "Net Results", emoji: "🧊", strategy: "Rebuild", lookingFor: "Picks, Young G", offering: "T. Demko" },
  { id: "tn6", team: "Bender's Burgers", emoji: "🍔", strategy: "Win Now", lookingFor: "Top-pair D", offering: "2026 1st" },
  { id: "tn7", team: "Victoria Whalers", emoji: "🐋", strategy: "Retool", lookingFor: "Scoring winger", offering: "Prospects" },
  { id: "tn8", team: "Snipe Show", emoji: "🤡", strategy: "Rebuild", lookingFor: "Everything", offering: "Cap space" },
];

/* ---------------- Franchise / Team Overview ---------------- */

export const FRANCHISE_CAP = {
  used: 76.3,
  total: 100.0,
  openRosterSpots: 2,
  rosterSize: 25,
  expiringContracts: 7,
  expiringYear: 2026,
  rookieSlotsUsed: 1,
  rookieSlotsTotal: 4,
};

export interface FuturePickYear {
  year: number;
  count: number;
}

export const FUTURE_PICKS: FuturePickYear[] = [
  { year: 2026, count: 2 },
  { year: 2027, count: 3 },
  { year: 2028, count: 1 },
];

export const FUTURE_PICKS_TOTAL = FUTURE_PICKS.reduce((s, p) => s + p.count, 0);

export interface CapHitYear {
  season: string;
  amount: number; // $M
}

export const CAP_HITS_BY_SEASON: CapHitYear[] = [
  { season: "2025-26", amount: 76.3 },
  { season: "2026-27", amount: 68.1 },
  { season: "2027-28", amount: 54.2 },
  { season: "2028-29", amount: 38.7 },
];