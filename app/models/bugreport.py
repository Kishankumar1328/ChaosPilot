from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class NavigationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    TARGET_UNREACHABLE = "TARGET_UNREACHABLE"
    DNS_FAILURE = "DNS_FAILURE"
    TLS_FAILURE = "TLS_FAILURE"
    HTTP_ERROR = "HTTP_ERROR"
    NAVIGATION_TIMEOUT = "NAVIGATION_TIMEOUT"
    BROWSER_ERROR = "BROWSER_ERROR"
    CHAOSPILOT_ERROR = "CHAOSPILOT_ERROR"

class TestExecutionStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    NOT_EXECUTED = "NOT_EXECUTED"

class BugSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # Uncaught 500 error, page crash, fatal exception
    HIGH = "HIGH"          # Data corruption, unhandled JS promise rejection
    MEDIUM = "MEDIUM"        # Form submit fails silently, HTTP 4xx on valid action
    LOW = "LOW"           # Minor UI layout or console warning

class StepResult(BaseModel):
    step_id: str
    success: bool
    status: TestExecutionStatus = TestExecutionStatus.PASSED
    nav_status: NavigationStatus = NavigationStatus.SUCCESS
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    console_errors: List[str] = Field(default_factory=list)
    network_errors: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    is_application_bug: bool = False

class ExecutionIssue(BaseModel):
    id: str  # e.g. CHAOSPILOT-EXEC-001
    title: str
    reason: str
    target_url: str
    stage: str
    nav_status: NavigationStatus
    blocked_tests_count: int = 0
    confirmed_bugs_count: int = 0

class BugReport(BaseModel):
    id: str
    title: str
    severity: BugSeverity
    route: str
    failed_step_id: str
    description: str
    reproduction_steps: List[str] = Field(default_factory=list)
    console_logs: List[str] = Field(default_factory=list)
    network_logs: List[str] = Field(default_factory=list)
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    har_path: Optional[str] = None
    reproduction_script_path: Optional[str] = None
    root_cause_analysis: Optional[Any] = None
