from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class BugSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # Uncaught 500 error, page crash, fatal exception
    HIGH = "HIGH"          # Data corruption, unhandled JS promise rejection
    MEDIUM = "MEDIUM"        # Form submit fails silently, HTTP 4xx on valid action
    LOW = "LOW"           # Minor UI layout or console warning

class StepResult(BaseModel):
    step_id: str
    success: bool
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    console_errors: List[str] = Field(default_factory=list)
    network_errors: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0

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
