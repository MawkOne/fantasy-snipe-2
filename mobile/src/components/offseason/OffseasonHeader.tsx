import { Pressable, Text, View } from "react-native";
import { Settings } from "lucide-react-native";

import { OFFSEASON_YEAR } from "../../data/offseason";

interface Props {
  /** Admin mode on → gear highlights. */
  admin?: boolean;
  onAdminToggle?: () => void;
}

/** UHHP-branded header for the Offseason hub. */
export function OffseasonHeader({ admin = false, onAdminToggle }: Props) {
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
            Offseason
          </Text>
          <Text className="text-fg-muted text-[10px] mt-0.5">
            {OFFSEASON_YEAR}
          </Text>
        </View>
      </View>
      <Pressable
        onPress={onAdminToggle}
        className="p-1.5"
        accessibilityLabel="Admin controls"
        accessibilityState={{ selected: admin }}
      >
        <Settings color={admin ? "#2AB3FF" : "#8CA3B8"} size={20} />
      </Pressable>
    </View>
  );
}