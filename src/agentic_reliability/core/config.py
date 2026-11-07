from pydantic import BaseModel, Field


class EngineConfig(BaseModel):
    """Configuration options governing agentic verification and self-healing policies."""
    speculative_verification: bool = Field(default=True, description="Enable pre-execution schema bounds check")
    max_self_healing_retries: int = Field(default=3, description="Maximum self-correction cycles per step")
    sandbox_timeout_ms: float = Field(default=5000.0, description="Maximum sandbox tool execution timeout")
    enforce_deterministic_hashes: bool = Field(default=True, description="Verify cryptographic hash chain on replay")
    trajectory_storage_dir: str = Field(default=".trajectories", description="Local path for serialized traces")
    strict_tool_bounds: bool = Field(default=True, description="Enforce strict type and numerical bounds on tool args")
