"""Factory for the shared context dict passed between all pipeline agents."""

import uuid
from datetime import datetime, timezone


def create_context(
    athlete_goals: list[str],
    bikes_under_consideration: list[str],
) -> dict:
    """Build the initial context dict that every agent reads from and writes to.

    Each agent receives this dict, populates its designated keys, and passes
    it to the next agent.  Keys set to ``None`` or ``[]`` indicate that no
    agent has written to them yet.

    Args:
        athlete_goals: Free-text goal strings supplied by the user
            (e.g. ``["lose 5 kg", "complete first century ride"]``).
        bikes_under_consideration: Bike model names the user wants evaluated
            (e.g. ``["Canyon Aeroad CF SLX 8", "Trek Madone SLR 7"]``).

    Returns:
        Initialized context dict with all expected keys present.
    """
    return {
        # --- Agent 1: Data Retrieval ---
        "athlete_profile": None,        # AthleteProfile dict from Strava
        "raw_activities": [],           # list of Activity dicts (unfiltered)
        "computed_metrics": None,       # aggregated training stats dict

        # --- Agent 2: Performance Analysis ---
        "performance_analysis": None,   # LLM-generated performance summary
        "rider_signature": None,        # riding style / strengths / limiter classification

        # --- Agent 3: Training Plan ---
        "training_plan": None,          # structured weekly training plan dict

        # --- Agent 4: Bike Recommender ---
        "bike_profiles": [],            # list of scraped/loaded bike spec dicts
        "bike_recommendations": None,   # ranked bike recommendations with reasoning

        # --- Inputs (set once at creation, read-only for agents) ---
        "athlete_goals": athlete_goals,
        "bikes_under_consideration": bikes_under_consideration,

        # --- System ---
        "errors": [],                   # error strings appended by any agent
        "metadata": {
            "run_id": str(uuid.uuid4()),
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    }
