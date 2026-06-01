import { useEffect, useState } from "react";
import { getRideSummary } from "../api";
import type { RideSummary } from "../api";

export function useRideSummary(days = 30) {
  const [summary, setSummary] = useState<RideSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getRideSummary(days)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Failed to load rides");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  return { summary, isLoading, error };
}
