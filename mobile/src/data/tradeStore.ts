// Tiny in-memory store for the Trade flow (mock; no backend yet).
// Shared between the Trade Room, Analysis tab, and Finalize Trade screens.
import type { TradeAsset } from "./mock";
import { ACTIVE_TRADE } from "./mock";

// --- Staged assets (the "Proposed Trade") ---
let youSend: TradeAsset[] = [];
let theySend: TradeAsset[] = [];

// --- Agreement state ---
// The other manager (Jamie) is always "agreed" in the mock once assets exist.
// `mineAgreed` is the signed-in manager's explicit agreement.
let mineAgreed = false;
let theirAgreed = true;

let initialized = false;

function ensureInit() {
  if (initialized) return;
  // Seed with the active trade's committed assets (detail screen does this too).
  youSend = ACTIVE_TRADE.theyReceive;
  theySend = ACTIVE_TRADE.youReceive;
  initialized = true;
}

export function getYouSend(): TradeAsset[] {
  ensureInit();
  return youSend;
}

export function getTheySend(): TradeAsset[] {
  ensureInit();
  return theySend;
}

export function setYouSend(assets: TradeAsset[]) {
  ensureInit();
  youSend = assets;
  mineAgreed = false; // any change resets my agreement
}

export function setTheySend(assets: TradeAsset[]) {
  ensureInit();
  theySend = assets;
  mineAgreed = false;
}

// --- Agreement ---

export function getMineAgreed() {
  ensureInit();
  return mineAgreed;
}

export function getTheirAgreed() {
  ensureInit();
  return theirAgreed;
}

export function setMineAgreed(v: boolean) {
  ensureInit();
  mineAgreed = v;
}

export function setTheirAgreed(v: boolean) {
  ensureInit();
  theirAgreed = v;
}

/** Both managers must agree before the trade can be submitted. */
export function getBothAgreed() {
  ensureInit();
  return mineAgreed && theirAgreed;
}

export function resetTradeFlow() {
  youSend = [];
  theySend = [];
  mineAgreed = false;
  theirAgreed = true;
  initialized = false;
}
