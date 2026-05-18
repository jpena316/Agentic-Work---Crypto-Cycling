"""Agent 2 — Performance Analysis: interprets training metrics via Claude."""

import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from agents.base_agent import BaseAgent

_ENV_PATH = Path(__file__).parent.parent / ".env"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "performance_analysis.txt"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 1500
_REQUIRED_KEYS = {
    "strengths",
    "weaknesses",
    "fatigue_level",
    "overtraining_risk",
    "fitness_trend",
    "key_observations",
    "recommended_focus",
}


class PerformanceAnalysisAgent(BaseAgent):
    """Calls Claude to interpret computed_metrics and produce structured analysis."""

    async def run(self, context: dict) -> dict:
        """Read metrics from context, call Claude, store structured analysis.

        Reads:
            context["computed_metrics"]  — written by DataRetrievalAgent
            context["athlete_profile"]   — written by DataRetrievalAgent
            context["athlete_goals"]     — set by create_context()

        Writes:
            context["performance_analysis"]  — parsed JSON dict from Claude

        Args:
            context: Shared pipeline state.

        Returns:
            Updated context dict.
        """
        metrics: dict = context.get("computed_metrics") or {}
        profile: dict = context.get("athlete_profile") or {}
        goals: list[str] = context.get("athlete_goals") or []

        if not metrics:
            self._add_error(context, "Performance analysis skipped: computed_metrics is empty.")
            context["performance_analysis"] = None
            return context

        # ------------------------------------------------------------------
        # Build prompt
        # ------------------------------------------------------------------
        self.logger.info("Building performance analysis prompt...")
        try:
            prompt = _build_prompt(metrics, profile, goals)
        except Exception as exc:
            self._add_error(context, f"Failed to build prompt: {exc}")
            context["performance_analysis"] = None
            return context

        # ------------------------------------------------------------------
        # Call Claude
        # ------------------------------------------------------------------
        self.logger.info("Calling Claude (%s, max_tokens=%d)...", _MODEL, _MAX_TOKENS)
        try:
            raw_response = _call_claude(prompt)
        except Exception as exc:
            self._add_error(context, f"Claude API call failed: {exc}")
            context["performance_analysis"] = None
            return context

        # ------------------------------------------------------------------
        # Parse and validate JSON
        # ------------------------------------------------------------------
        self.logger.info("Parsing Claude response...")
        try:
            analysis = _parse_json(raw_response)
        except (json.JSONDecodeError, ValueError) as exc:
            self._add_error(context, f"Failed to parse Claude response as JSON: {exc}")
            self.logger.debug("Raw Claude response:\n%s", raw_response)
            context["performance_analysis"] = None
            return context

        missing = _REQUIRED_KEYS - analysis.keys()
        if missing:
            self._add_error(
                context,
                f"Claude response missing required keys: {sorted(missing)}",
            )
            context["performance_analysis"] = None
            return context

        context["performance_analysis"] = analysis
        self.logger.info(
            "Analysis complete — fatigue=%s, overtraining_risk=%s, trend=%s",
            analysis.get("fatigue_level"),
            analysis.get("overtraining_risk"),
            analysis.get("fitness_trend"),
        )
        return context


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _build_prompt(metrics: dict, profile: dict, goals: list[str]) -> str:
    """Load the prompt template and substitute all metric placeholders.

    Uses plain string replacement rather than str.format() so that the
    template can safely contain braces (e.g. in JSON examples) without
    needing to escape them.

    Args:
        metrics: Computed training metrics from DataRetrievalAgent.
        profile: Athlete profile dict from Strava.
        goals: List of athlete goal strings from context.

    Returns:
        Fully rendered prompt string ready to send to Claude.
    """
    template = _PROMPT_PATH.read_text()

    has_power = (metrics.get("rides_with_power") or 0) > 0
    avg_power = metrics.get("avg_power")
    avg_hr = metrics.get("avg_heart_rate")
    ftp = profile.get("ftp")
    weight = profile.get("weight")
    firstname = profile.get("firstname", "")
    lastname = profile.get("lastname", "")

    substitutions = {
        "{athlete_name}":           f"{firstname} {lastname}".strip() or "Athlete",
        "{ftp_display}":            f"{ftp} W" if ftp else "Not set",
        "{weight_display}":         f"{weight} kg" if weight else "Not set",
        "{goals_display}":          "\n  ".join(goals) if goals else "Not specified",
        "{total_rides}":            str(metrics.get("total_rides", 0)),
        "{total_distance_km}":      str(metrics.get("total_distance_km", 0.0)),
        "{total_elevation_m}":      str(metrics.get("total_elevation_m", 0.0)),
        "{avg_ride_duration_mins}": str(metrics.get("avg_ride_duration_mins", 0.0)),
        "{longest_ride_km}":        str(metrics.get("longest_ride_km", 0.0)),
        "{weekly_tss}":             str(metrics.get("weekly_tss", 0.0)),
        "{six_week_tss}":           str(metrics.get("six_week_tss", 0.0)),
        "{fitness_trend}":          str(metrics.get("fitness_trend", "unknown")),
        "{power_data_available}":   "true" if has_power else "false",
        "{rides_with_power}":       str(metrics.get("rides_with_power", 0)),
        "{avg_power_display}":      f"{avg_power} W" if avg_power is not None else "N/A",
        "{avg_hr_display}":         f"{avg_hr} bpm" if avg_hr is not None else "N/A",
    }

    for placeholder, value in substitutions.items():
        template = template.replace(placeholder, value)

    return template


def _call_claude(prompt: str) -> str:
    """Send *prompt* to Claude and return the raw text response.

    Loads ANTHROPIC_API_KEY from .env before constructing the client so the
    key is always fresh (important after token refreshes on the same process).

    Args:
        prompt: Fully rendered performance analysis prompt.

    Returns:
        Raw text content from Claude's first response block.

    Raises:
        anthropic.APIError: On any Anthropic API error.
        RuntimeError: If the response contains no text content.
    """
    load_dotenv(_ENV_PATH, override=True)
    client = anthropic.Anthropic()

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=(
            "You are an expert cycling coach. "
            "Respond with valid JSON only. "
            "No preamble, no explanation, no markdown fences."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    if not message.content:
        raise RuntimeError("Claude returned an empty response.")

    return message.content[0].text


def _parse_json(raw: str) -> dict:
    """Strip optional markdown fences and parse JSON from Claude's response.

    Args:
        raw: Raw text returned by Claude.

    Returns:
        Parsed dict.

    Raises:
        json.JSONDecodeError: If the text cannot be parsed as JSON after cleaning.
        ValueError: If the parsed value is not a dict.
    """
    text = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if Claude added them anyway
    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if fenced:
        text = fenced.group(1).strip()

    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object, got {type(result).__name__}")
    return result
