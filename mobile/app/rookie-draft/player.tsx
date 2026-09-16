import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";

import { DraftHeader } from "../../src/components/draft/DraftHeader";
import { DraftStatusBar } from "../../src/components/draft/DraftStatusBar";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";
import { ROOKIE_PLAYERS } from "../../src/data/rookieDraft";
import { makePick } from "../../src/data/draftStore";

export default function DraftPlayerScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const player = ROOKIE_PLAYERS.find((p) => p.id === id);

  if (!player) {
    router.back();
    return null;
  }

  const confirmPick = () => {
    makePick(player);
    router.replace("/rookie-draft/confirmed");
  };

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <DraftHeader />
      <DraftStatusBar />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 16 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Player identity */}
        <View className="items-center mt-5 px-4">
          <View>
            <View className="rounded-full border-2 border-accent/60 p-1">
              <PlayerHeadshot url={player.headshotUrl} size={88} />
            </View>
            <View className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
              <Text className="text-fg text-[9px] font-black">
                {player.nhlTeam}
              </Text>
            </View>
          </View>
          <Text className="text-fg text-[22px] font-extrabold mt-3">
            {player.name}
          </Text>
          <Text className="text-fg-muted text-[13px] mt-0.5">
            {player.position} - {player.nhlTeamName}
          </Text>
        </View>

        {/* Bio stats */}
        <View className="flex-row gap-2 px-4 mt-5">
          <StatCell label="Rank" value={String(player.rank)} />
          <StatCell label="Pos" value={player.position} />
          <StatCell label="Age" value={String(player.age)} />
        </View>
        <View className="flex-row gap-2 px-4 mt-2">
          <StatCell label="Height" value={player.height} />
          <StatCell label="Weight" value={player.weight} />
          <StatCell label="Shoots" value={player.shoots} />
        </View>

        {/* Scouting report */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4">
          <Text className="text-fg text-[14px] font-bold mb-1.5">
            Scouting Report
          </Text>
          <Text className="text-fg-muted text-[13px] leading-5">
            {player.scoutingReport}
          </Text>
        </View>

        {/* NHL comparison */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-4 flex-row items-center justify-between">
          <Text className="text-fg-faint text-[11px] font-bold tracking-widest">
            NHL COMPARISON
          </Text>
          <Text className="text-fg text-[14px] font-bold">
            {player.nhlComparison}
          </Text>
        </View>
      </ScrollView>

      {/* CTAs */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60 gap-2.5">
        <Pressable
          onPress={confirmPick}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">
            Confirm Pick
          </Text>
        </Pressable>
        <Pressable
          onPress={() => router.back()}
          className="rounded-full py-3.5 items-center border border-ink-600 bg-ink-850"
        >
          <Text className="text-fg text-[15px] font-bold">
            Back to Player List
          </Text>
        </Pressable>
      </View>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card py-2.5 items-center">
      <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
        {label}
      </Text>
      <Text className="text-fg text-[14px] font-extrabold mt-0.5">
        {value}
      </Text>
    </View>
  );
}
