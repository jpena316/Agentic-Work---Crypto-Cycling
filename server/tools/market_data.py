import httpx
from server.config import settings
from server.models.schemas import MarketDataInput, MarketDataOutput


async def get_market_data(token: str) -> MarketDataOutput:
    """
    Fetch current market data for a given token from CoinGecko.
    Returns price, market cap, volume, price changes, and ATH drawdown.
    """
    validated = MarketDataInput(token=token)
    coin_id = validated.token.lower().strip()

    url = f"{settings.coingecko_base_url}/coins/{coin_id}"

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
    }

    headers = {}
    if settings.coingecko_api_key:
        headers["x-cg-pro-api-key"] = settings.coingecko_api_key

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    md = data["market_data"]
    ath = md["ath"]["usd"]
    current_price = md["current_price"]["usd"]
    ath_drawdown = ((current_price - ath) / ath) * 100

    return MarketDataOutput(
        token=coin_id,
        name=data["name"],
        symbol=data["symbol"].upper(),
        price_usd=current_price,
        market_cap_usd=md["market_cap"]["usd"],
        volume_24h_usd=md["total_volume"]["usd"],
        price_change_24h_pct=md["price_change_percentage_24h"] or 0.0,
        price_change_7d_pct=md["price_change_percentage_7d"] or 0.0,
        circulating_supply=md["circulating_supply"] or 0.0,
        ath_usd=ath,
        ath_drawdown_pct=round(ath_drawdown, 2),
        last_updated=md["last_updated"],
    )