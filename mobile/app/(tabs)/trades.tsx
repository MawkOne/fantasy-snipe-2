import { useState } from "react";
import {
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  ArrowLeftRight,
  ChevronDown,
  ChevronRight,
  Clock,
  MessageSquare,
  Plus,
  Search,
} from "lucide-react-native";

import {
  MARKET_PICKS,
  MARKET_TARGETS,
  MY_AVAILABLE_ASSETS,
  MY_LEAGUE,
  MY_TEAM_NEEDS,
  TEAM_NEEDS,
  TRADE_CONVERSATIONS,
  type ConversationStatus,
  type MarketTag,
} from "../../src/data/mock";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";

type TradesTab = "conversations" | "market" | "needs" | "activity";

const TABS: { id: TradesTab; label: string }[] = [
  { id: "conversations", label: "Conversations" },
  { id: "market", label: "Market" },
  { id: "needs", label: "Team Needs" },
  { id: "activity", label: "Activity" },
];

export default function TradesHomeScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<TradesTab>("conversations");

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 pt-2 pb-3">
        <View className="flex-row items-center gap-3">
          <View className="w-11 h-11 rounded-full bg-ink-700 border border-ink-600 items-center justify-center">
            <Text className="text-accent text-lg font-black">🐻‍❄️</Text>
          </View>
          <View>
            <View className="flex-row items-center gap-1">
              <Text className="text-fg text-xl font-extrabold tracking-tight">
                Trades
              </Text>
            </View>
            <Text className="text-fg-muted text-xs mt-0.5">
              {MY_LEAGUE.name}
            </Text>
          </View>
        </View>
      </View>

      {/* Tabs */}
      <View className="flex-row px-4 gap-2 pb-3 border-b border-ink-700/60">
        {TABS.map((t) => (
          <Pressable
            key={t.id}
            onPress={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-full border ${
              tab === t.id
                ? "border-accent bg-accent/15"
                : "border-transparent"
            }`}
          >
            <Text
              className={`text-[13px] font-semibold ${
                tab === t.id ? "text-accent" : "text-fg-muted"
              }`}
            >
              {t.label}
            </Text>
          </Pressable>
        ))}
      </View>

      {tab === "conversations" && <ConversationsTab />}
      {tab === "market" && <MarketTab />}
      {tab === "needs" && <TeamNeedsTab />}
      {tab === "activity" && <ActivityTab router={router} />}
    </SafeAreaView>
  );
}

/* ---------------- Conversations (screen 17) ---------------- */

function ConversationsTab() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<ConversationStatus | "All">("All");

  const counts = {
    All: TRADE_CONVERSATIONS.length,
    Active: TRADE_CONVERSATIONS.filter((c) => c.status === "Active").length,
    Waiting: TRADE_CONVERSATIONS.filter((c) => c.status === "Waiting").length,
    Closed: TRADE_CONVERSATIONS.filter((c) => c.status === "Closed").length,
  };

  const filtered = TRADE_CONVERSATIONS.filter((c) => {
    if (filter !== "All" && c.status !== filter) return false;
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      return (
        c.manager.toLowerCase().includes(q) ||
        c.teamName.toLowerCase().includes(q) ||
        c.playerFocus.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const sections: ConversationStatus[] = ["Active", "Waiting", "Closed"];

  return (
    <View className="flex-1">
      {/* Search */}
      <View className="mx-4 mt-3 mb-3 flex-row items-center bg-ink-850 border border-ink-700 rounded-full px-4 py-2.5">
        <Search color="#5A7186" size={16} />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search conversations..."
          placeholderTextColor="#5A7186"
          className="flex-1 ml-2 text-fg text-sm"
          style={{ outlineStyle: "none" } as never}
        />
      </View>

      {/* Start a conversation CTA */}
      <View className="px-4 pb-3">
        <Pressable
          onPress={() => router.push("/trades/builder")}
          className="flex-row items-center justify-center gap-2 bg-accent rounded-full py-3.5"
        >
          <MessageSquare color="#0A1420" size={16} />
          <Text className="text-ink-900 text-[15px] font-bold">
            Start a Trade Conversation
          </Text>
        </Pressable>
      </View>

      {/* Status filter pills */}
      <View className="flex-row px-4 gap-2 pb-3">
        {(["All", "Active", "Waiting", "Closed"] as const).map((f) => {
          const active = filter === f;
          return (
            <Pressable
              key={f}
              onPress={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-full border ${
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
                {f} ({counts[f]})
              </Text>
            </Pressable>
          );
        })}
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {filter === "All" ? (
          sections.map((section) => {
            const rows = filtered.filter((c) => c.status === section);
            if (rows.length === 0) return null;
            return (
              <View key={section}>
                <Text className="px-4 pt-2 pb-2 text-fg text-[13px] font-bold">
                  {section === "Active"
                    ? "Active Conversations"
                    : section === "Waiting"
                      ? "Waiting for a Reply"
                      : "Closed Conversations"}
                </Text>
                {rows.map((c) => (
                  <ConversationRow key={c.id} convo={c} />
                ))}
              </View>
            );
          })
        ) : (
          filtered.map((c) => <ConversationRow key={c.id} convo={c} />)
        )}
        {filtered.length === 0 && (
          <View className="items-center py-16">
            <Text className="text-fg-muted text-sm">No conversations.</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function ConversationRow({ convo }: { convo: (typeof TRADE_CONVERSATIONS)[number] }) {
  const router = useRouter();
  const statusColor =
    convo.status === "Active"
      ? "bg-win/15 text-win"
      : convo.status === "Waiting"
        ? "bg-warn/15 text-warn"
        : "bg-ink-700 text-fg-faint";

  return (
    <Pressable
      onPress={() => router.push("/trades/detail")}
      className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center"
    >
      <View className="w-11 h-11 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
        <Text className="text-xl">{convo.emoji}</Text>
      </View>
      <View className="flex-1 ml-3">
        <View className="flex-row items-center justify-between">
          <Text className="text-fg text-[13px] font-bold" numberOfLines={1}>
            {convo.manager} · {convo.teamName}
          </Text>
          <View className="flex-row items-center gap-1.5">
            <View className={`rounded-full px-2 py-0.5 ${statusColor.split(" ")[0]}`}>
              <Text className={`text-[9px] font-bold ${statusColor.split(" ")[1]}`}>
                {convo.status.toUpperCase()}
              </Text>
            </View>
            <Text className="text-fg-faint text-[10px]">{convo.ago}</Text>
          </View>
        </View>
        <Text className="text-fg text-[12px] font-semibold mt-0.5">
          {convo.playerFocus}
        </Text>
        <Text className="text-fg-muted text-[11px] mt-0.5" numberOfLines={2}>
          {convo.preview}
        </Text>
      </View>
      <ChevronRight color="#5A7186" size={16} />
    </Pressable>
  );
}

/* ---------------- Dynasty Trade Market (screen 18) ---------------- */

type MarketSubTab = "Players" | "Draft Picks" | "Teams" | "My Team";
type MarketFilter = "All" | "Available" | "Rentals" | "Prospects" | "Picks";

function MarketTab() {
  const [query, setQuery] = useState("");
  const [subTab, setSubTab] = useState<MarketSubTab>("Players");
  const [filter, setFilter] = useState<MarketFilter>("All");

  return (
    <View className="flex-1">
      {/* Search */}
      <View className="mx-4 mt-3 mb-3 flex-row items-center bg-ink-850 border border-ink-700 rounded-full px-4 py-2.5">
        <Search color="#5A7186" size={16} />
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search players, teams, or needs..."
          placeholderTextColor="#5A7186"
          className="flex-1 ml-2 text-fg text-sm"
          style={{ outlineStyle: "none" } as never}
        />
      </View>

      {/* Sub tabs */}
      <View className="flex-row px-4 gap-2 pb-3 border-b border-ink-700/60">
        {(["Players", "Draft Picks", "Teams", "My Team"] as MarketSubTab[]).map(
          (s) => (
            <Pressable
              key={s}
              onPress={() => setSubTab(s)}
              className={`px-2.5 py-1.5 rounded-full ${
                subTab === s ? "bg-accent/15" : ""
              }`}
            >
              <Text
                className={`text-[13px] font-semibold ${
                  subTab === s ? "text-accent" : "text-fg-muted"
                }`}
              >
                {s}
              </Text>
            </Pressable>
          )
        )}
      </View>

      {/* Filter pills */}
      <View className="flex-row px-4 gap-2 py-3">
        {(["All", "Available", "Rentals", "Prospects", "Picks"] as MarketFilter[]).map(
          (f) => {
            const active = filter === f;
            return (
              <Pressable
                key={f}
                onPress={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-full border ${
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
                  {f}
                </Text>
              </Pressable>
            );
          }
        )}
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {subTab === "Players" && (
          <>
            <View className="flex-row items-center justify-between px-4 pb-2">
              <Text className="text-fg text-[13px] font-bold">
                Featured Trade Targets
              </Text>
              <Text className="text-accent text-[11px] font-semibold">
                See All
              </Text>
            </View>
            {MARKET_TARGETS.map((target) => (
              <MarketTargetRow key={target.id} target={target} />
            ))}
          </>
        )}

        {subTab === "Draft Picks" && (
          <>
            <View className="flex-row items-center justify-between px-4 pb-2">
              <Text className="text-fg text-[13px] font-bold">Draft Picks</Text>
              <Text className="text-accent text-[11px] font-semibold">
                See All
              </Text>
            </View>
            {MARKET_PICKS.map((pick) => (
              <View
                key={pick.id}
                className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5"
              >
                <View className="flex-row items-center justify-between">
                  <Text className="text-fg text-[13px] font-bold">
                    {pick.label}
                  </Text>
                  <MarketTagPill tag={pick.statusTag} />
                </View>
                <Text className="text-fg-muted text-[11px] mt-1">
                  {pick.ownerTeam}
                </Text>
                <Text className="text-fg-faint text-[11px] mt-0.5">
                  Looking for {pick.lookingFor}
                </Text>
              </View>
            ))}
          </>
        )}

        {subTab === "Teams" && (
          <>
            <Text className="px-4 pb-2 text-fg text-[13px] font-bold">
              All Teams
            </Text>
            {TEAM_NEEDS.map((t) => (
              <TeamNeedsRow key={t.id} needs={t} />
            ))}
          </>
        )}

        {subTab === "My Team" && (
          <View>
            <Text className="px-4 pb-2 text-fg text-[13px] font-bold">
              Harbour Ice
            </Text>
            <View className="mx-4 mb-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
              <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1.5">
                LOOKING FOR
              </Text>
              <View className="flex-row flex-wrap gap-1.5 mb-3">
                {MY_TEAM_NEEDS.lookingFor.map((n) => (
                  <View
                    key={n}
                    className="bg-accent/15 border border-accent/40 rounded-full px-2.5 py-1"
                  >
                    <Text className="text-accent text-[11px] font-semibold">
                      {n}
                    </Text>
                  </View>
                ))}
              </View>
              <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1.5">
                WILLING TO MOVE
              </Text>
              <View className="flex-row flex-wrap gap-1.5">
                {MY_TEAM_NEEDS.offering.map((n) => (
                  <View
                    key={n}
                    className="bg-ink-800 border border-ink-600 rounded-full px-2.5 py-1"
                  >
                    <Text className="text-fg-muted text-[11px] font-semibold">
                      {n}
                    </Text>
                  </View>
                ))}
              </View>
            </View>

            <Text className="px-4 pb-2 text-fg text-[13px] font-bold">
              On Your Trade Block
            </Text>
            {MY_AVAILABLE_ASSETS.slice(8).map((a) => (
              <View
                key={a.id}
                className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-3 py-2.5"
              >
                {a.kind === "player" ? (
                  <PlayerHeadshot url={a.headshotUrl} size={32} />
                ) : (
                  <View className="w-8 h-8 rounded-full bg-ink-700 items-center justify-center">
                    <Text className="text-sm">🎟️</Text>
                  </View>
                )}
                <View className="flex-1 ml-2.5">
                  <Text className="text-fg text-[13px] font-bold">
                    {a.name}
                  </Text>
                  <Text className="text-fg-faint text-[10px] mt-0.5">
                    {a.detail}
                  </Text>
                </View>
                {a.projectedPoints ? (
                  <Text className="text-fg-muted text-[11px]">
                    {a.projectedPoints.toFixed(1)} proj
                  </Text>
                ) : null}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

/* ---------------- Team Needs (tab) ---------------- */

function TeamNeedsTab() {
  return (
    <ScrollView
      className="flex-1"
      contentContainerStyle={{ paddingBottom: 24 }}
      showsVerticalScrollIndicator={false}
    >
      {/* My needs */}
      <Text className="px-4 pt-3 pb-2 text-fg-faint text-[10px] font-bold tracking-widest">
        YOUR TEAM
      </Text>
      <View className="mx-4 mb-3 bg-ink-850 border border-accent/50 rounded-card p-3.5">
        <View className="flex-row items-center gap-2 mb-2.5">
          <Text className="text-xl">🐻‍❄️</Text>
          <Text className="text-fg text-[14px] font-bold">Harbour Ice</Text>
          <View className="bg-win/15 rounded-full px-2 py-0.5">
            <Text className="text-win text-[9px] font-bold">WIN NOW</Text>
          </View>
        </View>
        <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1.5">
          LOOKING FOR
        </Text>
        <View className="flex-row flex-wrap gap-1.5 mb-2.5">
          {MY_TEAM_NEEDS.lookingFor.map((n) => (
            <View
              key={n}
              className="bg-accent/15 border border-accent/40 rounded-full px-2.5 py-1"
            >
              <Text className="text-accent text-[11px] font-semibold">{n}</Text>
            </View>
          ))}
        </View>
        <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1.5">
          WILLING TO MOVE
        </Text>
        <View className="flex-row flex-wrap gap-1.5">
          {MY_TEAM_NEEDS.offering.map((n) => (
            <View
              key={n}
              className="bg-ink-800 border border-ink-600 rounded-full px-2.5 py-1"
            >
              <Text className="text-fg-muted text-[11px] font-semibold">
                {n}
              </Text>
            </View>
          ))}
        </View>
      </View>

      {/* Around the league */}
      <Text className="px-4 pt-1 pb-2 text-fg-faint text-[10px] font-bold tracking-widest">
        AROUND THE LEAGUE
      </Text>
      {TEAM_NEEDS.map((t) => (
        <TeamNeedsRow key={t.id} needs={t} />
      ))}
    </ScrollView>
  );
}

function TeamNeedsRow({ needs }: { needs: (typeof TEAM_NEEDS)[number] }) {
  const strategyColor =
    needs.strategy === "Win Now"
      ? "text-win"
      : needs.strategy === "Rebuild"
        ? "text-accent"
        : "text-warn";
  return (
    <View className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <View className="flex-row items-center gap-2">
        <Text className="text-xl">{needs.emoji}</Text>
        <Text className="flex-1 text-fg text-[13px] font-bold" numberOfLines={1}>
          {needs.team}
        </Text>
        <Text className={`text-[10px] font-bold ${strategyColor}`}>
          {needs.strategy}
        </Text>
      </View>
      <Text className="text-fg-muted text-[11px] mt-1.5">
        <Text className="text-fg-faint font-semibold">Wants:</Text>{" "}
        {needs.lookingFor}
      </Text>
      <Text className="text-fg-muted text-[11px] mt-0.5">
        <Text className="text-fg-faint font-semibold">Offers:</Text>{" "}
        {needs.offering}
      </Text>
    </View>
  );
}

function MarketTargetRow({ target }: { target: (typeof MARKET_TARGETS)[number] }) {
  return (
    <View className="mx-4 mb-2 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      <View className="flex-row items-center">
        <PlayerHeadshot url={target.headshotUrl} size={44} />
        <View className="flex-1 ml-3">
          <Text className="text-fg text-[14px] font-bold">
            {target.playerName}
          </Text>
          <Text className="text-fg-muted text-[11px] mt-0.5">
            {target.position} · {target.team}
          </Text>
          <View className="flex-row gap-1.5 mt-1.5">
            <MarketTagPill tag={target.statusTag} />
            <MarketTagPill tag={target.ownerTag} subtle />
          </View>
        </View>
        <View className="items-end">
          <View className="w-8 h-8 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-base">{target.ownerEmoji}</Text>
          </View>
          <Text className="text-fg text-[10px] font-bold mt-1">
            {target.ownerTeam}
          </Text>
          <Text className="text-accent text-[9px] font-semibold">
            {target.ownerStrategy}
          </Text>
        </View>
      </View>
      <Text className="text-fg-faint text-[11px] mt-2">
        <Text className="font-semibold text-fg-muted">Looking for</Text>{" "}
        {target.lookingFor}
      </Text>
    </View>
  );
}

function MarketTagPill({ tag, subtle = false }: { tag: MarketTag; subtle?: boolean }) {
  const styles: Record<MarketTag, string> = {
    Available: "bg-win/15 text-win",
    Listening: "bg-accent/15 text-accent",
    Rental: "bg-warn/15 text-warn",
    Core: "bg-ink-700 text-fg-muted",
    Rebuild: "bg-accent/15 text-accent",
  };
  const cls = styles[tag] ?? "bg-ink-700 text-fg-muted";
  const [bg, fg] = cls.split(" ");
  return (
    <View className={`rounded-full px-2 py-0.5 ${bg}`}>
      <Text className={`text-[9px] font-bold ${fg}`}>{tag}</Text>
    </View>
  );
}

/* ---------------- Activity (existing content) ---------------- */

function ActivityTab({ router }: { router: ReturnType<typeof useRouter> }) {
  return (
    <ScrollView
      className="flex-1"
      contentContainerStyle={{ paddingBottom: 24 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Propose Trade CTA */}
      <View className="px-4 pt-3 pb-4">
        <Pressable
          onPress={() => router.push("/trades/builder")}
          className="flex-row items-center justify-center gap-2 bg-accent rounded-full py-3.5"
        >
          <Plus color="#0A1420" size={18} />
          <Text className="text-ink-900 text-[15px] font-bold">
            Propose Trade
          </Text>
        </Pressable>
      </View>

      {/* Active Trade */}
      <View className="px-4 pb-2">
        <Text className="text-fg text-[15px] font-bold">Active Trades</Text>
      </View>

      <Pressable
        onPress={() => router.push("/trades/detail")}
        className="mx-4 mb-2 bg-ink-850 border border-accent/50 rounded-card p-3.5"
      >
        <View className="flex-row items-center justify-between mb-2.5">
          <View className="flex-row items-center gap-2">
            <Text className="text-xl">🏴‍☠️</Text>
            <View>
              <Text className="text-fg text-[13px] font-bold">
                Puck Pirates
              </Text>
              <Text className="text-fg-faint text-[10px]">
                Jamie · 2h ago
              </Text>
            </View>
          </View>
          <View className="flex-row items-center gap-2">
            <View className="flex-row items-center gap-1 bg-warn/10 border border-warn/30 rounded-full px-2 py-0.5">
              <Clock color="#F59E0B" size={10} />
              <Text className="text-warn text-[10px] font-bold">2d</Text>
            </View>
            <View className="bg-win/15 rounded-full px-2 py-0.5">
              <Text className="text-win text-[9px] font-bold">INCOMING</Text>
            </View>
          </View>
        </View>

        <View className="flex-row gap-3">
          <View className="flex-1">
            <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1">
              YOU SEND
            </Text>
            <Text className="text-fg-muted text-[12px] leading-5">
              N. Kucherov{"\n"}E. Bouchard
            </Text>
          </View>
          <View className="items-center justify-center">
            <ArrowLeftRight color="#5A7186" size={16} />
          </View>
          <View className="flex-1">
            <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-1">
              THEY SEND
            </Text>
            <Text className="text-fg text-[12px] font-semibold leading-5">
              J. Oettinger{"\n"}L. Stankoven{"\n"}2027 3rd
            </Text>
          </View>
        </View>
      </Pressable>

      {/* Empty state for more trades */}
      <View className="mx-4 mt-2 bg-ink-850 border border-ink-700 rounded-card p-6 items-center">
        <Text className="text-fg-muted text-[13px]">
          No other active trades
        </Text>
      </View>
    </ScrollView>
  );
}
