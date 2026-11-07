from agentic_reliability.verifier.schema_guard import SchemaGuard, ToolSchemaSpec
from agentic_reliability.verifier.sandbox import SpeculativeSandbox


def test_schema_guard_validation():
    guard = SchemaGuard()
    spec = ToolSchemaSpec(
        tool_name="transfer_funds",
        required_params={"recipient", "amount"},
        allowed_params={"recipient", "amount", "memo"},
        param_types={"recipient": str, "amount": float, "memo": str},
        param_ranges={"amount": (1.0, 10000.0)},
        param_patterns={"recipient": r"^usr_[a-zA-Z0-9]+$"},
    )
    guard.register_tool(spec)

    # Valid call
    res = guard.validate("transfer_funds", {"recipient": "usr_alice123", "amount": 250.0, "memo": "rent"})
    assert res.is_valid is True
    assert len(res.errors) == 0

    # Invalid range and regex
    res2 = guard.validate("transfer_funds", {"recipient": "bad_alice", "amount": 99999.0})
    assert res2.is_valid is False
    assert any("fails regex pattern" in e for e in res2.errors)
    assert any("exceeds allowed maximum" in e for e in res2.errors)

    # Hallucinated argument
    res3 = guard.validate("transfer_funds", {"recipient": "usr_alice123", "amount": 10.0, "bypass_auth": True})
    assert res3.is_valid is False
    assert "bypass_auth" in res3.hallucinated_params


def test_sandbox_safety_analysis():
    sandbox = SpeculativeSandbox()

    safe_code = """
def calculate_growth(principal, rate, years):
    return principal * ((1 + rate) ** years)
result = calculate_growth(1000, 0.05, 10)
"""
    res = sandbox.analyze_python_code(safe_code)
    assert res.is_safe is True
    assert len(res.violations) == 0

    dangerous_code = """
import os
os.system("rm -rf /")
"""
    res2 = sandbox.analyze_python_code(dangerous_code)
    assert res2.is_safe is False
    assert any("Forbidden import: 'os'" in v for v in res2.violations)
