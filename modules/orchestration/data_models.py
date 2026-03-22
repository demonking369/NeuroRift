from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from modules.tools.base import ToolMode


class Finding(BaseModel):
    title: str
    severity: str
    description: str
    tool_source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = {}


class ToolExecutionResult(BaseModel):
    tool_name: str
    command: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    status: str  # "success", "failed", "cancelled"
    raw_output: str
    structured_output: Dict[str, Any] = {}
    error: Optional[str] = None
    findings: List[Finding] = []


class SessionContext(BaseModel):
    session_id: str
    mode: ToolMode
    target: str
    history: List[ToolExecutionResult] = []
    created_at: datetime = Field(default_factory=datetime.now)


class ScanRequest(BaseModel):
    tool_name: str
    target: str
    args: Dict[str, Any] = {}
    mode_override: Optional[ToolMode] = None
