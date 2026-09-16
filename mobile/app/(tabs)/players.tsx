import { useMemo, useState } from "react";
import {
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  ChevronDown,
  Clock,
  Search,
  SlidersHorizontal,
} from "lucide-react-native";

import { useRouter } from "expo-router";
import {
  AVAILABLE_PLAYERS,
  MY_LEAGUE,
  SUBMITTED_CLAIMS,
  WAIVER_INFO,
  type SubmittedClaim,
} from "../../src/data/mock";
import type { Position } from "../../src/data/types";
import { setAdding } from "../../src/data/addDropStore";
import { AvailablePlayerRow } from "../../src/components/AvailablePlayerRow";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { formatLocalDateTime, formatCountdown } from "../../src/utils/timezone";

type Tab = "available" | "trending" | "watchlist" | "submitted";
const POSITIONS: Array<Position | "ALL"> = ["ALL", "C", "LW", "RW", "D", "G"];

export default function PlayersScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("available");
  const [position, setPosition] = useState<Position | "ALL">("ALL");
  const [query, setQuery] = useState("");

  const players = useMemo(() => {
    return AVAILABLE_PLAYERS.filter((p) => {
      if (position !== "ALL" && p.position !== position) return false;
      if (query.trim()) {
        const q = query.trim().toLowerCase();
        if (!p.name.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [position, query]);

  const pendingClaims = SUBMITTED_CLAIMS.filter((c) => c.status === "pending");

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
                {MY_LEAGUE.name}
              </Text>
              <ChevronDown color="#8CA3B8" size={16} />
            </View>
            <Text className="text-fg-muted text-xs mt-0.5">
              {MY_LEAGUE.myTeam.record.w} - {MY_LEAGUE.myTeam.record.l}
              {MY_LEAGUE.myTeam.division ? `   ${MY_LEAGUE.myTeam.division}` : ""}
            </Text>
          </View>
        </View>
        <Pressable className="flex-row items-center gap-1.5 border border-ink-600 rounded-full px-3.5 py-2 bg-ink-850">
          <Text className="text-fg text-sm font-semibold">Week 1</Text>
          <ChevronDown color="#8CA3B8" size={14} />
        </Pressable>
      </View>

      {/* Tabs */}
      <View className="flex-row px-4 gap-2 pb-3">
        {(["available", "trending", "watchlist", "submitted"] as Tab[]).map((t) => (
          <Pressable
            key={t}
            onPress={() => setTab(t)}
            className={`px-4 py-2 rounded-full border ${
              tab === t
                ? "border-accent bg-accent/15"
                : "border-ink-700 bg-ink-850"
            }`}
          >
            <Text
              className={`text-sm font-semibold capitalize ${
                tab === t ? "text-accent" : "text-fg-muted"
              }`}
            >
              {t}
            </Text>
            {t === "submitted" && pendingClaims.length > 0 && (
              <View className="bg-accent rounded-full w-4 h-4 items-center justify-center ml-1.5">
                <Text className="text-ink-900 text-[9px] font-bold">
                  {pendingClaims.length}
                </Text>
              </View>
            )}
          </Pressable>
        ))}
      </View>

      {tab === "submitted" ? (
        /* ---- Submitted claims view ---- */
        <SubmittedClaimsView claims={SUBMITTED_CLAIMS} />
      ) : (
        /* ---- Player list views (available/trending/watchlist) ---- */
        <>
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

          {/* Position filters + Filters */}
          <View className="flex-row items-center px-4 gap-2 pb-3">
            {POSITIONS.map((pos) => {
              const active = position === pos;
              return (
                <Pressable
                  key={pos}
                  onPress={() => setPosition(pos)}
                  className={`min-w-[34px] items-center px-2 py-1.5 rounded-lg border ${
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
            <View className="flex-1" />
            <Pressable className="flex-row items-center gap-1.5 bg-ink-850 border border-ink-700 rounded-full px-3 py-1.5">
              <SlidersHorizontal color="#8CA3B8" size={14} />
              <Text className="text-fg text-[12px] font-semibold">Filters</Text>
            </Pressable>
          </View>

          {/* List */}
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
                <AvailablePlayerRow
                  key={p.id}
                  player={p}
                  onPress={(player) => router.push(`/player/${player.id}`)}
                  onAdd={(player) => {
                    setAdding(player);
                    router.push("/add-drop/bid");
                  }}
                />
              ))
            )}
          </ScrollView>
        </>
      )}
    </SafeAreaView>
  );
}

/* ---------------- Submitted Claims View ---------------- */

function SubmittedClaimsView({ claims }: { claims: SubmittedClaim[] }) {
  if (claims.length === 0) {
    return (
      <View className="flex-1 items-center justify-center px-8">
        <Text className="text-fg-muted text-[14px] text-center">
          No submitted waiver claims.
        </Text>
        <Text className="text-fg-faint text-[12px] text-center mt-2">
          When you place a bid on a player, it will appear here.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      className="flex-1"
      contentContainerStyle={{ paddingBottom: 24 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Waivers clear banner */}
      <View className="mx-4 mt-2 bg-warn/10 border border-warn/30 rounded-card px-3.5 py-2.5 flex-row items-center gap-2">
        <Clock color="#F59E0B" size={14} />
        <View className="flex-1">
          <Text className="text-warn text-[12px] font-semibold">
            Waivers clear {formatLocalDateTime(WAIVER_INFO.clearsAt)}
          </Text>
          <Text className="text-warn/70 text-[10px] mt-0.5">
            {formatCountdown(WAIVER_INFO.clearsAt)}
          </Text>
        </View>
      </View>

      {/* Claims */}
      {claims.map((claim) => (
        <ClaimCard key={claim.id} claim={claim} />
      ))}
    </ScrollView>
  );
}

function ClaimCard({ claim }: { claim: SubmittedClaim }) {
  const isPending = claim.status === "pending";
  const isWon = claim.status === "won";

  return (
    <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
      {/* Status header */}
      <View className="flex-row items-center justify-between mb-2.5">
        <View
          className={`rounded-full px-2.5 py-0.5 ${
            isPending
              ? "bg-warn/15"
              : isWon
                ? "bg-win/15"
                : "bg-loss/15"
          }`}
        >
          <Text
            className={`text-[10px] font-bold ${
              isPending
                ? "text-warn"
                : isWon
                  ? "text-win"
                  : "text-loss"
            }`}
          >
            {isPending ? "PENDING" : isWon ? "WON" : "LOST"}
          </Text>
        </View>
        <Text className="text-fg-faint text-[10px]">
          {formatCountdown(claim.submittedAt)}
        </Text>
      </View>

      {/* Player + bid */}
      <View className="flex-row items-center">
        <PlayerHeadshot url={claim.player.headshotUrl} size={40} />
        <View className="flex-1 ml-3">
          <Text className="text-fg text-[14px] font-semibold">
            {claim.player.name}
          </Text>
          <Text className="text-fg-muted text-[11px] mt-0.5">
            {claim.player.team} · {claim.player.position} ·{" "}
            {claim.player.projectedPoints.toFixed(1)} proj
          </Text>
        </View>
        <View className="items-end">
          <Text className="text-fg text-[16px] font-extrabold">
            ${claim.bidAmount}
          </Text>
          <Text className="text-fg-faint text-[9px]">FAAB bid</Text>
        </View>
      </View>

      {/* Drop player if applicable */}
      {claim.dropPlayer && (
        <View className="flex-row items-center mt-2.5 pt-2.5 border-t border-ink-700/50">
          <Text className="text-fg-faint text-[10px] font-bold tracking-widest mr-2">
            DROP:
          </Text>
          <PlayerHeadshot url={claim.dropPlayer.headshotUrl} size={24} />
          <Text className="text-fg-muted text-[11px] ml-2">
            {claim.dropPlayer.name}
          </Text>
        </View>
      )}
    </View>
  );
}