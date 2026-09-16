import { Text, View } from "react-native";

interface Props {
  label: string;
  active?: boolean;
}

export function PositionBadge({ label, active = false }: Props) {
  return (
    <View
      className={`w-8 h-8 rounded-lg items-center justify-center border ${
        active ? "border-accent bg-accent/10" : "border-accent/60 bg-transparent"
      }`}
    >
      <Text className="text-accent text-xs font-bold tracking-wide">
        {label}
      </Text>
    </View>
  );
}
