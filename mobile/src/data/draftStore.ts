// Tiny in-memory store for the Rookie Draft flow (mock; no backend yet).
import { useState } from "react";
import {
  DRAFT_META,
  DRAFT_ORDER,
  MY_DRAFT_TEAM_ID,
  type DraftPick,
  type DraftTeam,
  type RookiePlayer,
} from "./rookieDraft";

const TEAM_COUNT = DRAFT_ORDER.length;

let picks: DraftPick[] = [];

export function getPicks() {
  return picks;
}

export function getCurrentOverall() {
  return picks.length + 1;
}

export function getTotalPicks() {
  return DRAFT_META.rounds * TEAM_COUNT;
}

/** Snake order: odd rounds follow DRAFT_ORDER, even rounds reverse it. */
export function teamForOverall(overall: number): {
  overall: number;
  round: number;
  pickInRound: number;
  team: DraftTeam;
} {
  const round = Math.ceil(overall / TEAM_COUNT);
  const pickInRound = ((overall - 1) % TEAM_COUNT) + 1;
  const index = round % 2 === 1 ? pickInRound - 1 : TEAM_COUNT - pickInRound;
  return { overall, round, pickInRound, team: DRAFT_ORDER[index] };
}

export function isMyPick() {
  return teamForOverall(getCurrentOverall()).team.id === MY_DRAFT_TEAM_ID;
}

export function getUpcoming(count: number) {
  const start = getCurrentOverall() + 1;
  return Array.from({ length: count }, (_, i) => teamForOverall(start + i));
}

export function makePick(player: RookiePlayer) {
  const slot = teamForOverall(getCurrentOverall());
  const pick: DraftPick = { ...slot, player };
  picks = [...picks, pick];
  return pick;
}

export function getLastPick() {
  return picks.length > 0 ? picks[picks.length - 1] : null;
}

export function isPlayerDrafted(id: string) {
  return picks.some((p) => p.player.id === id);
}

export function resetDraft() {
  picks = [];
}

/** Hook to force re-render when navigating back within the flow. */
export function useDraftVersion() {
  return useState(0)[1];
}
