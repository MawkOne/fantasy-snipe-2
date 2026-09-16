import { useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import {
  BarChart3,
  ChevronDown,
  ChevronRight,
  GraduationCap,
  Layers,
  Plus,
  Ticket,
  User,
} from "lucide-react-native";

import {
  CAP_HITS_BY_SEASON,
  FRANCHISE_CAP,
  FUTURE_PICKS,
  FUTURE_PICKS_TOTAL,
  MY_LEAGUE,
} from "../src/data/mock";
import {
  FRANCHISE_ASSETS,
  FRANCHISE_CONTRACTS,
  FRANCHISE_PROSPECTS,
  FRANCHISE_SKATERS,
  type ContractStatus,
} from "../src/data/franchise";
import { PlayerHeadshot } from "../src/components/PlayerHeadshot";
import { BottomNav } from "../src/components/BottomNav";

type RosterTab = "active" | "prospects" | "contracts" | "assets";

const TABS: { id: RosterTab; label: string }[] = [
  { id: "active", label: `Active (${FRANCHISE_SKATERS.length + 12})` },
  { id: "prospects", label: `Prospects (${FRANCHISE_PROSPECTS.length})` },
  { id: "contracts", label: `Contracts (${FRANCHISE_CONTRACTS.length})` },
  { id: "assets", label: `Assets (${FRANCHISE_ASSETS.length})` },
];

export default function FranchiseScreen() {
  const router = useRouter();
  const [tab, setTab] = useState<RosterTab>("active");

  const capPct = (FRANCHISE_CAP.used / FRANCHISE_CAP.total) * 100;
  const capSpace = (FRANCHISE_CAP.total - FRANCHISE_CAP.used).toFixed(1);

  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      {/* Header */}
      <View className="flex-row items-center justify-between px-4 pt-2 pb-3">
        <View>
          <Text className="text-fg text-[26px] font-black tracking-tight">
            Franchise
          </Text>
          <Text className="text-fg-muted text-[13px] mt-0.5">
            Build Today. Dominate Tomorrow.
          </Text>
        </View>
        <Pressable className="flex-row items-center gap-2 border border-ink-600 rounded-full px-3 py-1.5 bg-ink-850 mt-1">
          <View className="w-7 h-7 rounded-full bg-ink-700 border border-ink-600 items-center justify-center">
            <Text className="text-sm">🐻‍❄️</Text>
          </View>
          <Text className="text-fg text-[13px] font-semibold">
            {MY_LEAGUE.myTeam.name}
          </Text>
          <ChevronDown color="#8CA3B8" size={14} />
        </Pressable>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Top stat cards */}
        <View className="flex-row px-4 gap-2 mt-1">
          {/* Salary cap */}
          <View className="flex-[1.5] bg-ink-850 border border-ink-700 rounded-card p-3">
            <Text className="text-fg text-[13px] font-bold">Salary Cap</Text>
            <View className="h-1.5 rounded-full bg-ink-700 mt-2.5 overflow-hidden">
              <View
                className="h-full rounded-full bg-accent"
                style={{ width: `${capPct}%` }}
              />
            </View>
            <View className="flex-row items-baseline mt-2">
              <Text className="text-fg text-[16px] font-extrabold">
                ${FRANCHISE_CAP.used.toFixed(1)}M
              </Text>
              <Text className="text-fg-faint text-[11px] font-semibold">
                {" "}
                / ${FRANCHISE_CAP.total.toFixed(1)}M
              </Text>
            </View>
            <Text className="text-fg-muted text-[10px] mt-0.5">
              ${capSpace}M Cap Space
            </Text>
          </View>

          <StatCard
            icon={<User color="#2AB3FF" size={15} />}
            label="Open Roster Spots"
            value={String(FRANCHISE_CAP.openRosterSpots)}
            sub={`of ${FRANCHISE_CAP.rosterSize}`}
          />
          <StatCard
            icon={<Layers color="#2AB3FF" size={15} />}
            label="Expiring Contracts"
            value={String(FRANCHISE_CAP.expiringContracts)}
            sub={`in ${FRANCHISE_CAP.expiringYear}`}
          />
          <StatCard
            icon={<GraduationCap color="#2AB3FF" size={15} />}
            label="Rookie Slots"
            value={String(FRANCHISE_CAP.rookieSlotsUsed)}
            sub={`of ${FRANCHISE_CAP.rookieSlotsTotal}`}
          />
        </View>

        {/* Roster tabs */}
        <View className="flex-row px-4 gap-2 mt-3">
          {TABS.map((t) => {
            const active = tab === t.id;
            return (
              <Pressable
                key={t.id}
                onPress={() => setTab(t.id)}
                className={`flex-1 items-center py-2 rounded-lg border ${
                  active
                    ? "border-accent bg-accent/15"
                    : "border-ink-700 bg-ink-850"
                }`}
              >
                <Text
                  className={`text-[11px] font-bold ${
                    active ? "text-accent" : "text-fg-muted"
                  }`}
                >
                  {t.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {tab === "active" && <ActiveTab onShowAll={() => setTab("contracts")} onOpenPlayer={(id) => router.push(`/player/${id}`)} />}
        {tab === "prospects" && <ProspectsTab />}
        {tab === "contracts" && <ContractsTab />}
        {tab === "assets" && <AssetsTab />}

        {/* Future picks + Cap hits */}
        <View className="flex-row px-4 gap-2 mt-4">
          {/* Future picks */}
          <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5">
            <View className="flex-row items-center gap-1.5 mb-2">
              <Layers color="#2AB3FF" size={14} />
              <Text className="text-fg text-[13px] font-bold">Future Picks</Text>
            </View>
            {FUTURE_PICKS.map((p) => (
              <View
                key={p.year}
                className="flex-row items-center justify-between py-1.5 border-b border-ink-700/50"
              >
                <Text className="text-fg-muted text-[12px]">{p.year}</Text>
                <View className="flex-row items-center gap-1">
                  <Text className="text-fg text-[12px] font-semibold">
                    {p.count} {p.count === 1 ? "pick" : "picks"}
                  </Text>
                  <ChevronRight color="#5A7186" size={13} />
                </View>
              </View>
            ))}
            <Pressable
              onPress={() => setTab("assets")}
              className="flex-row items-center justify-between pt-2"
            >
              <Text className="text-accent text-[11px] font-semibold">
                View All Picks ({FUTURE_PICKS_TOTAL})
              </Text>
              <ChevronRight color="#2AB3FF" size={13} />
            </Pressable>
          </View>

          {/* Cap hits by season */}
          <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3.5">
            <View className="flex-row items-center gap-1.5 mb-2">
              <BarChart3 color="#2AB3FF" size={14} />
              <Text className="text-fg text-[13px] font-bold">
                Cap Hits by Season
              </Text>
            </View>
            {CAP_HITS_BY_SEASON.map((c) => (
              <View
                key={c.season}
                className="flex-row items-center justify-between py-1.5 border-b border-ink-700/50"
              >
                <Text className="text-fg-muted text-[12px]">{c.season}</Text>
                <Text className="text-fg text-[12px] font-semibold">
                  ${c.amount.toFixed(1)}M
                </Text>
              </View>
            ))}
            <Pressable onPress={() => setTab("contracts")} className="pt-2">
              <Text className="text-accent text-[11px] font-semibold">
                View Cap Details
              </Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>

      <BottomNav active="more" />
    </SafeAreaView>
  );
}

/* ---------------- Active tab ---------------- */

function ActiveTab({
  onShowAll,
  onOpenPlayer,
}: {
  onShowAll: () => void;
  onOpenPlayer: (id: string) => void;
}) {
  const router = useRouter();
  return (
    <View>
      {/* Skaters table */}
      <View className="flex-row items-center px-4 pt-3 pb-1.5">
        <Text className="flex-1 text-fg-faint text-[10px] font-bold tracking-widest">
          SKATERS ({FRANCHISE_SKATERS.length})
        </Text>
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest w-[38px] text-center">
          POS
        </Text>
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest w-[62px] text-right">
          SALARY
        </Text>
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest w-[38px] text-center">
          YEARS
        </Text>
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest w-[52px] text-right">
          STATUS
        </Text>
      </View>

      {FRANCHISE_SKATERS.map((p) => (
        <Pressable
          key={p.id}
          onPress={() => onOpenPlayer(p.id)}
          className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-2.5 py-2"
        >
          <View className="w-8 h-8 rounded-lg border border-accent/60 items-center justify-center">
            <Text className="text-accent text-[11px] font-bold">
              {p.position}
            </Text>
          </View>
          <PlayerHeadshot url={p.headshotUrl} size={36} />
          <View className="flex-1 ml-2.5">
            <Text className="text-fg text-[13px] font-bold" numberOfLines={1}>
              {p.name}
            </Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">{p.team}</Text>
          </View>
          <Text className="text-fg-muted text-[12px] w-[38px] text-center">
            {p.position}
          </Text>
          <Text className="text-fg text-[12px] font-semibold w-[62px] text-right">
            {p.salary}
          </Text>
          <Text className="text-fg-muted text-[12px] w-[38px] text-center">
            {p.years}
          </Text>
          <View className="w-[52px] items-end">
            <StatusBadge status={p.status} />
          </View>
        </Pressable>
      ))}

      <Pressable
        onPress={onShowAll}
        className="flex-row items-center px-4 py-2.5"
      >
        <Text className="text-accent text-[13px] font-semibold">
          View All Skaters ({FRANCHISE_CONTRACTS.length})
        </Text>
        <ChevronRight color="#2AB3FF" size={15} />
      </Pressable>

      {/* Reserves */}
      <View className="flex-row items-center px-4 pt-3 pb-2">
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
          RESERVES (0/4)
        </Text>
      </View>
      <View className="flex-row px-4 gap-2">
        {[0, 1, 2, 3].map((i) => (
          <Pressable
            key={i}
            onPress={() => router.push("/(tabs)/players")}
            className="flex-1 flex-row items-center justify-center gap-1.5 border border-dashed border-ink-600 rounded-card py-3 bg-ink-850"
          >
            <Plus color="#5A7186" size={14} />
            <Text className="text-fg-faint text-[10px] font-semibold">
              Add Reserve
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

/* ---------------- Prospects tab ---------------- */

function ProspectsTab() {
  return (
    <View>
      <Text className="px-4 pt-3 pb-1.5 text-fg-faint text-[10px] font-bold tracking-widest">
        PROSPECT ROSTER ({FRANCHISE_PROSPECTS.length})
      </Text>
      {FRANCHISE_PROSPECTS.map(({ rookie, status, year }) => (
        <View
          key={rookie.id}
          className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-2.5 py-2"
        >
          <View className="w-8 h-8 rounded-lg border border-accent/60 items-center justify-center">
            <Text className="text-accent text-[11px] font-bold">
              {rookie.position}
            </Text>
          </View>
          <PlayerHeadshot url={rookie.headshotUrl} size={36} />
          <View className="flex-1 ml-2.5">
            <Text className="text-fg text-[13px] font-bold" numberOfLines={1}>
              {rookie.name}
            </Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              {rookie.position} · {rookie.nhlTeam} · Age {rookie.age}
            </Text>
          </View>
          <View className="items-end">
            <Text className="text-fg-muted text-[10px]">
              Rookie yr {year}/3
            </Text>
            <View
              className={`rounded-full px-2 py-0.5 mt-1 ${
                status === "Signed" ? "bg-win/15" : "bg-warn/15"
              }`}
            >
              <Text
                className={`text-[9px] font-bold ${
                  status === "Signed" ? "text-win" : "text-warn"
                }`}
              >
                {status.toUpperCase()}
              </Text>
            </View>
          </View>
        </View>
      ))}
      <Text className="px-4 pt-1 text-fg-faint text-[10px] leading-4">
        Rookies do not score fantasy points. Unsigned rookies become UFAs
        after 3 years.
      </Text>
    </View>
  );
}

/* ---------------- Contracts tab ---------------- */

function ContractsTab() {
  const expiring = FRANCHISE_CONTRACTS.filter((c) => c.years <= 1).length;

  return (
    <View>
      <View className="flex-row items-center justify-between px-4 pt-3 pb-1.5">
        <Text className="text-fg-faint text-[10px] font-bold tracking-widest">
          ALL CONTRACTS ({FRANCHISE_CONTRACTS.length})
        </Text>
        <Text className="text-warn text-[10px] font-bold">
          {expiring} EXPIRING
        </Text>
      </View>
      {FRANCHISE_CONTRACTS.map((p) => (
        <View
          key={p.id}
          className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-2.5 py-2"
        >
          <PlayerHeadshot url={p.headshotUrl} size={36} />
          <View className="flex-1 ml-2.5">
            <Text className="text-fg text-[13px] font-bold" numberOfLines={1}>
              {p.name}
            </Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              {p.position} · {p.team}
            </Text>
          </View>
          <Text className="text-fg text-[12px] font-semibold w-[62px] text-right">
            {p.salary}
          </Text>
          <Text
            className={`text-[12px] w-[38px] text-center ${
              p.years <= 1 ? "text-warn font-bold" : "text-fg-muted"
            }`}
          >
            {p.years} yr
          </Text>
          <View className="w-[52px] items-end">
            <StatusBadge status={p.status} />
          </View>
        </View>
      ))}
    </View>
  );
}

/* ---------------- Assets tab ---------------- */

function AssetsTab() {
  return (
    <View>
      <Text className="px-4 pt-3 pb-1.5 text-fg-faint text-[10px] font-bold tracking-widest">
        DRAFT PICKS ({FRANCHISE_ASSETS.length})
      </Text>
      {FRANCHISE_ASSETS.map((pick) => (
        <View
          key={pick.id}
          className="mx-4 mb-1.5 flex-row items-center bg-ink-850 border border-ink-700 rounded-card px-3 py-3"
        >
          <View className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/40 items-center justify-center">
            <Ticket color="#2AB3FF" size={16} />
          </View>
          <View className="flex-1 ml-3">
            <Text className="text-fg text-[13px] font-bold">{pick.label}</Text>
            <Text className="text-fg-faint text-[10px] mt-0.5">
              {pick.origin}
            </Text>
          </View>
        </View>
      ))}
    </View>
  );
}

/* ---------------- Shared bits ---------------- */

function StatCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <View className="flex-1 bg-ink-850 border border-ink-700 rounded-card p-3">
      <View className="flex-row items-center gap-1.5">
        {icon}
        <Text className="text-fg-muted text-[10px] font-semibold flex-1 leading-3">
          {label}
        </Text>
      </View>
      <Text className="text-fg text-[22px] font-extrabold mt-1.5">{value}</Text>
      <Text className="text-fg-faint text-[10px] mt-0.5">{sub}</Text>
    </View>
  );
}

function StatusBadge({ status }: { status: ContractStatus }) {
  const styles: Record<ContractStatus, { bg: string; fg: string }> = {
    UFA: { bg: "bg-loss/15 border-loss/50", fg: "text-loss" },
    RFA: { bg: "bg-warn/15 border-warn/50", fg: "text-warn" },
    ELC: { bg: "bg-win/15 border-win/50", fg: "text-win" },
  };
  const s = styles[status];
  return (
    <View className={`rounded-full px-2.5 py-1 border ${s.bg}`}>
      <Text className={`text-[10px] font-bold ${s.fg}`}>{status}</Text>
    </View>
  );
}
