/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#060D16",
          900: "#0A1420",
          850: "#0D1B2A",
          800: "#11222F",
          700: "#1B3042",
          600: "#27435C",
        },
        accent: {
          DEFAULT: "#2AB3FF",
          bright: "#4DC6FF",
          dim: "#1A7FBF",
          glow: "rgba(42,179,255,0.35)",
        },
        win: "#22C55E",
        loss: "#EF4444",
        warn: "#F59E0B",
        sit: "#64748B",
        fg: {
          DEFAULT: "#F2F7FC",
          muted: "#8CA3B8",
          faint: "#5A7186",
        },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
      },
    },
  },
  plugins: [],
};