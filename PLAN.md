# ChaosPilot: Autonomous AI QA & Bug-Hunting Engineer
## Implementation Plan (PLAN.md) — PLAN Phase

> **Phase**: PLAN  
> **Status**: In Execution  
> **Version**: 1.0.0 (V1 Scope)  
> **Framework**: Addy Osmani Agent Engineering Workflow (DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP)

---

## 1. Project Directory Layout

```
ChaosPilot/
├── SPEC.md                      # Approved product & technical specification
├── PLAN.md                      # This implementation plan document
├── pyproject.toml               # Python dependencies & build config
├── requirements.txt             # Fast installation dependencies
├── pytest.ini                   # Pytest configuration
├── Dockerfile                   # Single-container / multi-stage build setup
├── docker-compose.yml           # Backend + Frontend compose setup
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules
│
├── app/                         # Backend Python Application
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint
│   ├── config.py                # Pydantic Settings & environment variables
│   │
│   ├── db/                      # Persistence Layer
│   │   ├── __init__.py
│   │   ├── database.py          # Async SQLite engine & SQLModel sessions
│   │   └── models.py            # SQLite database models
│   │
│   ├── models/                  # Core Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── state.py             # LangGraph ChaosPilotState & schemas
│   │   ├── sitemap.py           # Route & Form element models
│   │   ├── testplan.py          # TestCase, TestStep, TestCategory models
│   │   └── bugreport.py         # BugReport, BugSeverity, StepResult models
│   │
│   ├── safety/                  # Safety & Guardrail System
│   │   ├── __init__.py
│   │   ├── domain_lock.py       # Domain URL whitelist validator
│   │   ├── action_interceptor.py# Destructive action regex matcher
│   │   └── payload_sanitizer.py # Synthetic data & PII filter
│   │
│   ├── tools/                   # Agent Tools (Playwright & Evidence)
│   │   ├── __init__.py
│   │   ├── browser_manager.py   # Async Playwright browser context manager
│   │   ├── navigator.py         # Navigation & AXTree extractor tool
│   │   ├── executor.py          # Click, fill, press UI action runner
│   │   ├── listener.py          # Console log & 4xx/5xx network listener
│   │   ├── evidence.py          # Screenshots, HAR, trace recorder
│   │   └── script_generator.py # Python reproduction script generator
│   │
│   ├── agents/                  # LangGraph Node Agents
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph workflow builder & state graph
│   │   ├── explorer.py          # Discovery Node (Explorer Agent)
│   │   ├── planner.py           # Planner Node (Test Planner Agent)
│   │   ├── runner.py            # Executor Node (Test Runner Agent)
│   │   ├── triage.py            # Triage Node (Bug Triage Agent)
│   │   └── reporter.py          # Reporter Node (Report Generator Agent)
│   │
│   └── api/                     # FastAPI Endpoints & WebSockets
│       ├── __init__.py
│       ├── runs.py              # Launch, status, cancel test runs
│       ├── bugs.py              # List & download bug reports / artifacts
│       └── websocket.py         # Live streaming run events to UI
│
├── frontend/                    # React + Vite + Tailwind Web UI
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/          # React components
│       │   ├── Navbar.jsx
│       │   ├── NewRunModal.jsx
│       │   ├── RunList.jsx
│       │   ├── RunDetail.jsx
│       │   ├── LiveLogViewer.jsx
│       │   ├── SiteMapTree.jsx
│       │   ├── BugCard.jsx
│       │   └── EvidenceViewer.jsx
│       ├── api/                 # Axios / Fetch client
│       │   └── client.js
│       └── types/               # JS/JSDoc types matching state
│
└── tests/                       # Automated Test Suite
    ├── conftest.py              # Pytest fixtures & mock browser setup
    ├── mock_app/                # Sample target web app with deliberate bugs
    │   └── app.py               # Tiny FastAPI app containing intentional bugs
    ├── test_safety.py           # Guardrail unit tests
    ├── test_browser_tools.py    # Playwright browser tools tests
    ├── test_agents.py           # LangGraph agents & state transition tests
    └── test_api.py              # FastAPI endpoint integration tests
```

---

## 2. Implementation Milestones & Task Breakdown

### Milestone 1: Core Foundation & Dependencies (BUILD Phase Start)
- [ ] Create `requirements.txt` with FastAPI, LangGraph, LangChain, `langchain-google-genai`, Playwright, SQLModel, Uvicorn, and Pytest.
- [ ] Initialize Python virtual environment `.venv` dependencies and install Playwright Chromium browser (`playwright install chromium`).
- [ ] Scaffold `frontend/` using Vite + React + Tailwind CSS.
- [ ] Create `.env.example` and `app/config.py` for Settings management.

### Milestone 2: Pydantic Data Models & SQLite Persistence
- [ ] Implement `app/models/` schemas (`state.py`, `sitemap.py`, `testplan.py`, `bugreport.py`).
- [ ] Implement `app/db/database.py` and `app/db/models.py` for SQLite run tracking.

### Milestone 3: Safety Guardrails Engine
- [ ] Implement `DomainLock` (`app/safety/domain_lock.py`).
- [ ] Implement `ActionInterceptor` (`app/safety/action_interceptor.py`).
- [ ] Implement `PayloadSanitizer` (`app/safety/payload_sanitizer.py`).
- [ ] Write unit tests for safety guardrails in `tests/test_safety.py`.

### Milestone 4: Playwright Browser Engine & Tools
- [ ] Implement `BrowserManager` (`app/tools/browser_manager.py`) with async Playwright lifecycle.
- [ ] Implement `Navigator` & Accessibility Tree (AXTree) parser (`app/tools/navigator.py`).
- [ ] Implement `ConsoleNetworkListener` (`app/tools/listener.py`) for uncaught errors & HTTP 4xx/5xx interception.
- [ ] Implement `UIExecutor` (`app/tools/executor.py`) with element reference ID binding.
- [ ] Implement `EvidenceRecorder` (`app/tools/evidence.py`) for screenshots, traces, and HAR logs.
- [ ] Implement `ReproductionScriptGenerator` (`app/tools/script_generator.py`).

### Milestone 5: LangGraph Agents Architecture
- [ ] Implement `ExplorerAgent` (`app/agents/explorer.py`).
- [ ] Implement `TestPlannerAgent` (`app/agents/planner.py`) using Gemini API.
- [ ] Implement `TestRunnerAgent` (`app/agents/runner.py`).
- [ ] Implement `BugTriageAgent` (`app/agents/triage.py`).
- [ ] Implement `ReportGeneratorAgent` (`app/agents/reporter.py`).
- [ ] Assemble `ChaosPilotStateGraph` (`app/agents/graph.py`).

### Milestone 6: FastAPI Backend & Real-time WebSockets
- [ ] Implement `/api/runs` endpoints for starting, listing, and retrieving runs.
- [ ] Implement `/api/bugs` endpoints for retrieving bug reports and downloading evidence artifacts.
- [ ] Implement `/ws/runs/{run_id}` WebSocket endpoint for streaming state updates to the UI.

### Milestone 7: React + Vite + Tailwind Dashboard UI
- [ ] Build clean, dark-themed dashboard with navbar, summary metrics, and active runs list.
- [ ] Build New Run modal to input target URL, max depth, max pages, and auth seed credentials.
- [ ] Build Run Detail view with interactive SiteMap visualization, real-time agent log stream, and test plan table.
- [ ] Build Bug Details modal showing reproduction steps, console/network error traces, and embedded screenshots/traces.

### Milestone 8: End-to-End Verification & Mock Bug Hunting (VERIFY Phase)
- [ ] Build `tests/mock_app/app.py` containing deliberate web app bugs:
  - Uncaught JS error on button click
  - HTTP 500 error on form submit with special characters
  - Missing field validation causing empty state crash
  - Long input boundary overflow bug
- [ ] Run full ChaosPilot test suite against `mock_app` using `pytest`.
- [ ] Verify that ChaosPilot autonomously discovers `mock_app`, generates test cases, catches all 4 intentional bugs, captures evidence, and outputs valid reproduction scripts.

### Milestone 9: Review, Optimization & Containerization (REVIEW & SHIP Phases)
- [ ] Create single multi-stage `Dockerfile` and `docker-compose.yml`.
- [ ] Add GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- [ ] Final code cleanup, linting, and documentation updates.

---

## 3. Verification Criteria (Definition of Done)

1. `pytest` passes 100% of unit and integration tests.
2. ChaosPilot runs end-to-end against the mock test application without human intervention.
3. Every detected bug includes:
   - Screenshot PNG file
   - Runnable standalone `.py` script reproducing the exact steps
   - Complete console and network error logs
4. React frontend loads cleanly, connects to WebSocket, and displays live progress without errors.

---

**Next Action**: Proceed directly to **BUILD** Phase starting with Milestone 1.
