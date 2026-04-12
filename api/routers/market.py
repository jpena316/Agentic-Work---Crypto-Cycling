from fastapi import APIRouter, HTTPException
from api.services.mcp_client import fetch_market_data
from api.services.cache import cache
from api.models.responses import MarketDataResponse

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/{token}", response_model=MarketDataResponse)
async def get_market_data(token: str):
    """
    Fetch live market data for a cryptocurrency.
    Results cached for 60 seconds to respect CoinGecko rate limits.
    """
    cache_key = f"market:{token.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await fetch_market_data(token.lower())
        response = MarketDataResponse(**result.model_dump())
        cache.set(cache_key, response, ttl_seconds=60)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))