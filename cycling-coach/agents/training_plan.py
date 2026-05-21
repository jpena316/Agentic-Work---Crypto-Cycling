"""Agent 3 — Training Plan: generates a structured 7-day plan via Claude."""

import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from tools.validators import validate_training_plan

_ENV_PATH = Path(__file__).parent.parent / ".env"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "training_plan.txt"
_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 2000
_REQUIRED_KEYS = {"week_focus", "tss_target", "days", "coaching_notes"}
_DAY_REQUIRED_KEYS = {"day", "workout_type", "duration_mins", "intensity", "description", "rationale"}


class TrainingPlanAgent(BaseAgent):
    """Calls Claude to produce a validated 7-day training plan."""

    async def run(self, context: dict) -> dict:
        """Read analysis and metrics from context, call Claude, store the plan.

        Reads:
            context["performance_analysis"]  — written by PerformanceAnalysisAgent
            context["computed_metrics"]      — written by DataRetrievalAgent
            context["athlete_profile"]       — written by DataRetrievalAgent
            context["athlete_goals"]         — set by create_context()

        Writes:
            context["training_plan"]  — validated 7-day plan dict from Claude

        Args:
            context: Shared pipeline state.

        Returns:
            Updated context dict.
        """
        analysis: dict = context.get("performance_analysis") or {}
        metrics: dict = context.get("computed_metrics") or {}
        profile: dict = context.get("athlete_profile") or {}
        goals: list[str] = context.get("athlete_goals") or []

        if not analysis:
            self._add_error(context, "Training plan skipped: performance_analysis is empty.")
            context["training_plan"] = None
            return context

        self.logger.info("Building training plan prompt...")
        try:
            prompt = _build_prompt(analysis, metrics, profile, goals)
        except Exception as exc:
            self._add_error(context, f"Failed to build training plan prompt: {exc}")
            context["training_plan"] = None
            return context

        self.logger.info("Calling Claude (%s, max_tokens=%d)...", _MODEL, _MAX_TOKENS)
        try:
            raw_response = _call_claude(prompt)
        except Exception as exc:
            self._add_error(context, f"Claude API call failed: {exc}")
            context["training_plan"] = None
            return context

        self.logger.info("Parsing Claude response...")
        try:
            plan = _parse_json(raw_response)
        except (json.JSONDecodeError, ValueError) as exc:
            self._add_error(context, f"Failed to parse training plan JSON: {exc}")
            self.logger.debug("Raw Claude response:\n%s", raw_response)
            context["training_plan"] = None
            return context

        missing = _REQUIRED_KEYS - plan.keys()
        if missing:
            self._add_error(
                context,
                f"Training plan missing required keys: {sorted(missing)}",
            )
            context["training_plan"] = None
            return context

        violations = validate_training_plan(plan)
        for violation in violations:
            self._add_error(context, f"Training plan violation: {violation}")

        context["training_plan"] = plan
        self.logger.info(
            "Training plan complete — focus=%r, tss_target=%s, violations=%d",
            plan.get("week_focus"),
            plan.get("tss_target"),
            len(violations),
        )
        return context


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _build_prompt(
    analysis: dict,
    metrics: dict,
    profile: dict,
    goals: list[str],
) -> str:
    """Load the prompt template and substitute all placeholders.

    Uses plain string replacement rather than str.format() so the template
    can safely contain braces (e.g. in JSON examples).

    Args:
        analysis: Structured performance analysis from PerformanceAnalysisAgent.
        metrics: Computed training metrics from DataRetrievalAgent.
        profile: Athlete profile dict from Strava.
        goals: List of athlete goal strings.

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

    strengths: list[str] = analysis.get("strengths") or []
    weaknesses: list[str] = analysis.get("weaknesses") or []

    substitutions = {
        "{athlete_name}":           f"{firstname} {lastname}".strip() or "Athlete",
        "{ftp_display}":            f"{ftp} W" if ftp else "Not set",
        "{weight_display}":         f"{weight} kg" if weight else "Not set",
        "{goals_display}":          "\n  ".join(goals) if goals else "Not specified",
        "{fatigue_level}":          analysis.get("fatigue_level", "unknown"),
        "{overtraining_risk}":      analysis.get("overtraining_risk", "unknown"),
        "{fitness_trend}":          analysis.get("fitness_trend", "unknown"),
        "{strengths_display}":      "; ".join(strengths) if strengths else "Not identified",
        "{weaknesses_display}":     "; ".join(weaknesses) if weaknesses else "Not identified",
        "{recommended_focus}":      analysis.get("recommended_focus", "Not specified"),
        "{weekly_tss}":             str(metrics.get("weekly_tss", 0.0)),
        "{six_week_tss}":           str(metrics.get("six_week_tss", 0.0)),
        "{total_rides}":            str(metrics.get("total_rides", 0)),
        "{avg_ride_duration_mins}": str(metrics.get("avg_ride_duration_mins", 0.0)),
        "{power_data_available}":   "true" if has_power else "false",
        "{avg_power_display}":      f"{avg_power} W" if avg_power is not None else "N/A",
        "{avg_hr_display}":         f"{avg_hr} bpm" if avg_hr is not None else "N/A",
    }

    for placeholder, value in substitutions.items():
        template = template.replace(placeholder, value)

    return template


def _call_claude(prompt: str) -> str:
    """Send *prompt* to Claude and return the raw text response.

    Args:
        prompt: Fully rendered training plan prompt.

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

    fenced = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if fenced:
        text = fenced.group(1).strip()

    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object, got {type(result).__name__}")
    return result
