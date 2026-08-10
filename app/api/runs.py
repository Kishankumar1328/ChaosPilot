import uuid
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import select

from app.db.database import async_session_maker
from app.db.models import RunRecord, BugReportRecord
from app.models.state import ChaosPilotState, RunStatus
from app.agents.graph import chaospilot_app

router = APIRouter(prefix="/runs", tags=["runs"])
logger = logging.getLogger(__name__)

# Active run state in-memory cache
active_runs: dict[str, ChaosPilotState] = {}

class CreateRunRequest(BaseModel):
    target_url: str
    max_depth: Optional[int] = 3
    max_pages: Optional[int] = 25

async def save_run_to_db(state: ChaosPilotState):
    """
    Persists ChaosPilot run state and discovered bug reports into MySQL database.
    """
    try:
        async with async_session_maker() as session:
            record = await session.get(RunRecord, state.run_id)
            if record:
                record.status = state.status.value
                record.state_json = state.model_dump_json()
                record.updated_at = datetime.utcnow()
            else:
                record = RunRecord(
                    id=state.run_id,
                    target_url=state.target_url,
                    status=state.status.value,
                    max_depth=state.max_depth,
                    max_pages=state.max_pages,
                    state_json=state.model_dump_json()
                )
                session.add(record)

            # Persist discovered bugs to MySQL
            for bug in state.discovered_bugs:
                bug_rec = await session.get(BugReportRecord, bug.id)
                if not bug_rec:
                    bug_rec = BugReportRecord(
                        id=bug.id,
                        run_id=state.run_id,
                        title=bug.title,
                        severity=bug.severity.value,
                        route=bug.route,
                        description=bug.description,
                        report_json=bug.model_dump_json()
                    )
                    session.add(bug_rec)

            await session.commit()
            logger.debug(f"Successfully persisted run {state.run_id} state & bugs to MySQL database.")
    except Exception as e:
        logger.warning(f"Could not persist run {state.run_id} to MySQL: {e}")

async def execute_run_task(state: ChaosPilotState):
    """
    Background worker that streams LangGraph state machine node updates in real-time
    and persists updates to MySQL database.
    """
    active_runs[state.run_id] = state
    await save_run_to_db(state)
    
    try:
        async for output in chaospilot_app.astream(state):
            for node_name, node_state in output.items():
                if isinstance(node_state, ChaosPilotState):
                    active_runs[state.run_id] = node_state
                elif isinstance(node_state, dict):
                    active_runs[state.run_id] = ChaosPilotState(**node_state)
                
                # Persist state update to MySQL
                await save_run_to_db(active_runs[state.run_id])
                logger.debug(f"Streamed node '{node_name}' update for run {state.run_id}")

        logger.info(f"Run {state.run_id} completed with status: {active_runs[state.run_id].status}")
    except Exception as e:
        logger.error(f"Execution error in run task {state.run_id}: {e}")
        state.status = RunStatus.EXECUTION_FAILED
        state.error_summary = str(e)
        active_runs[state.run_id] = state
        await save_run_to_db(state)

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
    await save_run_to_db(initial_state)

    background_tasks.add_task(execute_run_task, initial_state)
    return initial_state

@router.get("", response_model=List[ChaosPilotState])
async def list_runs():
    runs_map = dict(active_runs)
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(RunRecord).order_by(RunRecord.created_at.desc()))
            db_records = result.scalars().all()
            for rec in db_records:
                if rec.id not in runs_map:
                    try:
                        state_dict = json.loads(rec.state_json)
                        runs_map[rec.id] = ChaosPilotState(**state_dict)
                    except Exception as e:
                        logger.warning(f"Error parsing DB state_json for run {rec.id}: {e}")
    except Exception as e:
        logger.warning(f"Error fetching runs from MySQL database: {e}")

    return list(runs_map.values())

@router.get("/{run_id}", response_model=ChaosPilotState)
async def get_run(run_id: str):
    if run_id in active_runs:
        return active_runs[run_id]
    try:
        async with async_session_maker() as session:
            rec = await session.get(RunRecord, run_id)
            if rec:
                state_dict = json.loads(rec.state_json)
                return ChaosPilotState(**state_dict)
    except Exception as e:
        logger.warning(f"Error fetching run {run_id} from MySQL database: {e}")
    raise HTTPException(status_code=404, detail=f"Run ID '{run_id}' not found.")
