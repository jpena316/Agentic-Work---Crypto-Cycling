from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from api.services.mcp_client import fetch_investment_brief
from api.models.responses import InvestmentBriefResponse
import json

router = APIRouter(prefix="/brief", tags=["brief"])


@router.get("/{token}", response_model=InvestmentBriefResponse)
async def get_investment_brief(
    token: str,
    horizon: str = Query(default="medium", pattern="^(short|medium|long)$"),
):
    """
    Generate a full investment research brief for a cryptocurrency.
    This endpoint calls all three data tools plus Claude — expect 15-20 seconds.
    """
    try:
        result = await fetch_investment_brief(token.lower(), horizon)
        return InvestmentBriefResponse(**result.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{token}")
async def brief_websocket(
    websocket: WebSocket,
    token: str,
    horizon: str = "medium",
):
    """
    WebSocket endpoint for streaming investment brief generation.
    Sends status updates as each data tool completes, then streams the brief.
    """
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({
            "type": "status",
            "message": f"Fetching market data for {token}..."
        }))

        result = await fetch_investment_brief(token.lower(), horizon)

        await websocket.send_text(json.dumps({
            "type": "complete",
            "data": result.model_dump()
        }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))