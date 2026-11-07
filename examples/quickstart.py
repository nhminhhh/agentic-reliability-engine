"""
Quickstart demonstration of Agentic Reliability Engine.
Simulates an agent executing tools, experiencing a schema mistake, self-healing, and evaluating trajectory.
"""

from agentic_reliability.core.types import StepType, ToolCall
from agentic_reliability.eval.judge import TrajectoryJudge
from agentic_reliability.orchestrator.runner import ReliableAgentRunner
from agentic_reliability.orchestrator.tools import SafeMathTool, VectorRetrieverTool


def mock_llm_agent(trajectory, feedback_prompt):
    step_num = len(trajectory.steps)

    if feedback_prompt:
        # Agent reflects on error and fixes parameters
        return (
            StepType.TOOL_CALL,
            "Self-correction: Adjusting parameter operation to 'add' with numerical floats.",
            [ToolCall(call_id="c2", tool_name="safe_math", arguments={"operation": "add", "x": 10.0, "y": 25.0})],
        )

    if step_num == 0:
        # Step 1: Agent tries calling safe_math with invalid argument 'op' instead of 'operation'
        return (
            StepType.TOOL_CALL,
            "Attempting to calculate initial sum...",
            [ToolCall(call_id="c1", tool_name="safe_math", arguments={"operation": "unknown_op", "x": 10.0, "y": 25.0})],
        )

    # Final step
    return (
        StepType.FINAL_RESPONSE,
        "The calculated sum is 35.0.",
        [],
    )


def main():
    print("=" * 60)
    print("Agentic Reliability Engine - Quickstart Demo")
    print("=" * 60)

    tools = [SafeMathTool(), VectorRetrieverTool()]
    runner = ReliableAgentRunner(tools=tools)

    print("\n[1] Running Autonomous Agent with Speculative Guardrails...")
    trajectory = runner.run_agentic_loop(
        goal="Calculate 10 + 25 safely",
        agent_step_fn=mock_llm_agent,
    )

    print(f"Execution finished with status: {trajectory.status.value.upper()}")
    print(f"Total steps executed: {len(trajectory.steps)}")

    print("\n[2] Evaluating Trajectory with Autonomous Judge...")
    judge = TrajectoryJudge(verifier=runner.guard)
    scorecard = judge.evaluate(trajectory)

    print(f"Goal Reached: {scorecard.goal_reached}")
    print(f"Reliability Grade: {scorecard.grade}")
    print(f"Reliability Index: {scorecard.reliability_index}/100.0")
    print(f"Total Tool Calls: {scorecard.metrics.total_tool_calls}")
    print(f"Tool Error Rate: {scorecard.metrics.tool_error_rate * 100:.1f}%")
    if scorecard.anomalies:
        print("\nAnomalies detected:")
        for a in scorecard.anomalies:
            print(f" - {a}")

    print("\nStep Checksum Chain (Deterministic Verification):")
    for idx, csum in enumerate(trajectory.get_step_checksum_chain()):
        print(f"  Step {idx}: {csum[:16]}...")


if __name__ == "__main__":
    main()
