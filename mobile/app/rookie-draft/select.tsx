import { useMemo, useState } from "react";
import {
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { ChevronDown, Search, X } from "lucide-react-native";

import { DraftHeader } from "../../src/components/draft/DraftHeader";
import { DraftStatusBar } from "../../src/components/draft/DraftStatusBar";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";
import { ROOKIE_PLAYERS } from "../../src/data/rookieDraft";
import { isPlayerDrafted } from "../../src/data/draftStore";

const POSITION_FILTERS = ["All", "F", "D", "G"] as const;
type PositionFilter = (typeof POSITION_FILTERS)[number];

export default function SelectPlayerScreen() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<PositionFilter>("All");

  const players = useMemo(() => {
    return ROOKIE_PLAYERS.filter((p) => {
      if (isPlayerDrafted(p.id)) return false;
      if (position === "F" && !["C", "LW", "RW"].includes(p.position))
        return false;
      if (position === "D" && p.position !== "D") return false;
      if (position === "G" && p.position !== "G") return false;
      if (query.trim()) {
        const q = query.trim().toLowerCase();
        if (!p.name.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [position, query]);

  const openPlayer = (id: string) =>
    router.push({ pathname: "/rookie-draft/player", params: { id } });

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <DraftHeader />
      <DraftStatusBar
        right={
          <Pressable onPress={() => router.back()} className="p-0.5">
            <X color="#8CA3B8" size={20} />
          </Pressable>
        }
      />

      <Text className="px-4 pt-3 pb-2 text-fg text-lg font-extrabold">
        Select a Player
      </Text>

      {/* Search */}
      <View className="mx-4 mb-3 flex-row items-center bg-ink-850 border border-ink-700 rounded-full px-4 py-2.5">
        <Search color="#5A7186" size={16} />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search players..."
          placeholderTextColor="#5A7186"
          className="flex-1 ml-2 text-fg text-sm"
          style={{ outlineStyle: "none" } as never}
        />
      </View>

      {/* Position filters */}
      <View className="flex-row items-center px-4 gap-2 pb-2.5">
        {POSITION_FILTERS.map((pos) => {
          const active = position === pos;
          return (
            <Pressable
              key={pos}
              onPress={() => setPosition(pos)}
              className={`min-w-[40px] items-center px-3 py-1.5 rounded-lg border ${
                active
                  ? "border-accent bg-accent/15"
                  : "border-ink-700 bg-ink-850"
              }`}
            >
              <Text
                className={`text-[12px] font-bold ${
                  active ? "text-accent" : "text-fg-muted"
                }`}
              >
                {pos}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {/* Dropdowns (visual only — mock) */}
      <View className="flex-row px-4 gap-2 pb-3">
        <Pressable className="flex-1 flex-row items-center justify-between bg-ink-850 border border-ink-700 rounded-lg px-3 py-2">
          <Text className="text-fg text-[12px] font-semibold">All Teams</Text>
          <ChevronDown color="#8CA3B8" size={14} />
        </Pressable>
        <Pressable className="flex-1 flex-row items-center justify-between bg-ink-850 border border-ink-700 rounded-lg px-3 py-2">
          <Text className="text-fg text-[12px] font-semibold">Rankings</Text>
          <ChevronDown color="#8CA3B8" size={14} />
        </Pressable>
      </View>

      {/* Player list */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {players.length === 0 ? (
          <View className="items-center py-16">
            <Text className="text-fg-muted text-sm">
              No players match these filters.
            </Text>
          </View>
        ) : (
          players.map((p) => (
            <Pressable
              key={p.id}
              onPress={() => openPlayer(p.id)}
              className="mx-4 mb-2 flex-row items-center bg-ink-850 border border-ink-700 rounded-card p-3"
            >
              <Text className="text-fg-faint text-[13px] font-bold w-5">
                {p.rank}
              </Text>
              <PlayerHeadshot url={p.headshotUrl} size={44} />
              <View className="flex-1 ml-3">
                <Text className="text-fg text-[14px] font-bold">{p.name}</Text>
                <Text className="text-fg-muted text-[11px] mt-0.5">
                  {p.position} - {p.nhlTeam}
                </Text>
                <Text className="text-fg-faint text-[10px] mt-0.5">
                  Rank {p.rank}
                </Text>
              </View>
              <View className="bg-accent rounded-lg px-3.5 py-2">
                <Text className="text-ink-900 text-[12px] font-bold">
                  Select
                </Text>
              </View>
            </Pressable>
          ))
        )}
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}
