import pytest
import asyncio
from app.models.state import ChaosPilotState, RunStatus
from app.models.testplan import TestCase, TestStep, ActionType, TestCategory
from app.models.bugreport import StepResult, NavigationStatus, TestExecutionStatus, BugSeverity, BugReport
from app.tools.preflight import TargetPreflight
from app.agents.explorer import discovery_node
from app.agents.triage import triage_node
from app.agents.reporter import reporter_node
from app.agents.code_fixer import analyze_root_cause_and_fix

@pytest.mark.asyncio
async def test_target_preflight_valid_target():
    """Verifies target preflight check succeeds for valid target."""
    health = await TargetPreflight.check_health("https://example.com")
    assert health.reachable is True
    assert health.error_kind == "SUCCESS"

@pytest.mark.asyncio
async def test_target_preflight_unreachable_target():
    """Verifies preflight check returns unreachable for invalid domain."""
    health = await TargetPreflight.check_health("http://invalid-domain-does-not-exist-12345.com")
    assert health.reachable is False
    assert health.error_kind in ["DNS_FAILURE", "TARGET_UNREACHABLE", "HTTP_PROBE_FAILED"]

@pytest.mark.asyncio
async def test_unreachable_target_sets_target_unavailable():
    """Verifies discovery node sets TARGET_UNAVAILABLE state without generating fake bugs."""
    state = ChaosPilotState(
        run_id="RUN-TEST-UNREACHABLE",
        target_url="http://invalid-domain-does-not-exist-9999.com"
    )
    res_state = await discovery_node(state)
    assert res_state.status == RunStatus.TARGET_UNAVAILABLE
    assert res_state.target_reachable is False

@pytest.mark.asyncio
async def test_triage_deduplicates_infrastructure_timeouts():
    """Verifies triage node classifies navigation timeouts into execution issues without creating fake application bugs."""
    state = ChaosPilotState(
        run_id="RUN-TEST-TIMEOUT",
        target_url="https://example.com",
        test_plan=[
            TestCase(
                id="TC-01",
                title="Test Route 1",
                description="Test navigation timeout",
                category=TestCategory.FUNCTIONAL,
                target_route="https://example.com/route1",
                steps=[TestStep(step_id="S1", action=ActionType.NAVIGATE, value="https://example.com/route1", expected_outcome="Route loaded")]
            ),
            TestCase(
                id="TC-02",
                title="Test Route 2",
                description="Test navigation timeout 2",
                category=TestCategory.FUNCTIONAL,
                target_route="https://example.com/route1",
                steps=[TestStep(step_id="S1", action=ActionType.NAVIGATE, value="https://example.com/route1", expected_outcome="Route loaded")]
            )
        ],
        execution_results={
            "TC-01": [
                StepResult(
                    step_id="S1",
                    success=False,
                    status=TestExecutionStatus.INFRASTRUCTURE_ERROR,
                    nav_status=NavigationStatus.NAVIGATION_TIMEOUT,
                    error_message="Navigation timeout loading https://example.com/route1",
                    is_application_bug=False
                )
            ],
            "TC-02": [
                StepResult(
                    step_id="S1",
                    success=False,
                    status=TestExecutionStatus.INFRASTRUCTURE_ERROR,
                    nav_status=NavigationStatus.NAVIGATION_TIMEOUT,
                    error_message="Navigation timeout loading https://example.com/route1",
                    is_application_bug=False
                )
            ]
        }
    )

    res_state = await triage_node(state)
    # Must NOT create application bugs for browser navigation timeouts
    assert len(res_state.discovered_bugs) == 0
    # Must create deduplicated execution issue
    assert len(res_state.execution_issues) == 1
    assert res_state.execution_issues[0].id == "CHAOSPILOT-EXEC-001"
    assert res_state.execution_issues[0].blocked_tests_count == 2

@pytest.mark.asyncio
async def test_reporter_status_calculation():
    """Verifies reporter node sets accurate status for runs with blocked tests vs bugs."""
    # Case A: Execution Issues -> COMPLETED_WITH_BLOCKED_TESTS
    state_blocked = ChaosPilotState(
        run_id="RUN-BLOCKED",
        target_url="https://example.com",
        execution_issues=[
            {"id": "CHAOSPILOT-EXEC-001", "title": "Timeout", "reason": "Timeout", "target_url": "https://example.com", "stage": "Exec", "nav_status": NavigationStatus.NAVIGATION_TIMEOUT, "blocked_tests_count": 1}
        ]
    )
    res_blocked = await reporter_node(state_blocked)
    assert res_blocked.status == RunStatus.COMPLETED_WITH_BLOCKED_TESTS

    # Case B: Discovered Bugs -> COMPLETED_WITH_BUGS
    state_bugs = ChaosPilotState(
        run_id="RUN-BUGS",
        target_url="https://example.com",
        discovered_bugs=[
            BugReport(
                id="BUG-001",
                title="HTTP 500 Unhandled Exception",
                severity=BugSeverity.CRITICAL,
                route="https://example.com",
                failed_step_id="S1",
                description="HTTP 500 Server Error"
            )
        ]
    )
    res_bugs = await reporter_node(state_bugs)
    assert res_bugs.status == RunStatus.COMPLETED_WITH_BUGS

@pytest.mark.asyncio
async def test_code_fixer_rejects_generic_patches():
    """Verifies code fixer rejects generic exception suppression patches for runner timeouts."""
    timeout_bug = BugReport(
        id="BUG-TIMEOUT",
        title="Timeout Error",
        severity=BugSeverity.MEDIUM,
        route="https://example.com",
        failed_step_id="S1",
        description="Execution issue caused by Playwright browser navigation timeout."
    )

    analysis = await analyze_root_cause_and_fix(timeout_bug)
    assert len(analysis.proposed_patches) == 0
    assert "No application code defect identified" in analysis.probable_root_cause
