import { useCallback, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useFocusEffect, useRouter } from "expo-router";
import {
  CircleCheck,
  Download,
  ListOrdered,
  Trophy,
  Users,
} from "lucide-react-native";

import { DraftHeader } from "../../src/components/draft/DraftHeader";
import { DraftTabs } from "../../src/components/draft/DraftTabs";
import { TeamEmblem } from "../../src/components/draft/TeamEmblem";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";
import {
  DRAFT_META,
  DRAFT_ORDER,
  WHATS_NEXT,
} from "../../src/data/rookieDraft";
import {
  getCurrentOverall,
  getPicks,
  getUpcoming,
  isMyPick,
  teamForOverall,
} from "../../src/data/draftStore";

const TABS = ["Live", "Picks", "Results"] as const;
type RoomTab = (typeof TABS)[number];

export default function DraftRoomScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<RoomTab>("Live");

  // Re-sync from the store whenever the room regains focus.
  const [, bump] = useState(0);
  useFocusEffect(useCallback(() => bump((v) => v + 1), []));

  const overall = getCurrentOverall();
  const onClock = teamForOverall(overall);
  const mine = isMyPick();
  const picks = getPicks();
  const upcoming = getUpcoming(4);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <DraftHeader live />
      <DraftTabs tabs={TABS} active={tab} onChange={setTab} />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {tab === "Live" && (
          <LiveTab
            onClock={onClock}
            mine={mine}
            upcoming={upcoming}
            recentPicks={[...picks].reverse()}
            onViewPlayers={() => router.push("/rookie-draft/select")}
          />
        )}
        {tab === "Picks" && <PicksTab currentOverall={overall} />}
        {tab === "Results" && (
          <ResultsTab
            onViewPicks={() => setTab("Picks")}
            onViewRosters={() => router.push("/franchise")}
          />
        )}
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}

/* ---------------- Live ---------------- */

function LiveTab({
  onClock,
  mine,
  upcoming,
  recentPicks,
  onViewPlayers,
}: {
  onClock: ReturnType<typeof teamForOverall>;
  mine: boolean;
  upcoming: ReturnType<typeof teamForOverall>[];
  recentPicks: ReturnType<typeof getPicks>;
  onViewPlayers: () => void;
}) {
  return (
    <View>
      {/* Round / pick (design screen 4) */}
      <View className="items-center mt-4">
        <Text className="text-fg text-[13px] font-bold">
          Round {onClock.round} ·{" "}
          <Text className="text-accent">Pick {onClock.pickInRound}/12</Text>
        </Text>
      </View>

      {/* On the clock */}
      <Text className="text-accent text-[13px] font-bold text-center mt-2">
        On the Clock
      </Text>
      <View className="mx-4 mt-2 bg-ink-850 border border-accent/60 rounded-card px-4 py-3.5 flex-row items-center justify-center gap-3">
        <TeamEmblem emoji={onClock.team.emoji} size={36} />
        <Text className="text-fg text-[16px] font-extrabold">
          {onClock.team.name}
        </Text>
      </View>

      {/* Upcoming */}
      <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
        UPCOMING
      </Text>
      {upcoming.map((slot) => (
        <View
          key={slot.overall}
          className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-3 py-2.5"
        >
          <Text className="text-fg-faint text-[12px] font-bold w-6">
            {slot.overall}
          </Text>
          <TeamEmblem emoji={slot.team.emoji} size={30} />
          <Text className="text-fg text-[13px] font-semibold ml-3">
            {slot.team.name}
          </Text>
        </View>
      ))}

      {/* Your pick CTA */}
      {mine && (
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4 items-center">
          <Text className="text-fg text-[15px] font-extrabold">
            You're on the clock!
          </Text>
          <Text className="text-fg-muted text-[12px] mt-1">
            Select a player to make your pick.
          </Text>
          <Pressable
            onPress={onViewPlayers}
            className="mt-3.5 bg-accent rounded-full py-3 self-stretch items-center"
          >
            <Text className="text-ink-900 text-[14px] font-bold">
              View Available Players
            </Text>
          </Pressable>
        </View>
      )}

      {/* Recent picks */}
      {recentPicks.length > 0 && (
        <>
          <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
            RECENT PICKS
          </Text>
          {recentPicks.map((pick) => (
            <View
              key={pick.overall}
              className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-3 py-2.5"
            >
              <Text className="text-fg-faint text-[12px] font-bold w-6">
                {pick.overall}
              </Text>
              <TeamEmblem emoji={pick.team.emoji} size={30} />
              <Text className="text-fg-muted text-[13px] font-semibold ml-3 flex-1">
                {pick.team.name}
              </Text>
              <View className="items-end">
                <Text className="text-fg text-[13px] font-bold">
                  {pick.player.name}
                </Text>
                <Text className="text-fg-faint text-[10px] mt-0.5">
                  {pick.player.position} - {pick.player.nhlTeam}
                </Text>
              </View>
            </View>
          ))}
        </>
      )}
    </View>
  );
}

/* ---------------- Picks ---------------- */

function PicksTab({ currentOverall }: { currentOverall: number }) {
  const picks = getPicks();

  return (
    <View>
      {Array.from({ length: DRAFT_META.rounds }, (_, r) => {
        const round = r + 1;
        return (
          <View key={round}>
            <Text className="px-4 pt-4 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
              ROUND {round}
            </Text>
            {Array.from({ length: DRAFT_ORDER.length }, (_, i) => {
              const overall = r * DRAFT_ORDER.length + i + 1;
              const { team } = teamForOverall(overall);
              const made = picks.find((p) => p.overall === overall);
              const isCurrent = overall === currentOverall;
              return (
                <View
                  key={overall}
                  className={`mx-4 mb-1.5 flex-row items-center rounded-card border px-3 py-2.5 ${
                    isCurrent
                      ? "border-accent/60 bg-accent/10"
                      : "border-ink-700 bg-ink-850"
                  }`}
                >
                  <Text className="text-fg-faint text-[12px] font-bold w-6">
                    {i + 1}
                  </Text>
                  <TeamEmblem emoji={team.emoji} size={30} />
                  <Text className="text-fg-muted text-[13px] font-semibold ml-3 flex-1">
                    {team.name}
                  </Text>
                  {made ? (
                    <View className="flex-row items-center">
                      <View className="items-end mr-2.5">
                        <Text className="text-fg text-[13px] font-bold">
                          {made.player.name}
                        </Text>
                        <Text className="text-fg-faint text-[10px] mt-0.5">
                          {made.player.position} - {made.player.nhlTeam}
                        </Text>
                      </View>
                      <PlayerHeadshot
                        url={made.player.headshotUrl}
                        size={30}
                      />
                    </View>
                  ) : isCurrent ? (
                    <Text className="text-accent text-[12px] font-bold">
                      On the clock...
                    </Text>
                  ) : (
                    <Text className="text-fg-faint text-[12px]">
                      Upcoming...
                    </Text>
                  )}
                </View>
              );
            })}
          </View>
        );
      })}
    </View>
  );
}

/* ---------------- Results ---------------- */

function ResultsTab({
  onViewPicks,
  onViewRosters,
}: {
  onViewPicks: () => void;
  onViewRosters: () => void;
}) {
  const [downloaded, setDownloaded] = useState(false);

  return (
    <View className="px-4">
      <View className="items-center mt-8">
        <View className="w-20 h-20 rounded-full bg-warn/15 border border-warn/30 items-center justify-center">
          <Trophy color="#F59E0B" size={38} />
        </View>
        <Text className="text-fg text-2xl font-black tracking-wide mt-4">
          DRAFT COMPLETE
        </Text>
        <Text className="text-fg-muted text-[13px] mt-1">
          2025 Rookie Draft
        </Text>
      </View>

      <View className="mt-6 gap-2">
        <ResultsButton
          icon={<ListOrdered color="#2AB3FF" size={16} />}
          label="View All Picks"
          onPress={onViewPicks}
        />
        <ResultsButton
          icon={<Users color="#2AB3FF" size={16} />}
          label="Team Rosters"
          onPress={onViewRosters}
        />
        <ResultsButton
          icon={
            downloaded ? (
              <CircleCheck color="#22C55E" size={16} />
            ) : (
              <Download color="#2AB3FF" size={16} />
            )
          }
          label={downloaded ? "Results Saved" : "Download Results"}
          onPress={() => setDownloaded(true)}
        />
      </View>

      <View className="mt-5 bg-ink-850 border border-ink-700 rounded-card p-4">
        <Text className="text-fg text-[14px] font-bold mb-2.5">
          What's Next?
        </Text>
        {WHATS_NEXT.map((item) => (
          <View key={item} className="flex-row items-center mb-2">
            <CircleCheck color="#22C55E" size={15} />
            <Text className="text-fg-muted text-[13px] ml-2.5">{item}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function ResultsButton({
  icon,
  label,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  onPress?: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      className="flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-4 py-3.5"
    >
      {icon}
      <Text className="text-fg text-[14px] font-semibold ml-3">{label}</Text>
    </Pressable>
  );
}
