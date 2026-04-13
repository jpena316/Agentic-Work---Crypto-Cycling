/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f1117",
        surface: "#1a1d27",
        border: "#2a2d3a",
        accent: "#6366f1",
        positive: "#22c55e",
        negative: "#ef4444",
        neutral: "#f59e0b",
        muted: "#6b7280",
      },
    },
  },
  plugins: [],
}