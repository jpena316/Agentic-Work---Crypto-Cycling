import { Navigate, Route, Routes } from "react-router-dom";
import { TopBar } from "./components/shared/TopBar";
import { Overview } from "./screens/Overview";
import { Today } from "./screens/Today";
import { Bikes } from "./screens/Bikes";
import { useAnalysis } from "./hooks/useAnalysis";
import { useBikes } from "./hooks/useBikes";

function ErrorBanner({ errors }: { errors: string[] }) {
  if (!errors.length) return null;
  return (
    <div className="rounded-[14px] border border-negative/30 bg-negative/10 p-3 mb-4 text-sm text-negative">
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
  const { report, isLoading, error: analysisError, elapsedSeconds, run } = useAnalysis();
  const { profiles: bikeProfiles } = useBikes();

  return (
    <div className="min-h-screen bg-background text-text">
      <TopBar />

      <main className="max-w-[1400px] mx-auto p-6">
        {analysisError && (
          <div className="rounded-[14px] border border-negative/30 bg-negative/10 p-3 mb-4 text-sm text-negative">
            {analysisError}
          </div>
        )}

        {report && <ErrorBanner errors={report.errors} />}

        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route
            path="/overview"
            element={
              <Overview
                report={report}
                isLoading={isLoading}
                elapsedSeconds={elapsedSeconds}
                bikeProfiles={bikeProfiles}
                onRunAnalysis={run}
              />
            }
          />
          <Route path="/today" element={<Today report={report} bikeProfiles={bikeProfiles} />} />
          <Route
            path="/bikes"
            element={
              <Bikes profiles={bikeProfiles} recommendations={report?.bike_recommendations ?? null} />
            }
          />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </main>
    </div>
  );
}
