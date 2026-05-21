"""Validation rules for generated training plans."""

_HARD_WORKOUT_TYPES = {"Threshold", "VO2max"}
_HARD_INTENSITIES = {"Hard"}


def is_hard_workout(workout_type: str, intensity: str) -> bool:
    """Return True if this workout qualifies as a hard training day.

    Args:
        workout_type: One of Rest | Endurance | Threshold | VO2max | Recovery.
        intensity: One of Easy | Moderate | Hard | Rest.

    Returns:
        True when the type is Threshold/VO2max or the intensity is Hard.
    """
    return workout_type in _HARD_WORKOUT_TYPES or intensity in _HARD_INTENSITIES


def validate_training_plan(plan: dict) -> list[str]:
    """Check a generated training plan against safety and load-management rules.

    Rules checked:
    1. No more than 2 hard days per week.
    2. No hard day immediately after another hard day.
    3. At least 1 rest day per week.

    Args:
        plan: Parsed training plan dict as returned by the Claude API.

    Returns:
        List of violation message strings.  Empty list means the plan is valid.
    """
    violations: list[str] = []
    days: list[dict] = plan.get("days", [])

    hard_indices: list[int] = []
    rest_count = 0

    for i, day in enumerate(days):
        wtype = day.get("workout_type", "")
        intensity = day.get("intensity", "")

        if is_hard_workout(wtype, intensity):
            hard_indices.append(i)

        if wtype == "Rest" or intensity == "Rest":
            rest_count += 1

    if len(hard_indices) > 2:
        violations.append(
            f"Plan has {len(hard_indices)} hard days; maximum allowed is 2."
        )

    for a, b in zip(hard_indices, hard_indices[1:]):
        if b == a + 1:
            day_a = days[a].get("day", f"day {a + 1}")
            day_b = days[b].get("day", f"day {b + 1}")
            violations.append(
                f"Back-to-back hard days: {day_a} and {day_b}."
            )

    if rest_count == 0:
        violations.append("Plan has no rest day; at least 1 is required.")

    return violations
