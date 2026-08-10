import uuid
import asyncio
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_session
from app.db.models import RunRecord, BugReportRecord
from app.models.state import ChaosPilotState, RunStatus
from app.agents.graph import chaospilot_app

router = APIRouter(prefix="/runs", tags=["runs"])
logger = logging.getLogger(__name__)

# Active run state cache for real-time WebSocket and polling access
active_runs: dict[str, ChaosPilotState] = {}

class CreateRunRequest(BaseModel):
    target_url: str
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 25

async def execute_run_task(state: ChaosPilotState):
    """
    Background worker that streams LangGraph state machine node updates in real-time.
    """
    active_runs[state.run_id] = state
    try:
        # Stream updates from each LangGraph node as it executes
        async for output in chaospilot_app.astream(state):
            for node_name, node_state in output.items():
                if isinstance(node_state, ChaosPilotState):
                    active_runs[state.run_id] = node_state
                elif isinstance(node_state, dict):
                    active_runs[state.run_id] = ChaosPilotState(**node_state)
                logger.debug(f"Streamed node '{node_name}' update for run {state.run_id}")

        logger.info(f"Run {state.run_id} completed with status: {active_runs[state.run_id].status}")
    except Exception as e:
        logger.error(f"Execution error in run task {state.run_id}: {e}")
        state.status = RunStatus.FAILED
        state.error_summary = str(e)
        active_runs[state.run_id] = state

@router.post("", response_model=ChaosPilotState)
async def start_run(req: CreateRunRequest, background_tasks: BackgroundTasks):
    if not req.target_url.startswith("http://") and not req.target_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid target_url scheme. Must start with http:// or https://")

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    initial_state = ChaosPilotState(
        run_id=run_id,
        target_url=req.target_url,
        max_depth=req.max_depth or 3,
        max_pages=req.max_pages or 25,
        status=RunStatus.IDLE
    )
    active_runs[run_id] = initial_state

    # Launch background task
    background_tasks.add_task(execute_run_task, initial_state)
    return initial_state

@router.get("", response_model=List[ChaosPilotState])
async def list_runs():
    return list(active_runs.values())

@router.get("/{run_id}", response_model=ChaosPilotState)
async def get_run(run_id: str):
    if run_id in active_runs:
        return active_runs[run_id]
    raise HTTPException(status_code=404, detail=f"Run ID '{run_id}' not found.")
