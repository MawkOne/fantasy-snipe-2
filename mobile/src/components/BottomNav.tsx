import { Pressable, Text, View } from "react-native";
import { useRouter } from "expo-router";
import {
  ArrowLeftRight,
  Menu,
  Search,
  Shirt,
} from "lucide-react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { OFFSEASON_STEPS } from "../data/offseason";
import { STAGE_ICONS } from "./offseason/stageIcons";
import { useOffseason } from "./offseason/OffseasonProvider";

const ACTIVE = "#2AB3FF";
const INACTIVE = "#5A7186";

export type BottomNavTab =
  | "offseason"
  | "lineup"
  | "players"
  | "trades"
  | "more";

const STATIC_TABS: {
  id: Exclude<BottomNavTab, "offseason">;
  label: string;
  route: string;
  Icon: typeof Shirt;
}[] = [
  { id: "lineup", label: "Lineup", route: "/(tabs)/lineup", Icon: Shirt },
  { id: "players", label: "Players", route: "/(tabs)/players", Icon: Search },
  { id: "trades", label: "Trades", route: "/(tabs)/trades", Icon: ArrowLeftRight },
  { id: "more", label: "More", route: "/(tabs)/more", Icon: Menu },
];

interface Props {
  /** Which tab to highlight. Defaults to "more" since pushed screens live under More. */
  active?: BottomNavTab;
}

/**
 * Static bottom navigation for pushed (non-tab) screens.
 * The middle (offseason) item dynamically reflects the current live stage.
 */
export function BottomNav({ active = "more" }: Props) {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { liveStage } = useOffseason();
  const liveStep = OFFSEASON_STEPS.find((s) => s.id === liveStage)!;
  const LiveIcon = STAGE_ICONS[liveStage];

  return (
    <View
      className="flex-row border-t border-ink-700 bg-ink-850"
      style={{ paddingBottom: Math.max(insets.bottom, 8), paddingTop: 6 }}
    >
      {STATIC_TABS.map(({ id, label, route, Icon }) => {
        const isActive = id === active;
        const color = isActive ? ACTIVE : INACTIVE;
        return (
          <Pressable
            key={id}
            accessibilityLabel={label}
            onPress={() => {
              router.dismissAll();
              router.replace(route as never);
            }}
            className="flex-1 items-center"
          >
            <Icon color={color} size={22} />
            <Text
              className="text-[11px] font-semibold mt-0.5"
              style={{ color }}
            >
              {label}
            </Text>
          </Pressable>
        );
      })}

      {/* Middle — dynamic offseason stage */}
      <Pressable
        accessibilityLabel={liveStep.label}
        onPress={() => {
          router.dismissAll();
          router.replace("/(tabs)" as never);
        }}
        className="flex-1 items-center"
      >
        <LiveIcon
          color={active === "offseason" ? ACTIVE : INACTIVE}
          size={22}
        />
        <Text
          className="text-[11px] font-semibold mt-0.5"
          style={{ color: active === "offseason" ? ACTIVE : INACTIVE }}
        >
          {liveStep.label}
        </Text>
      </Pressable>
    </View>
  );
}