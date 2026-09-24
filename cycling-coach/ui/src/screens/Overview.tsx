import { useMemo } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BikeProfile, CoachingReport } from "@/api";
import { useRideSummary } from "@/hooks/useRideSummary";
import { useDerivedMetrics } from "@/hooks/useDerivedMetrics";
import { StatTile } from "@/components/shared/StatTile";
import { Card } from "@/components/shared/Card";
import { ContributionHeatmap } from "@/components/shared/ContributionHeatmap";
import { RunAnalysisPanel } from "@/components/shared/RunAnalysisPanel";
import { PerformanceInsights } from "@/components/shared/PerformanceInsights";
import { CHART_COLORS } from "@/lib/theme";

interface OverviewProps {
  report: CoachingReport | null;
  isLoading: boolean;
  elapsedSeconds: number;
  bikeProfiles: BikeProfile[];
  onRunAnalysis: (goals: string[], bikes: string[]) => void;
}

const CYCLING_TYPES = new Set(["Ride", "VirtualRide"]);

export function Overview({ report, isLoading, elapsedSeconds, bikeProfiles, onRunAnalysis }: OverviewProps) {
  const { summary, isLoading: summaryLoading } = useRideSummary();
  const { activities, heatmapCells, isLoading: metricsLoading } = useDerivedMetrics();

  const rideTypeData = useMemo(() => {
    const cycling = activities.filter((a) => CYCLING_TYPES.has(a.type));
    const indoor = cycling.filter((a) => a.type === "VirtualRide").length;
    const outdoor = cycling.length - indoor;
    return [
      { name: "Outdoor", value: outdoor, color: CHART_COLORS.accent },
      { name: "Indoor", value: indoor, color: CHART_COLORS.accentLight },
    ].filter((d) => d.value > 0);
  }, [activities]);

  const elevationData = useMemo(() => {
    return activities
      .filter((a) => CYCLING_TYPES.has(a.type))
      .slice()
      .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime())
      .slice(-12)
      .map((a) => ({
        name: new Date(a.start_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        elevation: Math.round(a.total_elevation_gain),
      }));
  }, [activities]);

  const bestBike = report?.bike_recommendations
    ? bikeProfiles.find((b) => b.name === report.bike_recommendations!.best_overall)
    : null;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-heading text-xl font-bold text-text">Overview</h1>
        <p className="text-sm text-muted mt-1">Your season at a glance.</p>
      </div>

      <RunAnalysisPanel
        onRunAnalysis={onRunAnalysis}
        isLoading={isLoading}
        elapsedSeconds={elapsedSeconds}
        availableBikes={bikeProfiles}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile
          label="Total Rides"
          value={summaryLoading ? "—" : String(summary?.cycling_rides ?? 0)}
        />
        <StatTile
          label="Total Distance"
          value={summaryLoading ? "—" : `${Math.round(summary?.total_distance_km ?? 0).toLocaleString()} km`}
        />
        <StatTile
          label="Total Elevation"
          value={summaryLoading ? "—" : `${Math.round(summary?.total_elevation_m ?? 0).toLocaleString()} m`}
        />
        <StatTile
          label="Avg Duration"
          value={summaryLoading ? "—" : `${Math.round(summary?.avg_duration_mins ?? 0)} min`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <h2 className="font-heading text-sm font-semibold text-text mb-3">Training Load</h2>
          {metricsLoading ? (
            <p className="text-sm text-muted">Loading…</p>
          ) : (
            <ContributionHeatmap cells={heatmapCells} />
          )}
        </Card>

        <Card>
          <h2 className="font-heading text-sm font-semibold text-text mb-3">Ride Type Mix</h2>
          {rideTypeData.length === 0 ? (
            <p className="text-sm text-muted">No ride data yet.</p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={rideTypeData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={2}
                  >
                    {rideTypeData.map((d) => (
                      <Cell key={d.name} fill={d.color} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: CHART_COLORS.surface,
                      border: `1px solid ${CHART_COLORS.border}`,
                      borderRadius: 8,
                      fontSize: 12,
                      color: CHART_COLORS.text,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 text-xs text-muted mt-1">
                {rideTypeData.map((d) => (
                  <span key={d.name} className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full" style={{ background: d.color }} />
                    {d.name} ({d.value})
                  </span>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <h2 className="font-heading text-sm font-semibold text-text mb-1">Elevation Gain — Recent Rides</h2>
          <p className="text-xs text-muted mb-3">
            Per-ride elevation gain across your last {elevationData.length} rides.
          </p>
          {elevationData.length === 0 ? (
            <p className="text-sm text-muted">No ride data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={elevationData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: CHART_COLORS.muted }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: CHART_COLORS.muted }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: CHART_COLORS.surface,
                    border: `1px solid ${CHART_COLORS.border}`,
                    borderRadius: 8,
                    fontSize: 12,
                    color: CHART_COLORS.text,
                  }}
                  cursor={{ fill: "rgba(255,255,255,0.03)" }}
                />
                <Bar dataKey="elevation" fill={CHART_COLORS.accent} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <h2 className="font-heading text-sm font-semibold text-text mb-3">Bike Recommendation</h2>
          {report?.bike_recommendations && bestBike ? (
            <div className="flex flex-col gap-2">
              <p className="font-heading font-semibold text-text">{bestBike.name}</p>
              <p className="text-xs text-muted capitalize">{bestBike.category}</p>
              <p className="text-sm text-text mt-1 leading-relaxed">
                {report.bike_recommendations.rationale[bestBike.name]}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted">Run an analysis to get a bike recommendation.</p>
          )}
        </Card>
      </div>

      {report?.performance_analysis && (
        <PerformanceInsights analysis={report.performance_analysis} />
      )}
    </div>
  );
}
