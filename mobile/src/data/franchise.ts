// Mock data for the Franchise screen tabs. Replace with Railway API calls later.

import { ROOKIE_PLAYERS, type RookiePlayer } from "./rookieDraft";

const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export type ContractStatus = "UFA" | "RFA" | "ELC";

export interface FranchisePlayer {
  id: string;
  name: string;
  team: string;
  position: string;
  headshotUrl?: string;
  salary: string;
  years: number;
  status: ContractStatus;
}

/** Active roster shown on the Franchise overview (top 8 by salary). */
export const FRANCHISE_SKATERS: FranchisePlayer[] = [
  { id: "matthews", name: "A. Matthews", team: "TOR", position: "C", headshotUrl: headshot(8479318), salary: "$13.2M", years: 5, status: "UFA" },
  { id: "mcdavid", name: "C. McDavid", team: "EDM", position: "C", headshotUrl: headshot(8478402), salary: "$12.5M", years: 3, status: "UFA" },
  { id: "bobrovsky", name: "S. Bobrovsky", team: "FLA", position: "G", headshotUrl: headshot(8475683), salary: "$10.0M", years: 1, status: "UFA" },
  { id: "kucherov", name: "N. Kucherov", team: "TB", position: "RW", headshotUrl: headshot(8476453), salary: "$9.5M", years: 2, status: "UFA" },
  { id: "point", name: "B. Point", team: "TB", position: "C", headshotUrl: headshot(8478010), salary: "$9.5M", years: 3, status: "UFA" },
  { id: "rantanen", name: "M. Rantanen", team: "COL", position: "RW", headshotUrl: headshot(8478420), salary: "$9.3M", years: 2, status: "UFA" },
  { id: "kaprizov", name: "K. Kaprizov", team: "MIN", position: "LW", headshotUrl: headshot(8478864), salary: "$9.0M", years: 4, status: "UFA" },
  { id: "hughes", name: "Q. Hughes", team: "VAN", position: "D", headshotUrl: headshot(8480800), salary: "$9.0M", years: 4, status: "UFA" },
];

/** Full contract book (20 contracts). */
export const FRANCHISE_CONTRACTS: FranchisePlayer[] = [
  ...FRANCHISE_SKATERS,
  { id: "makar", name: "D. Makar", team: "COL", position: "D", headshotUrl: headshot(8480069), salary: "$9.0M", years: 6, status: "UFA" },
  { id: "oettinger", name: "J. Oettinger", team: "DAL", position: "G", headshotUrl: headshot(8479979), salary: "$8.3M", years: 5, status: "RFA" },
  { id: "tkachuk", name: "B. Tkachuk", team: "OTT", position: "LW", headshotUrl: headshot(8480801), salary: "$8.2M", years: 5, status: "UFA" },
  { id: "hellebuyck", name: "C. Hellebuyck", team: "WPG", position: "G", headshotUrl: headshot(8476945), salary: "$8.1M", years: 4, status: "UFA" },
  { id: "demko", name: "T. Demko", team: "VAN", position: "G", headshotUrl: headshot(8477967), salary: "$7.5M", years: 3, status: "UFA" },
  { id: "heiskanen", name: "M. Heiskanen", team: "DAL", position: "D", headshotUrl: headshot(8480036), salary: "$6.7M", years: 3, status: "UFA" },
  { id: "dahlin", name: "R. Dahlin", team: "BUF", position: "D", headshotUrl: headshot(8480839), salary: "$6.0M", years: 1, status: "RFA" },
  { id: "boeser", name: "B. Boeser", team: "VAN", position: "RW", headshotUrl: headshot(8478444), salary: "$5.5M", years: 1, status: "UFA" },
  { id: "thompson", name: "T. Thompson", team: "BUF", position: "C", headshotUrl: headshot(8479420), salary: "$5.0M", years: 1, status: "UFA" },
  { id: "kane", name: "P. Kane", team: "DET", position: "RW", headshotUrl: headshot(8474141), salary: "$4.0M", years: 1, status: "UFA" },
  { id: "skinner", name: "J. Skinner", team: "EDM", position: "LW", headshotUrl: headshot(8477498), salary: "$3.5M", years: 1, status: "UFA" },
  { id: "guenther", name: "D. Guenther", team: "UTA", position: "RW", headshotUrl: headshot(8481585), salary: "$2.0M", years: 1, status: "ELC" },
  { id: "stankoven", name: "L. Stankoven", team: "DAL", position: "C", headshotUrl: headshot(8481583), salary: "$0.9M", years: 2, status: "ELC" },
];

/** Prospect pool (8) — drawn from the rookie class. */
export interface ProspectEntry {
  rookie: RookiePlayer;
  status: "Signed" | "Unsigned";
  year: number; // year on rookie roster (max 3)
}

export const FRANCHISE_PROSPECTS: ProspectEntry[] = ROOKIE_PLAYERS.slice(0, 8).map(
  (rookie, i) => ({
    rookie,
    status: i < 6 ? "Signed" : "Unsigned",
    year: (i % 3) + 1,
  })
);

/** Draft pick assets (6). */
export interface PickAsset {
  id: string;
  label: string;
  origin: string;
}

export const FRANCHISE_ASSETS: PickAsset[] = [
  { id: "p1", label: "2026 1st Round", origin: "Own" },
  { id: "p2", label: "2026 2nd Round", origin: "Own" },
  { id: "p3", label: "2027 1st Round", origin: "Own" },
  { id: "p4", label: "2027 2nd Round", origin: "via Puck Pirates" },
  { id: "p5", label: "2027 3rd Round", origin: "Own" },
  { id: "p6", label: "2028 1st Round", origin: "Own" },
];
