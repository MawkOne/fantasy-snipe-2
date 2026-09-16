import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  ChevronLeft,
  Lightbulb,
  TrendingDown,
  TrendingUp,
  UserPlus,
  UserMinus,
} from "lucide-react-native";

import { getAdding, getDropping, getBid } from "../../src/data/addDropStore";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";

export default function ReviewAddDropScreen() {
  const router = useRouter();
  const adding = getAdding();
  const dropping = getDropping();
  const bid = getBid();

  if (!adding) {
    router.back();
    return null;
  }

  const projDelta = dropping
    ? adding.projectedPoints - dropping.projectedPoints
    : adding.projectedPoints;
  const gain = projDelta >= 0;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="flex-row items-center px-4 py-3 border-b border-ink-700/60">
        <Pressable onPress={() => router.back()} className="mr-3 p-1 -ml-1">
          <ChevronLeft color="#F2F7FC" size={24} />
        </Pressable>
        <Text className="text-fg text-lg font-extrabold">
          {dropping ? "Review Add / Drop" : "Review Add"}
        </Text>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Adding */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center gap-1.5 mb-2.5">
            <UserPlus color="#22C55E" size={14} />
            <Text className="text-win text-[12px] font-bold tracking-wide">
              Adding
            </Text>
          </View>
          <View className="flex-row items-center">
            <PlayerHeadshot url={adding.headshotUrl} size={44} />
            <View className="flex-1 ml-3">
              <Text className="text-fg text-[15px] font-semibold">
                {adding.name}
              </Text>
              <Text className="text-fg-muted text-xs mt-0.5">
                {adding.team} · {adding.position}
              </Text>
              <Text className="text-fg-faint text-[11px] mt-1">
                {adding.projectedPoints.toFixed(1)} proj · {adding.rosteredPct}% rostered
              </Text>
            </View>
            <View className="w-6 h-6 rounded-full bg-win items-center justify-center">
              <Text className="text-ink-900 text-sm font-black">+</Text>
            </View>
          </View>
        </View>

        {/* Dropping — only if a player was selected */}
        {dropping && (
          <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
            <View className="flex-row items-center gap-1.5 mb-2.5">
              <UserMinus color="#EF4444" size={14} />
              <Text className="text-loss text-[12px] font-bold tracking-wide">
                Dropping
              </Text>
            </View>
            <View className="flex-row items-center">
              <PlayerHeadshot url={dropping.headshotUrl} size={44} />
              <View className="flex-1 ml-3">
                <Text className="text-fg text-[15px] font-semibold">
                  {dropping.name}
                </Text>
                <Text className="text-fg-muted text-xs mt-0.5">
                  {dropping.team} · {dropping.position}
                </Text>
                <Text className="text-fg-faint text-[11px] mt-1">
                  {dropping.projectedPoints.toFixed(1)} proj
                </Text>
              </View>
              <View className="w-6 h-6 rounded-full bg-loss items-center justify-center">
                <Text className="text-ink-900 text-sm font-black">−</Text>
              </View>
            </View>
          </View>
        )}

        {/* Impact */}
        <Text className="text-fg-faint text-[11px] font-bold tracking-widest px-4 pt-5 pb-2">
          IMPACT ON YOUR ROSTER
        </Text>
        <View className="flex-row mx-4 gap-3">
          <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5 items-center">
            <View className="flex-row items-center gap-1">
              <TrendingUp color="#22C55E" size={14} />
              <Text className="text-win text-xl font-extrabold">
                +{adding.projectedPoints.toFixed(1)}
              </Text>
            </View>
            <Text className="text-fg-muted text-[11px] mt-1 text-center">
              Projected points{"\n"}(this week)
            </Text>
          </View>
          {dropping && (
            <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5 items-center">
              <View className="flex-row items-center gap-1">
                <TrendingDown color="#EF4444" size={14} />
                <Text className="text-loss text-xl font-extrabold">
                  −{dropping.projectedPoints.toFixed(1)}
                </Text>
              </View>
              <Text className="text-fg-muted text-[11px] mt-1 text-center">
                Projected points{"\n"}(this week)
              </Text>
            </View>
          )}
        </View>

        {/* Bid summary */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center justify-between">
          <Text className="text-fg-muted text-[12px]">Waiver bid</Text>
          <Text className="text-fg text-[14px] font-bold">
            ${bid} FAAB
          </Text>
        </View>

        {/* Roster note */}
        <View className="mx-4 mt-3 flex-row items-start bg-ink-850 border border-ink-700 rounded-card p-3.5 gap-2.5">
          <Lightbulb color="#2AB3FF" size={16} />
          <Text className="flex-1 text-fg-muted text-[12px] leading-5">
            {dropping
              ? `You'll have 3 forwards, 2 defencemen and 2 goalies after this move. Net impact: `
              : `Adding ${adding.name} without dropping anyone. Net impact: `}
            <Text className={gain ? "text-win font-bold" : "text-loss font-bold"}>
              {gain ? "+" : ""}
              {projDelta.toFixed(1)} pts
            </Text>
            .
          </Text>
        </View>

        {/* Confirm */}
        <View className="px-4 mt-6">
          <Pressable
            onPress={() => router.push("/add-drop/success")}
            className="rounded-full py-4 items-center bg-accent"
          >
            <Text className="text-ink-900 text-[15px] font-bold">
              {dropping ? "Confirm Add / Drop" : "Confirm Add"}
            </Text>
          </Pressable>
          <Pressable onPress={() => router.back()} className="mt-3 py-2 items-center">
            <Text className="text-fg-muted text-[14px] font-semibold">Cancel</Text>
          </Pressable>
        </View>
      </ScrollView>

      <BottomNav active="players" />
    </SafeAreaView>
  );
}