import { Pressable, Text, View } from "react-native";
import type { Player } from "../data/types";
import type { TodayGame } from "../data/mock";
import { GameDayDots } from "./GameDayDots";
import { GoalieDayPills } from "./GoalieDayPills";
import { PlayerHeadshot } from "./PlayerHeadshot";
import { PositionBadge } from "./PositionBadge";
import { TeamLogo } from "./TeamLogo";
import type { RowView } from "./PlayerRow";

interface Props {
  slotLabel: string;
  player: Player;
  mode: "today" | "week";
  rowView?: RowView;
  todayGame?: TodayGame;
  onPress?: (player: Player) => void;
}

export function GoalieRow({ slotLabel, player, mode, rowView = "schedule", todayGame, onPress }: Props) {
  return (
    <Pressable
      onPress={() => onPress?.(player)}
      className="flex-row items-center py-2 px-2 border-b border-ink-700/60"
    >
      <PositionBadge label={slotLabel} />
      <View className="ml-2">
        <PlayerHeadshot url={player.headshotUrl} size={36} />
      </View>

      <View className="flex-1 ml-2 mr-1">
        <Text className="text-fg text-[13px] font-semibold" numberOfLines={1}>
          {player.name}
        </Text>
        <View className="flex-row items-center gap-1 mt-0.5">
          <TeamLogo abbrev={player.team} size={15} />
          <Text className="text-fg-muted text-[11px]">{player.team}</Text>
        </View>
      </View>

      {/* Right-side content varies by rowView */}
      {rowView === "schedule" && (
        <>
          <View className="w-[50px] mr-1">
            <Text className="text-fg-muted text-[10px] font-medium" numberOfLines={1}>
              {player.opponent}
            </Text>
            {mode === "today" && todayGame ? (
              todayGame.isLive ? (
                <Text className="text-loss text-[11px] font-semibold mt-0.5">
                  {todayGame.liveStatus}
                </Text>
              ) : (
                <Text className="text-fg-faint text-[11px] mt-0.5">
                  {todayGame.gameTime}
                </Text>
              )
            ) : null}
          </View>

          {mode === "week" ? (
            <View className="mr-1.5">
              {player.goalieDays ? (
                <GoalieDayPills days={player.goalieDays} />
              ) : (
                <GameDayDots gameDays={player.gameDays} />
              )}
            </View>
          ) : null}

          <View className="w-[38px] items-end">
            <Text className="text-fg text-[14px] font-bold">
              {player.projectedPoints.toFixed(1)}
            </Text>
          </View>
        </>
      )}

      {rowView === "salary" && (
        <>
          <View className="w-[52px] mr-1">
            <Text className="text-fg-muted text-[10px] font-medium">
              {player.contractType}
            </Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              {player.contractYears}yr left
            </Text>
          </View>

          <View className="w-[52px] items-end">
            <Text className="text-fg text-[14px] font-bold">
              {player.capHit}
            </Text>
            <Text className="text-fg-faint text-[9px] mt-0.5">
              cap hit
            </Text>
          </View>
        </>
      )}

      {rowView === "performance" && (
        <>
          <View className="flex-row items-center gap-3 mr-1">
            <StatMini label="W" value={player.wins} />
            <StatMini label="GAA" value={player.gaa?.toFixed(2)} />
            <StatMini label="SV%" value={player.svPct ? `.${Math.round(player.svPct * 1000)}` : undefined} />
          </View>

          <View className="w-[38px] items-end">
            <Text className="text-fg text-[14px] font-bold">
              {player.wins}
            </Text>
            <Text className="text-fg-faint text-[9px] mt-0.5">
              wins
            </Text>
          </View>
        </>
      )}
    </Pressable>
  );
}

function StatMini({ label, value }: { label: string; value?: string | number }) {
  return (
    <View className="items-center">
      <Text className="text-fg text-[12px] font-bold">{value ?? "-"}</Text>
      <Text className="text-fg-faint text-[8px]">{label}</Text>
    </View>
  );
}