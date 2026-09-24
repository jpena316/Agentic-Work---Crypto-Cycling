/**
 * Client-side training-load metrics, ported from the backend's
 * tools/metrics.py (read-only reference — not modified). The backend never
 * exposes per-day TSS or CTL/ATL/TSB, so these are derived here from the raw
 * activities returned by GET /rides/activities.
 *
 * Approximation: normalized power (NP) is estimated as average_watts, since
 * no power stream is available client-side — same simplification the
 * backend's calculate_weekly_load makes. Treat all TSS figures as estimates.
 */
import type { Activity } from "@/api";

const CYCLING_TYPES = new Set(["Ride", "VirtualRide"]);

export interface DailyTss {
  date: string; // YYYY-MM-DD
  tss: number;
}

/** 95% of best 20-min (>=1200s) average_watts in the pool; 200W fallback. */
export function inferFtp(activities: Activity[]): number {
  const candidates = activities
    .filter((a) => a.average_watts != null && a.moving_time >= 1200)
    .map((a) => a.average_watts as number);
  if (candidates.length === 0) return 200;
  return Math.max(...candidates) * 0.95;
}

export function calculateIntensityFactor(normalizedPower: number, ftp: number): number {
  if (ftp <= 0) return 0;
  return normalizedPower / ftp;
}

/** TSS = (duration_s * NP * IF) / (FTP * 3600) * 100 */
export function calculateTss(normalizedPower: number, ftp: number, durationSeconds: number): number {
  if (ftp <= 0) return 0;
  const intensityFactor = calculateIntensityFactor(normalizedPower, ftp);
  return ((durationSeconds * normalizedPower * intensityFactor) / (ftp * 3600)) * 100;
}

function dateKey(isoDate: string): string {
  return isoDate.slice(0, 10);
}

/** Zero-filled daily TSS totals for the last rangeDays days, ending today. */
export function bucketDailyTss(activities: Activity[], ftp: number, rangeDays: number): DailyTss[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const byDate = new Map<string, number>();
  for (const act of activities) {
    if (!CYCLING_TYPES.has(act.type)) continue;
    if (act.average_watts == null || act.moving_time === 0) continue;
    const key = dateKey(act.start_date);
    const tss = calculateTss(act.average_watts, ftp, act.moving_time);
    byDate.set(key, (byDate.get(key) ?? 0) + tss);
  }

  const days: DailyTss[] = [];
  for (let i = rangeDays - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    days.push({ date: key, tss: Math.round((byDate.get(key) ?? 0) * 10) / 10 });
  }
  return days;
}

export interface CtlAtlTsbPoint {
  date: string;
  ctl: number;
  atl: number;
  tsb: number;
}

/**
 * CTL = 42-day EWMA of daily TSS, ATL = 7-day EWMA of daily TSS,
 * TSB = yesterday's CTL - yesterday's ATL (assigned to each day's point).
 */
export function calculateCtlAtlTsb(dailyTss: DailyTss[]): CtlAtlTsbPoint[] {
  const CTL_TIME_CONSTANT = 42;
  const ATL_TIME_CONSTANT = 7;
  const ctlDecay = Math.exp(-1 / CTL_TIME_CONSTANT);
  const atlDecay = Math.exp(-1 / ATL_TIME_CONSTANT);

  let ctl = 0;
  let atl = 0;
  const points: CtlAtlTsbPoint[] = [];

  for (const day of dailyTss) {
    const tsb = ctl - atl; // yesterday's values, before today's TSS is folded in
    ctl = day.tss * (1 - ctlDecay) + ctl * ctlDecay;
    atl = day.tss * (1 - atlDecay) + atl * atlDecay;
    points.push({
      date: day.date,
      ctl: Math.round(ctl * 10) / 10,
      atl: Math.round(atl * 10) / 10,
      tsb: Math.round(tsb * 10) / 10,
    });
  }

  return points;
}

export interface HeatmapCell {
  date: string;
  tss: number;
  level: 0 | 1 | 2 | 3 | 4;
}

export function buildHeatmapCells(dailyTss: DailyTss[]): HeatmapCell[] {
  const max = Math.max(1, ...dailyTss.map((d) => d.tss));
  return dailyTss.map((d) => {
    const ratio = d.tss / max;
    let level: HeatmapCell["level"];
    if (d.tss <= 0) level = 0;
    else if (ratio < 0.25) level = 1;
    else if (ratio < 0.5) level = 2;
    else if (ratio < 0.75) level = 3;
    else level = 4;
    return { date: d.date, tss: d.tss, level };
  });
}
