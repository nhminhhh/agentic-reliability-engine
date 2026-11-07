from __future__ import annotations

import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from agentic_reliability.core.types import Trajectory, StepType
from agentic_reliability.verifier.schema_guard import SchemaGuard


class TrajectoryMetrics(BaseModel):
    total_steps: int = 0
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    tool_error_rate: float = 0.0
    tool_redundancy_rate: float = 0.0
    hallucinated_arguments_count: int = 0
    total_tool_latency_ms: float = 0.0
    average_tool_latency_ms: float = 0.0
    reliability_index: float = 100.0  # 0 to 100 scale


def compute_trajectory_metrics(
    trajectory: Trajectory,
    verifier: Optional[SchemaGuard] = None,
) -> TrajectoryMetrics:
    total_steps = len(trajectory.steps)
    all_calls = []
    failed_calls = 0
    successful_calls = 0
    total_latency = 0.0
    hallucinations = 0
    seen_call_signatures: List[str] = []
    redundant_calls = 0

    for step in trajectory.steps:
        # Tally tool calls
        for tc in step.tool_calls:
            all_calls.append(tc)
            sig = f"{tc.tool_name}:{json.dumps(tc.arguments, sort_keys=True)}"
            if sig in seen_call_signatures:
                redundant_calls += 1
            else:
                seen_call_signatures.append(sig)

            if verifier:
                v_res = verifier.validate(tc.tool_name, tc.arguments)
                hallucinations += len(v_res.hallucinated_params)

        for tr in step.tool_results:
            total_latency += tr.latency_ms
            if tr.success:
                successful_calls += 1
            else:
                failed_calls += 1

    total_tool_calls = len(all_calls)
    error_rate = (failed_calls / total_tool_calls) if total_tool_calls > 0 else 0.0
    redundancy_rate = (redundant_calls / total_tool_calls) if total_tool_calls > 0 else 0.0
    avg_latency = (total_latency / total_tool_calls) if total_tool_calls > 0 else 0.0

    # Calculate composite reliability index
    # Penalty: 35% error rate, 25% redundancy, 20% hallucinations, 20% step bloat
    penalty = (
        (error_rate * 35.0)
        + (redundancy_rate * 25.0)
        + (min(hallucinations * 10.0, 20.0))
        + (min(max(total_steps - 5, 0) * 2.0, 20.0))
    )
    reliability_index = max(0.0, round(100.0 - penalty, 2))

    return TrajectoryMetrics(
        total_steps=total_steps,
        total_tool_calls=total_tool_calls,
        successful_tool_calls=successful_calls,
        failed_tool_calls=failed_calls,
        tool_error_rate=round(error_rate, 4),
        tool_redundancy_rate=round(redundancy_rate, 4),
        hallucinated_arguments_count=hallucinations,
        total_tool_latency_ms=round(total_latency, 2),
        average_tool_latency_ms=round(avg_latency, 2),
        reliability_index=reliability_index,
    )
