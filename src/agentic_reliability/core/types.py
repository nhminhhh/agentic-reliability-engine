from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepType(str, Enum):
    SYSTEM = "system"
    USER = "user"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_RESPONSE = "final_response"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HEALED = "healed"


class ToolCall(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    speculative_verified: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    call_id: str
    output: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    success: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentStep(BaseModel):
    index: int
    step_type: StepType
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[ToolResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        """Computes a deterministic hash of the step for tamper-evident trajectory tracing."""
        payload = {
            "index": self.index,
            "step_type": self.step_type.value,
            "content": self.content,
            "tool_calls": [tc.model_dump(mode="json") for tc in self.tool_calls],
            "tool_results": [tr.model_dump(mode="json") for tr in self.tool_results],
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class Checkpoint(BaseModel):
    step_index: int
    state_snapshot: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Trajectory(BaseModel):
    trajectory_id: str
    goal: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    steps: List[AgentStep] = Field(default_factory=list)
    checkpoints: List[Checkpoint] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def get_step_checksum_chain(self) -> List[str]:
        """Returns the sequential SHA-256 hash chain verifying trajectory integrity."""
        return [step.compute_hash() for step in self.steps]
