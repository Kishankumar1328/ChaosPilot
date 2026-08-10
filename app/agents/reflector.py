import logging
from typing import List, Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.models.state import ChaosPilotState, RunStatus
from app.models.testplan import TestCase, TestStep, ActionType

logger = logging.getLogger(__name__)

class CorrectionPlan(BaseModel):
    obstacle_description: str
    suggested_corrective_action: str  # CLICK_MODAL_CLOSE, SCROLL_INTO_VIEW, WAIT_NETWORK, DISMISS_OVERLAY
    target_selector: Optional[str] = None

REFLECT_PROMPT = """You are ChaosPilot's Self-Healing & Reflection Agent.
A test step encountered an unexpected obstacle or execution failure during browser automation.

Analyze the step error and generate a corrective action plan:
- Obstacle types: Dynamic modal overlay, sticky banner, delayed network load, hidden selector.
- Corrective actions: CLICK_MODAL_CLOSE, SCROLL_INTO_VIEW, WAIT_NETWORK, DISMISS_OVERLAY
"""

async def reflect_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Reflect Node (Self-Healing Agent):
    Evaluates execution failures, generates dynamic self-healing steps,
    and updates the test plan to retry failed execution gracefully.
    """
    state.logs.append("🔄 [ReflectNode] Agent reflection & self-healing triggered for failed execution steps...")
    logger.info(f"ReflectNode running for run {state.run_id}")

    healed_count = 0

    for tc in state.test_plan:
        results = state.execution_results.get(tc.id, [])
        failed_result = next((r for r in results if not r.success), None)

        if failed_result and "GUARDRAIL_BLOCKED" not in (failed_result.error_message or ""):
            # Reflection reasoning
            failed_step = next((s for s in tc.steps if s.step_id == failed_result.step_id), None)
            if failed_step:
                state.logs.append(f"🧠 [ReflectNode] Reflecting on failure in {tc.id} Step {failed_step.step_id}: {failed_result.error_message}")
                
                # Check LLM for intelligent self-healing
                corrective_step = None
                if settings.GEMINI_API_KEY:
                    try:
                        llm = ChatGoogleGenerativeAI(
                            model=settings.GEMINI_MODEL_FAST,
                            google_api_key=settings.GEMINI_API_KEY
                        )
                        structured_llm = llm.with_structured_output(CorrectionPlan)
                        plan: CorrectionPlan = await structured_llm.ainvoke([
                            SystemMessage(content=REFLECT_PROMPT),
                            HumanMessage(content=f"Failed Step: {failed_step.model_dump_json()}\nError: {failed_result.error_message}")
                        ])

                        if plan.target_selector:
                            corrective_step = TestStep(
                                step_id=f"HEAL_{failed_step.step_id}",
                                action=ActionType.CLICK,
                                target_selector=plan.target_selector,
                                expected_outcome="Dismiss obstacle overlay"
                            )
                    except Exception as e:
                        logger.warning(f"ReflectNode Gemini LLM reasoning note: {e}")

                # Rule-engine self-healing fallback
                if not corrective_step:
                    corrective_step = TestStep(
                        step_id=f"HEAL_{failed_step.step_id}",
                        action=ActionType.NAVIGATE,
                        value=tc.target_route,
                        expected_outcome="Reset navigation to clean route state"
                    )

                # Inject self-healing step before the failed step
                idx = tc.steps.index(failed_step)
                tc.steps.insert(idx, corrective_step)
                healed_count += 1
                state.logs.append(f"🛠️ [ReflectNode] Injected self-healing step '{corrective_step.step_id}' into {tc.id}")

    if healed_count > 0:
        state.logs.append(f"✨ [ReflectNode] Self-healing complete. Modified {healed_count} test paths.")
    else:
        state.logs.append("ℹ️ [ReflectNode] No recoverable dynamic obstacles found during reflection.")

    return state
