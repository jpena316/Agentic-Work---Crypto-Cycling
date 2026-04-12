from pydantic import BaseModel


class MarketDataResponse(BaseModel):
    token: str
    name: str
    symbol: str
    price_usd: float
    market_cap_usd: float
    volume_24h_usd: float
    price_change_24h_pct: float
    price_change_7d_pct: float
    circulating_supply: float
    ath_usd: float
    ath_drawdown_pct: float
    last_updated: str


class TechnicalSignalsResponse(BaseModel):
    sma_7: float
    sma_30: float
    sma_cross_signal: str
    rsi_14: float
    rsi_signal: str
    volume_trend: str
    volume_ratio: float
    price_trend: str
    support_level: float
    resistance_level: float


class TechnicalAnalysisResponse(BaseModel):
    token: str
    days_analyzed: int
    current_price: float
    signals: TechnicalSignalsResponse
    summary: str


class NewsItemResponse(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    sentiment: str


class NewsSentimentResponse(BaseModel):
    token: str
    days_analyzed: int
    total_articles: int
    sentiment_breakdown: dict[str, int]
    sentiment_score: float
    top_headlines: list[NewsItemResponse]


class InvestmentBriefResponse(BaseModel):
    token: str
    generated_at: str
    brief_markdown: str


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""