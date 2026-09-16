// Mock data for the UHHP 2025 Rookie Draft. Replace with Railway API calls later.

import type { SkaterPosition } from "./types";

// NHL headshots use the official NHL CDN pattern.
const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export interface DraftTeam {
  id: string;
  name: string;
  emoji: string;
}

export interface RookiePlayer {
  id: string;
  name: string;
  position: SkaterPosition | "G";
  nhlTeam: string; // abbrev e.g. "MTL"
  nhlTeamName: string; // e.g. "Montréal Canadiens"
  rank: number;
  age: number;
  height: string;
  weight: string;
  shoots: "L" | "R";
  headshotUrl?: string;
  scoutingReport: string;
  nhlComparison: string;
}

export interface DraftPick {
  overall: number;
  round: number;
  pickInRound: number;
  team: DraftTeam;
  player: RookiePlayer;
}

export const DRAFT_META = {
  title: "2026 Entry Draft",
  date: "Jun 22, 2026 - 8:00 PM",
  format: "Entry Draft (1 Round)",
  rosters: "Rookies move to Prospect Roster",
  rounds: 1,
  secondsPerPick: 60,
};

/** The signed-in manager's team in this draft. */
export const MY_DRAFT_TEAM_ID = "pylons";

/** Draft order — reverse order of standings (subject to change by commissioner). */
export const DRAFT_ORDER: DraftTeam[] = [
  { id: "pylons", name: "Pylons", emoji: "🚧" },
  { id: "basteerds", name: "Basteerds", emoji: "🍗" },
  { id: "oilers-nation", name: "New Oilers Nation", emoji: "🛢️" },
  { id: "doomsday", name: "Doomsday", emoji: "☠️" },
  { id: "ice-holes", name: "Ice Holes", emoji: "🕳️" },
  { id: "slapshot", name: "Slapshot", emoji: "🏒" },
  { id: "litter-box", name: "Litter Box", emoji: "🐈‍⬛" },
  { id: "northern-curse", name: "Northern Curse", emoji: "🌲" },
  { id: "misconducts", name: "Misconducts", emoji: "🟥" },
  { id: "greasy-mitts", name: "Greasy Mitts", emoji: "🧤" },
  { id: "knights-ni", name: "Knights Who Say Ni", emoji: "⚔️" },
  { id: "kitten-mittons", name: "Kitten Mittons", emoji: "🐱" },
];

/** Rookie rankings — headshot IDs are real NHL CDN ids. */
export const ROOKIE_PLAYERS: RookiePlayer[] = [
  {
    id: "demidov",
    name: "Ivan Demidov",
    position: "RW",
    nhlTeam: "MTL",
    nhlTeamName: "Montréal Canadiens",
    rank: 1,
    age: 18,
    height: "5'11\"",
    weight: "183 lbs",
    shoots: "L",
    headshotUrl: headshot(8484984),
    scoutingReport:
      "Dynamic offensive talent with elite hands and vision. Projects as a top-line winger with franchise potential.",
    nhlComparison: "Kirill Kaprizov",
  },
  {
    id: "silayev",
    name: "Anton Silayev",
    position: "D",
    nhlTeam: "NJD",
    nhlTeamName: "New Jersey Devils",
    rank: 2,
    age: 18,
    height: "6'7\"",
    weight: "211 lbs",
    shoots: "L",
    headshotUrl: headshot(8484987),
    scoutingReport:
      "Towering two-way defenseman with surprising mobility for his size. Eats minutes and projects as a top-pair anchor.",
    nhlComparison: "Victor Hedman",
  },
  {
    id: "buium",
    name: "Zeev Buium",
    position: "D",
    nhlTeam: "MIN",
    nhlTeamName: "Minnesota Wild",
    rank: 3,
    age: 18,
    height: "6'0\"",
    weight: "183 lbs",
    shoots: "L",
    headshotUrl: headshot(8484798),
    scoutingReport:
      "Elite puck-moving defenseman with high-end vision. Future power-play quarterback from the back end.",
    nhlComparison: "Quinn Hughes",
  },
  {
    id: "celebrini",
    name: "Macklin Celebrini",
    position: "C",
    nhlTeam: "SJS",
    nhlTeamName: "San Jose Sharks",
    rank: 4,
    age: 18,
    height: "6'0\"",
    weight: "190 lbs",
    shoots: "L",
    headshotUrl: headshot(8484801),
    scoutingReport:
      "Complete two-way center with a motor that never quits. Franchise cornerstone and future captain material.",
    nhlComparison: "Jonathan Toews",
  },
  {
    id: "levshunov",
    name: "Artyom Levshunov",
    position: "D",
    nhlTeam: "CHI",
    nhlTeamName: "Chicago Blackhawks",
    rank: 5,
    age: 18,
    height: "6'2\"",
    weight: "208 lbs",
    shoots: "R",
    headshotUrl: headshot(8484783),
    scoutingReport:
      "Smooth-skating defenseman with offensive instincts and a heavy shot from the point.",
    nhlComparison: "Moritz Seider",
  },
  {
    id: "yakemchuk",
    name: "Carter Yakemchuk",
    position: "D",
    nhlTeam: "OTT",
    nhlTeamName: "Ottawa Senators",
    rank: 6,
    age: 18,
    height: "6'3\"",
    weight: "219 lbs",
    shoots: "R",
    headshotUrl: headshot(8484759),
    scoutingReport:
      "Big, aggressive defenseman who loves to join the rush. Raw tools with top-four upside.",
    nhlComparison: "Darnell Nurse",
  },
  {
    id: "catton",
    name: "Berkly Catton",
    position: "C",
    nhlTeam: "SEA",
    nhlTeamName: "Seattle Kraken",
    rank: 7,
    age: 18,
    height: "5'10\"",
    weight: "179 lbs",
    shoots: "L",
    headshotUrl: headshot(8484800),
    scoutingReport:
      "Shifty playmaking center with elite edges and creativity. Thrives in tight spaces.",
    nhlComparison: "Brayden Point",
  },
  {
    id: "helenius",
    name: "Konsta Helenius",
    position: "C",
    nhlTeam: "BUF",
    nhlTeamName: "Buffalo Sabres",
    rank: 8,
    age: 18,
    height: "5'11\"",
    weight: "190 lbs",
    shoots: "R",
    headshotUrl: headshot(8484797),
    scoutingReport:
      "Smart, versatile center who already plays a pro-style game. Reliable in all three zones.",
    nhlComparison: "Aleksander Barkov",
  },
  {
    id: "parekh",
    name: "Zayne Parekh",
    position: "D",
    nhlTeam: "CGY",
    nhlTeamName: "Calgary Flames",
    rank: 9,
    age: 18,
    height: "6'0\"",
    weight: "179 lbs",
    shoots: "R",
    headshotUrl: headshot(8484768),
    scoutingReport:
      "Pure offensive defenseman with dynamic rushing ability. A power-play weapon from the back end.",
    nhlComparison: "Cale Makar",
  },
  {
    id: "connelly",
    name: "Trevor Connelly",
    position: "LW",
    nhlTeam: "VGK",
    nhlTeamName: "Vegas Golden Knights",
    rank: 10,
    age: 18,
    height: "6'1\"",
    weight: "175 lbs",
    shoots: "L",
    headshotUrl: headshot(8484803),
    scoutingReport:
      "Explosive winger with a quick release and fearless attack mentality. High-end scoring talent.",
    nhlComparison: "Alex DeBrincat",
  },
  {
    id: "eiserman",
    name: "Cole Eiserman",
    position: "LW",
    nhlTeam: "NYI",
    nhlTeamName: "New York Islanders",
    rank: 11,
    age: 18,
    height: "6'0\"",
    weight: "195 lbs",
    shoots: "L",
    headshotUrl: headshot(8484807),
    scoutingReport:
      "Elite goal-scoring winger with a lethal one-timer. Among the best pure shooters in the class.",
    nhlComparison: "Auston Matthews",
  },
  {
    id: "puljujarvi",
    name: "Jesse Puljujarvi",
    position: "RW",
    nhlTeam: "PIT",
    nhlTeamName: "Pittsburgh Penguins",
    rank: 12,
    age: 27,
    height: "6'4\"",
    weight: "216 lbs",
    shoots: "R",
    headshotUrl: headshot(8479344),
    scoutingReport:
      "Big-bodied winger with a heavy cycle game. A wildcard pick with veteran savvy.",
    nhlComparison: "—",
  },
  {
    id: "michkov",
    name: "Matvei Michkov",
    position: "RW",
    nhlTeam: "PHI",
    nhlTeamName: "Philadelphia Flyers",
    rank: 13,
    age: 19,
    height: "5'10\"",
    weight: "172 lbs",
    shoots: "L",
    headshotUrl: headshot(8484387),
    scoutingReport:
      "Game-breaking skill and creativity. Pure offensive dynamo with highlight-reel upside.",
    nhlComparison: "Nikita Kucherov",
  },
  {
    id: "askarov",
    name: "Yaroslav Askarov",
    position: "G",
    nhlTeam: "SJS",
    nhlTeamName: "San Jose Sharks",
    rank: 14,
    age: 22,
    height: "6'3\"",
    weight: "180 lbs",
    shoots: "R",
    headshotUrl: headshot(8482137),
    scoutingReport:
      "Athletic, aggressive goaltender with elite reflexes. Projects as a future number-one starter.",
    nhlComparison: "Andrei Vasilevskiy",
  },
];

export const ROOKIE_ELIGIBILITY: string[] = [
  "Maximum 6 rookie players per team",
  "Only rookies from the entry draft (or acquired via trade) can be classified as a rookie",
  "Rookies do not accumulate fantasy points",
  "A rookie can be moved to active roster at any time, at minimum salary",
  "Rookie roster duration + active term = 4 years",
  "Maximum 3 years on rookie roster",
  "Once moved to active roster, cannot be sent down or reclassified as a rookie",
  "Unsigned rookies after 3 years become UFAs",
];

export const DRAFT_FORMAT_RULES: string[] = [
  "1 Round (12 total picks)",
  "Straight draft order by reverse standings",
  "60 seconds per pick",
  "Commissioner may pause if needed",
];

export const WHATS_NEXT: string[] = [
  "Review and sign rookie contracts",
  "Move rookies to prospect roster",
  "Finalize offseason transactions",
];
