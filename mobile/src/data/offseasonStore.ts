// Tiny in-memory store for the Offseason flow (mock; no backend yet).
import type { BuyoutCandidate } from "./offseason";

let selectedIds: string[] = [];
let boughtOut: BuyoutCandidate[] = [];

export function getSelectedIds() {
  return selectedIds;
}

export function isSelected(id: string) {
  return selectedIds.includes(id);
}

export function toggleSelected(id: string) {
  selectedIds = isSelected(id)
    ? selectedIds.filter((s) => s !== id)
    : [...selectedIds, id];
}

export function clearSelected() {
  selectedIds = [];
}

export function getBoughtOut() {
  return boughtOut;
}

export function recordBuyout(p: BuyoutCandidate) {
  boughtOut = [...boughtOut, p];
  selectedIds = selectedIds.filter((s) => s !== p.id);
}

export function resetOffseason() {
  selectedIds = [];
  boughtOut = [];
}
