from agentic_reliability.core.types import ExecutionStatus, StepType, ToolCall, ToolResult
from agentic_reliability.eval.judge import TrajectoryJudge
from agentic_reliability.eval.metrics import compute_trajectory_metrics
from agentic_reliability.tracer.recorder import TrajectoryRecorder
from agentic_reliability.verifier.schema_guard import SchemaGuard, ToolSchemaSpec


def test_trajectory_eval_and_judge():
    recorder = TrajectoryRecorder(goal="Scrape user profile and compute credit score")
    
    # Step 1: Valid tool call
    tc1 = ToolCall(call_id="c1", tool_name="fetch_profile", arguments={"user_id": "u123"})
    tr1 = ToolResult(call_id="c1", output={"status": "ok"}, latency_ms=120.0, success=True)
    recorder.record_step(StepType.TOOL_CALL, tool_calls=[tc1], tool_results=[tr1])

    # Step 2: Redundant tool call
    tc2 = ToolCall(call_id="c2", tool_name="fetch_profile", arguments={"user_id": "u123"})
    tr2 = ToolResult(call_id="c2", output={"status": "ok"}, latency_ms=115.0, success=True)
    recorder.record_step(StepType.TOOL_CALL, tool_calls=[tc2], tool_results=[tr2])

    traj = recorder.finalize(ExecutionStatus.COMPLETED)

    metrics = compute_trajectory_metrics(traj)
    assert metrics.total_tool_calls == 2
    assert metrics.tool_redundancy_rate == 0.5  # 1 redundant out of 2

    judge = TrajectoryJudge()
    card = judge.evaluate(traj)
    assert card.goal_reached is True
    assert card.grade in ("A", "B", "C")
    assert any("redundancy" in a.lower() for a in card.anomalies)
