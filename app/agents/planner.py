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
"""

async def planner_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Planner Node (Test Planner Agent):
    Analyzes discovered SiteMap and generates risk-based test cases.
    Falls back gracefully to heuristic rule-based planning on LLM quota limits.
    """
    state.status = RunStatus.PLANNING
    state.logs.append("📋 [TestPlannerAgent] Analyzing SiteMap to generate risk-based test plan...")
    logger.info(f"TestPlannerAgent running for run {state.run_id}")

    test_plan: List[TestCase] = []

    # Check if Gemini API Key is present for LLM-driven planning
    if settings.GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL_FAST,
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
            for rc in raw_cases:
                tc = TestCase(**rc)
                test_plan.append(tc)

            state.logs.append(f"✅ [TestPlannerAgent] Generated {len(test_plan)} LLM-driven risk-based test cases.")

        except Exception as e:
            logger.warning(f"LLM planner note ({e}). Switching to Heuristic Rule Engine.")
            state.logs.append(f"ℹ️ [TestPlannerAgent] LLM unavailable/rate-limited. Executing Heuristic Rule Engine...")

    # Heuristic Rule Engine Fallback (Guarantees test suite generation for any site)
    if not test_plan:
        tc_count = 1
        for route_url, route_node in state.site_map.items():
            # 1. Functional Route Navigation Test
            test_plan.append(TestCase(
                id=f"TC-FUNC-{tc_count:02d}",
                title=f"Functional Route Exploration for {route_node.title or route_url}",
                description=f"Navigates to route {route_url} and verifies clean 200 HTTP response.",
                category=TestCategory.FUNCTIONAL,
                target_route=route_url,
                steps=[
                    TestStep(
                        step_id="S1",
                        action=ActionType.NAVIGATE,
                        value=route_url,
                        expected_outcome="Page loads cleanly without unhandled exceptions"
                    )
                ]
            ))
            tc_count += 1

            # 2. Form Boundary & Chaos Tests
            for form in route_node.forms:
                if form.element_type in ["text", "textarea", "email"]:
                    test_plan.append(TestCase(
                        id=f"TC-BOUND-{tc_count:02d}",
                        title=f"Boundary Input Overflow Test on {form.selector}",
                        description=f"Fills {form.selector} with 1,000+ character string to test buffer overflow resilience.",
                        category=TestCategory.BOUNDARY,
                        target_route=route_url,
                        steps=[
                            TestStep(
                                step_id="S1",
                                action=ActionType.NAVIGATE,
                                value=route_url,
                                expected_outcome="Route loaded"
                            ),
                            TestStep(
                                step_id="S2",
                                action=ActionType.FILL,
                                target_selector=form.selector,
                                value="A" * 1000,
                                expected_outcome="Input accepts or truncates long string"
                            )
                        ]
                    ))
                    tc_count += 1

            # 3. Interactive Selector Chaos Click Tests
            for sel in route_node.interactive_selectors[:3]:
                test_plan.append(TestCase(
                    id=f"TC-CHAOS-{tc_count:02d}",
                    title=f"Interactive Click Stress Test on {sel}",
                    description=f"Simulates user click interaction on selector {sel}.",
                    category=TestCategory.CHAOS,
                    target_route=route_url,
                    steps=[
                        TestStep(
                            step_id="S1",
                            action=ActionType.NAVIGATE,
                            value=route_url,
                            expected_outcome="Route loaded"
                        ),
                        TestStep(
                            step_id="S2",
                            action=ActionType.CLICK,
                            target_selector=sel,
                            expected_outcome="Element handles click without throwing JS exception"
                        )
                    ]
                ))
                tc_count += 1

        state.logs.append(f"✅ [TestPlannerAgent] Generated {len(test_plan)} heuristic risk-based test cases.")

    state.test_plan = test_plan
    return state
