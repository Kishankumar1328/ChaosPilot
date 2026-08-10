import json
import logging
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.models.state import ChaosPilotState, RunStatus
from app.models.testplan import TestCase, TestStep, TestCategory, ActionType
from app.safety.payload_sanitizer import PayloadSanitizer

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are ChaosPilot's Test Planner Agent.
Your job is to inspect a SiteMap of web routes and forms, then generate a comprehensive, risk-based test suite.

For each route and form in the SiteMap, create:
1. FUNCTIONAL tests (valid user paths)
2. NEGATIVE tests (empty required fields, invalid formats)
3. BOUNDARY tests (5000+ character strings, XSS payloads like `<script>alert(1)</script>`, special characters)
4. CHAOS tests (rapid submit button actions, boundary state tests)

Return JSON format matching:
[
  {
    "id": "TC-01",
    "title": "Submit Contact Form with Long Overflow String",
    "description": "Boundary testing for form input overflow",
    "category": "BOUNDARY",
    "target_route": "https://example.com/contact",
    "steps": [
      {"step_id": "S1", "action": "NAVIGATE", "target_selector": null, "value": "https://example.com/contact", "expected_outcome": "Page loads successfully"},
      {"step_id": "S2", "action": "FILL", "target_selector": "#name", "value": "AAAAAA...", "expected_outcome": "Input accepts or truncates overflow string"},
      {"step_id": "S3", "action": "CLICK", "target_selector": "button[type='submit']", "value": null, "expected_outcome": "Form submits without 500 error"}
    ]
  }
]
"""

async def planner_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Planner Node (Test Planner Agent):
    Analyzes discovered SiteMap and generates risk-based test cases.
    """
    state.status = RunStatus.PLANNING
    state.logs.append("📋 [TestPlannerAgent] Analyzing SiteMap to generate risk-based test plan...")
    logger.info(f"TestPlannerAgent running for run {state.run_id}")

    test_plan: List[TestCase] = []

    # Check if Gemini API Key is present for LLM-driven planning
    if settings.GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL_PRO,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2
            )
            sitemap_summary = json.dumps(
                {url: node.model_dump() for url, node in state.site_map.items()},
                default=str
            )
            
            messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=f"SiteMap Data:\n{sitemap_summary}")
            ]
            response = await llm.ainvoke(messages)
            content = response.content
            
            # Clean JSON formatting
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            raw_cases = json.loads(content)
            for tc in raw_cases:
                test_plan.append(TestCase(**tc))
                
            state.logs.append(f"🤖 [TestPlannerAgent] Gemini generated {len(test_plan)} intelligent test cases.")
        except Exception as e:
            logger.warning(f"Gemini LLM planning failed or fallback required: {e}")
            state.logs.append(f"⚠️ [TestPlannerAgent] LLM generation note: {e}. Falling back to Rule-Engine planner.")

    # Rule-Driven Fallback / Rule-Engine Test Planner
    if not test_plan:
        tc_count = 1
        for url, route in state.site_map.items():
            # 1. Functional Navigation Test
            test_plan.append(TestCase(
                id=f"TC-{tc_count:02d}",
                title=f"Functional Navigation: {route.title or url}",
                description=f"Verify route opens cleanly without JS errors",
                category=TestCategory.FUNCTIONAL,
                target_route=url,
                steps=[
                    TestStep(
                        step_id="S1",
                        action=ActionType.NAVIGATE,
                        value=url,
                        expected_outcome="Route loads cleanly with HTTP 200"
                    )
                ]
            ))
            tc_count += 1

            # 2. Form Boundary & Negative Tests for each form element
            for form in route.forms:
                if form.element_type in ["text", "textarea", "email"]:
                    # Boundary Overflow Test
                    test_plan.append(TestCase(
                        id=f"TC-{tc_count:02d}",
                        title=f"Boundary Test on {form.selector}",
                        description="Test 5000 character overflow string handling",
                        category=TestCategory.BOUNDARY,
                        target_route=url,
                        steps=[
                            TestStep(step_id="S1", action=ActionType.NAVIGATE, value=url, expected_outcome="Page loaded"),
                            TestStep(
                                step_id="S2",
                                action=ActionType.FILL,
                                target_selector=form.selector,
                                value=PayloadSanitizer.get_boundary_string("OVERFLOW_STRING"),
                                expected_outcome="Input field handles long string safely"
                            )
                        ]
                    ))
                    tc_count += 1

                    # Negative Special Character / XSS Test
                    test_plan.append(TestCase(
                        id=f"TC-{tc_count:02d}",
                        title=f"Negative Injection Test on {form.selector}",
                        description="Inject special character validation string",
                        category=TestCategory.NEGATIVE,
                        target_route=url,
                        steps=[
                            TestStep(step_id="S1", action=ActionType.NAVIGATE, value=url, expected_outcome="Page loaded"),
                            TestStep(
                                step_id="S2",
                                action=ActionType.FILL,
                                target_selector=form.selector,
                                value=PayloadSanitizer.get_boundary_string("SPECIAL_CHARS"),
                                expected_outcome="Input handles special chars without throwing JS unhandled error"
                            )
                        ]
                    ))
                    tc_count += 1

        state.logs.append(f"✅ [TestPlannerAgent] Rule-Engine generated {len(test_plan)} structured test cases.")

    state.test_plan = test_plan
    return state
