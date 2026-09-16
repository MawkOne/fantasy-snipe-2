import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { Building2, CalendarClock, ChevronDown, ChevronRight, Gavel, Sparkles, Trophy } from "lucide-react-native";

import { MY_LEAGUE } from "../../src/data/mock";

export default function MoreScreen() {
  const router = useRouter();

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 pt-2 pb-3">
        <View className="flex-row items-center gap-3">
          <View className="w-11 h-11 rounded-full bg-ink-700 border border-ink-600 items-center justify-center">
            <Text className="text-accent text-lg font-black">🐻‍❄️</Text>
          </View>
          <View>
            <View className="flex-row items-center gap-1">
              <Text className="text-fg text-xl font-extrabold tracking-tight">
                {MY_LEAGUE.name}
              </Text>
              <ChevronDown color="#8CA3B8" size={16} />
            </View>
            <Text className="text-fg-muted text-xs mt-0.5">
              {MY_LEAGUE.myTeam.record.w} - {MY_LEAGUE.myTeam.record.l}
              {MY_LEAGUE.myTeam.division ? `   ${MY_LEAGUE.myTeam.division}` : ""}
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        <Text className="px-4 pt-2 pb-2 text-fg-faint text-[10px] font-bold tracking-widest">
          LEAGUE
        </Text>

        {/* Rookie Draft */}
        <Pressable
          onPress={() => router.push("/rookie-draft")}
          className="mx-4 mb-2 bg-ink-850 border border-accent/50 rounded-card p-3.5 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-full bg-accent/10 border border-accent/40 items-center justify-center">
            <Trophy color="#2AB3FF" size={18} />
          </View>
          <View className="flex-1 ml-3">
            <View className="flex-row items-center gap-2">
              <Text className="text-fg text-[14px] font-bold">
                Rookie Draft
              </Text>
              <View className="flex-row items-center gap-1 bg-loss/15 rounded-full px-1.5 py-0.5">
                <View className="w-1 h-1 rounded-full bg-loss" />
                <Text className="text-loss text-[8px] font-bold tracking-widest">
                  LIVE
                </Text>
              </View>
            </View>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              2025 Rookie Draft · Round 1 · You're on the clock
            </Text>
          </View>
          <ChevronRight color="#5A7186" size={16} />
        </Pressable>

        {/* Offseason */}
        <Pressable
          onPress={() => router.push("/offseason")}
          className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <CalendarClock color="#2AB3FF" size={18} />
          </View>
          <View className="flex-1 ml-3">
            <Text className="text-fg text-[14px] font-bold">Offseason</Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              2026 · Step 1 of 7: Buyouts
            </Text>
          </View>
          <ChevronRight color="#5A7186" size={16} />
        </Pressable>

        {/* Events */}
        <Pressable
          onPress={() => router.push("/events")}
          className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Sparkles color="#2AB3FF" size={18} />
          </View>
          <View className="flex-1 ml-3">
            <View className="flex-row items-center gap-2">
              <Text className="text-fg text-[14px] font-bold">Events</Text>
              <View className="flex-row items-center gap-1 bg-win/15 rounded-full px-1.5 py-0.5">
                <View className="w-1 h-1 rounded-full bg-win" />
                <Text className="text-win text-[8px] font-bold tracking-widest">
                  2 ACTIVE
                </Text>
              </View>
            </View>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              Side competitions. More hockey. Year-round.
            </Text>
          </View>
          <ChevronRight color="#5A7186" size={16} />
        </Pressable>

        {/* UFA Auction — live */}
        <Pressable
          onPress={() => router.push("/auction")}
          className="mx-4 mb-2 bg-ink-850 border border-accent/50 rounded-card p-3.5 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-full bg-accent/10 border border-accent/40 items-center justify-center">
            <Gavel color="#2AB3FF" size={18} />
          </View>
          <View className="flex-1 ml-3">
            <View className="flex-row items-center gap-2">
              <Text className="text-fg text-[14px] font-bold">UFA Auction</Text>
              <View className="flex-row items-center gap-1 bg-win/15 rounded-full px-1.5 py-0.5">
                <View className="w-1 h-1 rounded-full bg-win" />
                <Text className="text-win text-[8px] font-bold tracking-widest">
                  LIVE
                </Text>
              </View>
            </View>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              Round 2 · Mitch Marner · High bid $28
            </Text>
          </View>
          <ChevronRight color="#5A7186" size={16} />
        </Pressable>

        {/* Franchise */}
        <Pressable
          onPress={() => router.push("/franchise")}
          className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center"
        >
          <View className="w-10 h-10 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Building2 color="#2AB3FF" size={18} />
          </View>
          <View className="flex-1 ml-3">
            <Text className="text-fg text-[14px] font-bold">Franchise</Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              Salary cap, contracts, picks & assets
            </Text>
          </View>
          <ChevronRight color="#5A7186" size={16} />
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}
