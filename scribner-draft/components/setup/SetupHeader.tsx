import { Check, ClipboardCheck } from "lucide-react";
import { BrandMark, cx, focusRing } from "./ui";

export function SetupHeader({
  draftName,
  roomId,
  copied,
  onCopyRoomCode,
}: {
  draftName: string;
  roomId: string;
  copied: boolean;
  onCopyRoomCode: () => void;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-700/80 bg-ink-900/95 backdrop-blur-xl">
      <div className="mx-auto flex min-h-[68px] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <BrandMark compact />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="truncate text-sm font-extrabold tracking-tight text-fg sm:text-base">{draftName || "Untitled draft"}</p>
              <span className="hidden rounded-full border border-win/30 bg-win/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.16em] text-win sm:inline-flex">
                Setup
              </span>
            </div>
            <button
              type="button"
              onClick={onCopyRoomCode}
              className={cx(
                "group -ml-1 mt-0.5 inline-flex min-h-[24px] items-center gap-1.5 rounded px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-fg-faint hover:text-accent",
                focusRing,
              )}
              aria-label={`Copy room code ${roomId}`}
            >
              Room <span className="font-mono text-fg-muted">{roomId}</span>
              {copied ? <Check className="h-3 w-3 text-win" /> : <ClipboardCheck className="h-3 w-3" />}
            </button>
          </div>
        </div>

        <ol className="hidden items-center text-[10px] font-bold uppercase tracking-[0.14em] text-fg-faint md:flex" aria-label="Draft setup progress">
          <li className="flex items-center gap-2 text-win">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-win/15">
              <Check className="h-3 w-3" aria-hidden="true" />
            </span>
            Create
          </li>
          <li className="mx-3 h-px w-8 bg-accent/50" aria-hidden="true" />
          <li className="flex items-center gap-2 text-accent" aria-current="step">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[9px] text-ink-900">2</span>
            Configure
          </li>
          <li className="mx-3 h-px w-8 bg-ink-700" aria-hidden="true" />
          <li className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ink-700 text-[9px]">3</span>
            Review
          </li>
        </ol>

        <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-win/30 bg-win/10 px-2.5 py-1.5 sm:hidden">
          <span className="h-1.5 w-1.5 rounded-full bg-win" />
          <span className="text-[9px] font-bold uppercase tracking-[0.14em] text-win">Setup</span>
        </div>
      </div>
    </header>
  );
}
