"""Agent 4 — Bike Recommender: scrapes specs, builds rider signature, ranks bikes via Claude."""

import json
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from agents.base_agent import BaseAgent
from tools.scraper import fetch_bike_specs

_ENV_PATH = Path(__file__).parent.parent / ".env"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bike_recommendation.txt"
_BIKES_DIR = Path(__file__).parent.parent / "data" / "bikes"
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 4000

BIKE_URLS: dict[str, str] = {
    "trek_madone_slr7_gen8": (
        "https://www.trekbikes.com/us/en_US/bikes/road-bikes/performance-road-bikes"
        "/madone/f/F213/madone-slr-7-gen-8/46687/5339086"
    ),
    "cervelo_caledonia": "https://www.cervelo.com/en-US/bikes/caledonia",
    "cervelo_soloist": "https://www.cervelo.com/en-US/bikes/soloist",
    "specialized_tarmac_sl8": (
        "https://www.specialized.com/us/en/tarmac-sl8-expert-sram-force-axs-/p/4293510"
    ),
    "canyon_aeroad_cf_slx8": (
        "https://www.canyon.com/en-us/road-bikes/aero-bikes/aeroad/cf-slx"
        "/aeroad-cf-slx-8-axs-speed/4536.html"
    ),
    "canyon_endurace_cf_slx8": (
        "https://www.canyon.com/en-us/road-bikes/endurance-bikes/endurace/cf-slx"
        "/endurace-cf-slx-8-di2/4432.html"
    ),
    "canyon_endurace_cf_slx7": (
        "https://www.canyon.com/en-us/road-bikes/endurance-bikes/endurace/cf-slx"
        "/endurace-cf-slx-7-axs/4431.html"
    ),
    "factor_monza": "https://factorbikes.com/bike-builder/monza-shimano-ultegra",
}

_FALLBACK_SPECS: dict[str, dict] = {
    "trek_madone_slr7_gen8": {
        "name": "Trek Madone SLR 7 Gen 8",
        "brand": "Trek",
        "model": "Madone SLR 7 Gen 8",
        "category": "aero road",
        "price_usd": 7499,
        "weight_kg": 7.1,
        "geometry": {"stack": 530, "reach": 377, "head_tube_angle": 73.5, "bb_drop": 73},
        "components": {
            "groupset": "Shimano Ultegra Di2",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "Bontrager Aeolus Pro 37 carbon",
        },
        "intended_use": ["racing", "fast group rides"],
        "terrain_fit": ["flat", "rolling"],
        "key_characteristics": [
            "Kammtail Virtual Foil aerodynamic tube shaping",
            "IsoSpeed decoupler for rear-end compliance without sacrificing stiffness",
            "Integrated cockpit for aerodynamic advantage and clean lines",
            "Race geometry suited to aggressive riders seeking aerodynamic efficiency",
            "Best-in-class aero credentials validated in professional racing",
        ],
        "source_url": BIKE_URLS["trek_madone_slr7_gen8"],
    },
    "cervelo_caledonia": {
        "name": "Cervélo Caledonia 5",
        "brand": "Cervélo",
        "model": "Caledonia 5",
        "category": "endurance road",
        "price_usd": 6499,
        "weight_kg": 7.8,
        "geometry": {"stack": 565, "reach": 382, "head_tube_angle": 72.0, "bb_drop": 75},
        "components": {
            "groupset": "SRAM Force eTap AXS",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "DT Swiss ARC 1100 Dicut 48",
        },
        "intended_use": ["gran fondo", "endurance training", "all-road"],
        "terrain_fit": ["rolling", "mixed", "climbing"],
        "key_characteristics": [
            "SMP geometry balances efficiency and long-ride comfort",
            "Wide tire clearance up to 35mm for mixed-surface capability",
            "Compliance-focused layup reduces road vibration on long efforts",
            "Versatile all-road design suits cyclists who ride varied terrain",
            "More relaxed geometry than Cervélo's race models for all-day riding",
        ],
        "source_url": BIKE_URLS["cervelo_caledonia"],
    },
    "cervelo_soloist": {
        "name": "Cervélo Soloist",
        "brand": "Cervélo",
        "model": "Soloist",
        "category": "aero road",
        "price_usd": 6999,
        "weight_kg": 7.3,
        "geometry": {"stack": 535, "reach": 380, "head_tube_angle": 73.0, "bb_drop": 74},
        "components": {
            "groupset": "SRAM Force eTap AXS",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "Zipp 303 S carbon",
        },
        "intended_use": ["racing", "fast training rides"],
        "terrain_fit": ["flat", "rolling"],
        "key_characteristics": [
            "Aerodynamic tube shapes derived from Cervélo's S-Series race bikes",
            "Disc brakes and wider tire clearance vs. previous generation",
            "Balanced between full aero and all-day compliance",
            "Race-oriented geometry with slightly more stack than pure aero competitors",
            "Boutique finish quality and frameset stiffness at a competitive price",
        ],
        "source_url": BIKE_URLS["cervelo_soloist"],
    },
    "specialized_tarmac_sl8": {
        "name": "Specialized Tarmac SL8 Expert",
        "brand": "Specialized",
        "model": "Tarmac SL8",
        "category": "all-around road",
        "price_usd": 5750,
        "weight_kg": 6.9,
        "geometry": {"stack": 532, "reach": 382, "head_tube_angle": 73.5, "bb_drop": 72},
        "components": {
            "groupset": "SRAM Force eTap AXS",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "Roval Rapide CLX 50",
        },
        "intended_use": ["racing", "climbing", "all-around performance"],
        "terrain_fit": ["flat", "rolling", "climbing"],
        "key_characteristics": [
            "Lightest complete bike in its price class at 6.9 kg",
            "Best aerodynamic efficiency of any lightweight all-rounder",
            "Rider-First Engineered for consistent performance across all frame sizes",
            "Race geometry suits aggressive riders who want a single bike for all conditions",
            "Integrated Future Shock 2.0 damper option available for rough roads",
        ],
        "source_url": BIKE_URLS["specialized_tarmac_sl8"],
    },
    "canyon_aeroad_cf_slx8": {
        "name": "Canyon Aeroad CF SLX 8 AXS Speed",
        "brand": "Canyon",
        "model": "Aeroad CF SLX 8",
        "category": "aero road",
        "price_usd": 5499,
        "weight_kg": 7.5,
        "geometry": {"stack": 528, "reach": 378, "head_tube_angle": 73.5, "bb_drop": 73},
        "components": {
            "groupset": "SRAM Force eTap AXS",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "DT Swiss ARC 1400 Dicut 50",
        },
        "intended_use": ["racing", "fast group rides", "criteriums"],
        "terrain_fit": ["flat", "rolling"],
        "key_characteristics": [
            "Wind-tunnel-validated aerodynamic frame at a direct-to-consumer price advantage",
            "Integrated CFR cockpit eliminates drag and cleans up the front end",
            "Stiff bottom bracket area for efficient power transfer under hard efforts",
            "Race geometry optimized for riders seeking aerodynamic speed on flat to rolling terrain",
            "Best value aero road bike in the sub-$6,000 category",
        ],
        "source_url": BIKE_URLS["canyon_aeroad_cf_slx8"],
    },
    "canyon_endurace_cf_slx8": {
        "name": "Canyon Endurace CF SLX 8 Di2",
        "brand": "Canyon",
        "model": "Endurace CF SLX 8",
        "category": "endurance road",
        "price_usd": 4999,
        "weight_kg": 7.9,
        "geometry": {"stack": 568, "reach": 375, "head_tube_angle": 71.5, "bb_drop": 76},
        "components": {
            "groupset": "Shimano Ultegra Di2",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "DT Swiss R 470 DB alloy",
        },
        "intended_use": ["gran fondo", "endurance training", "long-distance"],
        "terrain_fit": ["rolling", "climbing", "mixed"],
        "key_characteristics": [
            "VCLS 2.0 leaf-spring seatpost absorbs road vibration for all-day comfort",
            "Progressive endurance geometry with high stack for upright, fatigue-reducing position",
            "30mm tire clearance for wider tires on rough roads",
            "Shimano Ultegra Di2 delivers reliable electronic shifting at a value price",
            "Best-in-class compliance for riders prioritizing comfort over outright speed",
        ],
        "source_url": BIKE_URLS["canyon_endurace_cf_slx8"],
    },
    "canyon_endurace_cf_slx7": {
        "name": "Canyon Endurace CF SLX 7 AXS",
        "brand": "Canyon",
        "model": "Endurace CF SLX 7",
        "category": "endurance road",
        "price_usd": 3999,
        "weight_kg": 8.2,
        "geometry": {"stack": 568, "reach": 375, "head_tube_angle": 71.5, "bb_drop": 76},
        "components": {
            "groupset": "SRAM Rival eTap AXS",
            "drivetrain": "12-speed",
            "brakes": "hydraulic disc",
            "wheelset": "DT Swiss R 470 DB alloy",
        },
        "intended_use": ["endurance training", "gran fondo", "recreational road riding"],
        "terrain_fit": ["rolling", "mixed", "climbing"],
        "key_characteristics": [
            "Same comfort-focused Endurace CF SLX frame as the SLX 8 at a lower price",
            "VCLS 2.0 seatpost and endurance geometry for long-ride comfort",
            "SRAM Rival eTap AXS wireless shifting — excellent entry point to wireless groupsets",
            "Wide tire clearance and relaxed geometry suit riders new to road cycling",
            "Best-value endurance carbon bike in the Canyon lineup",
        ],
        "source_url": BIKE_URLS["canyon_endurace_cf_slx7"],
    },
    "factor_monza": {
        "name": "Factor Monza Shimano Ultegra",
        "brand": "Factor",
        "model": "Monza",
        "category": "aero road",
        "price_usd": 5299,
        "weight_kg": 7.2,
        "geometry": {"stack": 527, "reach": 379, "head_tube_angle": 73.5, "bb_drop": 73},
        "components": {
            "groupset": "Shimano Ultegra R8000",
            "drivetrain": "11-speed",
            "brakes": "hydraulic disc",
            "wheelset": "Factor-branded alloy with carbon option",
        },
        "intended_use": ["racing", "fast training rides"],
        "terrain_fit": ["flat", "rolling"],
        "key_characteristics": [
            "Boutique brand with monocoque carbon construction for a stiff, light aero frame",
            "Distinctive integrated cable routing and aerodynamic tube shaping",
            "Stiffer bottom bracket than many competitors for direct power transfer",
            "Race-aggressive geometry positions riders for aerodynamic efficiency",
            "Differentiated aesthetics appeal to riders who want to stand out from mainstream brands",
        ],
        "source_url": BIKE_URLS["factor_monza"],
    },
}

_REQUIRED_KEYS = {"ranked", "match_scores", "rationale", "best_overall", "summary"}


class BikeRecommenderAgent(BaseAgent):
    """Loads bike specs, builds rider signature, calls Claude for ranked recommendations."""

    async def run(self, context: dict) -> dict:
        """Load/scrape bike specs, infer rider signature, call Claude, store recommendations.

        Reads:
            context["computed_metrics"]     — from DataRetrievalAgent
            context["athlete_profile"]      — from DataRetrievalAgent
            context["athlete_goals"]        — from create_context()
            context["performance_analysis"] — from PerformanceAnalysisAgent
            context["training_plan"]        — from TrainingPlanAgent

        Writes:
            context["bike_profiles"]        — list of loaded/scraped spec dicts
            context["rider_signature"]      — inferred rider profile dict
            context["bike_recommendations"] — ranked recommendation dict from Claude

        Args:
            context: Shared pipeline state.

        Returns:
            Updated context dict.
        """
        # ------------------------------------------------------------------
        # Step 1: load bike JSON files; scrape or fall back for empty ones
        # ------------------------------------------------------------------
        bike_profiles = await self._load_bike_profiles(context)
        context["bike_profiles"] = bike_profiles

        if not bike_profiles:
            self._add_error(context, "No bike profiles available — skipping recommendations.")
            context["bike_recommendations"] = None
            return context

        # ------------------------------------------------------------------
        # Step 2: build rider signature
        # ------------------------------------------------------------------
        rider_signature = _build_rider_signature(context)
        context["rider_signature"] = rider_signature
        self.logger.info(
            "Rider signature — terrain=%s, style=%s, fitness=%s",
            rider_signature["dominant_terrain"],
            rider_signature["riding_style"],
            rider_signature["fitness_level"],
        )

        # ------------------------------------------------------------------
        # Step 3: call Claude for ranked recommendations
        # ------------------------------------------------------------------
        self.logger.info(
            "Calling Claude to rank %d bikes (%s, max_tokens=%d)...",
            len(bike_profiles), _MODEL, _MAX_TOKENS,
        )
        try:
            prompt = _build_prompt(rider_signature, bike_profiles)
            raw_response = _call_claude(prompt)
        except Exception as exc:
            self._add_error(context, f"Claude API call failed: {exc}")
            context["bike_recommendations"] = None
            return context

        # ------------------------------------------------------------------
        # Step 4: parse and validate response
        # ------------------------------------------------------------------
        try:
            recommendations = _parse_json(raw_response)
        except (json.JSONDecodeError, ValueError) as exc:
            self._add_error(context, f"Failed to parse bike recommendations JSON: {exc}")
            self.logger.debug("Raw Claude response:\n%s", raw_response)
            context["bike_recommendations"] = None
            return context

        missing = _REQUIRED_KEYS - recommendations.keys()
        if missing:
            self._add_error(
                context,
                f"Bike recommendations missing required keys: {sorted(missing)}",
            )
            context["bike_recommendations"] = None
            return context

        ranked: list[str] = recommendations.get("ranked") or []
        match_scores: dict = recommendations.get("match_scores") or {}
        unscored = [name for name in ranked if name not in match_scores]
        if unscored:
            self._add_error(
                context,
                f"match_scores missing entries for ranked bikes: {unscored}",
            )
            context["bike_recommendations"] = None
            return context

        context["bike_recommendations"] = recommendations
        self.logger.info(
            "Recommendations complete — best_overall=%r, top_score=%s, ranked=%s",
            recommendations.get("best_overall"),
            match_scores.get(recommendations.get("best_overall")),
            ranked,
        )
        return context

    async def _load_bike_profiles(self, context: dict) -> list[dict]:
        """Load each bike JSON; scrape or use fallback if the file is empty.

        Args:
            context: Shared pipeline state (used for error reporting).

        Returns:
            List of resolved spec dicts ready for use in the recommendation prompt.
        """
        profiles: list[dict] = []

        for json_file in sorted(_BIKES_DIR.glob("*.json")):
            key = json_file.stem
            try:
                with open(json_file) as fh:
                    spec = json.load(fh)
            except Exception as exc:
                self._add_error(context, f"Failed to load {json_file.name}: {exc}")
                continue

            if not _is_empty(spec):
                profiles.append(spec)
                self.logger.info("Loaded pre-filled specs for %s", key)
                continue

            # File is empty — try scraping first
            url = BIKE_URLS.get(key)
            scraped: dict | None = None
            if url:
                self.logger.info("Attempting to scrape specs for %s...", key)
                try:
                    scraped = await fetch_bike_specs(url, key.replace("_", " ").title())
                except Exception as exc:
                    self.logger.warning("Scrape error for %s: %s", key, exc)

            if scraped:
                profiles.append(scraped)
                self.logger.info("Used scraped specs for %s", key)
                continue

            # Scrape failed or returned None — use hardcoded fallback
            fallback = _FALLBACK_SPECS.get(key)
            if fallback:
                profiles.append(fallback)
                self.logger.info("Using hardcoded fallback specs for %s", key)
            else:
                self._add_error(context, f"No specs available for {key}, skipping.")

        return profiles


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _is_empty(spec: dict) -> bool:
    """Return True when a bike JSON file hasn't been filled in yet."""
    return not spec.get("name")


def _build_rider_signature(context: dict) -> dict:
    """Infer a structured rider profile from context data.

    Args:
        context: Shared pipeline state containing metrics, goals, and plan.

    Returns:
        Rider signature dict with terrain, style, fitness, goals, and stats.
    """
    metrics: dict = context.get("computed_metrics") or {}
    goals: list[str] = context.get("athlete_goals") or []
    training_plan: dict = context.get("training_plan") or {}
    profile: dict = context.get("athlete_profile") or {}

    total_elevation = metrics.get("total_elevation_m", 0.0)
    total_distance = metrics.get("total_distance_km", 0.0) or 1.0
    elevation_per_km = total_elevation / total_distance

    if elevation_per_km > 15:
        dominant_terrain = "climbing"
    elif elevation_per_km > 8:
        dominant_terrain = "mixed/rolling"
    else:
        dominant_terrain = "flat/fast"

    avg_duration = metrics.get("avg_ride_duration_mins", 0.0)
    total_rides = metrics.get("total_rides", 0)
    rides_per_week = total_rides / 6.4  # 45-day window

    if avg_duration > 120 and rides_per_week < 4:
        riding_style = "gran fondo / endurance"
    elif avg_duration < 60 and rides_per_week >= 4:
        riding_style = "frequent short rides / criterium-style"
    else:
        riding_style = "all-around road cycling"

    weekly_tss = metrics.get("weekly_tss", 0.0)
    if weekly_tss > 400:
        fitness_level = "advanced"
    elif weekly_tss > 200:
        fitness_level = "intermediate"
    else:
        fitness_level = "beginner / recreational"

    return {
        "dominant_terrain": dominant_terrain,
        "riding_style": riding_style,
        "fitness_level": fitness_level,
        "goals": goals,
        "training_focus": training_plan.get("week_focus", "Not specified"),
        "ftp": profile.get("ftp"),
        "weight_kg": profile.get("weight"),
        "avg_ride_duration_mins": round(avg_duration, 1),
        "rides_per_week": round(rides_per_week, 1),
        "elevation_per_km": round(elevation_per_km, 1),
        "weekly_tss": weekly_tss,
        "fitness_trend": metrics.get("fitness_trend", "unknown"),
    }


def _build_prompt(rider_signature: dict, bike_profiles: list[dict]) -> str:
    """Render the bike recommendation prompt with rider and bike data injected.

    Args:
        rider_signature: Rider profile dict from _build_rider_signature.
        bike_profiles: List of resolved spec dicts for all bikes.

    Returns:
        Fully rendered prompt string ready to send to Claude.
    """
    template = _PROMPT_PATH.read_text()

    goals_text = (
        "\n  ".join(rider_signature["goals"]) if rider_signature["goals"] else "Not specified"
    )
    ftp_text = f"{rider_signature['ftp']} W" if rider_signature.get("ftp") else "Not set"
    weight_text = (
        f"{rider_signature['weight_kg']} kg" if rider_signature.get("weight_kg") else "Not set"
    )

    rider_lines = [
        f"Dominant terrain:      {rider_signature['dominant_terrain']}",
        f"Riding style:          {rider_signature['riding_style']}",
        f"Fitness level:         {rider_signature['fitness_level']}",
        f"Weekly TSS:            {rider_signature['weekly_tss']}",
        f"Fitness trend:         {rider_signature['fitness_trend']}",
        f"Avg ride duration:     {rider_signature['avg_ride_duration_mins']} min",
        f"Rides per week:        {rider_signature['rides_per_week']}",
        f"Elevation per km:      {rider_signature['elevation_per_km']} m/km",
        f"FTP:                   {ftp_text}",
        f"Weight:                {weight_text}",
        f"Training focus:        {rider_signature['training_focus']}",
        f"Goals:\n  {goals_text}",
    ]
    rider_profile_text = "\n".join(rider_lines)

    bike_blocks: list[str] = []
    for i, bike in enumerate(bike_profiles, 1):
        comps = bike.get("components", {})
        geo = bike.get("geometry", {})
        chars = bike.get("key_characteristics", [])
        block = (
            f"Bike {i}: {bike.get('name', 'Unknown')}\n"
            f"  Category:        {bike.get('category', 'N/A')}\n"
            f"  Price:           ${bike.get('price_usd', 0):,}\n"
            f"  Weight:          {bike.get('weight_kg', 0)} kg\n"
            f"  Groupset:        {comps.get('groupset', 'N/A')}\n"
            f"  Drivetrain:      {comps.get('drivetrain', 'N/A')}\n"
            f"  Brakes:          {comps.get('brakes', 'N/A')}\n"
            f"  Wheelset:        {comps.get('wheelset', 'N/A')}\n"
            f"  Stack/Reach:     {geo.get('stack', 0)} mm / {geo.get('reach', 0)} mm\n"
            f"  Intended use:    {', '.join(bike.get('intended_use', []))}\n"
            f"  Terrain fit:     {', '.join(bike.get('terrain_fit', []))}\n"
            f"  Key characteristics:\n"
            + "\n".join(f"    - {c}" for c in chars)
        )
        bike_blocks.append(block)
    bike_profiles_text = "\n\n".join(bike_blocks)

    return (
        template
        .replace("{rider_profile_text}", rider_profile_text)
        .replace("{bike_profiles_text}", bike_profiles_text)
    )


def _call_claude(prompt: str) -> str:
    """Send *prompt* to Claude and return the raw text response.

    Args:
        prompt: Fully rendered bike recommendation prompt.

    Returns:
        Raw text from Claude's first response block.

    Raises:
        anthropic.APIError: On any Anthropic API error.
        RuntimeError: If the response contains no text content.
    """
    load_dotenv(_ENV_PATH, override=True)
    client = anthropic.Anthropic()

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system="Respond with valid JSON only. No preamble, no markdown fences, no explanation.",
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
        json.JSONDecodeError: On invalid JSON.
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
