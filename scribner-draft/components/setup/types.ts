export type InviteState = "not-sent" | "sent" | "joined";
export type ScoringGroup = "skater" | "dBonus" | "goalie";
export type SaveStatus = "idle" | "saving" | "saved" | "error";

export interface Team {
  id: string;
  name: string;
  ownerEmail: string;
  inviteToken: string;
  inviteState: InviteState;
  isAdminTeam: boolean;
  inviteLink?: string;
}

export interface TeamInput {
  teamName: string;
  ownerEmail: string;
  isAdminTeam: boolean;
}

export interface RosterRequirements {
  C: number;
  W: number;
  F: number;
  D: number;
  G: number;
}

export interface ScoringMetric {
  id: string;
  key: string;
  code: string;
  label: string;
  group: ScoringGroup;
  enabled: boolean;
  value: string;
}

export interface DraftSetup {
  roomId: string;
  adminToken: string;
  draftName: string;
  status: string;
  teams: Team[];
  rounds: number;
  rosterReqs: RosterRequirements;
  scoring: ScoringMetric[];
}

export interface ActionFeedback {
  tone: "success" | "error" | "warning" | "info";
  message: string;
}

export interface ValidationIssue {
  section: "identity" | "teams" | "format" | "scoring";
  message: string;
}

export interface TeamBusyState {
  action: "add" | "edit" | "remove" | "admin" | "invite";
  teamId?: string;
}

export interface AdminSession {
  roomId: string;
  adminToken: string;
}

export interface ScoringConfigPayload {
  skater: Record<string, { enabled: boolean; value: number }>;
  dBonus: Record<string, { enabled: boolean; value: number }>;
  goalie: Record<string, { enabled: boolean; value: number }>;
}
