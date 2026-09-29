import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },
        brand: {
          50: "#f0fdf4",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
        risk: {
          severe: "#ef4444",
          warning: "#f59e0b",
          caution: "#3b82f6",
          safe: "#10b981",
        }
      },
      fontFamily: {
        sans: ["Pretendard", "-apple-system", "BlinkMacSystemFont", "system-ui", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
