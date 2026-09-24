import { useMemo } from "react";
import { useActivities } from "./useActivities";
import {
  inferFtp,
  bucketDailyTss,
  calculateCtlAtlTsb,
  buildHeatmapCells,
} from "../lib/metrics";

const LOOKBACK_DAYS = 120; // gives the 42-day CTL EWMA room to stabilize
const HEATMAP_DAYS = 120;

export function useDerivedMetrics() {
  const { activities, isLoading, error } = useActivities(LOOKBACK_DAYS);

  const derived = useMemo(() => {
    const ftp = inferFtp(activities);
    const dailyTss = bucketDailyTss(activities, ftp, HEATMAP_DAYS);
    const ctlAtlTsb = calculateCtlAtlTsb(dailyTss);
    const heatmapCells = buildHeatmapCells(dailyTss);
    const todayPoint = ctlAtlTsb[ctlAtlTsb.length - 1] ?? null;
    return { ftp, dailyTss, ctlAtlTsb, heatmapCells, todayPoint };
  }, [activities]);

  return { ...derived, activities, isLoading, error };
}
