import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro Text",
          "Inter",
          "Helvetica Neue",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      letterSpacing: {
        tightest: "-0.04em",
        tighter: "-0.02em",
        tight: "-0.01em",
      },
      borderRadius: {
        mac: "14px",
        macLg: "18px",
      },
      boxShadow: {
        mac: "0 6px 24px rgba(0,0,0,0.28)",
        macLight: "0 4px 14px rgba(15,23,42,0.06)",
        macInset: "0 1px 0 rgba(255,255,255,0.08) inset",
      },
      colors: {
        traffic: {
          red: "#ff5f57",
          yellow: "#febc2e",
          green: "#28c840",
        },
      },
      keyframes: {
        macFadeUp: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        macFadeUp: "macFadeUp 380ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
      },
    },
  },
  plugins: [],
};

export default config;
