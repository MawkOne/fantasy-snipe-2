import { Info, Minus, Plus, Save, SlidersHorizontal, TriangleAlert } from "lucide-react";
import type { ActionFeedback, RosterRequirements, SaveStatus } from "./types";
import { rosterTarget } from "./setup-utils";
import { ChangeState, FeedbackBanner, SectionCard, Spinner, cx, focusRing } from "./ui";

const POSITIONS: Array<{ key: keyof RosterRequirements; label: string }> = [
  { key: "F", label: "Flex" },
  { key: "C", label: "Centres" },
  { key: "W", label: "Wingers" },
  { key: "D", label: "Defence" },
  { key: "G", label: "Goalies" },
];

export function DraftFormatSection({
  rounds,
  rosterReqs,
  dirty,
  saveStatus,
  feedback,
  onRoundsChange,
  onRosterChange,
  onSave,
}: {
  rounds: number;
  rosterReqs: RosterRequirements;
  dirty: boolean;
  saveStatus: SaveStatus;
  feedback?: ActionFeedback;
  onRoundsChange: (value: number) => void;
  onRosterChange: (position: keyof RosterRequirements, value: number) => void;
  onSave: () => void;
}) {
  const target = rosterTarget(rosterReqs);
  const roundRangeInvalid = !Number.isInteger(rounds) || rounds < 1 || rounds > 30;
  const shortfall = Math.max(0, target - rounds);
  const invalid = roundRangeInvalid || shortfall > 0;

  return (
    <SectionCard
      id="format"
      step="03 · Format"
      title="Draft format & roster target"
      description="One sealed pick per team, per round. Requirements guide roster construction."
      icon={<SlidersHorizontal className="h-4 w-4" aria-hidden="true" />}
      action={<ChangeState dirty={dirty} status={saveStatus} />}
    >
      <div className="grid gap-5 p-4 sm:p-5 md:grid-cols-[190px_minmax(0,1fr)] md:gap-5">
        <div className="rounded-xl border border-ink-700 bg-ink-800/60 p-4">
          <label htmlFor="rounds" className="text-xs font-bold text-fg">Number of rounds</label>
          <p className="mt-1 text-[11px] leading-4 text-fg-faint">1–30 rounds · no countdown clock</p>
          <div className="mt-3 grid grid-cols-[44px_1fr_44px] overflow-hidden rounded-xl border border-ink-600 bg-ink-900">
            <button
              type="button"
              onClick={() => onRoundsChange(Math.max(1, rounds - 1))}
              disabled={rounds <= 1}
              className={cx("flex min-h-[46px] items-center justify-center border-r border-ink-700 text-fg-muted hover:bg-ink-700 hover:text-fg disabled:opacity-30", focusRing)}
              aria-label="Decrease rounds"
            >
              <Minus className="h-4 w-4" aria-hidden="true" />
            </button>
            <input
              id="rounds"
              type="number"
              min={1}
              max={30}
              step={1}
              value={rounds}
              onChange={(event) => onRoundsChange(Number(event.target.value))}
              className={cx("min-w-0 bg-transparent text-center text-lg font-black tabular-nums text-fg [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none", focusRing)}
              aria-invalid={roundRangeInvalid}
            />
            <button
              type="button"
              onClick={() => onRoundsChange(Math.min(30, rounds + 1))}
              disabled={rounds >= 30}
              className={cx("flex min-h-[46px] items-center justify-center border-l border-ink-700 text-fg-muted hover:bg-ink-700 hover:text-fg disabled:opacity-30", focusRing)}
              aria-label="Increase rounds"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {["1 pick / round", "Duplicates allowed", "No timer"].map((rule) => (
              <span key={rule} className="rounded-md bg-ink-700/70 px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-fg-muted">{rule}</span>
            ))}
          </div>
        </div>

        <div>
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h3 className="text-xs font-bold text-fg">Roster requirements</h3>
              <p className="mt-1 text-[11px] leading-4 text-fg-faint">Minimum targets shown to GMs during the draft.</p>
            </div>
            <div className="text-right">
              <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-fg-faint">Roster target</p>
              <p className="mt-0.5 text-lg font-black tabular-nums text-accent">{target} <span className="text-[10px] font-bold uppercase tracking-wider text-fg-faint">players</span></p>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
            {POSITIONS.map(({ key, label }) => (
              <label key={key} htmlFor={`roster-${key}`} className="rounded-xl border border-ink-700 bg-ink-800/60 p-2.5 text-center">
                <span className="block text-lg font-black text-fg">{key}</span>
                <span className="mt-0.5 block text-[9px] font-bold uppercase tracking-wider text-fg-faint">{label}</span>
                <input
                  id={`roster-${key}`}
                  type="number"
                  min={0}
                  step={1}
                  value={rosterReqs[key]}
                  onChange={(event) => onRosterChange(key, Math.max(0, Math.floor(Number(event.target.value) || 0)))}
                  className={cx("mt-2 min-h-[44px] w-full rounded-lg border border-ink-600 bg-ink-900 px-1 text-center text-sm font-bold tabular-nums text-fg", focusRing)}
                />
              </label>
            ))}
          </div>

          <div className="mt-3 flex items-start gap-2 rounded-lg border border-accent/20 bg-accent/5 px-3 py-2.5 text-[11px] leading-4 text-fg-muted">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" aria-hidden="true" />
            <p><strong className="text-fg">F is a flex forward slot</strong> filled by either a centre or winger. Requirements guide picks; they do not silently reject a player.</p>
          </div>
        </div>
      </div>

      {shortfall > 0 ? (
        <div className="mx-4 mb-4 flex items-start gap-2.5 rounded-xl border border-warn/35 bg-warn/10 px-3.5 py-3 text-xs leading-5 text-amber-100 sm:mx-5 sm:mb-5" role="alert">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-warn" aria-hidden="true" />
          <p><strong>Rounds are below the roster target.</strong> Add {shortfall} round{shortfall === 1 ? "" : "s"} or lower the {target}-player target before review.</p>
        </div>
      ) : null}

      {feedback ? <div className="px-4 pb-4 sm:px-5 sm:pb-5"><FeedbackBanner feedback={feedback} /></div> : null}

      <div className="flex items-center justify-between gap-3 border-t border-ink-700/80 bg-ink-800/30 px-4 py-3 sm:px-5">
        <p className={cx("text-[11px]", invalid ? "text-warn" : "text-fg-faint")}>
          {invalid ? "Resolve the format warning to save." : `${rounds} rounds can fill the ${target}-player target.`}
        </p>
        <button
          type="button"
          onClick={onSave}
          disabled={!dirty || saveStatus === "saving" || invalid}
          className={cx("inline-flex min-h-[44px] shrink-0 items-center justify-center gap-2 rounded-lg bg-accent px-4 text-xs font-extrabold text-ink-900 transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-40", focusRing)}
        >
          {saveStatus === "saving" ? <Spinner /> : <Save className="h-3.5 w-3.5" aria-hidden="true" />}
          Save format
        </button>
      </div>
    </SectionCard>
  );
}
