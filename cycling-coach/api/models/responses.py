"""Pydantic request and response models for the Cycling Coach API."""

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Rides
# ---------------------------------------------------------------------------

class RideSummaryResponse(BaseModel):
    days_lookback: int
    total_activities: int
    cycling_rides: int
    total_distance_km: float
    total_elevation_m: float
    avg_duration_mins: float
    longest_ride_km: float


class ActivityResponse(BaseModel):
    id: int
    name: str
    type: str
    distance: float
    moving_time: int
    total_elevation_gain: float
    average_watts: float | None = None
    average_heartrate: float | None = None
    suffer_score: int | None = None
    start_date: str


class ActivitiesResponse(BaseModel):
    days_lookback: int
    count: int
    activities: list[ActivityResponse]


# ---------------------------------------------------------------------------
# Analysis (orchestrator run)
# ---------------------------------------------------------------------------

class CoachingRunRequest(BaseModel):
    athlete_goals: list[str]
    bikes: list[str]


class CoachingReportResponse(BaseModel):
    status: str
    athlete: dict[str, Any] | None = None
    performance_analysis: dict[str, Any] | None = None
    training_plan: dict[str, Any] | None = None
    bike_recommendations: dict[str, Any] | None = None
    rider_signature: dict[str, Any] | None = None
    errors: list[str] = []
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Training plan
# ---------------------------------------------------------------------------

class TrainingDayResponse(BaseModel):
    day: str
    workout_type: str
    duration_mins: int
    intensity: str
    description: str
    rationale: str


class TrainingPlanResponse(BaseModel):
    week_focus: str
    tss_target: float
    days: list[TrainingDayResponse]
    coaching_notes: str


# ---------------------------------------------------------------------------
# Bikes
# ---------------------------------------------------------------------------

class BikeGeometryResponse(BaseModel):
    stack: float = 0
    reach: float = 0
    head_tube_angle: float = 0
    bb_drop: float = 0


class BikeComponentsResponse(BaseModel):
    groupset: str = ""
    drivetrain: str = ""
    brakes: str = ""
    wheelset: str = ""


class BikeProfileResponse(BaseModel):
    name: str
    brand: str = ""
    model: str = ""
    category: str = ""
    price_usd: int = 0
    weight_kg: float = 0.0
    geometry: BikeGeometryResponse = BikeGeometryResponse()
    components: BikeComponentsResponse = BikeComponentsResponse()
    intended_use: list[str] = []
    terrain_fit: list[str] = []
    key_characteristics: list[str] = []
    source_url: str = ""


class BikeProfilesResponse(BaseModel):
    count: int
    bike_profiles: list[BikeProfileResponse]


class BikeRecommendationsResponse(BaseModel):
    ranked: list[str]
    match_scores: dict[str, int]
    rationale: dict[str, str]
    best_overall: str
    summary: str


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
