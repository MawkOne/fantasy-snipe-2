import { Text, View } from "react-native";
import { Ellipsis } from "lucide-react-native";

interface Props {
  live?: boolean;
}

/** UHHP-branded header shown on every Rookie Draft screen. */
export function DraftHeader({ live = false }: Props) {
  return (
    <View className="flex-row items-center justify-between px-4 pt-2 pb-3 border-b border-ink-700/60">
      <View className="flex-row items-center gap-2.5">
        <View className="w-9 h-9 rounded-full bg-ink-700 border border-accent/50 items-center justify-center">
          <Text className="text-accent text-[8px] font-black tracking-tight">
            UHHP
          </Text>
        </View>
        <View>
          <Text className="text-fg text-[17px] font-extrabold tracking-tight">
            Rookie Draft
          </Text>
          <Text className="text-fg-muted text-[10px] mt-0.5">
            2025 Rookie Draft
          </Text>
        </View>
      </View>
      {live ? (
        <View className="flex-row items-center gap-1.5 bg-loss/15 border border-loss/40 rounded-full px-2.5 py-1">
          <View className="w-1.5 h-1.5 rounded-full bg-loss" />
          <Text className="text-loss text-[10px] font-bold tracking-widest">
            LIVE
          </Text>
        </View>
      ) : (
        <Ellipsis color="#8CA3B8" size={20} />
      )}
    </View>
  );
}
