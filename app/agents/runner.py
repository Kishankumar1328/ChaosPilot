import logging
from app.models.state import ChaosPilotState, RunStatus
from app.safety.domain_lock import DomainLock
from app.safety.action_interceptor import ActionInterceptor
from app.tools.browser_manager import BrowserManager
from app.tools.executor import UIExecutor
from app.db.memory import MemoryManager

logger = logging.getLogger(__name__)

async def runner_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Executor Node (Test Runner Agent):
    Executes each generated TestCase using Playwright and records memory of successful interactions.
    """
    state.status = RunStatus.EXECUTING
    state.logs.append(f"🚀 [TestRunnerAgent] Starting execution of {len(state.test_plan)} test cases...")
    logger.info(f"TestRunnerAgent running for run {state.run_id}")

    domain_lock = DomainLock(state.target_url)
    interceptor = ActionInterceptor(allow_destructive=False)
    browser_mgr = BrowserManager()
    await browser_mgr.start(headless=True)

    try:
        executor = UIExecutor(browser_mgr.page, browser_mgr.listener, interceptor)

        for tc in state.test_plan:
            state.logs.append(f"▶️ [TestRunnerAgent] Executing {tc.id}: '{tc.title}' ({tc.category.value})")
            step_results = []

            for step in tc.steps:
                result = await executor.execute_step(step)
                step_results.append(result)

                if result.success:
                    # Persist successful action to Episodic Memory
                    try:
                        await MemoryManager.record_successful_action(
                            route_url=tc.target_route,
                            action_type=step.action.value,
                            selector=step.target_selector or "route",
                            payload=step.value
                        )
                    except Exception as e:
                        logger.debug(f"Memory logging note: {e}")
                else:
                    state.logs.append(f"⚠️ [TestRunnerAgent] Anomaly detected in {tc.id} Step {step.step_id}: {result.error_message}")
                    if result.console_errors:
                        state.logs.append(f"   Console Log: {result.console_errors[0]}")
                    if result.network_errors:
                        state.logs.append(f"   Network Log: {result.network_errors[0]}")

            state.execution_results[tc.id] = step_results

        state.logs.append(f"✅ [TestRunnerAgent] Test suite execution complete.")

    except Exception as e:
        logger.error(f"TestRunnerAgent execution error: {e}")
        state.logs.append(f"❌ [TestRunnerAgent] Fatal execution error: {str(e)}")
        state.error_summary = str(e)
    finally:
        await browser_mgr.close()

    return state
