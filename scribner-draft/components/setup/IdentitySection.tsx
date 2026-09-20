import { KeyRound, Save, ShieldCheck } from "lucide-react";
import type { ActionFeedback, SaveStatus } from "./types";
import { ChangeState, FeedbackBanner, SectionCard, Spinner, cx, focusRing } from "./ui";

export function IdentitySection({
  draftName,
  roomId,
  status,
  dirty,
  saveStatus,
  feedback,
  onDraftNameChange,
  onSave,
}: {
  draftName: string;
  roomId: string;
  status: string;
  dirty: boolean;
  saveStatus: SaveStatus;
  feedback?: ActionFeedback;
  onDraftNameChange: (value: string) => void;
  onSave: () => void;
}) {
  const nameInvalid = !draftName.trim() || draftName.trim().length > 80;

  return (
    <SectionCard
      id="identity"
      step="01 · Identity"
      title="Draft identity"
      description="The name is shown to every GM. Your room code stays fixed."
      icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />}
      action={<ChangeState dirty={dirty} status={saveStatus} />}
    >
      <div className="grid gap-4 p-4 sm:p-5 xl:grid-cols-[minmax(0,1fr)_180px]">
        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <label htmlFor="setup-draft-name" className="text-xs font-bold text-fg">Draft name</label>
            <span className={cx("text-[10px] tabular-nums", draftName.length > 80 ? "text-loss" : "text-fg-faint")}>
              {draftName.length}/80
            </span>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              id="setup-draft-name"
              value={draftName}
              onChange={(event) => onDraftNameChange(event.target.value)}
              maxLength={100}
              aria-invalid={nameInvalid}
              className={cx(
                "min-h-[44px] min-w-0 flex-1 rounded-lg border bg-ink-800 px-3 text-sm font-semibold text-fg placeholder:text-fg-faint",
                nameInvalid ? "border-loss/60" : "border-ink-600",
                focusRing,
              )}
            />
            <button
              type="button"
              onClick={onSave}
              disabled={!dirty || saveStatus === "saving" || nameInvalid}
              className={cx(
                "inline-flex min-h-[44px] shrink-0 items-center justify-center gap-2 rounded-lg border border-ink-600 bg-ink-800 px-4 text-xs font-bold text-fg transition hover:border-accent/50 hover:text-accent disabled:cursor-not-allowed disabled:opacity-40",
                focusRing,
              )}
            >
              {saveStatus === "saving" ? <Spinner /> : <Save className="h-3.5 w-3.5" aria-hidden="true" />}
              Save name
            </button>
          </div>
          {nameInvalid ? (
            <p className="mt-2 text-xs text-loss" role="alert">
              {!draftName.trim() ? "Draft name is required." : "Draft name must be 80 characters or fewer."}
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-2 xl:grid-cols-1">
          <div className="rounded-xl border border-ink-700 bg-ink-800/70 px-3 py-2.5">
            <div className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-[0.15em] text-fg-faint">
              <KeyRound className="h-3 w-3" aria-hidden="true" /> Room code
            </div>
            <p className="mt-1.5 truncate font-mono text-sm font-bold tracking-wider text-fg">{roomId}</p>
          </div>
          <div className="rounded-xl border border-win/20 bg-win/5 px-3 py-2.5">
            <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-fg-faint">Draft status</p>
            <div className="mt-1.5 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-win" />
              <p className="text-sm font-bold capitalize text-win">{status === "pending" ? "Setup" : status}</p>
            </div>
          </div>
        </div>
      </div>
      {feedback ? <div className="px-4 pb-4 sm:px-5 sm:pb-5"><FeedbackBanner feedback={feedback} /></div> : null}
    </SectionCard>
  );
}
