"""Async scraper: fetch a manufacturer page and extract structured bike specs via Claude."""

import asyncio
import json
import logging
import re
from pathlib import Path

import anthropic
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).parent.parent / ".env"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 900
_TEXT_THRESHOLD = 500   # chars of visible text below which the page is treated as JS-rendered
_EXCERPT_CHARS = 5000   # max chars sent to Claude

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

logger = logging.getLogger(__name__)


async def fetch_bike_specs(url: str, bike_name: str) -> dict | None:
    """Fetch a manufacturer page and extract structured bike specs via Claude.

    Waits 2 seconds before each request to avoid rate-limiting manufacturer sites.
    Returns None (instead of raising) on any failure so callers can fall back
    to hardcoded specs gracefully.

    Args:
        url: Full manufacturer URL for this bike model.
        bike_name: Human-readable name used in the Claude extraction prompt.

    Returns:
        Spec dict matching the data/bikes/ JSON template, or None on failure.
    """
    await asyncio.sleep(2)

    logger.info("Fetching specs for '%s' from %s", bike_name, url)
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        logger.warning("HTTP fetch failed for '%s': %s", bike_name, exc)
        return None

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    visible_text = soup.get_text(separator=" ", strip=True)

    if len(visible_text) < _TEXT_THRESHOLD:
        logger.warning(
            "'%s' returned only %d chars of text — JS-rendered page, skipping scrape",
            bike_name, len(visible_text),
        )
        return None

    excerpt = visible_text[:_EXCERPT_CHARS]
    logger.info("Extracted %d chars; sending to Claude for spec extraction", len(excerpt))

    try:
        return _extract_with_claude(excerpt, bike_name, url)
    except Exception as exc:
        logger.warning("Claude extraction failed for '%s': %s", bike_name, exc)
        return None


def _extract_with_claude(text: str, bike_name: str, url: str) -> dict | None:
    """Ask Claude to extract structured specs from visible page text.

    Args:
        text: Stripped visible text from the manufacturer page.
        bike_name: Human-readable model name for the prompt.
        url: Original URL, stored in the returned spec dict.

    Returns:
        Parsed spec dict, or None if Claude returns unparseable content.
    """
    load_dotenv(_ENV_PATH, override=True)
    client = anthropic.Anthropic()

    prompt = (
        f"Extract bicycle specifications for the model '{bike_name}' from the webpage text below.\n\n"
        "Return a JSON object with exactly these fields:\n"
        '{\n'
        '  "name": "<full model name as sold>",\n'
        '  "brand": "<manufacturer brand name>",\n'
        '  "model": "<model line name>",\n'
        '  "category": "<one of: aero road | endurance road | all-around road | climbing road>",\n'
        '  "price_usd": <retail price as a number, or 0 if not found>,\n'
        '  "weight_kg": <complete bike weight as a number, or 0 if not found>,\n'
        '  "geometry": {\n'
        '    "stack": <mm for size 56 or nearest, or 0>,\n'
        '    "reach": <mm for size 56 or nearest, or 0>,\n'
        '    "head_tube_angle": <degrees or 0>,\n'
        '    "bb_drop": <mm or 0>\n'
        '  },\n'
        '  "components": {\n'
        '    "groupset": "<e.g. Shimano Ultegra Di2>",\n'
        '    "drivetrain": "<e.g. 12-speed>",\n'
        '    "brakes": "<hydraulic disc or rim>",\n'
        '    "wheelset": "<brand and model or generic description>"\n'
        '  },\n'
        '  "intended_use": ["<use1>", "<use2>"],\n'
        '  "terrain_fit": ["<flat>" and/or "<rolling>" and/or "<climbing>" and/or "<mixed>"],\n'
        '  "key_characteristics": ["<3 to 5 short bullet points about what makes this bike distinctive>"],\n'
        f'  "source_url": "{url}"\n'
        '}\n\n'
        f"Webpage text:\n{text}"
    )

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=(
            "You are a bicycle specification extractor. "
            "Respond with valid JSON only. No preamble, no explanation, no markdown fences."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    if not message.content:
        return None

    raw = message.content[0].text.strip()
    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw)
    if fenced:
        raw = fenced.group(1).strip()

    result = json.loads(raw)
    return result if isinstance(result, dict) else None
