"""Bikes router — bike profiles and recommendations endpoints."""

from fastapi import APIRouter, HTTPException

from api.models.responses import (
    BikeProfileResponse,
    BikeProfilesResponse,
    BikeRecommendationsResponse,
)
from api.services.cache import cache
from api.services.session import get_last_report
from server.tools.coaching_tools import get_bike_profiles

router = APIRouter(prefix="/bikes", tags=["bikes"])


@router.get("/profiles", response_model=BikeProfilesResponse)
async def bikes_profiles():
    """
    Return spec profiles for all bikes in data/bikes/.
    Cached for 24 hours — bike data rarely changes.
    """
    cache_key = "bikes:profiles"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await get_bike_profiles()
        response = BikeProfilesResponse(
            count=result["count"],
            bike_profiles=[BikeProfileResponse(**p) for p in result["bike_profiles"]],
        )
        cache.set(cache_key, response, ttl_seconds=86400)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=BikeRecommendationsResponse)
async def bikes_recommendations():
    """
    Return ranked bike recommendations from the most recent coaching run.

    Returns 404 if /analysis/run has not been called yet this session.
    """
    report = get_last_report()
    if not report or not report.get("bike_recommendations"):
        raise HTTPException(
            status_code=404,
            detail="No bike recommendations available. Call POST /analysis/run first.",
        )
    return BikeRecommendationsResponse(**report["bike_recommendations"])
