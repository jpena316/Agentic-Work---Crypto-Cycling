import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8001",
  timeout: 0, // analysis endpoint can take 2-3 min; individual calls set their own
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RideSummary {
  days_lookback: number;
  total_activities: number;
  cycling_rides: number;
  total_distance_km: number;
  total_elevation_m: number;
  avg_duration_mins: number;
  longest_ride_km: number;
}

export interface Activity {
  id: number;
  name: string;
  type: string;
  distance: number;
  moving_time: number;
  total_elevation_gain: number;
  average_watts: number | null;
  average_heartrate: number | null;
  suffer_score: number | null;
  start_date: string;
}

export interface PerformanceAnalysis {
  strengths: string[];
  weaknesses: string[];
  fatigue_level: string;
  overtraining_risk: string;
  fitness_trend: string;
  key_observations: string[];
  recommended_focus: string;
}

export interface TrainingDay {
  day: string;
  workout_type: string;
  duration_mins: number;
  intensity: string;
  description: string;
  rationale: string;
}

export interface TrainingPlan {
  week_focus: string;
  tss_target: number;
  days: TrainingDay[];
  coaching_notes: string;
}

export interface BikeGeometry {
  stack: number;
  reach: number;
  head_tube_angle: number;
  bb_drop: number;
}

export interface BikeComponents {
  groupset: string;
  drivetrain: string;
  brakes: string;
  wheelset: string;
}

export interface BikeProfile {
  name: string;
  brand: string;
  model: string;
  category: string;
  price_usd: number;
  weight_kg: number;
  geometry: BikeGeometry;
  components: BikeComponents;
  intended_use: string[];
  terrain_fit: string[];
  key_characteristics: string[];
  source_url: string;
}

export interface BikeRecommendations {
  ranked: string[];
  match_scores: Record<string, number>;
  rationale: Record<string, string>;
  best_overall: string;
  summary: string;
}

export interface RiderSignature {
  dominant_terrain: string;
  riding_style: string;
  fitness_level: string;
  goals: string[];
  training_focus: string;
  ftp: number | null;
  weight_kg: number | null;
  avg_ride_duration_mins: number;
  rides_per_week: number;
  elevation_per_km: number;
  weekly_tss: number;
  fitness_trend: string;
}

export interface CoachingReport {
  status: string;
  athlete: Record<string, unknown> | null;
  performance_analysis: PerformanceAnalysis | null;
  training_plan: TrainingPlan | null;
  bike_recommendations: BikeRecommendations | null;
  rider_signature: RiderSignature | null;
  errors: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getRideSummary(days = 30): Promise<RideSummary> {
  const { data } = await client.get<RideSummary>("/rides/summary", {
    params: { days },
    timeout: 15_000,
  });
  return data;
}

export async function getActivities(
  days = 45
): Promise<{ days_lookback: number; count: number; activities: Activity[] }> {
  const { data } = await client.get("/rides/activities", {
    params: { days },
    timeout: 15_000,
  });
  return data;
}

export async function runAnalysis(
  athlete_goals: string[],
  bikes: string[]
): Promise<CoachingReport> {
  const { data } = await client.post<CoachingReport>("/analysis/run", {
    athlete_goals,
    bikes,
  });
  return data;
}

export async function getBikeProfiles(): Promise<{
  count: number;
  bike_profiles: BikeProfile[];
}> {
  const { data } = await client.get("/bikes/profiles", { timeout: 10_000 });
  return data;
}

export async function getBikeRecommendations(): Promise<BikeRecommendations> {
  const { data } = await client.get<BikeRecommendations>(
    "/bikes/recommendations",
    { timeout: 10_000 }
  );
  return data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    await client.get("/health", { timeout: 3_000 });
    return true;
  } catch {
    return false;
  }
}
