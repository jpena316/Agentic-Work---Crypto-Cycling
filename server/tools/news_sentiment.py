import httpx
from datetime import datetime, timedelta, timezone
from server.config import settings
from server.models.schemas import NewsSentimentInput, NewsSentimentOutput, NewsItem


# Keyword map for token name → search terms
TOKEN_KEYWORDS = {
    "bitcoin": "bitcoin OR BTC",
    "ethereum": "ethereum OR ETH",
    "solana": "solana OR SOL",
    "cardano": "cardano OR ADA",
    "ripple": "ripple OR XRP",
    "dogecoin": "dogecoin OR DOGE",
    "polkadot": "polkadot OR DOT",
    "avalanche-2": "avalanche OR AVAX",
    "chainlink": "chainlink OR LINK",
}

POSITIVE_WORDS = {
    "surge", "rally", "soar", "gain", "rise", "bull", "bullish", "breakout",
    "adoption", "partnership", "upgrade", "milestone", "record", "high",
    "growth", "strong", "positive", "boost", "recover", "outperform"
}

NEGATIVE_WORDS = {
    "crash", "drop", "fall", "plunge", "bear", "bearish", "hack", "exploit",
    "lawsuit", "ban", "regulation", "risk", "loss", "sell", "dump", "fear",
    "concern", "warning", "decline", "weak", "negative", "fraud", "scam"
}


def _score_headline(title: str) -> str:
    """Simple keyword-based sentiment scoring on a headline."""
    title_lower = title.lower()
    pos = sum(1 for word in POSITIVE_WORDS if word in title_lower)
    neg = sum(1 for word in NEGATIVE_WORDS if word in title_lower)

    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


async def get_news_sentiment(token: str, days: int = 7) -> NewsSentimentOutput:
    """
    Fetch recent crypto news for a token from NewsAPI and compute sentiment.
    Returns sentiment score, breakdown, and top headlines.
    """
    validated = NewsSentimentInput(token=token, days=days)
    token_lower = validated.token.lower().strip()
    lookback_days = validated.days

    # Build search query
    query = TOKEN_KEYWORDS.get(token_lower, token_lower)

    # Date range
    from_date = (
        datetime.now(timezone.utc) - timedelta(days=lookback_days)
    ).strftime("%Y-%m-%d")

    url = f"{settings.news_api_base_url}/everything"
    params = {
        "q": query,
        "from": from_date,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,
        "apiKey": settings.news_api_key,
    }

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    articles = data.get("articles", [])

    # Score each article
    scored = []
    for article in articles:
        title = article.get("title") or ""
        if not title or title == "[Removed]":
            continue
        sentiment = _score_headline(title)
        scored.append({
            "title": title,
            "source": article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "url": article.get("url", ""),
            "sentiment": sentiment,
        })

    # Aggregate sentiment
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for item in scored:
        counts[item["sentiment"]] += 1

    total = len(scored)
    if total > 0:
        sentiment_score = round(
            (counts["positive"] - counts["negative"]) / total, 2
        )
    else:
        sentiment_score = 0.0

    # Top 5 headlines
    top_headlines = [
        NewsItem(
            title=item["title"],
            source=item["source"],
            published_at=item["published_at"],
            url=item["url"],
            sentiment=item["sentiment"],
        )
        for item in scored[:5]
    ]

    return NewsSentimentOutput(
        token=token_lower,
        days_analyzed=lookback_days,
        total_articles=total,
        sentiment_breakdown=counts,
        sentiment_score=sentiment_score,
        top_headlines=top_headlines,
    )