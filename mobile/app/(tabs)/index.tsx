import { SafeAreaView } from "react-native-safe-area-context";
import { OffseasonHub } from "../../src/components/offseason/OffseasonHub";

// Offseason is now the starting screen of the app.
export default function OffseasonStartScreen() {
  return (
    <SafeAreaView className="flex-1 bg-ink-900" edges={["top"]}>
      <OffseasonHub />
    </SafeAreaView>
  );
}