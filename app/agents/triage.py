import uuid
import logging
from typing import List, Dict
from app.models.state import ChaosPilotState, RunStatus
from app.models.bugreport import BugReport, BugSeverity, ExecutionIssue, NavigationStatus, TestExecutionStatus
from app.safety.domain_lock import DomainLock
from app.tools.browser_manager import BrowserManager
from app.tools.evidence import EvidenceRecorder
from app.tools.script_generator import ReproductionScriptGenerator

logger = logging.getLogger(__name__)

async def triage_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Triage Node (Bug Triage Agent):
    Evaluates step failure results, distinguishes genuine application defects from runner/infrastructure timeouts,
    deduplicates infrastructure issues (CHAOSPILOT-EXEC-001), and generates bug reports only when evidence exists.
    """
    state.status = RunStatus.TRIAGING
    state.logs.append("🧐 [BugTriageAgent] Triaging execution failures and evidence classification...")
    logger.info(f"BugTriageAgent running for run {state.run_id}")

    if not state.target_reachable:
        state.logs.append("ℹ️ [BugTriageAgent] Target application unreachable during preflight. Skipping bug creation.")
        return state

    evidence_recorder = EvidenceRecorder(output_dir=f"./artifacts/{state.run_id}")
    browser_mgr = BrowserManager()
    await browser_mgr.start(headless=True)

    try:
        discovered_bugs: List[BugReport] = []
        execution_issues: List[ExecutionIssue] = []
        blocked_tests_count = 0
        infrastructure_fingerprints: Dict[str, ExecutionIssue] = {}

        for tc in state.test_plan:
            results = state.execution_results.get(tc.id, [])
            failed_step = next((r for r in results if not r.success), None)

            if failed_step:
                combined_err = f"{failed_step.error_message or ''} {' '.join(failed_step.console_errors)} {' '.join(failed_step.network_errors)}"

                # A. Application Bug Check (Requires concrete evidence: uncaught JS crash, HTTP 500, or assertion failure)
                if failed_step.is_application_bug or "HTTP 500" in combined_err or "UNCAUGHT" in combined_err.upper() or "ASSERTIONERROR" in combined_err.upper():
                    bug_id = f"BUG-{uuid.uuid4().hex[:6].upper()}"
                    severity = BugSeverity.MEDIUM
                    
                    if "HTTP 5" in combined_err or "UNCAUGHT" in combined_err.upper():
                        severity = BugSeverity.CRITICAL
                    elif "ASSERTIONERROR" in combined_err.upper():
                        severity = BugSeverity.HIGH

                    # Capture visual screenshot safely using domcontentloaded
                    screenshot_path = ""
                    try:
                        await browser_mgr.page.goto(tc.target_route, wait_until="domcontentloaded", timeout=5000)
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
                        title=f"Application Defect on {tc.target_route}",
                        severity=severity,
                        route=tc.target_route,
                        failed_step_id=failed_step.step_id,
                        description=failed_step.error_message or "Verified application execution defect",
                        reproduction_steps=[s.model_dump_json() for s in tc.steps],
                        console_logs=failed_step.console_errors,
                        network_logs=failed_step.network_errors,
                        screenshot_path=screenshot_path,
                        reproduction_script_path=script_path
                    )
                    discovered_bugs.append(bug)
                    state.logs.append(f"🐛 [BugTriageAgent] Confirmed Application Bug {bug.id} ({bug.severity.value}) on {bug.route}")

                # B. Runner / Infrastructure / Navigation Timeout Handling
                else:
                    blocked_tests_count += 1
                    fp_key = f"{failed_step.nav_status.value}_{tc.target_route}"
                    if fp_key not in infrastructure_fingerprints:
                        exec_issue = ExecutionIssue(
                            id=f"CHAOSPILOT-EXEC-{len(infrastructure_fingerprints)+1:03d}",
                            title=f"Navigation / Infrastructure Execution Issue ({failed_step.nav_status.value})",
                            reason=failed_step.error_message or "Browser navigation engine timed out before DOM ready state",
                            target_url=tc.target_route,
                            stage="Test Execution",
                            nav_status=failed_step.nav_status,
                            blocked_tests_count=1
                        )
                        infrastructure_fingerprints[fp_key] = exec_issue
                    else:
                        infrastructure_fingerprints[fp_key].blocked_tests_count += 1

                    state.logs.append(f"ℹ️ [BugTriageAgent] Test {tc.id} classified as {failed_step.status.value} ({failed_step.nav_status.value}). Not reported as application bug.")

        state.discovered_bugs = discovered_bugs
        state.execution_issues = list(infrastructure_fingerprints.values())
        state.logs.append(f"✅ [BugTriageAgent] Triage complete. {len(discovered_bugs)} application bugs confirmed, {len(state.execution_issues)} execution issues deduplicated ({blocked_tests_count} tests blocked).")

    except Exception as e:
        logger.error(f"BugTriageAgent error: {e}")
        state.logs.append(f"❌ [BugTriageAgent] Triage error: {str(e)}")
    finally:
        await browser_mgr.close()

    return state
