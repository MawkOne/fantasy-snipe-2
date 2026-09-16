import { Text, View } from "react-native";

interface Props {
  /** Indices of days (0 = Mon) the player has a game. */
  gameDays?: number[];
}

const DAY_LETTERS = ["M", "T", "W", "T", "F", "S", "S"];

/** Column of 7 day-slots (Mon–Sun); lit dot + label on game days. */
export function GameDayDots({ gameDays = [] }: Props) {
  return (
    <View className="flex-row items-center gap-[5px]">
      {Array.from({ length: 7 }).map((_, i) => {
        const hasGame = gameDays.includes(i);
        return (
          <View key={i} className="items-center w-[10px]">
            <Text
              className={`text-[8px] font-semibold mb-[3px] ${
                hasGame ? "text-fg-muted" : "text-ink-700"
              }`}
            >
              {DAY_LETTERS[i]}
            </Text>
            <View
              className={`w-[6px] h-[6px] rounded-full ${
                hasGame ? "bg-accent" : "bg-ink-700"
              }`}
            />
          </View>
        );
      })}
    </View>
  );
}
