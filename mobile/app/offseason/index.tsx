import { SafeAreaView } from "react-native-safe-area-context";

import { OffseasonHub } from "../../src/components/offseason/OffseasonHub";
import { BottomNav } from "../../src/components/BottomNav";

export default function OffseasonStandaloneScreen() {
  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonHub />
      <BottomNav active="offseason" />
    </SafeAreaView>
  );
}