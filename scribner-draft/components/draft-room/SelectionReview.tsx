"use client";

import {
  CheckCircle2,
  Clock3,
  LockKeyhole,
  LoaderCircle,
  RotateCcw,
  ShieldCheck,
  X,
} from "lucide-react";
import type { DraftPlayer } from "./types";
import { formatProjectedPoints, playerStatLine } from "./state";
import { focusRing, PlayerAvatar, PositionBadge, StatusPill } from "./ui";

export function SelectionReview({
  player,
  impact,
  onChange,
  onClear,
  onSubmit,
  busy = false,
  variant = "desktop",
}: {
  player: DraftPlayer | null;
  impact: string;
  onChange: () => void;
  onClear: () => void;
  onSubmit: () => void;
  busy?: boolean;
  variant?: "desktop" | "mobile";
}) {
  if (variant === "mobile" && !player) return null;

  const containerClass =
    variant === "mobile"
      ? "fixed inset-x-0 bottom-0 z-50 rounded-t-[20px] border-x-0 border-b-0 border-t border-accent/30 bg-ink-850 px-4 pt-3 shadow-[0_-24px_70px_rgba(0,0,0,0.55)] lg:hidden"
      : "rounded-card border border-ink-700 bg-ink-850 p-4 shadow-[0_18px_50px_rgba(0,0,0,0.2)]";

  return (
    <section
      className={containerClass}
      aria-label="Selection review"
      style={variant === "mobile" ? { paddingBottom: "max(1rem, env(safe-area-inset-bottom))" } : undefined}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <LockKeyhole size={15} className="text-accent" aria-hidden="true" />
          <h2 className="text-xs font-black uppercase tracking-[0.13em] text-fg-muted">
            Selection review
          </h2>
        </div>
        <StatusPill tone="neutral">Not submitted</StatusPill>
      </div>

      {!player ? (
        <div className="py-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-dashed border-ink-500 bg-ink-800 text-fg-faint">
            <ShieldCheck size={20} aria-hidden="true" />
          </div>
          <h3 className="mt-3 text-sm font-bold text-fg">No player selected</h3>
          <p className="mt-1 text-xs leading-5 text-fg-muted">
            Choose a player to review roster fit before sealing your pick.
          </p>
        </div>
      ) : (
        <>
          <div className="mt-3 flex min-w-0 items-center gap-3">
            <PlayerAvatar name={player.name} src={player.headshot} size={variant === "mobile" ? "md" : "lg"} />
            <div className="min-w-0 flex-1">
              <div className="flex items-start gap-2">
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-base font-extrabold text-fg">{player.name}</h3>
                  <p className="mt-0.5 text-xs font-semibold text-fg-muted">
                    {player.team} <span className="mx-1 text-ink-600">•</span> {player.position}
                  </p>
                </div>
                <PositionBadge position={player.position} selected />
              </div>
              <p className="mt-1.5 truncate text-[11px] text-fg-faint">{playerStatLine(player, true)}</p>
            </div>
            <div className="text-right">
              <strong className="block text-xl font-black tabular-nums text-accent">
                {formatProjectedPoints(player.projectedPts)}
              </strong>
              <span className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">proj pts</span>
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-accent/20 bg-accent/5 px-3 py-2.5">
            <p className="text-[10px] font-black uppercase tracking-[0.12em] text-accent">Roster impact</p>
            <p className="mt-1 text-xs leading-5 text-fg-muted">{impact}</p>
          </div>

          <div className="mt-3 grid grid-cols-[auto_auto_minmax(0,1fr)] gap-2">
            <button
              type="button"
              onClick={onChange}
              className={`flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-ink-600 bg-ink-800 px-3 text-xs font-bold text-fg-muted transition hover:border-accent/50 hover:text-accent ${focusRing}`}
            >
              <RotateCcw size={14} aria-hidden="true" /> Change
            </button>
            <button
              type="button"
              onClick={onClear}
              className={`flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-ink-600 bg-ink-800 px-3 text-xs font-bold text-fg-muted transition hover:border-loss/50 hover:text-loss ${focusRing}`}
            >
              <X size={14} aria-hidden="true" /> Clear
            </button>
            <button
              type="button"
              onClick={onSubmit}
              disabled={busy}
              className={`flex min-h-11 min-w-0 items-center justify-center gap-2 rounded-xl bg-accent px-3 text-xs font-black text-ink-950 shadow-[0_0_24px_rgba(42,179,255,0.16)] transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-60 ${focusRing}`}
            >
              {busy ? (
                <LoaderCircle size={15} className="animate-spin" aria-hidden="true" />
              ) : (
                <LockKeyhole size={15} aria-hidden="true" />
              )}
              <span className="truncate">Submit Sealed Pick</span>
            </button>
          </div>
        </>
      )}
    </section>
  );
}

export function SealedPickCard({
  player,
  submittedCount,
  teamCount,
  prominent = false,
}: {
  player: DraftPlayer | null;
  submittedCount: number;
  teamCount: number;
  prominent?: boolean;
}) {
  return (
    <section
      className={`overflow-hidden rounded-card border border-win/30 bg-ink-850 shadow-[0_18px_50px_rgba(0,0,0,0.18)] ${
        prominent ? "p-5 sm:p-6" : "p-4"
      }`}
      aria-labelledby={prominent ? "sealed-pick-title" : undefined}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-win/30 bg-win/10 text-win">
            <CheckCircle2 size={20} aria-hidden="true" />
          </div>
          <div>
            <h2 id={prominent ? "sealed-pick-title" : undefined} className="text-sm font-extrabold text-fg">
              Pick sealed
            </h2>
            <p className="mt-0.5 text-[11px] text-fg-muted">Final until the round is revealed</p>
          </div>
        </div>
        <StatusPill tone="success">Submitted</StatusPill>
      </div>

      {player ? (
        <div className={`mt-4 flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-800/80 ${prominent ? "p-4" : "p-3"}`}>
          <PlayerAvatar name={player.name} src={player.headshot} size={prominent ? "lg" : "md"} />
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-extrabold text-fg">{player.name}</h3>
            <p className="mt-0.5 text-xs text-fg-muted">
              {player.team} <span className="mx-1 text-ink-600">•</span> {player.position}
            </p>
            <p className="mt-1 truncate text-[10px] text-fg-faint">{playerStatLine(player)}</p>
          </div>
          <div className="text-right">
            <strong className="text-lg font-black tabular-nums text-accent">
              {formatProjectedPoints(player.projectedPts)}
            </strong>
            <p className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">pts</p>
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded-xl border border-ink-700 bg-ink-800 p-3 text-xs text-fg-muted">
          Your sealed selection is recorded. Player details will refresh shortly.
        </p>
      )}

      <div className="mt-4 flex items-center gap-2 border-t border-ink-700/70 pt-3 text-xs text-fg-muted">
        <Clock3 size={14} className="text-warn" aria-hidden="true" />
        <span>
          Waiting for reveal
          <span className="mx-1.5 text-ink-600">•</span>
          <strong className="font-bold text-fg">{submittedCount}/{teamCount}</strong> teams submitted
        </span>
      </div>
    </section>
  );
}
