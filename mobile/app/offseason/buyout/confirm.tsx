import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Check, TriangleAlert } from "lucide-react-native";

import { OffseasonNav } from "../../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../../src/components/BottomNav";
import { PlayerHeadshot } from "../../../src/components/PlayerHeadshot";
import {
  BUYOUT_CANDIDATES,
  BUYOUT_WHATS_NEXT,
  TEAM_CAP,
  buyoutMath,
} from "../../../src/data/offseason";

export default function ConfirmBuyoutScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const player = BUYOUT_CANDIDATES.find((p) => p.id === id);
  const [acknowledged, setAcknowledged] = useState(false);

  if (!player) {
    router.back();
    return null;
  }

  const math = buyoutMath(player);
  const newCap = TEAM_CAP.used + math.capHit;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title="Confirm Buyout" />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Player identity */}
        <View className="flex-row items-center px-4 mt-4">
          <PlayerHeadshot url={player.headshotUrl} size={56} />
          <View className="flex-1 ml-3.5">
            <Text className="text-fg text-[18px] font-extrabold">
              {player.name}
            </Text>
            <Text className="text-fg-muted text-[12px] mt-0.5">
              {player.position} · {player.nhlTeamName}
            </Text>
          </View>
          <View className="w-9 h-9 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-fg text-[9px] font-black">
              {player.nhlTeam}
            </Text>
          </View>
        </View>

        {/* Cash payment */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4 flex-row items-center">
          <Text className="text-loss text-[30px] font-extrabold">
            ${math.cashCost}
          </Text>
          <Text className="text-fg-muted text-[13px] ml-3">
            Cash Payment Due
          </Text>
        </View>

        {/* Warning */}
        <View className="mx-4 mt-3 flex-row items-start bg-loss/10 border border-loss/30 rounded-card p-3.5 gap-2.5">
          <TriangleAlert color="#EF4444" size={16} />
          <Text className="flex-1 text-loss/90 text-[12px] leading-5">
            This payment will be added to your league buyout pool and
            distributed to end-of-season payouts.
          </Text>
        </View>

        {/* Cap impact */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          CAP IMPACT (NEXT SEASON)
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4">
          <ImpactRow label="Current Projected Cap" value={`${TEAM_CAP.used}`} />
          <ImpactRow
            label="Buyout Cap Hit"
            value={`+ ${math.capHit}`}
            valueClass="text-loss"
          />
          <ImpactRow
            label="New Projected Cap"
            value={`${newCap} / ${TEAM_CAP.total}`}
            last
          />
        </View>

        {/* What happens next */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          WHAT HAPPENS NEXT?
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4 gap-3">
          {BUYOUT_WHATS_NEXT(player, math).map((item, i) => (
            <View key={item} className="flex-row items-start">
              <View className="w-5 h-5 rounded-full bg-ink-700 items-center justify-center mr-2.5">
                <Text className="text-fg-muted text-[10px] font-bold">
                  {i + 1}
                </Text>
              </View>
              <Text className="flex-1 text-fg-muted text-[12px] leading-5">
                {item}
              </Text>
            </View>
          ))}
        </View>

        {/* Acknowledgement */}
        <Pressable
          onPress={() => setAcknowledged((v) => !v)}
          className="mx-4 mt-4 flex-row items-center"
        >
          <View
            className={`w-5 h-5 rounded-md border-2 items-center justify-center ${
              acknowledged ? "bg-accent border-accent" : "border-ink-600"
            }`}
          >
            {acknowledged && (
              <Check color="#0A1420" size={12} strokeWidth={3} />
            )}
          </View>
          <Text className="text-fg text-[13px] font-semibold ml-2.5">
            I understand and confirm this buyout
          </Text>
        </Pressable>
      </ScrollView>

      {/* CTAs */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60 gap-2.5">
        <Pressable
          disabled={!acknowledged}
          onPress={() =>
            router.push({
              pathname: "/offseason/buyout/complete",
              params: { id: player.id },
            })
          }
          className={`rounded-full py-3.5 items-center ${
            acknowledged ? "bg-loss" : "bg-ink-700"
          }`}
        >
          <Text
            className={`text-[15px] font-bold ${
              acknowledged ? "text-fg" : "text-fg-faint"
            }`}
          >
            Confirm Buyout
          </Text>
        </Pressable>
        <Pressable
          onPress={() => router.back()}
          className="rounded-full py-3.5 items-center border border-ink-600 bg-ink-850"
        >
          <Text className="text-fg text-[15px] font-bold">Go Back</Text>
        </Pressable>
      </View>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}

function ImpactRow({
  label,
  value,
  valueClass = "text-fg",
  last = false,
}: {
  label: string;
  value: string;
  valueClass?: string;
  last?: boolean;
}) {
  return (
    <View
      className={`flex-row items-center justify-between py-3 ${
        last ? "" : "border-b border-ink-700/60"
      }`}
    >
      <Text className="text-fg-muted text-[13px]">{label}</Text>
      <Text className={`text-[13px] font-bold ${valueClass}`}>{value}</Text>
    </View>
  );
}
