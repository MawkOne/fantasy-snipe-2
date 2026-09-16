import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  ArrowLeftRight,
  Star,
  Ellipsis,
} from "lucide-react-native";

import { PLAYER_DETAILS, type PlayerDetail } from "../../src/data/mock";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { TeamLogo } from "../../src/components/TeamLogo";
import { BottomNav } from "../../src/components/BottomNav";

type TabKey = "overview" | "stats" | "schedule" | "news";
const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "stats", label: "Stats" },
  { key: "schedule", label: "Schedule" },
  { key: "news", label: "News" },
];

export default function PlayerDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("overview");
  const [watched, setWatched] = useState(false);

  const player: PlayerDetail | undefined =
    PLAYER_DETAILS[id ?? ""] ?? PLAYER_DETAILS.matthews;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav bar */}
      <View className="flex-row items-center justify-between px-4 py-2">
        <Pressable
          onPress={() => router.back()}
          className="flex-row items-center gap-1 -ml-1"
        >
          <ChevronLeft color="#F2F7FC" size={24} />
          <Text className="text-fg text-[15px] font-semibold">Players</Text>
        </Pressable>
        <View className="flex-row items-center gap-4">
          <Pressable onPress={() => setWatched(!watched)}>
            <Star
              color={watched ? "#2AB3FF" : "#F2F7FC"}
              fill={watched ? "#2AB3FF" : "transparent"}
              size={20}
            />
          </Pressable>
          <Pressable>
            <Ellipsis color="#F2F7FC" size={20} />
          </Pressable>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 110 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View className="items-center pt-2 pb-4">
          <PlayerHeadshot url={player.headshotUrl} size={110} />
          <Text className="text-fg text-2xl font-extrabold mt-3">
            {player.name}
          </Text>
          <Text className="text-fg-muted text-sm mt-1">
            {player.position} · {player.team} · #{player.number}
          </Text>
          <Text className="text-fg-faint text-xs mt-1">
            {player.rosteredPct}% Rostered | {player.startedPct}% Started
          </Text>

          {/* Action buttons */}
          <View className="flex-row gap-3 mt-4 px-6 w-full">
            <Pressable className="flex-1 flex-row items-center justify-center gap-1.5 bg-accent rounded-full py-2.5">
              <Plus color="#0A1420" size={16} />
              <Text className="text-ink-900 text-sm font-bold">Add</Text>
            </Pressable>
            <Pressable className="flex-1 flex-row items-center justify-center gap-1.5 border border-ink-600 rounded-full py-2.5">
              <ArrowLeftRight color="#F2F7FC" size={15} />
              <Text className="text-fg text-sm font-bold">Trade</Text>
            </Pressable>
            <Pressable
              onPress={() => setWatched(!watched)}
              className="flex-1 flex-row items-center justify-center gap-1.5 border border-ink-600 rounded-full py-2.5"
            >
              <Star color="#F2F7FC" size={15} />
              <Text className="text-fg text-sm font-bold">Watch</Text>
            </Pressable>
          </View>
        </View>

        {/* Tabs */}
        <View className="flex-row border-b border-ink-700 px-4">
          {TABS.map((t) => {
            const active = tab === t.key;
            return (
              <Pressable
                key={t.key}
                onPress={() => setTab(t.key)}
                className="flex-1 items-center pb-2"
              >
                <Text
                  className={`text-[14px] font-semibold ${
                    active ? "text-fg" : "text-fg-faint"
                  }`}
                >
                  {t.label}
                </Text>
                {active ? (
                  <View className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent rounded-t" />
                ) : null}
              </Pressable>
            );
          })}
        </View>

        {tab === "overview" ? <OverviewTab player={player} /> : null}
        {tab === "stats" ? <StatsTab player={player} /> : null}
        {tab === "schedule" ? <ScheduleTab player={player} /> : null}
        {tab === "news" ? <NewsTab player={player} /> : null}
      </ScrollView>

      <BottomNav active="players" />
    </SafeAreaView>
  );
}

/* ---------------- Overview ---------------- */

function OverviewTab({ player }: { player: PlayerDetail }) {
  return (
    <View className="px-4 pt-4 gap-4">
      {/* Game + Outlook/Line row */}
      <View className="flex-row gap-3">
        <GameCard player={player} />
        {player.kind === "goalie" ? (
          <GoalieOutlookCard player={player} />
        ) : (
          <LineRoleCard player={player} />
        )}
      </View>

      {/* Goalie start probability */}
      {player.kind === "goalie" && player.startProbability != null ? (
        <StartProbabilityCard player={player} />
      ) : null}

      {/* Weekly schedule */}
      <WeeklyScheduleCard player={player} />

      {/* Recent */}
      {player.kind === "goalie" ? (
        <RecentGoalieStarts player={player} />
      ) : (
        <RecentSkaterGames player={player} />
      )}

      {/* Season stats */}
      <SeasonStatsCard player={player} />

      {/* News */}
      <NewsCard player={player} />
    </View>
  );
}

function GameCard({ player }: { player: PlayerDetail }) {
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <View className="flex-row items-center justify-between">
        <Text className="text-fg text-[13px] font-bold">{player.gameLabel}</Text>
        <Text className="text-fg-faint text-[11px]">
          {player.gameDate} · {player.gameTime}
        </Text>
      </View>

      <View className="flex-row items-center justify-center gap-4 mt-3">
        <View className="items-center">
          <TeamLogo abbrev={player.team} size={34} />
          <Text className="text-fg text-[13px] font-bold mt-1">
            {player.team}
          </Text>
          <Text className="text-fg-faint text-[10px]">{player.myRecord}</Text>
        </View>
        <Text className="text-fg-muted text-sm font-bold">
          {player.homeAway}
        </Text>
        <View className="items-center">
          <TeamLogo abbrev={player.oppTeam} size={34} />
          <Text className="text-fg text-[13px] font-bold mt-1">
            {player.oppTeam}
          </Text>
          <Text className="text-fg-faint text-[10px]">{player.oppRecord}</Text>
        </View>
      </View>

      <View className="mt-3 pt-3 border-t border-ink-700">
        <Text className="text-fg-faint text-[11px]">Proj. Points</Text>
        <Text className="text-fg text-2xl font-extrabold mt-0.5">
          {player.projPoints.toFixed(1)}
        </Text>
      </View>

      {/* Skater matchup ranks */}
      {player.matchupRanks ? (
        <View className="flex-row gap-2 mt-3">
          {player.matchupRanks.map((r) => (
            <View
              key={r.label}
              className="flex-1 bg-ink-800 rounded-lg py-1.5 items-center"
            >
              <Text className="text-fg-faint text-[9px] font-bold">
                {r.label}
              </Text>
              <Text
                className={`text-[12px] font-bold ${
                  r.bad ? "text-loss" : "text-win"
                }`}
              >
                {r.value}
              </Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function GoalieOutlookCard({ player }: { player: PlayerDetail }) {
  const o = player.goalieOutlook;
  if (!o) return null;
  const rows: [string, string][] = [
    ["Expected Starter", o.expectedStarter],
    ["Confirmed", o.confirmed],
    ["Back-to-Back", o.backToBack],
    ["Opponent Goal Rank", o.oppGoalRank],
    ["Opponent xG", o.oppXg],
    ["Game Total", o.gameTotal],
    ["Projection (Fantrax)", o.projectionFp],
  ];
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <Text className="text-fg text-[13px] font-bold mb-2">Goalie Outlook</Text>
      {rows.map(([label, value]) => (
        <View key={label} className="flex-row justify-between py-[3px]">
          <Text className="text-fg-faint text-[11px]">{label}</Text>
          <Text className="text-fg text-[11px] font-semibold">{value}</Text>
        </View>
      ))}
    </View>
  );
}

function LineRoleCard({ player }: { player: PlayerDetail }) {
  const role = player.lineRole;
  if (!role) return null;
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <Text className="text-fg text-[13px] font-bold mb-2">Line & PP Role</Text>
      {role.map((r) => (
        <View key={r.label} className="flex-row justify-between py-[3px]">
          <Text className="text-fg-faint text-[11px]">{r.label}</Text>
          <Text className="text-fg text-[11px] font-semibold">{r.value}</Text>
        </View>
      ))}
    </View>
  );
}

function StartProbabilityCard({ player }: { player: PlayerDetail }) {
  const pct = player.startProbability ?? 0;
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <View className="flex-row items-center justify-between">
        <Text className="text-fg-faint text-[11px]">Projected Start</Text>
        <View className="bg-win/15 rounded-full px-2.5 py-1">
          <Text className="text-win text-[11px] font-bold">
            {player.startStatusPill}
          </Text>
        </View>
      </View>
      <View className="flex-row items-end gap-2 mt-1.5">
        <Text className="text-fg text-2xl font-extrabold">{pct}%</Text>
      </View>
      {/* Progress bar */}
      <View className="h-2 rounded-full bg-ink-700 mt-2 overflow-hidden">
        <View
          className="h-full rounded-full bg-win"
          style={{ width: `${pct}%` }}
        />
      </View>
    </View>
  );
}

function WeeklyScheduleCard({ player }: { player: PlayerDetail }) {
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <View className="flex-row items-center justify-between mb-2.5">
        <Text className="text-fg text-[13px] font-bold">Weekly Schedule</Text>
        <Text className="text-fg-faint text-[11px]">Week 3 (Oct 7 – Oct 13)</Text>
      </View>
      <View className="flex-row gap-2">
        {player.weekGames.map((g, i) => (
          <View
            key={i}
            className="flex-1 bg-ink-800 rounded-lg py-2 px-1 items-center"
          >
            <Text className="text-fg-faint text-[9px]">{g.day}</Text>
            <Text className="text-fg-faint text-[9px]">{g.date}</Text>
            <Text className="text-fg text-[11px] font-bold mt-1">{g.opp}</Text>
            {g.status ? (
              <View className="flex-row items-center gap-1 mt-1">
                <View
                  className={`w-1.5 h-1.5 rounded-full ${
                    g.status === "tbd" ? "bg-warn" : "bg-win"
                  }`}
                />
                <Text
                  className={`text-[9px] font-bold ${
                    g.status === "tbd" ? "text-warn" : "text-win"
                  }`}
                >
                  {g.status === "likely"
                    ? "Likely"
                    : g.status === "expected"
                      ? "Expected"
                      : "TBD"}
                </Text>
              </View>
            ) : null}
          </View>
        ))}
      </View>
    </View>
  );
}

/* ---------------- Recent ---------------- */

function SectionHeader({ title }: { title: string }) {
  return (
    <View className="flex-row items-center justify-between mb-2">
      <Text className="text-fg text-[15px] font-bold">{title}</Text>
      <View className="flex-row items-center gap-1">
        <Text className="text-fg-muted text-[12px]">View All</Text>
        <ChevronRight color="#5A7186" size={14} />
      </View>
    </View>
  );
}

function RecentSkaterGames({ player }: { player: PlayerDetail }) {
  const games = player.recentSkaterGames ?? [];
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <SectionHeader title="Recent Games" />
      <View className="flex-row py-1.5 border-b border-ink-700">
        {["Date", "Opp", "G", "A", "+/-", "SOG", "Hits", "Blk", "FP"].map(
          (h, i) => (
            <Text
              key={h}
              className={`text-fg-faint text-[10px] font-bold ${
                i === 0 ? "w-[46px]" : i === 1 ? "w-[52px]" : "flex-1 text-right"
              }`}
            >
              {h}
            </Text>
          )
        )}
      </View>
      {games.map((g, i) => (
        <View key={i} className="flex-row py-2 border-b border-ink-700/50">
          <Text className="text-fg-muted text-[11px] w-[46px]">{g.date}</Text>
          <Text className="text-fg-muted text-[11px] w-[52px]">{g.opp}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{g.g}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{g.a}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">
            {g.plusMinus}
          </Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{g.sog}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{g.hits}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{g.blk}</Text>
          <Text className="text-win text-[11px] font-bold flex-1 text-right">
            {g.fp.toFixed(1)}
          </Text>
        </View>
      ))}
    </View>
  );
}

function RecentGoalieStarts({ player }: { player: PlayerDetail }) {
  const starts = player.recentGoalieStarts ?? [];
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <SectionHeader title="Recent Starts" />
      <View className="flex-row py-1.5 border-b border-ink-700">
        {["Date", "Opp", "Result", "GA", "SOG", "SV", "SV%", "FP"].map(
          (h, i) => (
            <Text
              key={h}
              className={`text-fg-faint text-[10px] font-bold ${
                i === 0 ? "w-[44px]" : i === 1 ? "w-[50px]" : i === 2 ? "w-[48px]" : "flex-1 text-right"
              }`}
            >
              {h}
            </Text>
          )
        )}
      </View>
      {starts.map((s, i) => (
        <View key={i} className="flex-row py-2 border-b border-ink-700/50">
          <Text className="text-fg-muted text-[11px] w-[44px]">{s.date}</Text>
          <Text className="text-fg-muted text-[11px] w-[50px]">{s.opp}</Text>
          <Text
            className={`text-[11px] font-semibold w-[48px] ${
              s.result.startsWith("W") ? "text-win" : "text-loss"
            }`}
          >
            {s.result}
          </Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{s.ga}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{s.sog}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{s.sv}</Text>
          <Text className="text-fg text-[11px] flex-1 text-right">{s.svPct}</Text>
          <Text className="text-win text-[11px] font-bold flex-1 text-right">
            {s.fp.toFixed(1)}
          </Text>
        </View>
      ))}
    </View>
  );
}

/* ---------------- Season stats ---------------- */

function SeasonStatsCard({ player }: { player: PlayerDetail }) {
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <SectionHeader title="Season Stats (2024–25)" />
      <View className="flex-row flex-wrap">
        {player.seasonStats.map((s) => (
          <View
            key={s.label}
            className="w-1/4 items-center py-2"
            style={{ minWidth: "22%" }}
          >
            <Text className="text-fg-faint text-[10px] font-bold">
              {s.label}
            </Text>
            <Text className="text-fg text-lg font-extrabold mt-0.5">
              {s.value}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

/* ---------------- News ---------------- */

function NewsCard({ player }: { player: PlayerDetail }) {
  return (
    <View className="bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <SectionHeader title="News" />
      {player.news.map((n) => (
        <View key={n.id} className="flex-row gap-3 py-2.5 border-b border-ink-700/50">
          <View className="w-14 h-14 rounded-lg bg-ink-700 overflow-hidden">
            {n.imageUrl ? (
              <PlayerHeadshot url={n.imageUrl} size={56} />
            ) : null}
          </View>
          <View className="flex-1">
            <Text className="text-fg text-[13px] font-semibold leading-4" numberOfLines={2}>
              {n.title}
            </Text>
            <Text className="text-fg-faint text-[11px] mt-1">
              {n.source} · {n.ago}
            </Text>
          </View>
        </View>
      ))}
    </View>
  );
}

/* ---------------- Other tabs ---------------- */

function StatsTab({ player }: { player: PlayerDetail }) {
  return (
    <View className="px-4 pt-4 gap-4">
      <SeasonStatsCard player={player} />
      {player.kind === "goalie" ? (
        <RecentGoalieStarts player={player} />
      ) : (
        <RecentSkaterGames player={player} />
      )}
    </View>
  );
}

function ScheduleTab({ player }: { player: PlayerDetail }) {
  return (
    <View className="px-4 pt-4 gap-4">
      <GameCard player={player} />
      <WeeklyScheduleCard player={player} />
    </View>
  );
}

function NewsTab({ player }: { player: PlayerDetail }) {
  return (
    <View className="px-4 pt-4">
      <NewsCard player={player} />
    </View>
  );
}
