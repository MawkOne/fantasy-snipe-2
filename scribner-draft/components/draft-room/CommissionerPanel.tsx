"use client";

import { useState } from "react";
import {
  Check,
  CheckCircle2,
  Eye,
  Flag,
  Link2,
  LoaderCircle,
  Pencil,
  Play,
  Settings2,
  ShieldAlert,
  Trash2,
  Trophy,
  UserRoundCog,
  UserRoundCheck,
  UsersRound,
} from "lucide-react";
import type {
  CommissionerAction,
  DraftManagementView,
  DraftRoomState,
} from "./types";
import { nextRoundNumber } from "./state";
import { focusRing, InlineNotice, StatusPill, TeamMark } from "./ui";

export function CommissionerPanel({
  state,
  onAction,
  busyAction,
  error,
  onManagement,
  compact = false,
}: {
  state: DraftRoomState;
  onAction: (action: CommissionerAction) => void;
  busyAction: string;
  error?: string;
  onManagement: (view: DraftManagementView) => void;
  compact?: boolean;
}) {
  const nextRound = nextRoundNumber(state);
  const waitingTeams = state.teams.filter((team) => !team.submitted);
  const progress = state.teams.length > 0 ? (state.submittedCount / state.teams.length) * 100 : 0;
  const [copiedTeamId, setCopiedTeamId] = useState<string | null>(null);

  const copyInviteLink = async (teamId: string, inviteToken?: string) => {
    if (!inviteToken) return;
    const link = `${window.location.origin}/room/${encodeURIComponent(state.roomCode)}?invite=${encodeURIComponent(inviteToken)}`;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(link);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = link;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      setCopiedTeamId(teamId);
      window.setTimeout(() => setCopiedTeamId((current) => (current === teamId ? null : current)), 1600);
    } catch {
      // Clipboard unavailable; leave the button in its default state.
    }
  };

  let primary: {
    action: CommissionerAction;
    label: string;
    icon: typeof Play;
    enabled: boolean;
    tone: "accent" | "warning";
  } | null = null;

  if (state.phase === "picking") {
    primary = {
      action: "reveal",
      label: `Reveal Picks (${state.submittedCount}/${state.teams.length})`,
      icon: Eye,
      enabled: state.actionFlags.canReveal,
      tone: waitingTeams.length > 0 ? "warning" : "accent",
    };
  } else if (
    state.phase === "revealed" &&
    state.currentRound >= state.totalRounds
  ) {
    primary = {
      action: "finish-draft",
      label: "Finish Draft",
      icon: Trophy,
      enabled: state.actionFlags.canFinishDraft,
      tone: "accent",
    };
  } else if (state.phase !== "completed") {
    primary = {
      action: "start-round",
      label: state.currentRound > 0 ? `Start Round ${nextRound}` : "Start Round 1",
      icon: Play,
      enabled: state.actionFlags.canStartRound,
      tone: "accent",
    };
  }

  const busy = primary ? busyAction === primary.action : false;
  const PrimaryIcon = primary?.icon ?? Play;

  return (
    <section
      className={`rounded-card border border-ink-700 bg-ink-850 ${compact ? "p-4" : "p-4 sm:p-5"}`}
      aria-labelledby={compact ? undefined : "commissioner-title"}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-accent/30 bg-accent/10 text-accent">
            <Settings2 size={17} aria-hidden="true" />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.13em] text-accent">Commissioner</p>
            <h2 id={compact ? undefined : "commissioner-title"} className="mt-0.5 text-sm font-extrabold text-fg">
              Round controls
            </h2>
          </div>
        </div>
        <StatusPill
          tone={state.phase === "picking" ? "warning" : state.phase === "completed" ? "success" : "neutral"}
        >
          {state.phase}
        </StatusPill>
      </div>

      {state.phase === "picking" ? (
        <div className="mt-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <strong className="text-2xl font-black tabular-nums text-fg">{state.submittedCount}</strong>
              <span className="ml-1 text-xs font-semibold text-fg-muted">of {state.teams.length}</span>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-fg-faint">
              teams submitted
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-ink-700" aria-hidden="true">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                waitingTeams.length === 0 ? "bg-win" : "bg-accent"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
          {waitingTeams.length > 0 ? (
            <p className="mt-2 text-[11px] leading-4 text-fg-muted">
              {waitingTeams.length} {waitingTeams.length === 1 ? "team is" : "teams are"} still waiting. Their names will be confirmed before an early reveal.
            </p>
          ) : (
            <p className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-semibold text-win">
              <CheckCircle2 size={13} aria-hidden="true" /> Every team has submitted.
            </p>
          )}
        </div>
      ) : state.phase === "completed" ? (
        <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-win/30 bg-win/10 px-3 py-3 text-xs text-win">
          <Trophy size={16} className="shrink-0" aria-hidden="true" />
          The draft is complete. Final rosters and totals are locked.
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-ink-700 bg-ink-800/60 px-3 py-3">
          <p className="text-xs font-semibold text-fg">
            {state.phase === "revealed"
              ? `Round ${state.currentRound} is revealed.`
              : `Round ${nextRound} is ready to open.`}
          </p>
          <p className="mt-1 text-[11px] leading-4 text-fg-muted">
            {state.phase === "revealed"
              ? state.currentRound >= state.totalRounds
                ? "Finish the draft to lock final rosters."
                : "Start the next round when every GM is ready."
              : "Starting opens the shared player browser for every GM."}
          </p>
        </div>
      )}

      {error ? (
        <div className="mt-3">
          <InlineNotice tone="danger">{error}</InlineNotice>
        </div>
      ) : null}

      {primary ? (
        <button
          type="button"
          onClick={() => onAction(primary!.action)}
          disabled={!primary.enabled || busy}
          className={`mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-45 ${
            primary.tone === "warning"
              ? "border border-warn/50 bg-warn text-ink-950 hover:bg-amber-400"
              : "bg-accent text-ink-950 hover:bg-accent-bright"
          } ${focusRing}`}
        >
          {busy ? (
            <LoaderCircle size={17} className="animate-spin" aria-hidden="true" />
          ) : (
            <PrimaryIcon size={17} aria-hidden="true" />
          )}
          {busy
            ? primary.action === "reveal"
              ? "Revealing…"
              : primary.action === "finish-draft"
                ? "Finishing…"
                : "Starting…"
            : primary.label}
        </button>
      ) : null}

      {!compact || state.phase === "picking" ? (
        <div className="mt-5 border-t border-ink-700 pt-4">
          <div className="mb-2.5 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <UsersRound size={15} className="text-accent" aria-hidden="true" />
              <h3 className="text-xs font-black uppercase tracking-[0.11em] text-fg-muted">Team status</h3>
            </div>
            <span className="text-[10px] tabular-nums text-fg-faint">{state.teams.length} teams</span>
          </div>

          <div className={`${compact ? "max-h-[310px] overflow-y-auto pr-1" : ""} space-y-1.5`}>
            {state.teams.map((team) => (
              <div
                key={team.id}
                className={`flex min-h-12 items-center gap-2.5 rounded-xl border px-2.5 py-2 ${
                  team.isViewer
                    ? "border-accent/30 bg-accent/10"
                    : "border-ink-700 bg-ink-800/50"
                }`}
              >
                <TeamMark name={team.name} highlight={team.isViewer} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="truncate text-xs font-bold text-fg">{team.name}</span>
                    {team.isViewer ? <span className="text-[9px] font-black uppercase text-accent">You</span> : null}
                  </div>
                  <span className="text-[10px] text-fg-faint">
                    {state.phase === "picking"
                      ? team.submitted
                        ? "Sealed pick received"
                        : "No pick received"
                      : `${team.roster.length} rostered`}
                  </span>
                </div>
                {team.inviteToken ? (
                  <button
                    type="button"
                    onClick={() => void copyInviteLink(team.id, team.inviteToken)}
                    className={`inline-flex min-h-[26px] shrink-0 items-center gap-1 rounded-lg border px-2 text-[9px] font-bold uppercase tracking-[0.1em] transition ${focusRing} ${
                      copiedTeamId === team.id
                        ? "border-win/40 bg-win/10 text-win"
                        : "border-ink-600 bg-ink-800 text-fg-muted hover:border-accent/40 hover:text-accent"
                    }`}
                    aria-label={`Copy invite link for ${team.name}`}
                    title="Copy private invite link"
                  >
                    {copiedTeamId === team.id ? (
                      <Check size={11} aria-hidden="true" />
                    ) : (
                      <Link2 size={11} aria-hidden="true" />
                    )}
                    {copiedTeamId === team.id ? "Copied" : "Invite"}
                  </button>
                ) : null}
                {state.phase === "picking" ? (
                  team.submitted ? (
                    <StatusPill tone="success">
                      <UserRoundCheck size={11} aria-hidden="true" /> Submitted
                    </StatusPill>
                  ) : (
                    <StatusPill tone="neutral">Waiting</StatusPill>
                  )
                ) : (
                  <StatusPill tone="neutral">Ready</StatusPill>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {!compact ? (
        <>
          <div className="mt-5 border-t border-ink-700 pt-5" aria-labelledby="draft-management-title">
            <div className="flex items-start gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-ink-600 bg-ink-800 text-accent">
                <UserRoundCog size={17} aria-hidden="true" />
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.13em] text-fg-faint">
                  Commissioner tools
                </p>
                <h3 id="draft-management-title" className="mt-0.5 text-sm font-extrabold text-fg">
                  Draft management
                </h3>
                <p className="mt-1 text-[11px] leading-4 text-fg-muted">
                  Correct rosters, update the live setup, or permanently remove this draft.
                </p>
              </div>
            </div>

            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              <button
                type="button"
                onClick={() => onManagement("rosters")}
                className={`flex min-h-12 items-center justify-center gap-2 rounded-xl border border-accent/35 bg-accent/10 px-3 text-xs font-black text-accent transition hover:border-accent/60 hover:bg-accent/15 ${focusRing}`}
              >
                <UserRoundCog size={16} aria-hidden="true" /> Manage Rosters
              </button>
              <button
                type="button"
                onClick={() => onManagement("setup")}
                className={`flex min-h-12 items-center justify-center gap-2 rounded-xl border border-ink-600 bg-ink-800 px-3 text-xs font-black text-fg transition hover:border-accent/40 hover:text-accent ${focusRing}`}
              >
                <Pencil size={15} aria-hidden="true" /> Edit Setup
              </button>
              <button
                type="button"
                onClick={() => onManagement("delete")}
                className={`flex min-h-12 items-center justify-center gap-2 rounded-xl border border-loss/40 bg-loss/10 px-3 text-xs font-black text-loss transition hover:bg-loss/20 ${focusRing}`}
              >
                <Trash2 size={15} aria-hidden="true" /> Delete Draft
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-start gap-2 rounded-xl border border-ink-700/80 bg-ink-800/50 px-3 py-2.5 text-[10px] leading-4 text-fg-faint">
            <ShieldAlert size={14} className="mt-0.5 shrink-0 text-fg-muted" aria-hidden="true" />
            Submission status is visible here, but every other team’s player remains sealed until reveal.
          </div>
        </>
      ) : null}
    </section>
  );
}
