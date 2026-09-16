import "react-native-gesture-handler";
import "../global.css";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import { Platform } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { OffseasonProvider } from "../src/components/offseason/OffseasonProvider";

export default function RootLayout() {
  // App is dark-only; force the dark class so web NativeWind stays dark.
  useEffect(() => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      document.documentElement.classList.add("dark");
    }
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: "#0A1420" }}>
      <OffseasonProvider>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "#0A1420" },
          }}
        >
        <Stack.Screen
          name="add-drop"
          options={{ presentation: "card", gestureEnabled: true }}
        />
        <Stack.Screen
          name="player/[id]"
          options={{ presentation: "card", gestureEnabled: true }}
        />
        <Stack.Screen
          name="trade/finalize"
          options={{ presentation: "card", gestureEnabled: true }}
        />
        </Stack>
      </OffseasonProvider>
    </GestureHandlerRootView>
  );
}
