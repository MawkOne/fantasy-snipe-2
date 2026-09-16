import { Image } from "expo-image";
import { View } from "react-native";

interface Props {
  url?: string;
  size?: number;
}

export function PlayerHeadshot({ url, size = 40 }: Props) {
  return (
    <View
      style={{ width: size, height: size }}
      className="rounded-full overflow-hidden bg-ink-700"
    >
      {url ? (
        <Image
          source={{ uri: url }}
          style={{ width: size, height: size }}
          contentFit="cover"
          transition={150}
        />
      ) : null}
    </View>
  );
}
