import { Text, View } from "react-native";
import type { GameDayState } from "../data/types";

interface Props {
  days?: GameDayState[];
}

/** Start/Sit pills per game day (week view for goalies). */
export function GoalieDayPills({ days = [] }: Props) {
  return (
    <View className="flex-row items-center gap-1.5">
      {days.map((state, i) => (
        <View
          key={i}
          className={`px-2 py-1 rounded-md border ${
            state === "start"
              ? "border-win bg-win/10"
              : "border-sit bg-sit/10"
          }`}
        >
          <Text
            className={`text-[10px] font-bold ${
              state === "start" ? "text-win" : "text-sit"
            }`}
          >
            {state === "start" ? "Start" : state === "sit" ? "Sit" : "TBD"}
          </Text>
        </View>
      ))}
    </View>
  );
}
