import type {
  DraftSetup,
  InviteState,
  RosterRequirements,
  ScoringConfigPayload,
  ScoringGroup,
  ScoringMetric,
  Team,
  ValidationIssue,
} from "./types";
import { asRecord } from "./api";

export const DEFAULT_ROSTER_REQUIREMENTS: RosterRequirements = {
  F: 4,
  C: 2,
  W: 3,
  D: 4,
  G: 2,
};

export const DEFAULT_SCORING: ScoringMetric[] = [
  { id: "skater-g", key: "g", code: "G", label: "Goals", group: "skater", enabled: true, value: "3" },
  { id: "skater-a", key: "a", code: "A", label: "Assists", group: "skater", enabled: true, value: "2" },
  { id: "skater-pm", key: "pm", code: "+/-", label: "Plus / minus", group: "skater", enabled: true, value: "0.25" },
  { id: "skater-pim", key: "pim", code: "PIM", label: "Penalty minutes", group: "skater", enabled: true, value: "0" },
  { id: "skater-shg", key: "shg", code: "SHG", label: "Short-handed goals", group: "skater", enabled: true, value: "2" },
  { id: "skater-shog", key: "shog", code: "SHOG", label: "Shootout goals", group: "skater", enabled: true, value: "1" },
  { id: "dbonus-g", key: "g", code: "DG", label: "Defence goals bonus", group: "dBonus", enabled: true, value: "2" },
  { id: "dbonus-a", key: "a", code: "DA", label: "Defence assists bonus", group: "dBonus", enabled: true, value: "1" },
  { id: "goalie-w", key: "w", code: "W", label: "Wins", group: "goalie", enabled: true, value: "2" },
  { id: "goalie-ga", key: "ga", code: "GA", label: "Goals against", group: "goalie", enabled: true, value: "-1.25" },
  { id: "goalie-sv", key: "sv", code: "S", label: "Saves", group: "goalie", enabled: true, value: "0.2" },
  { id: "goalie-ol", key: "ol", code: "OL", label: "Overtime losses", group: "goalie", enabled: true, value: "1" },
  { id: "goalie-shol", key: "shol", code: "SHOL", label: "Shootout losses", group: "goalie", enabled: true, value: "1" },
  { id: "goalie-so", key: "so", code: "SO", label: "Shutouts", group: "goalie", enabled: true, value: "1" },
];

export const SCORING_GROUPS: Array<{
  id: ScoringGroup;
  title: string;
  description: string;
}> = [
  { id: "skater", title: "Skaters", description: "Applied to all skaters" },
  { id: "dBonus", title: "Defence bonus", description: "Added for defencemen" },
  { id: "goalie", title: "Goalies", description: "Applied to goalie projections" },
];

export function cloneDefaultScoring(): ScoringMetric[] {
  return DEFAULT_SCORING.map((metric) => ({ ...metric }));
}

export function rosterTarget(rosterReqs: RosterRequirements): number {
  return Object.values(rosterReqs).reduce((total, value) => total + value, 0);
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

function stringValue(...values: unknown[]): string | undefined {
  return values.find((value): value is string => typeof value === "string");
}

function numberValue(...values: unknown[]): number | undefined {
  const match = values.find(
    (value): value is number => typeof value === "number" && Number.isFinite(value),
  );
  return match;
}

function booleanValue(...values: unknown[]): boolean | undefined {
  return values.find((value): value is boolean => typeof value === "boolean");
}

function normalizeInviteState(value: unknown): InviteState {
  if (typeof value !== "string") return "not-sent";
  const normalized = value.toLowerCase().replaceAll("_", "-").replaceAll(" ", "-");
  if (normalized === "joined" || normalized === "accepted") return "joined";
  if (normalized === "sent" || normalized === "delivered") return "sent";
  return "not-sent";
}

export function normalizeTeam(value: unknown, fallback?: Partial<Team>): Team {
  const record = asRecord(value);
  return {
    id: stringValue(record.id, record.teamId, fallback?.id) ?? "",
    name: stringValue(record.name, record.teamName, fallback?.name) ?? "Untitled team",
    ownerEmail: stringValue(record.ownerEmail, record.email, fallback?.ownerEmail) ?? "",
    inviteToken: stringValue(record.inviteToken, fallback?.inviteToken) ?? "",
    inviteState: normalizeInviteState(record.inviteState ?? record.inviteStatus ?? fallback?.inviteState),
    isAdminTeam:
      booleanValue(record.isAdminTeam, record.adminTeam, fallback?.isAdminTeam) ?? false,
    inviteLink: stringValue(record.inviteLink, record.inviteUrl, fallback?.inviteLink),
  };
}

function rosterFrom(value: unknown): RosterRequirements {
  const record = asRecord(value);
  const result = { ...DEFAULT_ROSTER_REQUIREMENTS };
  (Object.keys(result) as Array<keyof RosterRequirements>).forEach((position) => {
    const raw = record[position];
    if (typeof raw === "number" && Number.isInteger(raw) && raw >= 0) {
      result[position] = raw;
    }
  });
  return result;
}

function scoringSourceEntry(
  source: Record<string, unknown>,
  group: ScoringGroup,
  key: string,
): unknown {
  const groupAliases =
    group === "dBonus"
      ? ["dBonus", "defenceBonus", "defenseBonus", "defence"]
      : [group];

  for (const alias of groupAliases) {
    const groupRecord = asRecord(source[alias]);
    if (key in groupRecord) return groupRecord[key];
  }
  return undefined;
}

function normalizeScoring(value: unknown): ScoringMetric[] {
  if (Array.isArray(value)) {
    const byId = new Map<string, Record<string, unknown>>();
    value.forEach((entry) => {
      const record = asRecord(entry);
      const id = stringValue(record.id);
      if (id) byId.set(id, record);
    });
    return cloneDefaultScoring().map((metric) => {
      const entry = byId.get(metric.id);
      if (!entry) return metric;
      return {
        ...metric,
        enabled: booleanValue(entry.enabled) ?? metric.enabled,
        value: String(numberValue(entry.value, entry.points) ?? metric.value),
      };
    });
  }

  const source = asRecord(value);
  return cloneDefaultScoring().map((metric) => {
    const rawEntry = scoringSourceEntry(source, metric.group, metric.key);
    if (typeof rawEntry === "number" && Number.isFinite(rawEntry)) {
      return { ...metric, enabled: true, value: String(rawEntry) };
    }
    const entry = asRecord(rawEntry);
    const numeric = numberValue(entry.value, entry.points);
    return {
      ...metric,
      enabled: booleanValue(entry.enabled) ?? metric.enabled,
      value: numeric === undefined ? metric.value : String(numeric),
    };
  });
}

export function normalizeSetupResponse(
  raw: Record<string, unknown>,
  roomId: string,
  adminToken: string,
): DraftSetup {
  const room = asRecord(raw.room);
  const config = asRecord(raw.config ?? room.config);
  const draftConfig = asRecord(raw.draftConfig ?? config.draft ?? room.draftConfig);
  const rawTeams = raw.teams ?? room.teams;
  const scoringValue =
    raw.scoringConfig ?? config.scoringConfig ?? config.scoring ?? room.scoringConfig;

  return {
    roomId,
    adminToken,
    draftName:
      stringValue(raw.draftName, raw.name, room.draftName, room.name) ?? `Draft ${roomId}`,
    status: stringValue(raw.status, room.status) ?? "setup",
    teams: Array.isArray(rawTeams) ? rawTeams.map((team) => normalizeTeam(team)) : [],
    rounds: numberValue(raw.rounds, config.rounds, draftConfig.rounds) ?? 15,
    rosterReqs: rosterFrom(
      raw.rosterReqs ?? config.rosterReqs ?? draftConfig.rosterReqs,
    ),
    scoring: normalizeScoring(scoringValue),
  };
}

export function createEmptySetup(
  roomId: string,
  adminToken: string,
  draftName: string,
): DraftSetup {
  return {
    roomId,
    adminToken,
    draftName,
    status: "setup",
    teams: [],
    rounds: 15,
    rosterReqs: { ...DEFAULT_ROSTER_REQUIREMENTS },
    scoring: cloneDefaultScoring(),
  };
}

export function scoringPayload(scoring: ScoringMetric[]): ScoringConfigPayload {
  const payload: ScoringConfigPayload = { skater: {}, dBonus: {}, goalie: {} };
  scoring.forEach((metric) => {
    const parsed = Number(metric.value);
    payload[metric.group][metric.key] = {
      enabled: metric.enabled,
      value: Number.isFinite(parsed) ? parsed : 0,
    };
  });
  return payload;
}

export function validateSetup(setup: DraftSetup): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const name = setup.draftName.trim();
  if (!name || name.length > 80) {
    issues.push({
      section: "identity",
      message: !name
        ? "Give the draft a name."
        : "Keep the draft name to 80 characters or fewer.",
    });
  }

  if (setup.teams.length === 0) {
    issues.push({ section: "teams", message: "Add at least one team." });
  }

  setup.teams.forEach((team) => {
    if (!team.name.trim()) {
      issues.push({ section: "teams", message: "Every team needs a name." });
    }
    if (team.ownerEmail.trim() && !isValidEmail(team.ownerEmail)) {
      issues.push({
        section: "teams",
        message: `${team.name || "Each team"} has an invalid owner email.`,
      });
    }
  });

  const adminTeams = setup.teams.filter((team) => team.isAdminTeam);
  if (adminTeams.length !== 1) {
    issues.push({
      section: "teams",
      message:
        adminTeams.length === 0
          ? "Choose exactly one team as My team."
          : "Only one team can be My team.",
    });
  }

  if (!Number.isInteger(setup.rounds) || setup.rounds < 1 || setup.rounds > 30) {
    issues.push({ section: "format", message: "Rounds must be a whole number from 1 to 30." });
  }

  const invalidRoster = Object.values(setup.rosterReqs).some(
    (value) => !Number.isInteger(value) || value < 0,
  );
  if (invalidRoster) {
    issues.push({
      section: "format",
      message: "Roster requirements must be whole numbers of zero or greater.",
    });
  }

  const target = rosterTarget(setup.rosterReqs);
  if (setup.rounds < target) {
    issues.push({
      section: "format",
      message: `Add ${target - setup.rounds} round${target - setup.rounds === 1 ? "" : "s"} or lower the ${target}-player roster target.`,
    });
  }

  const invalidMetrics = setup.scoring.filter(
    (metric) => metric.enabled && (metric.value.trim() === "" || !Number.isFinite(Number(metric.value))),
  );
  if (invalidMetrics.length) {
    issues.push({
      section: "scoring",
      message: `Enter a valid point value for ${invalidMetrics.map((metric) => metric.code).join(", ")}.`,
    });
  }

  return issues;
}

export function sameRoster(a: RosterRequirements, b: RosterRequirements): boolean {
  return (Object.keys(a) as Array<keyof RosterRequirements>).every(
    (position) => a[position] === b[position],
  );
}

export function sameScoring(a: ScoringMetric[], b: ScoringMetric[]): boolean {
  return (
    a.length === b.length &&
    a.every((metric, index) => {
      const other = b[index];
      return (
        metric.id === other?.id &&
        metric.enabled === other.enabled &&
        metric.value === other.value
      );
    })
  );
}
