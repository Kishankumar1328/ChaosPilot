from typing import List, Optional
from pydantic import BaseModel, Field

class FormElement(BaseModel):
    selector: str
    element_type: str = "text"  # text, email, password, select, checkbox, submit, button, textarea
    name: Optional[str] = None
    placeholder: Optional[str] = None
    is_required: bool = False
    ref_id: Optional[int] = None

class RouteNode(BaseModel):
    url: str
    title: str
    depth: int
    forms: List[FormElement] = Field(default_factory=list)
    interactive_selectors: List[str] = Field(default_factory=list)
    axtree_snippet: Optional[str] = None
