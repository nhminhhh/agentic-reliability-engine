from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from agentic_reliability.core.types import ExecutionStatus, Trajectory
from agentic_reliability.eval.metrics import TrajectoryMetrics, compute_trajectory_metrics
from agentic_reliability.verifier.schema_guard import SchemaGuard


class EvaluationScorecard(BaseModel):
    goal: str
    goal_reached: bool
    grade: str  # A, B, C, D, F
    reliability_index: float
    metrics: TrajectoryMetrics
    anomalies: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class TrajectoryJudge:
    """Evaluates agent trajectories against production reliability standards."""

    def __init__(self, verifier: Optional[SchemaGuard] = None):
        self.verifier = verifier

    def evaluate(self, trajectory: Trajectory) -> EvaluationScorecard:
        metrics = compute_trajectory_metrics(trajectory, self.verifier)
        anomalies: List[str] = []
        recommendations: List[str] = []

        # Check anomalies
        if metrics.tool_redundancy_rate > 0.2:
            anomalies.append(f"High tool call redundancy detected: {metrics.tool_redundancy_rate * 100:.1f}% repeated invocations.")
            recommendations.append("Implement tool call memoization or enhance agent context with prior query outcomes.")

        if metrics.hallucinated_arguments_count > 0:
            anomalies.append(f"Detected {metrics.hallucinated_arguments_count} hallucinated tool parameters.")
            recommendations.append("Enforce strict Pydantic tool schemas with speculative verification before execution.")

        if metrics.tool_error_rate > 0.3:
            anomalies.append(f"High tool execution failure rate: {metrics.tool_error_rate * 100:.1f}%.")
            recommendations.append("Equip agent with structured error-reflection prompts to avoid repeated failure patterns.")

        # Determine letter grade
        score = metrics.reliability_index
        goal_reached = trajectory.status in (ExecutionStatus.COMPLETED, ExecutionStatus.HEALED)

        if not goal_reached:
            grade = "F"
        elif score >= 90.0:
            grade = "A"
        elif score >= 80.0:
            grade = "B"
        elif score >= 70.0:
            grade = "C"
        elif score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        return EvaluationScorecard(
            goal=trajectory.goal,
            goal_reached=goal_reached,
            grade=grade,
            reliability_index=score,
            metrics=metrics,
            anomalies=anomalies,
            recommendations=recommendations,
        )
