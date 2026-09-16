import type { ComponentType } from "react";
import type { ColorValue } from "react-native";
import {
  Coins,
  Gavel,
  GraduationCap,
  ListOrdered,
  Lock,
  ShieldCheck,
  Star,
} from "lucide-react-native";

import type { OffseasonStepId } from "../../data/offseason";

export type StageIcon = ComponentType<{
  color?: ColorValue;
  size?: number | string;
}>;

/** Icon per offseason stage — used by the tab bar, bottom nav, and stage list. */
export const STAGE_ICONS: Record<OffseasonStepId, StageIcon> = {
  buyouts: Coins,
  rookies: GraduationCap,
  "entry-draft": ListOrdered,
  superstar: Star,
  ufa: Gavel,
  rfa: ShieldCheck,
  finalize: Lock,
};