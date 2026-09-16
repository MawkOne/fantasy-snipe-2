import { Text, View, Pressable } from "react-native";
import { Plus } from "lucide-react-native";
import type { AvailablePlayer } from "../data/mock";
import { PlayerHeadshot } from "./PlayerHeadshot";
import { PositionBadge } from "./PositionBadge";

interface Props {
  player: AvailablePlayer;
  onAdd?: (player: AvailablePlayer) => void;
  onPress?: (player: AvailablePlayer) => void;
}

export function AvailablePlayerRow({ player, onAdd, onPress }: Props) {
  const onWaivers = player.status === "waivers";
  return (
    <Pressable
      onPress={() => onPress?.(player)}
      className="flex-row items-center py-2.5 px-3 border-b border-ink-700/60"
    >
      <PositionBadge label={player.position} />
      <View className="ml-2.5">
        <PlayerHeadshot url={player.headshotUrl} size={40} />
      </View>

      {/* Name / team / matchup */}
      <View className="flex-1 ml-2.5 mr-1">
        <Text className="text-fg text-[14px] font-semibold" numberOfLines={1}>
          {player.name}
        </Text>
        <Text className="text-fg-muted text-xs mt-0.5">
          {player.team} · {player.position}
        </Text>
      </View>

      {/* Proj / rostered / trend */}
      <View className="items-end mr-2">
        <Text className="text-fg text-[14px] font-bold">
          {player.projectedPoints.toFixed(1)}
          <Text className="text-fg-muted text-[10px] font-normal"> proj</Text>
        </Text>
        <View className="flex-row items-center gap-1.5 mt-0.5">
          <Text className="text-fg-faint text-[11px]">
            {player.rosteredPct}% rostered
          </Text>
          {player.trendPct ? (
            <Text className="text-win text-[11px] font-bold">
              +{player.trendPct}%
            </Text>
          ) : null}
        </View>
      </View>

      {/* Add button */}
      <Pressable
        onPress={() => onAdd?.(player)}
        className={`flex-row items-center gap-1 rounded-full px-3 py-1.5 border ${
          onWaivers
            ? "border-warn/70 bg-warn/10"
            : "border-accent bg-accent/10"
        }`}
      >
        <Plus color={onWaivers ? "#F59E0B" : "#2AB3FF"} size={13} />
        <Text
          className={`text-[13px] font-bold ${
            onWaivers ? "text-warn" : "text-accent"
          }`}
        >
          Add
        </Text>
      </Pressable>
    </Pressable>
  );
}
