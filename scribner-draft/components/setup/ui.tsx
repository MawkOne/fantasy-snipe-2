import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info, Loader2, TriangleAlert } from "lucide-react";
import type { ActionFeedback } from "./types";

export const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ink-900";

export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cx(
        "relative flex shrink-0 items-center justify-center rounded-xl border border-accent/50 bg-ink-800 shadow-[0_0_24px_rgba(42,179,255,0.14)]",
        compact ? "h-10 w-10" : "h-14 w-14",
      )}
      aria-hidden="true"
    >
      <span className={cx("font-black tracking-[-0.08em] text-accent", compact ? "text-xs" : "text-base")}>
        FS
      </span>
      <span className="absolute -bottom-1 -right-1 h-2.5 w-2.5 rounded-full border-2 border-ink-900 bg-win" />
    </div>
  );
}

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return <Loader2 className={cx(className, "animate-spin")} aria-hidden="true" />;
}

export function FeedbackBanner({ feedback }: { feedback: ActionFeedback }) {
  const styles = {
    success: "border-win/35 bg-win/10 text-win",
    error: "border-loss/35 bg-loss/10 text-red-200",
    warning: "border-warn/35 bg-warn/10 text-amber-100",
    info: "border-accent/35 bg-accent/10 text-sky-100",
  }[feedback.tone];
  const Icon = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: TriangleAlert,
    info: Info,
  }[feedback.tone];

  return (
    <div
      className={cx("flex items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm leading-5", styles)}
      role={feedback.tone === "error" ? "alert" : "status"}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{feedback.message}</span>
    </div>
  );
}

export function SectionCard({
  id,
  step,
  title,
  description,
  icon,
  action,
  children,
  className,
}: {
  id: string;
  step: string;
  title: string;
  description: string;
  icon: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      id={id}
      className={cx("scroll-mt-24 overflow-hidden rounded-card border border-ink-700 bg-ink-850", className)}
      aria-labelledby={`${id}-title`}
    >
      <div className="flex flex-col gap-3 border-b border-ink-700/80 px-4 py-4 sm:flex-row sm:items-start sm:justify-between sm:px-5">
        <div className="flex min-w-0 gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-accent/25 bg-accent/10 text-accent">
            {icon}
          </div>
          <div className="min-w-0">
            <div className="mb-0.5 flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">{step}</span>
            </div>
            <h2 id={`${id}-title`} className="text-base font-extrabold tracking-tight text-fg sm:text-lg">
              {title}
            </h2>
            <p className="mt-1 max-w-2xl text-xs leading-5 text-fg-muted sm:text-sm">{description}</p>
          </div>
        </div>
        {action ? <div className="shrink-0 pl-12 sm:pl-0">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function ChangeState({
  dirty,
  status,
}: {
  dirty: boolean;
  status: "idle" | "saving" | "saved" | "error";
}) {
  if (status === "saving") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-fg-muted">
        <Spinner /> Saving
      </span>
    );
  }
  if (dirty) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-warn/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-warn">
        <span className="h-1.5 w-1.5 rounded-full bg-warn" /> Unsaved
      </span>
    );
  }
  if (status === "saved") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-win">
        <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Saved
      </span>
    );
  }
  return null;
}

export function IconButtonLabel({ children }: { children: ReactNode }) {
  return <span className="hidden sm:inline">{children}</span>;
}
