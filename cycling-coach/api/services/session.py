"""In-process session store for the most recent coaching run result.

/analysis/run writes here after every successful orchestrator call.
/plan/current and /bikes/recommendations read from here.
This is intentionally simple — single-user local tool, no persistence needed.
"""

_last_report: dict | None = None


def set_last_report(report: dict) -> None:
    """Overwrite the stored report with the result of the latest run."""
    global _last_report
    _last_report = report


def get_last_report() -> dict | None:
    """Return the most recent coaching report, or None if none has run yet."""
    return _last_report
