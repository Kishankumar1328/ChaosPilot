from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class PatchStatus(str, Enum):
    PENDING_ANALYSIS = "PENDING_ANALYSIS"
    ANALYZED = "ANALYZED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"

class CodePatch(BaseModel):
    file_path: str
    original_code: str
    proposed_code: str
    diff: str

class RootCauseAnalysis(BaseModel):
    bug_id: str
    probable_root_cause: str
    affected_files: List[str] = Field(default_factory=list)
    proposed_patches: List[CodePatch] = Field(default_factory=list)
    regression_test_code: Optional[str] = None
    status: PatchStatus = PatchStatus.PENDING_ANALYSIS
    verification_output: Optional[str] = None
