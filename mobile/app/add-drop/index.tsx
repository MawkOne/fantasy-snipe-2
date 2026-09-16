import { useMemo, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { ChevronLeft, X } from "lucide-react-native";

import { DROPPABLE_PLAYERS, type AvailablePlayer } from "../../src/data/mock";
import { getAdding, setDropping } from "../../src/data/addDropStore";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { PositionBadge } from "../../src/components/PositionBadge";
import { BottomNav } from "../../src/components/BottomNav";

export default function AddDropScreen() {
  const router = useRouter();
  const adding = getAdding();
  const [selectedDropId, setSelectedDropId] = useState<string | null>(null);

  const dropping = useMemo(
    () => DROPPABLE_PLAYERS.find((p) => p.id === selectedDropId) ?? null,
    [selectedDropId]
  );

  if (!adding) {
    // No player chosen — bounce back.
    router.back();
    return null;
  }

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="flex-row items-center px-4 py-3 border-b border-ink-700/60">
        <Pressable onPress={() => router.back()} className="mr-3 p-1 -ml-1">
          <ChevronLeft color="#F2F7FC" size={24} />
        </Pressable>
        <Text className="text-fg text-lg font-extrabold">Add / Drop</Text>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 120 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Adding card */}
        <Text className="text-fg-faint text-[11px] font-bold tracking-widest px-4 pt-4 pb-2">
          ADD
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center">
            <PlayerHeadshot url={adding.headshotUrl} size={44} />
            <View className="flex-1 ml-3">
              <Text className="text-fg text-[15px] font-semibold">
                {adding.name}
              </Text>
              <Text className="text-fg-muted text-xs mt-0.5">
                {adding.team} · {adding.position}
              </Text>
              <View className="flex-row items-center gap-1.5 mt-1">
                <Text className="text-fg-faint text-[11px]">
                  {adding.projectedPoints.toFixed(1)} proj
                </Text>
                <Text className="text-fg-faint text-[11px]">·</Text>
                <Text className="text-fg-faint text-[11px]">
                  {adding.rosteredPct}% rostered
                </Text>
              </View>
            </View>
            <Pressable onPress={() => router.back()} className="p-1">
              <X color="#5A7186" size={18} />
            </Pressable>
          </View>
        </View>

        {/* Drop section */}
        <View className="flex-row items-center justify-between px-4 pt-6 pb-1">
          <Text className="text-fg-faint text-[11px] font-bold tracking-widest">
            DROP
          </Text>
          <Text className="text-fg-faint text-[11px]">
            Optional
          </Text>
        </View>
        <Text className="text-fg-muted text-xs px-4 pb-2">
          Choose a player to drop, or skip to add without dropping
        </Text>

        {DROPPABLE_PLAYERS.map((p) => {
          const selected = p.id === selectedDropId;
          return (
            <Pressable
              key={p.id}
              onPress={() => {
                setSelectedDropId(p.id);
                setDropping(p);
              }}
              className={`mx-4 mb-2 flex-row items-center rounded-card border p-3 ${
                selected
                  ? "border-accent bg-accent/10"
                  : "border-ink-700 bg-ink-850"
              }`}
            >
              <PositionBadge label={p.position} />
              <View className="ml-2.5">
                <PlayerHeadshot url={p.headshotUrl} size={40} />
              </View>
              <View className="flex-1 ml-2.5">
                <Text className="text-fg text-[14px] font-semibold">
                  {p.name}
                </Text>
                <Text className="text-fg-muted text-xs mt-0.5">
                  {p.team} · {p.position}
                </Text>
              </View>
              <Text className="text-fg text-[14px] font-bold mr-3">
                {p.projectedPoints.toFixed(1)}
              </Text>
              {/* Radio circle */}
              <View
                className={`w-5 h-5 rounded-full border-2 items-center justify-center ${
                  selected ? "border-accent" : "border-ink-600"
                }`}
              >
                {selected ? (
                  <View className="w-2.5 h-2.5 rounded-full bg-accent" />
                ) : null}
              </View>
            </Pressable>
          );
        })}
      </ScrollView>

      {/* Continue CTA */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60">
        <Pressable
          onPress={() => {
            setDropping(dropping);
            router.push("/add-drop/review");
          }}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">
            {dropping ? "Continue" : "Add Without Dropping"}
          </Text>
        </Pressable>
      </View>

      <BottomNav active="players" />
    </SafeAreaView>
  );
}
