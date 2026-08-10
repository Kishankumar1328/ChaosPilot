import pytest
from app.models.state import ChaosPilotState, RunStatus
from app.models.testplan import TestCase, TestStep, TestCategory, ActionType
from app.models.bugreport import StepResult
from app.agents.reflector import reflect_node
from app.db.memory import MemoryManager

@pytest.mark.asyncio
async def test_reflector_self_healing():
    state = ChaosPilotState(
        run_id="REFLECT-TEST-01",
        target_url="http://127.0.0.1:8888",
        status=RunStatus.EXECUTING,
        test_plan=[
            TestCase(
                id="TC-REFLECT-01",
                title="Test with Dynamic Obstacle",
                description="Simulated step failure",
                category=TestCategory.FUNCTIONAL,
                target_route="http://127.0.0.1:8888/contact",
                steps=[
                    TestStep(step_id="S1", action=ActionType.NAVIGATE, value="http://127.0.0.1:8888/contact", expected_outcome="Navigated"),
                    TestStep(step_id="S2", action=ActionType.CLICK, target_selector="#submit-btn", expected_outcome="Submit")
                ]
            )
        ],
        execution_results={
            "TC-REFLECT-01": [
                StepResult(step_id="S1", success=True),
                StepResult(step_id="S2", success=False, error_message="Element not interactable / blocked by overlay")
            ]
        }
    )

    updated_state = await reflect_node(state)
    tc = updated_state.test_plan[0]
    
    # Verify self-healing step was injected before S2
    assert len(tc.steps) == 3
    assert tc.steps[1].step_id.startswith("HEAL_")

@pytest.mark.asyncio
async def test_episodic_memory_persistence():
    await MemoryManager.record_successful_action(
        route_url="http://127.0.0.1:8888/contact",
        action_type="FILL",
        selector="#name",
        payload="Test User"
    )

    memories = await MemoryManager.recall_domain_memory("http://127.0.0.1:8888")
    assert len(memories) > 0
    assert any(m.selector == "#name" for m in memories)
