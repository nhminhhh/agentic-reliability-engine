from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ToolSchemaSpec(BaseModel):
    tool_name: str
    required_params: Set[str] = Field(default_factory=set)
    allowed_params: Set[str] = Field(default_factory=set)
    param_types: Dict[str, type] = Field(default_factory=dict)
    param_ranges: Dict[str, tuple[Optional[float], Optional[float]]] = Field(default_factory=dict)
    param_patterns: Dict[str, str] = Field(default_factory=dict)
    allow_unknown_args: bool = False


class ValidationResult(BaseModel):
    is_valid: bool
    sanitized_args: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    hallucinated_params: List[str] = Field(default_factory=list)


class SchemaGuard:
    """Pre-flight speculative validator for tool calls before execution."""

    def __init__(self):
        self._registry: Dict[str, ToolSchemaSpec] = {}

    def register_tool(self, spec: ToolSchemaSpec) -> None:
        self._registry[spec.tool_name] = spec

    def validate(self, tool_name: str, arguments: Dict[str, Any]) -> ValidationResult:
        if tool_name not in self._registry:
            # If tool is unmonitored, pass through with warning
            return ValidationResult(is_valid=True, sanitized_args=arguments)

        spec = self._registry[tool_name]
        errors: List[str] = []
        hallucinated: List[str] = []
        sanitized: Dict[str, Any] = dict(arguments)

        # 1. Check for hallucinated/unknown arguments
        for param in arguments:
            if param not in spec.allowed_params and not spec.allow_unknown_args:
                hallucinated.append(param)
                errors.append(f"Hallucinated parameter '{param}' not found in schema for tool '{tool_name}'")

        # 2. Check required parameters
        for required in spec.required_params:
            if required not in arguments:
                errors.append(f"Missing required parameter '{required}' for tool '{tool_name}'")

        # 3. Check types and ranges
        for param, value in arguments.items():
            if param in spec.param_types:
                expected_type = spec.param_types[param]
                # Relax int/float interchangeability for numbers
                if expected_type is float and isinstance(value, int):
                    value = float(value)
                    sanitized[param] = value

                if not isinstance(value, expected_type):
                    errors.append(f"Parameter '{param}' expected type {expected_type.__name__}, got {type(value).__name__}")

            if param in spec.param_ranges and isinstance(value, (int, float)):
                min_v, max_v = spec.param_ranges[param]
                if min_v is not None and value < min_v:
                    errors.append(f"Parameter '{param}' value {value} is below allowed minimum {min_v}")
                if max_v is not None and value > max_v:
                    errors.append(f"Parameter '{param}' value {value} exceeds allowed maximum {max_v}")

            if param in spec.param_patterns and isinstance(value, str):
                pattern = spec.param_patterns[param]
                if not re.match(pattern, value):
                    errors.append(f"Parameter '{param}' with value '{value}' fails regex pattern '{pattern}'")

        return ValidationResult(
            is_valid=len(errors) == 0,
            sanitized_args=sanitized if len(errors) == 0 else {},
            errors=errors,
            hallucinated_params=hallucinated,
        )
