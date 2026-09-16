import { useState } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import {
  ArrowLeftRight,
  Bell,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  CircleCheck,
  History,
  Plus,
  RotateCcw,
  Search,
  Send,
  Smile,
  TrendingUp,
  Users,
  X,
} from "lucide-react-native";

import {
  ACTIVE_TRADE,
  MANAGERS,
  MY_AVAILABLE_ASSETS,
  THEIR_AVAILABLE_ASSETS,
  type TradeAsset,
  type AvailableTradeAsset,
  type ManagerOption,
} from "../../src/data/mock";
import * as tradeStore from "../../src/data/tradeStore";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";

type AddingTo = "youSend" | "theySend" | null;
type TradeTab = "chat" | "analysis" | "changelog";

interface ChatMsg {
  id: string;
  author: string;
  time: string;
  text: string;
  mine: boolean;
}

interface ChangeLogEntry {
  id: string;
  action: "added" | "removed";
  assetName: string;
  side: "youSend" | "theySend";
  time: string;
  committed: boolean;
}

interface TradeVersion {
  id: string;
  version: number;
  time: string;
  youSend: TradeAsset[];
  theySend: TradeAsset[];
  changeCount: number;
  isCurrent: boolean;
}

export default function TradeDetailScreen() {
  const router = useRouter();
  const { managerId } = useLocalSearchParams<{ managerId?: string }>();

  const tradePartner: ManagerOption =
    MANAGERS.find((m) => m.id === managerId) ?? {
      id: "puck-pirates",
      name: ACTIVE_TRADE.theirs.name,
      emoji: ACTIVE_TRADE.theirs.logoEmoji,
      manager: ACTIVE_TRADE.theirs.manager,
      record: "5-4-1",
      strategy: ACTIVE_TRADE.theirs.strategy,
    };

  const t = ACTIVE_TRADE;
  const isNewTrade = !!managerId;

  // --- Committed state (what's been sent to the other manager) ---
  const [committedYouSend, setCommittedYouSend] = useState<TradeAsset[]>(
    isNewTrade ? [] : t.theyReceive
  );
  const [committedTheySend, setCommittedTheySend] = useState<TradeAsset[]>(
    isNewTrade ? [] : t.youReceive
  );

  // --- Staged state (local edits, not yet sent) ---
  const [stagedYouSend, setStagedYouSend] = useState<TradeAsset[]>(committedYouSend);
  const [stagedTheySend, setStagedTheySend] = useState<TradeAsset[]>(committedTheySend);

  // --- Dirty tracking ---
  const youSendDirty = JSON.stringify(stagedYouSend.map((a) => a.id).sort()) !==
    JSON.stringify(committedYouSend.map((a) => a.id).sort());
  const theySendDirty = JSON.stringify(stagedTheySend.map((a) => a.id).sort()) !==
    JSON.stringify(committedTheySend.map((a) => a.id).sort());
  const hasChanges = youSendDirty || theySendDirty;

  // --- Tabs ---
  const [activeTab, setActiveTab] = useState<TradeTab>("chat");

  // --- Chat ---
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);

  // --- Change log ---
  const [changeLog, setChangeLog] = useState<ChangeLogEntry[]>([]);

  const logChange = (action: "added" | "removed", assetName: string, side: "youSend" | "theySend") => {
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    setChangeLog((prev) => [
      { id: `cl-${Date.now()}`, action, assetName, side, time, committed: false },
      ...prev,
    ]);
  };

  const sendMessage = () => {
    const text = draft.trim();
    if (!text) return;
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    setMessages((prev) => [
      ...prev,
      { id: `msg-${Date.now()}`, author: t.mine.manager, time, text, mine: true },
    ]);
    setDraft("");
  };

  // --- Asset picker ---
  const [addingTo, setAddingTo] = useState<AddingTo>(null);
  const [pickerSearch, setPickerSearch] = useState("");

  const usedIds = new Set([
    ...stagedYouSend.map((a) => a.id),
    ...stagedTheySend.map((a) => a.id),
  ]);

  const pickerAssets: AvailableTradeAsset[] =
    addingTo === "youSend"
      ? MY_AVAILABLE_ASSETS.filter((a) => !usedIds.has(a.id))
      : addingTo === "theySend"
        ? THEIR_AVAILABLE_ASSETS.filter((a) => !usedIds.has(a.id))
        : [];

  const filteredPickerAssets = pickerSearch.trim()
    ? pickerAssets.filter((a) =>
        a.name.toLowerCase().includes(pickerSearch.trim().toLowerCase())
      )
    : pickerAssets;

  const pickerPlayers = filteredPickerAssets.filter((a) => a.kind === "player");
  const pickerPicks = filteredPickerAssets.filter((a) => a.kind === "pick");

  const addAsset = (asset: AvailableTradeAsset) => {
    const newAsset: TradeAsset = {
      id: asset.id,
      kind: asset.kind,
      name: asset.name,
      detail: asset.detail,
      headshotUrl: asset.headshotUrl,
    };
    if (addingTo === "youSend") {
      setStagedYouSend((prev) => [...prev, newAsset]);
      logChange("added", asset.name, "youSend");
    } else if (addingTo === "theySend") {
      setStagedTheySend((prev) => [...prev, newAsset]);
      logChange("added", asset.name, "theySend");
    }
    setAddingTo(null);
    setPickerSearch("");
  };

  const removeAsset = (side: "youSend" | "theySend", assetId: string) => {
    const assets = side === "youSend" ? stagedYouSend : stagedTheySend;
    const asset = assets.find((a) => a.id === assetId);
    if (asset) {
      logChange("removed", asset.name, side);
    }
    if (side === "youSend") {
      setStagedYouSend((prev) => prev.filter((a) => a.id !== assetId));
    } else {
      setStagedTheySend((prev) => prev.filter((a) => a.id !== assetId));
    }
  };

  // --- Version history ---
  const [versions, setVersions] = useState<TradeVersion[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  const [viewingVersion, setViewingVersion] = useState<number | null>(null);

  // --- Notify: commit staged changes as a new version + sync shared store ---
  const notify = () => {
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    const newVersion: TradeVersion = {
      id: `v${Date.now()}`,
      version: versions.length + 1,
      time,
      youSend: [...stagedYouSend],
      theySend: [...stagedTheySend],
      changeCount: changeLog.filter((e) => !e.committed).length,
      isCurrent: true,
    };
    setVersions((prev) => [
      newVersion,
      ...prev.map((v) => ({ ...v, isCurrent: false })),
    ]);
    setCommittedYouSend(stagedYouSend);
    setCommittedTheySend(stagedTheySend);
    setChangeLog((prev) => prev.map((e) => ({ ...e, committed: true })));
    setViewingVersion(null);

    // Sync the shared store so Analysis + Finalize reflect this proposal.
    tradeStore.setYouSend(stagedYouSend);
    tradeStore.setTheySend(stagedTheySend);
  };

  const restoreVersion = (version: TradeVersion) => {
    setStagedYouSend([...version.youSend]);
    setStagedTheySend([...version.theySend]);
    setViewingVersion(null);
    setShowVersions(false);
  };

  const totalStaged = stagedYouSend.length + stagedTheySend.length;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="px-4 pt-2 pb-3 border-b border-ink-700/60">
        <View className="flex-row items-center justify-between">
          <Pressable onPress={() => router.replace("/trades")} className="p-1 -ml-1">
            <ChevronLeft color="#F2F7FC" size={24} />
          </Pressable>
          <View className="items-center">
            <Text className="text-fg text-lg font-extrabold">Trade Room</Text>
            <View className="flex-row items-center gap-1 mt-0.5">
              <Text className="text-fg-muted text-[11px]">{t.mine.name}</Text>
              <ArrowLeftRight color="#5A7186" size={11} />
              <Text className="text-fg-muted text-[11px]">{tradePartner.name}</Text>
            </View>
          </View>
          <Pressable
            onPress={() => setShowVersions(!showVersions)}
            className="p-1 -mr-1 flex-row items-center gap-1"
          >
            <History color="#F2F7FC" size={18} />
            {versions.length > 0 && (
              <View className="bg-accent rounded-full w-4 h-4 items-center justify-center">
                <Text className="text-ink-900 text-[9px] font-bold">
                  {versions.length}
                </Text>
              </View>
            )}
          </Pressable>
        </View>
      </View>

      <KeyboardAvoidingView
        className="flex-1"
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          className="flex-1"
          contentContainerStyle={{ paddingBottom: 16 }}
          showsVerticalScrollIndicator={false}
        >
          {/* Compact team header */}
          <CollapsibleTeamHeader
            mine={{
              emoji: t.mine.logoEmoji,
              name: t.mine.name,
              manager: t.mine.manager,
              strategy: t.mine.strategy,
              goals: t.mine.goals,
            }}
            theirs={{
              emoji: tradePartner.emoji,
              name: tradePartner.name,
              manager: tradePartner.manager,
              strategy: tradePartner.strategy,
              goals: t.theirs.goals,
            }}
          />

          {/* Asset columns — always visible */}
          <View className="flex-row px-4 pt-4 gap-3">
            <AssetColumn
              title="You Send"
              assets={stagedYouSend}
              committedAssets={committedYouSend}
              tone="accent"
              onAdd={() => setAddingTo("youSend")}
              onRemove={(id) => removeAsset("youSend", id)}
            />
            <AssetColumn
              title="They Send"
              assets={stagedTheySend}
              committedAssets={committedTheySend}
              tone="win"
              onAdd={() => setAddingTo("theySend")}
              onRemove={(id) => removeAsset("theySend", id)}
            />
          </View>

          {/* Unsaved changes indicator */}
          {hasChanges && (
            <View className="mx-4 mt-3 bg-warn/10 border border-warn/30 rounded-card px-3 py-2 flex-row items-center gap-2">
              <View className="w-2 h-2 rounded-full bg-warn" />
              <Text className="text-warn text-[12px] font-semibold flex-1">
                Unsent changes — tap Notify to update {tradePartner.manager}
              </Text>
            </View>
          )}

          {/* Tab bar — below assets */}
          <View className="flex-row px-4 pt-4 gap-2">
            {(["chat", "analysis", "changelog"] as TradeTab[]).map((tab) => (
              <Pressable
                key={tab}
                onPress={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-full border ${
                  activeTab === tab
                    ? "border-accent bg-accent/15"
                    : "border-ink-700 bg-ink-850"
                }`}
              >
                <Text
                  className={`text-[12px] font-semibold ${
                    activeTab === tab ? "text-accent" : "text-fg-muted"
                  }`}
                >
                  {tab === "chat"
                    ? "Chat"
                    : tab === "analysis"
                      ? "Analysis"
                      : "Change Log"}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Tab content */}
          {activeTab === "chat" && (
            <View className="px-4 pt-4 gap-3">
              {messages.length === 0 ? (
                <View className="items-center py-8">
                  <Text className="text-fg-faint text-[13px]">
                    No messages yet. Start the conversation.
                  </Text>
                </View>
              ) : (
                messages.map((m) => (
                  <ChatBubble
                    key={m.id}
                    author={m.author}
                    time={m.time}
                    text={m.text}
                    mine={m.mine}
                    emoji={m.mine ? t.mine.logoEmoji : tradePartner.emoji}
                  />
                ))
              )}
            </View>
          )}

          {activeTab === "changelog" && (
            <View className="px-4 pt-4">
              {changeLog.length === 0 ? (
                <View className="items-center py-8">
                  <Text className="text-fg-faint text-[13px]">
                    No changes yet. Add or remove assets to see the log.
                  </Text>
                </View>
              ) : (
                changeLog.map((entry) => (
                  <ChangeLogRow key={entry.id} entry={entry} />
                ))
              )}
            </View>
          )}

          {activeTab === "analysis" && (
            <TradeAnalysis
              youSend={stagedYouSend}
              theySend={stagedTheySend}
              mineEmoji={t.mine.logoEmoji}
              mineName={t.mine.name}
              mineStrategy={t.mine.strategy}
              theirEmoji={tradePartner.emoji}
              theirName={tradePartner.name}
              theirStrategy={tradePartner.strategy}
              impact={t.impact}
              bothAgreed={tradeStore.getBothAgreed()}
              onFinalize={() => router.push("/trade/finalize")}
            />
          )}
        </ScrollView>

        {/* Composer + Notify */}
        <View className="border-t border-ink-700/60 bg-ink-900 px-4 pt-2 pb-6">
          {/* Chat composer */}
          <View className="flex-row items-center gap-2">
            <Pressable className="p-2">
              <Plus color="#5A7186" size={20} />
            </Pressable>
            <View className="flex-1 flex-row items-center bg-ink-850 border border-ink-700 rounded-full px-3.5">
              <TextInput
                value={draft}
                onChangeText={setDraft}
                placeholder="Type a message…"
                placeholderTextColor="#5A7186"
                className="flex-1 py-2.5 text-fg text-[13px]"
              />
              <Pressable className="p-1">
                <Smile color="#5A7186" size={18} />
              </Pressable>
            </View>
            <Pressable onPress={sendMessage} className="p-2">
              <Send color={draft.trim() ? "#2AB3FF" : "#5A7186"} size={18} />
            </Pressable>
          </View>

          {/* Notify + Not Interested */}
          <View className="mt-3 gap-2">
            <Pressable
              onPress={notify}
              disabled={totalStaged === 0}
              className={`rounded-full py-3.5 items-center ${
                hasChanges
                  ? "bg-accent"
                  : totalStaged > 0
                    ? "bg-ink-700 border border-ink-600"
                    : "bg-ink-700"
              }`}
            >
              <View className="flex-row items-center gap-1.5">
                <Bell
                  color={hasChanges ? "#0A1420" : "#5A7186"}
                  size={15}
                />
                <Text
                  className={`text-[14px] font-bold ${
                    hasChanges ? "text-ink-900" : "text-fg-faint"
                  }`}
                >
                  {hasChanges
                    ? `Notify ${tradePartner.manager}`
                    : totalStaged > 0
                      ? `${tradePartner.manager} is up to date`
                      : "Add assets to start"}
                </Text>
              </View>
              {hasChanges && (
                <Text className="text-ink-900/70 text-[10px] font-semibold mt-0.5">
                  {stagedYouSend.length} you send · {stagedTheySend.length} they send
                </Text>
              )}
            </Pressable>

            {/* Not Interested */}
            <Pressable
              onPress={() => router.replace("/trades")}
              className="rounded-full py-3 items-center border border-loss/40 bg-loss/10"
            >
              <View className="flex-row items-center gap-1.5">
                <X color="#EF4444" size={14} />
                <Text className="text-loss text-[13px] font-bold">
                  Not Interested
                </Text>
              </View>
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>

      {/* ---- Asset Picker Modal ---- */}
      <Modal
        visible={addingTo !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setAddingTo(null)}
      >
        <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
          <View className="flex-row items-center justify-between px-4 py-3 border-b border-ink-700/60">
            <Pressable onPress={() => setAddingTo(null)} className="p-1 -ml-1">
              <ChevronLeft color="#F2F7FC" size={24} />
            </Pressable>
            <View className="items-center">
              <Text className="text-fg text-lg font-extrabold">Add Asset</Text>
              <Text className="text-fg-muted text-[11px] mt-0.5">
                {addingTo === "youSend"
                  ? `From your roster`
                  : `From ${tradePartner.name}'s roster`}
              </Text>
            </View>
            <View className="w-8" />
          </View>

          <View className="mx-4 mt-3 mb-2 flex-row items-center bg-ink-850 border border-ink-700 rounded-full px-4 py-2.5">
            <Search color="#5A7186" size={16} />
            <TextInput
              value={pickerSearch}
              onChangeText={setPickerSearch}
              placeholder="Search players or picks..."
              placeholderTextColor="#5A7186"
              className="flex-1 ml-2 text-fg text-sm"
            />
          </View>

          <ScrollView
            className="flex-1"
            contentContainerStyle={{ paddingBottom: 24 }}
            showsVerticalScrollIndicator={false}
          >
            {pickerPlayers.length > 0 && (
              <>
                <Text className="px-4 pt-3 pb-1.5 text-fg-faint text-[10px] font-bold tracking-widest">
                  PLAYERS ({pickerPlayers.length})
                </Text>
                {pickerPlayers.map((asset) => (
                  <PickerAssetRow
                    key={asset.id}
                    asset={asset}
                    onAdd={() => addAsset(asset)}
                  />
                ))}
              </>
            )}

            {pickerPicks.length > 0 && (
              <>
                <Text className="px-4 pt-4 pb-1.5 text-fg-faint text-[10px] font-bold tracking-widest">
                  DRAFT PICKS ({pickerPicks.length})
                </Text>
                {pickerPicks.map((asset) => (
                  <PickerAssetRow
                    key={asset.id}
                    asset={asset}
                    onAdd={() => addAsset(asset)}
                  />
                ))}
              </>
            )}

            {filteredPickerAssets.length === 0 && (
              <View className="items-center py-16">
                <Text className="text-fg-muted text-sm">
                  {pickerSearch.trim()
                    ? "No assets match your search."
                    : "All assets are already in the trade."}
                </Text>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* ---- Version History Dropdown ---- */}
      <Modal
        visible={showVersions}
        animationType="fade"
        transparent
        onRequestClose={() => setShowVersions(false)}
      >
        <Pressable
          className="flex-1 bg-black/60"
          onPress={() => setShowVersions(false)}
        >
          <View className="flex-1 justify-start items-end pt-24 pr-4">
            <Pressable
              onPress={(e) => e.stopPropagation()}
              className="bg-ink-850 border border-ink-700 rounded-card w-[280px] overflow-hidden"
            >
              {/* Header */}
              <View className="px-4 py-3 border-b border-ink-700">
                <Text className="text-fg text-[14px] font-bold">
                  Version History
                </Text>
                <Text className="text-fg-muted text-[11px] mt-0.5">
                  {versions.length} version{versions.length !== 1 ? "s" : ""}
                </Text>
              </View>

              {/* Current draft */}
              <Pressable
                onPress={() => {
                  setViewingVersion(null);
                  setShowVersions(false);
                }}
                className={`px-4 py-3 border-b border-ink-700/50 flex-row items-center ${
                  viewingVersion === null ? "bg-accent/10" : ""
                }`}
              >
                <View className="w-8 h-8 rounded-full bg-accent/15 items-center justify-center">
                  <Text className="text-accent text-[12px] font-bold">
                    {versions.length + 1}
                  </Text>
                </View>
                <View className="flex-1 ml-3">
                  <Text className="text-fg text-[13px] font-semibold">
                    Current Draft
                  </Text>
                  <Text className="text-fg-faint text-[10px] mt-0.5">
                    {stagedYouSend.length + stagedTheySend.length} assets
                    {hasChanges ? " · unsent changes" : ""}
                  </Text>
                </View>
                {viewingVersion === null && (
                  <View className="bg-accent/15 rounded-full px-2 py-0.5">
                    <Text className="text-accent text-[9px] font-bold">ACTIVE</Text>
                  </View>
                )}
              </Pressable>

              {/* Version list */}
              <ScrollView className="max-h-[300px]">
                {versions.map((v) => (
                  <Pressable
                    key={v.id}
                    onPress={() => {
                      setViewingVersion(v.version);
                    }}
                    className={`px-4 py-3 border-b border-ink-700/50 flex-row items-center ${
                      viewingVersion === v.version ? "bg-accent/10" : ""
                    }`}
                  >
                    <View className="w-8 h-8 rounded-full bg-ink-700 items-center justify-center">
                      <Text className="text-fg-muted text-[12px] font-bold">
                        {v.version}
                      </Text>
                    </View>
                    <View className="flex-1 ml-3">
                      <Text className="text-fg text-[13px] font-semibold">
                        Version {v.version}
                      </Text>
                      <Text className="text-fg-faint text-[10px] mt-0.5">
                        {v.youSend.length + v.theySend.length} assets · {v.changeCount} changes · {v.time}
                      </Text>
                    </View>
                    {v.isCurrent && (
                      <View className="bg-win/15 rounded-full px-2 py-0.5">
                        <Text className="text-win text-[9px] font-bold">SENT</Text>
                      </View>
                    )}
                  </Pressable>
                ))}
              </ScrollView>

              {/* Restore button when viewing a past version */}
              {viewingVersion !== null && (
                <View className="px-4 py-3 border-t border-ink-700">
                  <Pressable
                    onPress={() => {
                      const v = versions.find((x) => x.version === viewingVersion);
                      if (v) restoreVersion(v);
                    }}
                    className="flex-row items-center justify-center gap-2 bg-warn/15 border border-warn/40 rounded-full py-2.5"
                  >
                    <RotateCcw color="#F59E0B" size={14} />
                    <Text className="text-warn text-[13px] font-bold">
                      Restore Version {viewingVersion}
                    </Text>
                  </Pressable>
                </View>
              )}

              {versions.length === 0 && (
                <View className="px-4 py-6 items-center">
                  <Text className="text-fg-faint text-[12px]">
                    No versions yet. Tap Notify to save a version.
                  </Text>
                </View>
              )}
            </Pressable>
          </View>
        </Pressable>
      </Modal>

      <BottomNav active="trades" />
    </SafeAreaView>
  );
}

/* ---------------- Sub-components ---------------- */

interface TeamInfo {
  emoji: string;
  name: string;
  manager: string;
  strategy: string;
  goals: string[];
}

function CollapsibleTeamHeader({
  mine,
  theirs,
}: {
  mine: TeamInfo;
  theirs: TeamInfo;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <View className="mx-4 mt-3">
      <Pressable
        onPress={() => setExpanded(!expanded)}
        className="bg-ink-850 border border-ink-700 rounded-card px-3 py-2.5 flex-row items-center"
      >
        <View className="flex-row items-center gap-1.5 flex-1">
          <View className="w-7 h-7 rounded-full items-center justify-center border border-win/60 bg-win/10">
            <Text className="text-sm">{mine.emoji}</Text>
          </View>
          <Text className="text-fg text-[12px] font-bold" numberOfLines={1}>
            {mine.name}
          </Text>
          <Text className="text-win text-[10px] font-semibold">
            {mine.strategy}
          </Text>
        </View>

        <ArrowLeftRight color="#5A7186" size={14} />

        <View className="flex-row items-center gap-1.5 flex-1 justify-end">
          <Text className="text-accent text-[10px] font-semibold">
            {theirs.strategy}
          </Text>
          <Text className="text-fg text-[12px] font-bold" numberOfLines={1}>
            {theirs.name}
          </Text>
          <View className="w-7 h-7 rounded-full items-center justify-center border border-accent/60 bg-accent/10">
            <Text className="text-sm">{theirs.emoji}</Text>
          </View>
        </View>

        <View className="ml-2">
          {expanded ? (
            <ChevronUp color="#5A7186" size={14} />
          ) : (
            <ChevronDown color="#5A7186" size={14} />
          )}
        </View>
      </Pressable>

      {expanded && (
        <View className="flex-row gap-3 mt-2">
          <GoalsCard label="Our Goals" goals={mine.goals} />
          <GoalsCard label="Their Goals" goals={theirs.goals} />
        </View>
      )}
    </View>
  );
}

function GoalsCard({ label, goals }: { label: string; goals: string[] }) {
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3">
      <Text className="text-fg-faint text-[10px] font-semibold mb-1.5">
        {label}
      </Text>
      <View className="flex-row flex-wrap gap-1">
        {goals.map((g, i) => (
          <View
            key={g}
            className={`rounded-full px-2 py-0.5 border ${
              i === 0
                ? "bg-win/15 border-win/40"
                : "bg-ink-800 border-ink-700"
            }`}
          >
            <Text
              className={`text-[10px] font-semibold ${
                i === 0 ? "text-win" : "text-fg-muted"
              }`}
            >
              {g}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function AssetColumn({
  title,
  assets,
  committedAssets,
  tone,
  onAdd,
  onRemove,
}: {
  title: string;
  assets: TradeAsset[];
  committedAssets: TradeAsset[];
  tone: "win" | "accent";
  onAdd: () => void;
  onRemove: (assetId: string) => void;
}) {
  const border = tone === "win" ? "border-win/40" : "border-ink-700";
  const committedIds = new Set(committedAssets.map((a) => a.id));

  return (
    <View className={`flex-1 bg-ink-850 border ${border} rounded-card p-3`}>
      <View className="flex-row items-baseline justify-between mb-2">
        <Text className="text-fg text-[13px] font-bold">{title}</Text>
        <Text className="text-fg-faint text-[10px]">
          {assets.length} assets
        </Text>
      </View>
      <View className="gap-2">
        {assets.map((a) => (
          <AssetRow
            key={a.id}
            asset={a}
            isNew={!committedIds.has(a.id)}
            onRemove={() => onRemove(a.id)}
          />
        ))}
        <Pressable
          onPress={onAdd}
          className="flex-row items-center justify-center gap-1.5 border border-dashed border-ink-600 rounded-lg py-2.5"
        >
          <Plus color="#5A7186" size={14} />
          <Text className="text-fg-muted text-[12px] font-semibold">
            Add Asset
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

function AssetRow({
  asset,
  isNew,
  onRemove,
}: {
  asset: TradeAsset;
  isNew: boolean;
  onRemove: () => void;
}) {
  return (
    <View
      className={`flex-row items-center gap-2 rounded-lg px-1 py-1 ${
        isNew ? "bg-win/5 border border-win/20" : ""
      }`}
    >
      {asset.kind === "player" ? (
        <PlayerHeadshot url={asset.headshotUrl} size={28} />
      ) : (
        <View className="w-7 h-7 rounded-full bg-ink-700 items-center justify-center">
          <Text className="text-[13px]">🎟️</Text>
        </View>
      )}
      <View className="flex-1">
        <Text className="text-fg text-[12px] font-semibold" numberOfLines={1}>
          {asset.name}
        </Text>
        <Text className="text-fg-faint text-[10px]">{asset.detail}</Text>
      </View>
      {isNew && (
        <View className="bg-win/15 rounded-full px-1.5 py-0.5">
          <Text className="text-win text-[8px] font-bold">NEW</Text>
        </View>
      )}
      <Pressable onPress={onRemove} className="p-0.5">
        <X color="#5A7186" size={14} />
      </Pressable>
    </View>
  );
}

function PickerAssetRow({
  asset,
  onAdd,
}: {
  asset: AvailableTradeAsset;
  onAdd: () => void;
}) {
  return (
    <Pressable
      onPress={onAdd}
      className="flex-row items-center py-2.5 px-4 border-b border-ink-700/60"
    >
      {asset.kind === "player" ? (
        <PlayerHeadshot url={asset.headshotUrl} size={36} />
      ) : (
        <View className="w-9 h-9 rounded-full bg-ink-700 items-center justify-center">
          <Text className="text-[15px]">🎟️</Text>
        </View>
      )}
      <View className="flex-1 ml-2.5">
        <Text className="text-fg text-[13px] font-semibold" numberOfLines={1}>
          {asset.name}
        </Text>
        <Text className="text-fg-muted text-[11px] mt-0.5">
          {asset.detail}
          {asset.projectedPoints
            ? ` · ${asset.projectedPoints.toFixed(1)} proj`
            : ""}
        </Text>
      </View>
      <View className="flex-row items-center gap-1 rounded-full px-3 py-1.5 border border-accent bg-accent/10">
        <Plus color="#2AB3FF" size={13} />
        <Text className="text-accent text-[12px] font-bold">Add</Text>
      </View>
    </Pressable>
  );
}

function ChatBubble({
  author,
  time,
  text,
  mine,
  emoji,
}: {
  author: string;
  time: string;
  text: string;
  mine: boolean;
  emoji: string;
}) {
  return (
    <View className={`flex-row gap-2 ${mine ? "" : "flex-row-reverse"}`}>
      <Text className="text-lg mt-0.5">{emoji}</Text>
      <View className={`flex-1 ${mine ? "items-start" : "items-end"}`}>
        <Text className="text-fg-faint text-[10px] mb-1">
          {author} · {time}
        </Text>
        <View
          className={`rounded-2xl px-3 py-2 ${
            mine
              ? "bg-ink-800 rounded-tl-sm"
              : "bg-accent/15 border border-accent/30 rounded-tr-sm"
          }`}
        >
          <Text className="text-fg text-[13px] leading-5">{text}</Text>
        </View>
      </View>
    </View>
  );
}

function ChangeLogRow({ entry }: { entry: ChangeLogEntry }) {
  const isAdd = entry.action === "added";
  return (
    <View className="flex-row items-center py-2.5 border-b border-ink-700/60">
      {/* Action icon */}
      <View
        className={`w-7 h-7 rounded-full items-center justify-center ${
          isAdd ? "bg-win/15" : "bg-loss/15"
        }`}
      >
        {isAdd ? (
          <Plus color="#22C55E" size={14} />
        ) : (
          <X color="#EF4444" size={14} />
        )}
      </View>

      {/* Details */}
      <View className="flex-1 ml-2.5">
        <Text className="text-fg text-[12px] font-semibold">
          {entry.assetName}
        </Text>
        <Text className="text-fg-muted text-[10px] mt-0.5">
          {isAdd ? "Added to" : "Removed from"}{" "}
          {entry.side === "youSend" ? "You Send" : "They Send"}
        </Text>
      </View>

      {/* Status + time */}
      <View className="items-end">
        <View
          className={`rounded-full px-2 py-0.5 ${
            entry.committed ? "bg-win/15" : "bg-warn/15"
          }`}
        >
          <Text
            className={`text-[9px] font-bold ${
              entry.committed ? "text-win" : "text-warn"
            }`}
          >
            {entry.committed ? "SENT" : "PENDING"}
          </Text>
        </View>
        <Text className="text-fg-faint text-[10px] mt-0.5">{entry.time}</Text>
      </View>
    </View>
  );
}

/* ---------------- Trade Analysis Tab ---------------- */

interface ImpactRowShape {
  label: string;
  mine: string;
  theirs: string;
  mineGood: boolean | null;
  theirsGood: boolean | null;
}

function TradeAnalysis({
  youSend,
  theySend,
  mineEmoji,
  mineName,
  mineStrategy,
  theirEmoji,
  theirName,
  theirStrategy,
  impact,
  bothAgreed,
  onFinalize,
}: {
  youSend: TradeAsset[];
  theySend: TradeAsset[];
  mineEmoji: string;
  mineName: string;
  mineStrategy: string;
  theirEmoji: string;
  theirName: string;
  theirStrategy: string;
  impact: ImpactRowShape[];
  bothAgreed: boolean;
  onFinalize: () => void;
}) {
  const hasAssets = youSend.length + theySend.length > 0;

  if (!hasAssets) {
    return (
      <View className="items-center py-12 px-8">
        <TrendingUp color="#5A7186" size={28} />
        <Text className="text-fg-muted text-[13px] text-center mt-3 leading-5">
          Add assets to the trade to see how it impacts both teams.
        </Text>
      </View>
    );
  }

  return (
    <View className="pt-4">
      {/* Proposed trade summary */}
      <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
        <View className="flex-row items-center justify-between mb-3">
          <Text className="text-fg text-[13px] font-bold">
            Proposed Trade{" "}
            <Text className="text-fg-faint font-semibold">(Discussion)</Text>
          </Text>
        </View>
        <View className="flex-row gap-3">
          <AnalysisColumn
            title="You Receive"
            assets={theySend}
            tone="win"
          />
          <AnalysisColumn
            title="They Receive"
            assets={youSend}
            tone="accent"
          />
        </View>
      </View>

      {/* Trade impact */}
      <Text className="text-fg text-[14px] font-bold px-4 pt-5 pb-2">
        Trade Impact
      </Text>
      <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
        <View className="flex-row">
          <AnalysisTeam emoji={mineEmoji} name={mineName} strategy={mineStrategy} strategyColor="text-win" rows={impact.map((r) => ({ label: r.label, value: r.mine, good: r.mineGood }))} />
          <View className="w-px bg-ink-700 mx-2" />
          <AnalysisTeam emoji={theirEmoji} name={theirName} strategy={theirStrategy} strategyColor="text-accent" rows={impact.map((r) => ({ label: r.label, value: r.theirs, good: r.theirsGood }))} />
        </View>
      </View>

      {/* Verdict */}
      <View className="mx-4 mt-3 flex-row items-start bg-win/10 border border-win/30 rounded-card p-3.5 gap-2.5">
        <CircleCheck color="#22C55E" size={16} />
        <View className="flex-1">
          <Text className="text-win text-[13px] font-bold">
            This trade helps you win now
          </Text>
          <Text className="text-fg-muted text-[12px] leading-5 mt-0.5">
            You add a top starting goalie at the cost of future value. This
            aligns with your current {mineStrategy} strategy.
          </Text>
        </View>
      </View>

      {/* Finalize CTA — review is always available; submit unlocks once both agree */}
      <View className="px-4 mt-5">
        <Pressable
          onPress={onFinalize}
          className="rounded-full py-3.5 items-center bg-accent"
        >
          <Text className="text-ink-900 text-[14px] font-bold">
            {bothAgreed ? "Review & Finalize Trade" : "Review Trade Terms"}
          </Text>
        </Pressable>
        {!bothAgreed && (
          <Text className="text-fg-faint text-[11px] text-center mt-2 leading-4">
            The trade can only be submitted once both managers agree.{"\n"}
            Review the terms and mark your agreement on the next screen.
          </Text>
        )}
      </View>
    </View>
  );
}

function AnalysisColumn({
  title,
  assets,
  tone,
}: {
  title: string;
  assets: TradeAsset[];
  tone: "win" | "accent";
}) {
  const border = tone === "win" ? "border-win/40" : "border-ink-700";
  return (
    <View className={`flex-1 bg-ink-800 border ${border} rounded-card p-2.5`}>
      <Text className="text-fg-faint text-[9px] font-bold tracking-widest mb-2">
        {title.toUpperCase()}
      </Text>
      <View className="gap-2">
        {assets.map((a) => (
          <View key={a.id} className="flex-row items-center gap-2">
            {a.kind === "player" ? (
              <PlayerHeadshot url={a.headshotUrl} size={24} />
            ) : (
              <View className="w-6 h-6 rounded-full bg-ink-700 items-center justify-center">
                <Text className="text-[11px]">🎟️</Text>
              </View>
            )}
            <View className="flex-1">
              <Text className="text-fg text-[11px] font-semibold" numberOfLines={1}>
                {a.name}
              </Text>
              <Text className="text-fg-faint text-[9px]">{a.detail}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

function AnalysisTeam({
  emoji,
  name,
  strategy,
  strategyColor,
  rows,
}: {
  emoji: string;
  name: string;
  strategy: string;
  strategyColor: string;
  rows: { label: string; value: string; good: boolean | null }[];
}) {
  return (
    <View className="flex-1">
      <View className="flex-row items-center gap-1.5 mb-2.5">
        <Text className="text-lg">{emoji}</Text>
        <View>
          <Text className="text-fg text-[12px] font-bold" numberOfLines={1}>
            {name}
          </Text>
          <Text className={`text-[9px] font-semibold ${strategyColor}`}>
            {strategy}
          </Text>
        </View>
      </View>
      <View className="gap-2.5">
        {rows.map((r) => (
          <View key={r.label} className="flex-row items-center justify-between">
            <Text className="text-fg-muted text-[11px]">{r.label}</Text>
            <Text
              className={`text-[12px] font-bold ${
                r.good === true
                  ? "text-win"
                  : r.good === false
                    ? "text-loss"
                    : "text-fg"
              }`}
            >
              {r.value}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}