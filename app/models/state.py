from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.sitemap import RouteNode
from app.models.testplan import TestCase
from app.models.bugreport import BugReport, StepResult

class RunStatus(str, Enum):
    IDLE = "IDLE"
    DISCOVERING = "DISCOVERING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    TRIAGING = "TRIAGING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ChaosPilotState(BaseModel):
    run_id: str
    target_url: str
    max_depth: int = 3
    max_pages: int = 25
    status: RunStatus = RunStatus.IDLE
    
    # Discovery data
    site_map: Dict[str, RouteNode] = Field(default_factory=dict)
    visited_urls: List[str] = Field(default_factory=list)
    
    # Test plan data
    test_plan: List[TestCase] = Field(default_factory=list)
    current_test_index: int = 0
    
    # Execution & triage tracking
    execution_results: Dict[str, List[StepResult]] = Field(default_factory=dict)
    discovered_bugs: List[BugReport] = Field(default_factory=list)
    
    # Real-time event log stream for WebSockets
    logs: List[str] = Field(default_factory=list)
    error_summary: Optional[str] = None
