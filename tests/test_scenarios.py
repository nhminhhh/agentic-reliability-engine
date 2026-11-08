

def test_speculative_verification_scenario_2026_11_08():
    from agentic_reliability.verifier.schema_guard import SchemaGuard, ToolSchemaSpec
    guard = SchemaGuard()
    spec = ToolSchemaSpec(
        tool_name="api_fetcher_2026_11_08",
        required_params={"target"},
        allowed_params={"target", "retry_count"},
        param_types={"target": str, "retry_count": int},
        param_ranges={"retry_count": (0, 5)},
    )
    guard.register_tool(spec)
    res = guard.validate("api_fetcher_2026_11_08", {"target": "https://api.internal/v1", "retry_count": 2})
    assert res.is_valid is True


def test_speculative_verification_2026_11_08_a63d0f():
    from agentic_reliability.verifier.schema_guard import SchemaGuard, ToolSchemaSpec
    guard = SchemaGuard()
    spec = ToolSchemaSpec(
        tool_name="api_fetcher_2026_11_08_a63d0f",
        required_params={"target"},
        allowed_params={"target", "retry_count"},
        param_types={"target": str, "retry_count": int},
        param_ranges={"retry_count": (0, 5)},
    )
    guard.register_tool(spec)
    res = guard.validate("api_fetcher_2026_11_08_a63d0f", {"target": "https://api.internal/v1", "retry_count": 2})
    assert res.is_valid is True
