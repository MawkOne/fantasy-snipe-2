import { useState } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  ChevronLeft,
  Clock,
  DollarSign,
  TrendingUp,
  Users,
} from "lucide-react-native";

import { WAIVER_INFO } from "../../src/data/mock";
import { getAdding, setBid } from "../../src/data/addDropStore";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";
import { formatLocalDateTime, formatCountdown, getTimezoneName } from "../../src/utils/timezone";

export default function WaiverBidScreen() {
  const router = useRouter();
  const adding = getAdding();
  const [bid, setBidText] = useState("0");

  if (!adding) {
    router.back();
    return null;
  }

  const bidNum = parseInt(bid) || 0;
  const isValidBid = bidNum >= 0 && bidNum <= WAIVER_INFO.faabRemaining;
  const pctUsed = (WAIVER_INFO.faabRemaining / WAIVER_INFO.faabBudget) * 100;

  const handleContinue = () => {
    setBid(bidNum);
    router.push("/add-drop");
  };

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="flex-row items-center px-4 py-3 border-b border-ink-700/60">
        <Pressable onPress={() => router.back()} className="mr-3 p-1 -ml-1">
          <ChevronLeft color="#F2F7FC" size={24} />
        </Pressable>
        <Text className="text-fg text-lg font-extrabold">Place Bid</Text>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 120 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Player being added + inline bid input */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center">
            <PlayerHeadshot url={adding.headshotUrl} size={44} />
            <View className="flex-1 ml-3">
              <Text className="text-fg text-[15px] font-semibold">
                {adding.name}
              </Text>
              <Text className="text-fg-muted text-xs mt-0.5">
                {adding.team} · {adding.position}
              </Text>
              <Text className="text-fg-faint text-[11px] mt-1">
                {adding.projectedPoints.toFixed(1)} proj · {adding.rosteredPct}% rostered
              </Text>
            </View>
            {/* Inline bid input */}
            <View className="flex-row items-center bg-ink-800 border border-ink-600 rounded-lg px-2.5 py-1.5">
              <Text className="text-fg text-[15px] font-bold mr-0.5">$</Text>
              <TextInput
                value={bid}
                onChangeText={(text) => {
                  const cleaned = text.replace(/[^0-9]/g, "");
                  setBidText(cleaned);
                }}
                keyboardType="number-pad"
                placeholder="0"
                placeholderTextColor="#5A7186"
                className="text-fg text-[15px] font-bold min-w-[32px] text-center"
              />
            </View>
          </View>
          {/* Validation */}
          {bidNum > WAIVER_INFO.faabRemaining && (
            <Text className="text-loss text-[11px] mt-2 font-semibold">
              Bid exceeds remaining budget (${WAIVER_INFO.faabRemaining})
            </Text>
          )}
        </View>

        {/* FAAB budget card */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center gap-1.5 mb-2">
            <DollarSign color="#22C55E" size={14} />
            <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
              FAAB BUDGET
            </Text>
          </View>
          <View className="flex-row items-baseline justify-between">
            <Text className="text-fg text-2xl font-extrabold">
              ${WAIVER_INFO.faabRemaining}
            </Text>
            <Text className="text-fg-muted text-[11px]">
              of ${WAIVER_INFO.faabBudget} remaining
            </Text>
          </View>
          {/* Budget bar */}
          <View className="h-1.5 rounded-full bg-ink-700 mt-2 overflow-hidden">
            <View
              style={{ width: `${pctUsed}%` }}
              className="h-full rounded-full bg-win"
            />
          </View>
          {/* After bid */}
          {bidNum > 0 && isValidBid && (
            <Text className="text-fg-muted text-[11px] mt-2">
              After bid:{" "}
              <Text className="text-warn font-semibold">
                ${WAIVER_INFO.faabRemaining - bidNum} remaining
              </Text>
            </Text>
          )}
        </View>

        {/* Priority order */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center gap-1.5 mb-2">
            <Users color="#2AB3FF" size={14} />
            <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
              WAIVER PRIORITY ORDER
            </Text>
          </View>
          <View className="gap-1.5">
            {Array.from({ length: WAIVER_INFO.waiverPriorityTotal }).map((_, i) => {
              const priority = i + 1;
              const isMe = priority === WAIVER_INFO.waiverPriority;
              return (
                <View
                  key={i}
                  className={`flex-row items-center px-2.5 py-1.5 rounded-lg ${
                    isMe ? "bg-accent/10 border border-accent/40" : ""
                  }`}
                >
                  <Text
                    className={`text-[12px] font-bold w-6 ${
                      isMe ? "text-accent" : "text-fg-faint"
                    }`}
                  >
                    #{priority}
                  </Text>
                  <Text
                    className={`text-[12px] flex-1 ${
                      isMe ? "text-fg font-semibold" : "text-fg-muted"
                    }`}
                  >
                    {isMe ? "Your Team" : `Team ${priority}`}
                  </Text>
                  {isMe && (
                    <View className="bg-accent/15 rounded-full px-2 py-0.5">
                      <Text className="text-accent text-[9px] font-bold">YOU</Text>
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        </View>

        {/* Clears at — in user's local timezone */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card px-3.5 py-2.5">
          <View className="flex-row items-center gap-2">
            <Clock color="#F59E0B" size={14} />
            <View className="flex-1">
              <Text className="text-fg-muted text-[12px]">
                Waivers clear{" "}
                <Text className="text-warn font-semibold">
                  {formatLocalDateTime(WAIVER_INFO.clearsAt)}
                </Text>
              </Text>
              <Text className="text-fg-faint text-[10px] mt-0.5">
                {formatCountdown(WAIVER_INFO.clearsAt)} · {getTimezoneName()}
              </Text>
            </View>
          </View>
        </View>

        {/* How waivers work */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-start gap-2.5">
            <TrendingUp color="#2AB3FF" size={16} />
            <View className="flex-1">
              <Text className="text-fg text-[12px] font-semibold mb-1">
                How waivers work
              </Text>
              <Text className="text-fg-muted text-[11px] leading-4">
                If multiple teams bid on the same player, the highest bid wins.
                If bids are tied, waiver priority breaks the tie. Your bid is
                only charged if the claim is successful.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Continue CTA */}
      <View className="px-4 pb-6 pt-2 bg-ink-900 border-t border-ink-700/60">
        <Pressable
          disabled={!isValidBid}
          onPress={handleContinue}
          className={`rounded-full py-3.5 items-center ${
            isValidBid ? "bg-accent" : "bg-ink-700"
          }`}
        >
          <Text
            className={`text-[15px] font-bold ${
              isValidBid ? "text-ink-900" : "text-fg-faint"
            }`}
          >
            {bidNum > 0 ? `Continue with $${bidNum} Bid` : "Continue with $0 Bid"}
          </Text>
        </Pressable>
      </View>

      <BottomNav active="players" />
    </SafeAreaView>
  );
}