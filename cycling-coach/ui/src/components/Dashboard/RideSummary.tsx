import { useRideSummary } from "../../hooks/useRideSummary";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}

function StatCard({ label, value, sub, accent }: StatCardProps) {
  return (
    <div
      className="rounded-lg p-4 border flex flex-col gap-1"
      style={{
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
      }}
    >
      <p className="text-xs" style={{ color: "var(--color-muted)" }}>
        {label}
      </p>
      <p
        className="text-2xl font-bold tracking-tight"
        style={{ color: accent ? "var(--color-accent)" : "#f3f4f6" }}
      >
        {value}
      </p>
      {sub && (
        <p className="text-xs" style={{ color: "var(--color-muted)" }}>
          {sub}
        </p>
      )}
    </div>
  );
}

export function RideSummary() {
  const { summary, isLoading, error } = useRideSummary(45);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg p-4 border animate-pulse h-24"
            style={{
              background: "var(--color-surface)",
              borderColor: "var(--color-border)",
            }}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="rounded-lg p-4 mb-6 text-sm border"
        style={{
          background: "rgba(239,68,68,0.08)",
          borderColor: "rgba(239,68,68,0.3)",
          color: "var(--color-negative)",
        }}
      >
        Could not load ride data: {error}
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--color-muted)" }}>
        Last 45 Days
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        <StatCard
          label="Rides"
          value={String(summary.cycling_rides)}
          sub={`of ${summary.total_activities} total`}
          accent
        />
        <StatCard
          label="Distance"
          value={`${summary.total_distance_km.toLocaleString()} km`}
        />
        <StatCard
          label="Elevation"
          value={`${summary.total_elevation_m.toLocaleString()} m`}
        />
        <StatCard
          label="Avg Duration"
          value={`${summary.avg_duration_mins} min`}
        />
        <StatCard
          label="Longest Ride"
          value={`${summary.longest_ride_km} km`}
        />
        <StatCard
          label="Lookback"
          value={`${summary.days_lookback} days`}
        />
      </div>
    </div>
  );
}
