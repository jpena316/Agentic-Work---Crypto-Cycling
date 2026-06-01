import type { TrainingPlan as TrainingPlanType, TrainingDay } from "../../api";

interface TrainingPlanProps {
  plan: TrainingPlanType | null;
}

const INTENSITY_STYLE: Record<string, { bg: string; color: string }> = {
  rest:      { bg: "rgba(107,114,128,0.15)", color: "var(--color-muted)" },
  easy:      { bg: "rgba(34,197,94,0.12)",   color: "var(--color-positive)" },
  recovery:  { bg: "rgba(34,197,94,0.12)",   color: "var(--color-positive)" },
  moderate:  { bg: "rgba(249,115,22,0.12)",  color: "var(--color-accent)" },
  tempo:     { bg: "rgba(249,115,22,0.12)",  color: "var(--color-accent)" },
  threshold: { bg: "rgba(239,68,68,0.12)",   color: "var(--color-negative)" },
  hard:      { bg: "rgba(239,68,68,0.12)",   color: "var(--color-negative)" },
  "vo2max":  { bg: "rgba(239,68,68,0.12)",   color: "var(--color-negative)" },
};

function intensityStyle(intensity: string) {
  const key = intensity.toLowerCase();
  return INTENSITY_STYLE[key] ?? { bg: "rgba(107,114,128,0.15)", color: "var(--color-muted)" };
}

function DayCard({ day }: { day: TrainingDay }) {
  const style = intensityStyle(day.intensity);
  return (
    <div
      className="rounded-lg border p-4 flex flex-col gap-2"
      style={{
        background: "var(--color-background)",
        borderColor: "var(--color-border)",
      }}
    >
      <div className="flex items-center justify-between">
        <p className="font-semibold text-sm text-white">{day.day}</p>
        <span
          className="text-xs px-2 py-0.5 rounded-full font-medium capitalize"
          style={{ background: style.bg, color: style.color }}
        >
          {day.intensity}
        </span>
      </div>

      <p className="text-sm font-medium" style={{ color: "var(--color-accent)" }}>
        {day.workout_type}
      </p>

      <p className="text-xs" style={{ color: "#d1d5db" }}>
        {day.description}
      </p>

      <div className="flex items-center justify-between mt-1">
        <p className="text-xs" style={{ color: "var(--color-muted)" }}>
          {day.duration_mins > 0 ? `${day.duration_mins} min` : "Off"}
        </p>
        <p className="text-xs italic" style={{ color: "var(--color-muted)" }}>
          {day.rationale}
        </p>
      </div>
    </div>
  );
}

export function TrainingPlan({ plan }: TrainingPlanProps) {
  if (!plan) {
    return (
      <div
        className="rounded-lg border p-8 text-center"
        style={{
          background: "var(--color-surface)",
          borderColor: "var(--color-border)",
        }}
      >
        <p className="text-4xl mb-3">📅</p>
        <p className="text-base font-medium text-white mb-1">No Training Plan Yet</p>
        <p className="text-sm" style={{ color: "var(--color-muted)" }}>
          Run an analysis to generate your personalised 7-day plan.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Plan header */}
      <div
        className="rounded-lg border p-5 mb-5"
        style={{
          background: "var(--color-surface)",
          borderColor: "var(--color-border)",
        }}
      >
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-base font-semibold text-white mb-0.5">
              7-Day Training Plan
            </h2>
            <p className="text-sm" style={{ color: "var(--color-accent)" }}>
              {plan.week_focus}
            </p>
          </div>
          <div
            className="text-right rounded-lg px-3 py-2"
            style={{ background: "var(--color-background)" }}
          >
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>TSS Target</p>
            <p className="text-xl font-bold" style={{ color: "var(--color-accent)" }}>
              {plan.tss_target}
            </p>
          </div>
        </div>
        <p className="text-sm" style={{ color: "#d1d5db" }}>
          {plan.coaching_notes}
        </p>
      </div>

      {/* Day cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-7 gap-3">
        {plan.days.map((day) => (
          <DayCard key={day.day} day={day} />
        ))}
      </div>
    </div>
  );
}
