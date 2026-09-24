import type { PerformanceAnalysis } from "@/api";
import { Card } from "./Card";
import { Badge } from "@/components/ui/badge";

interface PerformanceInsightsProps {
  analysis: PerformanceAnalysis;
}

const TREND_VARIANT: Record<string, "positive" | "default" | "destructive"> = {
  improving: "positive",
  maintaining: "default",
  declining: "destructive",
};

export function PerformanceInsights({ analysis }: PerformanceInsightsProps) {
  const trendVariant = TREND_VARIANT[analysis.fitness_trend?.toLowerCase()] ?? "default";

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-base font-semibold text-text">Performance Insights</h2>
        <Badge variant={trendVariant} className="capitalize">
          {analysis.fitness_trend}
        </Badge>
      </div>

      {analysis.key_observations?.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">
            Key Observations
          </p>
          <ul className="flex flex-col gap-1">
            {analysis.key_observations.map((obs, i) => (
              <li key={i} className="flex gap-2 text-sm text-text">
                <span className="text-accent">•</span>
                {obs}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-md p-3 bg-accent/10 border border-accent/25">
        <p className="text-xs font-semibold uppercase tracking-wider text-accent mb-1">
          Recommended Focus
        </p>
        <p className="text-sm text-text">{analysis.recommended_focus}</p>
      </div>
    </Card>
  );
}
