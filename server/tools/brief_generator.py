import httpx
from datetime import datetime, timezone
from anthropic import Anthropic
from server.config import settings
from server.models.schemas import (
    InvestmentBriefInput,
    InvestmentBriefOutput,
)
from server.tools.market_data import get_market_data
from server.tools.technical import run_technical_analysis
from server.tools.news_sentiment import get_news_sentiment
from pathlib import Path


PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "investment_brief.txt"

HORIZON_LABELS = {
    "short": "Short-term (days)",
    "medium": "Medium-term (weeks)",
    "long": "Long-term (months)",
}


async def generate_investment_brief(
    token: str,
    horizon: str = "medium",
) -> InvestmentBriefOutput:
    """
    Orchestrates all three data tools and calls Claude to generate
    a structured investment research brief for the given token.
    """
    validated = InvestmentBriefInput(token=token, horizon=horizon)
    coin_id = validated.token.lower().strip()
    horizon_label = HORIZON_LABELS.get(validated.horizon, "Medium-term (weeks)")

    # ── Step 1: Gather data from all three tools ──────────────
    market_data = await get_market_data(coin_id)
    technical = await run_technical_analysis(coin_id)
    sentiment = await get_news_sentiment(coin_id)

    # ── Step 2: Load and fill prompt template ─────────────────
    prompt_template = PROMPT_PATH.read_text()

    filled_prompt = prompt_template.format(
        token=coin_id,
        token_name=market_data.name,
        symbol=market_data.symbol,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        horizon=horizon_label,
        market_data=market_data.model_dump_json(indent=2),
        technical_analysis=technical.model_dump_json(indent=2),
        news_sentiment=sentiment.model_dump_json(indent=2),
    )

    # ── Step 3: Call Claude to synthesize the brief ───────────
    client = Anthropic(api_key=settings.anthropic_api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": filled_prompt,
            }
        ],
    )

    brief_markdown = message.content[0].text

    # ── Step 4: Return structured output ──────────────────────
    return InvestmentBriefOutput(
        token=coin_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        brief_markdown=brief_markdown,
    )