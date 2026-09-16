import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { ChevronLeft, ChevronRight } from "lucide-react-native";

import { MANAGERS, type ManagerOption } from "../../src/data/mock";
import { BottomNav } from "../../src/components/BottomNav";

export default function TradeBuilderScreen() {
  const router = useRouter();

  const selectManager = (manager: ManagerOption) => {
    router.push({
      pathname: "/trades/detail",
      params: { managerId: manager.id },
    });
  };

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="flex-row items-center justify-between px-4 py-2 border-b border-ink-700/60">
        <Pressable onPress={() => router.back()} className="p-1 -ml-1">
          <ChevronLeft color="#F2F7FC" size={24} />
        </Pressable>
        <View className="items-center">
          <Text className="text-fg text-lg font-extrabold">New Trade</Text>
          <Text className="text-fg-muted text-[11px] mt-0.5">
            Choose a manager to trade with
          </Text>
        </View>
        <View className="w-8" />
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        <Text className="px-4 pt-3 pb-2 text-fg-faint text-[10px] font-bold tracking-widest">
          SELECT A MANAGER
        </Text>
        {MANAGERS.map((m) => (
          <Pressable
            key={m.id}
            onPress={() => selectManager(m)}
            className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center"
          >
            <View className="w-10 h-10 rounded-full items-center justify-center border-2 border-accent/60 bg-accent/10">
              <Text className="text-xl">{m.emoji}</Text>
            </View>
            <View className="flex-1 ml-3">
              <Text className="text-fg text-[14px] font-bold">{m.name}</Text>
              <Text className="text-fg-muted text-[11px] mt-0.5">
                {m.manager} · {m.record} ·{" "}
                <Text className="text-accent font-semibold">{m.strategy}</Text>
              </Text>
            </View>
            <ChevronRight color="#5A7186" size={16} />
          </Pressable>
        ))}
      </ScrollView>

      <BottomNav active="trades" />
    </SafeAreaView>
  );
}