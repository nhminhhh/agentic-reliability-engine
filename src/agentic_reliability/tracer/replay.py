from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from agentic_reliability.core.exceptions import TrajectoryReplayMismatch
from agentic_reliability.core.types import AgentStep, Trajectory


class DeterministicReplayer:
    """Replays recorded trajectories and validates that new agent runs stay deterministic."""

    def __init__(self, recorded_trajectory: Trajectory, strict_hash_verification: bool = True):
        self.recorded_trajectory = recorded_trajectory
        self.strict_hash_verification = strict_hash_verification
        self._current_step_pointer = 0

    def verify_step(self, live_step: AgentStep) -> bool:
        """Compares a step from a live run against the recorded reference trajectory."""
        if self._current_step_pointer >= len(self.recorded_trajectory.steps):
            raise TrajectoryReplayMismatch(
                f"Live execution emitted extra step at index {live_step.index}, but recorded trajectory only has "
                f"{len(self.recorded_trajectory.steps)} steps."
            )

        ref_step = self.recorded_trajectory.steps[self._current_step_pointer]

        if ref_step.step_type != live_step.step_type:
            raise TrajectoryReplayMismatch(
                f"Step {live_step.index} type mismatch: expected '{ref_step.step_type}', got '{live_step.step_type}'."
            )

        # Check tool calls equivalence
        ref_calls = [(tc.tool_name, tc.arguments) for tc in ref_step.tool_calls]
        live_calls = [(tc.tool_name, tc.arguments) for tc in live_step.tool_calls]
        if ref_calls != live_calls:
            raise TrajectoryReplayMismatch(
                f"Step {live_step.index} tool calls mismatch.\nExpected: {ref_calls}\nActual:   {live_calls}"
            )

        if self.strict_hash_verification:
            ref_hash = ref_step.compute_hash()
            live_hash = live_step.compute_hash()
            if ref_hash != live_hash:
                raise TrajectoryReplayMismatch(
                    f"Cryptographic hash mismatch at step {live_step.index}: {live_hash} != {ref_hash}"
                )

        self._current_step_pointer += 1
        return True

    def is_complete(self) -> bool:
        return self._current_step_pointer == len(self.recorded_trajectory.steps)
