"""Input schemas and tool implementations for the cycling-coach MCP server."""

import json
from pathlib import Path

from pydantic import BaseModel

from orchestrator.orchestrator import CyclingCoachOrchestrator
from tools.strava_client import StravaClient

_BIKES_DIR = Path(__file__).parent.parent.parent / "data" / "bikes"
_CYCLING_TYPES = {"Ride", "VirtualRide"}


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class RunCoachingSessionInput(BaseModel):
    """Inputs for a full AI coaching pipeline run."""

    athlete_goals: list[str]
    bikes_under_consideration: list[str]


class GetRideSummaryInput(BaseModel):
    """Inputs for the lightweight ride summary tool."""

    days: int = 30


class GetBikeProfilesInput(BaseModel):
    """No inputs required — returns all cached bike profiles."""


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def run_coaching_session(
    athlete_goals: list[str],
    bikes_under_consideration: list[str],
) -> dict:
    """Run the full four-agent coaching pipeline and return the report.

    Delegates to :class:`CyclingCoachOrchestrator` which fetches live Strava
    data, calls Claude for performance analysis and training planning, and
    ranks the supplied bikes by fit to the rider's profile.

    Args:
        athlete_goals: Free-text goals, e.g. ``["build endurance", "increase FTP"]``.
        bikes_under_consideration: Bike model names to evaluate.

    Returns:
        Full coaching report dict (status, analysis, plan, recommendations).
    """
    orchestrator = CyclingCoachOrchestrator()
    return await orchestrator.run(
        athlete_goals=athlete_goals,
        bikes_under_consideration=bikes_under_consideration,
    )


async def get_ride_summary(days: int = 30) -> dict:
    """Fetch a lightweight ride summary directly from Strava.

    Skips the full orchestration pipeline — useful for a quick data check
    before committing to a full coaching session.

    Args:
        days: How many days of history to retrieve (default 30).

    Returns:
        Summary dict with ride counts, totals, and averages.
    """
    client = StravaClient()
    all_activities = await client.get_activities(days=days)
    rides = [a for a in all_activities if a.type in _CYCLING_TYPES]

    if not rides:
        return {
            "days_lookback": days,
            "total_activities": len(all_activities),
            "cycling_rides": 0,
            "total_distance_km": 0.0,
            "total_elevation_m": 0.0,
            "avg_duration_mins": 0.0,
            "longest_ride_km": 0.0,
        }

    total_distance = round(sum(r.distance for r in rides) / 1000, 1)
    total_elevation = round(sum(r.total_elevation_gain for r in rides), 0)
    avg_duration = round(sum(r.moving_time for r in rides) / len(rides) / 60, 1)
    longest = round(max(r.distance for r in rides) / 1000, 1)

    return {
        "days_lookback": days,
        "total_activities": len(all_activities),
        "cycling_rides": len(rides),
        "total_distance_km": total_distance,
        "total_elevation_m": total_elevation,
        "avg_duration_mins": avg_duration,
        "longest_ride_km": longest,
    }


async def get_bike_profiles() -> dict:
    """Return spec profiles for all bikes in data/bikes/.

    For each bike JSON file: uses the stored spec if it has been populated,
    otherwise falls back to the hardcoded reference specs in the bike
    recommender module so Claude always receives complete profile data.

    Returns:
        Dict with a ``bike_profiles`` list and a ``count`` field.
    """
    from agents.bike_recommender import _FALLBACK_SPECS

    profiles: list[dict] = []

    for json_file in sorted(_BIKES_DIR.glob("*.json")):
        key = json_file.stem
        try:
            spec: dict = json.loads(json_file.read_text())
        except Exception:
            continue

        if spec.get("name"):
            profiles.append(spec)
        elif key in _FALLBACK_SPECS:
            profiles.append(_FALLBACK_SPECS[key])

    return {"bike_profiles": profiles, "count": len(profiles)}
