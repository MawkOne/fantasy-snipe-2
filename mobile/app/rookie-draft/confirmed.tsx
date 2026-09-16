import { Pressable, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import { DraftHeader } from "../../src/components/draft/DraftHeader";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";
import { getLastPick, teamForOverall } from "../../src/data/draftStore";

// Fixed confetti pieces (deterministic so they don't jump on re-render).
const CONFETTI = [
  { left: "12%", top: "18%", color: "#2AB3FF", rotate: "24deg" },
  { left: "22%", top: "30%", color: "#F59E0B", rotate: "-30deg" },
  { left: "8%", top: "44%", color: "#22C55E", rotate: "45deg" },
  { left: "30%", top: "14%", color: "#EF4444", rotate: "-15deg" },
  { left: "70%", top: "16%", color: "#22C55E", rotate: "30deg" },
  { left: "84%", top: "28%", color: "#2AB3FF", rotate: "-40deg" },
  { left: "90%", top: "46%", color: "#F59E0B", rotate: "20deg" },
  { left: "76%", top: "52%", color: "#A78BFA", rotate: "-24deg" },
  { left: "16%", top: "58%", color: "#A78BFA", rotate: "40deg" },
  { left: "88%", top: "12%", color: "#EF4444", rotate: "15deg" },
] as const;

export default function PickConfirmedScreen() {
  const router = useRouter();
  const pick = getLastPick();

  if (!pick) {
    router.back();
    return null;
  }

  const next = teamForOverall(pick.overall + 1);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <DraftHeader />

      <View className="flex-1 items-center justify-center px-6">
        {/* Confetti */}
        {CONFETTI.map((c, i) => (
          <View
            key={i}
            style={{
              position: "absolute",
              left: c.left,
              top: c.top,
              width: 7,
              height: 7,
              borderRadius: 2,
              backgroundColor: c.color,
              transform: [{ rotate: c.rotate }],
              opacity: 0.9,
            }}
          />
        ))}

        <View className="rounded-full border-2 border-accent p-1.5">
          <PlayerHeadshot url={pick.player.headshotUrl} size={110} />
        </View>

        <Text className="text-accent text-[11px] font-bold tracking-widest mt-5">
          PICK CONFIRMED
        </Text>
        <Text className="text-fg-muted text-[13px] mt-2">
          {pick.team.name} select
        </Text>
        <Text className="text-fg text-[26px] font-black tracking-tight mt-1 text-center">
          {pick.player.name}
        </Text>
        <Text className="text-fg-muted text-[13px] mt-1">
          {pick.player.position} - {pick.player.nhlTeamName}
        </Text>
      </View>

      <View className="px-6 pb-8">
        <Pressable
          onPress={() => router.dismissTo("/rookie-draft/room")}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[15px] font-bold">Continue</Text>
        </Pressable>
        <Text className="text-fg-faint text-[12px] text-center mt-3">
          Next Pick: {next.team.name}
        </Text>
      </View>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}
