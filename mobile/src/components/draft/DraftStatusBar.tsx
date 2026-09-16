import type { ReactNode } from "react";
import { Text, View } from "react-native";

import { getCurrentOverall, teamForOverall } from "../../data/draftStore";

interface Props {
  /** Optional element rendered at the far right (e.g. close button). */
  right?: ReactNode;
}

/** "Round 1 · Pick 1/12", shown under the header during the draft. */
export function DraftStatusBar({ right }: Props) {
  const { round, pickInRound } = teamForOverall(getCurrentOverall());

  return (
    <View className="flex-row items-center justify-between px-4 py-2.5 border-b border-ink-700/60">
      <Text className="text-fg text-[13px] font-bold">
        Round {round} · <Text className="text-accent">Pick {pickInRound}/12</Text>
      </Text>
      <View className="flex-row items-center gap-3">{right}</View>
    </View>
  );
}