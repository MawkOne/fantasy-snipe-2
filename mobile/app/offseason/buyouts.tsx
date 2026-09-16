import { useMemo, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { Check, ChevronRight } from "lucide-react-native";

import { OffseasonNav } from "../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../src/components/BottomNav";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import {
  BUYOUT_CANDIDATES,
  BUYOUT_GROUPS,
  groupForPosition,
  OFFSEASON_YEAR,
  type BuyoutGroup,
} from "../../src/data/offseason";
import {
  getBoughtOut,
  getSelectedIds,
  toggleSelected,
} from "../../src/data/offseasonStore";

export default function BuyoutSelectScreen() {
  const router = useRouter();
  const [group, setGroup] = useState<BuyoutGroup>("All");
  const [, bump] = useState(0);

  const boughtOutIds = getBoughtOut().map((p) => p.id);
  const selectedIds = getSelectedIds();

  const players = useMemo(
    () =>
      BUYOUT_CANDIDATES.filter((p) => {
        if (boughtOutIds.includes(p.id)) return false;
        if (group !== "All" && groupForPosition(p.position) !== group)
          return false;
        return true;
      }),
    [group, boughtOutIds.join(",")]
  );

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title="Buyouts" subtitle={`${OFFSEASON_YEAR} Offseason`} />

      {/* Group filters */}
      <View className="flex-row px-4 gap-2 py-3 border-b border-ink-700/60">
        {BUYOUT_GROUPS.map((g) => {
          const active = group === g;
          return (
            <Pressable
              key={g}
              onPress={() => setGroup(g)}
              className={`px-3.5 py-1.5 rounded-lg border ${
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
                {g}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 16 }}
        showsVerticalScrollIndicator={false}
      >
        {players.map((p) => {
          const selected = selectedIds.includes(p.id);
          return (
            <View
              key={p.id}
              className={`mx-4 mt-2 flex-row items-center rounded-card border p-3 ${
                selected
                  ? "border-accent bg-accent/10"
                  : "border-ink-700 bg-ink-850"
              }`}
            >
              {/* Checkbox */}
              <Pressable
                onPress={() => {
                  toggleSelected(p.id);
                  bump((v) => v + 1);
                }}
                className={`w-6 h-6 rounded-md border-2 items-center justify-center mr-3 ${
                  selected ? "bg-accent border-accent" : "border-ink-600"
                }`}
              >
                {selected && <Check color="#0A1420" size={14} strokeWidth={3} />}
              </Pressable>

              {/* Player → details */}
              <Pressable
                onPress={() =>
                  router.push({
                    pathname: "/offseason/buyout/[id]",
                    params: { id: p.id },
                  })
                }
                className="flex-1 flex-row items-center"
              >
                <PlayerHeadshot url={p.headshotUrl} size={44} />
                <View className="flex-1 ml-3">
                  <Text className="text-fg text-[14px] font-bold">
                    {p.name}
                  </Text>
                  <Text className="text-fg-muted text-[11px] mt-0.5">
                    {p.position} · {p.nhlTeam} · Age {p.age}
                  </Text>
                  <Text className="text-fg-faint text-[11px] mt-0.5">
                    ${p.salary} · {p.yearsRemaining}{" "}
                    {p.yearsRemaining === 1 ? "year" : "years"}
                  </Text>
                </View>
                <ChevronRight color="#5A7186" size={16} />
              </Pressable>
            </View>
          );
        })}
      </ScrollView>

      {/* Review CTA — sits above the BottomNav */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60">
        <Pressable
          disabled={selectedIds.length === 0}
          onPress={() => {
            const first = selectedIds[0];
            if (first)
              router.push({
                pathname: "/offseason/buyout/[id]",
                params: { id: first },
              });
          }}
          className={`rounded-full py-3.5 items-center ${
            selectedIds.length > 0 ? "bg-accent" : "bg-ink-700"
          }`}
        >
          <Text
            className={`text-[15px] font-bold ${
              selectedIds.length > 0 ? "text-ink-900" : "text-fg-faint"
            }`}
          >
            Review Buyout
            {selectedIds.length > 0 ? ` (${selectedIds.length})` : ""}
          </Text>
        </Pressable>
      </View>

      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}
