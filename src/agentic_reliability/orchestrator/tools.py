from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, Dict
from agentic_reliability.verifier.schema_guard import ToolSchemaSpec


class BaseTool(ABC):
    @property
    @abstractmethod
    def spec(self) -> ToolSchemaSpec:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass


class SafeMathTool(BaseTool):
    @property
    def spec(self) -> ToolSchemaSpec:
        return ToolSchemaSpec(
            tool_name="safe_math",
            required_params={"operation", "x", "y"},
            allowed_params={"operation", "x", "y"},
            param_types={"operation": str, "x": float, "y": float},
        )

    def execute(self, operation: str, x: float, y: float) -> float:
        if operation == "add":
            return x + y
        elif operation == "sub":
            return x - y
        elif operation == "mul":
            return x * y
        elif operation == "div":
            if y == 0:
                raise ValueError("Division by zero")
            return x / y
        elif operation == "pow":
            return math.pow(x, y)
        else:
            raise ValueError(f"Unknown operation: {operation}")


class VectorRetrieverTool(BaseTool):
    def __init__(self, documents: Dict[str, str] | None = None):
        self.corpus = documents or {
            "doc_1": "Agentic AI refers to systems where LLMs autonomously orchestrate tools, plans, and sub-goals.",
            "doc_2": "Self-healing loops intercept runtime tool errors and re-prompt the agent with targeted feedback.",
            "doc_3": "Speculative tool execution validates arguments against strict schema boundaries before execution.",
        }

    @property
    def spec(self) -> ToolSchemaSpec:
        return ToolSchemaSpec(
            tool_name="vector_search",
            required_params={"query"},
            allowed_params={"query", "top_k"},
            param_types={"query": str, "top_k": int},
            param_ranges={"top_k": (1, 10)},
        )

    def execute(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        query_lower = query.lower()
        results = []
        for doc_id, text in self.corpus.items():
            overlap = sum(1 for word in query_lower.split() if word in text.lower())
            if overlap > 0:
                results.append({"doc_id": doc_id, "snippet": text, "relevance": overlap})
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return {"query": query, "matches": results[:top_k]}


class SQLQueryTool(BaseTool):
    def __init__(self, mock_tables: Dict[str, list] | None = None):
        self.tables = mock_tables or {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "orders": [{"id": 101, "user_id": 1, "amount": 250.0}],
        }

    @property
    def spec(self) -> ToolSchemaSpec:
        return ToolSchemaSpec(
            tool_name="sql_query",
            required_params={"table_name"},
            allowed_params={"table_name", "limit"},
            param_types={"table_name": str, "limit": int},
            param_ranges={"limit": (1, 100)},
        )

    def execute(self, table_name: str, limit: int = 10) -> Dict[str, Any]:
        if table_name not in self.tables:
            raise KeyError(f"Table '{table_name}' does not exist in schema.")
        return {"table": table_name, "rows": self.tables[table_name][:limit]}
