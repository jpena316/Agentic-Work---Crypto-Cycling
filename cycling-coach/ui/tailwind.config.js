/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        border: "var(--color-border)",
        accent: "var(--color-accent)",
        positive: "var(--color-positive)",
        negative: "var(--color-negative)",
        muted: "var(--color-muted)",
      },
    },
  },
  plugins: [],
};

