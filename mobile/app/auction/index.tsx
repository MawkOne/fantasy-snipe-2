import { useEffect, useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  ChevronDown,
  ChevronUp,
  Ellipsis,
  Keyboard,
  Star,
} from "lucide-react-native";

import {
  AUCTION_META,
  AUCTION_PLAYER,
  AUCTION_STATE,
  AUCTION_TEAMS,
  NOMINATION_NOTE,
  NOMINATION_QUEUE,
  RECENT_BIDS,
} from "../../src/data/auction";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";

const QUICK_BIDS = [1, 2, 5];
const MIN_BID = 2; // UHHP minimum annual salary (units)
const DRAFT_CONTRACT_YEARS = 3; // all draft signings are 3-year deals

export default function AuctionScreen() {
  const router = useRouter();
  const [secondsLeft, setSecondsLeft] = useState(AUCTION_STATE.secondsStart);
  const [raise, setRaise] = useState(QUICK_BIDS[2]); // default +5
  const [teamsView, setTeamsView] = useState<"cap" | "max">("cap");
  const [watching, setWatching] = useState(false);
  const [highBid, setHighBid] = useState(AUCTION_STATE.highBid);
  const [placed, setPlaced] = useState(false);
  const [showAllBids, setShowAllBids] = useState(false);
  const [customOpen, setCustomOpen] = useState(false);
  const [customBid, setCustomBid] = useState("");

  useEffect(() => {
    const id = setInterval(
      () => setSecondsLeft((s) => (s > 0 ? s - 1 : 0)),
      1000
    );
    return () => clearInterval(id);
  }, []);

  const nextValidBid = Math.max(highBid + AUCTION_STATE.minRaise, MIN_BID);
  const myBid = Math.max(highBid + raise, MIN_BID);

  // Timer ring progress (0..1) over an assumed 30s window.
  const progress = Math.min(1, secondsLeft / 30);
  const R = 34;
  const CIRC = 2 * Math.PI * R;

  const placeBid = () => {
    setHighBid(myBid);
    setPlaced(true);
    setSecondsLeft(AUCTION_STATE.secondsStart);
  };

  const customAmount = parseInt(customBid, 10);
  const customValid =
    !Number.isNaN(customAmount) && customAmount >= nextValidBid;

  const placeCustomBid = () => {
    if (!customValid) return;
    setHighBid(customAmount);
    setPlaced(true);
    setSecondsLeft(AUCTION_STATE.secondsStart);
    setCustomOpen(false);
    setCustomBid("");
  };

  const visibleBids = showAllBids ? RECENT_BIDS : RECENT_BIDS.slice(0, 5);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 pt-2 pb-3 border-b border-ink-700/60">
        <View className="flex-row items-center gap-2.5">
          <View className="w-10 h-10 rounded-full bg-ink-700 border border-accent/50 items-center justify-center">
            <Text className="text-lg">🐻‍❄️</Text>
          </View>
          <View>
            <Text className="text-fg text-[17px] font-extrabold tracking-tight">
              UHHP
            </Text>
            <Text className="text-fg-muted text-[10px] mt-0.5">
              Dynasty Hockey
            </Text>
          </View>
        </View>
        <View className="flex-row items-center gap-3">
          <View className="items-end">
            <View className="flex-row items-center gap-1.5">
              <View className="w-1.5 h-1.5 rounded-full bg-win" />
              <Text className="text-win text-[11px] font-bold">Live Draft</Text>
            </View>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              {AUCTION_META.ownersOnline}
            </Text>
          </View>
          <Ellipsis color="#8CA3B8" size={20} />
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Auction status bar */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card px-3.5 py-3 flex-row items-center">
          <View className="flex-1">
            <Text className="text-fg text-[14px] font-extrabold">
              {AUCTION_META.title}
            </Text>
            <Text className="text-fg-muted text-[10px] mt-0.5">
              {AUCTION_META.subtitle}
            </Text>
          </View>
          <View className="items-center px-3 border-l border-ink-700/60">
            <Text className="text-fg text-[14px] font-extrabold">
              {AUCTION_META.onClock}
            </Text>
            <Text className="text-fg-faint text-[9px] mt-0.5">On the Clock</Text>
          </View>
          <View className="items-center pl-3 border-l border-ink-700/60">
            <Text className="text-xl">{AUCTION_META.nominatingEmoji}</Text>
            <Text className="text-fg text-[11px] font-bold mt-0.5">
              {AUCTION_META.nominatingTeam}
            </Text>
            <Text className="text-accent text-[9px] font-semibold">
              Nominating
            </Text>
          </View>
        </View>

        {/* Player + current bid */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row">
            <PlayerHeadshot url={AUCTION_PLAYER.headshotUrl} size={72} />
            <View className="flex-1 ml-3">
              <View className="flex-row items-start justify-between">
                <Text className="text-fg text-[20px] font-extrabold flex-1">
                  {AUCTION_PLAYER.name}
                </Text>
                <Pressable onPress={() => setWatching((w) => !w)} className="p-1">
                  <Star
                    color={watching ? "#2AB3FF" : "#5A7186"}
                    size={18}
                    fill={watching ? "#2AB3FF" : "transparent"}
                  />
                </Pressable>
              </View>
              <Text className="text-fg-muted text-[12px] mt-0.5">
                {AUCTION_PLAYER.position}  |  {AUCTION_PLAYER.team}
              </Text>
              <View className="flex-row items-center gap-2 mt-1.5">
                <Text className="text-fg-faint text-[11px]">
                  Age {AUCTION_PLAYER.age}  |  {AUCTION_PLAYER.contract}
                </Text>
                <View className="bg-accent/15 border border-accent/50 rounded-full px-2 py-0.5">
                  <Text className="text-accent text-[9px] font-bold">
                    {AUCTION_PLAYER.tag}
                  </Text>
                </View>
              </View>
            </View>
          </View>

          {/* Current high bid */}
          <View className="mt-3 pt-3 border-t border-ink-700/60 items-end">
            <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
              CURRENT HIGH BID
            </Text>
            <Text className="text-fg text-[28px] font-extrabold mt-0.5">
              ${highBid}
            </Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              by <Text className="text-accent font-bold">{AUCTION_STATE.highBidTeam}</Text>
            </Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              Market Value   ${AUCTION_PLAYER.marketValue}
            </Text>
          </View>
        </View>

        {/* Contract note — draft signings are fixed 3-year deals */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row items-center justify-between">
          <View className="flex-1">
            <Text className="text-fg text-[12px] font-bold">Contract Term</Text>
            <Text className="text-fg-muted text-[10px] mt-0.5">
              {AUCTION_PLAYER.note}
            </Text>
          </View>
          <View className="bg-accent/15 border border-accent/50 rounded-lg px-3 py-1.5">
            <Text className="text-accent text-[13px] font-bold">
              {DRAFT_CONTRACT_YEARS} years
            </Text>
          </View>
        </View>

        {/* Bidding row */}
        <View className="mx-4 mt-3 bg-ink-850 border border-ink-700 rounded-card p-3.5 flex-row gap-3">
          {/* Timer */}
          <View className="items-center">
            <Text className="text-fg-muted text-[10px] font-bold mb-1.5">
              Time Remaining
            </Text>
            <View className="w-[84px] h-[84px] items-center justify-center">
              {/* Ring */}
              <View className="absolute w-[84px] h-[84px] rounded-full border-[6px] border-ink-700" />
              <View
                className="absolute w-[84px] h-[84px] rounded-full border-[6px] border-accent"
                style={{
                  borderTopColor: "#2AB3FF",
                  borderRightColor: progress > 0.25 ? "#2AB3FF" : "transparent",
                  borderBottomColor: progress > 0.5 ? "#2AB3FF" : "transparent",
                  borderLeftColor: progress > 0.75 ? "#2AB3FF" : "transparent",
                  transform: [{ rotate: "-90deg" }],
                }}
              />
              <Text className="text-fg text-[18px] font-extrabold">
                0:{String(secondsLeft).padStart(2, "0")}
              </Text>
            </View>
          </View>

          {/* Bid controls */}
          <View className="flex-1">
            <View className="flex-row gap-2">
              {QUICK_BIDS.map((amt) => {
                const active = raise === amt;
                return (
                  <Pressable
                    key={amt}
                    onPress={() => setRaise(amt)}
                    className={`flex-1 items-center py-2.5 rounded-lg border ${
                      active
                        ? "border-accent bg-accent/15"
                        : "border-ink-700 bg-ink-800"
                    }`}
                  >
                    <Text
                      className={`text-[14px] font-bold ${
                        active ? "text-accent" : "text-fg"
                      }`}
                    >
                      +{amt}
                    </Text>
                  </Pressable>
                );
              })}
              <Pressable
                onPress={() => setCustomOpen(true)}
                className="flex-row items-center gap-1 px-2.5 py-2.5 rounded-lg border border-ink-700 bg-ink-800"
              >
                <Text className="text-fg-muted text-[11px] font-semibold">
                  Custom
                </Text>
                <Keyboard color="#8CA3B8" size={13} />
              </Pressable>
            </View>
            <Pressable
              onPress={placeBid}
              className="mt-2 bg-accent rounded-lg py-3 items-center"
            >
              <Text className="text-ink-900 text-[15px] font-extrabold">
                Place Bid  ${myBid}
              </Text>
            </Pressable>
            <Text className="text-fg-faint text-[10px] text-center mt-1.5">
              Next valid bid: ${nextValidBid}  |  Minimum raise: $
              {AUCTION_STATE.minRaise}
            </Text>
          </View>
        </View>

        {placed && (
          <View className="mx-4 mt-2 bg-win/10 border border-win/40 rounded-card px-3.5 py-2.5">
            <Text className="text-win text-[12px] font-bold">
              You're the high bidder at ${highBid} ({termYears} yr term)
            </Text>
          </View>
        )}

        {/* Teams */}
        <View className="flex-row items-center px-4 pt-4 pb-2 gap-3">
          <Text className="text-fg text-[14px] font-bold">Teams</Text>
          <View className="flex-row bg-ink-850 rounded-full p-0.5 border border-ink-700">
            {(["cap", "max"] as const).map((v) => (
              <Pressable
                key={v}
                onPress={() => setTeamsView(v)}
                className={`px-3.5 py-1 rounded-full ${
                  teamsView === v ? "bg-accent" : ""
                }`}
              >
                <Text
                  className={`text-[11px] font-bold ${
                    teamsView === v ? "text-ink-900" : "text-fg-muted"
                  }`}
                >
                  {v === "cap" ? "Cap Room" : "Max Bid"}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>
        <View className="flex-row flex-wrap px-4 gap-2">
          {AUCTION_TEAMS.map((team) => (
            <View
              key={team.id}
              className={`w-[31.5%] bg-ink-850 rounded-card border p-2.5 items-center ${
                team.nominating ? "border-accent" : "border-ink-700"
              }`}
            >
              <Text className="text-fg-muted text-[9px] font-semibold" numberOfLines={1}>
                {team.name}
              </Text>
              <Text className="text-xl my-1">{team.emoji}</Text>
              <Text className="text-fg text-[13px] font-extrabold">
                ${teamsView === "cap" ? team.capRoom : team.maxBid}
              </Text>
              <Text className="text-fg-faint text-[8px]">
                Max: ${team.maxBid}
              </Text>
            </View>
          ))}
        </View>

        {/* Recent bids + Nomination queue */}
        <View className="flex-row px-4 gap-2 mt-4">
          {/* Recent bids */}
          <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3">
            <View className="flex-row items-center justify-between mb-2">
              <Text className="text-fg text-[13px] font-bold">Recent Bids</Text>
              <Pressable
                onPress={() => setShowAllBids((v) => !v)}
                className="flex-row items-center gap-1"
              >
                <Text className="text-accent text-[10px] font-semibold">
                  {showAllBids ? "Fewer" : "All Bids"}
                </Text>
                {showAllBids ? (
                  <ChevronUp color="#2AB3FF" size={12} />
                ) : (
                  <ChevronDown color="#8CA3B8" size={12} />
                )}
              </Pressable>
            </View>
            {visibleBids.map((bid) => (
              <View
                key={bid.id}
                className="flex-row items-center py-1.5 border-b border-ink-700/50"
              >
                <Text className="text-fg text-[13px] font-extrabold w-8">
                  ${bid.amount}
                </Text>
                <Text className="text-sm mx-1.5">{bid.teamEmoji}</Text>
                <Text
                  className="flex-1 text-fg-muted text-[11px]"
                  numberOfLines={1}
                >
                  {bid.teamName}
                </Text>
                <Text className="text-fg-faint text-[9px]">{bid.time}</Text>
              </View>
            ))}
          </View>

          {/* Nomination queue */}
          <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3">
            <Text className="text-fg text-[13px] font-bold mb-2">
              Nomination Queue
            </Text>
            {NOMINATION_QUEUE.map((slot) => (
              <View key={slot.order} className="flex-row items-center py-1.5">
                <Text className="text-fg-faint text-[11px] font-bold w-4">
                  {slot.order}
                </Text>
                <Text className="text-sm mx-1.5">{slot.teamEmoji}</Text>
                <Text
                  className="flex-1 text-fg-muted text-[11px]"
                  numberOfLines={1}
                >
                  {slot.teamName}
                </Text>
              </View>
            ))}
            <Text className="text-fg-faint text-[9px] mt-2 leading-3">
              {NOMINATION_NOTE}
            </Text>
          </View>
        </View>
      </ScrollView>

      {/* Custom bid modal */}
      <Modal
        visible={customOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setCustomOpen(false)}
      >
        <Pressable
          className="flex-1 bg-ink-950/80 items-center justify-center px-8"
          onPress={() => setCustomOpen(false)}
        >
          <Pressable
            onPress={() => {}}
            className="w-full bg-ink-850 border border-ink-700 rounded-card p-4"
          >
            <Text className="text-fg text-[15px] font-extrabold">
              Custom Bid
            </Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              Minimum ${nextValidBid} · Your cap room $47
            </Text>
            <View className="flex-row items-center bg-ink-800 border border-ink-600 rounded-lg px-3 mt-3">
              <Text className="text-fg text-[18px] font-extrabold mr-1">$</Text>
              <TextInput
                value={customBid}
                onChangeText={setCustomBid}
                keyboardType="number-pad"
                placeholder={String(nextValidBid)}
                placeholderTextColor="#5A7186"
                autoFocus
                className="flex-1 py-2.5 text-fg text-[18px] font-extrabold"
                style={{ outlineStyle: "none" } as never}
              />
            </View>
            {customBid.length > 0 && !customValid && (
              <Text className="text-loss text-[11px] mt-1.5">
                Bid must be at least ${nextValidBid}
              </Text>
            )}
            <Pressable
              onPress={placeCustomBid}
              disabled={!customValid}
              className={`mt-3 rounded-full py-3 items-center ${
                customValid ? "bg-accent" : "bg-ink-700"
              }`}
            >
              <Text
                className={`text-[14px] font-bold ${
                  customValid ? "text-ink-900" : "text-fg-faint"
                }`}
              >
                Place Bid{customValid ? `  $${customAmount}` : ""}
              </Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}
