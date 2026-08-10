import os
import subprocess
from typing import List
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse

from app.models.bugreport import BugReport
from app.models.codefix import RootCauseAnalysis, PatchStatus
from app.agents.code_fixer import analyze_root_cause_and_fix
from app.tools.patch_engine import PatchEngine
from app.api.runs import active_runs

router = APIRouter(prefix="/bugs", tags=["bugs"])

@router.get("", response_model=List[BugReport])
async def list_all_bugs():
    all_bugs = []
    for run in active_runs.values():
        all_bugs.extend(run.discovered_bugs)
    return all_bugs

@router.get("/{bug_id}/evidence", response_class=FileResponse)
async def download_evidence(bug_id: str):
    for run in active_runs.values():
        for bug in run.discovered_bugs:
            if bug.id == bug_id and bug.screenshot_path and os.path.exists(bug.screenshot_path):
                return FileResponse(bug.screenshot_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Evidence screenshot not found")

@router.post("/{bug_id}/analyze", response_model=RootCauseAnalysis)
async def analyze_bug(bug_id: str):
    target_bug = None
    for run in active_runs.values():
        for bug in run.discovered_bugs:
            if bug.id == bug_id:
                target_bug = bug
                break

    if not target_bug:
        raise HTTPException(status_code=404, detail=f"Bug ID '{bug_id}' not found.")

    analysis = await analyze_root_cause_and_fix(target_bug, repo_dir=".")
    target_bug.root_cause_analysis = analysis
    return analysis

@router.post("/{bug_id}/apply-fix")
async def apply_fix(bug_id: str, approve: bool = Body(embed=True)):
    if not approve:
        raise HTTPException(status_code=400, detail="Explicit human approval is required to apply code fixes.")

    target_bug = None
    for run in active_runs.values():
        for bug in run.discovered_bugs:
            if bug.id == bug_id:
                target_bug = bug
                break

    if not target_bug or not target_bug.root_cause_analysis:
        raise HTTPException(status_code=404, detail="Bug or root cause analysis not found. Run analysis first.")

    analysis: RootCauseAnalysis = target_bug.root_cause_analysis

    applied_results = []
    for patch in analysis.proposed_patches:
        success, msg = PatchEngine.apply_patch(patch)
        applied_results.append({"file": patch.file_path, "success": success, "msg": msg})

    analysis.status = PatchStatus.VERIFIED
    return {
        "status": "APPROVED_AND_APPLIED",
        "bug_id": bug_id,
        "results": applied_results
    }
