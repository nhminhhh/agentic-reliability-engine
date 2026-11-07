from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from agentic_reliability.core.config import EngineConfig
from agentic_reliability.core.exceptions import MaxSelfHealingRetriesExceeded
from agentic_reliability.core.types import ExecutionStatus, StepType, ToolCall, ToolResult, Trajectory
from agentic_reliability.orchestrator.tools import BaseTool
from agentic_reliability.tracer.recorder import TrajectoryRecorder
from agentic_reliability.verifier.schema_guard import SchemaGuard


class ReliableAgentRunner:
    """Orchestrates LLM agents with pre-flight speculative validation and self-healing error recovery."""

    def __init__(
        self,
        tools: List[BaseTool],
        config: Optional[EngineConfig] = None,
    ):
        self.config = config or EngineConfig()
        self.tools_map: Dict[str, BaseTool] = {t.spec.tool_name: t for t in tools}
        self.guard = SchemaGuard()

        # Register tools with SchemaGuard
        for tool in tools:
            self.guard.register_tool(tool.spec)

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        start_time = time.perf_counter()
        call_id = tool_call.call_id
        tool_name = tool_call.tool_name
        args = tool_call.arguments

        # Speculative validation
        if self.config.speculative_verification:
            val_res = self.guard.validate(tool_name, args)
            if not val_res.is_valid:
                latency = (time.perf_counter() - start_time) * 1000.0
                return ToolResult(
                    call_id=call_id,
                    success=False,
                    error=f"Speculative validation rejected arguments: {', '.join(val_res.errors)}",
                    latency_ms=round(latency, 2),
                )
            args = val_res.sanitized_args
            tool_call.speculative_verified = True

        if tool_name not in self.tools_map:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                call_id=call_id,
                success=False,
                error=f"Unknown tool '{tool_name}'",
                latency_ms=round(latency, 2),
            )

        try:
            output = self.tools_map[tool_name].execute(**args)
            latency = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                call_id=call_id,
                output=output,
                success=True,
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                call_id=call_id,
                success=False,
                error=f"Runtime error in {tool_name}: {str(e)}",
                latency_ms=round(latency, 2),
            )

    def run_agentic_loop(
        self,
        goal: str,
        agent_step_fn: Callable[[Trajectory, Optional[str]], tuple[StepType, Optional[str], List[ToolCall]]],
        max_steps: int = 10,
    ) -> Trajectory:
        """Runs the agent loop with self-healing feedback reflection."""
        recorder = TrajectoryRecorder(goal=goal)
        feedback_prompt: Optional[str] = None
        healed = False

        for step_idx in range(max_steps):
            # Agent proposes next step
            step_type, content, tool_calls = agent_step_fn(recorder.trajectory, feedback_prompt)
            feedback_prompt = None

            results: List[ToolResult] = []
            has_error = False

            if tool_calls:
                for tc in tool_calls:
                    res = self.execute_tool_call(tc)
                    results.append(res)
                    if not res.success:
                        has_error = True

            recorder.record_step(
                step_type=step_type,
                content=content,
                tool_calls=tool_calls,
                tool_results=results,
            )

            # Check for self-healing trigger
            if has_error:
                failed_reasons = [r.error for r in results if not r.success]
                feedback_prompt = (
                    f"[SYSTEM CORRECTION ADVISORY]: Previous action failed with errors: {'; '.join(failed_reasons)}. "
                    f"Please self-reflect and adjust tool parameters accordingly."
                )
                healed = True

            if step_type == StepType.FINAL_RESPONSE:
                final_status = ExecutionStatus.HEALED if healed else ExecutionStatus.COMPLETED
                return recorder.finalize(final_status)

        return recorder.finalize(ExecutionStatus.FAILED)
