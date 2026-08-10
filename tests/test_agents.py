import pytest
from app.models.state import ChaosPilotState, RunStatus
from app.agents.graph import chaospilot_app

@pytest.mark.asyncio
async def test_full_chaospilot_pipeline(mock_server_url):
    initial_state = ChaosPilotState(
        run_id="TEST-RUN-01",
        target_url=mock_server_url,
        max_depth=2,
        max_pages=5
    )

    final_state_dict = await chaospilot_app.ainvoke(initial_state)
    final_state = ChaosPilotState(**final_state_dict) if isinstance(final_state_dict, dict) else final_state_dict

    # Verification assertions
    assert final_state.status in [RunStatus.COMPLETED, RunStatus.COMPLETED_WITH_BUGS, RunStatus.COMPLETED_WITH_BLOCKED_TESTS, RunStatus.TRIAGING]
    assert len(final_state.site_map) > 0
    assert len(final_state.test_plan) > 0
