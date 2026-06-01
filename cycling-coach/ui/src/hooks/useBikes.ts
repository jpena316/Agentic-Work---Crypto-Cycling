import { useEffect, useState } from "react";
import { getBikeProfiles } from "../api";
import type { BikeProfile } from "../api";

export function useBikes() {
  const [profiles, setProfiles] = useState<BikeProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    getBikeProfiles()
      .then((data) => {
        if (!cancelled) setProfiles(data.bike_profiles);
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load bike profiles"
          );
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { profiles, isLoading, error };
}
