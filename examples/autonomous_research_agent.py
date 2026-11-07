"""
Autonomous Research Agent Example.
Demonstrates multi-step semantic retrieval, mathematical synthesis, and trajectory evaluation.
"""

from agentic_reliability.core.types import StepType, ToolCall
from agentic_reliability.eval.judge import TrajectoryJudge
from agentic_reliability.orchestrator.runner import ReliableAgentRunner
from agentic_reliability.orchestrator.tools import SafeMathTool, VectorRetrieverTool


def research_agent_policy(trajectory, feedback_prompt):
    step_num = len(trajectory.steps)

    if step_num == 0:
        return (
            StepType.TOOL_CALL,
            "Researching definitions for agentic self-healing mechanisms...",
            [ToolCall(call_id="call_search", tool_name="vector_search", arguments={"query": "self-healing loops", "top_k": 2})],
        )
    elif step_num == 1:
        return (
            StepType.TOOL_CALL,
            "Computing latency budget scaling...",
            [ToolCall(call_id="call_math", tool_name="safe_math", arguments={"operation": "mul", "x": 120.0, "y": 3.0})],
        )
    else:
        return (
            StepType.FINAL_RESPONSE,
            "Research synthesis complete: Identified self-healing feedback patterns with 360ms budget.",
            [],
        )


def main():
    tools = [SafeMathTool(), VectorRetrieverTool()]
    runner = ReliableAgentRunner(tools=tools)

    print("Running Autonomous Research Agent...")
    trajectory = runner.run_agentic_loop(
        goal="Synthesize research on agentic self-healing and latency bounds",
        agent_step_fn=research_agent_policy,
    )

    judge = TrajectoryJudge(verifier=runner.guard)
    card = judge.evaluate(trajectory)

    print("\n--- Evaluation Scorecard ---")
    print(f"Status: {trajectory.status.value}")
    print(f"Grade:  {card.grade}")
    print(f"Score:  {card.reliability_index}/100.0")
    print(f"Steps:  {card.metrics.total_steps}")
    print(f"Average Latency: {card.metrics.average_tool_latency_ms} ms")


if __name__ == "__main__":
    main()
