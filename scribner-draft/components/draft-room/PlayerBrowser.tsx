"use client";

import { useMemo, useState, type RefObject } from "react";
import {
  ArrowDownAZ,
  ArrowDownWideNarrow,
  ArrowUpAZ,
  Check,
  Search,
  SlidersHorizontal,
  Users,
} from "lucide-react";
import type { DraftPlayer } from "./types";
import { playerStatLine } from "./state";
import { focusRing, PositionBadge } from "./ui";

const POSITIONS = ["All", "F", "C", "W", "D", "G"] as const;
type PositionFilter = (typeof POSITIONS)[number];
type SortKey = "adp" | "name" | "team" | "position";

const POSITION_ORDER: Record<string, number> = { C: 0, LW: 1, RW: 2, D: 3, G: 4 };

export function PlayerBrowser({
  players,
  selectedId,
  onSelect,
  round,
  searchInputRef,
  readOnly = false,
}: {
  players: DraftPlayer[];
  selectedId: string;
  onSelect?: (player: DraftPlayer) => void;
  round: number;
  searchInputRef: RefObject<HTMLInputElement>;
  readOnly?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<PositionFilter>("All");
  const [sortKey, setSortKey] = useState<SortKey>("adp");
  const [descending, setDescending] = useState(false);

  const filteredPlayers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = players.filter((player) => {
      const playerPosition = player.position.toUpperCase();
      const matchesPosition =
        position === "All" ||
        (position === "F" && ["C", "LW", "RW", "W"].includes(playerPosition)) ||
        (position === "W" && ["LW", "RW", "W"].includes(playerPosition)) ||
        playerPosition === position;
      if (!matchesPosition) return false;
      if (!normalizedQuery) return true;
      return (
        player.name.toLowerCase().includes(normalizedQuery) ||
        player.team.toLowerCase().includes(normalizedQuery) ||
        player.position.toLowerCase().includes(normalizedQuery)
      );
    });

    return [...filtered].sort((a, b) => {
      let comparison = 0;
      if (sortKey === "adp") comparison = (a.adp ?? 999) - (b.adp ?? 999);
      else if (sortKey === "name") comparison = a.name.localeCompare(b.name);
      else if (sortKey === "team") comparison = a.team.localeCompare(b.team);
      else {
        comparison =
          (POSITION_ORDER[a.position.toUpperCase()] ?? 99) -
          (POSITION_ORDER[b.position.toUpperCase()] ?? 99);
        if (comparison === 0) comparison = a.name.localeCompare(b.name);
      }
      return descending ? -comparison : comparison;
    });
  }, [descending, players, position, query, sortKey]);

  const changeSort = (key: SortKey) => {
    setSortKey(key);
    setDescending(key === "adp");
  };

  return (
    <section aria-labelledby="player-browser-title">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                readOnly
                  ? "bg-fg-faint"
                  : "animate-pulse bg-accent shadow-[0_0_12px_rgba(42,179,255,0.8)]"
              }`}
            />
            <p
              className={`text-[10px] font-black uppercase tracking-[0.16em] ${
                readOnly ? "text-fg-faint" : "text-accent"
              }`}
            >
              {readOnly ? `Round ${round} player preview` : `Round ${round} is open`}
            </p>
          </div>
          <h2 id="player-browser-title" className="mt-1.5 text-xl font-extrabold tracking-tight text-fg">
            {readOnly ? "Review available players" : "Select a player"}
          </h2>
          <p className="mt-1 text-xs text-fg-muted">
            {readOnly
              ? `Search, filter, and compare projections before Round ${round} opens.`
              : "Your selection stays private until the commissioner reveals the round."}
          </p>
        </div>
        <div className="hidden text-right sm:block">
          <strong className="block text-lg font-black tabular-nums text-fg">
            {filteredPlayers.length}
          </strong>
          <span className="text-[10px] uppercase tracking-wider text-fg-faint">matching players</span>
        </div>
      </div>

      <div className="rounded-card border border-ink-700 bg-ink-850/90 shadow-[0_18px_50px_rgba(0,0,0,0.16)]">
        <div className="border-b border-ink-700 p-3 sm:p-4">
          <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_210px]">
            <label className="relative block">
              <span className="sr-only">Search available players</span>
              <Search
                size={17}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-fg-faint"
                aria-hidden="true"
              />
              <input
                ref={searchInputRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search player or NHL team"
                className={`h-11 w-full rounded-xl border border-ink-600 bg-ink-800 pl-10 pr-3 text-sm text-fg placeholder:text-fg-faint hover:border-ink-500 ${focusRing}`}
              />
            </label>

            <div className="grid grid-cols-[minmax(0,1fr)_44px] gap-2">
              <label className="relative">
                <span className="sr-only">Sort players</span>
                <SlidersHorizontal
                  size={15}
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-faint"
                  aria-hidden="true"
                />
                <select
                  value={sortKey}
                  onChange={(event) => changeSort(event.target.value as SortKey)}
                  className={`h-11 w-full appearance-none rounded-xl border border-ink-600 bg-ink-800 pl-9 pr-7 text-xs font-bold text-fg ${focusRing}`}
                >
                  <option value="adp">ADP (rank)</option>
                  <option value="name">Player name</option>
                  <option value="team">NHL team</option>
                  <option value="position">Position</option>
                </select>
              </label>
              <button
                type="button"
                onClick={() => setDescending((value) => !value)}
                className={`flex h-11 w-11 items-center justify-center rounded-xl border border-ink-600 bg-ink-800 text-fg-muted transition hover:border-accent/50 hover:text-accent ${focusRing}`}
                aria-label={descending ? "Sort descending; activate for ascending" : "Sort ascending; activate for descending"}
              >
                {sortKey === "adp" ? (
                  <ArrowDownWideNarrow size={17} className={descending ? "" : "rotate-180"} aria-hidden="true" />
                ) : descending ? (
                  <ArrowDownAZ size={17} aria-hidden="true" />
                ) : (
                  <ArrowUpAZ size={17} aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-6 gap-1.5" aria-label="Filter by position">
            {POSITIONS.map((item) => {
              const active = item === position;
              return (
                <button
                  key={item}
                  type="button"
                  onClick={() => setPosition(item)}
                  aria-pressed={active}
                  className={`min-h-11 rounded-lg border px-1 text-xs font-black transition ${
                    active
                      ? "border-accent bg-accent/20 text-accent"
                      : "border-ink-700 bg-ink-800 text-fg-muted hover:border-ink-600 hover:text-fg"
                  } ${focusRing}`}
                >
                  {item}
                </button>
              );
            })}
          </div>
        </div>

        <div className="hidden grid-cols-[46px_44px_minmax(160px,1fr)_minmax(200px,1.2fr)_80px_34px] items-center gap-3 border-b border-ink-700/80 bg-ink-800/50 px-4 py-2 text-[10px] font-black uppercase tracking-[0.12em] text-fg-faint md:grid">
          <span>ADP</span>
          <span>Pos</span>
          <span>Player</span>
          <span>Write-up</span>
          <span className="text-right">ADP</span>
          <span />
        </div>

        <div className="divide-y divide-ink-700/70">
          {filteredPlayers.map((player, index) => {
            const selected = selectedId === player.id;
            return (
              <button
                key={player.id}
                type="button"
                onClick={() => {
                  if (!readOnly) onSelect?.(player);
                }}
                disabled={readOnly}
                aria-pressed={readOnly ? undefined : selected}
                className={`group grid min-h-[72px] w-full grid-cols-[38px_minmax(0,1fr)_66px_24px] items-center gap-2.5 px-3 py-2.5 text-left transition md:grid-cols-[46px_44px_minmax(160px,1fr)_minmax(200px,1.2fr)_80px_34px] md:gap-3 md:px-4 ${
                  selected
                    ? "bg-accent/10 shadow-[inset_3px_0_0_#2AB3FF]"
                    : readOnly
                      ? "cursor-default"
                      : "hover:bg-ink-800/80"
                } ${readOnly ? "" : focusRing}`}
              >
                <span className="hidden text-xs font-bold tabular-nums text-fg-faint md:block">
                  {player.adp != null ? player.adp.toFixed(1) : `#${player.rank ?? index + 1}`}
                </span>
                <div className="hidden md:block">
                  <PositionBadge position={player.position} selected={selected} />
                </div>
                <div className="col-span-2 flex min-w-0 items-center gap-2.5 md:col-span-1">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-bold text-fg group-hover:text-white">
                        {player.name}
                      </span>
                      <span className="md:hidden">
                        <PositionBadge position={player.position} selected={selected} />
                      </span>
                    </div>
                    <div className="mt-0.5 flex items-center gap-1.5 text-[11px] text-fg-muted">
                      <span className="font-bold text-fg-muted">{player.team}</span>
                      <span className="text-ink-600">•</span>
                      <span className="truncate md:hidden">ADP {player.adp != null ? player.adp.toFixed(1) : "—"}</span>
                      <span className="hidden md:inline">{player.position}</span>
                    </div>
                  </div>
                </div>
                <div className="hidden min-w-0 md:block">
                  <p className="line-clamp-3 text-xs leading-5 text-fg-muted">{playerStatLine(player)}</p>
                </div>
                <div className="text-right">
                  <strong className="block text-base font-black tabular-nums text-accent">
                    {player.adp != null ? player.adp.toFixed(1) : "—"}
                  </strong>
                  <span className="text-[9px] font-bold uppercase tracking-wider text-fg-faint">ADP</span>
                </div>
                {readOnly ? (
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded-full border border-ink-600 text-[9px] font-black text-fg-faint"
                    aria-hidden="true"
                  >
                    i
                  </span>
                ) : (
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full border-2 transition ${
                      selected
                        ? "border-accent bg-accent text-ink-950"
                        : "border-ink-500 text-transparent group-hover:border-accent/60"
                    }`}
                    aria-hidden="true"
                  >
                    <Check size={12} strokeWidth={3} />
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {filteredPlayers.length === 0 ? (
          <div className="flex flex-col items-center px-5 py-14 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full border border-ink-600 bg-ink-800 text-fg-faint">
              <Users size={20} aria-hidden="true" />
            </div>
            <h3 className="mt-3 text-sm font-bold text-fg">No matching players</h3>
            <p className="mt-1 max-w-xs text-xs leading-5 text-fg-muted">
              Try a different name, NHL team, position, or sort option.
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
