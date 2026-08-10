from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime

class RunRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    target_url: str
    status: str
    max_depth: int
    max_pages: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    state_json: str = Field(sa_column=Column(LONGTEXT))  # Serialized ChaosPilotState JSON (LONGTEXT for full state maps)

class BugReportRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    title: str
    severity: str
    route: str
    description: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    report_json: str = Field(sa_column=Column(LONGTEXT))  # Serialized BugReport JSON

class EpisodicMemoryRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(index=True)
    route_url: str
    action_type: str
    selector: str
    successful_payload: Optional[str] = Field(default=None, sa_column=Column(Text))
    success_count: int = 1
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
