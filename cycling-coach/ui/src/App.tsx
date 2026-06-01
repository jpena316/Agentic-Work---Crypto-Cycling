import { useEffect, useState } from "react";
import { BikeRankings } from "./components/Bikes/BikeRankings";
import { PerformancePanel } from "./components/Dashboard/PerformancePanel";
import { RideSummary } from "./components/Dashboard/RideSummary";
import { TrainingPlan } from "./components/Dashboard/TrainingPlan";
import { Header } from "./components/Layout/Header";
import { Sidebar } from "./components/Layout/Sidebar";
import type { View } from "./components/Layout/Sidebar";
import { useAnalysis } from "./hooks/useAnalysis";
import { useBikes } from "./hooks/useBikes";
import { healthCheck } from "./api";

function EmptyState({ message }: { message: string }) {
  return (
    <div
      className="rounded-lg border p-10 text-center"
      style={{
        background: "var(--color-surface)",
        borderColor: "var(--color-border)",
      }}
    >
      <p className="text-4xl mb-3">⚡</p>
      <p className="text-base font-medium text-white mb-1">No Data Yet</p>
      <p className="text-sm" style={{ color: "var(--color-muted)" }}>
        {message}
      </p>
    </div>
  );
}

function ErrorBanner({ errors }: { errors: string[] }) {
  if (!errors.length) return null;
  return (
    <div
      className="rounded-lg border p-3 mb-4 text-sm"
      style={{
        background: "rgba(239,68,68,0.08)",
        borderColor: "rgba(239,68,68,0.3)",
        color: "var(--color-negative)",
      }}
    >
      <p className="font-semibold mb-1">Pipeline errors ({errors.length})</p>
      <ul className="list-disc list-inside space-y-0.5">
        {errors.map((e, i) => (
          <li key={i} className="text-xs">{e}</li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const [activeView, setActiveView] = useState<View>("dashboard");
  const [apiOnline, setApiOnline] = useState(false);

  const { report, isLoading, error: analysisError, elapsedSeconds, run } = useAnalysis();
  const { profiles: bikeProfiles } = useBikes();

  // Check API health on mount
  useEffect(() => {
    healthCheck().then(setApiOnline);
  }, []);

  return (
    <div style={{ background: "var(--color-background)", color: "#e5e7eb", minHeight: "100vh" }}>
      <Header isAnalysisRunning={isLoading} apiOnline={apiOnline} />

      <div className="flex" style={{ height: "calc(100vh - 56px)" }}>
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          onRunAnalysis={run}
          isLoading={isLoading}
          elapsedSeconds={elapsedSeconds}
          availableBikes={bikeProfiles}
        />

        <main className="flex-1 overflow-y-auto p-6">
          {/* Analysis-level error */}
          {analysisError && (
            <div
              className="rounded-lg border p-3 mb-4 text-sm"
              style={{
                background: "rgba(239,68,68,0.08)",
                borderColor: "rgba(239,68,68,0.3)",
                color: "var(--color-negative)",
              }}
            >
              {analysisError}
            </div>
          )}

          {/* Pipeline errors from partial run */}
          {report && <ErrorBanner errors={report.errors} />}

          {/* ---- Dashboard view ---- */}
          {activeView === "dashboard" && (
            <div>
              <RideSummary />

              {report?.performance_analysis ? (
                <PerformancePanel analysis={report.performance_analysis} />
              ) : !isLoading ? (
                <EmptyState message="Run an analysis to see your performance breakdown." />
              ) : (
                <div
                  className="rounded-lg border p-6 mb-6 animate-pulse"
                  style={{
                    background: "var(--color-surface)",
                    borderColor: "var(--color-border)",
                    height: 200,
                  }}
                />
              )}
            </div>
          )}

          {/* ---- Training plan view ---- */}
          {activeView === "plan" && (
            <TrainingPlan plan={report?.training_plan ?? null} />
          )}

          {/* ---- Bike rankings view ---- */}
          {activeView === "bikes" && (
            <BikeRankings
              profiles={bikeProfiles}
              recommendations={report?.bike_recommendations ?? null}
            />
          )}
        </main>
      </div>
    </div>
  );
}
