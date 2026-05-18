"""Cycling training metrics: TSS, IF, weekly load, and fitness trend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.strava_client import Activity


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def calculate_intensity_factor(normalized_power: float, ftp: float) -> float:
    """Compute the Intensity Factor (IF) for a workout.

    IF = NP / FTP.  A value of 1.0 means the effort matched FTP exactly.

    Args:
        normalized_power: Normalized power in watts for the activity.
        ftp: Athlete's current Functional Threshold Power in watts.

    Returns:
        Intensity Factor as a float (typically 0.5–1.05 for most rides).

    Raises:
        ValueError: If ftp is zero or negative.
    """
    if ftp <= 0:
        raise ValueError(f"FTP must be positive, got {ftp}")
    return normalized_power / ftp


def calculate_tss(
    normalized_power: float,
    ftp: float,
    duration_seconds: int,
) -> float:
    """Compute Training Stress Score (TSS) for a single activity.

    TSS = (duration_s * NP * IF) / (FTP * 3600) * 100

    A one-hour ride at exactly FTP yields a TSS of 100.

    Args:
        normalized_power: Normalized power in watts.
        ftp: Athlete's current Functional Threshold Power in watts.
        duration_seconds: Moving duration of the activity in seconds.

    Returns:
        TSS as a float.  Values > 150 indicate a very hard/long effort.

    Raises:
        ValueError: If ftp is zero or negative.
    """
    if ftp <= 0:
        raise ValueError(f"FTP must be positive, got {ftp}")
    intensity_factor = calculate_intensity_factor(normalized_power, ftp)
    return (duration_seconds * normalized_power * intensity_factor) / (ftp * 3600) * 100


def calculate_weekly_load(activities: list[Activity]) -> float:
    """Sum the TSS across a list of activities to get total weekly load.

    Activities without average_watts are skipped because TSS cannot be
    computed without power data.

    Args:
        activities: List of Activity objects, typically spanning one week.

    Returns:
        Total TSS for the period.  Returns 0.0 if no power data is present.
    """
    total = 0.0
    for act in activities:
        if act.average_watts is None or act.moving_time == 0:
            continue
        # Use average_watts as a proxy for NP when streams aren't loaded.
        # This slightly underestimates TSS for variable-intensity rides.
        try:
            total += calculate_tss(
                normalized_power=act.average_watts,
                ftp=_infer_ftp(activities),
                duration_seconds=act.moving_time,
            )
        except ValueError:
            continue
    return round(total, 1)


def classify_fitness_trend(weekly_loads: list[float]) -> str:
    """Classify the athlete's fitness trajectory from recent weekly TSS totals.

    Compares the most recent week against the rolling average of the prior
    weeks to detect whether load is increasing, stable, or declining.

    Args:
        weekly_loads: Ordered list of weekly TSS totals, oldest first.
            At least two values are required for a meaningful classification.

    Returns:
        One of ``"building"``, ``"maintaining"``, or ``"declining"``.
        Returns ``"maintaining"`` if fewer than two weeks of data are provided.
    """
    if len(weekly_loads) < 2:
        return "maintaining"

    current = weekly_loads[-1]
    prior_avg = sum(weekly_loads[:-1]) / len(weekly_loads[:-1])

    if prior_avg == 0:
        return "maintaining"

    change_pct = (current - prior_avg) / prior_avg * 100

    if change_pct >= 5:
        return "building"
    if change_pct <= -5:
        return "declining"
    return "maintaining"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _infer_ftp(activities: list[Activity]) -> float:
    """Estimate FTP from activities as 95 % of the best 20-min average power.

    This is a rough heuristic used when the athlete's FTP is not stored on
    their Strava profile.  It looks for activities that are at least 20
    minutes long and takes 95 % of the highest average watts seen.

    Args:
        activities: Pool of activities to search.

    Returns:
        Estimated FTP.  Falls back to 200 W if no power data is available.
    """
    candidates = [
        act.average_watts
        for act in activities
        if act.average_watts is not None and act.moving_time >= 1200
    ]
    if not candidates:
        return 200.0  # sensible fallback
    return max(candidates) * 0.95
