import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { Check, ChevronRight, ShieldCheck } from "lucide-react-native";

import { OffseasonHeader } from "./OffseasonHeader";
import { STAGE_ICONS } from "./stageIcons";
import { useOffseason } from "./OffseasonProvider";
import {
  OFFSEASON_STEPS,
  OFFSEASON_STEP_DETAILS,
} from "../../data/offseason";

/**
 * Offseason landing screen — shows every stage with its status.
 * The gear in the header enters admin mode, where tapping a stage
 * sets it as the LIVE stage (updating the middle tab bar entry).
 */
export function OffseasonHub() {
  const router = useRouter();
  const { liveStage, setLiveStage, completedStages } = useOffseason();
  const [admin, setAdmin] = useState(false);

  const liveIndex = OFFSEASON_STEPS.findIndex((s) => s.id === liveStage);

  return (
    <View className="flex-1">
      <OffseasonHeader
        admin={admin}
        onAdminToggle={() => setAdmin((v) => !v)}
      />

      {admin && (
        <View className="mx-4 mt-3 flex-row items-center gap-2.5 bg-warn/10 border border-warn/30 rounded-card px-3.5 py-2.5">
          <ShieldCheck color="#F59E0B" size={16} />
          <Text className="flex-1 text-warn text-[12px] font-bold leading-4">
            Admin mode — tap a stage to set it live
          </Text>
        </View>
      )}

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        <Text className="px-4 pt-4 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
          OFFSEASON STAGES
        </Text>

        {OFFSEASON_STEPS.map((step, i) => {
          const Icon = STAGE_ICONS[step.id];
          const detail = OFFSEASON_STEP_DETAILS[step.id];
          const isLive = step.id === liveStage;
          const isDone =
            completedStages.includes(step.id) || i < liveIndex;

          return (
            <Pressable
              key={step.id}
              onPress={() =>
                admin
                  ? setLiveStage(step.id)
                  : router.push({
                      pathname: "/offseason/step/[id]",
                      params: { id: step.id },
                    })
              }
              className={`mx-4 mb-2 flex-row items-center rounded-card border p-3 ${
                isLive
                  ? "border-accent bg-accent/10"
                  : "border-ink-700 bg-ink-850"
              }`}
            >
              {/* Stage badge */}
              <View
                className={`w-9 h-9 rounded-full items-center justify-center ${
                  isLive
                    ? "bg-accent"
                    : isDone
                      ? "bg-win/15 border border-win/40"
                      : "bg-ink-800 border border-ink-600"
                }`}
              >
                {isDone ? (
                  <Check color="#22C55E" size={16} strokeWidth={3} />
                ) : (
                  <Icon color={isLive ? "#0A1420" : "#2AB3FF"} size={16} />
                )}
              </View>

              <View className="flex-1 ml-3">
                <Text
                  className={`text-[14px] font-bold ${
                    isLive ? "text-accent" : "text-fg"
                  }`}
                >
                  {i + 1}. {step.label}
                </Text>
                <Text className="text-fg-muted text-[11px] mt-0.5">
                  {detail.window}
                </Text>
              </View>

              {admin ? (
                <View
                  className={`rounded-full px-2.5 py-1 ${
                    isLive ? "bg-accent" : "bg-ink-700"
                  }`}
                >
                  <Text
                    className={`text-[10px] font-bold tracking-widest ${
                      isLive ? "text-ink-900" : "text-fg-faint"
                    }`}
                  >
                    {isLive ? "LIVE" : "SET LIVE"}
                  </Text>
                </View>
              ) : (
                <View
                  className={`rounded-full px-2.5 py-1 ${
                    isLive
                      ? "bg-accent"
                      : isDone
                        ? "bg-win/15"
                        : "bg-ink-700"
                  }`}
                >
                  <Text
                    className={`text-[10px] font-bold tracking-widest ${
                      isLive
                        ? "text-ink-900"
                        : isDone
                          ? "text-win"
                          : "text-fg-faint"
                    }`}
                  >
                    {isLive ? "LIVE" : isDone ? "DONE" : "UPCOMING"}
                  </Text>
                </View>
              )}

              {!admin && (
                <View className="ml-1">
                  <ChevronRight color="#5A7186" size={16} />
                </View>
              )}
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}