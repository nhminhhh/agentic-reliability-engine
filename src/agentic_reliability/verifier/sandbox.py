from __future__ import annotations

import ast
from typing import List, Set
from pydantic import BaseModel, Field


class SafetyAnalysis(BaseModel):
    is_safe: bool
    violations: List[str] = Field(default_factory=list)
    ast_nodes_count: int = 0
    max_ast_depth: int = 0


class SpeculativeSandbox:
    """Performs static AST analysis on code/commands emitted by LLM agents to detect dangerous operations."""

    DISALLOWED_MODULES: Set[str] = {
        "os", "subprocess", "sys", "socket", "pty", "shutil", "posix",
        "requests", "urllib", "http", "pickle", "ctypes"
    }
    DISALLOWED_BUILTINS: Set[str] = {
        "eval", "exec", "compile", "__import__", "open", "input"
    }

    def __init__(self, max_ast_depth: int = 25, max_ast_nodes: int = 500):
        self.max_ast_depth = max_ast_depth
        self.max_ast_nodes = max_ast_nodes

    def analyze_python_code(self, source_code: str) -> SafetyAnalysis:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return SafetyAnalysis(is_safe=False, violations=[f"Syntax error: {str(e)}"])

        violations: List[str] = []
        node_count = 0
        max_depth = 0

        def traverse(node: ast.AST, depth: int):
            nonlocal node_count, max_depth
            node_count += 1
            max_depth = max(max_depth, depth)

            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in self.DISALLOWED_MODULES:
                        violations.append(f"Forbidden import: '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in self.DISALLOWED_MODULES:
                        violations.append(f"Forbidden import from module: '{node.module}'")

            # Check calls to dangerous builtins
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.DISALLOWED_BUILTINS:
                    violations.append(f"Forbidden call to builtin: '{node.func.id}()'")

            for child in ast.iter_child_nodes(node):
                traverse(child, depth + 1)

        traverse(tree, 1)

        if node_count > self.max_ast_nodes:
            violations.append(f"AST node limit exceeded: {node_count} > {self.max_ast_nodes}")
        if max_depth > self.max_ast_depth:
            violations.append(f"AST depth limit exceeded: {max_depth} > {self.max_ast_depth}")

        return SafetyAnalysis(
            is_safe=len(violations) == 0,
            violations=violations,
            ast_nodes_count=node_count,
            max_ast_depth=max_depth,
        )
