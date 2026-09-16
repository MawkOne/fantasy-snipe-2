import { useState } from "react";
import { Modal, Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter, type Href } from "expo-router";
import { ArrowRight, Calendar, Check, Lock, Play, Zap } from "lucide-react-native";

import { OffseasonNav } from "../../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../../src/components/BottomNav";
import { useOffseason } from "../../../src/components/offseason/OffseasonProvider";
import {
  OFFSEASON_STEPS,
  OFFSEASON_STEP_DETAILS,
} from "../../../src/data/offseason";

export default function OffseasonStepScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const detail = id ? OFFSEASON_STEP_DETAILS[id] : undefined;

  const { liveStage } = useOffseason();

  // Start-stage confirmation modal
  const [showStartModal, setShowStartModal] = useState(false);
  const [notifyOwners, setNotifyOwners] = useState(true);

  const confirmStart = () => {
    setShowStartModal(false);
    if (notifyOwners) {
      // Backend: notify all GMs that this stage is now live.
      console.log(`[mock] Notifying team owners: ${detail!.title} stage started`);
    }
    router.push(detail!.action!.route as Href);
  };

  if (!detail || !id) {
    router.back();
    return null;
  }

  const liveIndex = OFFSEASON_STEPS.findIndex((s) => s.id === liveStage);
  const stageIndex = OFFSEASON_STEPS.findIndex((s) => s.id === id);
  const isLive = id === liveStage;
  const isDone = stageIndex < liveIndex;

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav title={detail.title} subtitle="2026 Offseason" />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Status */}
        <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4">
          <View className="flex-row items-center gap-2 mb-2">
            {isLive ? (
              <>
                <Zap color="#2AB3FF" size={14} />
                <Text className="text-accent text-[11px] font-bold tracking-widest">
                  LIVE NOW
                </Text>
              </>
            ) : isDone ? (
              <>
                <Check color="#22C55E" size={14} />
                <Text className="text-win text-[11px] font-bold tracking-widest">
                  COMPLETE
                </Text>
              </>
            ) : (
              <>
                <Lock color="#F59E0B" size={14} />
                <Text className="text-warn text-[11px] font-bold tracking-widest">
                  NOT STARTED
                </Text>
              </>
            )}
          </View>
          <Text className="text-fg text-[15px] font-extrabold">
            {detail.title}
          </Text>
          <Text className="text-fg-muted text-[13px] mt-1.5 leading-5">
            {detail.description}
          </Text>
          <View className="flex-row items-center gap-2 mt-3 pt-3 border-t border-ink-700/60">
            <Calendar color="#2AB3FF" size={14} />
            <Text className="text-fg text-[12px] font-semibold">
              {detail.window}
            </Text>
          </View>
        </View>

        {/* What happens in this step */}
        <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          WHAT HAPPENS IN THIS STEP
        </Text>
        <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-4 gap-2.5">
          {detail.bullets.map((b) => (
            <View key={b} className="flex-row">
              <View className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 mr-2.5" />
              <Text className="flex-1 text-fg-muted text-[13px] leading-5">
                {b}
              </Text>
            </View>
          ))}
        </View>

        {/* Stage action (deep-link) */}
        {detail.action && (
          <Pressable
            onPress={() => setShowStartModal(true)}
            className="mx-4 mt-4 bg-accent rounded-full py-3.5 flex-row items-center justify-center gap-2"
          >
            <Text className="text-ink-900 text-[15px] font-bold">
              {detail.action.label}
            </Text>
            <ArrowRight color="#0A1420" size={16} />
          </Pressable>
        )}
      </ScrollView>

      <BottomNav active="offseason" />

      {/* Start stage confirmation modal */}
      <Modal
        visible={showStartModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowStartModal(false)}
      >
        <View className="flex-1 bg-black/60 items-center justify-center px-6">
          <View className="w-full bg-ink-850 border border-ink-700 rounded-card p-5">
            <View className="w-12 h-12 rounded-full bg-accent/15 border border-accent/40 items-center justify-center self-center">
              <Play color="#2AB3FF" size={22} />
            </View>
            <Text className="text-fg text-lg font-extrabold text-center mt-3">
              Start {detail.title}?
            </Text>
            <Text className="text-fg-muted text-[13px] leading-5 text-center mt-2">
              Opening the {detail.title.toLocaleLowerCase()} stage. Team owners
              will be able to participate once it is live.
            </Text>

            {/* Notify checkbox */}
            <Pressable
              onPress={() => setNotifyOwners((v) => !v)}
              className="flex-row items-center mt-4 px-1"
            >
              <View
                className={`w-5 h-5 rounded-md border-2 items-center justify-center ${
                  notifyOwners
                    ? "bg-accent border-accent"
                    : "border-ink-600"
                }`}
              >
                {notifyOwners && (
                  <Check color="#0A1420" size={12} strokeWidth={3} />
                )}
              </View>
              <Text className="text-fg text-[13px] font-semibold ml-2.5">
                Notify all Team Owners
              </Text>
            </Pressable>

            <View className="flex-row gap-2.5 mt-5">
              <Pressable
                onPress={() => setShowStartModal(false)}
                className="flex-1 py-3.5 items-center rounded-full border border-ink-600 bg-ink-800"
              >
                <Text className="text-fg text-[15px] font-bold">Cancel</Text>
              </Pressable>
              <Pressable
                onPress={confirmStart}
                className="flex-1 py-3.5 items-center rounded-full bg-accent"
              >
                <Text className="text-ink-900 text-[15px] font-bold">
                  Start Stage
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}