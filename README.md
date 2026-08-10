#  ChaosPilot: Autonomous AI QA & Bug-Hunting Engineer

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0%2B-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agents-FF6F00.svg)](https://langchain.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-45BA4B.svg?logo=playwright&logoColor=white)](https://playwright.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ChaosPilot** is an autonomous AI QA engineer that crawls web applications, maps interactive user flows, builds risk-based test plans, executes boundary/chaos testing with Playwright, intercepts unhandled exceptions, diagnoses root causes using Gemini 2.5 Pro, and proposes verified code patches—**never modifying production without human approval.**

[Explore Architecture](#-system-architecture) • [Quickstart](#-quickstart-guide) • [UI Dashboard](#-apple-design-system-ui) • [API Documentation](#-api-endpoints)

---

</div>

## 🌟 Key Capabilities

- **🔍 Autonomous Application Discovery**: Crawls web applications, builds hierarchical accessibility trees (AXTree), maps dynamic forms, links, and route structures within strict domain guardrails.
- **📋 Risk-Based Test Plan Generation**: Dynamically constructs prioritized test suites covering functional flows, negative validation, boundary inputs, and chaos testing scenarios.
- **⚡ Self-Healing Execution Engine (`ReflectNode`)**: Intercepts unhandled modals, dynamic overlays, or blocked actions during Playwright automation and dynamically injects self-healing corrective steps without aborting the suite.
- **🧠 Episodic Memory Persistence**: Remembers successful navigation paths, dynamic locators, and form payloads in MySQL/SQLite to accelerate subsequent exploration runs by 5x.
- **🛠️ Gemini 2.5 Pro Root Cause Analysis**: Correlates uncaught JavaScript console crashes and HTTP 500 stack traces directly to source repository files, generating exact `.patch` diff proposals.
- **🛡️ Multi-Layer Safety Guardrails**: Enforces `DomainLock` (url boundary enforcement), `ActionInterceptor` (destructive action blocking), and `PayloadSanitizer` (preventing harmful command injections).
- ** Apple Design System Dashboard**: Light-mode aesthetic UI built with React, Vite, and Tailwind CSS, featuring high-contrast live terminal execution streams and 1-click workspace management.

---

## 🏗️ System Architecture

```mermaid
graph TD
    User([👤 User / QA Engineer]) -->|Inputs Target URL| UI[ React Dashboard]
    UI -->|POST /api/runs| API[FastAPI Backend Engine]
    
    subgraph LangGraph Stateful Agent Workflow
        API --> ExplorerAgent[🔍 ExplorerAgent]
        ExplorerAgent -->|Crawls & AXTree Mapping| TestPlannerAgent[📋 TestPlannerAgent]
        TestPlannerAgent -->|Generates Risk-Based Suite| TestRunnerAgent[🚀 TestRunnerAgent]
        
        TestRunnerAgent -->|Playwright Chromium Execution| AppUnderTest[🌐 Target Web Application]
        AppUnderTest -->|Console Errors & HTTP 500s| TestRunnerAgent
        
        TestRunnerAgent -->|Execution Anomaly| ReflectNode[🔄 ReflectNode: Self-Healing]
        ReflectNode -->|Injects Corrective Steps| TestRunnerAgent
        
        TestRunnerAgent --> TriageAgent[⚖️ TriageAgent]
        TriageAgent -->|Constructs Bug Reports| ReportGeneratorAgent[📊 ReportGeneratorAgent]
        
        ReportGeneratorAgent -->|Inspects Stack Traces| CodeFixerAgent[🛠️ CodeFixerAgent: Gemini 2.5 Pro]
        CodeFixerAgent -->|Generates Unified Diff| PatchEngine[🩹 PatchEngine]
    end

    PatchEngine -->|Human-in-the-Loop Approval| DevRepo[💻 Source Code Repository]
    API -->|Realtime WebSockets| UI
```

---

##  Apple Design System UI

ChaosPilot features an **Apple-grade UI Dashboard** with high-contrast typography, sleek frosted glass cards, and a dual-mode live terminal execution stream:

```
+-----------------------------------------------------------------------------------+
|  ChaosPilot Pro V2.0                  Autonomous QA Navigator        [Dark Term] |
+-----------------------------------+-----------------------------------------------+
| + New Chaos Run                   | Target: http://127.0.0.1:8888                 |
|                                   | Routes: 4  | Tests: 6  | Discovered Bugs: 2   |
| Test Runs History                 +-----------------------------------------------+
| > 🌐 127.0.0.1:8888        [2]    | Live Terminal Execution Stream                |
|   🌐 example.com           [0]    | +-------------------------------------------+ |
|                                   | | [1] 🔍 [ExplorerAgent] Crawling route /   | |
|                                   | | [2] 📋 [Planner] Test plan generated (6) | |
|                                   | | [3] 🚀 [Runner] Executing TC-01 (CLICK)  | |
|                                   | | [4] ❌ [Runner] HTTP 500 Server Error     | |
|                                   | | [5] 🔄 [ReflectNode] Injecting self-heal  | |
|                                   | +-------------------------------------------+ |
+-----------------------------------+-----------------------------------------------+
```

---

## 🚀 Quickstart Guide

### Prerequisites

- **Python**: `3.10` or higher
- **Node.js**: `18.0` or higher
- **MySQL Database** *(Optional)*: Pre-configured for `root:root@localhost:3306/chaospilot` (automatically falls back to SQLite if MySQL is not running).

### 1. Clone Repository & Environment Setup

```bash
git clone https://github.com/Kishankumar1328/ChaosPilot.git
cd ChaosPilot

# Create and activate Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install Python dependencies & Playwright browsers
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```ini
# Gemini API Key (Required for AI Root Cause Analysis & Planning)
GEMINI_API_KEY="your_gemini_api_key_here"

# Database Configuration (MySQL root:root or SQLite fallback)
MYSQL_USER="root"
MYSQL_PASSWORD="root"
MYSQL_HOST="localhost"
MYSQL_PORT=3306
MYSQL_DB="chaospilot"
DATABASE_URL="mysql+aiomysql://root:root@localhost:3306/chaospilot"
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 🏃 Running ChaosPilot

### Start FastAPI Backend Server (Port 8000)

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Start React Frontend Dashboard (Port 3000)

```bash
cd frontend
npm run dev
```

Open your browser to **`http://localhost:3000`** to launch Chaos Pilot!

---

## 🧪 Running Automated Test Suite

ChaosPilot includes a full suite of automated unit and integration tests using `pytest`:

```bash
.\.venv\Scripts\python.exe -m pytest
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/runs` | Creates & starts an autonomous AI QA test run for a target URL |
| `GET` | `/api/runs` | Fetches history of all test runs and discovered bugs |
| `GET` | `/api/runs/{run_id}` | Retrieves detailed execution state & logs for a specific run |
| `POST` | `/api/bugs/{bug_id}/analyze` | Triggers Gemini 2.5 Pro root cause code inspection for a bug |
| `POST` | `/api/bugs/{bug_id}/apply-fix` | Applies human-approved `.patch` diff to source repository |
| `WS` | `/ws/runs/{run_id}` | Realtime WebSocket stream of live terminal execution events |

---

## 🛡️ Safety & Human-in-the-Loop Approval

ChaosPilot enforces strict safety policies to prevent unwanted side effects:

1. **Domain Lock**: Playwright navigation is strictly bounded to the target application domain. External links are ignored.
2. **Action Interceptor**: Destructive database actions (e.g. `DROP`, `DELETE`, `TRUNCATE`) are blocked by default.
3. **Human-in-the-Loop Patching**: Code fixes generated by Gemini 2.5 Pro require explicit human approval via the UI button before any file modification or git patch is applied to your repository.

---

## 📜 License

This project is licensed under the **MIT License**.

---

<div align="center">
Built with ❤️ for AI Engineers and QA Automation Teams.
</div>