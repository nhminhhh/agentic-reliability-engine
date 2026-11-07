import pytest
from agentic_reliability.core.types import StepType, ToolCall, ToolResult
from agentic_reliability.tracer.recorder import TrajectoryRecorder
from agentic_reliability.tracer.replay import DeterministicReplayer
from agentic_reliability.core.exceptions import TrajectoryReplayMismatch


def test_trajectory_recording_and_hashing():
    recorder = TrajectoryRecorder(goal="Retrieve financial metrics for Q3")
    
    # Step 0: User input
    step0 = recorder.record_step(StepType.USER, content="What was the net profit in Q3?")
    assert step0.index == 0
    assert len(step0.compute_hash()) == 64

    # Step 1: Tool invocation
    tc = ToolCall(call_id="call_1", tool_name="query_db", arguments={"table": "finance", "quarter": "Q3"})
    tr = ToolResult(call_id="call_1", output={"net_profit": 1250000}, latency_ms=45.2)
    step1 = recorder.record_step(StepType.TOOL_CALL, tool_calls=[tc], tool_results=[tr])
    assert step1.index == 1

    traj = recorder.finalize()
    assert len(traj.steps) == 2
    hashes = traj.get_step_checksum_chain()
    assert len(hashes) == 2


def test_deterministic_replay_matching():
    recorder = TrajectoryRecorder(goal="Calculate 25 * 40")
    tc = ToolCall(call_id="c1", tool_name="calc", arguments={"expr": "25*40"})
    step = recorder.record_step(StepType.TOOL_CALL, tool_calls=[tc])
    traj = recorder.finalize()

    replayer = DeterministicReplayer(traj, strict_hash_verification=True)
    # Match step
    assert replayer.verify_step(step) is True
    assert replayer.is_complete() is True


def test_deterministic_replay_divergence():
    recorder = TrajectoryRecorder(goal="Calculate 25 * 40")
    tc = ToolCall(call_id="c1", tool_name="calc", arguments={"expr": "25*40"})
    recorder.record_step(StepType.TOOL_CALL, tool_calls=[tc])
    traj = recorder.finalize()

    replayer = DeterministicReplayer(traj)
    # Divergent step
    divergent_tc = ToolCall(call_id="c1", tool_name="calc", arguments={"expr": "25*41"})
    divergent_step = recorder.record_step(StepType.TOOL_CALL, tool_calls=[divergent_tc])

    with pytest.raises(TrajectoryReplayMismatch):
        replayer.verify_step(divergent_step)
