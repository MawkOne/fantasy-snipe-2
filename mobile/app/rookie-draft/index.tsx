import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  ArrowRight,
  Calendar,
  FileText,
  ListOrdered,
  Users,
} from "lucide-react-native";

import { DraftHeader } from "../../src/components/draft/DraftHeader";
import { BottomNav } from "../../src/components/BottomNav";
import { DraftTabs } from "../../src/components/draft/DraftTabs";
import { TeamEmblem } from "../../src/components/draft/TeamEmblem";
import {
  DRAFT_FORMAT_RULES,
  DRAFT_META,
  DRAFT_ORDER,
  MY_DRAFT_TEAM_ID,
  ROOKIE_ELIGIBILITY,
} from "../../src/data/rookieDraft";

const TABS = ["Overview", "Order", "Rules"] as const;
type HubTab = (typeof TABS)[number];

export default function RookieDraftHub() {
  const router = useRouter();
  const [tab, setTab] = useState<HubTab>("Overview");

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <DraftHeader />
      <DraftTabs tabs={TABS} active={tab} onChange={setTab} />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {tab === "Overview" && <OverviewTab onViewOrder={() => setTab("Order")} onEnterRoom={() => router.push("/rookie-draft/room")} />}
        {tab === "Order" && <OrderTab />}
        {tab === "Rules" && <RulesTab />}
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}

/* ---------------- Overview ---------------- */

function OverviewTab({
  onViewOrder,
  onEnterRoom,
}: {
  onViewOrder: () => void;
  onEnterRoom: () => void;
}) {
  return (
    <View>
      {/* Hero */}
      <View className="mx-4 mt-3 rounded-card bg-ink-850 border border-ink-700 overflow-hidden">
        <View className="h-24 bg-ink-800 items-center justify-center">
          <Text className="text-4xl">🏒🥅</Text>
        </View>
        <View className="p-4">
          <Text className="text-fg text-2xl font-black tracking-tight">
            {DRAFT_META.title.toUpperCase()}
          </Text>
          <Text className="text-fg-muted text-[13px] mt-1.5 leading-5">
            The future starts here. Select the next generation of stars to
            build your franchise.
          </Text>
        </View>
      </View>

      {/* Live banner */}
      <Pressable
        onPress={onEnterRoom}
        className="mx-4 mt-3 bg-accent/10 border border-accent/50 rounded-card p-3.5 flex-row items-center"
      >
        <View className="w-2 h-2 rounded-full bg-loss mr-2.5" />
        <View className="flex-1">
          <Text className="text-fg text-[13px] font-bold">
            The draft is live — you're on the clock!
          </Text>
          <Text className="text-fg-muted text-[11px] mt-0.5">
            Round 1 · Pick 1 of 12
          </Text>
        </View>
        <Text className="text-accent text-[13px] font-bold">Enter</Text>
        <ArrowRight color="#2AB3FF" size={14} />
      </Pressable>

      {/* Info rows */}
      <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card px-4">
        <InfoRow
          icon={<Calendar color="#2AB3FF" size={16} />}
          label="Draft Date"
          lines={[DRAFT_META.date]}
        />
        <InfoRow
          icon={<ListOrdered color="#2AB3FF" size={16} />}
          label="Format"
          lines={[DRAFT_META.format]}
        />
        <InfoRow
          icon={<Users color="#2AB3FF" size={16} />}
          label="Rosters"
          lines={[DRAFT_META.rosters]}
        />
        <InfoRow
          icon={<FileText color="#2AB3FF" size={16} />}
          label="Rules"
          lines={[
            "Max 6 rookies per team *",
            "Rookies do not score points",
            "Max 3 years on rookie roster",
          ]}
          last
        />
      </View>

      {/* CTA */}
      <Pressable
        onPress={onViewOrder}
        className="mx-4 mt-4 bg-accent rounded-full py-3.5 flex-row items-center justify-center gap-2"
      >
        <Text className="text-ink-900 text-[15px] font-bold">
          View Draft Order
        </Text>
        <ArrowRight color="#0A1420" size={16} />
      </Pressable>
    </View>
  );
}

function InfoRow({
  icon,
  label,
  lines,
  last = false,
}: {
  icon: React.ReactNode;
  label: string;
  lines: string[];
  last?: boolean;
}) {
  return (
    <View
      className={`flex-row py-3.5 ${
        last ? "" : "border-b border-ink-700/60"
      }`}
    >
      <View className="w-8 pt-0.5">{icon}</View>
      <View className="flex-1">
        <Text className="text-fg text-[14px] font-bold">{label}</Text>
        {lines.map((line) => (
          <Text
            key={line}
            className="text-fg-muted text-[12px] mt-0.5 leading-4"
          >
            {line}
          </Text>
        ))}
      </View>
    </View>
  );
}

/* ---------------- Order ---------------- */

function OrderTab() {
  return (
    <View>
      <Text className="px-4 pt-4 text-fg-faint text-[11px] font-bold tracking-widest">
        DRAFT ORDER
      </Text>
      <Text className="px-4 pt-1 pb-3 text-fg-muted text-[11px] leading-4">
        Determined by reverse order of standings{"\n"}(Subject to change by
        commissioner)
      </Text>
      {DRAFT_ORDER.map((team, i) => {
        const mine = team.id === MY_DRAFT_TEAM_ID;
        return (
          <View
            key={team.id}
            className={`mx-4 mb-1.5 flex-row items-center rounded-card border px-3 py-2.5 ${
              mine
                ? "border-accent/60 bg-accent/10"
                : "border-ink-700 bg-ink-850"
            }`}
          >
            <Text className="text-fg-faint text-[13px] font-bold w-6">
              {i + 1}
            </Text>
            <TeamEmblem emoji={team.emoji} size={32} />
            <Text className="text-fg text-[14px] font-semibold ml-3 flex-1">
              {team.name}
            </Text>
            {mine && (
              <View className="bg-accent rounded-full px-2 py-0.5">
                <Text className="text-ink-900 text-[9px] font-bold">YOU</Text>
              </View>
            )}
          </View>
        );
      })}
    </View>
  );
}

/* ---------------- Rules ---------------- */

function RulesTab() {
  return (
    <View>
      <RuleSection title="ROOKIE ELIGIBILITY" rules={ROOKIE_ELIGIBILITY} />
      <RuleSection title="DRAFT FORMAT" rules={DRAFT_FORMAT_RULES} />
    </View>
  );
}

function RuleSection({ title, rules }: { title: string; rules: string[] }) {
  return (
    <View className="mt-4">
      <Text className="px-4 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
        {title}
      </Text>
      <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4 gap-2.5">
        {rules.map((rule) => (
          <View key={rule} className="flex-row">
            <View className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 mr-2.5" />
            <Text className="flex-1 text-fg-muted text-[13px] leading-5">
              {rule}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}
