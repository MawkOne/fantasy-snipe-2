"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCircle2,
  LoaderCircle,
  Pencil,
  Plus,
  Save,
  Search,
  ShieldAlert,
  Trash2,
  UserRoundCog,
} from "lucide-react";
import type {
  DraftPlayer,
  DraftRoomState,
  RoomTeam,
  RosterRequirements,
  RosterSlotKey,
  ScoringConfig,
  ScoringGroup,
} from "./types";
import {
  Dialog,
  focusRing,
  PositionBadge,
  StatusPill,
  TeamMark,
} from "./ui";

export type CommissionerMutation = (
  action: string,
  payload: Record<string, unknown>,
) => Promise<boolean>;

type Feedback = { tone: "success" | "error"; message: string };
type PlayerOperation = "assign" | "replace" | "remove";
type RosterStep =
  | { view: "roster" }
  | { view: "picker"; operation: "assign" | "replace"; oldPlayer?: DraftPlayer }
  | {
      view: "confirm";
      operation: PlayerOperation;
      oldPlayer?: DraftPlayer;
      newPlayer?: DraftPlayer;
    };

const POSITION_FILTERS = ["All", "F", "C", "W", "D", "G"] as const;
type PositionFilter = (typeof POSITION_FILTERS)[number];

const ROSTER_FIELDS: Array<{
  key: RosterSlotKey;
  shortLabel: string;
  label: string;
}> = [
  { key: "F", shortLabel: "F", label: "Flex forwards" },
  { key: "C", shortLabel: "C", label: "Centres" },
  { key: "W", shortLabel: "W", label: "Wingers" },
  { key: "D", shortLabel: "D", label: "Defence" },
  { key: "G", shortLabel: "G", label: "Goalies" },
];

const SCORING_GROUPS: Array<{
  id: ScoringGroup;
  title: string;
  description: string;
  metrics: Array<{ key: string; code: string; label: string }>;
}> = [
  {
    id: "skater",
    title: "Skaters",
    description: "Applied to every skater",
    metrics: [
      { key: "g", code: "G", label: "Goals" },
      { key: "a", code: "A", label: "Assists" },
      { key: "pm", code: "+/-", label: "Plus / minus" },
      { key: "pim", code: "PIM", label: "Penalty minutes" },
      { key: "shg", code: "SHG", label: "Short-handed goals" },
      { key: "shog", code: "SHOG", label: "Shootout goals" },
    ],
  },
  {
    id: "dBonus",
    title: "Defence bonus",
    description: "Added for defencemen",
    metrics: [
      { key: "g", code: "DG", label: "Defence goals bonus" },
      { key: "a", code: "DA", label: "Defence assists bonus" },
    ],
  },
  {
    id: "goalie",
    title: "Goalies",
    description: "Applied to goalie projections",
    metrics: [
      { key: "w", code: "W", label: "Wins" },
      { key: "ga", code: "GA", label: "Goals against" },
      { key: "sv", code: "S", label: "Saves" },
      { key: "ol", code: "OL", label: "Overtime losses" },
      { key: "shol", code: "SHOL", label: "Shootout losses" },
      { key: "so", code: "SO", label: "Shutouts" },
    ],
  },
];

function messageFrom(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

function matchesPosition(player: DraftPlayer, filter: PositionFilter): boolean {
  const position = player.position.toUpperCase();
  if (filter === "All") return true;
  if (filter === "F") return ["C", "LW", "RW", "W"].includes(position);
  if (filter === "W") return ["LW", "RW", "W"].includes(position);
  return position === filter;
}

function isManualAssignment(player: DraftPlayer): boolean {
  const source = player.assignmentSource?.toLowerCase() ?? "";
  return source.includes("manual") || source.includes("commissioner") || source === "admin";
}

function useGuardedClose(busy: boolean, onClose: () => void): () => void {
  const busyRef = useRef(busy);
  busyRef.current = busy;
  return useCallback(() => {
    if (!busyRef.current) onClose();
  }, [onClose]);
}

function FeedbackBanner({ feedback }: { feedback: Feedback }) {
  const success = feedback.tone === "success";
  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-2.5 rounded-xl border px-3 py-2.5 text-xs leading-5 ${
        success
          ? "border-win/30 bg-win/10 text-win"
          : "border-loss/30 bg-loss/10 text-loss"
      }`}
    >
      {success ? (
        <CheckCircle2 size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      ) : (
        <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      )}
      <span>{feedback.message}</span>
    </div>
  );
}

function PlayerDetails({
  player,
  showOwnership = false,
}: {
  player: DraftPlayer;
  showOwnership?: boolean;
}) {
  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-1.5">
        <h4 className="truncate text-sm font-extrabold text-fg">{player.name}</h4>
        {isManualAssignment(player) ? (
          <StatusPill tone="accent">Manual assignment</StatusPill>
        ) : null}
      </div>
      <p className="mt-0.5 text-[11px] font-semibold text-fg-muted">
        {player.position} · {player.team} · ADP {player.adp ? player.adp.toFixed(1) : "—"}
      </p>
      {showOwnership && (player.rosteredByTeamIds?.length ?? 0) > 0 ? (
        <p className="mt-0.5 text-[10px] font-semibold text-warn">
          Rostered by another team · shared assignment allowed
        </p>
      ) : null}
    </div>
  );
}

function ProjectedPoints({ player }: { player: DraftPlayer }) {
  return (
    <div className="shrink-0 text-right">
      <strong className="block text-base font-black tabular-nums text-accent">
        {player.adp != null ? player.adp.toFixed(1) : "—"}
      </strong>
      <span className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">
        ADP
      </span>
    </div>
  );
}

function SelectedPlayerCard({
  player,
  label,
}: {
  player: DraftPlayer;
  label: string;
}) {
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-800/70 p-3">
      <p className="mb-2 text-[10px] font-black uppercase tracking-[0.12em] text-fg-faint">
        {label}
      </p>
      <div className="flex items-center gap-3">
        <PositionBadge position={player.position} />
        <div className="min-w-0 flex-1">
          <PlayerDetails player={player} />
        </div>
        <ProjectedPoints player={player} />
      </div>
    </div>
  );
}

export function ManageRostersDialog({
  open,
  state,
  busyAction,
  onClose,
  onMutation,
}: {
  open: boolean;
  state: DraftRoomState;
  busyAction: string;
  onClose: () => void;
  onMutation: CommissionerMutation;
}) {
  const [selectedTeamId, setSelectedTeamId] = useState(state.teams[0]?.id ?? "");
  const [step, setStep] = useState<RosterStep>({ view: "roster" });
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<PositionFilter>("All");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const stepFocusRef = useRef<HTMLDivElement>(null);
  const initialStepRef = useRef(true);
  const busy = busyAction.startsWith("manual-");
  const selectedTeam =
    state.teams.find((team) => team.id === selectedTeamId) ?? state.teams[0] ?? null;

  const selectedTeamPlayerIds = useMemo(
    () => new Set((selectedTeam?.roster ?? []).map((player) => player.id)),
    [selectedTeam],
  );
  const filteredPlayers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return state.manualPlayerPool
      .filter((player) => !selectedTeamPlayerIds.has(player.id))
      .filter((player) => matchesPosition(player, position))
      .filter(
        (player) =>
          !normalizedQuery ||
          player.name.toLowerCase().includes(normalizedQuery) ||
          player.team.toLowerCase().includes(normalizedQuery) ||
          player.position.toLowerCase().includes(normalizedQuery),
      )
      .sort(
        (left, right) =>
          (left.adp ?? 999) - (right.adp ?? 999) || left.name.localeCompare(right.name),
      );
  }, [position, query, selectedTeamPlayerIds, state.manualPlayerPool]);

  useEffect(() => {
    if (initialStepRef.current) {
      initialStepRef.current = false;
      return;
    }
    const timer = window.setTimeout(() => {
      const preferred = stepFocusRef.current?.querySelector<HTMLElement>(
        "[data-step-autofocus]",
      );
      (preferred ?? stepFocusRef.current)?.focus();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [step.view]);

  const resetToRoster = () => {
    setStep({ view: "roster" });
    setQuery("");
    setPosition("All");
  };

  const close = useGuardedClose(busy, onClose);

  const startPicker = (operation: "assign" | "replace", oldPlayer?: DraftPlayer) => {
    setFeedback(null);
    setQuery("");
    setPosition("All");
    setStep({ view: "picker", operation, oldPlayer });
  };

  const confirmMutation = async () => {
    if (step.view !== "confirm" || !selectedTeam) return;
    setFeedback(null);

    let action = "";
    let payload: Record<string, unknown> = { teamId: selectedTeam.id };
    let successMessage = "Roster updated.";

    if (step.operation === "assign" && step.newPlayer) {
      action = "manual-assign-player";
      payload = { ...payload, playerId: step.newPlayer.id };
      successMessage = `${step.newPlayer.name} was manually assigned to ${selectedTeam.name}.`;
    } else if (step.operation === "replace" && step.oldPlayer && step.newPlayer) {
      action = "manual-replace-player";
      payload = {
        ...payload,
        oldPlayerId: step.oldPlayer.id,
        newPlayerId: step.newPlayer.id,
      };
      successMessage = `${step.oldPlayer.name} was replaced with ${step.newPlayer.name} on ${selectedTeam.name}.`;
    } else if (step.operation === "remove" && step.oldPlayer) {
      action = "manual-remove-player";
      payload = { ...payload, playerId: step.oldPlayer.id };
      successMessage = `${step.oldPlayer.name} was removed from ${selectedTeam.name}.`;
    } else {
      return;
    }

    try {
      const refreshed = await onMutation(action, payload);
      resetToRoster();
      setFeedback({
        tone: "success",
        message: refreshed
          ? successMessage
          : `${successMessage} Live sync will retry the room refresh.`,
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message: messageFrom(error, "The roster change could not be completed."),
      });
    }
  };

  return (
    <Dialog
      open={open}
      title="Manage rosters"
      description="Assign, replace, or remove players on behalf of any team. Every change requires confirmation."
      onClose={close}
      size="xl"
    >
      <div className="space-y-4">
        {state.teams.length > 0 ? (
          <label className="block rounded-xl border border-ink-700 bg-ink-800/60 p-3">
            <span className="text-[10px] font-black uppercase tracking-[0.12em] text-fg-faint">
              Team to manage
            </span>
            <div className="mt-2 flex items-center gap-2.5">
              <TeamMark name={selectedTeam?.name ?? "Team"} highlight />
              <select
                data-autofocus
                value={selectedTeam?.id ?? ""}
                onChange={(event) => {
                  setSelectedTeamId(event.target.value);
                  setFeedback(null);
                  resetToRoster();
                }}
                disabled={busy}
                className={`h-11 min-w-0 flex-1 rounded-xl border border-ink-600 bg-ink-900 px-3 text-sm font-bold text-fg disabled:opacity-60 ${focusRing}`}
                aria-label="Team to manage"
              >
                {state.teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name} · {team.roster.length} players
                  </option>
                ))}
              </select>
            </div>
          </label>
        ) : (
          <div className="rounded-xl border border-warn/30 bg-warn/10 p-4 text-sm text-warn">
            Add teams before manually managing rosters.
          </div>
        )}

        {feedback ? <FeedbackBanner feedback={feedback} /> : null}

        <div ref={stepFocusRef} tabIndex={-1} className="focus:outline-none">
          {selectedTeam && step.view === "roster" ? (
            <RosterOverview
              team={selectedTeam}
              busy={busy}
              onAdd={() => startPicker("assign")}
              onReplace={(player) => startPicker("replace", player)}
              onRemove={(player) => {
                setFeedback(null);
                setStep({ view: "confirm", operation: "remove", oldPlayer: player });
              }}
            />
          ) : null}

          {selectedTeam && step.view === "picker" ? (
            <PlayerPicker
              team={selectedTeam}
              operation={step.operation}
              oldPlayer={step.oldPlayer}
              players={filteredPlayers}
              totalPlayers={state.manualPlayerPool.length}
              query={query}
              position={position}
              onQueryChange={setQuery}
              onPositionChange={setPosition}
              onBack={resetToRoster}
              onSelect={(player) =>
                setStep({
                  view: "confirm",
                  operation: step.operation,
                  oldPlayer: step.oldPlayer,
                  newPlayer: player,
                })
              }
            />
          ) : null}

          {selectedTeam && step.view === "confirm" ? (
            <RosterMutationConfirmation
              team={selectedTeam}
              step={step}
              busy={busy}
              onCancel={resetToRoster}
              onConfirm={() => void confirmMutation()}
            />
          ) : null}
        </div>
      </div>
    </Dialog>
  );
}

function RosterOverview({
  team,
  busy,
  onAdd,
  onReplace,
  onRemove,
}: {
  team: RoomTeam;
  busy: boolean;
  onAdd: () => void;
  onReplace: (player: DraftPlayer) => void;
  onRemove: (player: DraftPlayer) => void;
}) {
  return (
    <section aria-labelledby="managed-roster-title">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-accent">
            Selected team
          </p>
          <h3 id="managed-roster-title" className="mt-1 text-base font-extrabold text-fg">
            {team.name} roster
          </h3>
          <p className="mt-0.5 text-xs text-fg-muted">
            {team.roster.length} players
          </p>
        </div>
        <button
          type="button"
          data-step-autofocus
          onClick={onAdd}
          disabled={busy}
          className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 transition hover:bg-accent-bright disabled:opacity-50 ${focusRing}`}
        >
          <Plus size={16} aria-hidden="true" /> Add Player
        </button>
      </div>

      <div className="mt-3 overflow-hidden rounded-xl border border-ink-700 bg-ink-850">
        {team.roster.length > 0 ? (
          <div className="divide-y divide-ink-700/70">
            {team.roster.map((player, index) => (
              <div
                key={`${player.id}-${index}`}
                className="grid gap-3 p-3 sm:grid-cols-[minmax(0,1fr)_100px_208px] sm:items-center"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <PositionBadge position={player.position} />
                  <div className="min-w-0 flex-1">
                    <PlayerDetails player={player} />
                  </div>
                </div>
                <ProjectedPoints player={player} />
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => onReplace(player)}
                    disabled={busy}
                    className={`flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-ink-600 bg-ink-800 px-3 text-xs font-black text-fg-muted transition hover:border-accent/50 hover:text-accent disabled:opacity-50 ${focusRing}`}
                  >
                    <Pencil size={14} aria-hidden="true" /> Replace
                  </button>
                  <button
                    type="button"
                    onClick={() => onRemove(player)}
                    disabled={busy}
                    className={`flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-loss/40 bg-loss/10 px-3 text-xs font-black text-loss transition hover:bg-loss/20 disabled:opacity-50 ${focusRing}`}
                  >
                    <Trash2 size={14} aria-hidden="true" /> Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-5 py-12 text-center">
            <UserRoundCog size={24} className="mx-auto text-fg-faint" aria-hidden="true" />
            <h4 className="mt-3 text-sm font-extrabold text-fg">This roster is empty</h4>
            <p className="mt-1 text-xs text-fg-muted">Use Add Player to make the first manual assignment.</p>
          </div>
        )}
      </div>
    </section>
  );
}

function PlayerPicker({
  team,
  operation,
  oldPlayer,
  players,
  totalPlayers,
  query,
  position,
  onQueryChange,
  onPositionChange,
  onBack,
  onSelect,
}: {
  team: RoomTeam;
  operation: "assign" | "replace";
  oldPlayer?: DraftPlayer;
  players: DraftPlayer[];
  totalPlayers: number;
  query: string;
  position: PositionFilter;
  onQueryChange: (value: string) => void;
  onPositionChange: (value: PositionFilter) => void;
  onBack: () => void;
  onSelect: (player: DraftPlayer) => void;
}) {
  return (
    <section aria-labelledby="manual-player-pool-title">
      <button
        type="button"
        onClick={onBack}
        className={`flex min-h-11 items-center gap-2 rounded-xl px-2 text-sm font-bold text-fg-muted hover:text-fg ${focusRing}`}
      >
        <ArrowLeft size={16} aria-hidden="true" /> Back to {team.name}
      </button>

      <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-accent">
            {operation === "replace" ? "Choose a replacement" : "Manual assignment"}
          </p>
          <h3 id="manual-player-pool-title" className="mt-1 text-base font-extrabold text-fg">
            All player pool
          </h3>
          <p className="mt-0.5 text-xs text-fg-muted">
            {oldPlayer
              ? `Replacing ${oldPlayer.name} on ${team.name}.`
              : `Adding a player to ${team.name}.`}
          </p>
        </div>
        <span className="text-xs font-semibold tabular-nums text-fg-faint">
          {players.length} matches · {totalPlayers} in pool
        </span>
      </div>

      <div className="mt-3 rounded-xl border border-ink-700 bg-ink-850">
        <div className="border-b border-ink-700 p-3">
          <label className="relative block">
            <span className="sr-only">Search all players</span>
            <Search
              size={17}
              className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-fg-faint"
              aria-hidden="true"
            />
            <input
              type="search"
              data-step-autofocus
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="Search player, NHL team, or position"
              className={`h-11 w-full rounded-xl border border-ink-600 bg-ink-900 pl-10 pr-3 text-sm text-fg placeholder:text-fg-faint ${focusRing}`}
            />
          </label>
          <div className="mt-2 grid grid-cols-6 gap-1.5" aria-label="Filter player pool by position">
            {POSITION_FILTERS.map((filter) => {
              const active = position === filter;
              return (
                <button
                  key={filter}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onPositionChange(filter)}
                  className={`min-h-11 rounded-lg border px-1 text-xs font-black transition ${
                    active
                      ? "border-accent bg-accent/20 text-accent"
                      : "border-ink-700 bg-ink-800 text-fg-muted hover:border-ink-600 hover:text-fg"
                  } ${focusRing}`}
                >
                  {filter}
                </button>
              );
            })}
          </div>
        </div>

        {players.length > 0 ? (
          <div className="divide-y divide-ink-700/70">
            {players.map((player) => (
              <button
                key={player.id}
                type="button"
                onClick={() => onSelect(player)}
                className={`grid min-h-[72px] w-full grid-cols-[minmax(0,1fr)_86px_28px] items-center gap-3 px-3 py-2.5 text-left transition hover:bg-ink-800/80 ${focusRing}`}
              >
                <div className="flex min-w-0 items-center gap-3">
                  <PositionBadge position={player.position} />
                  <PlayerDetails player={player} showOwnership />
                </div>
                <ProjectedPoints player={player} />
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-ink-600 text-fg-faint" aria-hidden="true">
                  <Plus size={14} />
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="px-5 py-12 text-center">
            <Search size={22} className="mx-auto text-fg-faint" aria-hidden="true" />
            <h4 className="mt-3 text-sm font-extrabold text-fg">No eligible players found</h4>
            <p className="mt-1 text-xs leading-5 text-fg-muted">
              Try another search or position. Players already on this team are excluded.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

function RosterMutationConfirmation({
  team,
  step,
  busy,
  onCancel,
  onConfirm,
}: {
  team: RoomTeam;
  step: Extract<RosterStep, { view: "confirm" }>;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const actionLabel =
    step.operation === "remove"
      ? "Remove Player"
      : step.operation === "replace"
        ? "Replace Player"
        : "Assign Player";

  return (
    <section aria-labelledby="roster-change-confirmation-title">
      <div className="rounded-xl border border-warn/30 bg-warn/10 p-4">
        <div className="flex items-start gap-2.5">
          <ShieldAlert size={18} className="mt-0.5 shrink-0 text-warn" aria-hidden="true" />
          <div>
            <h3 id="roster-change-confirmation-title" className="text-sm font-extrabold text-fg">
              Confirm roster change
            </h3>
            <p className="mt-1 text-xs leading-5 text-fg-muted">
              This updates {team.name} immediately and will be visible after the room refreshes.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {step.oldPlayer ? (
          <SelectedPlayerCard
            player={step.oldPlayer}
            label={step.operation === "remove" ? "Player to remove" : "Current player"}
          />
        ) : null}
        {step.newPlayer ? (
          <SelectedPlayerCard
            player={step.newPlayer}
            label={step.operation === "replace" ? "Replacement player" : "Player to assign"}
          />
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          data-step-autofocus
          onClick={onCancel}
          disabled={busy}
          className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg disabled:opacity-50 ${focusRing}`}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className={`flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-black disabled:opacity-60 ${
            step.operation === "remove"
              ? "border border-loss/50 bg-loss text-white hover:bg-red-500"
              : "bg-accent text-ink-950 hover:bg-accent-bright"
          } ${focusRing}`}
        >
          {busy ? (
            <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
          ) : step.operation === "remove" ? (
            <Trash2 size={16} aria-hidden="true" />
          ) : (
            <Check size={16} aria-hidden="true" />
          )}
          {busy ? "Updating…" : actionLabel}
        </button>
      </div>
    </section>
  );
}

type EditableScoringConfig = Record<
  ScoringGroup,
  Record<string, { enabled: boolean; value: string }>
>;
type EditableRosterRequirements = Record<RosterSlotKey, string>;

function editableScoring(config: ScoringConfig): EditableScoringConfig {
  const result: EditableScoringConfig = { skater: {}, dBonus: {}, goalie: {} };
  for (const group of SCORING_GROUPS) {
    for (const metric of group.metrics) {
      const current = config[group.id][metric.key] ?? { enabled: true, value: 0 };
      result[group.id][metric.key] = {
        enabled: current.enabled,
        value: String(current.value),
      };
    }
  }
  return result;
}

function editableRoster(requirements: RosterRequirements): EditableRosterRequirements {
  return {
    F: String(requirements.F),
    C: String(requirements.C),
    W: String(requirements.W),
    D: String(requirements.D),
    G: String(requirements.G),
  };
}

function parseRoster(
  requirements: EditableRosterRequirements,
): RosterRequirements | null {
  const parsed = {} as RosterRequirements;
  for (const field of ROSTER_FIELDS) {
    const raw = requirements[field.key].trim();
    const value = Number(raw);
    if (!raw || !Number.isInteger(value) || value < 0) return null;
    parsed[field.key] = value;
  }
  return parsed;
}

function scoringPayload(config: EditableScoringConfig): ScoringConfig {
  const payload: ScoringConfig = { skater: {}, dBonus: {}, goalie: {} };
  for (const group of SCORING_GROUPS) {
    for (const metric of group.metrics) {
      const current = config[group.id][metric.key];
      const value = Number(current.value);
      payload[group.id][metric.key] = {
        enabled: current.enabled,
        value: Number.isFinite(value) ? value : 0,
      };
    }
  }
  return payload;
}

export function EditLiveSetupDialog({
  open,
  state,
  busyAction,
  onClose,
  onMutation,
}: {
  open: boolean;
  state: DraftRoomState;
  busyAction: string;
  onClose: () => void;
  onMutation: CommissionerMutation;
}) {
  const [draftName, setDraftName] = useState(state.draftName);
  const [rounds, setRounds] = useState(String(state.totalRounds));
  const [rosterReqs, setRosterReqs] = useState<EditableRosterRequirements>(() =>
    editableRoster(state.rosterReqs),
  );
  const [scoring, setScoring] = useState<EditableScoringConfig>(() =>
    editableScoring(state.scoringConfig),
  );
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const busy = busyAction === "update-live-setup";
  const parsedRoster = parseRoster(rosterReqs);
  const rosterTarget = parsedRoster
    ? Object.values(parsedRoster).reduce((total, value) => total + value, 0)
    : 0;
  const parsedRounds = Number(rounds);
  const minimumRounds = Math.max(1, state.currentRound, rosterTarget);
  const invalidScoring = SCORING_GROUPS.some((group) =>
    group.metrics.some((metric) => {
      const current = scoring[group.id][metric.key];
      return (
        current.enabled &&
        (!current.value.trim() || !Number.isFinite(Number(current.value)))
      );
    }),
  );

  const issues: string[] = [];
  if (state.phase === "completed") {
    issues.push("Completed drafts can no longer be edited.");
  }
  if (!draftName.trim()) issues.push("Draft name is required.");
  else if (draftName.trim().length > 80) issues.push("Draft name must be 80 characters or fewer.");
  if (!parsedRoster) issues.push("Roster requirements must be whole numbers of zero or greater.");
  if (!rounds.trim() || !Number.isInteger(parsedRounds) || parsedRounds < 1 || parsedRounds > 30) {
    issues.push("Rounds must be a whole number from 1 to 30.");
  } else if (parsedRounds < state.currentRound) {
    issues.push(`Rounds cannot be lower than the current round (${state.currentRound}).`);
  } else if (parsedRounds < rosterTarget) {
    issues.push(`Rounds must cover the ${rosterTarget}-player roster target.`);
  }
  if (invalidScoring) issues.push("Every enabled scoring category needs a valid decimal value.");

  const close = useGuardedClose(busy, onClose);

  const updateMetric = (
    group: ScoringGroup,
    key: string,
    update: Partial<{ enabled: boolean; value: string }>,
  ) => {
    setFeedback(null);
    setScoring((current) => ({
      ...current,
      [group]: {
        ...current[group],
        [key]: { ...current[group][key], ...update },
      },
    }));
  };

  const save = async () => {
    if (issues.length > 0 || !parsedRoster) return;
    setFeedback(null);
    try {
      const refreshed = await onMutation("update-live-setup", {
        draftName: draftName.trim(),
        rounds: parsedRounds,
        rosterReqs: parsedRoster,
        scoringConfig: scoringPayload(scoring),
      });
      setFeedback({
        tone: "success",
        message: refreshed
          ? "Live draft setup saved and the room state was refreshed."
          : "Live draft setup saved. Live sync will retry the room refresh.",
      });
    } catch (error) {
      setFeedback({
        tone: "error",
        message: messageFrom(error, "The live setup could not be saved."),
      });
    }
  };

  return (
    <Dialog
      open={open}
      title="Edit live setup"
      description="Update the draft identity, remaining format, roster target, and projection scoring without leaving the room."
      onClose={close}
      size="xl"
    >
      <div className="space-y-5">
        {feedback ? <FeedbackBanner feedback={feedback} /> : null}

        <section className="rounded-xl border border-ink-700 bg-ink-800/50 p-3 sm:p-4" aria-labelledby="live-identity-title">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 id="live-identity-title" className="text-sm font-extrabold text-fg">Draft identity & rounds</h3>
              <p className="mt-0.5 text-[11px] text-fg-faint">
                {state.currentRound > 0
                  ? `Round ${state.currentRound} is the current live floor.`
                  : "No rounds have opened yet."}
              </p>
            </div>
            <StatusPill tone="neutral">Target {rosterTarget}</StatusPill>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_150px]">
            <label>
              <span className="text-[10px] font-black uppercase tracking-[0.11em] text-fg-muted">Draft name</span>
              <input
                type="text"
                data-autofocus
                value={draftName}
                maxLength={81}
                onChange={(event) => {
                  setDraftName(event.target.value);
                  setFeedback(null);
                }}
                className={`mt-1.5 h-11 w-full rounded-xl border border-ink-600 bg-ink-900 px-3 text-sm font-bold text-fg ${focusRing}`}
              />
            </label>
            <label>
              <span className="text-[10px] font-black uppercase tracking-[0.11em] text-fg-muted">Rounds</span>
              <input
                type="number"
                min={minimumRounds}
                max={30}
                step={1}
                inputMode="numeric"
                value={rounds}
                onChange={(event) => {
                  setRounds(event.target.value);
                  setFeedback(null);
                }}
                className={`mt-1.5 h-11 w-full rounded-xl border border-ink-600 bg-ink-900 px-3 text-sm font-black tabular-nums text-fg ${focusRing}`}
              />
            </label>
          </div>
        </section>

        <section aria-labelledby="live-roster-target-title">
          <div className="flex items-end justify-between gap-3">
            <div>
              <h3 id="live-roster-target-title" className="text-sm font-extrabold text-fg">Roster requirements</h3>
              <p className="mt-0.5 text-[11px] text-fg-faint">F / C / W / D / G · whole players only</p>
            </div>
            <span className="text-xs font-bold tabular-nums text-fg-muted">{rosterTarget} total</span>
          </div>
          <div className="mt-3 grid grid-cols-5 gap-1.5 sm:gap-2">
            {ROSTER_FIELDS.map((field) => (
              <label key={field.key} className="rounded-xl border border-ink-700 bg-ink-800/60 p-2 text-center sm:p-3">
                <span className="block text-xs font-black text-accent">{field.shortLabel}</span>
                <span className="mt-0.5 hidden text-[9px] font-semibold text-fg-faint sm:block">{field.label}</span>
                <input
                  type="number"
                  min={0}
                  step={1}
                  inputMode="numeric"
                  value={rosterReqs[field.key]}
                  onChange={(event) => {
                    setRosterReqs((current) => ({ ...current, [field.key]: event.target.value }));
                    setFeedback(null);
                  }}
                  aria-label={`${field.label} required`}
                  className={`mt-2 h-11 w-full rounded-lg border border-ink-600 bg-ink-900 px-1 text-center text-sm font-black tabular-nums text-fg ${focusRing}`}
                />
              </label>
            ))}
          </div>
        </section>

        <section aria-labelledby="live-scoring-title">
          <div>
            <h3 id="live-scoring-title" className="text-sm font-extrabold text-fg">Scoring configuration</h3>
            <p className="mt-0.5 text-[11px] text-fg-faint">Toggle categories and enter positive, negative, zero, or decimal point values.</p>
          </div>
          <div className="mt-3 grid gap-3 lg:grid-cols-2 xl:grid-cols-[1.05fr_.85fr_1.05fr]">
            {SCORING_GROUPS.map((group) => (
              <div key={group.id} className="overflow-hidden rounded-xl border border-ink-700 bg-ink-800/50">
                <div className="border-b border-ink-700 px-3.5 py-3">
                  <h4 className="text-xs font-extrabold text-fg">{group.title}</h4>
                  <p className="mt-0.5 text-[10px] text-fg-faint">{group.description}</p>
                </div>
                <div className="divide-y divide-ink-700/70">
                  {group.metrics.map((metric) => {
                    const current = scoring[group.id][metric.key];
                    const invalid = current.enabled && (!current.value.trim() || !Number.isFinite(Number(current.value)));
                    return (
                      <div
                        key={`${group.id}-${metric.key}`}
                        className={`grid min-h-[60px] grid-cols-[44px_minmax(0,1fr)_96px] items-center gap-2 px-2.5 py-2 ${
                          current.enabled ? "" : "opacity-55"
                        }`}
                      >
                        <button
                          type="button"
                          role="switch"
                          aria-checked={current.enabled}
                          aria-label={`${current.enabled ? "Disable" : "Enable"} ${metric.label}`}
                          onClick={() => updateMetric(group.id, metric.key, { enabled: !current.enabled })}
                          className={`flex h-11 w-11 items-center justify-center rounded-lg ${focusRing}`}
                        >
                          <span className={`flex h-5 w-5 items-center justify-center rounded-md border-2 transition ${
                            current.enabled
                              ? "border-accent bg-accent text-ink-950"
                              : "border-ink-600 bg-ink-900 text-transparent"
                          }`}>
                            <Check size={12} strokeWidth={3} aria-hidden="true" />
                          </span>
                        </button>
                        <label htmlFor={`live-score-${group.id}-${metric.key}`} className="min-w-0 cursor-pointer">
                          <span className="block truncate text-xs font-bold text-fg">{metric.label}</span>
                          <span className="mt-0.5 block font-mono text-[9px] font-bold uppercase tracking-wider text-accent">{metric.code}</span>
                        </label>
                        <div className="relative">
                          <input
                            id={`live-score-${group.id}-${metric.key}`}
                            type="number"
                            inputMode="decimal"
                            step="any"
                            value={current.value}
                            disabled={!current.enabled}
                            aria-invalid={invalid}
                            onChange={(event) => updateMetric(group.id, metric.key, { value: event.target.value })}
                            className={`h-11 w-full rounded-lg border bg-ink-900 py-2 pl-2 pr-7 text-right text-xs font-bold tabular-nums text-fg disabled:cursor-not-allowed ${
                              invalid ? "border-loss/70" : "border-ink-600"
                            } ${focusRing}`}
                          />
                          <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-bold text-fg-faint">pt</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {issues.length > 0 ? (
          <div className="rounded-xl border border-warn/30 bg-warn/10 px-3 py-3 text-xs text-warn" role="alert">
            <div className="flex items-start gap-2.5">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
              <div>
                <p className="font-black">Review setup before saving</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-4 text-fg-muted">
                  {issues.map((issue) => <li key={issue}>{issue}</li>)}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        <div className="grid grid-cols-2 gap-2 border-t border-ink-700 pt-4">
          <button
            type="button"
            onClick={close}
            disabled={busy}
            className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg disabled:opacity-50 ${focusRing}`}
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => void save()}
            disabled={busy || issues.length > 0}
            className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-50 ${focusRing}`}
          >
            {busy ? (
              <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
            ) : (
              <Save size={16} aria-hidden="true" />
            )}
            {busy ? "Saving…" : "Save Live Setup"}
          </button>
        </div>
      </div>
    </Dialog>
  );
}


export function DeleteDraftDialog({
  open,
  draftName,
  busyAction,
  onClose,
  onDelete,
}: {
  open: boolean;
  draftName: string;
  busyAction: string;
  onClose: () => void;
  onDelete: (confirmationName: string) => Promise<void>;
}) {
  const [confirmationName, setConfirmationName] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const busy = busyAction === "delete-draft";
  const confirmed = confirmationName === draftName;

  const close = useGuardedClose(busy, onClose);

  const remove = async () => {
    if (!confirmed) return;
    setFeedback(null);
    try {
      await onDelete(confirmationName);
    } catch (error) {
      setFeedback({
        tone: "error",
        message: messageFrom(error, "The draft could not be deleted."),
      });
    }
  };

  return (
    <Dialog
      open={open}
      title="Delete draft"
      description="Permanently delete this draft, its rosters, picks, teams, and room access. This cannot be undone."
      onClose={close}
      size="md"
    >
      <div className="rounded-xl border border-loss/40 bg-loss/10 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-loss/40 bg-loss/10 text-loss">
            <Trash2 size={18} aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-fg">This deletion is permanent</h3>
            <p className="mt-1 text-xs leading-5 text-fg-muted">
              All GM links will stop working immediately. No draft history or roster data can be recovered from this room.
            </p>
          </div>
        </div>
      </div>

      {feedback ? <div className="mt-3"><FeedbackBanner feedback={feedback} /></div> : null}

      <label className="mt-4 block">
        <span className="text-xs font-bold text-fg-muted">
          Type <strong className="text-fg">{draftName}</strong> exactly to confirm
        </span>
        <input
          type="text"
          data-autofocus
          autoComplete="off"
          spellCheck={false}
          value={confirmationName}
          onChange={(event) => {
            setConfirmationName(event.target.value);
            setFeedback(null);
          }}
          aria-invalid={confirmationName.length > 0 && !confirmed}
          className={`mt-2 h-11 w-full rounded-xl border bg-ink-900 px-3 text-sm font-bold text-fg ${
            confirmationName.length > 0 && !confirmed ? "border-loss/60" : "border-ink-600"
          } ${focusRing}`}
        />
      </label>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={close}
          disabled={busy}
          className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg disabled:opacity-50 ${focusRing}`}
        >
          Keep Draft
        </button>
        <button
          type="button"
          onClick={() => void remove()}
          disabled={!confirmed || busy}
          className={`flex min-h-11 items-center justify-center gap-2 rounded-xl border border-loss/50 bg-loss px-4 text-sm font-black text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40 ${focusRing}`}
        >
          {busy ? (
            <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
          ) : (
            <Trash2 size={16} aria-hidden="true" />
          )}
          {busy ? "Deleting…" : "Delete Forever"}
        </button>
      </div>
    </Dialog>
  );
}
