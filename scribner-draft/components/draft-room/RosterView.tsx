"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Target,
  TrendingUp,
  Trophy,
  UsersRound,
} from "lucide-react";
import type {
  DraftPlayer,
  RoomTeam,
  RoomViewer,
  RosterSlotKey,
  RosterStatus,
} from "./types";
import { formatProjectedPoints, playerStatLine } from "./state";
import { PositionBadge, StatusPill, TeamMark } from "./ui";

const SLOT_LABEL: Record<RosterSlotKey, string> = {
  F: "Flex F",
  C: "Centre",
  W: "Winger",
  D: "Defence",
  G: "Goalie",
};

function targetTotal(status: RosterStatus): number {
  return Object.values(status).reduce((total, slot) => total + slot.required, 0);
}

function filledTotal(status: RosterStatus): number {
  return Object.values(status).reduce(
    (total, slot) => total + Math.min(slot.current, slot.required),
    0,
  );
}

export function RosterStatusGrid({
  status,
  compact = false,
}: {
  status: RosterStatus;
  compact?: boolean;
}) {
  return (
    <div className="grid grid-cols-5 gap-1.5" aria-label="Roster requirements">
      {(Object.keys(SLOT_LABEL) as RosterSlotKey[]).map((key) => {
        const slot = status[key];
        const style =
          slot.state === "unmet"
            ? "border-warn/30 bg-warn/10 text-warn"
            : slot.state === "exceeded"
              ? "border-accent/30 bg-accent/10 text-accent"
              : "border-win/30 bg-win/10 text-win";
        return (
          <div
            key={key}
            className={`rounded-xl border text-center ${compact ? "px-1 py-2" : "px-1.5 py-2.5"} ${style}`}
            title={`${SLOT_LABEL[key]}: ${slot.current} of ${slot.required}`}
          >
            <span className="block text-[9px] font-black uppercase tracking-[0.1em] opacity-80">
              {key}
            </span>
            <strong className={`${compact ? "text-sm" : "text-base"} mt-0.5 block font-black tabular-nums`}>
              {slot.current}<span className="font-semibold opacity-55">/{slot.required}</span>
            </strong>
          </div>
        );
      })}
    </div>
  );
}

export function RosterSnapshot({
  viewer,
  title = "Roster status",
}: {
  viewer: RoomViewer;
  title?: string;
}) {
  const total = targetTotal(viewer.rosterStatus);
  const filled = filledTotal(viewer.rosterStatus);
  const guidance = viewer.guidance[0] ?? "Roster targets complete";

  return (
    <section className="rounded-card border border-ink-700 bg-ink-850 p-4" aria-label={title}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.13em] text-fg-faint">Your team</p>
          <h2 className="mt-1 text-sm font-extrabold text-fg">
            {title}
          </h2>
        </div>
        <div className="text-right">
          <strong className="block text-lg font-black tabular-nums text-accent">
            {formatProjectedPoints(viewer.totalProjectedPts)}
          </strong>
          <span className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">projected pts</span>
        </div>
      </div>

      <div className="mt-3">
        <RosterStatusGrid status={viewer.rosterStatus} compact />
      </div>

      <div className="mt-3 flex items-center justify-between gap-3 text-[11px]">
        <span className="inline-flex items-center gap-1.5 font-semibold text-fg-muted">
          {filled >= total ? (
            <CheckCircle2 size={14} className="text-win" aria-hidden="true" />
          ) : (
            <AlertTriangle size={14} className="text-warn" aria-hidden="true" />
          )}
          {guidance}
        </span>
        <span className="shrink-0 tabular-nums text-fg-faint">{viewer.roster.length} picks</span>
      </div>
      <p className="mt-2 text-[10px] leading-4 text-fg-faint">
        W combines LW + RW. F uses surplus centres or wingers after C and W slots.
      </p>
    </section>
  );
}

export function RosterView({ viewer }: { viewer: RoomViewer }) {
  const total = targetTotal(viewer.rosterStatus);
  const filled = filledTotal(viewer.rosterStatus);

  return (
    <section aria-labelledby="my-roster-title">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.15em] text-accent">{viewer.teamName}</p>
          <h2 id="my-roster-title" className="mt-1 text-xl font-extrabold tracking-tight text-fg">
            My Roster
          </h2>
          <p className="mt-1 text-xs text-fg-muted">Revealed picks and positional targets</p>
        </div>
        <div className="rounded-xl border border-accent/25 bg-accent/10 px-4 py-2.5 text-right">
          <strong className="block text-xl font-black tabular-nums text-accent">
            {formatProjectedPoints(viewer.totalProjectedPts)}
          </strong>
          <span className="text-[9px] font-black uppercase tracking-[0.12em] text-fg-faint">
            total projected pts
          </span>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
        <div className="overflow-hidden rounded-card border border-ink-700 bg-ink-850">
          <div className="flex items-center justify-between border-b border-ink-700 px-4 py-3">
            <div className="flex items-center gap-2">
              <UsersRound size={16} className="text-accent" aria-hidden="true" />
              <h3 className="text-sm font-bold text-fg">Drafted players</h3>
            </div>
            <span className="text-xs font-semibold tabular-nums text-fg-muted">{viewer.roster.length} players</span>
          </div>
          {viewer.roster.length > 0 ? (
            <div className="divide-y divide-ink-700/70">
              {viewer.roster.map((player, index) => (
                <RosterPlayerRow key={`${player.id}-${index}`} player={player} />
              ))}
            </div>
          ) : (
            <div className="px-5 py-14 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-ink-600 bg-ink-800 text-fg-faint">
                <UsersRound size={20} aria-hidden="true" />
              </div>
              <h3 className="mt-3 text-sm font-bold text-fg">Your roster is empty</h3>
              <p className="mt-1 text-xs text-fg-muted">Revealed selections will appear here.</p>
            </div>
          )}
        </div>

        <aside className="space-y-3">
          <div className="rounded-card border border-ink-700 bg-ink-850 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Target size={16} className="text-accent" aria-hidden="true" />
                <h3 className="text-sm font-bold text-fg">Roster targets</h3>
              </div>
              <StatusPill tone={filled >= total ? "success" : "warning"}>
                {filled}/{total} filled
              </StatusPill>
            </div>
            <div className="mt-4">
              <RosterStatusGrid status={viewer.rosterStatus} />
            </div>
            <p className="mt-3 text-[10px] leading-4 text-fg-faint">
              W is the combined LW + RW count. F is a flex slot filled by extra C, LW, or RW players.
            </p>
          </div>

          <div className="rounded-card border border-ink-700 bg-ink-850 p-4">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-accent" aria-hidden="true" />
              <h3 className="text-sm font-bold text-fg">Draft guidance</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {viewer.guidance.map((message, index) => {
                const complete = message.toLowerCase().includes("complete");
                return (
                  <li key={`${message}-${index}`} className="flex items-start gap-2 text-xs leading-5 text-fg-muted">
                    {complete ? (
                      <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-win" aria-hidden="true" />
                    ) : (
                      <AlertTriangle size={14} className="mt-0.5 shrink-0 text-warn" aria-hidden="true" />
                    )}
                    {message}
                  </li>
                );
              })}
            </ul>
          </div>
        </aside>
      </div>
    </section>
  );
}

function RosterPlayerRow({ player }: { player: DraftPlayer }) {
  return (
    <div className="grid min-h-[68px] grid-cols-[34px_minmax(0,1fr)_70px] items-center gap-2.5 px-3 py-2.5 sm:grid-cols-[34px_minmax(0,1fr)_minmax(200px,1.2fr)_80px] sm:px-4">
      <PositionBadge position={player.position} />
      <div className="min-w-0">
        <h4 className="truncate text-sm font-bold text-fg">{player.name}</h4>
        <p className="mt-0.5 text-[11px] font-semibold text-fg-muted">{player.team}</p>
      </div>
      <p className="hidden line-clamp-2 text-xs leading-4 text-fg-faint sm:block" title={playerStatLine(player)}>{playerStatLine(player)}</p>
      <div className="text-right">
        <strong className="block text-sm font-black tabular-nums text-accent">
          {player.adp != null ? player.adp.toFixed(1) : "—"}
        </strong>
        <span className="text-[9px] uppercase tracking-wider text-fg-faint">ADP</span>
      </div>
    </div>
  );
}

export function FinalRostersView({
  teams,
  viewerTeamId,
}: {
  teams: RoomTeam[];
  viewerTeamId?: string;
}) {
  const ranked = [...teams].sort((a, b) => b.totalProjectedPts - a.totalProjectedPts);

  return (
    <section aria-labelledby="final-rosters-title">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-full border border-warn/30 bg-warn/10 text-warn">
          <Trophy size={21} aria-hidden="true" />
        </div>
        <div>
          <h2 id="final-rosters-title" className="text-xl font-extrabold tracking-tight text-fg">
            Final rosters
          </h2>
          <p className="mt-0.5 text-xs text-fg-muted">Every team’s completed roster and projected total</p>
        </div>
      </div>

      <div className="space-y-2.5">
        {ranked.map((team, rank) => {
          const isViewer = team.id === viewerTeamId;
          return (
            <details
              key={team.id}
              className={`group overflow-hidden rounded-card border bg-ink-850 ${
                isViewer ? "border-accent/50" : "border-ink-700"
              }`}
              open={isViewer || ranked.length <= 3}
            >
              <summary className="flex min-h-[68px] cursor-pointer list-none items-center gap-3 px-3 py-3 sm:px-4 [&::-webkit-details-marker]:hidden">
                <span className="w-5 text-center text-xs font-black tabular-nums text-fg-faint">{rank + 1}</span>
                <TeamMark name={team.name} highlight={isViewer} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="truncate text-sm font-extrabold text-fg">{team.name}</h3>
                    {isViewer ? <StatusPill tone="accent">You</StatusPill> : null}
                  </div>
                  <p className="mt-0.5 text-[11px] text-fg-muted">{team.roster.length} drafted players</p>
                </div>
                <div className="text-right">
                  <strong className="block text-base font-black tabular-nums text-accent">
                    {formatProjectedPoints(team.totalProjectedPts)}
                  </strong>
                  <span className="text-[9px] uppercase tracking-wider text-fg-faint">proj pts</span>
                </div>
                <ChevronDown
                  size={17}
                  className="text-fg-faint transition group-open:rotate-180"
                  aria-hidden="true"
                />
              </summary>
              <div className="border-t border-ink-700">
                <div className="bg-ink-800/50 p-3 sm:p-4">
                  <RosterStatusGrid status={team.rosterStatus} compact />
                </div>
                {team.roster.length > 0 ? (
                  <div className="divide-y divide-ink-700/70">
                    {team.roster.map((player, index) => (
                      <RosterPlayerRow key={`${player.id}-${index}`} player={player} />
                    ))}
                  </div>
                ) : (
                  <p className="px-4 py-6 text-center text-xs text-fg-muted">No revealed picks.</p>
                )}
              </div>
            </details>
          );
        })}
      </div>
    </section>
  );
}
