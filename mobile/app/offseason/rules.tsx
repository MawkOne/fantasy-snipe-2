import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { ArrowRight } from "lucide-react-native";

import { OffseasonNav } from "../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../src/components/BottomNav";
import { BUYOUT_RULES } from "../../src/data/offseason";

export default function BuyoutRulesScreen() {
  const router = useRouter();

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title="Buyout Rules" subtitle="2026 Offseason" />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4 gap-2.5">
          {BUYOUT_RULES.map((rule) => (
            <View key={rule} className="flex-row">
              <View className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 mr-2.5" />
              <Text className="flex-1 text-fg-muted text-[13px] leading-5">
                {rule}
              </Text>
            </View>
          ))}
        </View>

        <Pressable
          onPress={() => router.push("/offseason/buyouts")}
          className="mx-4 mt-4 bg-accent rounded-full py-3.5 flex-row items-center justify-center gap-2"
        >
          <Text className="text-ink-900 text-[15px] font-bold">
            View Roster for Buyouts
          </Text>
          <ArrowRight color="#0A1420" size={16} />
        </Pressable>
      </ScrollView>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}
