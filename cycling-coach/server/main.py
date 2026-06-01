"""MCP server entry point for the cycling-coach agent.

Exposes three tools that Claude can call dynamically:
  - run_coaching_session   Full four-agent pipeline
  - get_ride_summary       Lightweight Strava data check
  - get_bike_profiles      Returns all stored bike specs
"""

import asyncio
import json

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from server.tools.coaching_tools import (
    GetBikeProfilesInput,
    GetRideSummaryInput,
    RunCoachingSessionInput,
    get_bike_profiles,
    get_ride_summary,
    run_coaching_session,
)

app = Server("cycling-coach")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Advertise all available cycling-coach tools to the MCP client."""
    return [
        types.Tool(
            name="run_coaching_session",
            description=(
                "Run a complete AI coaching analysis using real Strava data. "
                "Analyzes recent rides, generates performance insights, creates a 7-day "
                "training plan, and ranks bikes under consideration by fit to the rider's "
                "profile. Takes 2-3 minutes to complete."
            ),
            inputSchema=RunCoachingSessionInput.model_json_schema(),
        ),
        types.Tool(
            name="get_ride_summary",
            description=(
                "Fetch a quick summary of recent Strava rides without "
                "running the full coaching pipeline. Returns ride count, total distance, "
                "elevation, and average duration."
            ),
            inputSchema=GetRideSummaryInput.model_json_schema(),
        ),
        types.Tool(
            name="get_bike_profiles",
            description=(
                "Return the stored bike profiles for all bikes under "
                "consideration. Shows specs, geometry, and characteristics for each bike."
            ),
            inputSchema=GetBikeProfilesInput.model_json_schema(),
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    """Dispatch an incoming tool call to the appropriate handler.

    Args:
        name: Tool name as advertised in :func:`list_tools`.
        arguments: Validated arguments dict from the MCP client.

    Returns:
        Single-element list with a TextContent block containing the JSON result.

    Raises:
        ValueError: If *name* does not match any registered tool.
    """
    if name == "run_coaching_session":
        result = await run_coaching_session(**arguments)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str),
        )]

    if name == "get_ride_summary":
        result = await get_ride_summary(**arguments)
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )]

    if name == "get_bike_profiles":
        result = await get_bike_profiles()
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str),
        )]

    raise ValueError(f"Unknown tool: {name}")


def main() -> None:
    """Synchronous entry point for pyproject.toml scripts."""
    asyncio.run(_run())


async def _run() -> None:
    """Start the MCP server on stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
