"""Analysis router — full orchestrator pipeline endpoint."""

from fastapi import APIRouter, HTTPException

from api.models.responses import CoachingReportResponse, CoachingRunRequest
from api.services.session import set_last_report
from orchestrator.orchestrator import CyclingCoachOrchestrator

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=CoachingReportResponse)
async def run_analysis(request: CoachingRunRequest):
    """
    Run the full four-agent coaching pipeline.

    Fetches live Strava data, generates performance analysis and a 7-day
    training plan via Claude, then ranks the supplied bikes.
    Expect 2–3 minutes for a full run.

    The result is stored in the session store so /plan/current and
    /bikes/recommendations can serve it without re-running the pipeline.
    """
    try:
        orchestrator = CyclingCoachOrchestrator()
        report = await orchestrator.run(
            athlete_goals=request.athlete_goals,
            bikes_under_consideration=request.bikes,
        )
        set_last_report(report)
        return CoachingReportResponse(**report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
