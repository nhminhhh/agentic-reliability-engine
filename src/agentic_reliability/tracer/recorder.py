from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic_reliability.core.types import (
    AgentStep,
    Checkpoint,
    ExecutionStatus,
    StepType,
    ToolCall,
    ToolResult,
    Trajectory,
)


class TrajectoryRecorder:
    """Captures and persists deterministic, event-sourced execution trajectories for LLM agents."""

    def __init__(self, goal: str, trajectory_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.trajectory = Trajectory(
            trajectory_id=trajectory_id or f"traj_{uuid.uuid4().hex[:12]}",
            goal=goal,
            metadata=metadata or {},
            status=ExecutionStatus.RUNNING,
        )
        self._current_index = 0

    @property
    def trajectory_id(self) -> str:
        return self.trajectory.trajectory_id

    def record_step(
        self,
        step_type: StepType,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
        tool_results: Optional[List[ToolResult]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentStep:
        step = AgentStep(
            index=self._current_index,
            step_type=step_type,
            content=content,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
            metadata=metadata or {},
        )
        self.trajectory.steps.append(step)
        self._current_index += 1
        return step

    def record_checkpoint(self, state_snapshot: Dict[str, Any]) -> Checkpoint:
        checkpoint = Checkpoint(
            step_index=self._current_index,
            state_snapshot=state_snapshot,
        )
        self.trajectory.checkpoints.append(checkpoint)
        return checkpoint

    def finalize(self, status: ExecutionStatus = ExecutionStatus.COMPLETED) -> Trajectory:
        self.trajectory.status = status
        self.trajectory.completed_at = datetime.now(timezone.utc)
        return self.trajectory

    def save_to_file(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.trajectory.model_dump_json(indent=2))
        return path

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> Trajectory:
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Trajectory.model_validate(data)
