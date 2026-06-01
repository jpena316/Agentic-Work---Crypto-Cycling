import type { PerformanceAnalysis } from "../../api";

interface PerformancePanelProps {
  analysis: PerformanceAnalysis;
}

const RISK_COLORS: Record<string, string> = {
  low: "var(--color-positive)",
  moderate: "var(--color-accent)",
  high: "var(--color-negative)",
};

const TREND_COLORS: Record<string, string> = {
  improving: "var(--color-positive)",
  maintaining: "var(--color-accent)",
  declining: "var(--color-negative)",
};

function Badge({ label, value, colorMap }: { label: string; value: string; colorMap: Record<string, string> }) {
  const key = value.toLowerCase();
  const color = colorMap[key] ?? "var(--color-muted)";
  return (
    <div
      className="flex flex-col gap-1 rounded-lg p-3 border text-center"
      style={{
        background: "var(--color-background)",
        borderColor: "var(--color-border)",
      }}
    >
      <p className="text-xs" style={{ color: "var(--color-muted)" }}>
        {label}
      </p>
      <p className="text-sm font-semibold capitalize" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

function Tag({ text, variant }: { text: string; variant: "positive" | "negative" }) {
  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full"
      style={{
        background:
          variant === "positive"
            ? "rgba(34,197,94,0.12)"
            : "rgba(239,68,68,0.12)",
        color:
          variant === "positive"
            ? "var(--color-positive)"
            : "var(--color-negative)",
      }}
    >
      {text}
    </span>
  );
}

export function PerformancePanel({ analysis }: PerformancePanelProps) {
  return (
    <div
      className="rounded-lg border p-5 mb-6"
      style={{
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
      }}
    >
      <h2 className="text-base font-semibold mb-4 text-white">
        Performance Analysis
      </h2>

      {/* Status badges */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <Badge label="Fitness Trend" value={analysis.fitness_trend} colorMap={TREND_COLORS} />
        <Badge label="Fatigue Level" value={analysis.fatigue_level} colorMap={RISK_COLORS} />
        <Badge label="Overtraining Risk" value={analysis.overtraining_risk} colorMap={RISK_COLORS} />
      </div>

      {/* Strengths / Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--color-muted)" }}>
            Strengths
          </p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.strengths.map((s) => (
              <Tag key={s} text={s} variant="positive" />
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--color-muted)" }}>
            Areas to Improve
          </p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.weaknesses.map((w) => (
              <Tag key={w} text={w} variant="negative" />
            ))}
          </div>
        </div>
      </div>

      {/* Key observations */}
      {analysis.key_observations?.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--color-muted)" }}>
            Key Observations
          </p>
          <ul className="flex flex-col gap-1">
            {analysis.key_observations.map((obs, i) => (
              <li key={i} className="flex gap-2 text-sm" style={{ color: "#d1d5db" }}>
                <span style={{ color: "var(--color-accent)" }}>•</span>
                {obs}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended focus */}
      <div
        className="rounded-lg p-3 border"
        style={{
          background: "rgba(249,115,22,0.07)",
          borderColor: "rgba(249,115,22,0.25)",
        }}
      >
        <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: "var(--color-accent)" }}>
          Recommended Focus
        </p>
        <p className="text-sm" style={{ color: "#e5e7eb" }}>
          {analysis.recommended_focus}
        </p>
      </div>
    </div>
  );
}
