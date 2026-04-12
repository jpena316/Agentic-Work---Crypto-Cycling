"""
MCP Client Service
Calls our MCP server tools directly as Python functions.
Since the MCP server and FastAPI backend are in the same codebase,
we import the tool functions directly rather than going through
the MCP protocol — this is more efficient for same-process calls.
"""
from server.tools.market_data import get_market_data
from server.tools.technical import run_technical_analysis
from server.tools.news_sentiment import get_news_sentiment
from server.tools.brief_generator import generate_investment_brief
from server.models.schemas import (
    MarketDataOutput,
    TechnicalAnalysisOutput,
    NewsSentimentOutput,
    InvestmentBriefOutput,
)


async def fetch_market_data(token: str) -> MarketDataOutput:
    return await get_market_data(token)


async def fetch_technical_analysis(
    token: str,
    days: int = 30,
) -> TechnicalAnalysisOutput:
    return await run_technical_analysis(token, days)


async def fetch_news_sentiment(
    token: str,
    days: int = 7,
) -> NewsSentimentOutput:
    return await get_news_sentiment(token, days)


async def fetch_investment_brief(
    token: str,
    horizon: str = "medium",
) -> InvestmentBriefOutput:
    return await generate_investment_brief(token, horizon)