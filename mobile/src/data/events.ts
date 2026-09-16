// Mock data for UHHP Events (side competitions). Replace with Railway API calls later.

export type EventStatus = "active" | "upcoming" | "completed";

export interface EventMeta {
  icon: string; // lucide key handled by caller
  label: string;
  sub: string;
}

export interface EventCountdown {
  days: number;
  hrs: number;
  min: number;
}

export interface GameEvent {
  id: string;
  name: string;
  tagline: string;
  status: EventStatus;
  statusLabel: string;
  featured?: boolean;
  emoji: string; // event emblem placeholder
  meta: [EventMeta, EventMeta, EventMeta];
  yourSideLabel: string; // e.g. "Your Squad" / "Your Nation" / "Your Team"
  yourSideName: string;
  yourSideDetail: string;
  yourSideEmoji: string;
  nextLabel: string; // e.g. "NEXT MATCHUP" / "BEGINS IN" / "OPPONENT"
  opponentName?: string;
  opponentEmoji?: string;
  opponentDetail?: string;
  countdown?: EventCountdown;
}

export const EVENTS: GameEvent[] = [
  {
    id: "captains-cup",
    name: "Captains Cup",
    tagline: "3 GMs. 1 Cup. Bragging rights.",
    status: "active",
    statusLabel: "In Progress",
    featured: true,
    emoji: "🐻‍❄️",
    meta: [
      { icon: "users", label: "3 GMs per team", sub: "Dynasty rosters" },
      { icon: "swords", label: "2v2 Round Robin", sub: "1v1 Playoffs" },
      { icon: "calendar", label: "Week 4 of 8", sub: "Round Robin" },
    ],
    yourSideLabel: "Your Squad",
    yourSideName: "Harbour Ice",
    yourSideDetail: "Mark · Jamie · Alex",
    yourSideEmoji: "🐻‍❄️",
    nextLabel: "NEXT MATCHUP",
    opponentName: "Slapshot City",
    opponentEmoji: "🐙",
    opponentDetail: "Week 4 · Tue, Oct 8",
  },
  {
    id: "world-cup",
    name: "World Cup",
    tagline: "Nations collide. Fantasy unites.",
    status: "active",
    statusLabel: "In Progress",
    emoji: "🌍",
    meta: [
      { icon: "users", label: "National Teams", sub: "6 skaters + 2 goalies" },
      { icon: "trophy", label: "Group Stage", sub: "Top 2 advance" },
      { icon: "calendar", label: "Week 2 of 5", sub: "Group Play" },
    ],
    yourSideLabel: "Your Nation",
    yourSideName: "Canada",
    yourSideDetail: "True North. Fantasy Strong.",
    yourSideEmoji: "🇨🇦",
    nextLabel: "NEXT MATCHUP",
    opponentName: "Sweden",
    opponentEmoji: "🇸🇪",
    opponentDetail: "Wed, Oct 9",
  },
  {
    id: "guillotine",
    name: "Guillotine",
    tagline: "Last place gets eliminated.",
    status: "upcoming",
    statusLabel: "Starts Soon",
    emoji: "🪓",
    meta: [
      { icon: "users", label: "Solo Competition", sub: "All league members" },
      { icon: "skull", label: "1 Team Eliminated", sub: "Each week" },
      { icon: "calendar", label: "Starts Week 3", sub: "Tue, Oct 14" },
    ],
    yourSideLabel: "Your Team",
    yourSideName: "Harbour Ice",
    yourSideDetail: "Survive and advance.",
    yourSideEmoji: "🐻‍❄️",
    nextLabel: "BEGINS IN",
    countdown: { days: 6, hrs: 22, min: 18 },
  },
  {
    id: "cross-league-cup",
    name: "Cross-League Cup",
    tagline: "Different leagues. One champion.",
    status: "upcoming",
    statusLabel: "Upcoming",
    emoji: "⚔️",
    meta: [
      { icon: "users", label: "Multi-League", sub: "8 teams + 2 leagues" },
      { icon: "bracket", label: "Knockout Format", sub: "Single elimination" },
      { icon: "calendar", label: "Starts Week 5", sub: "Tue, Oct 28" },
    ],
    yourSideLabel: "Your Team",
    yourSideName: "Harbour Ice",
    yourSideDetail: "Represent the North.",
    yourSideEmoji: "🐻‍❄️",
    nextLabel: "OPPONENT",
    opponentName: "TBD",
    opponentEmoji: "❓",
    opponentDetail: "Draw on Oct 26",
  },
];

export const EVENT_COUNTS = {
  active: EVENTS.filter((e) => e.status === "active").length,
  upcoming: EVENTS.filter((e) => e.status === "upcoming").length,
  completed: EVENTS.filter((e) => e.status === "completed").length,
};

/* ---------------- Event Detail (doc screen 32) ---------------- */

export interface StandingRow {
  rank: number;
  team: string;
  emoji: string;
  record: string;
  points: number;
  mine?: boolean;
}

export interface EventDetail {
  format: string;
  currentRound: string;
  yourStatus: string;
  prize: string;
  rules: string[];
  standingsTitle: string;
  standings: StandingRow[];
}

export const EVENT_DETAILS: Record<string, EventDetail> = {
  "captains-cup": {
    format: "2v2 Round Robin → 1v1 Playoffs",
    currentRound: "Week 4 of 8 · Round Robin",
    yourStatus: "Harbour Ice · 3rd place · 12 pts",
    prize: "Captains Cup trophy + $20 event pool",
    rules: [
      "3 GMs per team, dynasty rosters",
      "Round robin seeding over 8 weeks",
      "Top 4 teams advance to 1v1 playoffs",
      "Event transactions do not affect the main league",
    ],
    standingsTitle: "Round Robin Standings",
    standings: [
      { rank: 1, team: "Slapshot City", emoji: "🐙", record: "5-1", points: 16 },
      { rank: 2, team: "Puck Pirates", emoji: "🏴‍☠️", record: "4-2", points: 13 },
      { rank: 3, team: "Harbour Ice", emoji: "🐻‍❄️", record: "4-2", points: 12, mine: true },
      { rank: 4, team: "Net Results", emoji: "🥅", record: "3-3", points: 10 },
      { rank: 5, team: "Snipe Show", emoji: "🤡", record: "2-4", points: 7 },
      { rank: 6, team: "Mighty Drunks", emoji: "🍺", record: "0-6", points: 1 },
    ],
  },
  "world-cup": {
    format: "Group Stage → Knockout",
    currentRound: "Week 2 of 5 · Group Play",
    yourStatus: "Canada · 1st in Group A · 6 pts",
    prize: "World Cup medal + cross-league qualification",
    rules: [
      "National teams: 6 skaters + 2 goalies",
      "Top 2 in each group advance",
      "Event-only rosters, drafted per nation",
      "Tiebreak: head-to-head, then goal differential",
    ],
    standingsTitle: "Group A",
    standings: [
      { rank: 1, team: "Canada", emoji: "🇨🇦", record: "2-0", points: 6, mine: true },
      { rank: 2, team: "Sweden", emoji: "🇸🇪", record: "1-1", points: 3 },
      { rank: 3, team: "USA", emoji: "🇺🇸", record: "1-1", points: 3 },
      { rank: 4, team: "Finland", emoji: "🇫🇮", record: "0-2", points: 0 },
    ],
  },
  guillotine: {
    format: "Weekly elimination",
    currentRound: "Starts Week 3 · Tue, Oct 14",
    yourStatus: "Harbour Ice · Entered · Survive and advance",
    prize: "Last team standing takes the pot",
    rules: [
      "Solo competition, all league members",
      "Lowest-scoring team is eliminated each week",
      "Eliminated players enter a temporary event pool",
      "Uses your shared dynasty roster",
    ],
    standingsTitle: "Field",
    standings: [
      { rank: 1, team: "12 teams entered", emoji: "🪓", record: "—", points: 0 },
    ],
  },
  "cross-league-cup": {
    format: "Knockout · Single elimination",
    currentRound: "Starts Week 5 · Draw on Oct 26",
    yourStatus: "Harbour Ice · Qualified · Represent the North",
    prize: "Cross-League Cup + federation banner",
    rules: [
      "8 teams across 2 leagues",
      "Single-elimination bracket",
      "Shared rosters from each league",
      "Higher seed chooses matchup week",
    ],
    standingsTitle: "Bracket",
    standings: [
      { rank: 1, team: "Draw on Oct 26", emoji: "⚔️", record: "—", points: 0 },
    ],
  },
};
