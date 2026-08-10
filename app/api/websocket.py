import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.runs import active_runs

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)

@router.websocket("/runs/{run_id}")
async def run_websocket(websocket: WebSocket, run_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for run_id: {run_id}")

    try:
        last_log_count = 0
        while True:
            state = active_runs.get(run_id)
            if state:
                # Stream new logs and status updates
                current_logs = state.logs
                if len(current_logs) > last_log_count or state.status:
                    await websocket.send_json({
                        "run_id": run_id,
                        "status": state.status.value,
                        "logs": current_logs,
                        "bugs_count": len(state.discovered_bugs),
                        "routes_count": len(state.site_map),
                        "tests_count": len(state.test_plan)
                    })
                    last_log_count = len(current_logs)

                if state.status in ["COMPLETED", "FAILED"]:
                    break

            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run_id: {run_id}")
    except Exception as e:
        logger.error(f"WebSocket streaming error: {e}")

    await websocket.close()
