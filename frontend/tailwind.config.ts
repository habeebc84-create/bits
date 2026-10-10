import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080D18",
        surf1: "#0F1623",
        surf2: "#151E2E",
        line: "#1E2A3B",
        accent: "#3EC9D6",
        pri: "#F1F5F9",
        sec: "#8B9CB3",
        ter: "#5C6B7F",
        pos: "#34D399",
        warn: "#FBBF24",
        neg: "#F87171",
      },
      fontFamily: { sans: ["Inter", "Geist Sans", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
} satisfies Config;
