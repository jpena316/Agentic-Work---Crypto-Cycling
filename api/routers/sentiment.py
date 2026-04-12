from fastapi import APIRouter, HTTPException, Query
from api.services.mcp_client import fetch_news_sentiment
from api.services.cache import cache
from api.models.responses import NewsSentimentResponse

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/{token}", response_model=NewsSentimentResponse)
async def get_news_sentiment(
    token: str,
    days: int = Query(default=7, ge=1, le=30),
):
    """
    Fetch news sentiment for a cryptocurrency.
    Results cached for 15 minutes.
    """
    cache_key = f"sentiment:{token.lower()}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await fetch_news_sentiment(token.lower(), days)
        response = NewsSentimentResponse(**result.model_dump())
        cache.set(cache_key, response, ttl_seconds=900)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))