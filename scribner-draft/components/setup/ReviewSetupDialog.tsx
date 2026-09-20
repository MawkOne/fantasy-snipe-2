"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  LockKeyhole,
  Rocket,
  ShieldAlert,
  Users,
  X,
} from "lucide-react";
import type { ActionFeedback, DraftSetup, ScoringGroup } from "./types";
import { rosterTarget, SCORING_GROUPS } from "./setup-utils";
import { FeedbackBanner, Spinner, cx, focusRing } from "./ui";

export function ReviewSetupDialog({
  open,
  setup,
  unsavedCount,
  starting,
  startFeedback,
  onClose,
  onStart,
}: {
  open: boolean;
  setup: DraftSetup;
  unsavedCount: number;
  starting: boolean;
  startFeedback?: ActionFeedback;
  onClose: () => void;
  onStart: () => void;
}) {
  const [stage, setStage] = useState<"review" | "confirm">("review");
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const startingRef = useRef(starting);
  startingRef.current = starting;

  useEffect(() => {
    if (!open) return;
    setStage("review");
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.setTimeout(() => closeButtonRef.current?.focus(), 0);

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !startingRef.current) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = priorOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  const adminTeam = setup.teams.find((team) => team.isAdminTeam);
  const joinedCount = setup.teams.filter((team) => team.inviteState === "joined").length;
  const sentCount = setup.teams.filter((team) => team.inviteState === "sent").length;
  const unsentCount = setup.teams.filter((team) => team.inviteState === "not-sent").length;
  const enabledScoring = setup.scoring.filter((metric) => metric.enabled);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 p-0 backdrop-blur-sm sm:items-center sm:p-5">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        onClick={() => !starting && onClose()}
        aria-label="Close review"
        tabIndex={-1}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-title"
        className="relative flex max-h-[94vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-2xl border border-ink-700 bg-ink-900 shadow-2xl shadow-black/50 sm:max-h-[88vh] sm:rounded-2xl"
      >
        <header className="flex items-start justify-between gap-4 border-b border-ink-700 bg-ink-850 px-4 py-4 sm:px-6">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">
              {stage === "review" ? "Step 1 of 2 · Review" : "Step 2 of 2 · Confirm"}
            </p>
            <h2 id="review-title" className="mt-1 text-xl font-black tracking-tight text-fg sm:text-2xl">
              {stage === "review" ? "Review draft setup" : "Ready to start the draft?"}
            </h2>
            <p className="mt-1 text-xs leading-5 text-fg-muted">
              {stage === "review"
                ? "Check every team, roster target, and scoring value before locking setup."
                : "This is the final confirmation. The draft room opens after the server accepts setup."}
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            disabled={starting}
            className={cx("flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-ink-600 text-fg-muted hover:bg-ink-700 hover:text-fg disabled:opacity-40", focusRing)}
            aria-label="Close review"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </header>

        <div className="overflow-y-auto overscroll-contain">
          {stage === "review" ? (
            <div className="space-y-4 p-4 sm:p-6">
              {unsavedCount > 0 ? (
                <div className="flex items-start gap-2.5 rounded-xl border border-warn/30 bg-warn/10 px-3.5 py-3 text-xs leading-5 text-amber-100">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warn" aria-hidden="true" />
                  <p><strong>{unsavedCount} section{unsavedCount === 1 ? " has" : "s have"} unsaved changes.</strong> Valid changes will be saved automatically before Start Draft is sent.</p>
                </div>
              ) : null}

              <div className="grid gap-3 md:grid-cols-3">
                <SummaryStat label="Draft name" value={setup.draftName} subvalue={`Room ${setup.roomId}`} />
                <SummaryStat label="Teams" value={`${setup.teams.length} configured`} subvalue={adminTeam ? `${adminTeam.name} is My team` : "My team missing"} />
                <SummaryStat label="Format" value={`${setup.rounds} rounds`} subvalue={`${rosterTarget(setup.rosterReqs)}-player roster target`} />
              </div>

              <section className="overflow-hidden rounded-xl border border-ink-700 bg-ink-850" aria-labelledby="review-teams-title">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink-700 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-accent" aria-hidden="true" />
                    <h3 id="review-teams-title" className="text-sm font-extrabold text-fg">Teams & invitations</h3>
                  </div>
                  <div className="flex flex-wrap gap-1.5 text-[9px] font-bold uppercase tracking-wider">
                    <span className="rounded-full bg-win/10 px-2 py-1 text-win">{joinedCount} joined</span>
                    <span className="rounded-full bg-accent/10 px-2 py-1 text-accent">{sentCount} sent</span>
                    {unsentCount ? <span className="rounded-full bg-warn/10 px-2 py-1 text-warn">{unsentCount} not sent</span> : null}
                  </div>
                </div>
                <ul className="divide-y divide-ink-700/70">
                  {setup.teams.map((team) => (
                    <li key={team.id} className="grid gap-1 px-4 py-3 sm:grid-cols-[1fr_1fr_auto] sm:items-center sm:gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-xs font-bold text-fg">{team.name}</p>
                        {team.isAdminTeam ? <span className="mt-1 inline-flex rounded-full bg-accent/10 px-2 py-0.5 text-[8px] font-bold uppercase tracking-wider text-accent">My team</span> : null}
                      </div>
                      <p className="truncate text-[11px] text-fg-muted">{team.ownerEmail || "No email · share private link"}</p>
                      <span className={cx("text-[10px] font-bold capitalize", team.inviteState === "joined" ? "text-win" : team.inviteState === "sent" ? "text-accent" : "text-warn")}>
                        {team.inviteState.replace("-", " ")}
                      </span>
                    </li>
                  ))}
                </ul>
                {unsentCount > 0 ? (
                  <p className="border-t border-warn/20 bg-warn/5 px-4 py-2.5 text-[11px] leading-4 text-warn">
                    {unsentCount} owner{unsentCount === 1 ? " has" : "s have"} not been sent an invite. You can still copy their private links before starting.
                  </p>
                ) : null}
              </section>

              <div className="grid gap-3 lg:grid-cols-[.8fr_1.2fr]">
                <section className="rounded-xl border border-ink-700 bg-ink-850 p-4" aria-labelledby="review-roster-title">
                  <h3 id="review-roster-title" className="text-sm font-extrabold text-fg">Roster requirements</h3>
                  <div className="mt-3 grid grid-cols-5 gap-1.5">
                    {(Object.entries(setup.rosterReqs) as Array<[keyof typeof setup.rosterReqs, number]>).map(([position, value]) => (
                      <div key={position} className="rounded-lg border border-ink-700 bg-ink-800 px-1 py-2 text-center">
                        <p className="text-[9px] font-bold text-fg-faint">{position}</p>
                        <p className="mt-1 text-base font-black tabular-nums text-fg">{value}</p>
                      </div>
                    ))}
                  </div>
                  <p className="mt-3 text-[10px] leading-4 text-fg-faint">F is a flex slot filled by a centre or winger.</p>
                </section>

                <section className="rounded-xl border border-ink-700 bg-ink-850 p-4" aria-labelledby="review-scoring-title">
                  <div className="flex items-center justify-between gap-3">
                    <h3 id="review-scoring-title" className="text-sm font-extrabold text-fg">Enabled scoring</h3>
                    <span className="text-[10px] font-bold text-accent">{enabledScoring.length} metrics</span>
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-3">
                    {SCORING_GROUPS.map((group) => (
                      <ReviewScoringGroup
                        key={group.id}
                        title={group.title}
                        group={group.id}
                        metrics={enabledScoring}
                      />
                    ))}
                  </div>
                </section>
              </div>
            </div>
          ) : (
            <div className="p-4 sm:p-6">
              <div className="mx-auto max-w-2xl">
                <div className="flex flex-col items-center text-center">
                  <span className="flex h-14 w-14 items-center justify-center rounded-full border border-accent/35 bg-accent/10 text-accent">
                    <LockKeyhole className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <h3 className="mt-4 text-lg font-black text-fg">Setup will be locked</h3>
                  <p className="mt-2 max-w-lg text-sm leading-6 text-fg-muted">
                    Starting <strong className="text-fg">{setup.draftName}</strong> locks team structure and scoring for this MVP draft. Review changes require a future draft room.
                  </p>
                </div>

                <div className="mt-5 grid gap-2 sm:grid-cols-3">
                  {[
                    `${setup.teams.length} teams`,
                    `${setup.rounds} rounds`,
                    `${enabledScoring.length} scoring metrics`,
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-2 rounded-xl border border-ink-700 bg-ink-850 px-3 py-3 text-xs font-bold text-fg">
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-win" aria-hidden="true" /> {item}
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex items-start gap-2.5 rounded-xl border border-warn/35 bg-warn/10 px-4 py-3 text-xs leading-5 text-amber-100">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warn" aria-hidden="true" />
                  <p>Only continue when owners and scoring are final. The draft does not start until server-side validation succeeds.</p>
                </div>

                {startFeedback ? <div className="mt-4"><FeedbackBanner feedback={startFeedback} /></div> : null}
              </div>
            </div>
          )}
        </div>

        <footer className="mt-auto flex flex-col-reverse gap-2 border-t border-ink-700 bg-ink-850 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          {stage === "review" ? (
            <button
              type="button"
              onClick={onClose}
              className={cx("min-h-[44px] rounded-lg px-4 text-xs font-bold text-fg-muted hover:text-fg", focusRing)}
            >
              Back to setup
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setStage("review")}
              disabled={starting}
              className={cx("inline-flex min-h-[44px] items-center justify-center gap-2 rounded-lg px-4 text-xs font-bold text-fg-muted hover:text-fg disabled:opacity-40", focusRing)}
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Review again
            </button>
          )}

          {stage === "review" ? (
            <button
              type="button"
              onClick={() => setStage("confirm")}
              className={cx("inline-flex min-h-[46px] items-center justify-center gap-2 rounded-full bg-accent px-5 text-xs font-extrabold text-ink-900 hover:bg-accent-bright", focusRing)}
            >
              Continue to confirmation <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : (
            <button
              type="button"
              onClick={onStart}
              disabled={starting}
              className={cx("inline-flex min-h-[46px] items-center justify-center gap-2 rounded-full bg-win px-6 text-xs font-extrabold text-ink-900 hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60", focusRing)}
            >
              {starting ? <><Spinner /> Saving & starting…</> : <><Rocket className="h-4 w-4" aria-hidden="true" /> Start Draft</>}
            </button>
          )}
        </footer>
      </div>
    </div>
  );
}

function SummaryStat({ label, value, subvalue }: { label: string; value: string; subvalue: string }) {
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-850 p-3.5">
      <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-fg-faint">{label}</p>
      <p className="mt-1.5 truncate text-sm font-extrabold text-fg">{value}</p>
      <p className="mt-1 truncate text-[10px] text-fg-muted">{subvalue}</p>
    </div>
  );
}

function ReviewScoringGroup({
  title,
  group,
  metrics,
}: {
  title: string;
  group: ScoringGroup;
  metrics: DraftSetup["scoring"];
}) {
  const groupMetrics = metrics.filter((metric) => metric.group === group);
  return (
    <div>
      <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-fg-faint">{title}</p>
      <div className="mt-1.5 space-y-1">
        {groupMetrics.length ? groupMetrics.map((metric) => (
          <div key={metric.id} className="flex items-center justify-between gap-2 text-[10px]">
            <span className="font-mono font-bold text-fg-muted">{metric.code}</span>
            <span className="font-bold tabular-nums text-fg">{Number(metric.value)} pt</span>
          </div>
        )) : <p className="text-[10px] text-fg-faint">None enabled</p>}
      </div>
    </div>
  );
}
