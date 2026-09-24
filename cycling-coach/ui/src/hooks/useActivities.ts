import axios from "axios";
import { useEffect, useState } from "react";
import { getActivities } from "../api";
import type { Activity } from "../api";

export function useActivities(days?: number) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getActivities(days)
      .then((data) => {
        if (!cancelled) setActivities(data.activities);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const detail = axios.isAxiosError(err) ? err.response?.data?.detail : undefined;
          setError(detail ?? (err instanceof Error ? err.message : "Failed to load activities"));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [days]);

  return { activities, isLoading, error };
}
