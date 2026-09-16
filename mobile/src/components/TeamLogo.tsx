import { Image } from "expo-image";
import { View } from "react-native";

interface Props {
  abbrev: string;
  size?: number;
}

// NHL official CDN logos (light variant works on dark backgrounds).
export function TeamLogo({ abbrev, size = 22 }: Props) {
  const uri = `https://assets.nhle.com/logos/nhl/svg/${abbrev}_light.svg`;
  return (
    <View style={{ width: size, height: size }}>
      <Image
        source={{ uri }}
        style={{ width: size, height: size }}
        contentFit="contain"
        transition={150}
      />
    </View>
  );
}
