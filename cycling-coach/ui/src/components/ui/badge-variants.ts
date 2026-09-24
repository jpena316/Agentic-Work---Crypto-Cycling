import { cva } from "class-variance-authority";

export const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium font-sans transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-accent/15 text-accent",
        secondary: "border-transparent bg-surface text-muted",
        outline: "border-border text-text",
        positive: "border-transparent bg-positive/15 text-positive",
        warning: "border-transparent bg-warning/15 text-warning",
        destructive: "border-transparent bg-negative/15 text-negative",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);
