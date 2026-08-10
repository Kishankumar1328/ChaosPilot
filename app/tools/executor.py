import time
import logging
from typing import Optional, List, Tuple
from playwright.async_api import Page
from app.models.testplan import ActionType, TestStep
from app.models.bugreport import StepResult
from app.safety.action_interceptor import ActionInterceptor
from app.tools.listener import ConsoleNetworkListener

logger = logging.getLogger(__name__)

class UIExecutor:
    """
    Executes individual TestSteps via Playwright, enforcing safety guardrails
    and capturing step duration and console/network logs.
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
                error_message=f"GUARDRAIL_BLOCKED: {reason}",
                duration_ms=duration
            )

        # 2. Execute Playwright Action
        try:
            if step.action == ActionType.NAVIGATE:
                await self.page.goto(value or selector, wait_until="networkidle", timeout=10000)

            elif step.action == ActionType.CLICK:
                await self.page.click(selector, timeout=5000)

            elif step.action == ActionType.FILL:
                await self.page.fill(selector, value, timeout=5000)

            elif step.action == ActionType.SELECT:
                await self.page.select_option(selector, value, timeout=5000)

            elif step.action == ActionType.CHECK:
                await self.page.check(selector, timeout=5000)

            elif step.action == ActionType.PRESS:
                await self.page.press(selector, value or "Enter", timeout=5000)

            elif step.action == ActionType.ASSERT_TEXT:
                content = await self.page.content()
                if value not in content:
                    raise AssertionError(f"Expected text '{value}' not found in page content.")

            elif step.action == ActionType.ASSERT_URL:
                if value not in self.page.url:
                    raise AssertionError(f"Expected URL to contain '{value}', got '{self.page.url}'")

            # Collect errors captured during this action execution step
            c_errs, n_errs = self.listener.get_and_clear_logs()
            duration = (time.time() - start_time) * 1000

            has_error = len(c_errs) > 0 or len(n_errs) > 0
            return StepResult(
                step_id=step.step_id,
                success=not has_error,
                error_message=f"Captured {len(c_errs)} console errors and {len(n_errs)} network errors" if has_error else None,
                console_errors=c_errs,
                network_errors=n_errs,
                duration_ms=duration
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            c_errs, n_errs = self.listener.get_and_clear_logs()
            return StepResult(
                step_id=step.step_id,
                success=False,
                error_message=str(e),
                console_errors=c_errs,
                network_errors=n_errs,
                duration_ms=duration
            )
