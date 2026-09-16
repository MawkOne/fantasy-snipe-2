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
  Check,
  ChevronLeft,
  Info,
  Send,
} from "lucide-react-native";

import { ACTIVE_TRADE, type TradeAsset } from "../../src/data/mock";
import * as tradeStore from "../../src/data/tradeStore";
import { PlayerHeadshot } from "../../src/components/PlayerHeadshot";
import { BottomNav } from "../../src/components/BottomNav";

const STEPS = ["Discuss", "Agree", "Review", "Submit"];

export default function FinalizeTradeScreen() {
  const router = useRouter();
  const t = ACTIVE_TRADE;

  const youSend = tradeStore.getYouSend();
  const theySend = tradeStore.getTheySend();
  const [mineAgreed, setMineAgreed] = useState(tradeStore.getMineAgreed());
  const [theirAgreed] = useState(tradeStore.getTheirAgreed());
  const [note, setNote] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const bothAgreed = mineAgreed && theirAgreed;
  // Step: 0 Discuss, 1 Agree, 2 Review (both agreed), 3 Submit (done)
  const currentStep = submitted ? 3 : bothAgreed ? 2 : 1;

  const submit = () => {
    tradeStore.setMineAgreed(true);
    setSubmitted(true);
    // In a real app this would POST to the league for processing.
  };

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Nav */}
      <View className="px-4 pt-2 pb-3 border-b border-ink-700/60">
        <View className="flex-row items-center justify-between">
          <Pressable onPress={() => router.back()} className="p-1 -ml-1">
            <ChevronLeft color="#F2F7FC" size={24} />
          </Pressable>
          <View className="items-center">
            <Text className="text-fg text-lg font-extrabold">
              Finalize Trade
            </Text>
            <Text className="text-fg-muted text-[11px] mt-0.5">
              Both managers approve the final trade
            </Text>
          </View>
          <View className="w-8" />
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Stepper */}
        <Stepper steps={STEPS} current={currentStep} />

        {/* Trade summary header — teams */}
        <Text className="text-fg text-[14px] font-bold px-4 pt-5 pb-2">
          Trade Summary
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="flex-row items-center justify-between">
            <TeamHeader
              emoji={t.mine.logoEmoji}
              name={t.mine.name}
              tag="You"
              strategy={t.mine.strategy}
              strategyColor="text-win"
            />
            <ArrowLeftRight color="#5A7186" size={18} />
            <TeamHeader
              emoji={t.theirs.logoEmoji}
              name={t.theirs.name}
              tag={t.theirs.manager}
              strategy={t.theirs.strategy}
              strategyColor="text-accent"
              alignRight
            />
          </View>
        </View>

        {/* Receive columns */}
        <View className="flex-row px-4 gap-3 mt-3">
          <ReceiveColumn
            title="You Receive"
            assets={theySend}
            tone="win"
          />
          <ReceiveColumn
            title="They Receive"
            assets={youSend}
            tone="accent"
          />
        </View>

        {/* League validation */}
        <Text className="text-fg text-[14px] font-bold px-4 pt-5 pb-2">
          League Validation
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5">
          <View className="gap-2.5">
            <ValidationRow label="Roster rules" status="Valid" />
            <ValidationRow label="Position requirements" status="Valid" />
            <ValidationRow label="Trade deadline" status="Open" />
            <ValidationRow label="Keeper/dynasty rules" status="Valid" />
            <View className="flex-row items-center gap-1.5">
              <Check color="#22C55E" size={14} />
              <Text className="flex-1 text-fg-muted text-[11px]" numberOfLines={1}>
                No veto rules
              </Text>
              <Info color="#5A7186" size={13} />
              <Text className="text-fg-muted text-[10px]">
                Requires commissioner approval
              </Text>
            </View>
          </View>
        </View>

        {/* Agreement */}
        <Text className="text-fg text-[14px] font-bold px-4 pt-5 pb-2">
          Agreement
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-3.5 gap-2.5">
          <AgreementRow
            emoji={t.mine.logoEmoji}
            name={t.mine.name}
            agreed={mineAgreed}
            onToggle={() => {
              if (submitted) return;
              const next = !mineAgreed;
              setMineAgreed(next);
              tradeStore.setMineAgreed(next);
            }}
            disabled={submitted}
          />
          <AgreementRow
            emoji={t.theirs.logoEmoji}
            name={`${t.theirs.name} (${t.theirs.manager})`}
            agreed={theirAgreed}
          />
        </View>

        {/* Commissioner note */}
        <Text className="text-fg-faint text-[11px] px-4 pt-4 pb-1.5">
          Add a note for the commissioner (optional)
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-3.5 py-2.5">
          <TextInput
            value={note}
            onChangeText={setNote}
            placeholder="e.g. Strategic move for playoffs and future assets."
            placeholderTextColor="#5A7186"
            multiline
            className="text-fg text-[13px] min-h-[40px]"
            style={{ outlineStyle: "none" } as never}
          />
        </View>

        {/* Actions */}
        <View className="px-4 mt-6">
          {submitted ? (
            <View className="rounded-card bg-win/10 border border-win/40 p-4 items-center">
              <Check color="#22C55E" size={22} />
              <Text className="text-win text-[15px] font-bold mt-2">
                Trade Submitted
              </Text>
              <Text className="text-fg-muted text-[12px] text-center mt-1 leading-4">
                Sent to the league for commissioner approval.
              </Text>
            </View>
          ) : (
            <Pressable
              onPress={submit}
              disabled={!bothAgreed}
              className={`rounded-full py-3.5 items-center flex-row justify-center gap-2 ${
                bothAgreed ? "bg-accent" : "bg-ink-700"
              }`}
            >
              <Send color={bothAgreed ? "#0A1420" : "#5A7186"} size={15} />
              <Text
                className={`text-[14px] font-bold ${
                  bothAgreed ? "text-ink-900" : "text-fg-faint"
                }`}
              >
                Submit Trade for Approval
              </Text>
            </Pressable>
          )}
          {!bothAgreed && !submitted && (
            <Text className="text-fg-faint text-[11px] text-center mt-2.5 leading-4">
              Both managers must agree before the trade can be submitted.
            </Text>
          )}
          <Pressable
            onPress={() => router.back()}
            className="mt-3 rounded-full py-3.5 items-center border border-ink-600 bg-ink-850"
          >
            <Text className="text-fg text-[14px] font-bold">
              Back to Discussion
            </Text>
          </Pressable>
        </View>
      </ScrollView>

      <BottomNav active="trades" />
    </SafeAreaView>
  );
}

/* ---------------- Sub-components ---------------- */

function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <View className="flex-row items-start px-6 pt-4">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <View key={label} className="flex-1 items-center">
            <View className="flex-row items-center w-full">
              {i > 0 ? (
                <View
                  className={`flex-1 h-0.5 ${
                    i <= current ? "bg-accent" : "bg-ink-700"
                  }`}
                />
              ) : null}
              <View
                className={`w-6 h-6 rounded-full items-center justify-center border-2 ${
                  done || active
                    ? "bg-accent border-accent"
                    : "bg-ink-800 border-ink-600"
                }`}
              >
                {done ? (
                  <Check color="#0A1420" size={13} />
                ) : (
                  <Text
                    className={`text-[11px] font-bold ${
                      active ? "text-ink-900" : "text-fg-faint"
                    }`}
                  >
                    {i + 1}
                  </Text>
                )}
              </View>
              {i < steps.length - 1 ? (
                <View
                  className={`flex-1 h-0.5 ${
                    i < current ? "bg-accent" : "bg-ink-700"
                  }`}
                />
              ) : null}
            </View>
            <Text
              className={`text-[10px] mt-1.5 text-center ${
                active ? "text-fg font-semibold" : "text-fg-faint"
              }`}
            >
              {label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

function TeamHeader({
  emoji,
  name,
  tag,
  strategy,
  strategyColor,
  alignRight,
}: {
  emoji: string;
  name: string;
  tag: string;
  strategy: string;
  strategyColor: string;
  alignRight?: boolean;
}) {
  return (
    <View className={`flex-1 ${alignRight ? "items-end" : "items-start"}`}>
      <View
        className={`flex-row items-center gap-2 ${
          alignRight ? "flex-row-reverse" : ""
        }`}
      >
        <Text className="text-2xl">{emoji}</Text>
        <View className={alignRight ? "items-end" : ""}>
          <Text className="text-fg text-[13px] font-bold">{name}</Text>
          <Text className="text-fg-faint text-[10px] mt-0.5">
            {tag} ·{" "}
            <Text className={`${strategyColor} font-semibold`}>{strategy}</Text>
          </Text>
        </View>
      </View>
    </View>
  );
}

function ReceiveColumn({
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
    <View className={`flex-1 bg-ink-850 border ${border} rounded-card p-3`}>
      <Text className="text-fg text-[12px] font-bold mb-2">{title}</Text>
      <View className="gap-2.5">
        {assets.map((a) => (
          <View key={a.id} className="flex-row items-center gap-2">
            {a.kind === "player" ? (
              <PlayerHeadshot url={a.headshotUrl} size={26} />
            ) : (
              <View className="w-[26px] h-[26px] rounded-full bg-ink-700 items-center justify-center">
                <Text className="text-[12px]">🎟️</Text>
              </View>
            )}
            <View className="flex-1">
              <Text
                className="text-fg text-[12px] font-semibold"
                numberOfLines={1}
              >
                {a.name}
              </Text>
              <Text className="text-fg-faint text-[10px]">{a.detail}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
}

function ValidationRow({ label, status }: { label: string; status: string }) {
  return (
    <View className="flex-row items-center gap-1.5">
      <Check color="#22C55E" size={14} />
      <Text className="flex-1 text-fg-muted text-[11px]" numberOfLines={1}>
        {label}
      </Text>
      <Text className="text-win text-[11px] font-bold">{status}</Text>
    </View>
  );
}

function AgreementRow({
  emoji,
  name,
  agreed,
  onToggle,
  disabled = false,
}: {
  emoji: string;
  name: string;
  agreed: boolean;
  onToggle?: () => void;
  disabled?: boolean;
}) {
  const inner = (
    <>
      <Text className="text-xl">{emoji}</Text>
      <Text className="flex-1 text-fg text-[13px] font-semibold ml-2.5">
        {name}
      </Text>
      <View
        className={`w-6 h-6 rounded-full items-center justify-center border-2 ${
          agreed ? "bg-win border-win" : "border-ink-600"
        }`}
      >
        {agreed && <Check color="#0A1420" size={13} strokeWidth={3} />}
      </View>
    </>
  );

  if (onToggle) {
    return (
      <Pressable onPress={onToggle} disabled={disabled} className="flex-row items-center">
        {inner}
      </Pressable>
    );
  }
  return <View className="flex-row items-center">{inner}</View>;
}
