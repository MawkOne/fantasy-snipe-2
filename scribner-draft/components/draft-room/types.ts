export type RoomRole = "gm" | "admin";
export type RoomPhase = "waiting" | "picking" | "revealed" | "completed";
export type RoomTab = "draft" | "roster" | "results" | "commissioner";
export type ConnectionStatus = "connecting" | "connected" | "reconnecting" | "error";
export type RosterSlotKey = "C" | "W" | "F" | "D" | "G";
export type CommissionerAction = "start-round" | "reveal" | "finish-draft";
export type DraftManagementView = "rosters" | "setup" | "delete";
export type ScoringGroup = "skater" | "dBonus" | "goalie";

export interface ScoringMetricConfig {
  enabled: boolean;
  value: number;
}

export interface ScoringConfig {
  skater: Record<string, ScoringMetricConfig>;
  dBonus: Record<string, ScoringMetricConfig>;
  goalie: Record<string, ScoringMetricConfig>;
}

export interface ProjectedStats {
  goals?: number;
  assists?: number;
  plusMinus?: number;
  penaltyMinutes?: number;
  shortHandedGoals?: number;
  shootoutGoals?: number;
  wins?: number;
  goalsAgainst?: number;
  saves?: number;
  overtimeLosses?: number;
  shootoutLosses?: number;
  shutouts?: number;
}

export interface DraftPlayer {
  id: string;
  name: string;
  position: string;
  team: string;
  headshot?: string;
  adp?: number | null;
  rank?: number;
  writeup?: string;
  projectedPts: number;
  stats: ProjectedStats;
  assignmentSource?: string;
  available?: boolean;
  rosteredByTeamIds?: string[];
}

export interface RosterRequirement {
  key: RosterSlotKey;
  current: number;
  required: number;
  state: "unmet" | "met" | "exceeded";
}

export type RosterStatus = Record<RosterSlotKey, RosterRequirement>;
export type RosterRequirements = Record<RosterSlotKey, number>;

export interface RoomTeam {
  id: string;
  name: string;
  inviteToken?: string;
  submitted: boolean;
  isViewer: boolean;
  roster: DraftPlayer[];
  rosterStatus: RosterStatus;
  guidance: string[];
  totalProjectedPts: number;
}

export interface RevealedResult {
  teamId: string;
  teamName: string;
  player: DraftPlayer | null;
}

export interface RevealedRound {
  round: number;
  results: RevealedResult[];
}

export interface RoomViewer {
  teamId: string;
  teamName: string;
  myPick: DraftPlayer | null;
  roster: DraftPlayer[];
  rosterStatus: RosterStatus;
  guidance: string[];
  totalProjectedPts: number;
}

export interface RoomActionFlags {
  canStartRound: boolean;
  canReveal: boolean;
  canFinishDraft: boolean;
}

export interface DraftRoomState {
  draftName: string;
  roomCode: string;
  roomStatus: string;
  phase: RoomPhase;
  currentRound: number;
  totalRounds: number;
  availablePlayers: DraftPlayer[];
  allPlayers: DraftPlayer[];
  manualPlayerPool: DraftPlayer[];
  availableCount: number;
  teams: RoomTeam[];
  submittedCount: number;
  rosterReqs: RosterRequirements;
  scoringConfig: ScoringConfig;
  viewer: RoomViewer | null;
  revealedRounds: RevealedRound[];
  actionFlags: RoomActionFlags;
}
