import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  Brackets,
  Calendar,
  ChevronRight,
  Skull,
  Sparkles,
  Swords,
  Trophy,
  Users,
} from "lucide-react-native";

import {
  EVENT_COUNTS,
  EVENTS,
  type EventStatus,
  type GameEvent,
} from "../../src/data/events";
import { BottomNav } from "../../src/components/BottomNav";

const TABS: { id: EventStatus; label: string }[] = [
  { id: "active", label: `Active (${EVENT_COUNTS.active})` },
  { id: "upcoming", label: `Upcoming (${EVENT_COUNTS.upcoming})` },
  { id: "completed", label: `Completed (${EVENT_COUNTS.completed})` },
];

export default function EventsScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<EventStatus>("active");
  const [mineOnly, setMineOnly] = useState(false);

  const events = EVENTS.filter((e) => e.status === tab);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Header */}
      <View className="flex-row items-start justify-between px-4 pt-2 pb-3">
        <View>
          <Text className="text-fg text-[26px] font-black tracking-tight">
            Events
          </Text>
          <Text className="text-fg-muted text-[13px] mt-0.5">
            Side competitions. More hockey. Year-round.
          </Text>
        </View>
        <Pressable
          onPress={() => setMineOnly((v) => !v)}
          className={`flex-row items-center gap-1.5 border rounded-full px-3.5 py-2 mt-1 ${
            mineOnly
              ? "border-accent bg-accent/15"
              : "border-ink-600 bg-ink-850"
          }`}
        >
          <Trophy color={mineOnly ? "#2AB3FF" : "#8CA3B8"} size={14} />
          <Text
            className={`text-[12px] font-semibold ${
              mineOnly ? "text-accent" : "text-fg"
            }`}
          >
            My Events
          </Text>
        </Pressable>
      </View>

      {/* Tabs */}
      <View className="flex-row px-4 gap-2 pb-3">
        {TABS.map((t) => {
          const active = tab === t.id;
          return (
            <Pressable
              key={t.id}
              onPress={() => setTab(t.id)}
              className={`flex-1 items-center py-2 rounded-full border ${
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
                {t.label}
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
        {events.length === 0 ? (
          <View className="items-center py-16 px-8">
            <Trophy color="#5A7186" size={28} />
            <Text className="text-fg-muted text-[13px] text-center mt-3">
              No events here yet.
            </Text>
          </View>
        ) : (
          events.map((event) => <EventCard key={event.id} event={event} />)
        )}
        {mineOnly && (
          <Text className="text-fg-faint text-[11px] text-center mt-3">
            Showing only events Harbour Ice is entered in.
          </Text>
        )}
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}

/* ---------------- Event Card ---------------- */

function EventCard({ event }: { event: GameEvent }) {
  const router = useRouter();

  return (
    <View
      className={`mx-4 mt-2 rounded-card overflow-hidden border ${
        event.featured
          ? "border-accent/60 bg-ink-850"
          : "border-ink-700 bg-ink-850"
      }`}
    >
      {/* Top banner */}
      <View className="p-3.5 pb-0">
        <View className="flex-row items-center justify-between mb-2">
          {event.featured ? (
            <View className="flex-row items-center gap-1 bg-accent/20 border border-accent/50 rounded-full px-2 py-0.5">
              <Sparkles color="#2AB3FF" size={10} />
              <Text className="text-accent text-[9px] font-bold tracking-widest">
                FEATURED
              </Text>
            </View>
          ) : (
            <View />
          )}
          <StatusPill status={event.status} label={event.statusLabel} />
        </View>

        <View className="flex-row items-center">
          <View className="w-12 h-12 rounded-xl bg-ink-800 border border-ink-600 items-center justify-center">
            <Text className="text-2xl">{event.emoji}</Text>
          </View>
          <View className="flex-1 ml-3">
            <Text className="text-fg text-[18px] font-extrabold">
              {event.name}
            </Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              {event.tagline}
            </Text>
          </View>
        </View>

        {/* Meta row */}
        <View className="flex-row mt-3 border-t border-ink-700/60 pt-2.5">
          {event.meta.map((m, i) => (
            <View
              key={m.label}
              className={`flex-1 flex-row items-start gap-1.5 ${
                i > 0 ? "border-l border-ink-700/60 pl-2.5 ml-1" : ""
              }`}
            >
              <MetaIcon icon={m.icon} />
              <View className="flex-1">
                <Text className="text-fg text-[10px] font-bold leading-3">
                  {m.label}
                </Text>
                <Text className="text-fg-faint text-[9px] leading-3 mt-0.5">
                  {m.sub}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* Your side + next + CTA */}
      <View className="mt-3 bg-ink-800/60 border-t border-ink-700/60 px-3.5 py-3 flex-row items-center">
        {/* Your side */}
        <View className="flex-1 flex-row items-center">
          <View className="w-9 h-9 rounded-full bg-ink-700 border border-ink-600 items-center justify-center">
            <Text className="text-base">{event.yourSideEmoji}</Text>
          </View>
          <View className="ml-2.5 flex-1">
            <Text className="text-fg-faint text-[8px] font-bold tracking-widest">
              {event.yourSideLabel.toUpperCase()}
            </Text>
            <Text className="text-fg text-[12px] font-bold" numberOfLines={1}>
              {event.yourSideName}
            </Text>
            <Text className="text-fg-faint text-[9px]" numberOfLines={1}>
              {event.yourSideDetail}
            </Text>
          </View>
        </View>

        <View className="w-px h-9 bg-ink-700 mx-2.5" />

        {/* Next matchup / countdown */}
        <View className="flex-1">
          <Text className="text-fg-faint text-[8px] font-bold tracking-widest">
            {event.nextLabel}
          </Text>
          {event.countdown ? (
            <View className="flex-row gap-1.5 mt-1">
              <CountdownCell value={event.countdown.days} unit="DAYS" />
              <CountdownCell value={event.countdown.hrs} unit="HRS" />
              <CountdownCell value={event.countdown.min} unit="MIN" />
            </View>
          ) : (
            <View className="flex-row items-center mt-1">
              {event.opponentEmoji ? (
                <Text className="text-base mr-1.5">{event.opponentEmoji}</Text>
              ) : null}
              <View>
                <Text className="text-fg text-[12px] font-bold" numberOfLines={1}>
                  {event.opponentName ? `vs ${event.opponentName}` : ""}
                </Text>
                <Text className="text-fg-faint text-[9px]">
                  {event.opponentDetail}
                </Text>
              </View>
            </View>
          )}
        </View>

        {/* CTA */}
        <Pressable
          onPress={() =>
            router.push({
              pathname: "/events/[id]",
              params: { id: event.id },
            })
          }
          className="flex-row items-center gap-1 bg-accent rounded-lg px-3 py-2.5 ml-2"
        >
          <Text className="text-ink-900 text-[11px] font-bold">View Event</Text>
          <ChevronRight color="#0A1420" size={13} />
        </Pressable>
      </View>
    </View>
  );
}

function StatusPill({
  status,
  label,
}: {
  status: EventStatus;
  label: string;
}) {
  const config =
    status === "active"
      ? { dot: "#22C55E", cls: "bg-win/15 border-win/40", text: "text-win" }
      : status === "upcoming"
        ? { dot: "#F59E0B", cls: "bg-warn/15 border-warn/40", text: "text-warn" }
        : { dot: "#5A7186", cls: "bg-ink-700 border-ink-600", text: "text-fg-muted" };
  return (
    <View
      className={`flex-row items-center gap-1.5 border rounded-full px-2.5 py-1 ${config.cls}`}
    >
      <View
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: config.dot }}
      />
      <Text className={`text-[9px] font-bold tracking-widest ${config.text}`}>
        {label.toUpperCase()}
      </Text>
    </View>
  );
}

function CountdownCell({ value, unit }: { value: number; unit: string }) {
  return (
    <View className="bg-ink-900 border border-ink-700 rounded-md px-1.5 py-1 items-center min-w-[30px]">
      <Text className="text-fg text-[13px] font-extrabold">{value}</Text>
      <Text className="text-fg-faint text-[7px] font-bold">{unit}</Text>
    </View>
  );
}

function MetaIcon({ icon }: { icon: string }) {
  switch (icon) {
    case "users":
      return <Users color="#2AB3FF" size={13} />;
    case "swords":
      return <Swords color="#2AB3FF" size={13} />;
    case "calendar":
      return <Calendar color="#2AB3FF" size={13} />;
    case "trophy":
      return <Trophy color="#2AB3FF" size={13} />;
    case "skull":
      return <Skull color="#2AB3FF" size={13} />;
    case "bracket":
      return <Brackets color="#2AB3FF" size={13} />;
    default:
      return <Users color="#2AB3FF" size={13} />;
  }
}
