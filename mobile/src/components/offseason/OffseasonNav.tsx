import { Pressable, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { ChevronLeft, X } from "lucide-react-native";

interface Props {
  title: string;
  subtitle?: string;
  /** Shows an X (close) instead of a back chevron. */
  close?: boolean;
}

/** Back-nav header used on Offseason sub-screens. */
export function OffseasonNav({ title, subtitle, close = false }: Props) {
  const router = useRouter();

  return (
    <View className="flex-row items-center justify-between px-4 py-2.5 border-b border-ink-700/60">
      <Pressable onPress={() => router.back()} className="p-1 -ml-1 w-8">
        {close ? (
          <X color="#F2F7FC" size={22} />
        ) : (
          <ChevronLeft color="#F2F7FC" size={24} />
        )}
      </Pressable>
      <View className="items-center">
        <Text className="text-fg text-lg font-extrabold">{title}</Text>
        {subtitle ? (
          <Text className="text-fg-muted text-[11px] mt-0.5">{subtitle}</Text>
        ) : null}
      </View>
      <View className="w-8" />
    </View>
  );
}
