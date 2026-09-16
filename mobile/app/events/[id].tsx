import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  Brackets,
  Calendar,
  ChevronLeft,
  CircleCheck,
  Trophy,
} from "lucide-react-native";

import { EVENT_DETAILS, EVENTS } from "../../src/data/events";
import { BottomNav } from "../../src/components/BottomNav";

export default function EventDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const event = EVENTS.find((e) => e.id === id);
  const detail = id ? EVENT_DETAILS[id] : undefined;

  if (!event || !detail) {
    router.back();
    return null;
  }

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="flex-row items-center justify-between px-4 py-2.5 border-b border-ink-700/60">
        <Pressable onPress={() => router.back()} className="p-1 -ml-1 w-8">
          <ChevronLeft color="#F2F7FC" size={24} />
        </Pressable>
        <View className="items-center">
          <Text className="text-fg text-lg font-extrabold">{event.name}</Text>
          <Text className="text-fg-muted text-[11px] mt-0.5">
            {detail.currentRound}
          </Text>
        </View>
        <View className="w-8" />
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-4 items-center">
          <View className="w-16 h-16 rounded-2xl bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-3xl">{event.emoji}</Text>
          </View>
          <Text className="text-fg text-[20px] font-extrabold mt-2.5">
            {event.name}
          </Text>
          <Text className="text-fg-muted text-[12px] mt-0.5">
            {event.tagline}
          </Text>
          <View className="flex-row items-center gap-1.5 mt-2 bg-accent/10 border border-accent/40 rounded-full px-3 py-1">
            <Brackets color="#2AB3FF" size={12} />
            <Text className="text-accent text-[11px] font-bold">
              {detail.format}
            </Text>
          </View>
        </View>

        {/* Your status */}
        <View className="mx-4 mt-3 bg-accent/10 border border-accent/50 rounded-card p-3.5 flex-row items-center">
          <Text className="text-2xl mr-3">{event.yourSideEmoji}</Text>
          <View className="flex-1">
            <Text className="text-fg-faint text-[9px] font-bold tracking-widest">
              YOUR STATUS
            </Text>
            <Text className="text-fg text-[13px] font-bold mt-0.5">
              {detail.yourStatus}
            </Text>
          </View>
          {event.opponentName && (
            <View className="items-end">
              <Text className="text-fg-faint text-[9px] font-bold tracking-widest">
                NEXT
              </Text>
              <Text className="text-fg text-[12px] font-bold mt-0.5">
                vs {event.opponentName}
              </Text>
              <Text className="text-fg-faint text-[10px]">
                {event.opponentDetail}
              </Text>
            </View>
          )}
        </View>

        {/* Standings / bracket */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          {detail.standingsTitle.toUpperCase()}
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-3.5">
          {detail.standings.map((row, i) => (
            <View
              key={`${row.team}-${row.rank}`}
              className={`flex-row items-center py-2.5 ${
                i < detail.standings.length - 1
                  ? "border-b border-ink-700/60"
                  : ""
              } ${row.mine ? "" : ""}`}
            >
              <Text className="text-fg-faint text-[12px] font-bold w-5">
                {row.rank}
              </Text>
              <Text className="text-lg mx-2">{row.emoji}</Text>
              <Text
                className={`flex-1 text-[13px] font-semibold ${
                  row.mine ? "text-accent" : "text-fg"
                }`}
              >
                {row.team}
              </Text>
              <Text className="text-fg-muted text-[12px] w-10 text-right">
                {row.record}
              </Text>
              <Text className="text-fg text-[12px] font-bold w-8 text-right">
                {row.points > 0 ? row.points : ""}
              </Text>
            </View>
          ))}
        </View>

        {/* Rules */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          FORMAT & RULES
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4 gap-2.5">
          {detail.rules.map((rule) => (
            <View key={rule} className="flex-row">
              <View className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 mr-2.5" />
              <Text className="flex-1 text-fg-muted text-[13px] leading-5">
                {rule}
              </Text>
            </View>
          ))}
        </View>

        {/* Prize */}
        <View className="mx-4 mt-3 bg-warn/10 border border-warn/30 rounded-card p-3.5 flex-row items-center gap-2.5">
          <Trophy color="#F59E0B" size={16} />
          <View className="flex-1">
            <Text className="text-fg-faint text-[9px] font-bold tracking-widest">
              PRIZE
            </Text>
            <Text className="text-fg text-[13px] font-semibold mt-0.5">
              {detail.prize}
            </Text>
          </View>
        </View>

        {/* Schedule note */}
        <View className="mx-4 mt-3 flex-row items-center bg-ink-850 border border-ink-700 rounded-card p-3.5 gap-2.5">
          <Calendar color="#2AB3FF" size={15} />
          <Text className="text-fg-muted text-[12px] flex-1">
            {detail.currentRound}
          </Text>
          <CircleCheck color="#22C55E" size={15} />
        </View>
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}
