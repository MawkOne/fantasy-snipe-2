import { Tabs } from "expo-router";
import { ArrowLeftRight, Menu, Search, Shirt } from "lucide-react-native";

import { OFFSEASON_STEPS } from "../../src/data/offseason";
import { STAGE_ICONS } from "../../src/components/offseason/stageIcons";
import { useOffseason } from "../../src/components/offseason/OffseasonProvider";

const ACTIVE = "#2AB3FF";
const INACTIVE = "#5A7186";

// Index is the Offseason page — app opens there even though Lineup is
// declared first in the tab bar order.
export const unstable_settings = { initialRouteName: "index" };

export default function TabsLayout() {
  const { liveStage } = useOffseason();
  const liveStep = OFFSEASON_STEPS.find((s) => s.id === liveStage)!;
  const LiveIcon = STAGE_ICONS[liveStage];

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#0D1B2A",
          borderTopColor: "#1B3042",
          borderTopWidth: 1,
          height: 84,
          paddingTop: 6,
        },
        tabBarActiveTintColor: ACTIVE,
        tabBarInactiveTintColor: INACTIVE,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "600",
        },
        sceneStyle: { backgroundColor: "#0A1420" },
      }}
    >
      <Tabs.Screen
        name="lineup"
        options={{
          title: "Lineup",
          tabBarIcon: ({ color, size }) => <Shirt color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="players"
        options={{
          title: "Players",
          tabBarIcon: ({ color, size }) => <Search color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="index"
        options={{
          title: liveStep.label,
          tabBarIcon: ({ color, size }) => (
            <LiveIcon color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="trades"
        options={{
          title: "Trades",
          tabBarIcon: ({ color, size }) => (
            <ArrowLeftRight color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="more"
        options={{
          title: "More",
          tabBarIcon: ({ color, size }) => <Menu color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}