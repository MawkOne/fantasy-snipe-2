import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { ArrowRight, BadgeDollarSign, CircleCheck, Clock3, Lock } from "lucide-react-native";

import { OffseasonNav } from "../../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../../src/components/BottomNav";
import { useOffseason } from "../../../src/components/offseason/OffseasonProvider";
import type { DraftTeam } from "../../../src/data/rookieDraft";
import {
  LEAGUE_TEAMS,
  MY_TEAM_ID,
  TEAM_BUYOUT_STATUS,
  TEAM_BUYOUT_SUBMISSIONS,
  TEAM_ROSTER_SNAPSHOTS,
} from "../../../src/data/offseason";

export default function TeamBuyoutDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { completedStages } = useOffseason();

  const team: DraftTeam | undefined = LEAGUE_TEAMS.find((t) => t.id === id);
  if (!team) {
    router.back();
    return null;
  }

  const isMine = team.id === MY_TEAM_ID;
  const myDone = completedStages.includes("buyouts");
  const status =
    team.id === MY_TEAM_ID
      ? myDone
        ? "done"
        : "in_progress"
      : TEAM_BUYOUT_STATUS[team.id] ?? "in_progress";

  // Other teams' submissions stay hidden until the admin submits their own.
  const canViewSubmissions = isMine || myDone;

  const snap = TEAM_ROSTER_SNAPSHOTS[team.id] ?? {
    C: 0,
    W: 0,
    F: 0,
    D: 0,
    G: 0,
    IR: 0,
    salary: 0,
  };
  const overCap = snap.salary > 100;

  const submissions = TEAM_BUYOUT_SUBMISSIONS[team.id];
  const submitted = (submissions ?? []).length;
  const totalCash = (submissions ?? []).reduce((s, b) => s + b.cashCost, 0);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title={team.name} subtitle="Buyout Review" />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Team identity */}
        <View className="mx-4 mt-4 flex-row items-center">
          <View className="w-12 h-12 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-xl">{team.emoji}</Text>
          </View>
          <View className="flex-1 ml-3.5">
            <View className="flex-row items-center gap-2">
              <Text className="text-fg text-[18px] font-extrabold">
                {team.name}
              </Text>
              {isMine && (
                <View className="bg-accent rounded-full px-2 py-0.5">
                  <Text className="text-ink-900 text-[9px] font-bold">YOU</Text>
                </View>
              )}
            </View>
            <Text className="text-fg-muted text-[12px] mt-0.5">
              {status === "done"
                ? canViewSubmissions
                  ? `${submitted} buyout${submitted === 1 ? "" : "s"} submitted`
                  : "Buyouts submitted"
                : "Buyouts in progress"}
            </Text>
          </View>
        </View>

        {/* Roster snapshot */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          ROSTER
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4 py-3">
          <Text className="text-fg text-[13px] font-semibold">
            {snap.C}C · {snap.W}W · {snap.F}F · {snap.D}D · {snap.G}G ·{" "}
            {snap.IR}IR
          </Text>
          <View className="flex-row items-center justify-between mt-2 pt-2 border-t border-ink-700/60">
            <Text className="text-fg-muted text-[12px]">Total Salary</Text>
            <Text
              className={`text-[14px] font-extrabold ${
                overCap ? "text-loss" : "text-win"
              }`}
            >
              ${snap.salary}
            </Text>
          </View>
        </View>

        {/* Status */}
        {status === "done" ? (
          <View className="mx-4 mt-3 flex-row items-center gap-2 bg-win/10 border border-win/30 rounded-card px-3.5 py-3">
            <CircleCheck color="#22C55E" size={16} />
            <Text className="text-win text-[12px] font-bold">
              Buyouts submitted
            </Text>
          </View>
        ) : (
          <View className="mx-4 mt-3 flex-row items-center gap-2 bg-warn/10 border border-warn/30 rounded-card px-3.5 py-3">
            <Clock3 color="#F59E0B" size={16} />
            <Text className="text-warn text-[12px] font-bold">
              Buyouts in progress — no submissions yet
            </Text>
          </View>
        )}

        {/* Submissions */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          {submitted > 0 ? "SUBMITTED BUYOUTS" : "SUBMISSIONS"}
        </Text>
        {!canViewSubmissions ? (
          <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-5 items-center">
            <Lock color="#5A7186" size={22} />
            <Text className="text-fg-muted text-[13px] font-semibold mt-2">
              Submissions hidden
            </Text>
            <Text className="text-fg-faint text-[11px] mt-1 text-center leading-5">
              Other GMs{"'"} buyouts unlock once you submit your own.
            </Text>
          </View>
        ) : status === "done" && submitted > 0 ? (
          <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4">
            {submissions!.map((b, i) => (
              <View
                key={b.id}
                className={`flex-row items-center justify-between py-3 ${
                  i < submissions!.length - 1
                    ? "border-b border-ink-700/60"
                    : ""
                }`}
              >
                <View className="flex-1">
                  <Text className="text-fg text-[13px] font-bold">
                    {b.playerName}
                  </Text>
                  <Text className="text-fg-muted text-[11px] mt-0.5">
                    {b.position} · ${b.salary} × {b.yearsRemaining}yr
                  </Text>
                </View>
                <View className="items-end ml-3">
                  <Text className="text-loss text-[13px] font-extrabold">
                    ${b.cashCost}
                  </Text>
                  <Text className="text-fg-faint text-[10px] mt-0.5">
                    cap hit ${b.capHit}
                  </Text>
                </View>
              </View>
            ))}

            {/* Totals */}
            <View className="flex-row items-center justify-between py-3 border-t border-ink-700/60">
              <Text className="text-fg-muted text-[12px]">
                Total cash ({submitted} buyouts)
              </Text>
              <Text className="text-loss text-[14px] font-extrabold">
                ${totalCash}
              </Text>
            </View>
          </View>
        ) : (
          <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4 items-center">
            <BadgeDollarSign color="#5A7186" size={22} />
            <Text className="text-fg-muted text-[12px] mt-2 text-center leading-5">
              No buyouts submitted yet.
            </Text>
          </View>
        )}

        {/* My team CTA */}
        {isMine && status === "in_progress" && (
          <Pressable
            onPress={() => router.push("/offseason/buyouts")}
            className="mx-4 mt-4 bg-accent rounded-full py-3.5 flex-row items-center justify-center gap-2"
          >
            <Text className="text-ink-900 text-[15px] font-bold">
              Manage My Buyouts
            </Text>
            <ArrowRight color="#0A1420" size={16} />
          </Pressable>
        )}
      </ScrollView>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}