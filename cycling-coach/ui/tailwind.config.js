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
        "accent-light": "var(--color-accent-light)",
        positive: "var(--color-positive)",
        warning: "var(--color-warning)",
        negative: "var(--color-negative)",
        muted: "var(--color-muted)",
        text: "var(--color-text)",
        // shadcn-expected aliases, pointed at the same tokens above
        card: "var(--color-surface)",
        "card-foreground": "var(--color-text)",
        primary: "var(--color-accent)",
        "primary-foreground": "var(--color-background)",
        destructive: "var(--color-negative)",
        "muted-foreground": "var(--color-muted)",
        input: "var(--color-border)",
        ring: "var(--color-accent)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 4px)",
        sm: "calc(var(--radius) - 8px)",
      },
      fontFamily: {
        sans: ["Manrope", "system-ui", "sans-serif"],
        heading: ["Space Grotesk", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
