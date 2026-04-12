from fastapi import APIRouter, HTTPException, Query
from api.services.mcp_client import fetch_technical_analysis
from api.services.cache import cache
from api.models.responses import TechnicalAnalysisResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{token}", response_model=TechnicalAnalysisResponse)
async def get_technical_analysis(
    token: str,
    days: int = Query(default=30, ge=14, le=90),
):
    """
    Run technical analysis on a cryptocurrency.
    Results cached for 5 minutes.
    """
    cache_key = f"analysis:{token.lower()}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await fetch_technical_analysis(token.lower(), days)
        response = TechnicalAnalysisResponse(**result.model_dump())
        cache.set(cache_key, response, ttl_seconds=300)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))