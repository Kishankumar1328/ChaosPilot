from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TestCategory(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    NEGATIVE = "NEGATIVE"
    BOUNDARY = "BOUNDARY"
    CHAOS = "CHAOS"

class ActionType(str, Enum):
    NAVIGATE = "NAVIGATE"
    CLICK = "CLICK"
    FILL = "FILL"
    SELECT = "SELECT"
    CHECK = "CHECK"
    PRESS = "PRESS"
    ASSERT_TEXT = "ASSERT_TEXT"
    ASSERT_URL = "ASSERT_URL"

class TestStep(BaseModel):
    step_id: str
    action: ActionType
    target_selector: Optional[str] = None
    ref_id: Optional[int] = None
    value: Optional[str] = None
    expected_outcome: str

class TestCase(BaseModel):
    id: str
    title: str
    description: str
    category: TestCategory
    target_route: str
    steps: List[TestStep] = Field(default_factory=list)
