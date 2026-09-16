import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { ChevronDown, Sparkles, TriangleAlert, TrendingUp } from "lucide-react-native";

import {
  LINEUP_SUMMARY,
  MY_LEAGUE,
  ROSTER,
  TODAY_GAMES,
  WEEK_DAYS,
} from "../../src/data/mock";
import { GoalieRow } from "../../src/components/GoalieRow";
import { PlayerRow, type RowView } from "../../src/components/PlayerRow";

type Mode = "today" | "week";

export default function LineupScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("week");
  const [rowView, setRowView] = useState<RowView>("schedule");
  const [selectedDay, setSelectedDay] = useState(1); // Tue Oct 8 (mock default)

  const openPlayer = (playerId: string) => router.push(`/player/${playerId}`);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* ---- Team header ---- */}
      <View className="flex-row items-center justify-between px-4 pt-2 pb-3">
        <View className="flex-row items-center gap-3">
          {/* League avatar placeholder */}
          <View className="w-11 h-11 rounded-full bg-ink-700 border border-ink-600 items-center justify-center">
            <Text className="text-accent text-lg font-black">🐻‍❄️</Text>
          </View>
          <View>
            <View className="flex-row items-center gap-1">
              <Text className="text-fg text-xl font-extrabold tracking-tight">
                {MY_LEAGUE.name}
              </Text>
              <ChevronDown color="#8CA3B8" size={16} />
            </View>
            <Text className="text-fg-muted text-xs mt-0.5">
              {MY_LEAGUE.myTeam.record.w} - {MY_LEAGUE.myTeam.record.l}
              {MY_LEAGUE.myTeam.division ? `   ${MY_LEAGUE.myTeam.division}` : ""}
            </Text>
          </View>
        </View>

        {/* Week selector */}
        <Pressable className="flex-row items-center gap-1.5 border border-ink-600 rounded-full px-3.5 py-2 bg-ink-850">
          <Text className="text-fg text-sm font-semibold">Week 1</Text>
          <ChevronDown color="#8CA3B8" size={14} />
        </Pressable>
      </View>

      {/* ---- Today / Week toggle + Optimize CTA ---- */}
      <View className="flex-row items-center px-4 gap-3 pb-3">
        <View className="flex-row bg-ink-850 rounded-full p-1 border border-ink-700">
          {(["today", "week"] as Mode[]).map((m) => (
            <Pressable
              key={m}
              onPress={() => setMode(m)}
              className={`px-5 py-1.5 rounded-full ${
                mode === m ? "bg-ink-700 border border-accent/60" : ""
              }`}
            >
              <Text
                className={`text-sm font-semibold capitalize ${
                  mode === m ? "text-fg" : "text-fg-muted"
                }`}
              >
                {m}
              </Text>
            </Pressable>
          ))}
        </View>

        <View className="flex-1" />

        <Pressable className="flex-row items-center gap-1.5 border border-accent rounded-full px-4 py-2.5 bg-accent/10">
          <Sparkles color="#2AB3FF" size={15} />
          <Text className="text-accent text-sm font-bold">
            {mode === "week" ? "Set Optimal Lineup" : "Optimize Today"}
          </Text>
        </Pressable>
      </View>

      {/* ---- Day selector (week mode) ---- */}
      {mode === "week" && (
        <View className="flex-row px-4 gap-2 pb-3">
          {WEEK_DAYS.map((d, i) => {
            const selected = i === selectedDay;
            return (
              <Pressable
                key={d.date}
                onPress={() => setSelectedDay(i)}
                className={`flex-1 items-center py-2 rounded-xl border ${
                  selected
                    ? "border-accent bg-accent/10"
                    : "border-ink-700 bg-ink-850"
                }`}
              >
                <Text
                  className={`text-[11px] font-semibold ${
                    selected ? "text-accent" : "text-fg-muted"
                  }`}
                >
                  {d.label}
                </Text>
                <Text
                  className={`text-[11px] mt-0.5 ${
                    selected ? "text-fg" : "text-fg-faint"
                  }`}
                >
                  {d.date}
                </Text>
              </Pressable>
            );
          })}
        </View>
      )}

      {/* ---- Summary cards ---- */}
      <View className="flex-row px-4 gap-3 pb-3">
        <SummaryCard
          value={String(LINEUP_SUMMARY.scheduledStarts)}
          label="Scheduled Starts this week"
          valueClass="text-fg"
        />
        <SummaryCard
          value={String(LINEUP_SUMMARY.benchConflicts)}
          label="Bench Conflicts"
          valueClass="text-warn"
          icon={<TriangleAlert color="#F59E0B" size={16} />}
        />
        <SummaryCard
          value={String(LINEUP_SUMMARY.emptyOpportunities)}
          label="Empty Roster Opportunities"
          valueClass="text-win"
          icon={<TrendingUp color="#22C55E" size={16} />}
        />
      </View>

      {/* ---- Row view toggle ---- */}
      <View className="flex-row px-4 gap-2 pb-3">
        {(["schedule", "salary", "performance"] as RowView[]).map((v) => (
          <Pressable
            key={v}
            onPress={() => setRowView(v)}
            className={`px-3.5 py-1.5 rounded-full border ${
              rowView === v
                ? "border-accent bg-accent/15"
                : "border-ink-700 bg-ink-850"
            }`}
          >
            <Text
              className={`text-[11px] font-semibold capitalize ${
                rowView === v ? "text-accent" : "text-fg-muted"
              }`}
            >
              {v}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* ---- Roster list ---- */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        <SectionHeader
          title={`SKATERS (${ROSTER.skaters.length}/8)`}
          right={rowView === "schedule" ? "PROJ" : rowView === "salary" ? "CAP HIT" : "PTS"}
          showOpp={rowView === "schedule"}
          showGameDays={mode === "week" && rowView === "schedule"}
        />
        {ROSTER.skaters.map((slot) =>
          slot.player ? (
            <PlayerRow
              key={slot.player.id}
              slotLabel={slot.slot}
              player={slot.player}
              mode={mode}
              rowView={rowView}
              todayGame={TODAY_GAMES[slot.player.id]}
              onPress={(p) => openPlayer(p.id)}
            />
          ) : null
        )}

        <SectionHeader
          title={`GOALIES (${ROSTER.goalies.length}/2)`}
          right={rowView === "schedule" ? "PROJ" : rowView === "salary" ? "CAP HIT" : "W"}
          showOpp={rowView === "schedule"}
          showGameDays={mode === "week" && rowView === "schedule"}
        />
        {ROSTER.goalies.map((slot, i) =>
          slot.player ? (
            <GoalieRow
              key={slot.player.id}
              slotLabel={`G${i + 1}`}
              player={slot.player}
              mode={mode}
              rowView={rowView}
              todayGame={TODAY_GAMES[slot.player.id]}
              onPress={(p) => openPlayer(p.id)}
            />
          ) : null
        )}

        <SectionHeader
          title={`BENCH (${ROSTER.bench.length}/7)`}
          right={rowView === "schedule" ? "PROJ" : rowView === "salary" ? "CAP HIT" : "PTS"}
          showOpp={rowView === "schedule"}
          showGameDays={mode === "week" && rowView === "schedule"}
        />
        {ROSTER.bench.map((slot) =>
          slot.player ? (
            <PlayerRow
              key={slot.player.id}
              slotLabel="BN"
              player={slot.player}
              mode={mode}
              rowView={rowView}
              todayGame={TODAY_GAMES[slot.player.id]}
              isBench
              onPress={(p) => openPlayer(p.id)}
            />
          ) : null
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function SummaryCard({
  value,
  label,
  valueClass,
  icon,
}: {
  value: string;
  label: string;
  valueClass: string;
  icon?: React.ReactNode;
}) {
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3">
      <View className="flex-row items-start justify-between">
        <Text className={`text-2xl font-extrabold ${valueClass}`}>{value}</Text>
        {icon}
      </View>
      <Text className="text-fg-muted text-[11px] mt-1 leading-4">{label}</Text>
    </View>
  );
}

function SectionHeader({
  title,
  right,
  showOpp,
  showGameDays,
}: {
  title: string;
  right?: string;
  showOpp?: boolean;
  showGameDays?: boolean;
}) {
  return (
    <View className="flex-row items-center px-2.5 pt-4 pb-1.5">
      <Text className="flex-1 text-fg-faint text-[10px] font-bold tracking-widest">
        {title}
      </Text>
      {showOpp ? (
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest mr-1">
          OPP
        </Text>
      ) : null}
      {showGameDays ? (
        <Text className="text-fg-faint text-[9px] font-bold tracking-widest mr-1.5">
          GAME DAYS
        </Text>
      ) : null}
      <Text className="text-fg-faint text-[10px] font-bold tracking-widest w-[40px] text-right">
        {right}
      </Text>
    </View>
  );
}