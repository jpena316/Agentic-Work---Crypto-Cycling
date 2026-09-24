import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { Card } from "./Card";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "flat";
  trendLabel?: string;
  accent?: boolean;
}

const TREND_ICON = { up: TrendingUp, down: TrendingDown, flat: Minus };

export function StatTile({ label, value, sub, trend, trendLabel, accent }: StatTileProps) {
  const TrendIcon = trend ? TREND_ICON[trend] : null;
  const trendColor =
    trend === "up" ? "text-positive" : trend === "down" ? "text-negative" : "text-muted";

  return (
    <Card className="flex flex-col gap-2">
      <p className="text-xs font-medium uppercase tracking-wider text-muted">{label}</p>
      <p
        className={cn(
          "font-heading text-2xl font-bold leading-none",
          accent ? "text-accent" : "text-text"
        )}
      >
        {value}
      </p>
      {(sub || trend) && (
        <div className="flex items-center gap-1.5 text-xs">
          {TrendIcon && <TrendIcon className={cn("h-3.5 w-3.5", trendColor)} />}
          {trendLabel && <span className={trendColor}>{trendLabel}</span>}
          {sub && <span className="text-muted">{sub}</span>}
        </div>
      )}
    </Card>
  );
}
