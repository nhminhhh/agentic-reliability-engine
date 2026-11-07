class ReliabilityEngineError(Exception):
    """Base exception for all agentic reliability failures."""
    pass


class SpeculativeValidationError(ReliabilityEngineError):
    """Raised when a tool call fails pre-flight speculative schema or bounds verification."""
    def __init__(self, tool_name: str, reason: str, details: dict | None = None):
        super().__init__(f"Speculative validation failed for tool '{tool_name}': {reason}")
        self.tool_name = tool_name
        self.reason = reason
        self.details = details or {}


class ExecutionSandboxedViolation(ReliabilityEngineError):
    """Raised when an agent attempts an unauthorized AST execution or dangerous system call."""
    pass


class TrajectoryReplayMismatch(ReliabilityEngineError):
    """Raised when replay step output diverges from recorded deterministic trajectory trace."""
    pass


class MaxSelfHealingRetriesExceeded(ReliabilityEngineError):
    """Raised when an autonomous agent exhausts its reflection loop quota without convergence."""
    pass
