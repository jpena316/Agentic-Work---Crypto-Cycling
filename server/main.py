import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from server.tools.market_data import get_market_data
from server.models.schemas import MarketDataInput

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