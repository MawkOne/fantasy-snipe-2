import { useState } from "react";
import { Modal, Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  AlertTriangle,
  Check,
  ChevronRight,
  Flag,
  Info,
  Loader,
  Pencil,
  Trash2,
  X,
  XCircle,
} from "lucide-react-native";

import { OffseasonNav } from "../../src/components/offseason/OffseasonNav";
import { BottomNav } from "../../src/components/BottomNav";
import { useOffseason } from "../../src/components/offseason/OffseasonProvider";
import type { DraftTeam } from "../../src/data/rookieDraft";
import {
  BUYOUT_WARNINGS,
  LEAGUE_TEAMS,
  MY_TEAM_ID,
  OFFSEASON_STEPS,
  OFFSEASON_YEAR,
  TEAM_BUYOUT_STATUS,
  TEAM_BUYOUT_SUBMISSIONS,
  TEAM_ROSTER_SNAPSHOTS,
  type BuyoutSubmission,
} from "../../src/data/offseason";
import { getBoughtOut } from "../../src/data/offseasonStore";

type BuyoutStatus = "done" | "in_progress";
type DisplayStatus = "done" | "in_progress" | "no_buyouts";

export default function BuyoutTeamStatusScreen() {
  const router = useRouter();
  const { completedStages, completeStage, setLiveStage } = useOffseason();
  const [finished, setFinished] = useState(false);

  // Editable copy of all submissions (initialised once).
  const [submissions, setSubmissions] = useState<
    Record<string, BuyoutSubmission[]>
  >(() => {
    const boughtOut = getBoughtOut();
    const mine: BuyoutSubmission[] = boughtOut.map((p) => ({
      id: `mine-${p.id}`,
      playerName: p.name,
      position: p.position,
      salary: p.salary,
      yearsRemaining: p.yearsRemaining,
      cashCost: p.salary * p.yearsRemaining,
      capHit: Math.ceil(p.salary / 2),
    }));
    return {
      ...TEAM_BUYOUT_SUBMISSIONS,
      ...(mine.length > 0 ? { [MY_TEAM_ID]: mine } : {}),
    };
  });

  // Inline editing
  const [editing, setEditing] = useState<{
    teamId: string;
    subId: string;
  } | null>(null);
  const [editCash, setEditCash] = useState("");
  const [editCap, setEditCap] = useState("");

  // Finish confirmation modal
  const [showFinishModal, setShowFinishModal] = useState(false);

  const myTeamDone = completedStages.includes("buyouts") || finished;
  const myTeam = LEAGUE_TEAMS.find((t) => t.id === MY_TEAM_ID)!;
  const others = LEAGUE_TEAMS.filter((t) => t.id !== MY_TEAM_ID);

  // ---------- helpers ----------
  const baseStatus = (teamId: string): BuyoutStatus => {
    if (teamId === MY_TEAM_ID) return myTeamDone ? "done" : "in_progress";
    return TEAM_BUYOUT_STATUS[teamId] ?? "in_progress";
  };
  const isDone = (teamId: string): boolean =>
    finished || baseStatus(teamId) === "done";
  const displayStatus = (teamId: string): DisplayStatus => {
    if (finished && baseStatus(teamId) === "in_progress") return "no_buyouts";
    if (isDone(teamId)) return "done";
    return "in_progress";
  };
  const doneCount = LEAGUE_TEAMS.filter((t) => isDone(t.id)).length;
  const remaining = LEAGUE_TEAMS.length - doneCount;

  const poolTotal = Object.values(submissions)
    .flat()
    .reduce((s, b) => s + b.cashCost, 0);
  const poolTeams = Object.keys(submissions).length;

  const removeSubmission = (teamId: string, subId: string) => {
    setSubmissions((prev) => ({
      ...prev,
      [teamId]: (prev[teamId] ?? []).filter((s) => s.id !== subId),
    }));
  };

  const startEdit = (teamId: string, sub: BuyoutSubmission) => {
    setEditing({ teamId, subId: sub.id });
    setEditCash(String(sub.cashCost));
    setEditCap(String(sub.capHit));
  };

  const saveEdit = () => {
    if (!editing) return;
    const cash = Number(editCash);
    const cap = Number(editCap);
    if (isNaN(cash) || isNaN(cap)) return;
    setSubmissions((prev) => {
      const list = prev[editing.teamId] ?? [];
      return {
        ...prev,
        [editing.teamId]: list.map((s) =>
          s.id === editing.subId ? { ...s, cashCost: cash, capHit: cap } : s,
        ),
      };
    });
    setEditing(null);
  };

  const cancelEdit = () => setEditing(null);

      // ---------- finish stage ----------
  const handleFinishStage = () => {
    setShowFinishModal(false);
    setFinished(true);
    completeStage("buyouts");
    const idx = OFFSEASON_STEPS.findIndex((s) => s.id === "buyouts");
    const next = OFFSEASON_STEPS[idx + 1];
    if (next) setLiveStage(next.id);
  };

  // ===================== RENDER =====================
  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonNav
        title="Buyouts"
        subtitle={
          finished
            ? `${OFFSEASON_YEAR} · Review`
            : `${OFFSEASON_YEAR} · Team Status`
        }
      />

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 16 }}
        showsVerticalScrollIndicator={false}
      >
        {!finished ? (
          // ---------- TEAMS VIEW (in progress) ----------
          <>
            <View className="mx-4 mt-4 bg-ink-850 border border-ink-700 rounded-card p-4">
              <View className="flex-row items-center justify-between">
                <Text className="text-fg text-[14px] font-bold">
                  League Buyout Progress
                </Text>
                <Text className="text-fg text-[13px] font-extrabold">
                  {doneCount} / {LEAGUE_TEAMS.length}
                </Text>
              </View>
              <View className="h-1.5 rounded-full bg-ink-700 mt-2.5 overflow-hidden">
                <View
                  className="h-full rounded-full bg-win"
                  style={{
                    width: `${(doneCount / LEAGUE_TEAMS.length) * 100}%`,
                  }}
                />
              </View>
            </View>

            {/* Your team */}
            <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
              YOUR TEAM
            </Text>
            <TeamRow
              team={myTeam}
              displayStatus={displayStatus(MY_TEAM_ID)}
              isMine
              disabled={finished}
              onPress={() => router.push("/offseason/buyouts")}
            />

            {/* League */}
            <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
              ALL TEAMS
            </Text>
            {others.map((team) => (
              <TeamRow
                key={team.id}
                team={team}
                displayStatus={displayStatus(team.id)}
                onPress={() =>
                  router.push(`/offseason/team-detail/${team.id}`)
                }
              />
            ))}

            {/* Warnings */}
            {BUYOUT_WARNINGS.length > 0 && (
              <>
                <Text className="px-4 pt-5 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
                  BUYOUT POOL & WARNINGS
                </Text>
                <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card px-4 py-3">
                  <View className="flex-row items-center justify-between">
                    <Text className="text-fg text-[13px] font-bold">
                      Pool Total
                    </Text>
                    <Text className="text-loss text-[16px] font-extrabold">
                      ${poolTotal}
                    </Text>
                  </View>
                  <Text className="text-fg-muted text-[11px] mt-1">
                    From {poolTeams} team
                    {poolTeams > 1 ? "s" : ""} · distributed in end-of-season
                    payouts
                  </Text>
                </View>
                {BUYOUT_WARNINGS.map((w) => {
                  const team = LEAGUE_TEAMS.find((t) => t.id === w.teamId);
                  const border =
                    w.level === "high"
                      ? "border-loss/30 bg-loss/10"
                      : "border-warn/30 bg-warn/10";
                  const iconColor =
                    w.level === "high" ? "#EF4444" : "#F59E0B";
                  const Icon = w.level === "high" ? AlertTriangle : Info;
                  return (
                    <View
                      key={w.teamId}
                      className={`mx-4 mt-2 flex-row items-start gap-2.5 rounded-card border px-3.5 py-2.5 ${border}`}
                    >
                      <Icon color={iconColor} size={15} />
                      <View className="flex-1">
                        <Text className="text-fg text-[12px] font-bold">
                          {team?.name ?? w.teamId}
                        </Text>
                        <Text className="text-fg-muted text-[11px] mt-0.5 leading-5">
                          {w.message}
                        </Text>
                      </View>
                    </View>
                  );
                })}
              </>
            )}
          </>
        ) : (
          // ---------- SUBMISSIONS REVIEW (after finish) ----------
          <>
            <Text className="px-4 pt-4 pb-2 text-fg-faint text-[11px] font-bold tracking-widest">
              SUBMITTED BUYOUTS
            </Text>

            {Object.entries(submissions).map(([teamId, buyouts]) => {
              if (buyouts.length === 0) return null;
              const team = LEAGUE_TEAMS.find((t) => t.id === teamId);
              return (
                <View key={teamId} className="mx-4 mb-3">
                  {/* Team header */}
                  <View className="flex-row items-center gap-2 mb-1.5 px-1">
                    <Text className="text-lg">{team?.emoji ?? "🏳️"}</Text>
                    <Text className="text-fg text-[13px] font-bold">
                      {team?.name ?? teamId}
                    </Text>
                  </View>

                  {/* Buyout rows */}
                  <View className="bg-ink-850 border border-ink-700 rounded-card">
                    {buyouts.map((b, i) => {
                      const isEditing =
                        editing?.teamId === teamId && editing.subId === b.id;
                      return (
                        <View
                          key={b.id}
                          className={`px-3 py-2.5 ${
                            i < buyouts.length - 1
                              ? "border-b border-ink-700/60"
                              : ""
                          }`}
                        >
                          <View className="flex-row items-center">
                            <View className="flex-1">
                              <Text className="text-fg text-[13px] font-bold">
                                {b.playerName}
                              </Text>
                              <Text className="text-fg-muted text-[11px] mt-0.5">
                                {b.position} · ${b.salary} × {b.yearsRemaining}
                                yr
                              </Text>
                            </View>

                            {/* Editable cost / cap */}
                            {isEditing ? (
                              <View className="flex-row items-center gap-1.5">
                                <TextInput
                                  value={editCash}
                                  onChangeText={setEditCash}
                                  keyboardType="numeric"
                                  className="bg-ink-800 border border-ink-600 rounded-md px-2 py-1 text-fg text-[12px] font-bold w-14 text-center"
                                  placeholder="cash"
                                  placeholderTextColor="#5A7186"
                                />
                                <TextInput
                                  value={editCap}
                                  onChangeText={setEditCap}
                                  keyboardType="numeric"
                                  className="bg-ink-800 border border-ink-600 rounded-md px-2 py-1 text-fg text-[12px] font-bold w-14 text-center"
                                  placeholder="cap"
                                  placeholderTextColor="#5A7186"
                                />
                                <Pressable onPress={saveEdit} className="p-1">
                                  <Check
                                    color="#22C55E"
                                    size={16}
                                    strokeWidth={3}
                                  />
                                </Pressable>
                                <Pressable onPress={cancelEdit} className="p-1">
                                  <X color="#EF4444" size={16} />
                                </Pressable>
                              </View>
                            ) : (
                              <>
                                <View className="items-end mr-2">
                                  <Text className="text-loss text-[13px] font-extrabold">
                                    ${b.cashCost}
                                  </Text>
                                  <Text className="text-fg-faint text-[9px]">
                                    cap ${b.capHit}
                                  </Text>
                                </View>
                                <Pressable
                                  onPress={() => startEdit(teamId, b)}
                                  className="p-1"
                                >
                                  <Pencil color="#8CA3B8" size={14} />
                                </Pressable>
                                <Pressable
                                  onPress={() => removeSubmission(teamId, b.id)}
                                  className="p-1"
                                >
                                  <Trash2 color="#EF4444" size={14} />
                                </Pressable>
                              </>
                            )}
                          </View>
                        </View>
                      );
                    })}
                  </View>
                </View>
              );
            })}

            {Object.values(submissions).flat().length === 0 && (
              <View className="mx-4 bg-ink-850 border border-ink-700 rounded-card p-6 items-center">
                <XCircle color="#5A7186" size={28} />
                <Text className="text-fg-muted text-[13px] font-semibold mt-2">
                  No buyouts submitted
                </Text>
              </View>
            )}

            {/* Next stage CTA */}
            <View className="mx-4 mt-5 bg-ink-850 border border-accent/40 rounded-card p-4">
              <Text className="text-fg text-[14px] font-bold">
                Next Stage: Entry Draft
              </Text>
              <Text className="text-fg-muted text-[12px] mt-1 leading-5">
                The 2026 Entry Draft is live. Single round, reverse order of
                standings — 12 picks on the clock.
              </Text>
              <Pressable
                onPress={() =>
                  router.push("/rookie-draft")
                }
                className="mt-3.5 rounded-full py-3.5 items-center bg-accent flex-row justify-center gap-2"
              >
                <Text className="text-ink-900 text-[15px] font-bold">
                  Start Next Stage
                </Text>
                <ChevronRight color="#0A1420" size={16} />
              </Pressable>
            </View>
          </>
        )}
      </ScrollView>

      {/* Bottom action */}
      {!finished ? (
        <View className="px-4 pb-6 pt-3 bg-ink-900 border-t border-ink-700/60">
          <Pressable
            onPress={() => setShowFinishModal(true)}
            className="rounded-full py-3.5 flex-row items-center justify-center gap-2 bg-accent"
          >
            <Flag color="#0A1420" size={15} />
            <Text className="text-ink-900 text-[15px] font-bold">
              Finish Stage
            </Text>
          </Pressable>
          <Text className="text-fg-faint text-[10px] text-center mt-1.5">
            {remaining > 0
              ? `${remaining} team${remaining > 1 ? "s" : ""} remaining will be marked No Buyouts`
              : "All teams submitted — close the stage"}
          </Text>
        </View>
      ) : null}

      <BottomNav active="offseason" />

      {/* Finish confirmation modal */}
      <Modal
        visible={showFinishModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowFinishModal(false)}
      >
        <View className="flex-1 bg-black/60 items-center justify-center px-6">
          <View className="w-full bg-ink-850 border border-ink-700 rounded-card p-5">
            <View className="w-12 h-12 rounded-full bg-warn/15 border border-warn/40 items-center justify-center self-center">
              <Flag color="#F59E0B" size={22} />
            </View>
            <Text className="text-fg text-lg font-extrabold text-center mt-3">
              Finish Buyout Stage?
            </Text>
            <Text className="text-fg-muted text-[13px] leading-5 text-center mt-2">
              {remaining > 0
                ? `${remaining} team${remaining > 1 ? "s" : ""} still in progress will be marked No Buyouts. The stage closes and the buyout pool is locked in.`
                : "All teams have submitted. The stage closes and the buyout pool is locked in."}
            </Text>

            <View className="flex-row gap-2.5 mt-5">
              <Pressable
                onPress={() => setShowFinishModal(false)}
                className="flex-1 py-3.5 items-center rounded-full border border-ink-600 bg-ink-800"
              >
                <Text className="text-fg text-[15px] font-bold">Cancel</Text>
              </Pressable>
              <Pressable
                onPress={handleFinishStage}
                className="flex-1 py-3.5 items-center rounded-full bg-accent"
              >
                <Text className="text-ink-900 text-[15px] font-bold">
                  Confirm & Close
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function TeamRow({
  team,
  displayStatus,
  isMine = false,
  disabled = false,
  onPress,
}: {
  team: DraftTeam;
  displayStatus: DisplayStatus;
  isMine?: boolean;
  disabled?: boolean;
  onPress?: () => void;
}) {
  const done = displayStatus === "done";
  const noBuyouts = displayStatus === "no_buyouts";
  const snap = TEAM_ROSTER_SNAPSHOTS[team.id] ?? {
    C: 0,
    W: 0,
    F: 0,
    D: 0,
    G: 0,
    IR: 0,
    salary: 0,
  };
  const overCap = snap.salary > 100;

  const content = (
    <>
      <View className="w-10 h-10 rounded-full bg-ink-800 border border-ink-600 items-center justify-center">
        <Text className="text-lg">{team.emoji}</Text>
      </View>
      <View className="flex-1 ml-3">
        <View className="flex-row items-center gap-2">
          <Text className="text-fg text-[14px] font-bold">{team.name}</Text>
          {isMine && (
            <View className="bg-accent rounded-full px-2 py-0.5">
              <Text className="text-ink-900 text-[9px] font-bold">YOU</Text>
            </View>
          )}
        </View>
        <Text className="text-fg-muted text-[11px] mt-1">
          {snap.C}C · {snap.W}W · {snap.F}F · {snap.D}D · {snap.G}G · {snap.IR}IR
        </Text>
        <Text className="text-fg-faint text-[10px] mt-0.5">
          Total Salary{" "}
          <Text className={`font-bold ${overCap ? "text-loss" : "text-win"}`}>
            ${snap.salary}
          </Text>
        </Text>
      </View>
      <View
        className={`rounded-full px-2.5 py-1 ${
          done ? "bg-win/15" : noBuyouts ? "bg-ink-700" : "bg-warn/15"
        }`}
      >
        {done ? (
          <View className="flex-row items-center gap-1">
            <Check color="#22C55E" size={11} strokeWidth={3} />
            <Text className="text-win text-[10px] font-bold tracking-widest">
              DONE
            </Text>
          </View>
        ) : noBuyouts ? (
          <View className="flex-row items-center gap-1">
            <XCircle color="#8CA3B8" size={10} />
            <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
              NO BUYOUTS
            </Text>
          </View>
        ) : (
          <View className="flex-row items-center gap-1">
            <Loader color="#F59E0B" size={10} />
            <Text className="text-warn text-[10px] font-bold tracking-widest">
              IN PROGRESS
            </Text>
          </View>
        )}
      </View>
      {onPress && !disabled && (
        <View className="ml-1">
          <ChevronRight color="#5A7186" size={16} />
        </View>
      )}
    </>
  );

  return (
    <View
      className={`mx-4 mb-2 flex-row items-center rounded-card border p-3 ${
        isMine ? "border-accent/60 bg-accent/10" : "border-ink-700 bg-ink-850"
      }`}
    >
      {onPress && !disabled ? (
        <Pressable onPress={onPress} className="flex-1 flex-row items-center">
          {content}
        </Pressable>
      ) : (
        <View className="flex-1 flex-row items-center">{content}</View>
      )}
    </View>
  );
}