import time
import logging
from typing import Optional, List, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from app.models.testplan import ActionType, TestStep
from app.models.bugreport import StepResult, NavigationStatus, TestExecutionStatus
from app.safety.action_interceptor import ActionInterceptor
from app.tools.listener import ConsoleNetworkListener

logger = logging.getLogger(__name__)

class UIExecutor:
    """
    Executes individual TestSteps via Playwright, enforcing safety guardrails,
    handling SPA client-side routing, inspecting element nature before interaction,
    and classifying navigation timeouts vs genuine application bugs.
    """
    def __init__(self, page: Page, listener: ConsoleNetworkListener, interceptor: ActionInterceptor):
        self.page = page
        self.listener = listener
        self.interceptor = interceptor

    async def execute_step(self, step: TestStep) -> StepResult:
        start_time = time.time()
        selector = step.target_selector or ""
        value = step.value or ""

        # 1. Safety Check via ActionInterceptor
        allowed, reason = self.interceptor.check_action(step.action.value, selector, value)
        if not allowed:
            duration = (time.time() - start_time) * 1000
            return StepResult(
                step_id=step.step_id,
                success=False,
                status=TestExecutionStatus.BLOCKED,
                nav_status=NavigationStatus.CHAOSPILOT_ERROR,
                error_message=f"GUARDRAIL_BLOCKED: {reason}",
                duration_ms=duration,
                is_application_bug=False
            )

        # 2. Execute Playwright Action
        nav_status = NavigationStatus.SUCCESS
        execution_status = TestExecutionStatus.PASSED
        is_bug = False
        error_msg = None

        try:
            if step.action == ActionType.NAVIGATE:
                target_url = value or selector
                try:
                    await self.page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
                except PlaywrightTimeoutError:
                    # Inspect if DOM content loaded despite network timeout
                    content = await self.page.content()
                    if len(content) > 100:
                        nav_status = NavigationStatus.PARTIAL_SUCCESS
                        logger.info(f"Navigation to {target_url} DOM content loaded despite network timeout.")
                    else:
                        nav_status = NavigationStatus.NAVIGATION_TIMEOUT
                        execution_status = TestExecutionStatus.INFRASTRUCTURE_ERROR
                        error_msg = f"Navigation timeout loading {target_url}"

            elif step.action == ActionType.CLICK:
                url_before = self.page.url
                # Wait for element to be visible without long sleep
                try:
                    await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                    await self.page.click(selector, timeout=5000)
                except PlaywrightTimeoutError:
                    # If selector wait timed out, check if element exists or is hidden
                    execution_status = TestExecutionStatus.FAILED
                    error_msg = f"Selector '{selector}' not visible or interactable within timeout"

                # Check SPA route transition or modal update
                url_after = self.page.url
                if url_before != url_after:
                    logger.debug(f"Click on {selector} triggered route transition: {url_before} -> {url_after}")

            elif step.action == ActionType.FILL:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                await self.page.fill(selector, value, timeout=5000)

            elif step.action == ActionType.SELECT:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                await self.page.select_option(selector, value, timeout=5000)

            elif step.action == ActionType.CHECK:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                await self.page.check(selector, timeout=5000)

            elif step.action == ActionType.PRESS:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                await self.page.press(selector, value or "Enter", timeout=5000)

            elif step.action == ActionType.ASSERT_TEXT:
                content = await self.page.content()
                if value not in content:
                    execution_status = TestExecutionStatus.FAILED
                    is_bug = True
                    error_msg = f"AssertionError: Expected text '{value}' not found in page content."

            elif step.action == ActionType.ASSERT_URL:
                if value not in self.page.url:
                    execution_status = TestExecutionStatus.FAILED
                    is_bug = True
                    error_msg = f"AssertionError: Expected URL containing '{value}', got '{self.page.url}'"

            # Collect errors captured during this action execution step
            c_errs, n_errs = self.listener.get_and_clear_logs()
            duration = (time.time() - start_time) * 1000

            # Distinguish genuine application uncaught crashes from background telemetry warnings
            uncaught_crashes = [c for c in c_errs if "UNCAUGHT" in c.upper() or "CRASH" in c.upper() or "ERROR" in c.upper()]
            http_500_errs = [n for n in n_errs if "500" in n or "502" in n or "503" in n]

            if uncaught_crashes or http_500_errs:
                execution_status = TestExecutionStatus.FAILED
                is_bug = True
                error_msg = error_msg or f"Captured {len(uncaught_crashes)} uncaught JS crashes and {len(http_500_errs)} HTTP 500 server errors"

            return StepResult(
                step_id=step.step_id,
                success=(execution_status == TestExecutionStatus.PASSED),
                status=execution_status,
                nav_status=nav_status,
                error_message=error_msg,
                console_errors=c_errs,
                network_errors=n_errs,
                duration_ms=duration,
                is_application_bug=is_bug
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            c_errs, n_errs = self.listener.get_and_clear_logs()
            err_str = str(e)
            
            # Classify exception type
            if "Timeout" in err_str:
                nav_status = NavigationStatus.NAVIGATION_TIMEOUT
                execution_status = TestExecutionStatus.INFRASTRUCTURE_ERROR
                is_bug = False
            else:
                execution_status = TestExecutionStatus.FAILED
                is_bug = "AssertionError" in err_str or "500" in err_str

            return StepResult(
                step_id=step.step_id,
                success=False,
                status=execution_status,
                nav_status=nav_status,
                error_message=err_str,
                console_errors=c_errs,
                network_errors=n_errs,
                duration_ms=duration,
                is_application_bug=is_bug
            )
