import { Text, View } from "react-native";

interface Props {
  emoji: string;
  size?: number;
}

/** Circular fantasy-team logo (emoji placeholder until real logos exist). */
export function TeamEmblem({ emoji, size = 36 }: Props) {
  return (
    <View
      style={{ width: size, height: size, borderRadius: size / 2 }}
      className="bg-ink-800 border border-ink-600 items-center justify-center"
    >
      <Text style={{ fontSize: size * 0.5 }}>{emoji}</Text>
    </View>
  );
}
