import Link from "next/link";
import { ArrowRight, CheckCircle2, Home, Link2, ShieldCheck } from "lucide-react";

export default function LeftRoomPage({
  searchParams,
}: {
  searchParams: { room?: string; team?: string };
}) {
  const roomId = typeof searchParams.room === "string" ? searchParams.room : "";
  const teamName = typeof searchParams.team === "string" ? searchParams.team : "Your team";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-ink-900 px-4 py-10 text-fg">
      <div className="pointer-events-none absolute -top-40 h-96 w-96 rounded-full bg-accent/10 blur-[110px]" aria-hidden="true" />
      <section className="relative w-full max-w-lg overflow-hidden rounded-card border border-ink-700 bg-ink-850 p-6 text-center shadow-2xl sm:p-8">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-win/30 bg-win/10 text-win">
          <CheckCircle2 size={28} aria-hidden="true" />
        </div>
        <p className="mt-5 text-[10px] font-black uppercase tracking-[0.16em] text-accent">Room left safely</p>
        <h1 className="mt-2 text-2xl font-black tracking-tight text-fg">You can come back anytime</h1>
        <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-fg-muted">
          {teamName} is still assigned to you. Your picks and draft progress remain on the server—leaving did not remove or reset anything.
        </p>

        <div className="mt-6 rounded-xl border border-accent/25 bg-accent/5 p-4 text-left">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
              <Link2 size={17} aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-fg">Re-enter with your invite</h2>
              <p className="mt-1 text-xs leading-5 text-fg-muted">
                Reopen the private invite link on any device. On this device, your team token is remembered, so you can also return directly to the room.
              </p>
            </div>
          </div>
        </div>

        <div className={`mt-6 grid gap-2 ${roomId ? "sm:grid-cols-2" : ""}`}>
          <Link
            href="/"
            className="flex min-h-12 items-center justify-center gap-2 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg-muted transition hover:border-ink-500 hover:text-fg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ink-900"
          >
            <Home size={16} aria-hidden="true" /> Home
          </Link>
          {roomId ? (
            <Link
              href={`/room/${encodeURIComponent(roomId)}`}
              className="flex min-h-12 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 transition hover:bg-accent-bright focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-ink-900"
            >
              Return to Room <ArrowRight size={16} aria-hidden="true" />
            </Link>
          ) : null}
        </div>

        <div className="mt-5 flex items-center justify-center gap-1.5 text-[10px] font-semibold text-fg-faint">
          <ShieldCheck size={13} aria-hidden="true" /> Your private team assignment stays saved.
        </div>
      </section>
    </main>
  );
}
