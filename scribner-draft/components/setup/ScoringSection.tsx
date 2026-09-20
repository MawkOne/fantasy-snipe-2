import { Check, Save, Zap } from "lucide-react";
import type { ActionFeedback, SaveStatus, ScoringMetric } from "./types";
import { SCORING_GROUPS } from "./setup-utils";
import { ChangeState, FeedbackBanner, SectionCard, Spinner, cx, focusRing } from "./ui";

export function ScoringSection({
  scoring,
  dirty,
  saveStatus,
  feedback,
  onToggle,
  onValueChange,
  onSave,
}: {
  scoring: ScoringMetric[];
  dirty: boolean;
  saveStatus: SaveStatus;
  feedback?: ActionFeedback;
  onToggle: (metricId: string) => void;
  onValueChange: (metricId: string, value: string) => void;
  onSave: () => void;
}) {
  const invalidEnabled = scoring.some(
    (metric) => metric.enabled && (metric.value.trim() === "" || !Number.isFinite(Number(metric.value))),
  );
  const enabledCount = scoring.filter((metric) => metric.enabled).length;

  return (
    <SectionCard
      id="scoring"
      step="04 · Scoring"
      title="Scoring configuration"
      description="Enable the stats that matter and set positive, negative, zero, or decimal values."
      icon={<Zap className="h-4 w-4" aria-hidden="true" />}
      action={<ChangeState dirty={dirty} status={saveStatus} />}
    >
      <div className="grid gap-3 p-4 sm:p-5 lg:grid-cols-2 xl:grid-cols-[1.05fr_.85fr_1.05fr]">
        {SCORING_GROUPS.map((group) => {
          const metrics = scoring.filter((metric) => metric.group === group.id);
          return (
            <div key={group.id} className="overflow-hidden rounded-xl border border-ink-700 bg-ink-800/50">
              <div className="flex items-center justify-between border-b border-ink-700 px-3.5 py-3">
                <div>
                  <h3 className="text-xs font-extrabold text-fg">{group.title}</h3>
                  <p className="mt-0.5 text-[10px] text-fg-faint">{group.description}</p>
                </div>
                <span className="rounded-full bg-ink-700 px-2 py-1 text-[9px] font-bold tabular-nums text-fg-muted">
                  {metrics.filter((metric) => metric.enabled).length}/{metrics.length}
                </span>
              </div>
              <div className="divide-y divide-ink-700/70">
                {metrics.map((metric) => {
                  const invalid = metric.enabled && (metric.value.trim() === "" || !Number.isFinite(Number(metric.value)));
                  return (
                    <div key={metric.id} className={cx("grid min-h-[58px] grid-cols-[44px_minmax(0,1fr)_88px] items-center gap-2 px-2.5 py-2", !metric.enabled && "opacity-55")}>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={metric.enabled}
                        aria-label={`${metric.enabled ? "Disable" : "Enable"} ${metric.label}`}
                        onClick={() => onToggle(metric.id)}
                        className={cx("flex h-11 w-11 items-center justify-center rounded-lg", focusRing)}
                      >
                        <span className={cx("flex h-5 w-5 items-center justify-center rounded-md border-2 transition-colors", metric.enabled ? "border-accent bg-accent text-ink-900" : "border-ink-600 bg-ink-900 text-transparent")}>
                          <Check className="h-3 w-3" strokeWidth={3} aria-hidden="true" />
                        </span>
                      </button>
                      <label htmlFor={`score-${metric.id}`} className="min-w-0 cursor-pointer">
                        <span className="block truncate text-xs font-bold text-fg">{metric.label}</span>
                        <span className="mt-0.5 block font-mono text-[9px] font-bold uppercase tracking-wider text-accent">{metric.code}</span>
                      </label>
                      <div className="relative">
                        <input
                          id={`score-${metric.id}`}
                          type="number"
                          inputMode="decimal"
                          step="any"
                          value={metric.value}
                          disabled={!metric.enabled}
                          onChange={(event) => onValueChange(metric.id, event.target.value)}
                          aria-label={`${metric.label} point value`}
                          aria-invalid={invalid}
                          className={cx("min-h-[40px] w-full rounded-lg border bg-ink-900 py-2 pl-2 pr-6 text-right text-xs font-bold tabular-nums text-fg disabled:cursor-not-allowed", invalid ? "border-loss/70" : "border-ink-600", focusRing)}
                        />
                        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-bold text-fg-faint">pt</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {feedback ? <div className="px-4 pb-4 sm:px-5 sm:pb-5"><FeedbackBanner feedback={feedback} /></div> : null}

      <div className="flex flex-col gap-3 border-t border-ink-700/80 bg-ink-800/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
        <p className="text-[11px] leading-4 text-fg-faint">
          <strong className="text-fg-muted">{enabledCount} metrics enabled.</strong> Disabled metrics contribute zero projected points.
        </p>
        <button
          type="button"
          onClick={onSave}
          disabled={!dirty || saveStatus === "saving" || invalidEnabled}
          className={cx("inline-flex min-h-[44px] items-center justify-center gap-2 rounded-lg bg-accent px-4 text-xs font-extrabold text-ink-900 transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-40", focusRing)}
        >
          {saveStatus === "saving" ? <Spinner /> : <Save className="h-3.5 w-3.5" aria-hidden="true" />}
          Save scoring
        </button>
      </div>
    </SectionCard>
  );
}
