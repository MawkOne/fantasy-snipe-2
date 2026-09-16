// Tiny in-memory store for the Add/Drop flow (mock; no backend yet).
import { useState } from "react";
import type { AvailablePlayer } from "./mock";

let addingPlayer: AvailablePlayer | null = null;
let droppingPlayer: AvailablePlayer | null = null;
let bidAmount: number = 0;

export function setAdding(p: AvailablePlayer | null) {
  addingPlayer = p;
}
export function getAdding() {
  return addingPlayer;
}
export function setDropping(p: AvailablePlayer | null) {
  droppingPlayer = p;
}
export function getDropping() {
  return droppingPlayer;
}
export function setBid(amount: number) {
  bidAmount = amount;
}
export function getBid() {
  return bidAmount;
}
export function clearAddDrop() {
  addingPlayer = null;
  droppingPlayer = null;
  bidAmount = 0;
}

/** Hook to force re-render when navigating back within the flow. */
export function useAddDropVersion() {
  return useState(0)[1];
}