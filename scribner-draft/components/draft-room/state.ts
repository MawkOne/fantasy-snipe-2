import type {
  DraftPlayer,
  DraftRoomState,
  RevealedResult,
  RevealedRound,
  RoomPhase,
  RoomRole,
  RoomTeam,
  RoomViewer,
  RosterRequirements,
  RosterSlotKey,
  RosterStatus,
  ScoringConfig,
} from "./types";

type UnknownRecord = Record<string, unknown>;

const ROSTER_KEYS: RosterSlotKey[] = ["F", "C", "W", "D", "G"];
const EMPTY_REQUIREMENTS: RosterRequirements = { F: 0, C: 0, W: 0, D: 0, G: 0 };
const SCORING_KEYS = {
  skater: ["g", "a", "pm", "pim", "shg", "shog"],
  dBonus: ["g", "a"],
  goalie: ["w", "ga", "sv", "ol", "shol", "so"],
} as const;
const DEFAULT_SCORING_CONFIG: ScoringConfig = {
  skater: {
    g: { enabled: true, value: 3 },
    a: { enabled: true, value: 2 },
    pm: { enabled: true, value: 0.25 },
    pim: { enabled: true, value: 0 },
    shg: { enabled: true, value: 2 },
    shog: { enabled: true, value: 1 },
  },
  dBonus: {
    g: { enabled: true, value: 2 },
    a: { enabled: true, value: 1 },
  },
  goalie: {
    w: { enabled: true, value: 2 },
    ga: { enabled: true, value: -1.25 },
    sv: { enabled: true, value: 0.2 },
    ol: { enabled: true, value: 1 },
    shol: { enabled: true, value: 1 },
    so: { enabled: true, value: 1 },
  },
};

function asRecord(value: unknown): UnknownRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as UnknownRecord)
    : {};
}

function valueFrom(sources: UnknownRecord[], keys: string[]): unknown {
  for (const source of sources) {
    for (const key of keys) {
      if (source[key] !== undefined && source[key] !== null) return source[key];
    }
  }
  return undefined;
}

function stringFrom(sources: UnknownRecord[], keys: string[], fallback = ""): string {
  const value = valueFrom(sources, keys);
  if (typeof value === "string") return value.trim();
  if (typeof value === "number") return String(value);
  return fallback;
}

function numberFrom(
  sources: UnknownRecord[],
  keys: string[],
  fallback = 0,
): number {
  const value = valueFrom(sources, keys);
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function optionalNumberFrom(sources: UnknownRecord[], keys: string[]): number | null {
  const value = valueFrom(sources, keys);
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

function optionalBooleanFrom(
  sources: UnknownRecord[],
  keys: string[],
): boolean | undefined {
  const value = valueFrom(sources, keys);
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (["true", "yes", "submitted", "ready", "1"].includes(normalized)) return true;
    if (["false", "no", "waiting", "pending", "0"].includes(normalized)) return false;
  }
  return undefined;
}

function arrayFrom(sources: UnknownRecord[], keys: string[]): unknown[] {
  const value = valueFrom(sources, keys);
  return Array.isArray(value) ? value : [];
}

function roundOneDecimal(value: number): number {
  return Math.round(value * 10) / 10;
}

function slug(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "") || "player";
}

function playerLookup(players: DraftPlayer[]): Map<string, DraftPlayer> {
  const lookup = new Map<string, DraftPlayer>();
  for (const player of players) {
    lookup.set(player.id.toLowerCase(), player);
    lookup.set(player.name.toLowerCase(), player);
  }
  return lookup;
}

function statFrom(sources: UnknownRecord[], keys: string[]): number | undefined {
  const value = optionalNumberFrom(sources, keys);
  return value === null ? undefined : value;
}

export function normalizePlayer(
  value: unknown,
  lookup?: Map<string, DraftPlayer>,
): DraftPlayer | null {
  if (value === null || value === undefined) return null;

  if (typeof value === "string") {
    const known = lookup?.get(value.toLowerCase());
    if (known) return known;
    return {
      id: slug(value),
      name: value,
      position: "—",
      team: "—",
      projectedPts: 0,
      stats: {},
    };
  }

  const wrapper = asRecord(value);
  const status = stringFrom([wrapper], ["status", "pickStatus"]).toLowerCase();
  if (
    optionalBooleanFrom([wrapper], ["noPick", "missing"]) === true ||
    ["no-pick", "no_pick", "missing", "skipped"].includes(status)
  ) {
    return null;
  }

  const nestedPlayer = asRecord(wrapper.player);
  const source = Object.keys(nestedPlayer).length
    ? { ...wrapper, ...nestedPlayer }
    : wrapper;

  const id = stringFrom([source], ["id", "playerId", "player_id"]);
  const name = stringFrom([source], ["name", "playerName", "fullName", "player_name"]);
  const known = lookup?.get(id.toLowerCase()) ?? lookup?.get(name.toLowerCase());

  if (!id && !name && !known) return null;

  const projectedStats = asRecord(
    valueFrom([source], ["projectedStats", "projections", "stats", "projected"]),
  );
  const assignment = asRecord(wrapper.assignment);
  const statSources = [projectedStats, source];
  const projectedPts = optionalNumberFrom(
    [source],
    ["projectedPts", "projectedPoints", "fantasyPoints", "points", "pts"],
  );
  const rosteredByTeamIds = arrayFrom(
    [source],
    ["rosteredByTeamIds", "rosteredTeamIds", "ownerTeamIds"],
  )
    .filter((teamId): teamId is string => typeof teamId === "string" && teamId.length > 0);
  const explicitlyManual = optionalBooleanFrom(
    [source, wrapper],
    ["isManual", "manuallyAssigned"],
  );

  return {
    id: id || known?.id || slug(name),
    name: name || known?.name || "Unknown player",
    position:
      stringFrom([source], ["position", "pos", "playerPosition"]) ||
      known?.position ||
      "—",
    team:
      stringFrom(
        [source],
        ["team", "nhlTeam", "teamAbbr", "proTeam", "playerTeam"],
      ) ||
      known?.team ||
      "—",
    headshot:
      stringFrom(
        [source],
        ["headshot", "headshotUrl", "imageUrl", "photoUrl", "image"],
      ) || known?.headshot,
    adp: optionalNumberFrom([source, known as unknown as UnknownRecord], ["adp", "avgDraftPosition"]) ?? (known as DraftPlayer | undefined)?.adp,
    rank: optionalNumberFrom([source, known as unknown as UnknownRecord], ["rank", "draftRank", "ranking"]) ?? (known as DraftPlayer | undefined)?.rank,
    writeup: stringFrom([source, known as unknown as UnknownRecord], ["writeup", "writeupSummary", "writeup_summary"]) || (known as DraftPlayer | undefined)?.writeup,
    projectedPts: roundOneDecimal(projectedPts ?? known?.projectedPts ?? 0),
    stats: {
      goals: statFrom(statSources, ["goals", "g"]),
      assists: statFrom(statSources, ["assists", "a"]),
      plusMinus: statFrom(statSources, ["plusMinus", "plus_minus", "pm"]),
      penaltyMinutes: statFrom(statSources, ["penaltyMinutes", "pim"]),
      shortHandedGoals: statFrom(statSources, ["shortHandedGoals", "shg"]),
      shootoutGoals: statFrom(statSources, ["shootoutGoals", "shog"]),
      wins: statFrom(statSources, ["wins", "w"]),
      goalsAgainst: statFrom(statSources, ["goalsAgainst", "ga"]),
      saves: statFrom(statSources, ["saves", "sv"]),
      overtimeLosses: statFrom(statSources, ["overtimeLosses", "otl", "ol"]),
      shootoutLosses: statFrom(statSources, ["shootoutLosses", "shol"]),
      shutouts: statFrom(statSources, ["shutouts", "so"]),
    },
    assignmentSource:
      stringFrom(
        [source, wrapper, assignment],
        [
          "assignmentSource",
          "assignment_source",
          "rosterSource",
          "pickSource",
          "selectionSource",
          "source",
          "method",
        ],
      ) ||
      (explicitlyManual ? "manual" : "") ||
      known?.assignmentSource ||
      undefined,
    available:
      optionalBooleanFrom([source], ["available", "isAvailable"]) ??
      known?.available,
    rosteredByTeamIds:
      rosteredByTeamIds.length > 0
        ? rosteredByTeamIds
        : known?.rosteredByTeamIds,
  };
}

function normalizePlayerList(values: unknown[], lookup?: Map<string, DraftPlayer>): DraftPlayer[] {
  return values
    .map((value) => normalizePlayer(value, lookup))
    .filter((player): player is DraftPlayer => player !== null);
}

function mergePlayers(...groups: DraftPlayer[][]): DraftPlayer[] {
  const merged = new Map<string, DraftPlayer>();
  for (const group of groups) {
    for (const player of group) {
      const key = (player.id || `${player.name}-${player.team}`).toLowerCase();
      const existing = merged.get(key);
      merged.set(
        key,
        existing
          ? {
              ...existing,
              ...player,
              assignmentSource: player.assignmentSource ?? existing.assignmentSource,
              available: player.available ?? existing.available,
              rosteredByTeamIds:
                player.rosteredByTeamIds ?? existing.rosteredByTeamIds,
            }
          : player,
      );
    }
  }
  return Array.from(merged.values());
}

export function normalizeRosterRequirements(value: unknown): RosterRequirements {
  const source = asRecord(value);
  const result = { ...EMPTY_REQUIREMENTS };
  for (const key of ROSTER_KEYS) {
    result[key] = Math.max(
      0,
      Math.floor(numberFrom([source], [key, key.toLowerCase()], 0)),
    );
  }
  return result;
}

export function normalizeScoringConfig(value: unknown): ScoringConfig {
  const source = asRecord(value);
  const result: ScoringConfig = { skater: {}, dBonus: {}, goalie: {} };

  for (const group of Object.keys(SCORING_KEYS) as Array<keyof typeof SCORING_KEYS>) {
    const aliases =
      group === "dBonus"
        ? ["dBonus", "defenceBonus", "defenseBonus", "defence", "defense"]
        : [group];
    const groupSource = aliases.reduce<UnknownRecord>((found, alias) => {
      if (Object.keys(found).length > 0) return found;
      return asRecord(source[alias]);
    }, {});

    for (const key of SCORING_KEYS[group]) {
      const fallback = DEFAULT_SCORING_CONFIG[group][key];
      const rawMetric = groupSource[key];
      if (typeof rawMetric === "number" && Number.isFinite(rawMetric)) {
        result[group][key] = { enabled: true, value: rawMetric };
        continue;
      }
      if (typeof rawMetric === "string" && rawMetric.trim() !== "") {
        const parsed = Number(rawMetric);
        if (Number.isFinite(parsed)) {
          result[group][key] = { enabled: true, value: parsed };
          continue;
        }
      }

      const metric = asRecord(rawMetric);
      result[group][key] = {
        enabled:
          optionalBooleanFrom([metric], ["enabled", "active", "included"]) ??
          fallback.enabled,
        value:
          optionalNumberFrom([metric], ["value", "points", "weight"]) ??
          fallback.value,
      };
    }
  }

  return result;
}

export function buildRosterStatus(
  players: DraftPlayer[],
  requirements: RosterRequirements,
): RosterStatus {
  let centres = 0;
  let wingers = 0;
  let defence = 0;
  let goalies = 0;

  for (const player of players) {
    const position = player.position.toUpperCase();
    if (position === "C") centres += 1;
    else if (position === "LW" || position === "RW" || position === "W") wingers += 1;
    else if (position === "D") defence += 1;
    else if (position === "G") goalies += 1;
  }

  const reservedCentres = Math.min(centres, requirements.C);
  const reservedWingers = Math.min(wingers, requirements.W);
  const flexForwards = Math.max(0, centres + wingers - reservedCentres - reservedWingers);
  const current: Record<RosterSlotKey, number> = {
    C: centres,
    W: wingers,
    F: flexForwards,
    D: defence,
    G: goalies,
  };

  return ROSTER_KEYS.reduce((status, key) => {
    const required = requirements[key];
    const count = current[key];
    status[key] = {
      key,
      current: count,
      required,
      state: count < required ? "unmet" : count === required ? "met" : "exceeded",
    };
    return status;
  }, {} as RosterStatus);
}

const SLOT_LABELS: Record<RosterSlotKey, [string, string]> = {
  C: ["centre", "centres"],
  W: ["winger", "wingers"],
  F: ["flex forward", "flex forwards"],
  D: ["defenceman", "defencemen"],
  G: ["goalie", "goalies"],
};

export function rosterGuidance(status: RosterStatus): string[] {
  const priority: RosterSlotKey[] = ["F", "C", "W", "D", "G"];
  const guidance: string[] = [];

  for (const key of priority) {
    const slot = status[key];
    const remaining = Math.max(0, slot.required - slot.current);
    if (remaining > 0) {
      guidance.push(
        `Need ${remaining} more ${remaining === 1 ? SLOT_LABELS[key][0] : SLOT_LABELS[key][1]}`,
      );
    }
  }

  return guidance.length > 0 ? guidance : ["Roster targets complete"];
}

export function selectionRosterImpact(
  roster: DraftPlayer[],
  requirements: RosterRequirements,
  player: DraftPlayer,
): string {
  const before = buildRosterStatus(roster, requirements);
  const after = buildRosterStatus([...roster, player], requirements);
  const changed = ROSTER_KEYS.filter((key) => after[key].current > before[key].current);
  const useful = changed.find((key) => before[key].current < before[key].required);

  if (!useful) return "Adds roster depth beyond your current positional targets.";

  const slot = after[useful];
  if (slot.current >= slot.required) {
    const label = useful === "F" ? "flex-forward" : SLOT_LABELS[useful][0];
    return `Completes your ${label} target at ${slot.current}/${slot.required}.`;
  }

  const remaining = slot.required - slot.current;
  return `${SLOT_LABELS[useful][0][0].toUpperCase()}${SLOT_LABELS[useful][0].slice(1)} moves to ${slot.current}/${slot.required}; ${remaining} still needed.`;
}

export function formatProjectedPoints(value: number): string {
  return roundOneDecimal(value).toFixed(1);
}

export function playerStatLine(player: DraftPlayer, _long = false): string {
  // Return the writeup summary when available, fall back to a brief stat line
  if (player.writeup) {
    return player.writeup;
  }
  const stats = player.stats;
  const values: string[] = [];

  if (player.position.toUpperCase() === "G") {
    if (stats.wins !== undefined) values.push(`${stats.wins} W`);
    if (stats.saves !== undefined) values.push(`${stats.saves} SV`);
    if (stats.shutouts !== undefined) values.push(`${stats.shutouts} SO`);
    if (_long && stats.goalsAgainst !== undefined) values.push(`${stats.goalsAgainst} GA`);
  } else {
    if (stats.goals !== undefined) values.push(`${stats.goals} G`);
    if (stats.assists !== undefined) values.push(`${stats.assists} A`);
    if (stats.plusMinus !== undefined) {
      values.push(`${stats.plusMinus > 0 ? "+" : ""}${stats.plusMinus} +/-`);
    }
    if (_long && stats.shortHandedGoals !== undefined) {
      values.push(`${stats.shortHandedGoals} SHG`);
    }
  }

  return values.length > 0 ? values.join(" · ") : "ADP: #" + (player.adp ?? "—");
}

function stringList(value: unknown): string[] {
  if (typeof value === "string" && value.trim()) return [value.trim()];
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item.trim();
      const record = asRecord(item);
      return stringFrom([record], ["message", "text", "guidance", "label"]);
    })
    .filter(Boolean);
}

function normalizeResultRow(
  value: unknown,
  lookup: Map<string, DraftPlayer>,
): RevealedResult | null {
  const row = asRecord(value);
  const team = asRecord(row.team);
  const teamId = stringFrom([row, team], ["teamId", "id", "team_id"]);
  const teamName = stringFrom([row, team], ["teamName", "name", "team_name"]);
  if (!teamId && !teamName) return null;

  const status = stringFrom([row], ["status", "pickStatus"]).toLowerCase();
  const explicitNoPick =
    optionalBooleanFrom([row], ["noPick", "missing"]) === true ||
    ["no-pick", "no_pick", "missing", "skipped"].includes(status);

  let playerValue: unknown;
  if (Object.prototype.hasOwnProperty.call(row, "player")) playerValue = row.player;
  else if (Object.prototype.hasOwnProperty.call(row, "pick")) playerValue = row.pick;
  else if (Object.prototype.hasOwnProperty.call(row, "selection")) playerValue = row.selection;
  else if (
    row.playerId !== undefined ||
    row.playerName !== undefined ||
    row.player_id !== undefined
  ) {
    playerValue = {
      id: row.playerId ?? row.player_id,
      name: row.playerName ?? row.player_name,
      position: row.playerPosition ?? row.position,
      team: row.playerTeam ?? row.nhlTeam,
      headshot: row.playerHeadshot ?? row.headshotUrl,
      projectedPts: row.projectedPts ?? row.projectedPoints,
      projectedStats: row.projectedStats,
    };
  }

  return {
    teamId: teamId || slug(teamName),
    teamName: teamName || "Team",
    player: explicitNoPick ? null : normalizePlayer(playerValue, lookup),
  };
}

function historySource(root: UnknownRecord, metadata: UnknownRecord): unknown[] {
  const keys = [
    "revealedResults",
    "revealedRounds",
    "resultsHistory",
    "revealedHistory",
    "history",
    "rounds",
  ];
  const value = valueFrom([root, metadata], keys);
  if (Array.isArray(value)) return value;

  const mapped = asRecord(value);
  return Object.entries(mapped).map(([round, results]) => ({ round, results }));
}

function normalizeHistory(
  root: UnknownRecord,
  metadata: UnknownRecord,
  teams: RoomTeam[],
  lookup: Map<string, DraftPlayer>,
): RevealedRound[] {
  const source = historySource(root, metadata);
  if (source.length === 0) return [];

  const grouped = new Map<number, unknown[]>();
  const looksFlat = source.every((item) => {
    const record = asRecord(item);
    return (
      valueFrom([record], ["round", "roundNumber", "number"]) !== undefined &&
      !["results", "picks", "selections", "teamResults", "teams"].some((key) =>
        Array.isArray(record[key]),
      )
    );
  });

  if (looksFlat) {
    for (const item of source) {
      const record = asRecord(item);
      const round = Math.max(1, Math.floor(numberFrom([record], ["round", "roundNumber", "number"], 1)));
      grouped.set(round, [...(grouped.get(round) ?? []), item]);
    }
  } else {
    for (const item of source) {
      const roundRecord = asRecord(item);
      const status = stringFrom([roundRecord], ["status", "roundStatus"]).toLowerCase();
      if (status && !["revealed", "complete", "completed", "finished"].includes(status)) {
        continue;
      }
      const round = Math.max(
        1,
        Math.floor(numberFrom([roundRecord], ["round", "roundNumber", "number"], 1)),
      );
      const rows = arrayFrom(
        [roundRecord],
        ["results", "picks", "selections", "teamResults", "teams"],
      );
      grouped.set(round, rows);
    }
  }

  return Array.from(grouped.entries())
    .map(([round, rows]) => {
      const normalized = rows
        .map((row) => normalizeResultRow(row, lookup))
        .filter((result): result is RevealedResult => result !== null);
      const byTeam = new Map<string, RevealedResult>();
      for (const result of normalized) {
        byTeam.set(result.teamId, result);
        byTeam.set(result.teamName.toLowerCase(), result);
      }
      const completeResults =
        teams.length === 0
          ? normalized
          : teams.map(
              (team): RevealedResult =>
                byTeam.get(team.id) ??
                byTeam.get(team.name.toLowerCase()) ?? {
                  teamId: team.id,
                  teamName: team.name,
                  player: null,
                },
            );
      return { round, results: completeResults };
    })
    .sort((a, b) => a.round - b.round);
}

function phaseFrom(roomStatus: string, roundStatus: string): RoomPhase {
  const room = roomStatus.toLowerCase();
  const round = roundStatus.toLowerCase();
  if (["complete", "completed", "finished"].includes(room)) return "completed";
  if (["submitting", "picking", "open", "active"].includes(round)) return "picking";
  if (["revealed", "complete", "completed"].includes(round)) return "revealed";
  return "waiting";
}

interface WorkingTeam extends RoomTeam {
  raw: UnknownRecord;
  explicitTotal: number | null;
  providedGuidance: string[];
  hasExplicitRoster: boolean;
}

export function normalizeRoomState(
  value: unknown,
  role: RoomRole,
  fallbackRoomCode: string,
): DraftRoomState {
  const root = asRecord(value);
  const metadata = asRecord(valueFrom([root], ["roomMetadata", "room", "metadata"]));
  const adminTeamState = asRecord(root.adminTeamState);
  const viewerSource = role === "admin" ? adminTeamState : root;

  const draftConfig = asRecord(root.draftConfig);
  const config = asRecord(root.config);
  const rosterReqs = normalizeRosterRequirements(
    valueFrom(
      [viewerSource, root, metadata, draftConfig, config],
      ["rosterReqs", "rosterRequirements", "requirements"],
    ),
  );
  const scoringConfig = normalizeScoringConfig(
    valueFrom(
      [root, metadata, draftConfig, config],
      ["scoringConfig", "scoring", "scoringMetrics"],
    ),
  );

  const allPlayersRaw = arrayFrom(
    [root, metadata],
    ["allPlayers", "allPlayerPool"],
  );
  const normalizedAllPlayers = normalizePlayerList(allPlayersRaw);
  const allPlayersLookup = playerLookup(normalizedAllPlayers);
  const manualPlayerPoolRaw = arrayFrom(
    [root, metadata],
    ["manualPlayerPool", "manualPlayers"],
  );
  const normalizedManualPlayerPool = normalizePlayerList(
    manualPlayerPoolRaw,
    allPlayersLookup,
  );
  const playerPoolSeed = mergePlayers(
    normalizedAllPlayers,
    normalizedManualPlayerPool,
  );
  const availableRaw = arrayFrom(
    [viewerSource, root],
    ["availablePlayers", "players", "playerPool"],
  );
  const availablePlayers = normalizePlayerList(
    availableRaw,
    playerLookup(playerPoolSeed),
  );
  const rosterPlayerLookup = playerLookup(
    mergePlayers(playerPoolSeed, availablePlayers),
  );

  const rawTeams = arrayFrom([root, metadata], ["teams", "teamStatuses"]);
  const workingTeams: WorkingTeam[] = rawTeams.map((value, index) => {
    const team = asRecord(value);
    const id = stringFrom([team], ["id", "teamId", "team_id"], `team-${index + 1}`);
    const name = stringFrom([team], ["name", "teamName", "team_name"], `Team ${index + 1}`);
    const submissionStatus = stringFrom(
      [team],
      ["submissionStatus", "pickStatus", "status"],
    ).toLowerCase();
    const submitted =
      optionalBooleanFrom([team], ["submitted", "hasSubmitted", "pickSubmitted"]) ??
      ["submitted", "sealed", "picked", "complete"].includes(submissionStatus);
    const rawRoster = valueFrom(
      [team],
      ["roster", "picks", "players", "draftedPlayers"],
    );
    const hasExplicitRoster = Array.isArray(rawRoster);
    const roster = normalizePlayerList(
      hasExplicitRoster ? rawRoster : [],
      rosterPlayerLookup,
    );
    const rosterStatus = buildRosterStatus(roster, rosterReqs);
    const providedGuidance = stringList(
      valueFrom([team], ["guidance", "rosterGuidance"]),
    );

    return {
      id,
      name,
      inviteToken: stringFrom([team], ["inviteToken", "invite_token", "teamToken"]),
      submitted,
      isViewer:
        optionalBooleanFrom([team], ["isViewer", "isMine", "isMe", "you"]) === true,
      roster,
      rosterStatus,
      guidance: providedGuidance.length > 0 ? providedGuidance : rosterGuidance(rosterStatus),
      totalProjectedPts: roundOneDecimal(
        roster.reduce((total, player) => total + player.projectedPts, 0),
      ),
      explicitTotal: optionalNumberFrom(
        [team],
        ["totalProjectedPts", "projectedTotal", "rosterTotal", "totalPoints"],
      ),
      providedGuidance,
      hasExplicitRoster,
      raw: team,
    };
  });

  const preliminaryPlayers = mergePlayers(
    playerPoolSeed,
    availablePlayers,
    ...workingTeams.map((team) => team.roster),
    normalizePlayerList(
      arrayFrom([viewerSource], ["myPicks", "roster", "picks", "draftedPlayers"]),
    ),
  );
  let lookup = playerLookup(preliminaryPlayers);
  let revealedRounds = normalizeHistory(root, metadata, workingTeams, lookup);

  const roomStatus = stringFrom([root, metadata], ["roomStatus", "status"], "pending");
  const roundStatus = stringFrom(
    [root, asRecord(root.currentRoundState), metadata],
    ["roundStatus", "status"],
  );
  const phase = phaseFrom(roomStatus, roundStatus);
  const currentRound = Math.max(
    0,
    Math.floor(numberFrom([root, metadata], ["currentRound", "round"], 0)),
  );

  if (
    (phase === "revealed" || phase === "completed") &&
    currentRound > 0 &&
    !revealedRounds.some((round) => round.round === currentRound)
  ) {
    const results = workingTeams.map((team): RevealedResult => {
      const pickValue = Object.prototype.hasOwnProperty.call(team.raw, "pick")
        ? team.raw.pick
        : team.raw.currentPick;
      return {
        teamId: team.id,
        teamName: team.name,
        player: normalizePlayer(pickValue, lookup),
      };
    });
    if (results.some((result) => result.player !== null)) {
      revealedRounds = [...revealedRounds, { round: currentRound, results }].sort(
        (a, b) => a.round - b.round,
      );
    }
  }

  const historyRosters = new Map<string, DraftPlayer[]>();
  for (const round of revealedRounds) {
    for (const result of round.results) {
      if (!result.player) continue;
      const current = historyRosters.get(result.teamId) ?? [];
      historyRosters.set(result.teamId, mergePlayers(current, [result.player]));
      const nameKey = result.teamName.toLowerCase();
      historyRosters.set(nameKey, mergePlayers(historyRosters.get(nameKey) ?? [], [result.player]));
    }
  }

  const rosterTotalsMap = asRecord(root.rosterTotals);
  const teams: RoomTeam[] = workingTeams.map((team) => {
    const roster = team.hasExplicitRoster
      ? team.roster
      : mergePlayers(
          team.roster,
          historyRosters.get(team.id) ?? [],
          historyRosters.get(team.name.toLowerCase()) ?? [],
        );
    const rosterStatus = buildRosterStatus(roster, rosterReqs);
    const mappedTotal = optionalNumberFrom(
      [asRecord(rosterTotalsMap[team.id]), rosterTotalsMap],
      ["totalProjectedPts", "projectedTotal", "totalPoints", team.id],
    );
    return {
      id: team.id,
      name: team.name,
      inviteToken: team.inviteToken,
      submitted: team.submitted,
      isViewer: team.isViewer,
      roster,
      rosterStatus,
      guidance:
        team.providedGuidance.length > 0
          ? team.providedGuidance
          : rosterGuidance(rosterStatus),
      totalProjectedPts: roundOneDecimal(
        team.explicitTotal ??
          mappedTotal ??
          roster.reduce((total, player) => total + player.projectedPts, 0),
      ),
    };
  });

  const allPlayers = mergePlayers(
    normalizedAllPlayers,
    normalizedManualPlayerPool,
    availablePlayers,
    ...teams.map((team) => team.roster),
  );
  const manualPlayerPool = mergePlayers(
    manualPlayerPoolRaw.length > 0
      ? normalizedManualPlayerPool
      : allPlayersRaw.length > 0
        ? normalizedAllPlayers
        : availablePlayers,
  );

  lookup = playerLookup(allPlayers);

  const explicitAdminTeamId = stringFrom([root, metadata], ["adminTeamId"]);
  let viewerTeamId =
    role === "admin"
      ? explicitAdminTeamId || stringFrom([adminTeamState], ["teamId", "id"])
      : stringFrom([root], ["myTeamId", "teamId"]);
  let viewerTeamName = stringFrom(
    [viewerSource],
    ["teamName", "myTeamName", "name"],
  );

  const markedViewerTeam = teams.find((team) => team.isViewer);
  const matchedViewerTeam = teams.find(
    (team) =>
      (viewerTeamId && team.id === viewerTeamId) ||
      (viewerTeamName && team.name.toLowerCase() === viewerTeamName.toLowerCase()),
  );
  const viewerTeam = matchedViewerTeam ?? markedViewerTeam;
  if (!viewerTeamId && viewerTeam) viewerTeamId = viewerTeam.id;
  if (!viewerTeamName && viewerTeam) viewerTeamName = viewerTeam.name;

  for (const team of teams) {
    team.isViewer = Boolean(
      (viewerTeamId && team.id === viewerTeamId) ||
        (viewerTeamName && team.name.toLowerCase() === viewerTeamName.toLowerCase()),
    );
  }

  const viewerRosterSource = valueFrom(
    [viewerSource],
    ["myPicks", "roster", "picks", "draftedPlayers"],
  );
  const hasExplicitViewerRoster = Array.isArray(viewerRosterSource);
  const viewerRosterRaw = normalizePlayerList(
    hasExplicitViewerRoster ? viewerRosterSource : [],
    lookup,
  );
  const viewerRoster = hasExplicitViewerRoster
    ? mergePlayers(viewerRosterRaw, viewerTeam?.roster ?? [])
    : mergePlayers(
        viewerRosterRaw,
        viewerTeam?.roster ?? [],
        historyRosters.get(viewerTeamId) ?? [],
        historyRosters.get(viewerTeamName.toLowerCase()) ?? [],
      );
  const rawMyPick = valueFrom([viewerSource], ["myPick", "sealedPick", "currentPick"]);
  const myPick = normalizePlayer(rawMyPick, lookup);
  const viewerRosterStatus = buildRosterStatus(viewerRoster, rosterReqs);
  const providedViewerGuidance = stringList(
    valueFrom([viewerSource], ["guidance", "rosterGuidance"]),
  );
  const explicitViewerTotal = optionalNumberFrom(
    [viewerSource],
    ["totalProjectedPts", "projectedTotal", "rosterTotal", "totalPoints"],
  );
  const hasAdminViewer =
    role !== "admin" ||
    Boolean(explicitAdminTeamId || Object.keys(adminTeamState).length > 0);

  const viewer: RoomViewer | null = hasAdminViewer
    ? {
        teamId: viewerTeamId,
        teamName: viewerTeamName || (role === "admin" ? "Commissioner Team" : "Your Team"),
        myPick,
        roster: viewerRoster,
        rosterStatus: viewerRosterStatus,
        guidance:
          providedViewerGuidance.length > 0
            ? providedViewerGuidance
            : rosterGuidance(viewerRosterStatus),
        totalProjectedPts: roundOneDecimal(
          explicitViewerTotal ??
            viewerTeam?.totalProjectedPts ??
            viewerRoster.reduce((total, player) => total + player.projectedPts, 0),
        ),
      }
    : null;

  const totalRounds = Math.max(
    1,
    Math.floor(
      numberFrom(
        [root, metadata, draftConfig],
        ["totalRounds", "numberOfRounds", "rounds"],
        Math.max(1, currentRound),
      ),
    ),
  );
  const flags = asRecord(valueFrom([root], ["actionFlags", "actions"]));
  const canStartRound = optionalBooleanFrom(
    [flags, root],
    ["canStartRound", "canStartNextRound", "startRound", "startNextRound"],
  );
  const canReveal = optionalBooleanFrom(
    [flags, root],
    ["canReveal", "canRevealRound", "reveal"],
  );
  const canFinishDraft = optionalBooleanFrom(
    [flags, root],
    ["canFinishDraft", "canFinish", "finishDraft"],
  );
  const submittedCount = teams.filter((team) => team.submitted).length;
  const availableCountValue = optionalNumberFrom(
    [root, metadata],
    ["availableCount", "playersRemaining", "availablePlayerCount"],
  );

  return {
    draftName: stringFrom([root, metadata], ["draftName", "name"], "Scribner Draft"),
    roomCode: stringFrom(
      [root, metadata],
      ["roomCode", "code", "id"],
      fallbackRoomCode,
    ).toUpperCase(),
    roomStatus,
    phase,
    currentRound,
    totalRounds,
    availablePlayers,
    allPlayers,
    manualPlayerPool,
    availableCount: Math.max(0, Math.floor(availableCountValue ?? availablePlayers.length)),
    teams,
    submittedCount,
    rosterReqs,
    scoringConfig,
    viewer,
    revealedRounds,
    actionFlags: {
      canStartRound:
        canStartRound ??
        (phase !== "completed" &&
          (phase === "waiting" || phase === "revealed") &&
          currentRound < totalRounds),
      canReveal: canReveal ?? (phase === "picking"),
      canFinishDraft:
        canFinishDraft ??
        (phase !== "completed" && phase === "revealed" && currentRound >= totalRounds),
    },
  };
}

export function nextRoundNumber(state: DraftRoomState): number {
  if (state.currentRound <= 0) return 1;
  const currentRoundWasRevealed = state.revealedRounds.some(
    (round) => round.round === state.currentRound,
  );
  if (state.phase === "revealed" || (state.phase === "waiting" && currentRoundWasRevealed)) {
    return Math.min(state.totalRounds, state.currentRound + 1);
  }
  return state.currentRound;
}

export function latestRevealedRound(state: DraftRoomState): RevealedRound | null {
  return state.revealedRounds[state.revealedRounds.length - 1] ?? null;
}
