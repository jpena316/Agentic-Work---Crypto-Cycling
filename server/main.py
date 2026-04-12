import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from server.tools.market_data import get_market_data
from server.tools.technical import run_technical_analysis
from server.tools.news_sentiment import get_news_sentiment
from server.models.schemas import MarketDataInput, TechnicalAnalysisInput, NewsSentimentInput

app = Server("crypto-research-agent")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_market_data",
            description=(
                "Fetch live market data for a cryptocurrency from CoinGecko. "
                "Returns current price, market cap, 24h and 7d price changes, "
                "trading volume, circulating supply, and drawdown from ATH. "
                "Use the CoinGecko coin ID e.g. 'bitcoin', 'ethereum', 'solana'."
            ),
            inputSchema=MarketDataInput.model_json_schema(),
        ),
        types.Tool(
            name="run_technical_analysis",
            description=(
                "Run technical analysis on a cryptocurrency using 30-day OHLCV data. "
                "Returns SMA-7, SMA-30, RSI-14, volume trend, price trend, "
                "and support/resistance levels with plain English signal summaries. "
                "Use the CoinGecko coin ID e.g. 'bitcoin', 'ethereum', 'solana'."
            ),
            inputSchema=TechnicalAnalysisInput.model_json_schema(),
        ),
        types.Tool(
            name="get_news_sentiment",
            description=(
                "Fetch recent cryptocurrency news and compute sentiment analysis. "
                "Returns sentiment score from -1.0 (negative) to 1.0 (positive), "
                "sentiment breakdown, and top headlines for a given token. "
                "Use token name e.g. 'bitcoin', 'ethereum', 'solana'."
            ),
            inputSchema=NewsSentimentInput.model_json_schema(),
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:

    if name == "get_market_data":
        result = await get_market_data(**arguments)
        return [types.TextContent(
            type="text",
            text=result.model_dump_json(indent=2),
        )]

    if name == "run_technical_analysis":
        result = await run_technical_analysis(**arguments)
        return [types.TextContent(
            type="text",
            text=result.model_dump_json(indent=2),
        )]

    if name == "get_news_sentiment":
        result = await get_news_sentiment(**arguments)
        return [types.TextContent(
            type="text",
            text=result.model_dump_json(indent=2),
        )]

    raise ValueError(f"Unknown tool: {name}")


def main():
    asyncio.run(_run())


async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    main()