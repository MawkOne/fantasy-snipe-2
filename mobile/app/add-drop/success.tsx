import { Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { CircleCheck } from "lucide-react-native";

import { clearAddDrop, getAdding, getDropping } from "../../src/data/addDropStore";
import { BottomNav } from "../../src/components/BottomNav";

export default function AddDropSuccessScreen() {
  const router = useRouter();
  const adding = getAdding();
  const dropping = getDropping();

  const finish = () => {
    clearAddDrop();
    // Pop back to Players tab.
    router.dismissAll();
    router.replace("/(tabs)/players");
  };

  return (
    <SafeAreaView className="flex-1 bg-ink-900 px-6">
      <View className="flex-1 items-center justify-center">
      <View className="w-16 h-16 rounded-full bg-win/15 items-center justify-center mb-5">
        <CircleCheck color="#22C55E" size={40} />
      </View>
      <Text className="text-fg text-xl font-extrabold text-center">
        Waiver claim submitted!
      </Text>
      <Text className="text-fg-muted text-sm text-center mt-2 leading-5">
        {adding?.name ?? "Player"} will be added if successful.
        {dropping ? ` ${dropping.name} will be dropped.` : " No player will be dropped."}
      </Text>

      </View>

      <View className="w-full gap-3 pb-6">
        <Pressable
          onPress={finish}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">View Waivers</Text>
        </Pressable>
        <Pressable
          onPress={finish}
          className="rounded-full py-3.5 items-center border border-ink-600 bg-ink-850"
        >
          <Text className="text-fg text-[15px] font-bold">Done</Text>
        </Pressable>
      </View>

      <BottomNav active="players" />
    </SafeAreaView>
  );
}
