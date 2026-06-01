"""Plan router — training plan endpoint."""

from fastapi import APIRouter, HTTPException

from api.models.responses import TrainingPlanResponse
from api.services.session import get_last_report

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("/current", response_model=TrainingPlanResponse)
async def get_current_plan():
    """
    Return the 7-day training plan from the most recent coaching run.

    Returns 404 if /analysis/run has not been called yet this session.
    The plan reflects the last completed orchestrator run and is held in
    memory — it is not persisted across server restarts.
    """
    report = get_last_report()
    if not report or not report.get("training_plan"):
        raise HTTPException(
            status_code=404,
            detail="No training plan available. Call POST /analysis/run first.",
        )
    return TrainingPlanResponse(**report["training_plan"])
