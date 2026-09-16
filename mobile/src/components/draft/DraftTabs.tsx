import { Pressable, Text, View } from "react-native";

interface Props<T extends string> {
  tabs: readonly T[];
  active: T;
  onChange: (tab: T) => void;
}

/** Underline-style tab bar used across the Rookie Draft screens. */
export function DraftTabs<T extends string>({ tabs, active, onChange }: Props<T>) {
  return (
    <View className="flex-row border-b border-ink-700/60">
      {tabs.map((t) => {
        const isActive = t === active;
        return (
          <Pressable
            key={t}
            onPress={() => onChange(t)}
            className="flex-1 items-center pt-2.5 pb-2.5"
          >
            <Text
              className={`text-[13px] font-bold ${
                isActive ? "text-accent" : "text-fg-muted"
              }`}
            >
              {t}
            </Text>
            <View
              className={`absolute bottom-0 h-0.5 rounded-full ${
                isActive ? "bg-accent left-8 right-8" : "left-0 right-0"
              }`}
            />
          </Pressable>
        );
      })}
    </View>
  );
}
