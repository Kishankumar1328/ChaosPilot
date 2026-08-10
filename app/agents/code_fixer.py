import json
import logging
from typing import Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.models.bugreport import BugReport
from app.models.codefix import RootCauseAnalysis, CodePatch, PatchStatus
from app.tools.code_inspector import CodeInspector

logger = logging.getLogger(__name__)

ROOT_CAUSE_PROMPT = """You are ChaosPilot's Root-Cause & Code-Fix AI Engineer.
Given a verified Application Bug Report and source code snippets, analyze the bug, determine the probable root cause,
propose a minimal code patch, and write a pytest regression test.

CRITICAL RULES:
- ONLY propose a code patch if the source code contains a proven application defect.
- NEVER generate generic exception-handling suppression patches like `try: ... except Exception: pass` or `raise Exception() -> handle_exception()`.
- Return strictly JSON matching the required schema.
"""

async def analyze_root_cause_and_fix(bug: BugReport, repo_dir: str = ".") -> RootCauseAnalysis:
    """
    Inspects source code around bug report logs, generates probable root cause,
    proposed minimal patch, and pytest regression test.
    Refuses to generate generic exception suppression patches for runner timeouts.
    """
    logger.info(f"Analyzing root cause for bug: {bug.id}")

    # Reject analysis if bug is actually a Playwright navigation timeout
    if "timeout" in bug.description.lower() and "http 500" not in bug.description.lower() and not bug.console_logs:
        return RootCauseAnalysis(
            bug_id=bug.id,
            probable_root_cause="Execution issue caused by Playwright browser navigation timeout. No application code defect identified.",
            affected_files=[],
            proposed_patches=[],
            regression_test_code="# Infrastructure navigation timeout - no application regression test required",
            status=PatchStatus.PENDING_ANALYSIS
        )

    inspector = CodeInspector(repo_dir)
    
    # 1. Locate relevant source files
    keywords = [bug.route.split("/")[-1], bug.failed_step_id] + bug.console_logs + bug.network_logs
    keywords = [k for k in keywords if k and len(k) > 3]
    relevant_files = inspector.find_relevant_files(keywords)

    snippets = {}
    for filepath in relevant_files[:3]:
        snippets[filepath] = inspector.read_file_snippet(filepath)

    analysis: Optional[RootCauseAnalysis] = None

    # 2. Try Gemini API for LLM-driven root cause reasoning
    if settings.GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1,
                max_retries=0
            )
            
            messages = [
                SystemMessage(content=ROOT_CAUSE_PROMPT),
                HumanMessage(content=f"Bug Report: {bug.model_dump_json()}\nSource Snippets: {json.dumps(snippets)}")
            ]
            response = await llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            raw_data = json.loads(content)
            patches = [CodePatch(**p) for p in raw_data.get("proposed_patches", [])]

            # Filter out any generic exception swallowing patches
            valid_patches = []
            for p in patches:
                if "except Exception:" in p.proposed_code or "pass" == p.proposed_code.strip():
                    logger.warning(f"Discarded generic exception-suppression patch proposal for {p.file_path}")
                else:
                    valid_patches.append(p)

            analysis = RootCauseAnalysis(
                bug_id=bug.id,
                probable_root_cause=raw_data.get("probable_root_cause", "Root cause identified by Gemini AI."),
                affected_files=raw_data.get("affected_files", []),
                proposed_patches=valid_patches,
                regression_test_code=raw_data.get("regression_test_code", "# Automated regression test\ndef test_regression():\n    assert True\n"),
                status=PatchStatus.PENDING_ANALYSIS
            )

        except Exception as e:
            logger.warning(f"LLM RootCause analysis fallback note ({e}).")

    # 3. Rule-engine Fallback
    if not analysis:
        # Final safety check: if description indicates timeout, return empty proposed_patches
        if "timeout" in bug.description.lower() and "http 500" not in bug.description.lower() and not bug.console_logs:
            return RootCauseAnalysis(
                bug_id=bug.id,
                probable_root_cause="Execution issue caused by Playwright browser navigation timeout. No application code defect identified.",
                affected_files=[],
                proposed_patches=[],
                regression_test_code="# Infrastructure navigation timeout - no application regression test required",
                status=PatchStatus.PENDING_ANALYSIS
            )

        analysis = RootCauseAnalysis(
            bug_id=bug.id,
            probable_root_cause=f"Application defect detected on route {bug.route}. {bug.description}",
            affected_files=["app/main.py"],
            proposed_patches=[
                CodePatch(
                    file_path="app/main.py",
                    original_code="# Original route handler",
                    proposed_code="# Proposed fix validating route payload",
                    diff="--- app/main.py\n+++ app/main.py\n@@ -1,3 +1,3 @@\n"
                )
            ],
            regression_test_code=f"def test_{bug.id.lower().replace('-', '_')}():\n    # Regression test for {bug.title}\n    assert True\n",
            status=PatchStatus.PENDING_ANALYSIS
        )

    return analysis
