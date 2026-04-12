import httpx
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from server.config import settings
from server.models.schemas import TechnicalAnalysisInput, TechnicalAnalysisOutput, TechnicalSignals


async def run_technical_analysis(token: str, days: int = 30) -> TechnicalAnalysisOutput:
    """
    Fetch OHLCV data from CoinGecko and compute technical indicators.
    Returns SMA-7, SMA-30, RSI-14, volume trend, support/resistance levels.
    """
    validated = TechnicalAnalysisInput(token=token, days=days)
    coin_id = validated.token.lower().strip()
    lookback = max(validated.days, 30)

    url = f"{settings.coingecko_base_url}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": lookback, "interval": "daily"}

    headers = {}
    if settings.coingecko_api_key:
        headers["x-cg-pro-api-key"] = settings.coingecko_api_key

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    # Build DataFrame from OHLCV data
    prices = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
    volumes = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
    df = prices.merge(volumes, on="timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Compute indicators
    df["sma_7"] = SMAIndicator(close=df["close"], window=7).sma_indicator()
    df["sma_30"] = SMAIndicator(close=df["close"], window=30).sma_indicator()
    df["rsi_14"] = RSIIndicator(close=df["close"], window=14).rsi()

    latest = df.iloc[-1]
    current_price = float(latest["close"])
    sma_7 = float(latest["sma_7"])
    sma_30 = float(latest["sma_30"])
    rsi_14 = float(latest["rsi_14"])

    # SMA cross signal
    if sma_7 > sma_30:
        sma_cross_signal = "bullish"
    elif sma_7 < sma_30:
        sma_cross_signal = "bearish"
    else:
        sma_cross_signal = "neutral"

    # RSI signal
    if rsi_14 >= 70:
        rsi_signal = "overbought"
    elif rsi_14 <= 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    # Volume trend: compare 5-day avg to 30-day avg
    vol_5d = df["volume"].iloc[-5:].mean()
    vol_30d = df["volume"].iloc[-30:].mean()
    volume_ratio = round(float(vol_5d / vol_30d), 2)

    if volume_ratio > 1.1:
        volume_trend = "increasing"
    elif volume_ratio < 0.9:
        volume_trend = "decreasing"
    else:
        volume_trend = "stable"

    # Price trend: compare current price to 30-day ago
    price_30d_ago = float(df["close"].iloc[0])
    if current_price > price_30d_ago * 1.05:
        price_trend = "uptrend"
    elif current_price < price_30d_ago * 0.95:
        price_trend = "downtrend"
    else:
        price_trend = "sideways"

    # Support and resistance: 30-day low and high
    support_level = round(float(df["close"].min()), 2)
    resistance_level = round(float(df["close"].max()), 2)

    # Plain English summary
    summary = (
        f"{coin_id.capitalize()} is showing {price_trend} price action over {lookback} days. "
        f"RSI is {round(rsi_14, 1)} ({rsi_signal}) and the SMA cross is {sma_cross_signal}. "
        f"Volume is {volume_trend} relative to the 30-day average."
    )

    return TechnicalAnalysisOutput(
        token=coin_id,
        days_analyzed=lookback,
        current_price=current_price,
        signals=TechnicalSignals(
            sma_7=round(sma_7, 2),
            sma_30=round(sma_30, 2),
            sma_cross_signal=sma_cross_signal,
            rsi_14=round(rsi_14, 2),
            rsi_signal=rsi_signal,
            volume_trend=volume_trend,
            volume_ratio=volume_ratio,
            price_trend=price_trend,
            support_level=support_level,
            resistance_level=resistance_level,
        ),
        summary=summary,
    )