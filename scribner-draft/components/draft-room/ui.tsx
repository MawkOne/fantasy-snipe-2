"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { AlertTriangle, ImageOff, LoaderCircle, X } from "lucide-react";

export const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ink-900";

export function PlayerAvatar({
  name,
  src,
  size = "md",
}: {
  name: string;
  src?: string;
  size?: "sm" | "md" | "lg";
}) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);

  const sizeClass =
    size === "sm" ? "h-10 w-10" : size === "lg" ? "h-16 w-16" : "h-12 w-12";

  return (
    <div
      className={`${sizeClass} relative flex shrink-0 items-center justify-center overflow-hidden rounded-full border border-ink-600 bg-gradient-to-b from-ink-700 to-ink-850`}
      aria-hidden="true"
    >
      {src && !failed ? (
        // Native images are used because player headshots are remote and the CDN is room data.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt=""
          className="h-full w-full object-cover object-top"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="text-xs font-black text-fg-muted">
          {name
            .split(/\s+/)
            .slice(0, 2)
            .map((part) => part[0])
            .join("")
            .toUpperCase() || <ImageOff size={14} />}
        </span>
      )}
    </div>
  );
}

export function TeamMark({ name, highlight = false }: { name: string; highlight?: boolean }) {
  return (
    <div
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-[11px] font-black ${
        highlight
          ? "border-accent/70 bg-accent/20 text-accent"
          : "border-ink-600 bg-ink-800 text-fg-muted"
      }`}
      aria-hidden="true"
    >
      {name
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase() || "T"}
    </div>
  );
}

export function PositionBadge({ position, selected = false }: { position: string; selected?: boolean }) {
  return (
    <span
      className={`flex h-8 min-w-8 shrink-0 items-center justify-center rounded-lg border px-1.5 text-[11px] font-black tracking-wide ${
        selected
          ? "border-accent bg-accent text-ink-950"
          : "border-accent/50 bg-accent/5 text-accent"
      }`}
    >
      {position}
    </span>
  );
}

export function StatusPill({
  tone,
  children,
}: {
  tone: "accent" | "success" | "warning" | "danger" | "neutral";
  children: ReactNode;
}) {
  const tones = {
    accent: "border-accent/30 bg-accent/10 text-accent",
    success: "border-win/30 bg-win/10 text-win",
    warning: "border-warn/30 bg-warn/10 text-warn",
    danger: "border-loss/30 bg-loss/10 text-loss",
    neutral: "border-ink-600 bg-ink-800 text-fg-muted",
  };
  return (
    <span
      className={`inline-flex min-h-6 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function InlineNotice({
  tone = "warning",
  children,
}: {
  tone?: "warning" | "danger" | "info";
  children: ReactNode;
}) {
  const tones = {
    warning: "border-warn/30 bg-warn/10 text-warn",
    danger: "border-loss/30 bg-loss/10 text-loss",
    info: "border-accent/30 bg-accent/10 text-accent",
  };
  return (
    <div className={`flex items-start gap-2.5 rounded-xl border px-3 py-2.5 text-xs ${tones[tone]}`}>
      <AlertTriangle size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 leading-5">{children}</div>
    </div>
  );
}

export function LoadingState({ label = "Loading draft room…" }: { label?: string }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-ink-900 px-5">
      <div className="text-center" role="status" aria-live="polite">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-accent/30 bg-accent/10 shadow-[0_0_40px_rgba(42,179,255,0.12)]">
          <LoaderCircle className="animate-spin text-accent" size={24} aria-hidden="true" />
        </div>
        <p className="mt-4 text-sm font-semibold text-fg-muted">{label}</p>
      </div>
    </main>
  );
}

export function Dialog({
  open,
  title,
  description,
  onClose,
  children,
  labelledBy,
  size = "md",
  closeDisabled = false,
}: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  labelledBy?: string;
  size?: "sm" | "md" | "lg" | "xl";
  closeDisabled?: boolean;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = labelledBy ?? `dialog-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  const sizeClass = {
    sm: "sm:max-w-sm",
    md: "sm:max-w-md",
    lg: "sm:max-w-2xl",
    xl: "sm:max-w-5xl",
  }[size];

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const timer = window.setTimeout(() => {
      const preferred = panelRef.current?.querySelector<HTMLElement>("[data-autofocus]");
      const first = preferred ?? panelRef.current?.querySelector<HTMLElement>(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
      );
      first?.focus();
    }, 0);

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (!closeDisabled) {
          event.preventDefault();
          onClose();
        }
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const focusable = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(
          "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
        ),
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(timer);
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", onKeyDown);
      previous?.focus();
    };
  }, [closeDisabled, onClose, open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-end justify-center bg-ink-950/80 p-0 backdrop-blur-sm sm:items-center sm:p-5">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
        disabled={closeDisabled}
        tabIndex={-1}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? `${titleId}-description` : undefined}
        className={`relative z-10 flex max-h-[94dvh] w-full flex-col rounded-t-[20px] border border-ink-600 bg-ink-850 p-5 shadow-2xl sm:max-h-[calc(100dvh-2.5rem)] sm:rounded-card ${sizeClass}`}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId} className="text-lg font-extrabold tracking-tight text-fg">
              {title}
            </h2>
            {description ? (
              <p id={`${titleId}-description`} className="mt-1.5 text-sm leading-5 text-fg-muted">
                {description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={closeDisabled}
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-ink-600 bg-ink-800 text-fg-muted transition hover:border-ink-500 hover:text-fg disabled:cursor-not-allowed disabled:opacity-40 ${focusRing}`}
            aria-label="Close"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <div className="mt-5 min-h-0 overflow-y-auto overscroll-contain pr-0.5">{children}</div>
      </div>
    </div>
  );
}
