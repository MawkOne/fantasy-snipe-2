import { Pressable, ScrollView, Text, View } from "react-native";

import { OFFSEASON_STEPS, type OffseasonStepId } from "../../data/offseason";

interface Props {
  active: OffseasonStepId;
  onSelect?: (id: OffseasonStepId) => void;
}

/** Horizontal 1–7 step indicator for the offseason wizard. */
export function StepIndicator({ active, onSelect }: Props) {
  const activeIndex = OFFSEASON_STEPS.findIndex((s) => s.id === active);

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      className="flex-none border-b border-ink-700/60"
      contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 10, gap: 6 }}
    >
      {OFFSEASON_STEPS.map((step, i) => {
        const isActive = i === activeIndex;
        const isDone = i < activeIndex;
        return (
          <Pressable
            key={step.id}
            onPress={() => !isActive && onSelect?.(step.id)}
            disabled={!onSelect || isActive}
            className="items-center w-[52px]"
          >
            <View
              className={`w-6 h-6 rounded-full items-center justify-center border ${
                isActive
                  ? "bg-accent border-accent"
                  : isDone
                    ? "bg-accent/20 border-accent/50"
                    : "bg-ink-850 border-ink-600"
              }`}
            >
              <Text
                className={`text-[11px] font-bold ${
                  isActive
                    ? "text-ink-900"
                    : isDone
                      ? "text-accent"
                      : "text-fg-faint"
                }`}
              >
                {i + 1}
              </Text>
            </View>
            <Text
              className={`text-[9px] font-semibold mt-1 text-center ${
                isActive ? "text-accent" : "text-fg-faint"
              }`}
              numberOfLines={2}
            >
              {step.label}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}
