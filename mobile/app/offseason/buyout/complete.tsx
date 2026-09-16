import { useEffect } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { ArrowRight, CircleCheck } from "lucide-react-native";

import { OffseasonNav } from "../../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../../src/components/BottomNav";
import { PlayerHeadshot } from "../../../src/components/PlayerHeadshot";
import { useOffseason } from "../../../src/components/offseason/OffseasonProvider";
import {
  BUYOUT_CANDIDATES,
  BUYOUT_NEXT_STEPS,
  buyoutMath,
} from "../../../src/data/offseason";
import { recordBuyout } from "../../../src/data/offseasonStore";

export default function BuyoutCompleteScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const player = BUYOUT_CANDIDATES.find((p) => p.id === id);
  const { completeStage } = useOffseason();

  // Record the buyout once when the screen mounts.
  useEffect(() => {
    if (player) {
      recordBuyout(player);
      completeStage("buyouts");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [player?.id]);

  if (!player) {
    router.back();
    return null;
  }

  const math = buyoutMath(player);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title="Buyout Complete" close />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Success */}
        <View className="items-center mt-8 px-4">
          <View className="w-20 h-20 rounded-full bg-win/15 border border-win/40 items-center justify-center">
            <CircleCheck color="#22C55E" size={44} />
          </View>
          <Text className="text-fg text-[22px] font-extrabold mt-4">
            Buyout Successful
          </Text>
          <Text className="text-fg-muted text-[13px] mt-1">
            {player.name} has been bought out.
          </Text>
        </View>

        {/* Player card */}
        <View className="mx-4 mt-5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <PlayerHeadshot url={player.headshotUrl} size={44} />
          <View className="flex-1 ml-3">
            <Text className="text-fg text-[14px] font-bold">{player.name}</Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              {player.position} · {player.nhlTeamName}
            </Text>
          </View>
          <View className="w-9 h-9 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-fg text-[9px] font-black">
              {player.nhlTeam}
            </Text>
          </View>
        </View>

        {/* Transaction summary */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          TRANSACTION SUMMARY
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4">
          <SummaryRow label="Cash Payment" value={`$${math.cashCost}`} />
          <SummaryRow
            label="New Cap Hit"
            value={`${math.capHit} units (1 year)`}
          />
          <SummaryRow label="Player Status" value="Released (UFA)" last />
        </View>
      </ScrollView>

      {/* CTAs + next steps */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60">
        <Pressable
          onPress={() => router.dismissTo("/offseason/buyout-teams")}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">
            Back to Buyouts
          </Text>
        </Pressable>

        <View className="mt-4 bg-ink-850 border border-ink-700 rounded-card p-4">
          <View className="flex-row items-center gap-2 mb-2.5">
            <ArrowRight color="#2AB3FF" size={15} />
            <Text className="text-fg text-[13px] font-bold">Next Steps</Text>
          </View>
          {BUYOUT_NEXT_STEPS.map((step) => (
            <View key={step} className="flex-row items-center mb-1.5">
              <CircleCheck color="#22C55E" size={14} />
              <Text className="text-fg-muted text-[12px] ml-2.5">{step}</Text>
            </View>
          ))}
        </View>
      </View>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}

function SummaryRow({
  label,
  value,
  last = false,
}: {
  label: string;
  value: string;
  last?: boolean;
}) {
  return (
    <View
      className={`flex-row items-center justify-between py-3 ${
        last ? "" : "border-b border-ink-700/60"
      }`}
    >
      <Text className="text-fg-muted text-[13px]">{label}</Text>
      <Text className="text-fg text-[13px] font-semibold">{value}</Text>
    </View>
  );
}
