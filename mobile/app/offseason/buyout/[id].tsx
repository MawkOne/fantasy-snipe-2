import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Info } from "lucide-react-native";

import { OffseasonNav } from "../../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../../src/components/BottomNav";
import { PlayerHeadshot } from "../../../src/components/PlayerHeadshot";
import { BUYOUT_CANDIDATES, buyoutMath } from "../../../src/data/offseason";

export default function BuyoutDetailsScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const player = BUYOUT_CANDIDATES.find((p) => p.id === id);

  if (!player) {
    router.back();
    return null;
  }

  const math = buyoutMath(player);
  const totalRemaining = player.salary * player.yearsRemaining;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title="Buyout Details" />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Player identity */}
        <View className="flex-row items-center px-4 mt-4">
          <PlayerHeadshot url={player.headshotUrl} size={64} />
          <View className="flex-1 ml-3.5">
            <Text className="text-fg text-[20px] font-extrabold">
              {player.name}
            </Text>
            <Text className="text-fg-muted text-[13px] mt-0.5">
              {player.position} · {player.nhlTeamName}
            </Text>
          </View>
          <View className="w-9 h-9 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-fg text-[9px] font-black">
              {player.nhlTeam}
            </Text>
          </View>
        </View>

        {/* Current contract */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          CURRENT CONTRACT
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4">
          <DetailRow label="Annual Salary" value={`${player.salary} units`} />
          <DetailRow
            label="Years Remaining"
            value={`${player.yearsRemaining} years`}
          />
          <DetailRow
            label="Total Remaining"
            value={`${totalRemaining} units`}
          />
          <DetailRow label="Contract Type" value={player.contractType} last />
        </View>

        {/* Buyout calculation */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          BUYOUT CALCULATION
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4">
          <View className="flex-row items-center justify-between">
            <Text className="text-fg-muted text-[13px]">Cash Cost</Text>
            <Text className="text-loss text-[22px] font-extrabold">
              ${math.cashCost}
            </Text>
          </View>
          <View className="flex-row items-center justify-between mt-1">
            <Text className="text-fg text-[13px] font-semibold">
              ${player.salary} × {player.yearsRemaining} = ${math.cashCost}
            </Text>
            <Text className="text-fg-faint text-[11px]">(real money)</Text>
          </View>

          <View className="h-px bg-ink-700/60 my-3.5" />

          <Text className="text-fg-muted text-[13px]">New Cap Hit</Text>
          <Text className="text-fg text-[13px] font-semibold mt-1">
            ${player.salary} ÷ 2 = ${math.capHit}{" "}
            <Text className="text-loss font-bold">→ {math.capHit} units</Text>
          </Text>
          <Text className="text-fg-faint text-[11px] mt-1">
            for 1 year (next season)
          </Text>
        </View>

        {/* Info note */}
        <View className="mx-4 mt-3 flex-row items-start bg-ink-850 border border-ink-700 rounded-card p-3.5 gap-2.5">
          <Info color="#2AB3FF" size={16} />
          <Text className="flex-1 text-fg-muted text-[12px] leading-5">
            After a buyout, the player is immediately released and becomes a
            free agent. The new cap hit will apply to your team next season.
          </Text>
        </View>
      </ScrollView>

      {/* CTAs */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60 gap-2.5">
        <Pressable
          onPress={() =>
            router.push({
              pathname: "/offseason/buyout/confirm",
              params: { id: player.id },
            })
          }
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">
            Confirm Buyout
          </Text>
        </Pressable>
        <Pressable
          onPress={() => router.back()}
          className="rounded-full py-3.5 items-center border border-ink-600 bg-ink-850"
        >
          <Text className="text-fg text-[15px] font-bold">Cancel</Text>
        </Pressable>
      </View>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}

function DetailRow({
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
