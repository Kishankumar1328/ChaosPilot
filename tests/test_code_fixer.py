import pytest
from app.models.bugreport import BugReport, BugSeverity
from app.models.codefix import PatchStatus
from app.agents.code_fixer import analyze_root_cause_and_fix

@pytest.mark.asyncio
async def test_code_fixer_analysis():
    sample_bug = BugReport(
        id="BUG-TEST01",
        title="HTTP 500 Unhandled Server Error on Form Submission",
        severity=BugSeverity.CRITICAL,
        route="http://127.0.0.1:8888/contact",
        failed_step_id="S2",
        description="HTTP 500 Unhandled Server Error on Form Submission",
        reproduction_steps=["NAVIGATE -> http://127.0.0.1:8888/contact", "FILL -> #name"],
        console_logs=[],
        network_logs=["HTTP 500 POST -> http://127.0.0.1:8888/submit-contact"]
    )

    analysis = await analyze_root_cause_and_fix(sample_bug, repo_dir=".")

    assert analysis.bug_id == "BUG-TEST01"
    assert analysis.status == PatchStatus.ANALYZED
    assert len(analysis.probable_root_cause) > 0
    assert len(analysis.proposed_patches) > 0
    assert analysis.regression_test_code is not None
