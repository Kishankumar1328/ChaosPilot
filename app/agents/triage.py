import uuid
import logging
from typing import List
from app.models.state import ChaosPilotState, RunStatus
from app.models.bugreport import BugReport, BugSeverity
from app.safety.domain_lock import DomainLock
from app.tools.browser_manager import BrowserManager
from app.tools.evidence import EvidenceRecorder
from app.tools.script_generator import ReproductionScriptGenerator

logger = logging.getLogger(__name__)

async def triage_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Triage Node (Bug Triage Agent):
    Evaluates step failure results, filters noise, captures visual evidence,
    and generates standalone reproduction scripts for verified bugs.
    """
    state.status = RunStatus.TRIAGING
    state.logs.append("🧐 [BugTriageAgent] Triaging execution failures and generating bug reports...")
    logger.info(f"BugTriageAgent running for run {state.run_id}")

    evidence_recorder = EvidenceRecorder(output_dir=f"./artifacts/{state.run_id}")
    browser_mgr = BrowserManager()
    await browser_mgr.start(headless=True)

    try:
        discovered_bugs: List[BugReport] = []

        for tc in state.test_plan:
            results = state.execution_results.get(tc.id, [])
            failed_step = next((r for r in results if not r.success), None)

            if failed_step:
                bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                
                # Determine Severity based on error characteristics
                severity = BugSeverity.MEDIUM
                combined_err = f"{failed_step.error_message} {' '.join(failed_step.console_errors)} {' '.join(failed_step.network_errors)}"
                
                if "HTTP 5" in combined_err or "UNCAUGHT_EXCEPTION" in combined_err or "page crash" in combined_err.lower():
                    severity = BugSeverity.CRITICAL
                elif "unhandled" in combined_err.lower() or "AssertionError" in combined_err:
                    severity = BugSeverity.HIGH
                elif "GUARDRAIL_BLOCKED" in combined_err:
                    severity = BugSeverity.LOW

                # Capture visual screenshot
                screenshot_path = ""
                try:
                    await browser_mgr.page.goto(tc.target_route, wait_until="networkidle", timeout=10000)
                    screenshot_path = await evidence_recorder.capture_screenshot(
                        page=browser_mgr.page,
                        run_id=state.run_id,
                        bug_id=bug_id
                    )
                except Exception as e:
                    logger.warning(f"Failed screenshot capture during triage: {e}")

                # Generate standalone Playwright reproduction script
                script_path = ReproductionScriptGenerator.generate_script(
                    run_id=state.run_id,
                    bug_id=bug_id,
                    bug_title=f"{tc.title} - Step {failed_step.step_id} Failure",
                    target_route=tc.target_route,
                    steps=tc.steps,
                    output_dir="./artifacts"
                )

                bug = BugReport(
                    id=bug_id,
                    title=f"Failure in {tc.id}: {tc.title}",
                    severity=severity,
                    route=tc.target_route,
                    failed_step_id=failed_step.step_id,
                    description=failed_step.error_message or "Test step failed assertion or error threshold",
                    reproduction_steps=[f"{step.action.value} -> {step.target_selector or step.value or 'route'}" for step in tc.steps],
                    console_logs=failed_step.console_errors,
                    network_logs=failed_step.network_errors,
                    screenshot_path=screenshot_path,
                    reproduction_script_path=script_path
                )
                discovered_bugs.append(bug)
                state.logs.append(f"🚨 [BugTriageAgent] Formatted Bug Report {bug.id} [{bug.severity.value}]: {bug.title}")

        state.discovered_bugs = discovered_bugs
        state.logs.append(f"✅ [BugTriageAgent] Triage complete. Total bugs recorded: {len(discovered_bugs)}")

    except Exception as e:
        logger.error(f"BugTriageAgent error: {e}")
        state.logs.append(f"❌ [BugTriageAgent] Unexpected triage error: {str(e)}")
    finally:
        await browser_mgr.close()

    return state
