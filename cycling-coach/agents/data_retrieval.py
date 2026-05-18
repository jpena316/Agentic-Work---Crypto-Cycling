"""Agent 1 — Data Retrieval: fetches Strava data and computes training metrics.

No LLM calls here — pure Python and Strava API only.
"""

from datetime import datetime, timedelta, timezone

from agents.base_agent import BaseAgent
from tools.metrics import calculate_tss, classify_fitness_trend
from tools.strava_client import Activity, StravaClient

_CYCLING_TYPES = {"Ride", "VirtualRide"}


class DataRetrievalAgent(BaseAgent):
    """Fetches the athlete's Strava data and populates computed_metrics."""

    async def run(self, context: dict) -> dict:
        """Fetch athlete profile and activities, compute training metrics.

        Writes to:
            context["athlete_profile"]  — AthleteProfile dict
            context["raw_activities"]   — all activities as dicts (not filtered)
            context["computed_metrics"] — aggregated training metrics

        Args:
            context: Shared pipeline state.

        Returns:
            Updated context dict.
        """
        client = StravaClient()
        all_activities: list[Activity] = []

        # ------------------------------------------------------------------
        # Step 1: athlete profile
        # ------------------------------------------------------------------
        self.logger.info("Fetching athlete profile from Strava...")
        try:
            profile = await client.get_athlete()
            context["athlete_profile"] = profile.model_dump()
            self.logger.info(
                "Athlete: %s %s (FTP=%s, weight=%s kg)",
                profile.firstname,
                profile.lastname,
                profile.ftp,
                profile.weight,
            )
        except Exception as exc:
            self._add_error(context, f"Failed to fetch athlete profile: {exc}")
            context["athlete_profile"] = None

        # ------------------------------------------------------------------
        # Step 2: raw activity list
        # ------------------------------------------------------------------
        self.logger.info("Fetching activities for the last 30 days...")
        try:
            all_activities = await client.get_activities(days=30)
            context["raw_activities"] = [a.model_dump() for a in all_activities]
            self.logger.info("Fetched %d total activities", len(all_activities))
        except Exception as exc:
            self._add_error(context, f"Failed to fetch activities: {exc}")
            context["raw_activities"] = []

        # ------------------------------------------------------------------
        # Step 3: filter to cycling
        # ------------------------------------------------------------------
        rides = [a for a in all_activities if a.type in _CYCLING_TYPES]
        self.logger.info(
            "Filtered to %d cycling activities (%s)",
            len(rides),
            "/".join(_CYCLING_TYPES),
        )

        # ------------------------------------------------------------------
        # Step 4: compute metrics
        # ------------------------------------------------------------------
        self.logger.info("Computing training metrics...")
        ftp_from_profile: int | None = (
            context["athlete_profile"].get("ftp")
            if context.get("athlete_profile")
            else None
        )
        try:
            context["computed_metrics"] = self._compute_metrics(rides, ftp_from_profile)
            self.logger.info(
                "Metrics done — %d rides, %.1f km, trend: %s",
                context["computed_metrics"]["total_rides"],
                context["computed_metrics"]["total_distance_km"],
                context["computed_metrics"]["fitness_trend"],
            )
        except Exception as exc:
            self._add_error(context, f"Failed to compute training metrics: {exc}")
            context["computed_metrics"] = {}

        return context

    # ------------------------------------------------------------------
    # Metric computation
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        rides: list[Activity],
        ftp: int | None,
    ) -> dict:
        """Aggregate training metrics from a list of cycling activities.

        Args:
            rides: Cycling-only Activity objects for the last 30 days.
            ftp: Athlete's FTP from their Strava profile, or None.

        Returns:
            Dict of computed metrics (see field list in module docstring).
        """
        if not rides:
            return _empty_metrics()

        now = datetime.now(tz=timezone.utc)
        effective_ftp = float(ftp) if ftp else _estimate_ftp(rides)
        self.logger.debug("Using FTP: %.0f W (from_profile=%s)", effective_ftp, ftp is not None)

        # Build 4 weekly TSS buckets, oldest first (required by classify_fitness_trend)
        week_offsets = [
            (timedelta(days=28), timedelta(days=21)),  # week 1 — oldest
            (timedelta(days=21), timedelta(days=14)),  # week 2
            (timedelta(days=14), timedelta(days=7)),   # week 3
            (timedelta(days=7),  timedelta(days=0)),   # week 4 — most recent
        ]
        week_loads: list[float] = []
        for back_start, back_end in week_offsets:
            bucket = _rides_in_window(rides, now - back_start, now - back_end)
            week_loads.append(_sum_tss(bucket, effective_ftp))

        weekly_tss = week_loads[-1]
        four_week_tss = round(sum(week_loads), 1)
        fitness_trend = classify_fitness_trend(week_loads)

        # Per-field aggregates
        power_rides = [r for r in rides if r.average_watts is not None]
        hr_rides = [r for r in rides if r.average_heartrate is not None]

        return {
            "total_rides": len(rides),
            "total_distance_km": round(sum(r.distance for r in rides) / 1000, 1),
            "total_elevation_m": round(sum(r.total_elevation_gain for r in rides), 0),
            "avg_ride_duration_mins": round(
                sum(r.moving_time for r in rides) / len(rides) / 60, 1
            ),
            "weekly_tss": round(weekly_tss, 1),
            "four_week_tss": four_week_tss,
            "fitness_trend": fitness_trend,
            "avg_power": (
                round(sum(r.average_watts for r in power_rides) / len(power_rides), 1)
                if power_rides else None
            ),
            "avg_heart_rate": (
                round(sum(r.average_heartrate for r in hr_rides) / len(hr_rides), 1)
                if hr_rides else None
            ),
            "longest_ride_km": round(max(r.distance for r in rides) / 1000, 1),
            "rides_with_power": len(power_rides),
        }


# ------------------------------------------------------------------
# Module-level helpers (no state, easy to test independently)
# ------------------------------------------------------------------

def _rides_in_window(
    rides: list[Activity],
    start: datetime,
    end: datetime,
) -> list[Activity]:
    """Return rides whose start_date falls in [start, end).

    Args:
        rides: Full list of Activity objects to filter.
        start: Window open boundary (inclusive).
        end: Window close boundary (exclusive).

    Returns:
        Subset of *rides* within the window.  Rides with unparseable
        start_date strings are silently excluded.
    """
    result: list[Activity] = []
    for ride in rides:
        try:
            dt = datetime.fromisoformat(ride.start_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if start <= dt < end:
                result.append(ride)
        except (ValueError, TypeError):
            pass
    return result


def _sum_tss(rides: list[Activity], ftp: float) -> float:
    """Sum TSS across rides that have power data.

    Args:
        rides: Activities to include.
        ftp: Functional Threshold Power to use for TSS calculation.

    Returns:
        Total TSS rounded to one decimal place.
    """
    total = 0.0
    for ride in rides:
        if ride.average_watts is None or ride.moving_time == 0:
            continue
        try:
            total += calculate_tss(
                normalized_power=ride.average_watts,
                ftp=ftp,
                duration_seconds=ride.moving_time,
            )
        except ValueError:
            pass
    return round(total, 1)


def _estimate_ftp(rides: list[Activity]) -> float:
    """Estimate FTP as 95 % of the best average power from rides ≥ 20 min.

    Args:
        rides: Pool of activities from which to derive an FTP estimate.

    Returns:
        Estimated FTP in watts.  Falls back to 200 W if no usable rides.
    """
    candidates = [
        r.average_watts
        for r in rides
        if r.average_watts is not None and r.moving_time >= 1200
    ]
    return max(candidates) * 0.95 if candidates else 200.0


def _empty_metrics() -> dict:
    """Return zero-valued metrics dict for when there are no rides."""
    return {
        "total_rides": 0,
        "total_distance_km": 0.0,
        "total_elevation_m": 0.0,
        "avg_ride_duration_mins": 0.0,
        "weekly_tss": 0.0,
        "four_week_tss": 0.0,
        "fitness_trend": "maintaining",
        "avg_power": None,
        "avg_heart_rate": None,
        "longest_ride_km": 0.0,
        "rides_with_power": 0,
    }
