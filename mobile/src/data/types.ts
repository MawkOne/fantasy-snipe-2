// Core domain types — shaped like future Railway API responses.

export type Position = "C" | "LW" | "RW" | "D" | "G" | "UTIL" | "BN";
export type SkaterPosition = "C" | "LW" | "RW" | "D";

export type GameDayState = "start" | "sit" | "tbd" | "game";

export interface Team {
  id: string;
  name: string;
  abbrev: string;
  logoUrl?: string;
  record: { w: number; l: number; t?: number };
  division?: string;
  rank?: number;
}

export interface Player {
  id: string;
  name: string;
  team: string; // NHL abbrev e.g. "TOR"
  position: Position;
  headshotUrl?: string;
  injured?: boolean;
  opponent?: string; // e.g. "vs VAN" or "@ COL"
  gameTime?: string; // e.g. "7:00 PM"
  liveStatus?: string; // e.g. "2nd 8:14"
  projectedPoints: number;
  /** For lineup week view: which days this player has games (0 = Mon). */
  gameDays?: number[];
  /** Goalie per-day start states for the week. */
  goalieDays?: GameDayState[];
  /** Projected weekly starts (goalies). */
  projectedStarts?: number;
  startProbability?: number; // 0-100, goalies
  /** Salary / contract */
  capHit?: string; // e.g. "$12.5M"
  contractYears?: number; // years remaining
  contractType?: string; // e.g. "UFA", "RFA", "ELC"
  /** Performance stats (season) */
  goals?: number;
  assists?: number;
  points?: number;
  plusMinus?: number;
  sog?: number; // shots on goal
  hits?: number;
  blk?: number; // blocks
  wins?: number; // goalies
  gaa?: number; // goalies
  svPct?: number; // goalies
}

export interface RosterSlot {
  slot: Position; // e.g. "C", "G1", "BN"
  player: Player | null;
}

export interface LineupSummary {
  scheduledStarts: number;
  benchConflicts: number;
  emptyOpportunities: number;
}

export interface League {
  id: string;
  name: string;
  sport: string;
  myTeam: Team;
}
