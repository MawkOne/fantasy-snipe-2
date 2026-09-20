"use client";

import { useEffect, useMemo, useState } from "react";
import { Ban, CheckCircle2, Copy, History, Trophy } from "lucide-react";
import type { RevealedRound } from "./types";
import { formatProjectedPoints, playerStatLine } from "./state";
import { focusRing, PlayerAvatar, PositionBadge, StatusPill, TeamMark } from "./ui";

export function ResultsView({
  rounds,
  title = "Round results",
  compact = false,
}: {
  rounds: RevealedRound[];
  title?: string;
  compact?: boolean;
}) {
  const latestRound = rounds[rounds.length - 1]?.round ?? 0;
  const [selectedRound, setSelectedRound] = useState(latestRound);

  useEffect(() => {
    if (!rounds.some((round) => round.round === selectedRound)) {
      setSelectedRound(rounds[rounds.length - 1]?.round ?? 0);
    }
  }, [rounds, selectedRound]);

  const active = rounds.find((round) => round.round === selectedRound) ?? rounds[rounds.length - 1];
  const duplicateCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const result of active?.results ?? []) {
      if (!result.player) continue;
      counts.set(result.player.id, (counts.get(result.player.id) ?? 0) + 1);
    }
    return counts;
  }, [active]);

  if (rounds.length === 0) {
    return (
      <section className="rounded-card border border-ink-700 bg-ink-850 px-5 py-12 text-center" aria-labelledby="results-title">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-ink-600 bg-ink-800 text-fg-faint">
          <History size={23} aria-hidden="true" />
        </div>
        <h2 id="results-title" className="mt-4 text-base font-extrabold text-fg">No revealed rounds yet</h2>
        <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-fg-muted">
          Every team’s selection, including duplicate picks and no-picks, will appear here after a reveal.
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="results-title">
      <div className={`flex flex-wrap items-end justify-between gap-3 ${compact ? "mb-3" : "mb-4"}`}>
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.15em] text-accent">Reveal history</p>
          <h2 id="results-title" className="mt-1 text-xl font-extrabold tracking-tight text-fg">{title}</h2>
          <p className="mt-1 text-xs text-fg-muted">Sealed picks are shown simultaneously for every team.</p>
        </div>
        <StatusPill tone="success">{rounds.length} revealed</StatusPill>
      </div>

      <div className="mb-3 overflow-x-auto pb-1" role="tablist" aria-label="Revealed rounds">
        <div className="flex min-w-max gap-2">
          {[...rounds].reverse().map((round) => {
            const selected = round.round === active?.round;
            return (
              <button
                key={round.round}
                type="button"
                role="tab"
                aria-selected={selected}
                onClick={() => setSelectedRound(round.round)}
                className={`min-h-11 rounded-xl border px-4 text-xs font-black transition ${
                  selected
                    ? "border-accent bg-accent/20 text-accent"
                    : "border-ink-700 bg-ink-850 text-fg-muted hover:border-ink-600 hover:text-fg"
                } ${focusRing}`}
              >
                Round {round.round}
              </button>
            );
          })}
        </div>
      </div>

      {active ? (
        <div className="overflow-hidden rounded-card border border-ink-700 bg-ink-850">
          <div className="flex items-center justify-between border-b border-ink-700 bg-ink-800/50 px-4 py-3">
            <div className="flex items-center gap-2">
              <Trophy size={16} className="text-warn" aria-hidden="true" />
              <h3 className="text-sm font-extrabold text-fg">Round {active.round}</h3>
            </div>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-win">
              <CheckCircle2 size={13} aria-hidden="true" /> Revealed
            </span>
          </div>

          <div className="divide-y divide-ink-700/70">
            {active.results.map((result, index) => {
              const duplicateCount = result.player
                ? duplicateCounts.get(result.player.id) ?? 1
                : 0;
              return (
                <div
                  key={`${result.teamId}-${index}`}
                  className="grid min-h-[76px] grid-cols-[34px_minmax(0,1fr)] items-center gap-2.5 px-3 py-2.5 sm:grid-cols-[minmax(150px,0.7fr)_minmax(240px,1fr)_90px] sm:gap-4 sm:px-4"
                >
                  <div className="col-span-2 flex min-w-0 items-center gap-2.5 sm:col-span-1">
                    <TeamMark name={result.teamName} />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-fg">{result.teamName}</p>
                      <p className="mt-0.5 text-[10px] uppercase tracking-wider text-fg-faint">Team pick</p>
                    </div>
                  </div>

                  {result.player ? (
                    <>
                      <div className="col-span-2 flex min-w-0 items-center gap-2.5 rounded-xl border border-ink-700 bg-ink-800/60 px-2.5 py-2 sm:col-span-1 sm:border-0 sm:bg-transparent sm:p-0">
                        <PlayerAvatar name={result.player.name} src={result.player.headshot} size="sm" />
                        <PositionBadge position={result.player.position} />
                        <div className="min-w-0 flex-1">
                          <div className="flex min-w-0 items-center gap-2">
                            <p className="truncate text-sm font-extrabold text-fg">{result.player.name}</p>
                            {duplicateCount > 1 ? (
                              <span
                                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-accent/10 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider text-accent"
                                title={`${duplicateCount} teams selected this player`}
                              >
                                <Copy size={10} aria-hidden="true" /> {duplicateCount} teams
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-0.5 line-clamp-2 text-[11px] leading-4 text-fg-muted">
                            {result.player.team} <span className="mx-1 text-ink-600">•</span> ADP {result.player.adp != null ? result.player.adp.toFixed(1) : "—"} · {playerStatLine(result.player)}
                          </p>
                        </div>
                        <div className="shrink-0 text-right sm:hidden">
                          <strong className="block text-sm font-black tabular-nums text-accent">
                            {result.player.adp != null ? result.player.adp.toFixed(1) : "—"}
                          </strong>
                          <span className="text-[8px] font-bold uppercase tracking-wider text-fg-faint">ADP</span>
                        </div>
                      </div>
                      <div className="col-span-2 hidden text-right sm:col-span-1 sm:block">
                        <strong className="block text-base font-black tabular-nums text-accent">
                          {result.player.adp != null ? result.player.adp.toFixed(1) : "—"}
                        </strong>
                        <span className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">ADP</span>
                      </div>
                    </>
                  ) : (
                    <div className="col-span-2 flex min-h-12 items-center gap-2.5 rounded-xl border border-dashed border-ink-600 bg-ink-800/50 px-3 text-sm font-bold text-fg-faint sm:col-span-2">
                      <Ban size={16} aria-hidden="true" /> No Pick
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}
