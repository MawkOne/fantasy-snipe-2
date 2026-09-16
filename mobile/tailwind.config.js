/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // FantasySnipe dark theme (from design mocks)
        ink: {
          950: "#060D16", // deepest background
          900: "#0A1420", // screen background
          850: "#0D1B2A", // card background
          800: "#11222F", // elevated card / row
          700: "#1B3042", // borders, dividers
          600: "#27435C", // muted borders
        },
        accent: {
          DEFAULT: "#2AB3FF", // primary cyan
          bright: "#4DC6FF",
          dim: "#1A7FBF",
          glow: "rgba(42,179,255,0.35)",
        },
        win: "#22C55E", // green - winning, start
        loss: "#EF4444", // red - losing, live game
        warn: "#F59E0B", // amber - warnings
        sit: "#64748B", // slate - sit state
        fg: {
          DEFAULT: "#F2F7FC", // primary text
          muted: "#8CA3B8", // secondary text
          faint: "#5A7186", // tertiary text
        },
      },
      fontFamily: {
        sans: ["System"],
      },
      borderRadius: {
        card: "14px",
      },
    },
  },
  plugins: [],
};
