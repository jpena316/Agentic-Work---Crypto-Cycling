"""Rides router — Strava activity data endpoints."""

from fastapi import APIRouter, HTTPException, Query

from api.models.responses import ActivitiesResponse, ActivityResponse, RideSummaryResponse
from api.services.cache import cache
from server.tools.coaching_tools import get_ride_summary
from tools.strava_client import StravaClient

router = APIRouter(prefix="/rides", tags=["rides"])


@router.get("/summary", response_model=RideSummaryResponse)
async def rides_summary(days: int = Query(default=30, ge=1, le=365)):
    """
    Fetch a lightweight ride summary for the last *days* days.
    Cached for 5 minutes.
    """
    cache_key = f"rides:summary:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await get_ride_summary(days=days)
        response = RideSummaryResponse(**result)
        cache.set(cache_key, response, ttl_seconds=300)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities", response_model=ActivitiesResponse)
async def rides_activities(days: int = Query(default=45, ge=1, le=365)):
    """
    Return the raw activity list for the last *days* days (all sport types).
    Cached for 5 minutes.
    """
    cache_key = f"rides:activities:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        client = StravaClient()
        activities = await client.get_activities(days=days)
        response = ActivitiesResponse(
            days_lookback=days,
            count=len(activities),
            activities=[ActivityResponse(**a.model_dump()) for a in activities],
        )
        cache.set(cache_key, response, ttl_seconds=300)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
