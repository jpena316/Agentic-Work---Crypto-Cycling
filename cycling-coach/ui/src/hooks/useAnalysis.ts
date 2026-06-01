import { useCallback, useState } from "react";
import { runAnalysis } from "../api";
import type { CoachingReport } from "../api";

export function useAnalysis() {
  const [report, setReport] = useState<CoachingReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const run = useCallback(async (goals: string[], bikes: string[]) => {
    setIsLoading(true);
    setError(null);
    setElapsedSeconds(0);

    const start = Date.now();
    const timer = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - start) / 1000));
    }, 1000);

    try {
      const result = await runAnalysis(goals, bikes);
      setReport(result);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Analysis failed — check that the API server is running"
      );
    } finally {
      clearInterval(timer);
      setIsLoading(false);
    }
  }, []);

  return { report, isLoading, error, elapsedSeconds, run };
}
