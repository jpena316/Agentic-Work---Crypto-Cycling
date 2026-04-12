from pydantic import BaseModel, Field


# ── Market Data ───────────────────────────────────────────────

class MarketDataInput(BaseModel):
    token: str = Field(
        ...,
        description="CoinGecko coin ID e.g. 'bitcoin', 'ethereum', 'solana'"
    )


class MarketDataOutput(BaseModel):
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


# ── News Sentiment ────────────────────────────────────────────

class NewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    sentiment: str


class NewsSentimentInput(BaseModel):
    token: str = Field(
        ...,
        description="Token symbol e.g. 'BTC', 'ETH', 'SOL'"
    )
    days: int = Field(
        default=7,
        description="Number of days of news to retrieve (1-30)"
    )


class NewsSentimentOutput(BaseModel):
    token: str
    days_analyzed: int
    total_articles: int
    sentiment_breakdown: dict[str, int]
    sentiment_score: float
    top_headlines: list[NewsItem]


# ── Technical Analysis ────────────────────────────────────────

class TechnicalAnalysisInput(BaseModel):
    token: str = Field(
        ...,
        description="CoinGecko coin ID e.g. 'bitcoin', 'ethereum'"
    )
    days: int = Field(
        default=30,
        description="Lookback period in days (14-90)"
    )


class TechnicalSignals(BaseModel):
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


class TechnicalAnalysisOutput(BaseModel):
    token: str
    days_analyzed: int
    current_price: float
    signals: TechnicalSignals
    summary: str


# ── Investment Brief ──────────────────────────────────────────

class InvestmentBriefInput(BaseModel):
    token: str = Field(
        ...,
        description="CoinGecko coin ID e.g. 'bitcoin', 'ethereum'"
    )
    horizon: str = Field(
        default="medium",
        description="Investment horizon: 'short' (days), 'medium' (weeks), 'long' (months)"
    )


class InvestmentBriefOutput(BaseModel):
    token: str
    generated_at: str
    brief_markdown: str