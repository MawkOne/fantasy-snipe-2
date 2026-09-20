import { randomBytes, randomUUID, timingSafeEqual } from "crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  writeFileSync,
} from "fs";
import { join } from "path";
import postgres from "postgres";
import {
  DEFAULT_SCORING_CONFIG,
  projectedPoints,
  type Player,
  type ScoringConfig,
  type ScoringMetric,
} from "./players";
import { DRAFT_PLAYERS as PLAYERS } from "./draft_players";

export type RoomStatus = "setup" | "in_progress" | "completed";
export type RoundStatus = "submitting" | "revealed";
export type InviteState = "not_sent" | "sent" | "joined";

export interface RosterRequirements {
  C: number;
  W: number;
  F: number;
  D: number;
  G: number;
}

export interface DraftConfig {
  rounds: number;
  rosterReqs: RosterRequirements;
}

export interface Team {
  id: string;
  name: string;
  ownerEmail: string | null;
  inviteToken: string;
  inviteState: InviteState;
  inviteSentAt: number | null;
  joinedAt: number | null;
  createdAt: number;
}

export interface SealedPick {
  teamId: string;
  playerId: string;
  submittedAt: number;
  revealedAt: number | null;
}

export interface Round {
  number: number;
  status: RoundStatus;
  picks: SealedPick[];
  startedAt: number;
  revealedAt: number | null;
}

export interface RosterEntry {
  teamId: string;
  playerId: string;
  roundNumber: number;
  addedAt: number;
}

export interface ManualRosterEntry {
  id: string;
  teamId: string;
  playerId: string;
  createdAt: number;
}

export interface DraftRoom {
  id: string;
  name: string;
  adminToken: string;
  status: RoomStatus;
  currentRound: number;
  rounds: Round[];
  teams: Team[];
  rosters: RosterEntry[];
  manualRosters: ManualRosterEntry[];
  availablePlayerIds: string[];
  draftConfig: DraftConfig;
  scoringConfig: ScoringConfig;
  adminTeamId: string | null;
  createdAt: number;
  updatedAt: number;
}

export interface RosterRequirementState {
  current: number;
  required: number;
  state: "unmet" | "met" | "exceeded";
  guidance: string;
}

export interface RosterStatus {
  C: RosterRequirementState;
  W: RosterRequirementState;
  F: RosterRequirementState;
  D: RosterRequirementState;
  G: RosterRequirementState;
  counts: {
    C: number;
    LW: number;
    RW: number;
    W: number;
    F: number;
    D: number;
    G: number;
  };
  totalPlayers: number;
  targetPlayers: number;
  totalProjectedPoints: number;
  guidance: string[];
}

export class DraftError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "DraftError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const DEFAULT_ROSTER_REQUIREMENTS: RosterRequirements = {
  F: 4,
  C: 2,
  W: 3,
  D: 4,
  G: 2,
};

const DATA_DIR = join(process.cwd(), ".data");
const DATA_FILE = join(DATA_DIR, "rooms.json");
const PLAYER_BY_ID = new Map(PLAYERS.map((player) => [player.id, player]));
const PLAYER_IDS = new Set(PLAYER_BY_ID.keys());
const MAX_ROUNDS = 30;
const MAX_NAME_LENGTH = 80;
const SCORING_KEYS = {
  skater: ["g", "a", "pm", "pim", "shg", "shog"],
  dBonus: ["g", "a"],
  goalie: ["w", "ga", "sv", "ol", "shol", "so"],
} as const;

export const MANUAL_ASSIGNMENT_AVAILABILITY_POLICY = {
  code: "commissioner_shared_ownership_allowed",
  sharedOwnershipAllowed: true,
  duplicateWithinTeamAllowed: false,
  explanation:
    "A commissioner may assign a player already rostered by another team because same-round duplicate ownership is valid. The same team cannot roster that player twice, and the player returns to shared availability only after no team rosters them.",
} as const;

type ScoringGroup = keyof typeof SCORING_KEYS;
type QueryExecutor = postgres.Sql | postgres.TransactionSql;

let sqlClient: postgres.Sql | null = null;
let sqlClientUrl = "";
let schemaPromise: Promise<void> | null = null;
let jsonQueue: Promise<void> = Promise.resolve();

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function asTrimmedString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function asTimestamp(value: unknown, fallback: number): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (value instanceof Date && Number.isFinite(value.getTime())) {
    return value.getTime();
  }
  if (typeof value === "string") {
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function integerInRange(
  value: unknown,
  fallback: number,
  minimum: number,
  maximum: number,
): number {
  return typeof value === "number" &&
    Number.isInteger(value) &&
    value >= minimum &&
    value <= maximum
    ? value
    : fallback;
}

function roomCode(): string {
  return randomBytes(6).toString("hex").toUpperCase();
}

function secretToken(): string {
  return randomBytes(32).toString("base64url");
}

function normalizeRoomId(value: string): string {
  return value.trim().toUpperCase();
}

function secureTokenEqual(expected: string, supplied: unknown): boolean {
  if (typeof supplied !== "string" || !supplied) return false;
  const expectedBuffer = Buffer.from(expected);
  const suppliedBuffer = Buffer.from(supplied);
  return (
    expectedBuffer.length === suppliedBuffer.length &&
    timingSafeEqual(expectedBuffer, suppliedBuffer)
  );
}

function cloneScoringConfig(config: ScoringConfig): ScoringConfig {
  return {
    skater: {
      g: { ...config.skater.g },
      a: { ...config.skater.a },
      pm: { ...config.skater.pm },
      pim: { ...config.skater.pim },
      shg: { ...config.skater.shg },
      shog: { ...config.skater.shog },
    },
    dBonus: {
      g: { ...config.dBonus.g },
      a: { ...config.dBonus.a },
    },
    goalie: {
      w: { ...config.goalie.w },
      ga: { ...config.goalie.ga },
      sv: { ...config.goalie.sv },
      ol: { ...config.goalie.ol },
      shol: { ...config.goalie.shol },
      so: { ...config.goalie.so },
    },
  };
}

function normalizePersistedScoring(value: unknown): ScoringConfig {
  const normalized = cloneScoringConfig(DEFAULT_SCORING_CONFIG);
  if (!isRecord(value)) return normalized;

  for (const group of Object.keys(SCORING_KEYS) as ScoringGroup[]) {
    const rawGroup = value[group];
    if (!isRecord(rawGroup)) continue;

    for (const key of SCORING_KEYS[group]) {
      const rawMetric = rawGroup[key];
      const targetGroup = normalized[group] as unknown as Record<
        string,
        ScoringMetric
      >;
      const fallback = targetGroup[key];

      if (rawMetric === undefined) {
        targetGroup[key] = { enabled: false, value: fallback.value };
      } else if (typeof rawMetric === "number" && Number.isFinite(rawMetric)) {
        targetGroup[key] = { enabled: true, value: rawMetric };
      } else if (isRecord(rawMetric)) {
        const metricValue = rawMetric.value;
        targetGroup[key] = {
          enabled:
            typeof rawMetric.enabled === "boolean" ? rawMetric.enabled : true,
          value:
            typeof metricValue === "number" && Number.isFinite(metricValue)
              ? metricValue
              : fallback.value,
        };
      }
    }
  }

  return normalized;
}

function validateScoringConfigUpdate(
  value: unknown,
  current: ScoringConfig,
): ScoringConfig {
  if (!isRecord(value)) {
    throw new DraftError(
      400,
      "invalid_scoring_config",
      "Scoring config must be an object grouped by skater, dBonus, and goalie.",
    );
  }

  const allowedGroups = new Set(Object.keys(SCORING_KEYS));
  for (const key of Object.keys(value)) {
    if (!allowedGroups.has(key)) {
      throw new DraftError(
        400,
        "invalid_scoring_group",
        `Unknown scoring group '${key}'.`,
      );
    }
  }

  const next = cloneScoringConfig(current);
  let suppliedGroup = false;

  for (const group of Object.keys(SCORING_KEYS) as ScoringGroup[]) {
    if (!(group in value)) continue;
    suppliedGroup = true;
    const rawGroup = value[group];
    if (!isRecord(rawGroup)) {
      throw new DraftError(
        400,
        "invalid_scoring_group",
        `Scoring group '${group}' must be an object.`,
      );
    }

    const allowedKeys = new Set<string>(SCORING_KEYS[group]);
    for (const key of Object.keys(rawGroup)) {
      if (!allowedKeys.has(key)) {
        throw new DraftError(
          400,
          "invalid_scoring_metric",
          `Unknown ${group} scoring metric '${key}'.`,
        );
      }
    }

    const targetGroup = next[group] as unknown as Record<string, ScoringMetric>;
    for (const key of SCORING_KEYS[group]) {
      const rawMetric = rawGroup[key];
      const previous = targetGroup[key];

      if (rawMetric === undefined) {
        targetGroup[key] = { ...previous, enabled: false };
        continue;
      }

      if (typeof rawMetric === "number") {
        if (!Number.isFinite(rawMetric)) {
          throw new DraftError(
            400,
            "invalid_scoring_value",
            `${group}.${key} must be a finite number.`,
          );
        }
        targetGroup[key] = { enabled: true, value: rawMetric };
        continue;
      }

      if (!isRecord(rawMetric)) {
        throw new DraftError(
          400,
          "invalid_scoring_metric",
          `${group}.${key} must be a number or { enabled, value } object.`,
        );
      }

      const enabled =
        typeof rawMetric.enabled === "boolean" ? rawMetric.enabled : true;
      const metricValue = rawMetric.value;
      if (
        metricValue !== undefined &&
        (typeof metricValue !== "number" || !Number.isFinite(metricValue))
      ) {
        throw new DraftError(
          400,
          "invalid_scoring_value",
          `${group}.${key}.value must be a finite number.`,
        );
      }
      if (enabled && metricValue === undefined) {
        throw new DraftError(
          400,
          "missing_scoring_value",
          `${group}.${key}.value is required when the metric is enabled.`,
        );
      }
      targetGroup[key] = {
        enabled,
        value:
          typeof metricValue === "number" ? metricValue : previous.value,
      };
    }
  }

  if (!suppliedGroup) {
    throw new DraftError(
      400,
      "empty_scoring_config",
      "Provide at least one scoring group to update.",
    );
  }

  return next;
}

function normalizePersistedRosterRequirements(
  value: unknown,
): RosterRequirements {
  const normalized = { ...DEFAULT_ROSTER_REQUIREMENTS };
  if (!isRecord(value)) return normalized;

  for (const key of Object.keys(normalized) as (keyof RosterRequirements)[]) {
    normalized[key] = integerInRange(value[key], normalized[key], 0, 1000);
  }
  return normalized;
}

function validateRosterRequirementsUpdate(
  value: unknown,
  current: RosterRequirements,
): RosterRequirements {
  if (!isRecord(value)) {
    throw new DraftError(
      400,
      "invalid_roster_requirements",
      "rosterReqs must be an object with C, W, F, D, and G values.",
    );
  }

  const next = { ...current };
  const allowed = new Set(["C", "W", "F", "D", "G"]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new DraftError(
        400,
        "invalid_roster_position",
        `Unknown roster requirement '${key}'. Use C, W, F, D, or G.`,
      );
    }
  }

  for (const key of allowed) {
    if (!(key in value)) continue;
    const count = value[key];
    if (
      typeof count !== "number" ||
      !Number.isInteger(count) ||
      count < 0
    ) {
      throw new DraftError(
        400,
        "invalid_roster_requirement",
        `${key} must be an integer of 0 or greater.`,
      );
    }
    if (count > 1000) {
      throw new DraftError(
        400,
        "invalid_roster_requirement",
        `${key} is too large; use a value of 1000 or less.`,
      );
    }
    next[key as keyof RosterRequirements] = count;
  }

  return next;
}

function validateCompleteRosterRequirements(
  value: unknown,
): RosterRequirements {
  if (!isRecord(value)) {
    throw new DraftError(
      400,
      "invalid_roster_requirements",
      "rosterReqs must be an object with C, W, F, D, and G values.",
    );
  }

  const requiredKeys = ["C", "W", "F", "D", "G"] as const;
  const allowed = new Set<string>(requiredKeys);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new DraftError(
        400,
        "invalid_roster_position",
        `Unknown roster requirement '${key}'. Use C, W, F, D, or G.`,
      );
    }
  }

  const normalized = {} as RosterRequirements;
  for (const key of requiredKeys) {
    if (!(key in value)) {
      throw new DraftError(
        400,
        "missing_roster_requirement",
        `rosterReqs.${key} is required for a live setup update.`,
      );
    }
    const count = value[key];
    if (
      typeof count !== "number" ||
      !Number.isInteger(count) ||
      count < 0 ||
      count > 1000
    ) {
      throw new DraftError(
        400,
        "invalid_roster_requirement",
        `rosterReqs.${key} must be an integer from 0 to 1000.`,
      );
    }
    normalized[key] = count;
  }
  return normalized;
}

function validateCompleteScoringConfig(value: unknown): ScoringConfig {
  if (!isRecord(value)) {
    throw new DraftError(
      400,
      "invalid_scoring_config",
      "scoringConfig must be a complete object grouped by skater, dBonus, and goalie.",
    );
  }

  const allowedGroups = new Set<string>(Object.keys(SCORING_KEYS));
  for (const key of Object.keys(value)) {
    if (!allowedGroups.has(key)) {
      throw new DraftError(
        400,
        "invalid_scoring_group",
        `Unknown scoring group '${key}'.`,
      );
    }
  }

  const normalized = cloneScoringConfig(DEFAULT_SCORING_CONFIG);
  for (const group of Object.keys(SCORING_KEYS) as ScoringGroup[]) {
    if (!(group in value)) {
      throw new DraftError(
        400,
        "missing_scoring_group",
        `scoringConfig.${group} is required for a live setup update.`,
      );
    }
    const rawGroup = value[group];
    if (!isRecord(rawGroup)) {
      throw new DraftError(
        400,
        "invalid_scoring_group",
        `Scoring group '${group}' must be an object.`,
      );
    }

    const allowedMetrics = new Set<string>(SCORING_KEYS[group]);
    for (const key of Object.keys(rawGroup)) {
      if (!allowedMetrics.has(key)) {
        throw new DraftError(
          400,
          "invalid_scoring_metric",
          `Unknown ${group} scoring metric '${key}'.`,
        );
      }
    }

    const targetGroup = normalized[group] as unknown as Record<
      string,
      ScoringMetric
    >;
    for (const key of SCORING_KEYS[group]) {
      if (!(key in rawGroup)) {
        throw new DraftError(
          400,
          "missing_scoring_metric",
          `scoringConfig.${group}.${key} is required for a live setup update.`,
        );
      }
      const rawMetric = rawGroup[key];
      if (typeof rawMetric === "number") {
        if (!Number.isFinite(rawMetric)) {
          throw new DraftError(
            400,
            "invalid_scoring_value",
            `scoringConfig.${group}.${key} must be a finite number.`,
          );
        }
        targetGroup[key] = { enabled: true, value: rawMetric };
        continue;
      }
      if (!isRecord(rawMetric)) {
        throw new DraftError(
          400,
          "invalid_scoring_metric",
          `scoringConfig.${group}.${key} must be a number or { enabled, value } object.`,
        );
      }

      const allowedMetricFields = new Set(["enabled", "value"]);
      for (const field of Object.keys(rawMetric)) {
        if (!allowedMetricFields.has(field)) {
          throw new DraftError(
            400,
            "invalid_scoring_metric",
            `Unknown field scoringConfig.${group}.${key}.${field}.`,
          );
        }
      }
      if (typeof rawMetric.enabled !== "boolean") {
        throw new DraftError(
          400,
          "invalid_scoring_enabled",
          `scoringConfig.${group}.${key}.enabled must be true or false.`,
        );
      }
      if (
        typeof rawMetric.value !== "number" ||
        !Number.isFinite(rawMetric.value)
      ) {
        throw new DraftError(
          400,
          "invalid_scoring_value",
          `scoringConfig.${group}.${key}.value must be a finite number.`,
        );
      }
      targetGroup[key] = {
        enabled: rawMetric.enabled,
        value: rawMetric.value,
      };
    }
  }

  return normalized;
}

function validateName(value: unknown, label: string): string {
  if (typeof value !== "string") {
    throw new DraftError(400, "invalid_name", `${label} is required.`);
  }
  const name = value.trim();
  if (!name) {
    throw new DraftError(400, "invalid_name", `${label} is required.`);
  }
  if (name.length > MAX_NAME_LENGTH) {
    throw new DraftError(
      400,
      "invalid_name",
      `${label} must be ${MAX_NAME_LENGTH} characters or fewer.`,
    );
  }
  return name;
}

function validateEmail(value: unknown): string | null {
  if (value === undefined || value === null || value === "") return null;
  if (typeof value !== "string") {
    throw new DraftError(
      400,
      "invalid_email",
      "Owner email must be a string or null.",
    );
  }
  const email = value.trim().toLowerCase();
  if (
    email.length > 254 ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  ) {
    throw new DraftError(
      400,
      "invalid_email",
      "Enter a valid owner email address.",
    );
  }
  return email;
}

function normalizePersistedEmail(value: unknown): string | null {
  const email = asTrimmedString(value).toLowerCase();
  return email && email.length <= 254 ? email : null;
}

function normalizeRoom(rawValue: unknown, idHint: string): DraftRoom {
  const raw = isRecord(rawValue) ? rawValue : {};
  const now = Date.now();
  const id = normalizeRoomId(asTrimmedString(raw.id) || idHint || roomCode());
  const rawStatus = raw.status;
  let status: RoomStatus =
    rawStatus === "in_progress" || rawStatus === "completed"
      ? rawStatus
      : "setup";
  if (rawStatus === "pending") status = "setup";

  const rawTeams = Array.isArray(raw.teams) ? raw.teams : [];
  const teams: Team[] = [];
  const legacyPicks = new Map<string, unknown[]>();
  const teamIds = new Set<string>();
  const inviteTokens = new Set<string>();

  for (const candidate of rawTeams) {
    if (!isRecord(candidate)) continue;
    let teamId = asTrimmedString(candidate.id) || randomUUID();
    while (teamIds.has(teamId)) teamId = randomUUID();
    teamIds.add(teamId);

    let inviteToken = asTrimmedString(candidate.inviteToken) || secretToken();
    while (inviteTokens.has(inviteToken)) inviteToken = secretToken();
    inviteTokens.add(inviteToken);

    const inviteState: InviteState =
      candidate.inviteState === "sent" || candidate.inviteState === "joined"
        ? candidate.inviteState
        : "not_sent";
    const createdAt = asTimestamp(candidate.createdAt, now);
    teams.push({
      id: teamId,
      name:
        asTrimmedString(candidate.name).slice(0, MAX_NAME_LENGTH) ||
        `Team ${teams.length + 1}`,
      ownerEmail: normalizePersistedEmail(
        candidate.ownerEmail ?? candidate.email,
      ),
      inviteToken,
      inviteState,
      inviteSentAt:
        candidate.inviteSentAt === null || candidate.inviteSentAt === undefined
          ? null
          : asTimestamp(candidate.inviteSentAt, createdAt),
      joinedAt:
        candidate.joinedAt === null || candidate.joinedAt === undefined
          ? null
          : asTimestamp(candidate.joinedAt, createdAt),
      createdAt,
    });

    legacyPicks.set(
      teamId,
      Array.isArray(candidate.picks) ? candidate.picks : [],
    );
  }

  const rawRounds = Array.isArray(raw.rounds) ? raw.rounds : [];
  const roundsByNumber = new Map<number, Round>();
  for (const candidate of rawRounds) {
    if (!isRecord(candidate)) continue;
    const number = integerInRange(candidate.number, 0, 1, MAX_ROUNDS);
    if (!number || roundsByNumber.has(number)) continue;
    const roundStatus: RoundStatus =
      candidate.status === "revealed" ? "revealed" : "submitting";
    const startedAt = asTimestamp(candidate.startedAt, now);
    const picks: SealedPick[] = [];
    const pickedTeams = new Set<string>();
    const rawPicks = Array.isArray(candidate.picks) ? candidate.picks : [];

    for (const rawPick of rawPicks) {
      if (!isRecord(rawPick)) continue;
      const teamId = asTrimmedString(rawPick.teamId);
      const playerId = asTrimmedString(rawPick.playerId);
      if (
        !teamIds.has(teamId) ||
        !PLAYER_IDS.has(playerId) ||
        pickedTeams.has(teamId)
      ) {
        continue;
      }
      pickedTeams.add(teamId);
      picks.push({
        teamId,
        playerId,
        submittedAt: asTimestamp(rawPick.submittedAt, startedAt),
        revealedAt:
          roundStatus === "revealed"
            ? asTimestamp(rawPick.revealedAt, now)
            : null,
      });
    }

    roundsByNumber.set(number, {
      number,
      status: roundStatus,
      picks,
      startedAt,
      revealedAt:
        roundStatus === "revealed"
          ? asTimestamp(candidate.revealedAt, now)
          : null,
    });
  }

  const rawCurrentRound = integerInRange(
    raw.currentRound,
    0,
    0,
    MAX_ROUNDS,
  );
  const maxLegacyRoster = Math.max(
    0,
    ...Array.from(legacyPicks.values(), (picks) => picks.length),
  );
  const inferredRoundCount = Math.max(rawCurrentRound, maxLegacyRoster);
  for (let number = 1; number <= inferredRoundCount; number += 1) {
    if (roundsByNumber.has(number)) continue;
    const revealed = number < rawCurrentRound || number <= maxLegacyRoster;
    roundsByNumber.set(number, {
      number,
      status: revealed ? "revealed" : "submitting",
      picks: [],
      startedAt: now,
      revealedAt: revealed ? now : null,
    });
  }

  const rounds = Array.from(roundsByNumber.values()).sort(
    (left, right) => left.number - right.number,
  );
  const currentRound = rounds.length ? rounds[rounds.length - 1].number : 0;
  if (currentRound > 0 && status === "setup") status = "in_progress";
  if (status === "completed" && rounds.length) {
    const lastRound = rounds[rounds.length - 1];
    lastRound.status = "revealed";
    lastRound.revealedAt ??= now;
    for (const pick of lastRound.picks) pick.revealedAt ??= now;
  }

  const rosterMap = new Map<string, RosterEntry>();
  const addRosterEntry = (
    teamId: string,
    playerId: string,
    roundNumber: number,
    addedAt: number,
  ) => {
    if (
      !teamIds.has(teamId) ||
      !PLAYER_IDS.has(playerId) ||
      !roundsByNumber.has(roundNumber)
    ) {
      return;
    }
    rosterMap.set(`${teamId}:${roundNumber}`, {
      teamId,
      playerId,
      roundNumber,
      addedAt,
    });
  };

  const hasPersistedRosters = Array.isArray(raw.rosters);
  const rawRosters = hasPersistedRosters ? (raw.rosters as unknown[]) : [];
  for (const candidate of rawRosters) {
    if (!isRecord(candidate)) continue;
    addRosterEntry(
      asTrimmedString(candidate.teamId),
      asTrimmedString(candidate.playerId),
      integerInRange(candidate.roundNumber, 0, 1, MAX_ROUNDS),
      asTimestamp(candidate.addedAt, now),
    );
  }

  // Older JSON shapes had picks but no explicit roster collection. Once a
  // roster collection exists it is authoritative, allowing commissioner
  // removals/replacements without mutating revealed pick history.
  if (!hasPersistedRosters) {
    for (const team of teams) {
      const picks = legacyPicks.get(team.id) ?? [];
      picks.forEach((candidate, index) => {
        const playerId = isRecord(candidate)
          ? asTrimmedString(candidate.playerId ?? candidate.id)
          : asTrimmedString(candidate);
        addRosterEntry(team.id, playerId, index + 1, now);
      });
    }

    for (const round of rounds) {
      if (round.status !== "revealed") continue;
      for (const pick of round.picks) {
        addRosterEntry(
          pick.teamId,
          pick.playerId,
          round.number,
          pick.revealedAt ?? round.revealedAt ?? now,
        );
      }
    }
  }

  const seenRosterTeamPlayers = new Set<string>();
  const rosters = Array.from(rosterMap.values())
    .sort(
      (left, right) =>
        left.roundNumber - right.roundNumber ||
        left.teamId.localeCompare(right.teamId),
    )
    .filter((entry) => {
      const teamPlayerKey = `${entry.teamId}:${entry.playerId}`;
      if (seenRosterTeamPlayers.has(teamPlayerKey)) return false;
      seenRosterTeamPlayers.add(teamPlayerKey);
      return true;
    });

  const manualRosters: ManualRosterEntry[] = [];
  const manualIds = new Set<string>();
  const rosteredTeamPlayers = new Set(
    rosters.map((entry) => `${entry.teamId}:${entry.playerId}`),
  );
  const rawManualRosters = Array.isArray(raw.manualRosters)
    ? raw.manualRosters
    : [];
  for (const candidate of rawManualRosters) {
    if (!isRecord(candidate)) continue;
    const teamId = asTrimmedString(candidate.teamId);
    const playerId = asTrimmedString(candidate.playerId);
    const teamPlayerKey = `${teamId}:${playerId}`;
    if (
      !teamIds.has(teamId) ||
      !PLAYER_IDS.has(playerId) ||
      rosteredTeamPlayers.has(teamPlayerKey)
    ) {
      continue;
    }

    let id = asTrimmedString(candidate.id) || randomUUID();
    while (manualIds.has(id)) id = randomUUID();
    manualIds.add(id);
    rosteredTeamPlayers.add(teamPlayerKey);
    manualRosters.push({
      id,
      teamId,
      playerId,
      createdAt: asTimestamp(candidate.createdAt, now),
    });
  }
  manualRosters.sort(
    (left, right) =>
      left.createdAt - right.createdAt || left.id.localeCompare(right.id),
  );

  const selectedPlayerIds = new Set([
    ...rosters.map((entry) => entry.playerId),
    ...manualRosters.map((entry) => entry.playerId),
  ]);
  const availablePlayerIds = PLAYERS.map((player) => player.id).filter(
    (playerId) => !selectedPlayerIds.has(playerId),
  );

  const rawDraftConfig = isRecord(raw.draftConfig) ? raw.draftConfig : {};
  const configuredRounds = integerInRange(
    rawDraftConfig.rounds ?? raw.totalRounds,
    1,
    1,
    MAX_ROUNDS,
  );
  const draftConfig: DraftConfig = {
    rounds: Math.min(MAX_ROUNDS, Math.max(configuredRounds, currentRound, 1)),
    rosterReqs: normalizePersistedRosterRequirements(
      rawDraftConfig.rosterReqs ?? raw.rosterReqs,
    ),
  };

  let adminTeamId = asTrimmedString(raw.adminTeamId) || null;
  if (adminTeamId && !teamIds.has(adminTeamId)) adminTeamId = null;
  if (!adminTeamId && status !== "setup" && teams.length) {
    adminTeamId = teams[0].id;
  }

  const createdAt = asTimestamp(raw.createdAt, now);
  return {
    id,
    name:
      asTrimmedString(raw.name ?? raw.draftName).slice(0, MAX_NAME_LENGTH) ||
      `Draft ${id}`,
    adminToken: asTrimmedString(raw.adminToken) || secretToken(),
    status,
    currentRound,
    rounds,
    teams,
    rosters,
    manualRosters,
    availablePlayerIds,
    draftConfig,
    scoringConfig: normalizePersistedScoring(
      raw.scoringConfig ?? raw.scoringMetrics,
    ),
    adminTeamId,
    createdAt,
    updatedAt: asTimestamp(raw.updatedAt, createdAt),
  };
}

function databaseUrl(): string {
  return (
    process.env.FANTASY_DATABASE_URL?.trim() ||
    process.env.DATABASE_URL?.trim() ||
    ""
  );
}

function usesPostgres(): boolean {
  return !!databaseUrl();
}

function assertLocalStorageAllowed(): void {
  if (
    !usesPostgres() &&
    process.env.NODE_ENV === "production" &&
    process.env.SCRIBNER_ALLOW_JSON_STORAGE !== "true"
  ) {
    throw new DraftError(
      503,
      "database_required",
      "Production draft storage requires DATABASE_URL or FANTASY_DATABASE_URL.",
    );
  }
}

function getSql(): postgres.Sql {
  const url = databaseUrl();
  if (!url) {
    throw new DraftError(
      503,
      "database_not_configured",
      "PostgreSQL is not configured for this environment.",
    );
  }
  if (!sqlClient || sqlClientUrl !== url) {
    sqlClient = postgres(url, {
      max: 5,
      idle_timeout: 20,
      connect_timeout: 10,
      prepare: false,
    });
    sqlClientUrl = url;
    schemaPromise = null;
  }
  return sqlClient;
}

async function initializeSchema(): Promise<void> {
  const sql = getSql();
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_rooms (
      id TEXT PRIMARY KEY,
      name VARCHAR(80) NOT NULL,
      admin_token TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL CHECK (status IN ('setup', 'in_progress', 'completed')),
      current_round INTEGER NOT NULL DEFAULT 0 CHECK (current_round >= 0),
      rounds_count INTEGER NOT NULL CHECK (rounds_count BETWEEN 1 AND 30),
      roster_requirements JSONB NOT NULL,
      scoring_metrics JSONB NOT NULL,
      admin_team_id TEXT,
      available_player_ids JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_teams (
      id TEXT PRIMARY KEY,
      room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
      name VARCHAR(80) NOT NULL,
      owner_email TEXT,
      invite_token TEXT NOT NULL UNIQUE,
      invite_state TEXT NOT NULL CHECK (invite_state IN ('not_sent', 'sent', 'joined')),
      invite_sent_at TIMESTAMPTZ,
      joined_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (room_id, id)
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_rounds (
      room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
      round_number INTEGER NOT NULL CHECK (round_number BETWEEN 1 AND 30),
      status TEXT NOT NULL CHECK (status IN ('submitting', 'revealed')),
      started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      revealed_at TIMESTAMPTZ,
      PRIMARY KEY (room_id, round_number)
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_picks (
      room_id TEXT NOT NULL,
      round_number INTEGER NOT NULL,
      team_id TEXT NOT NULL,
      player_id TEXT NOT NULL,
      submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      revealed_at TIMESTAMPTZ,
      PRIMARY KEY (room_id, round_number, team_id),
      FOREIGN KEY (room_id, round_number)
        REFERENCES scribner_rounds(room_id, round_number) ON DELETE CASCADE,
      FOREIGN KEY (room_id, team_id)
        REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_rosters (
      room_id TEXT NOT NULL,
      team_id TEXT NOT NULL,
      round_number INTEGER NOT NULL,
      player_id TEXT NOT NULL,
      added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (room_id, team_id, round_number),
      FOREIGN KEY (room_id, team_id)
        REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE,
      FOREIGN KEY (room_id, round_number)
        REFERENCES scribner_rounds(room_id, round_number) ON DELETE CASCADE
    )
  `;
  await sql`
    CREATE TABLE IF NOT EXISTS scribner_manual_rosters (
      id TEXT PRIMARY KEY,
      room_id TEXT NOT NULL REFERENCES scribner_rooms(id) ON DELETE CASCADE,
      team_id TEXT NOT NULL,
      player_id TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      UNIQUE (room_id, team_id, player_id),
      FOREIGN KEY (room_id, team_id)
        REFERENCES scribner_teams(room_id, id) ON DELETE CASCADE
    )
  `;
  await sql`
    CREATE INDEX IF NOT EXISTS scribner_teams_room_idx
      ON scribner_teams(room_id)
  `;
  await sql`
    CREATE INDEX IF NOT EXISTS scribner_teams_invite_token_idx
      ON scribner_teams(invite_token)
  `;
  await sql`
    CREATE INDEX IF NOT EXISTS scribner_picks_room_round_idx
      ON scribner_picks(room_id, round_number)
  `;
  await sql`
    CREATE INDEX IF NOT EXISTS scribner_rosters_room_team_idx
      ON scribner_rosters(room_id, team_id)
  `;
  await sql`
    CREATE INDEX IF NOT EXISTS scribner_manual_rosters_room_team_idx
      ON scribner_manual_rosters(room_id, team_id)
  `;
}

async function ensureSchema(): Promise<void> {
  if (!schemaPromise) {
    schemaPromise = initializeSchema().catch((error) => {
      schemaPromise = null;
      throw error;
    });
  }
  await schemaPromise;
}

function parseJsonColumn(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value) as unknown;
  } catch {
    return undefined;
  }
}

interface RoomRow {
  id: string;
  name: string;
  adminToken: string;
  status: string;
  currentRound: number;
  roundsCount: number;
  rosterRequirements: unknown;
  scoringMetrics: unknown;
  adminTeamId: string | null;
  availablePlayerIds: unknown;
  createdAt: Date | string;
  updatedAt: Date | string;
}

interface TeamRow {
  id: string;
  name: string;
  ownerEmail: string | null;
  inviteToken: string;
  inviteState: string;
  inviteSentAt: Date | string | null;
  joinedAt: Date | string | null;
  createdAt: Date | string;
}

interface RoundRow {
  number: number;
  status: string;
  startedAt: Date | string;
  revealedAt: Date | string | null;
}

interface PickRow {
  roundNumber: number;
  teamId: string;
  playerId: string;
  submittedAt: Date | string;
  revealedAt: Date | string | null;
}

interface RosterRow {
  teamId: string;
  roundNumber: number;
  playerId: string;
  addedAt: Date | string;
}

interface ManualRosterRow {
  id: string;
  teamId: string;
  playerId: string;
  createdAt: Date | string;
}

async function loadSqlRoom(
  executor: QueryExecutor,
  roomId: string,
  lock: boolean,
): Promise<DraftRoom | undefined> {
  const roomRows = lock
    ? await executor<RoomRow[]>`
        SELECT
          id,
          name,
          admin_token AS "adminToken",
          status,
          current_round AS "currentRound",
          rounds_count AS "roundsCount",
          roster_requirements AS "rosterRequirements",
          scoring_metrics AS "scoringMetrics",
          admin_team_id AS "adminTeamId",
          available_player_ids AS "availablePlayerIds",
          created_at AS "createdAt",
          updated_at AS "updatedAt"
        FROM scribner_rooms
        WHERE id = ${roomId}
        FOR UPDATE
      `
    : await executor<RoomRow[]>`
        SELECT
          id,
          name,
          admin_token AS "adminToken",
          status,
          current_round AS "currentRound",
          rounds_count AS "roundsCount",
          roster_requirements AS "rosterRequirements",
          scoring_metrics AS "scoringMetrics",
          admin_team_id AS "adminTeamId",
          available_player_ids AS "availablePlayerIds",
          created_at AS "createdAt",
          updated_at AS "updatedAt"
        FROM scribner_rooms
        WHERE id = ${roomId}
      `;
  const roomRow = roomRows[0];
  if (!roomRow) return undefined;

  const teamRows = await executor<TeamRow[]>`
    SELECT
      id,
      name,
      owner_email AS "ownerEmail",
      invite_token AS "inviteToken",
      invite_state AS "inviteState",
      invite_sent_at AS "inviteSentAt",
      joined_at AS "joinedAt",
      created_at AS "createdAt"
    FROM scribner_teams
    WHERE room_id = ${roomId}
    ORDER BY created_at, id
  `;
  const roundRows = await executor<RoundRow[]>`
    SELECT
      round_number AS "number",
      status,
      started_at AS "startedAt",
      revealed_at AS "revealedAt"
    FROM scribner_rounds
    WHERE room_id = ${roomId}
    ORDER BY round_number
  `;
  const pickRows = await executor<PickRow[]>`
    SELECT
      round_number AS "roundNumber",
      team_id AS "teamId",
      player_id AS "playerId",
      submitted_at AS "submittedAt",
      revealed_at AS "revealedAt"
    FROM scribner_picks
    WHERE room_id = ${roomId}
    ORDER BY round_number, submitted_at, team_id
  `;
  const rosterRows = await executor<RosterRow[]>`
    SELECT
      team_id AS "teamId",
      round_number AS "roundNumber",
      player_id AS "playerId",
      added_at AS "addedAt"
    FROM scribner_rosters
    WHERE room_id = ${roomId}
    ORDER BY round_number, team_id
  `;
  const manualRosterRows = await executor<ManualRosterRow[]>`
    SELECT
      id,
      team_id AS "teamId",
      player_id AS "playerId",
      created_at AS "createdAt"
    FROM scribner_manual_rosters
    WHERE room_id = ${roomId}
    ORDER BY created_at, id
  `;

  return normalizeRoom(
    {
      id: roomRow.id,
      name: roomRow.name,
      adminToken: roomRow.adminToken,
      status: roomRow.status,
      currentRound: Number(roomRow.currentRound),
      draftConfig: {
        rounds: Number(roomRow.roundsCount),
        rosterReqs: parseJsonColumn(roomRow.rosterRequirements),
      },
      scoringConfig: parseJsonColumn(roomRow.scoringMetrics),
      adminTeamId: roomRow.adminTeamId,
      availablePlayerIds: parseJsonColumn(roomRow.availablePlayerIds),
      createdAt: roomRow.createdAt,
      updatedAt: roomRow.updatedAt,
      teams: teamRows.map((team) => ({
        ...team,
        inviteSentAt: team.inviteSentAt,
        joinedAt: team.joinedAt,
      })),
      rounds: roundRows.map((round) => ({
        ...round,
        picks: pickRows.filter(
          (pick) => Number(pick.roundNumber) === Number(round.number),
        ),
      })),
      rosters: rosterRows,
      manualRosters: manualRosterRows,
    },
    roomId,
  );
}

async function writeSqlRoom(
  transaction: postgres.TransactionSql,
  room: DraftRoom,
): Promise<void> {
  room.updatedAt = Date.now();
  await transaction`
    INSERT INTO scribner_rooms (
      id,
      name,
      admin_token,
      status,
      current_round,
      rounds_count,
      roster_requirements,
      scoring_metrics,
      admin_team_id,
      available_player_ids,
      created_at,
      updated_at
    ) VALUES (
      ${room.id},
      ${room.name},
      ${room.adminToken},
      ${room.status},
      ${room.currentRound},
      ${room.draftConfig.rounds},
      ${JSON.stringify(room.draftConfig.rosterReqs)}::jsonb,
      ${JSON.stringify(room.scoringConfig)}::jsonb,
      ${room.adminTeamId},
      ${JSON.stringify(room.availablePlayerIds)}::jsonb,
      ${new Date(room.createdAt)},
      ${new Date(room.updatedAt)}
    )
    ON CONFLICT (id) DO UPDATE SET
      name = EXCLUDED.name,
      admin_token = EXCLUDED.admin_token,
      status = EXCLUDED.status,
      current_round = EXCLUDED.current_round,
      rounds_count = EXCLUDED.rounds_count,
      roster_requirements = EXCLUDED.roster_requirements,
      scoring_metrics = EXCLUDED.scoring_metrics,
      admin_team_id = EXCLUDED.admin_team_id,
      available_player_ids = EXCLUDED.available_player_ids,
      updated_at = EXCLUDED.updated_at
  `;

  await transaction`DELETE FROM scribner_manual_rosters WHERE room_id = ${room.id}`;
  await transaction`DELETE FROM scribner_rosters WHERE room_id = ${room.id}`;
  await transaction`DELETE FROM scribner_picks WHERE room_id = ${room.id}`;
  await transaction`DELETE FROM scribner_rounds WHERE room_id = ${room.id}`;
  await transaction`DELETE FROM scribner_teams WHERE room_id = ${room.id}`;

  for (const team of room.teams) {
    await transaction`
      INSERT INTO scribner_teams (
        id,
        room_id,
        name,
        owner_email,
        invite_token,
        invite_state,
        invite_sent_at,
        joined_at,
        created_at
      ) VALUES (
        ${team.id},
        ${room.id},
        ${team.name},
        ${team.ownerEmail},
        ${team.inviteToken},
        ${team.inviteState},
        ${team.inviteSentAt ? new Date(team.inviteSentAt) : null},
        ${team.joinedAt ? new Date(team.joinedAt) : null},
        ${new Date(team.createdAt)}
      )
    `;
  }

  for (const round of room.rounds) {
    await transaction`
      INSERT INTO scribner_rounds (
        room_id,
        round_number,
        status,
        started_at,
        revealed_at
      ) VALUES (
        ${room.id},
        ${round.number},
        ${round.status},
        ${new Date(round.startedAt)},
        ${round.revealedAt ? new Date(round.revealedAt) : null}
      )
    `;
    for (const pick of round.picks) {
      await transaction`
        INSERT INTO scribner_picks (
          room_id,
          round_number,
          team_id,
          player_id,
          submitted_at,
          revealed_at
        ) VALUES (
          ${room.id},
          ${round.number},
          ${pick.teamId},
          ${pick.playerId},
          ${new Date(pick.submittedAt)},
          ${pick.revealedAt ? new Date(pick.revealedAt) : null}
        )
      `;
    }
  }

  for (const entry of room.rosters) {
    await transaction`
      INSERT INTO scribner_rosters (
        room_id,
        team_id,
        round_number,
        player_id,
        added_at
      ) VALUES (
        ${room.id},
        ${entry.teamId},
        ${entry.roundNumber},
        ${entry.playerId},
        ${new Date(entry.addedAt)}
      )
    `;
  }

  for (const entry of room.manualRosters) {
    await transaction`
      INSERT INTO scribner_manual_rosters (
        id,
        room_id,
        team_id,
        player_id,
        created_at
      ) VALUES (
        ${entry.id},
        ${room.id},
        ${entry.teamId},
        ${entry.playerId},
        ${new Date(entry.createdAt)}
      )
    `;
  }
}

function ensureDataDirectory(): void {
  if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });
}

function saveJsonRooms(rooms: Map<string, DraftRoom>): void {
  ensureDataDirectory();
  const temporaryFile = `${DATA_FILE}.${process.pid}.tmp`;
  writeFileSync(
    temporaryFile,
    JSON.stringify(Object.fromEntries(rooms), null, 2),
    "utf8",
  );
  renameSync(temporaryFile, DATA_FILE);
}

function loadJsonRooms(): Map<string, DraftRoom> {
  ensureDataDirectory();
  if (!existsSync(DATA_FILE)) return new Map();

  let parsed: unknown;
  try {
    parsed = JSON.parse(readFileSync(DATA_FILE, "utf8")) as unknown;
  } catch (error) {
    console.error("Failed to read local Scribner draft data:", error);
    throw new DraftError(
      500,
      "local_data_invalid",
      `Local draft data at ${DATA_FILE} is not valid JSON. Fix or back up the file before retrying.`,
    );
  }

  const entries: [string, unknown][] = Array.isArray(parsed)
    ? parsed
        .filter(isRecord)
        .map((room) => [asTrimmedString(room.id), room])
    : isRecord(parsed)
      ? Object.entries(parsed)
      : [];
  const rooms = new Map<string, DraftRoom>();
  for (const [idHint, rawRoom] of entries) {
    const room = normalizeRoom(rawRoom, idHint);
    rooms.set(room.id, room);
  }

  const normalizedJson = JSON.stringify(Object.fromEntries(rooms));
  if (normalizedJson !== JSON.stringify(parsed)) saveJsonRooms(rooms);
  return rooms;
}

async function withJsonLock<T>(task: () => T | Promise<T>): Promise<T> {
  let release: () => void = () => {};
  const previous = jsonQueue;
  jsonQueue = new Promise<void>((resolve) => {
    release = resolve;
  });
  await previous;
  try {
    return await task();
  } finally {
    release();
  }
}

async function runStorageOperation<T>(task: () => Promise<T>): Promise<T> {
  try {
    return await task();
  } catch (error) {
    if (error instanceof DraftError) throw error;
    console.error("Scribner draft storage operation failed:", error);
    throw new DraftError(
      503,
      "storage_unavailable",
      "Draft storage is temporarily unavailable. Check the database connection and retry.",
    );
  }
}

async function readStoredRoom(roomIdValue: string): Promise<DraftRoom | undefined> {
  const roomId = normalizeRoomId(roomIdValue);
  return runStorageOperation(async () => {
    if (usesPostgres()) {
      await ensureSchema();
      return loadSqlRoom(getSql(), roomId, false);
    }
    assertLocalStorageAllowed();
    return withJsonLock(() => loadJsonRooms().get(roomId));
  });
}

async function mutateStoredRoom<T>(
  roomIdValue: string,
  mutation: (room: DraftRoom) => T | Promise<T>,
): Promise<T> {
  const roomId = normalizeRoomId(roomIdValue);
  return runStorageOperation(async () => {
    if (usesPostgres()) {
      await ensureSchema();
      const transactionResult = await getSql().begin(async (transaction) => {
        const room = await loadSqlRoom(transaction, roomId, true);
        if (!room) {
          throw new DraftError(404, "room_not_found", "Draft room not found.");
        }
        const result = await mutation(room);
        await writeSqlRoom(transaction, room);
        return result;
      });
      return transactionResult as T;
    }

    assertLocalStorageAllowed();
    return withJsonLock(async () => {
      const rooms = loadJsonRooms();
      const room = rooms.get(roomId);
      if (!room) {
        throw new DraftError(404, "room_not_found", "Draft room not found.");
      }
      const result = await mutation(room);
      room.updatedAt = Date.now();
      rooms.set(room.id, room);
      saveJsonRooms(rooms);
      return result;
    });
  });
}

async function insertStoredRoom(room: DraftRoom): Promise<boolean> {
  return runStorageOperation(async () => {
    if (usesPostgres()) {
      await ensureSchema();
      const inserted = await getSql()<Array<{ id: string }>>`
        INSERT INTO scribner_rooms (
          id,
          name,
          admin_token,
          status,
          current_round,
          rounds_count,
          roster_requirements,
          scoring_metrics,
          admin_team_id,
          available_player_ids,
          created_at,
          updated_at
        ) VALUES (
          ${room.id},
          ${room.name},
          ${room.adminToken},
          ${room.status},
          ${room.currentRound},
          ${room.draftConfig.rounds},
          ${JSON.stringify(room.draftConfig.rosterReqs)}::jsonb,
          ${JSON.stringify(room.scoringConfig)}::jsonb,
          ${room.adminTeamId},
          ${JSON.stringify(room.availablePlayerIds)}::jsonb,
          ${new Date(room.createdAt)},
          ${new Date(room.updatedAt)}
        )
        ON CONFLICT (id) DO NOTHING
        RETURNING id
      `;
      return inserted.length === 1;
    }

    assertLocalStorageAllowed();
    return withJsonLock(() => {
      const rooms = loadJsonRooms();
      if (rooms.has(room.id)) return false;
      rooms.set(room.id, room);
      saveJsonRooms(rooms);
      return true;
    });
  });
}

async function requireStoredRoom(roomId: string): Promise<DraftRoom> {
  const room = await readStoredRoom(roomId);
  if (!room) {
    throw new DraftError(404, "room_not_found", "Draft room not found.");
  }
  return room;
}

function requireAdmin(room: DraftRoom, suppliedToken: unknown): void {
  if (typeof suppliedToken !== "string" || !suppliedToken) {
    throw new DraftError(
      401,
      "admin_token_required",
      "adminToken is required for this action.",
    );
  }
  if (!secureTokenEqual(room.adminToken, suppliedToken)) {
    throw new DraftError(403, "invalid_admin_token", "Invalid admin token.");
  }
}

function requireTeamByToken(room: DraftRoom, suppliedToken: unknown): Team {
  if (typeof suppliedToken !== "string" || !suppliedToken) {
    throw new DraftError(
      401,
      "team_token_required",
      "teamToken (or inviteToken) is required; teamId alone is not accepted.",
    );
  }
  const team = room.teams.find((candidate) =>
    secureTokenEqual(candidate.inviteToken, suppliedToken),
  );
  if (!team) {
    throw new DraftError(403, "invalid_team_token", "Invalid team token.");
  }
  return team;
}

function requireSetup(room: DraftRoom): void {
  if (room.status !== "setup") {
    throw new DraftError(
      409,
      "draft_already_started",
      "Team structure and draft configuration cannot be changed after the draft starts.",
    );
  }
}

function findTeam(room: DraftRoom, teamIdValue: unknown): Team {
  const teamId = asTrimmedString(teamIdValue);
  if (!teamId) {
    throw new DraftError(400, "team_id_required", "teamId is required.");
  }
  const team = room.teams.find((candidate) => candidate.id === teamId);
  if (!team) {
    throw new DraftError(404, "team_not_found", "Team not found in this room.");
  }
  return team;
}

function findPlayer(
  playerIdValue: unknown,
  fieldName = "playerId",
): Player {
  const playerId = asTrimmedString(playerIdValue);
  if (!playerId) {
    throw new DraftError(
      400,
      "player_id_required",
      `${fieldName} is required.`,
      { field: fieldName },
    );
  }
  const player = PLAYER_BY_ID.get(playerId);
  if (!player) {
    throw new DraftError(
      404,
      "player_not_found",
      `Player '${playerId}' is not in the static player source.`,
      { field: fieldName, playerId },
    );
  }
  return player;
}

function currentRound(room: DraftRoom): Round | undefined {
  return room.rounds.find((round) => round.number === room.currentRound);
}

function invitationLink(roomId: string, token: string, origin?: string): string {
  const relative = `/room/${encodeURIComponent(roomId)}?invite=${encodeURIComponent(token)}`;
  if (!origin) return relative;
  try {
    return new URL(relative, `${origin.replace(/\/$/, "")}/`).toString();
  } catch {
    return relative;
  }
}

function projectedPlayer(player: Player) {
  return {
    ...player,
    projectedPts: projectedPoints(player),
  };
}

type CurrentRosterAssignment =
  | { assignmentType: "draft"; entry: RosterEntry }
  | { assignmentType: "manual"; entry: ManualRosterEntry };

function currentRosterAssignments(
  room: DraftRoom,
  teamId?: string,
): CurrentRosterAssignment[] {
  return [
    ...room.rosters
      .filter((entry) => !teamId || entry.teamId === teamId)
      .map(
        (entry): CurrentRosterAssignment => ({
          assignmentType: "draft",
          entry,
        }),
      ),
    ...room.manualRosters
      .filter((entry) => !teamId || entry.teamId === teamId)
      .map(
        (entry): CurrentRosterAssignment => ({
          assignmentType: "manual",
          entry,
        }),
      ),
  ];
}

function findCurrentRosterAssignment(
  room: DraftRoom,
  teamId: string,
  playerId: string,
): CurrentRosterAssignment | undefined {
  return currentRosterAssignments(room, teamId).find(
    ({ entry }) => entry.playerId === playerId,
  );
}

function rebuildPlayerAvailability(room: DraftRoom): void {
  const rosteredPlayerIds = new Set(
    currentRosterAssignments(room).map(({ entry }) => entry.playerId),
  );
  room.availablePlayerIds = PLAYERS.map((player) => player.id).filter(
    (playerId) => !rosteredPlayerIds.has(playerId),
  );
}

function playerOwnerTeamIds(room: DraftRoom, playerId: string): string[] {
  return Array.from(
    new Set(
      currentRosterAssignments(room)
        .filter(({ entry }) => entry.playerId === playerId)
        .map(({ entry }) => entry.teamId),
    ),
  );
}

type SerializedRosterPlayer = ReturnType<typeof projectedPlayer> & {
  playerId: string;
  assignmentId: string;
  rosterEntryId: string;
  assignmentType: "draft" | "manual";
  source: "draft" | "manual";
  isManual: boolean;
  manualRosterId: string | null;
  roundNumber: number | null;
  addedAt: number;
};

function rosterPlayers(
  room: DraftRoom,
  teamId: string,
): SerializedRosterPlayer[] {
  const assignments = currentRosterAssignments(room, teamId).sort(
    (left, right) => {
      if (left.assignmentType === "draft" && right.assignmentType === "draft") {
        return left.entry.roundNumber - right.entry.roundNumber;
      }
      if (left.assignmentType !== right.assignmentType) {
        return left.assignmentType === "draft" ? -1 : 1;
      }
      const leftCreatedAt =
        left.assignmentType === "manual"
          ? left.entry.createdAt
          : left.entry.addedAt;
      const rightCreatedAt =
        right.assignmentType === "manual"
          ? right.entry.createdAt
          : right.entry.addedAt;
      return leftCreatedAt - rightCreatedAt;
    },
  );
  const players: SerializedRosterPlayer[] = [];
  for (const assignment of assignments) {
    const player = PLAYER_BY_ID.get(assignment.entry.playerId);
    if (!player) continue;
    if (assignment.assignmentType === "draft") {
      const entry = assignment.entry;
      const assignmentId = `draft:${entry.teamId}:${entry.roundNumber}`;
      players.push({
        ...projectedPlayer(player),
        playerId: player.id,
        assignmentId,
        rosterEntryId: assignmentId,
        assignmentType: "draft",
        source: "draft",
        isManual: false,
        manualRosterId: null,
        roundNumber: entry.roundNumber,
        addedAt: entry.addedAt,
      });
    } else {
      const entry = assignment.entry;
      players.push({
        ...projectedPlayer(player),
        playerId: player.id,
        assignmentId: entry.id,
        rosterEntryId: entry.id,
        assignmentType: "manual",
        source: "manual",
        isManual: true,
        manualRosterId: entry.id,
        roundNumber: null,
        addedAt: entry.createdAt,
      });
    }
  }
  return players;
}

function allProjectedPlayers(room: DraftRoom) {
  return PLAYERS.map((player) => {
    const rosteredByTeamIds = playerOwnerTeamIds(room, player.id);
    const available = rosteredByTeamIds.length === 0;
    return {
      ...projectedPlayer(player),
      playerId: player.id,
      available,
      isAvailable: available,
      rosteredByTeamIds,
      rosteredTeamIds: rosteredByTeamIds,
      rosteredCount: rosteredByTeamIds.length,
    };
  });
}

function requirementState(
  current: number,
  required: number,
  singular: string,
  plural: string,
  completeLabel: string,
): RosterRequirementState {
  if (current < required) {
    const remaining = required - current;
    return {
      current,
      required,
      state: "unmet",
      guidance: `Need ${remaining} more ${remaining === 1 ? singular : plural}`,
    };
  }
  if (current === required) {
    return {
      current,
      required,
      state: "met",
      guidance: `${completeLabel} requirement complete`,
    };
  }
  const extra = current - required;
  return {
    current,
    required,
    state: "exceeded",
    guidance: `${completeLabel} requirement exceeded by ${extra}`,
  };
}

export function calculateRosterStatus(
  players: readonly Player[],
  rosterReqs: RosterRequirements,
  scoringConfig: ScoringConfig = DEFAULT_SCORING_CONFIG,
): RosterStatus {
  const counts = { C: 0, LW: 0, RW: 0, W: 0, F: 0, D: 0, G: 0 };
  for (const player of players) {
    counts[player.position] += 1;
  }
  counts.W = counts.LW + counts.RW;
  counts.F =
    Math.max(0, counts.C - rosterReqs.C) +
    Math.max(0, counts.W - rosterReqs.W);

  const C = requirementState(
    counts.C,
    rosterReqs.C,
    "centre",
    "centres",
    "Centre",
  );
  const W = requirementState(
    counts.W,
    rosterReqs.W,
    "winger",
    "wingers",
    "Winger",
  );
  const F = requirementState(
    counts.F,
    rosterReqs.F,
    "flex forward",
    "flex forwards",
    "Flex forward",
  );
  const D = requirementState(
    counts.D,
    rosterReqs.D,
    "defenceman",
    "defencemen",
    "Defence",
  );
  const G = requirementState(
    counts.G,
    rosterReqs.G,
    "goalie",
    "goalies",
    "Goalie",
  );

  return {
    C,
    W,
    F,
    D,
    G,
    counts,
    totalPlayers: players.length,
    targetPlayers:
      rosterReqs.C +
      rosterReqs.W +
      rosterReqs.F +
      rosterReqs.D +
      rosterReqs.G,
    totalProjectedPoints:
      Math.round(
        players.reduce(
          (total, player) =>
            total + projectedPoints(player),
          0,
        ) * 10,
      ) / 10,
    guidance: [F.guidance, C.guidance, W.guidance, D.guidance, G.guidance],
  };
}

export function getRosterStatus(
  teamOrPlayers: { picks?: Player[] } | readonly Player[],
  rosterReqs: RosterRequirements,
  scoringConfig: ScoringConfig = DEFAULT_SCORING_CONFIG,
): RosterStatus {
  const players: readonly Player[] = Array.isArray(teamOrPlayers)
    ? (teamOrPlayers as readonly Player[])
    : (teamOrPlayers as { picks?: Player[] }).picks ?? [];
  return calculateRosterStatus(players, rosterReqs, scoringConfig);
}

export function getTeamTotalPoints(
  teamOrPlayers: { picks?: Player[] } | readonly Player[],
  scoringConfig: ScoringConfig = DEFAULT_SCORING_CONFIG,
): number {
  const players: readonly Player[] = Array.isArray(teamOrPlayers)
    ? (teamOrPlayers as readonly Player[])
    : (teamOrPlayers as { picks?: Player[] }).picks ?? [];
  return (
    Math.round(
      players.reduce(
        (total, player) => total + projectedPoints(player),
        0,
      ) * 10,
    ) / 10
  );
}

function rosterStatusForTeam(room: DraftRoom, teamId: string): RosterStatus {
  const players = currentRosterAssignments(room, teamId).flatMap(({ entry }) => {
    const player = PLAYER_BY_ID.get(entry.playerId);
    return player ? [player] : [];
  });
  return calculateRosterStatus(
    players,
    room.draftConfig.rosterReqs,
    room.scoringConfig,
  );
}

function serializePick(room: DraftRoom, round: Round, pick: SealedPick) {
  const player = PLAYER_BY_ID.get(pick.playerId);
  return {
    roundNumber: round.number,
    teamId: pick.teamId,
    playerId: pick.playerId,
    playerName: player?.name ?? pick.playerId,
    player: player ? projectedPlayer(player) : null,
    submittedAt: pick.submittedAt,
    revealed: round.status === "revealed",
    revealedAt: pick.revealedAt,
  };
}

function revealedHistory(room: DraftRoom) {
  return room.rounds
    .filter((round) => round.status === "revealed")
    .map((round) => {
      const results = room.teams.map((team) => {
        const pick = round.picks.find((candidate) => candidate.teamId === team.id);
        return {
          teamId: team.id,
          teamName: team.name,
          pick: pick ? serializePick(room, round, pick) : null,
          player: pick
            ? (PLAYER_BY_ID.get(pick.playerId) ? projectedPlayer(PLAYER_BY_ID.get(pick.playerId)!) : null)
            : null,
        };
      });
      return {
        number: round.number,
        roundNumber: round.number,
        status: round.status,
        revealedAt: round.revealedAt,
        results,
        picks: results.filter((result) => result.pick !== null),
        missingTeams: results
          .filter((result) => result.pick === null)
          .map((result) => ({ id: result.teamId, name: result.teamName })),
      };
    });
}

function roomMetadata(room: DraftRoom) {
  const round = currentRound(room);
  return {
    roomId: room.id,
    roomCode: room.id,
    draftName: room.name,
    roomStatus: room.status,
    currentRound: room.currentRound,
    totalRounds: room.draftConfig.rounds,
    roundStatus: round?.status ?? null,
    rosterReqs: room.draftConfig.rosterReqs,
    scoringConfig: room.scoringConfig,
  };
}

function startDraftIssues(room: DraftRoom): string[] {
  const issues: string[] = [];
  if (room.teams.length === 0) issues.push("Add at least one team.");
  if (!room.adminTeamId) {
    issues.push("Select the admin's team.");
  } else if (!room.teams.some((team) => team.id === room.adminTeamId)) {
    issues.push("The selected admin team no longer exists.");
  }

  const rosterTarget = Object.values(room.draftConfig.rosterReqs).reduce(
    (total, requirement) => total + requirement,
    0,
  );
  if (room.draftConfig.rounds < rosterTarget) {
    issues.push(
      `Increase the draft to at least ${rosterTarget} rounds or lower the roster target.`,
    );
  }

  return issues;
}

function buildSetupState(room: DraftRoom, origin?: string) {
  const issues = startDraftIssues(room);
  return {
    roomId: room.id,
    roomCode: room.id,
    draftName: room.name,
    name: room.name,
    status: room.status,
    roomStatus: room.status,
    currentRound: room.currentRound,
    adminTeamId: room.adminTeamId,
    totalRounds: room.draftConfig.rounds,
    draftConfig: room.draftConfig,
    rosterReqs: room.draftConfig.rosterReqs,
    totalRosterTarget: Object.values(room.draftConfig.rosterReqs).reduce(
      (total, count) => total + count,
      0,
    ),
    scoringConfig: room.scoringConfig,
    teams: room.teams.map((team) => ({
      id: team.id,
      name: team.name,
      email: team.ownerEmail,
      ownerEmail: team.ownerEmail,
      inviteToken: team.inviteToken,
      teamToken: team.inviteToken,
      inviteState: team.inviteState,
      inviteSentAt: team.inviteSentAt,
      joinedAt: team.joinedAt,
      isAdminTeam: team.id === room.adminTeamId,
      inviteLink: invitationLink(room.id, team.inviteToken, origin),
    })),
    canStartDraft: room.status === "setup" && issues.length === 0,
    startDraftIssues: issues,
  };
}

function buildGmState(room: DraftRoom, team: Team) {
  const round = currentRound(room);
  const ownPick = round?.picks.find((pick) => pick.teamId === team.id);
  const myPicks = rosterPlayers(room, team.id);
  const rosterStatus = rosterStatusForTeam(room, team.id);
  const availablePlayers = room.availablePlayerIds.flatMap((playerId) => {
    const player = PLAYER_BY_ID.get(playerId);
    return player ? [projectedPlayer(player)] : [];
  });
  const teams = room.teams.map((candidate) => {
    const pick = round?.picks.find((item) => item.teamId === candidate.id);
    return {
      id: candidate.id,
      name: candidate.name,
      pickCount: currentRosterAssignments(room, candidate.id).length,
      submitted: !!pick,
      ...(round?.status === "revealed"
        ? { pick: pick ? serializePick(room, round, pick) : null }
        : {}),
    };
  });
  const history = revealedHistory(room);
  const serializedOwnPick =
    ownPick && round ? serializePick(room, round, ownPick) : null;
  const phase =
    room.status === "completed"
      ? "completed"
      : round?.status === "submitting"
        ? "picking"
        : round?.status === "revealed"
          ? "revealed"
          : "waiting";

  return {
    ...roomMetadata(room),
    phase,
    myTeam: { id: team.id, name: team.name },
    myTeamId: team.id,
    teamId: team.id,
    teamName: team.name,
    myPick: serializedOwnPick,
    myPicks,
    viewer: {
      teamId: team.id,
      teamName: team.name,
      myPick: serializedOwnPick,
      roster: myPicks,
      rosterStatus,
      guidance: rosterStatus.guidance,
      totalProjectedPts: rosterStatus.totalProjectedPoints,
    },
    availablePlayers,
    availableCount: availablePlayers.length,
    teams,
    submittedCount: round?.picks.length ?? 0,
    teamSubmissionStatuses: teams.map(({ id, name, submitted }) => ({
      id,
      name,
      submitted,
    })),
    rosterStatus,
    guidance: rosterStatus.guidance,
    totalProjectedPoints: rosterStatus.totalProjectedPoints,
    revealedHistory: history,
    revealedRounds: history.map(({ number, results }) => ({
      round: number,
      results: results.map(({ teamId, teamName, player }) => ({
        teamId,
        teamName,
        player,
      })),
    })),
    resultsHistory: history,
    actionFlags: {
      canStartRound: false,
      canReveal: false,
      canFinishDraft: false,
    },
  };
}

function buildAdminState(room: DraftRoom) {
  const round = currentRound(room);
  const allPlayers = allProjectedPlayers(room);
  const availablePlayers = allPlayers.filter((player) => player.available);
  const teamStates = room.teams.map((team) => {
    const pick = round?.picks.find((candidate) => candidate.teamId === team.id);
    const status = rosterStatusForTeam(room, team.id);
    return {
      id: team.id,
      name: team.name,
      ownerEmail: team.ownerEmail,
      inviteToken: team.inviteToken,
      inviteState: team.inviteState,
      isAdminTeam: team.id === room.adminTeamId,
      submitted: !!pick,
      pickCount: status.totalPlayers,
      picks: rosterPlayers(room, team.id),
      roster: rosterPlayers(room, team.id),
      rosterStatus: status,
      guidance: status.guidance,
      totalProjectedPoints: status.totalProjectedPoints,
      totalProjectedPts: status.totalProjectedPoints,
      ...(round?.status === "revealed"
        ? { pick: pick ? serializePick(room, round, pick) : null }
        : {}),
    };
  });
  const adminTeamBase = room.adminTeamId
    ? teamStates.find((team) => team.id === room.adminTeamId) ?? null
    : null;
  const adminOwnPick =
    round && room.adminTeamId
      ? round.picks.find((pick) => pick.teamId === room.adminTeamId)
      : undefined;
  const missingTeams = room.teams
    .filter(
      (team) => !round?.picks.some((pick) => pick.teamId === team.id),
    )
    .map((team) => ({ id: team.id, name: team.name }));
  const lastRound = currentRound(room);
  const canStartRound =
    room.status === "in_progress" &&
    room.currentRound < room.draftConfig.rounds &&
    (!lastRound || lastRound.status === "revealed");
  const canReveal =
    room.status === "in_progress" && lastRound?.status === "submitting";
  const canFinish =
    room.status === "in_progress" &&
    room.currentRound > 0 &&
    lastRound?.status === "revealed";
  const history = revealedHistory(room);
  const phase =
    room.status === "completed"
      ? "completed"
      : round?.status === "submitting"
        ? "picking"
        : round?.status === "revealed"
          ? "revealed"
          : "waiting";
  const adminTeamState = adminTeamBase
    ? {
        ...adminTeamBase,
        teamId: adminTeamBase.id,
        teamName: adminTeamBase.name,
        myPicks: adminTeamBase.picks,
        myPick:
          adminOwnPick && round
            ? serializePick(room, round, adminOwnPick)
            : null,
      }
    : null;

  return {
    ...roomMetadata(room),
    phase,
    adminTeamId: room.adminTeamId,
    adminTeam: adminTeamState,
    adminTeamState,
    availablePlayers,
    availableCount: availablePlayers.length,
    allPlayers,
    manualPlayerPool: allPlayers,
    manualAssignmentAvailabilityPolicy:
      MANUAL_ASSIGNMENT_AVAILABILITY_POLICY,
    manualAssignmentAvailabilityRule:
      MANUAL_ASSIGNMENT_AVAILABILITY_POLICY.explanation,
    teams: teamStates,
    teamSubmissionStatuses: teamStates.map(({ id, name, submitted }) => ({
      id,
      name,
      submitted,
    })),
    submittedCount: round?.picks.length ?? 0,
    allSubmitted:
      !!round && room.teams.length > 0 && missingTeams.length === 0,
    missingTeams,
    missingTeamNames: missingTeams.map((team) => team.name),
    revealedHistory: history,
    revealedRounds: history.map(({ number, results }) => ({
      round: number,
      results: results.map(({ teamId, teamName, player }) => ({
        teamId,
        teamName,
        player,
      })),
    })),
    resultsHistory: history,
    canStartRound,
    canReveal,
    canRevealWithoutConfirmation: canReveal && missingTeams.length === 0,
    canFinish,
    canFinishDraft: canFinish,
    actionFlags: {
      canStartRound,
      canReveal,
      canFinishDraft: canFinish,
    },
    isFinalRound:
      room.currentRound > 0 &&
      room.currentRound >= room.draftConfig.rounds,
  };
}

export async function createRoom(nameValue: unknown): Promise<DraftRoom> {
  const name = validateName(nameValue, "Draft name");
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const now = Date.now();
    const room: DraftRoom = {
      id: roomCode(),
      name,
      adminToken: secretToken(),
      status: "setup",
      currentRound: 0,
      rounds: [],
      teams: [],
      rosters: [],
      manualRosters: [],
      availablePlayerIds: PLAYERS.map((player) => player.id),
      draftConfig: {
        rounds: 1,
        rosterReqs: { ...DEFAULT_ROSTER_REQUIREMENTS },
      },
      scoringConfig: cloneScoringConfig(DEFAULT_SCORING_CONFIG),
      adminTeamId: null,
      createdAt: now,
      updatedAt: now,
    };
    if (await insertStoredRoom(room)) return room;
  }
  throw new DraftError(
    503,
    "room_id_generation_failed",
    "Could not allocate a unique room code. Please retry.",
  );
}

export async function getSetupState(
  roomId: string,
  adminToken: unknown,
  origin?: string,
) {
  const room = await requireStoredRoom(roomId);
  requireAdmin(room, adminToken);
  return buildSetupState(room, origin);
}

export async function updateRoomName(
  roomId: string,
  adminToken: unknown,
  nameValue: unknown,
): Promise<{ name: string }> {
  const name = validateName(nameValue, "Draft name");
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    room.name = name;
    return { name };
  });
}

export async function addTeam(
  roomId: string,
  adminToken: unknown,
  input: { name?: unknown; email?: unknown; isAdminTeam?: unknown },
): Promise<Team> {
  const name = validateName(input.name, "Team name");
  const ownerEmail = validateEmail(input.email);
  if (
    input.isAdminTeam !== undefined &&
    typeof input.isAdminTeam !== "boolean"
  ) {
    throw new DraftError(
      400,
      "invalid_admin_team_flag",
      "isAdminTeam must be true or false.",
    );
  }

  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    if (
      room.teams.some(
        (team) => team.name.toLowerCase() === name.toLowerCase(),
      )
    ) {
      throw new DraftError(
        409,
        "duplicate_team_name",
        `A team named '${name}' already exists in this room.`,
      );
    }
    const now = Date.now();
    const team: Team = {
      id: randomUUID(),
      name,
      ownerEmail,
      inviteToken: secretToken(),
      inviteState: "not_sent",
      inviteSentAt: null,
      joinedAt: null,
      createdAt: now,
    };
    room.teams.push(team);
    if (input.isAdminTeam === true) room.adminTeamId = team.id;
    return team;
  });
}

export async function updateTeam(
  roomId: string,
  adminToken: unknown,
  teamId: unknown,
  input: { name?: unknown; email?: unknown; isAdminTeam?: unknown },
): Promise<Team> {
  if (
    input.name === undefined &&
    input.email === undefined &&
    input.isAdminTeam === undefined
  ) {
    throw new DraftError(
      400,
      "empty_team_update",
      "Provide name, email, or isAdminTeam to update the team.",
    );
  }
  const name =
    input.name === undefined ? undefined : validateName(input.name, "Team name");
  const email =
    input.email === undefined ? undefined : validateEmail(input.email);
  if (
    input.isAdminTeam !== undefined &&
    typeof input.isAdminTeam !== "boolean"
  ) {
    throw new DraftError(
      400,
      "invalid_admin_team_flag",
      "isAdminTeam must be true or false.",
    );
  }

  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    const team = findTeam(room, teamId);
    if (
      name &&
      room.teams.some(
        (candidate) =>
          candidate.id !== team.id &&
          candidate.name.toLowerCase() === name.toLowerCase(),
      )
    ) {
      throw new DraftError(
        409,
        "duplicate_team_name",
        `A team named '${name}' already exists in this room.`,
      );
    }
    if (name) team.name = name;
    if (email !== undefined) {
      const emailChanged = team.ownerEmail !== email;
      team.ownerEmail = email;
      if (emailChanged && team.inviteState === "sent") {
        team.inviteState = "not_sent";
        team.inviteSentAt = null;
      }
    }
    if (input.isAdminTeam === true) room.adminTeamId = team.id;
    if (input.isAdminTeam === false && room.adminTeamId === team.id) {
      room.adminTeamId = null;
    }
    return { ...team };
  });
}

export async function removeTeam(
  roomId: string,
  adminToken: unknown,
  teamId: unknown,
): Promise<{ removedTeamId: string }> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    const team = findTeam(room, teamId);
    room.teams = room.teams.filter((candidate) => candidate.id !== team.id);
    room.rosters = room.rosters.filter((entry) => entry.teamId !== team.id);
    room.manualRosters = room.manualRosters.filter(
      (entry) => entry.teamId !== team.id,
    );
    rebuildPlayerAvailability(room);
    if (room.adminTeamId === team.id) room.adminTeamId = null;
    return { removedTeamId: team.id };
  });
}

export async function setAdminTeam(
  roomId: string,
  adminToken: unknown,
  teamId: unknown,
): Promise<{ adminTeamId: string }> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    const team = findTeam(room, teamId);
    room.adminTeamId = team.id;
    return { adminTeamId: team.id };
  });
}

export async function markInviteSent(
  roomId: string,
  adminToken: unknown,
  teamId: unknown,
): Promise<Team> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    const team = findTeam(room, teamId);
    if (room.status === "completed") {
      throw new DraftError(
        409,
        "draft_completed",
        "Invites cannot be changed after the draft is completed.",
      );
    }
    if (team.inviteState !== "joined") team.inviteState = "sent";
    team.inviteSentAt = Date.now();
    return { ...team };
  });
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    };
    return entities[character];
  });
}

export async function sendTeamInvite(
  roomId: string,
  adminToken: unknown,
  teamId: unknown,
  origin?: string,
) {
  const room = await requireStoredRoom(roomId);
  requireAdmin(room, adminToken);
  if (room.status === "completed") {
    throw new DraftError(
      409,
      "draft_completed",
      "Invites cannot be sent after the draft is completed.",
    );
  }
  const team = findTeam(room, teamId);
  const link = invitationLink(room.id, team.inviteToken, origin);
  const resendApiKey = process.env.RESEND_API_KEY?.trim();
  if (!resendApiKey) {
    return {
      inviteLink: link,
      emailConfigured: false,
      emailSent: false,
      inviteState: team.inviteState,
    };
  }
  if (!team.ownerEmail) {
    throw new DraftError(
      400,
      "team_email_required",
      "Add an owner email before sending this team's invite.",
      { teamId: team.id, teamName: team.name },
    );
  }

  let response: Response;
  try {
    response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${resendApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from:
          process.env.RESEND_FROM_EMAIL?.trim() ||
          "Scribner Draft <onboarding@resend.dev>",
        to: [team.ownerEmail],
        subject: `Join ${room.name}`,
        text: `You have been invited to manage ${team.name} in ${room.name}. Open your private team link: ${link}`,
        html: `<p>You have been invited to manage <strong>${escapeHtml(team.name)}</strong> in <strong>${escapeHtml(room.name)}</strong>.</p><p><a href="${escapeHtml(link)}">Open your private team link</a></p><p>Keep this link private because it grants access to your team.</p>`,
      }),
    });
  } catch (error) {
    console.error("Resend request failed:", error);
    throw new DraftError(
      502,
      "email_delivery_failed",
      "The invite email provider could not be reached. Copy the invite link and retry later.",
      { inviteLink: link, emailConfigured: true },
    );
  }

  const providerResponse = (await response.json().catch(() => ({}))) as Record<
    string,
    unknown
  >;
  if (!response.ok) {
    throw new DraftError(
      502,
      "email_delivery_failed",
      "Resend rejected the invite email. Verify RESEND_FROM_EMAIL and the recipient, then retry.",
      {
        inviteLink: link,
        emailConfigured: true,
        providerStatus: response.status,
        providerMessage:
          typeof providerResponse.message === "string"
            ? providerResponse.message
            : undefined,
      },
    );
  }

  const updatedTeam = await markInviteSent(
    room.id,
    adminToken,
    team.id,
  );
  return {
    inviteLink: link,
    emailConfigured: true,
    emailSent: true,
    inviteState: updatedTeam.inviteState,
    emailId:
      typeof providerResponse.id === "string" ? providerResponse.id : null,
  };
}

export async function joinByInvite(
  roomId: string,
  teamToken: unknown,
): Promise<{
  teamId: string;
  teamName: string;
  teamToken: string;
  inviteToken: string;
  draftName: string;
  roomStatus: RoomStatus;
}> {
  return mutateStoredRoom(roomId, (room) => {
    const team = requireTeamByToken(room, teamToken);
    if (team.inviteState !== "joined") {
      team.inviteState = "joined";
      team.joinedAt = Date.now();
    }
    return {
      teamId: team.id,
      teamName: team.name,
      teamToken: team.inviteToken,
      inviteToken: team.inviteToken,
      draftName: room.name,
      roomStatus: room.status,
    };
  });
}

export async function updateDraftConfig(
  roomId: string,
  adminToken: unknown,
  configValue: unknown,
): Promise<DraftConfig> {
  if (!isRecord(configValue)) {
    throw new DraftError(
      400,
      "invalid_draft_config",
      "config must be an object containing rounds and/or rosterReqs.",
    );
  }
  const allowedKeys = new Set(["rounds", "rosterReqs"]);
  for (const key of Object.keys(configValue)) {
    if (!allowedKeys.has(key)) {
      throw new DraftError(
        400,
        "invalid_draft_config",
        `Unknown draft config field '${key}'.`,
      );
    }
  }
  if (!("rounds" in configValue) && !("rosterReqs" in configValue)) {
    throw new DraftError(
      400,
      "empty_draft_config",
      "Provide rounds and/or rosterReqs to update.",
    );
  }

  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    if ("rounds" in configValue) {
      const rounds = configValue.rounds;
      if (
        typeof rounds !== "number" ||
        !Number.isInteger(rounds) ||
        rounds < 1 ||
        rounds > MAX_ROUNDS
      ) {
        throw new DraftError(
          400,
          "invalid_round_count",
          `rounds must be an integer from 1 to ${MAX_ROUNDS}.`,
        );
      }
      room.draftConfig.rounds = rounds;
    }
    if ("rosterReqs" in configValue) {
      room.draftConfig.rosterReqs = validateRosterRequirementsUpdate(
        configValue.rosterReqs,
        room.draftConfig.rosterReqs,
      );
    }
    return {
      rounds: room.draftConfig.rounds,
      rosterReqs: { ...room.draftConfig.rosterReqs },
    };
  });
}

export async function updateScoringConfig(
  roomId: string,
  adminToken: unknown,
  configValue: unknown,
): Promise<ScoringConfig> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    room.scoringConfig = validateScoringConfigUpdate(
      configValue,
      room.scoringConfig,
    );
    return cloneScoringConfig(room.scoringConfig);
  });
}

export async function startDraft(
  roomId: string,
  adminToken: unknown,
): Promise<{ roomStatus: RoomStatus }> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    requireSetup(room);
    const issues = startDraftIssues(room);
    if (issues.length) {
      throw new DraftError(
        409,
        "draft_setup_incomplete",
        "Complete draft setup before starting.",
        { issues },
      );
    }
    room.status = "in_progress";
    return { roomStatus: room.status };
  });
}

export async function getGmState(
  roomId: string,
  teamToken: unknown,
) {
  const room = await requireStoredRoom(roomId);
  const team = requireTeamByToken(room, teamToken);
  if (team.inviteState === "joined") return buildGmState(room, team);

  return mutateStoredRoom(room.id, (lockedRoom) => {
    const lockedTeam = requireTeamByToken(lockedRoom, teamToken);
    lockedTeam.inviteState = "joined";
    lockedTeam.joinedAt = Date.now();
    return buildGmState(lockedRoom, lockedTeam);
  });
}

function submitPickForTeam(
  room: DraftRoom,
  team: Team,
  playerIdValue: unknown,
) {
  if (room.status !== "in_progress") {
    throw new DraftError(
      409,
      "draft_not_in_progress",
      room.status === "setup"
        ? "The commissioner must start the draft before picks can be submitted."
        : "The draft is completed and no longer accepts picks.",
    );
  }
  const round = currentRound(room);
  if (!round || round.status !== "submitting") {
    throw new DraftError(
      409,
      "round_not_open",
      "No round is currently open for sealed picks.",
    );
  }
  if (round.picks.some((pick) => pick.teamId === team.id)) {
    throw new DraftError(
      409,
      "pick_already_submitted",
      `Team '${team.name}' already submitted its sealed pick for Round ${round.number}.`,
    );
  }
  const playerId = asTrimmedString(playerIdValue);
  if (!playerId) {
    throw new DraftError(400, "player_id_required", "playerId is required.");
  }
  const player = PLAYER_BY_ID.get(playerId);
  if (!player) {
    throw new DraftError(
      404,
      "player_not_found",
      `Player '${playerId}' is not in the static player source.`,
    );
  }
  if (!room.availablePlayerIds.includes(player.id)) {
    throw new DraftError(
      409,
      "player_unavailable",
      `${player.name} was selected in a revealed earlier round and is no longer available.`,
    );
  }

  const pick: SealedPick = {
    teamId: team.id,
    playerId: player.id,
    submittedAt: Date.now(),
    revealedAt: null,
  };
  round.picks.push(pick);
  if (team.inviteState !== "joined") {
    team.inviteState = "joined";
    team.joinedAt = Date.now();
  }
  return serializePick(room, round, pick);
}

export async function submitPick(
  roomId: string,
  teamToken: unknown,
  playerId: unknown,
) {
  return mutateStoredRoom(roomId, (room) => {
    const team = requireTeamByToken(room, teamToken);
    return submitPickForTeam(room, team, playerId);
  });
}

export async function getAdminState(
  roomId: string,
  adminToken: unknown,
) {
  const room = await requireStoredRoom(roomId);
  requireAdmin(room, adminToken);
  return buildAdminState(room);
}

export async function manualAssignPlayer(
  roomId: string,
  adminToken: unknown,
  teamIdValue: unknown,
  playerIdValue: unknown,
) {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    const team = findTeam(room, teamIdValue);
    const player = findPlayer(playerIdValue);
    if (findCurrentRosterAssignment(room, team.id, player.id)) {
      throw new DraftError(
        409,
        "duplicate_team_player",
        `${team.name} already rosters ${player.name}; a team cannot contain duplicate instances of the same player.`,
        { teamId: team.id, playerId: player.id },
      );
    }

    const ownerTeamIdsBefore = playerOwnerTeamIds(room, player.id);
    const entry: ManualRosterEntry = {
      id: randomUUID(),
      teamId: team.id,
      playerId: player.id,
      createdAt: Date.now(),
    };
    room.manualRosters.push(entry);
    rebuildPlayerAvailability(room);

    return {
      assigned: true,
      teamId: team.id,
      playerId: player.id,
      assignment: rosterPlayers(room, team.id).find(
        (candidate) => candidate.assignmentId === entry.id,
      ),
      playerWasUnavailable: ownerTeamIdsBefore.length > 0,
      sharedOwnershipCreated: ownerTeamIdsBefore.some(
        (ownerTeamId) => ownerTeamId !== team.id,
      ),
      availabilityPolicy: MANUAL_ASSIGNMENT_AVAILABILITY_POLICY,
      state: buildAdminState(room),
    };
  });
}

export async function manualReplacePlayer(
  roomId: string,
  adminToken: unknown,
  teamIdValue: unknown,
  oldPlayerIdValue: unknown,
  newPlayerIdValue: unknown,
) {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    const team = findTeam(room, teamIdValue);
    const oldPlayer = findPlayer(oldPlayerIdValue, "oldPlayerId");
    const newPlayer = findPlayer(newPlayerIdValue, "newPlayerId");
    if (oldPlayer.id === newPlayer.id) {
      throw new DraftError(
        409,
        "replacement_player_unchanged",
        "newPlayerId must differ from oldPlayerId.",
        { teamId: team.id, playerId: oldPlayer.id },
      );
    }

    const oldAssignment = findCurrentRosterAssignment(
      room,
      team.id,
      oldPlayer.id,
    );
    if (!oldAssignment) {
      throw new DraftError(
        404,
        "roster_player_not_found",
        `${oldPlayer.name} is not on ${team.name}'s current roster.`,
        { teamId: team.id, playerId: oldPlayer.id },
      );
    }
    if (findCurrentRosterAssignment(room, team.id, newPlayer.id)) {
      throw new DraftError(
        409,
        "duplicate_team_player",
        `${team.name} already rosters ${newPlayer.name}; a team cannot contain duplicate instances of the same player.`,
        { teamId: team.id, playerId: newPlayer.id },
      );
    }

    const ownerTeamIdsBefore = playerOwnerTeamIds(room, newPlayer.id);
    let replacementEntry: ManualRosterEntry;
    if (oldAssignment.assignmentType === "manual") {
      oldAssignment.entry.playerId = newPlayer.id;
      replacementEntry = oldAssignment.entry;
    } else {
      const oldEntry = oldAssignment.entry;
      room.rosters = room.rosters.filter(
        (entry) =>
          !(
            entry.teamId === oldEntry.teamId &&
            entry.roundNumber === oldEntry.roundNumber
          ),
      );
      replacementEntry = {
        id: randomUUID(),
        teamId: team.id,
        playerId: newPlayer.id,
        createdAt: Date.now(),
      };
      room.manualRosters.push(replacementEntry);
    }
    rebuildPlayerAvailability(room);

    return {
      replaced: true,
      teamId: team.id,
      oldPlayerId: oldPlayer.id,
      newPlayerId: newPlayer.id,
      replacedAssignmentType: oldAssignment.assignmentType,
      historicalPickPreserved: oldAssignment.assignmentType === "draft",
      assignment: rosterPlayers(room, team.id).find(
        (candidate) => candidate.assignmentId === replacementEntry.id,
      ),
      playerWasUnavailable: ownerTeamIdsBefore.length > 0,
      sharedOwnershipCreated: ownerTeamIdsBefore.some(
        (ownerTeamId) => ownerTeamId !== team.id,
      ),
      availabilityPolicy: MANUAL_ASSIGNMENT_AVAILABILITY_POLICY,
      state: buildAdminState(room),
    };
  });
}

export async function manualRemovePlayer(
  roomId: string,
  adminToken: unknown,
  teamIdValue: unknown,
  playerIdValue: unknown,
) {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    const team = findTeam(room, teamIdValue);
    const player = findPlayer(playerIdValue);
    const assignment = findCurrentRosterAssignment(room, team.id, player.id);
    if (!assignment) {
      throw new DraftError(
        404,
        "roster_player_not_found",
        `${player.name} is not on ${team.name}'s current roster.`,
        { teamId: team.id, playerId: player.id },
      );
    }

    if (assignment.assignmentType === "manual") {
      room.manualRosters = room.manualRosters.filter(
        (entry) => entry.id !== assignment.entry.id,
      );
    } else {
      room.rosters = room.rosters.filter(
        (entry) =>
          !(
            entry.teamId === assignment.entry.teamId &&
            entry.roundNumber === assignment.entry.roundNumber
          ),
      );
    }
    rebuildPlayerAvailability(room);

    return {
      removed: true,
      teamId: team.id,
      playerId: player.id,
      removedAssignmentType: assignment.assignmentType,
      historicalPickPreserved: assignment.assignmentType === "draft",
      playerAvailable: room.availablePlayerIds.includes(player.id),
      remainingOwnerTeamIds: playerOwnerTeamIds(room, player.id),
      availabilityPolicy: MANUAL_ASSIGNMENT_AVAILABILITY_POLICY,
      state: buildAdminState(room),
    };
  });
}

export async function updateLiveSetup(
  roomId: string,
  adminToken: unknown,
  input: {
    draftName: unknown;
    rounds: unknown;
    rosterReqs: unknown;
    scoringConfig: unknown;
  },
) {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    if (room.status === "completed") {
      throw new DraftError(
        409,
        "draft_completed",
        "Live setup cannot be changed after the draft is completed.",
      );
    }
    if (room.status !== "in_progress") {
      throw new DraftError(
        409,
        "draft_not_in_progress",
        "Live setup can only be changed while the draft is in progress.",
      );
    }

    const draftName = validateName(input.draftName, "Draft name");
    if (
      typeof input.rounds !== "number" ||
      !Number.isInteger(input.rounds) ||
      input.rounds < 1 ||
      input.rounds > MAX_ROUNDS
    ) {
      throw new DraftError(
        400,
        "invalid_round_count",
        `rounds must be an integer from 1 to ${MAX_ROUNDS}.`,
      );
    }
    const rounds = input.rounds;
    if (rounds < room.currentRound) {
      throw new DraftError(
        409,
        "round_count_below_current_round",
        `rounds cannot be less than the current round (${room.currentRound}).`,
        { currentRound: room.currentRound, minimumRounds: room.currentRound },
      );
    }

    const rosterReqs = validateCompleteRosterRequirements(input.rosterReqs);
    const rosterTarget = Object.values(rosterReqs).reduce(
      (total, requirement) => total + requirement,
      0,
    );
    if (rounds < rosterTarget) {
      throw new DraftError(
        409,
        "rounds_below_roster_target",
        `rounds cannot be below the roster target (${rosterTarget}).`,
        { rosterTarget, minimumRounds: rosterTarget },
      );
    }
    const scoringConfig = validateCompleteScoringConfig(input.scoringConfig);

    room.name = draftName;
    room.draftConfig = { rounds, rosterReqs };
    room.scoringConfig = scoringConfig;
    return buildAdminState(room);
  });
}

function requireConfirmationName(
  room: DraftRoom,
  confirmationName: unknown,
): void {
  if (typeof confirmationName !== "string") {
    throw new DraftError(
      400,
      "confirmation_name_required",
      "confirmationName is required and must exactly match the current draft name.",
    );
  }
  if (confirmationName !== room.name) {
    throw new DraftError(
      409,
      "confirmation_name_mismatch",
      "confirmationName must exactly match the current draft name.",
    );
  }
}

export async function deleteDraft(
  roomIdValue: string,
  adminToken: unknown,
  confirmationName: unknown,
): Promise<{ deleted: true; roomId: string }> {
  const roomId = normalizeRoomId(roomIdValue);
  return runStorageOperation(async () => {
    if (usesPostgres()) {
      await ensureSchema();
      const transactionResult = await getSql().begin(async (transaction) => {
        const room = await loadSqlRoom(transaction, roomId, true);
        if (!room) {
          throw new DraftError(404, "room_not_found", "Draft room not found.");
        }
        requireAdmin(room, adminToken);
        requireConfirmationName(room, confirmationName);
        await transaction`DELETE FROM scribner_rooms WHERE id = ${room.id}`;
        return { deleted: true as const, roomId: room.id };
      });
      return transactionResult as { deleted: true; roomId: string };
    }

    assertLocalStorageAllowed();
    return withJsonLock(() => {
      const rooms = loadJsonRooms();
      const room = rooms.get(roomId);
      if (!room) {
        throw new DraftError(404, "room_not_found", "Draft room not found.");
      }
      requireAdmin(room, adminToken);
      requireConfirmationName(room, confirmationName);
      rooms.delete(room.id);
      saveJsonRooms(rooms);
      return { deleted: true as const, roomId: room.id };
    });
  });
}

export async function submitAdminPick(
  roomId: string,
  adminToken: unknown,
  playerId: unknown,
) {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    if (!room.adminTeamId) {
      throw new DraftError(
        409,
        "admin_team_not_set",
        "Select the admin team before submitting an admin pick.",
      );
    }
    const team = findTeam(room, room.adminTeamId);
    return submitPickForTeam(room, team, playerId);
  });
}

export async function startRound(
  roomId: string,
  adminToken: unknown,
): Promise<{ round: number; roundStatus: RoundStatus }> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    if (room.status === "setup") {
      throw new DraftError(
        409,
        "draft_not_started",
        "Use start-draft after completing setup before starting Round 1.",
      );
    }
    if (room.status === "completed") {
      throw new DraftError(
        409,
        "draft_completed",
        "The completed draft cannot start another round.",
      );
    }
    if (!room.teams.length) {
      throw new DraftError(
        409,
        "no_teams",
        "Add at least one team before starting a round.",
      );
    }
    if (!room.adminTeamId) {
      throw new DraftError(
        409,
        "admin_team_not_set",
        "Select the admin team before starting the draft.",
      );
    }
    const previousRound = currentRound(room);
    if (previousRound?.status === "submitting") {
      throw new DraftError(
        409,
        "round_already_open",
        `Round ${previousRound.number} must be revealed before another round starts.`,
      );
    }
    if (room.currentRound >= room.draftConfig.rounds) {
      throw new DraftError(
        409,
        "round_limit_reached",
        `The configured ${room.draftConfig.rounds}-round limit has been reached. Finish the draft instead.`,
      );
    }

    const nextRoundNumber = room.currentRound + 1;
    const round: Round = {
      number: nextRoundNumber,
      status: "submitting",
      picks: [],
      startedAt: Date.now(),
      revealedAt: null,
    };
    room.currentRound = nextRoundNumber;
    room.rounds.push(round);
    return { round: round.number, roundStatus: round.status };
  });
}

export async function revealRound(
  roomId: string,
  adminToken: unknown,
  confirmMissing: unknown,
) {
  if (confirmMissing !== undefined && typeof confirmMissing !== "boolean") {
    throw new DraftError(
      400,
      "invalid_confirm_missing",
      "confirmMissing must be true or false.",
    );
  }
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    if (room.status !== "in_progress") {
      throw new DraftError(
        409,
        "draft_not_in_progress",
        "Only an in-progress draft can reveal a round.",
      );
    }
    const round = currentRound(room);
    if (!round || round.status !== "submitting") {
      throw new DraftError(
        409,
        "round_not_open",
        "There is no open round to reveal.",
      );
    }
    const missingTeams = room.teams
      .filter(
        (team) => !round.picks.some((pick) => pick.teamId === team.id),
      )
      .map((team) => ({ id: team.id, name: team.name }));
    if (missingTeams.length && confirmMissing !== true) {
      throw new DraftError(
        409,
        "missing_team_picks",
        `Cannot reveal Round ${round.number} without confirmation because ${missingTeams.length} team${missingTeams.length === 1 ? " has" : "s have"} not submitted.`,
        {
          missingTeams,
          missingTeamNames: missingTeams.map((team) => team.name),
          confirmMissingRequired: true,
        },
      );
    }

    const revealedAt = Date.now();
    round.status = "revealed";
    round.revealedAt = revealedAt;
    for (const pick of round.picks) {
      pick.revealedAt = revealedAt;
      const existingPlayerAssignment = findCurrentRosterAssignment(
        room,
        pick.teamId,
        pick.playerId,
      );
      if (existingPlayerAssignment?.assignmentType === "manual") {
        room.manualRosters = room.manualRosters.filter(
          (entry) => entry.id !== existingPlayerAssignment.entry.id,
        );
      }
      if (
        !existingPlayerAssignment ||
        existingPlayerAssignment.assignmentType === "manual"
      ) {
        room.rosters.push({
          teamId: pick.teamId,
          playerId: pick.playerId,
          roundNumber: round.number,
          addedAt: revealedAt,
        });
      }
    }

    rebuildPlayerAvailability(room);

    return {
      round: round.number,
      roundStatus: round.status,
      missingTeams,
      results: revealedHistory(room).find(
        (historyRound) => historyRound.number === round.number,
      ),
      canFinish: true,
      isFinalRound: round.number >= room.draftConfig.rounds,
    };
  });
}

export async function finishDraft(
  roomId: string,
  adminToken: unknown,
): Promise<{ roomStatus: RoomStatus; completedRound: number }> {
  return mutateStoredRoom(roomId, (room) => {
    requireAdmin(room, adminToken);
    if (room.status === "completed") {
      return { roomStatus: room.status, completedRound: room.currentRound };
    }
    if (room.status !== "in_progress") {
      throw new DraftError(
        409,
        "draft_not_in_progress",
        "Start the draft before finishing it.",
      );
    }
    const round = currentRound(room);
    if (!round || round.status !== "revealed") {
      throw new DraftError(
        409,
        "round_must_be_revealed",
        "Reveal the current round before finishing the draft.",
      );
    }
    room.status = "completed";
    return { roomStatus: room.status, completedRound: room.currentRound };
  });
}
