from agentic_reliability.core.types import ExecutionStatus, StepType, ToolCall
from agentic_reliability.orchestrator.runner import ReliableAgentRunner
from agentic_reliability.orchestrator.tools import SafeMathTool, VectorRetrieverTool


def test_agent_runner_self_healing():
    tools = [SafeMathTool()]
    runner = ReliableAgentRunner(tools=tools)

    def simple_policy(traj, feedback):
        if feedback:
            # Successfully heals
            return (
                StepType.FINAL_RESPONSE,
                "Healed answer",
                [],
            )
        # Induces failure
        return (
            StepType.TOOL_CALL,
            "Calling unknown operation",
            [ToolCall(call_id="c1", tool_name="safe_math", arguments={"operation": "invalid", "x": 1.0, "y": 2.0})],
        )

    trajectory = runner.run_agentic_loop(goal="Test healing", agent_step_fn=simple_policy)
    assert trajectory.status == ExecutionStatus.HEALED
    assert len(trajectory.steps) == 2
