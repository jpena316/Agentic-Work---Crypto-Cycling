from fastapi import APIRouter, HTTPException, Query
from api.services.mcp_client import fetch_market_data
from api.services.cache import cache
from api.models.responses import MarketDataResponse
import httpx

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


@router.get("/{token}/history")
async def get_price_history(
    token: str,
    days: int = Query(default=30, ge=7, le=90),
):
    """
    Fetch historical price data for charting.
    Returns list of {timestamp, price} points.
    Cached for 5 minutes.
    """
    cache_key = f"history:{token.lower()}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{token.lower()}/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        prices = [
            {"timestamp": point[0], "price": point[1]}
            for point in data["prices"]
        ]

        cache.set(cache_key, prices, ttl_seconds=300)
        return prices

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))