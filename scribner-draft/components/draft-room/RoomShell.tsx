"use client";

import {
  ClipboardList,
  ListChecks,
  LogOut,
  Settings2,
  ShieldCheck,
  Trophy,
  UsersRound,
  Wifi,
  WifiOff,
} from "lucide-react";
import type {
  ConnectionStatus,
  DraftRoomState,
  RoomRole,
  RoomTab,
} from "./types";
import { focusRing, StatusPill } from "./ui";

const TAB_META: Record<
  RoomTab,
  { label: string; icon: typeof ClipboardList }
> = {
  draft: { label: "Draft", icon: ClipboardList },
  roster: { label: "My Roster", icon: UsersRound },
  results: { label: "Results", icon: Trophy },
  commissioner: { label: "Commissioner", icon: Settings2 },
};

function phaseMeta(state: DraftRoomState) {
  switch (state.phase) {
    case "picking":
      return { label: "Picking", tone: "accent" as const, detail: "Picks are sealed" };
    case "revealed":
      return { label: "Revealed", tone: "success" as const, detail: "Round complete" };
    case "completed":
      return { label: "Complete", tone: "success" as const, detail: "Draft finished" };
    default:
      return { label: "Waiting", tone: "neutral" as const, detail: "Round not open" };
  }
}

function ConnectionPill({ status }: { status: ConnectionStatus }) {
  if (status === "connected") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-win">
        <Wifi size={13} aria-hidden="true" /> Synced
      </span>
    );
  }
  if (status === "connecting") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-fg-muted">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-fg-muted" /> Connecting
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[11px] font-semibold ${
        status === "error" ? "text-loss" : "text-warn"
      }`}
    >
      <WifiOff size={13} aria-hidden="true" />
      {status === "error" ? "Connection lost" : "Reconnecting"}
    </span>
  );
}

export function RoomShell({
  state,
  role,
  activeTab,
  onTabChange,
  onLeave,
  connectionStatus,
  onRetry,
  children,
  mobileReviewOpen = false,
}: {
  state: DraftRoomState;
  role: RoomRole;
  activeTab: RoomTab;
  onTabChange: (tab: RoomTab) => void;
  onLeave: () => void;
  connectionStatus: ConnectionStatus;
  onRetry: () => void;
  children: React.ReactNode;
  mobileReviewOpen?: boolean;
}) {
  const phase = phaseMeta(state);
  const tabs: RoomTab[] =
    role === "admin"
      ? ["draft", "roster", "results", "commissioner"]
      : ["draft", "roster", "results"];
  const teamLabel = state.viewer?.teamName || "No draft team assigned";
  const shownRound = state.currentRound > 0 ? state.currentRound : 1;

  return (
    <div className="min-h-screen bg-ink-900 text-fg">
      <a
        href="#room-content"
        className={`fixed left-3 top-3 z-[120] -translate-y-24 rounded-lg bg-accent px-4 py-2 text-sm font-bold text-ink-950 transition focus:translate-y-0 ${focusRing}`}
      >
        Skip to room content
      </a>

      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 -top-64 h-[520px] w-[520px] rounded-full bg-accent/10 blur-[120px]" />
        <div className="absolute -right-64 top-1/3 h-[460px] w-[460px] rounded-full bg-accent-dim/5 blur-[130px]" />
      </div>

      <header className="relative border-b border-ink-700/70 bg-ink-950/50">
        <div className="mx-auto max-w-[1440px] px-4 py-4 sm:px-6 lg:px-8 lg:py-5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-accent/50 bg-ink-800 shadow-[0_0_24px_rgba(42,179,255,0.12)]">
                <span className="text-xs font-black tracking-tight text-accent">FS</span>
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="truncate text-lg font-extrabold tracking-tight text-fg sm:text-xl">
                    {state.draftName}
                  </h1>
                  <StatusPill tone={phase.tone}>{phase.label}</StatusPill>
                </div>
                <p className="mt-1 truncate text-xs text-fg-muted">
                  {role === "admin" ? "Commissioner" : "General Manager"}
                  <span className="mx-1.5 text-ink-600">•</span>
                  <span className="font-semibold text-fg-muted">{teamLabel}</span>
                  <span className="mx-1.5 text-ink-600">•</span>
                  Room {state.roomCode}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onLeave}
              className={`flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-full border border-ink-600 bg-ink-850 px-3 text-xs font-bold text-fg-muted transition hover:border-loss/50 hover:bg-loss/10 hover:text-loss sm:px-4 ${focusRing}`}
            >
              <LogOut size={16} aria-hidden="true" />
              <span className="hidden sm:inline">Leave Room</span>
              <span className="sm:hidden">Leave</span>
            </button>
          </div>

          <div className="mt-4 grid grid-cols-2 overflow-hidden rounded-card border border-ink-700 bg-ink-850/80 sm:grid-cols-4">
            <SummaryItem
              label={state.currentRound > 0 ? "Round" : "Next round"}
              value={`${shownRound} / ${state.totalRounds}`}
              icon={<ListChecks size={15} aria-hidden="true" />}
            />
            <SummaryItem
              label="Phase"
              value={phase.label}
              detail={phase.detail}
              icon={<ShieldCheck size={15} aria-hidden="true" />}
            />
            <SummaryItem
              label="Submitted"
              value={`${state.submittedCount} / ${state.teams.length}`}
              detail={state.phase === "picking" ? "This round" : "Teams"}
              icon={<UsersRound size={15} aria-hidden="true" />}
            />
            <SummaryItem
              label="Available"
              value={String(state.availableCount)}
              detail="Players remaining"
              icon={<ClipboardList size={15} aria-hidden="true" />}
            />
          </div>
        </div>
      </header>

      <div className="sticky top-0 z-30 border-b border-ink-700/80 bg-ink-900/95 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-3 px-2 sm:px-6 lg:px-8">
          <nav
            className={`grid min-w-0 flex-1 ${role === "admin" ? "grid-cols-4" : "grid-cols-3"}`}
            aria-label="Draft room views"
            role="tablist"
          >
            {tabs.map((tab) => {
              const meta = TAB_META[tab];
              const Icon = meta.icon;
              const active = activeTab === tab;
              return (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  aria-controls="room-content"
                  onClick={() => onTabChange(tab)}
                  className={`relative flex min-h-[60px] min-w-0 flex-col items-center justify-center gap-0.5 px-0.5 text-[10px] font-bold transition sm:min-h-[54px] sm:flex-row sm:gap-2 sm:px-4 sm:text-sm ${
                    active ? "text-accent" : "text-fg-muted hover:text-fg"
                  } ${focusRing}`}
                >
                  <Icon size={16} className="shrink-0" aria-hidden="true" />
                  <span className="max-w-full whitespace-nowrap leading-tight">{meta.label}</span>
                  <span
                    className={`absolute inset-x-3 bottom-0 h-0.5 rounded-full transition ${
                      active ? "bg-accent" : "bg-transparent"
                    }`}
                  />
                </button>
              );
            })}
          </nav>
          <div className="hidden shrink-0 border-l border-ink-700 pl-4 sm:block">
            <ConnectionPill status={connectionStatus} />
          </div>
        </div>
      </div>

      {connectionStatus !== "connected" ? (
        <div
          className={`relative z-20 border-b px-4 py-2.5 ${
            connectionStatus === "error"
              ? "border-loss/30 bg-loss/10"
              : "border-warn/30 bg-warn/10"
          }`}
          role="status"
          aria-live="polite"
        >
          <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-3 text-xs">
            <div className="sm:hidden">
              <ConnectionPill status={connectionStatus} />
            </div>
            <p className="hidden text-fg-muted sm:block">
              {connectionStatus === "error"
                ? "Live updates are offline. Your last synced room state is still shown."
                : "Trying to restore live room updates…"}
            </p>
            <button
              type="button"
              onClick={onRetry}
              className={`min-h-9 rounded-full border border-current px-3 font-bold text-fg ${focusRing}`}
            >
              Retry now
            </button>
          </div>
        </div>
      ) : null}

      <main
        id="room-content"
        role="tabpanel"
        tabIndex={-1}
        className={`relative mx-auto max-w-[1440px] px-4 py-5 sm:px-6 lg:px-8 lg:py-6 ${
          mobileReviewOpen ? "pb-[290px] lg:pb-8" : "pb-10"
        }`}
      >
        {children}
      </main>
    </div>
  );
}

function SummaryItem({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="border-b border-r border-ink-700/70 px-3 py-3 last:border-r-0 sm:border-b-0 sm:px-4">
      <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-fg-faint">
        <span className="text-accent">{icon}</span>
        {label}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <strong className="text-base font-black tabular-nums text-fg">{value}</strong>
        {detail ? <span className="hidden text-[10px] text-fg-faint xl:inline">{detail}</span> : null}
      </div>
    </div>
  );
}
