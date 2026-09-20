"use client";

import { useState, type FormEvent } from "react";
import { ArrowRight, EyeOff, Layers3, TimerOff } from "lucide-react";
import type { ActionFeedback } from "./types";
import { BrandMark, FeedbackBanner, Spinner, cx, focusRing } from "./ui";

export function CreateDraftScreen({
  onCreate,
  loading,
  feedback,
}: {
  onCreate: (draftName: string) => Promise<void>;
  loading: boolean;
  feedback?: ActionFeedback;
}) {
  const [draftName, setDraftName] = useState("");
  const [validationError, setValidationError] = useState("");

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = draftName.trim();
    if (!trimmed) {
      setValidationError("Enter a draft name to continue.");
      return;
    }
    if (trimmed.length > 80) {
      setValidationError("Draft name must be 80 characters or fewer.");
      return;
    }
    setValidationError("");
    await onCreate(trimmed);
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-ink-900">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute -left-28 top-[-8rem] h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute bottom-[-14rem] right-[-8rem] h-[30rem] w-[30rem] rounded-full bg-accent/5 blur-3xl" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/60 to-transparent" />
      </div>

      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex items-center gap-3">
          <BrandMark compact />
          <div>
            <p className="text-sm font-black tracking-tight text-fg">FantasySnipe</p>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-fg-faint">Scribner Draft</p>
          </div>
        </header>

        <div className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[1.05fr_.95fr] lg:gap-16 lg:py-14">
          <section className="max-w-xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-accent">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" />
              Private weekend draft rooms
            </div>
            <h1 className="max-w-lg text-4xl font-black leading-[1.04] tracking-[-0.04em] text-fg sm:text-5xl">
              Everyone picks.
              <span className="block text-accent">Nobody peeks.</span>
            </h1>
            <p className="mt-5 max-w-lg text-sm leading-6 text-fg-muted sm:text-base sm:leading-7">
              Run a sealed-round fantasy hockey draft with private team links, configurable rosters, and scoring built for draft weekend.
            </p>

            <div className="mt-7 grid max-w-xl gap-2.5 sm:grid-cols-3">
              {[
                { icon: EyeOff, title: "Sealed picks", copy: "Reveal each round together" },
                { icon: Layers3, title: "Duplicates stay", copy: "Same-round picks are valid" },
                { icon: TimerOff, title: "No timer", copy: "Draft at your own pace" },
              ].map(({ icon: Icon, title, copy }) => (
                <div key={title} className="rounded-xl border border-ink-700 bg-ink-850/80 p-3.5">
                  <Icon className="h-4 w-4 text-accent" aria-hidden="true" />
                  <p className="mt-2.5 text-xs font-bold text-fg">{title}</p>
                  <p className="mt-1 text-[11px] leading-4 text-fg-faint">{copy}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="w-full lg:justify-self-end" aria-labelledby="create-draft-title">
            <div className="overflow-hidden rounded-2xl border border-ink-700 bg-ink-850 shadow-2xl shadow-black/20">
              <div className="border-b border-ink-700 bg-ink-800/60 px-5 py-4 sm:px-6">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">New room</p>
                <h2 id="create-draft-title" className="mt-1 text-xl font-extrabold tracking-tight text-fg">
                  Create your draft
                </h2>
                <p className="mt-1 text-xs leading-5 text-fg-muted">
                  Name it now. Teams, invites, rosters, and scoring come next.
                </p>
              </div>

              <form onSubmit={submit} className="space-y-4 p-5 sm:p-6" noValidate>
                <div>
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <label htmlFor="draft-name" className="text-xs font-bold text-fg">
                      Draft name
                    </label>
                    <span className={cx("text-[10px] tabular-nums", draftName.length > 80 ? "text-loss" : "text-fg-faint")}>
                      {draftName.length}/80
                    </span>
                  </div>
                  <input
                    id="draft-name"
                    value={draftName}
                    onChange={(event) => {
                      setDraftName(event.target.value);
                      if (validationError) setValidationError("");
                    }}
                    placeholder="e.g. UHH 2026 Weekend Draft"
                    maxLength={100}
                    autoComplete="off"
                    autoFocus
                    aria-invalid={Boolean(validationError)}
                    aria-describedby={validationError ? "draft-name-error" : "draft-name-help"}
                    className={cx(
                      "min-h-[48px] w-full rounded-xl border bg-ink-900 px-3.5 text-sm text-fg placeholder:text-fg-faint transition-colors",
                      validationError ? "border-loss/70" : "border-ink-600 hover:border-ink-600/80",
                      focusRing,
                    )}
                  />
                  {validationError ? (
                    <p id="draft-name-error" className="mt-2 text-xs font-medium text-loss" role="alert">
                      {validationError}
                    </p>
                  ) : (
                    <p id="draft-name-help" className="mt-2 text-[11px] leading-4 text-fg-faint">
                      1–80 characters. You can edit this during setup.
                    </p>
                  )}
                </div>

                {feedback ? <FeedbackBanner feedback={feedback} /> : null}

                <button
                  type="submit"
                  disabled={loading}
                  className={cx(
                    "flex min-h-[48px] w-full items-center justify-center gap-2 rounded-full bg-accent px-5 text-sm font-extrabold text-ink-900 transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-60",
                    focusRing,
                  )}
                >
                  {loading ? (
                    <>
                      <Spinner /> Creating draft…
                    </>
                  ) : (
                    <>
                      Create Draft <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </>
                  )}
                </button>
              </form>
            </div>
            <p className="mt-3 text-center text-[11px] leading-4 text-fg-faint">
              Your commissioner session is saved in this browser so you can return to setup.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}

export function RestoringSetup() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-ink-900 p-4">
      <div className="flex flex-col items-center text-center" role="status" aria-live="polite">
        <BrandMark />
        <Spinner className="mt-6 h-5 w-5 text-accent" />
        <p className="mt-3 text-sm font-bold text-fg">Reopening your draft setup</p>
        <p className="mt-1 text-xs text-fg-muted">Restoring the commissioner session from this browser…</p>
      </div>
    </main>
  );
}
