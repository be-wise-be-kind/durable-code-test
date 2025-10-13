#!/usr/bin/env python3
"""
Purpose: Nesting depth analysis rules for the pluggable framework
Scope: Converts nesting depth linter functionality to framework rules
Overview: Overview: This module enforces code complexity limits by detecting excessive nesting and overly
    deep function structures that harm code readability and maintainability. It identifies functions
    with too many nested blocks, deeply nested conditional statements, complex nested loops, and
    excessive indentation levels that make code difficult to understand and test. The rules analyze
    the AST to measure nesting depth, considering different statement types and their impact on
    complexity. Each violation includes refactoring suggestions such as early returns, guard clauses,
    extracting nested logic to separate functions, and using functional approaches to reduce nesting.
    The module helps maintain clean, readable code by enforcing maximum nesting levels, encouraging
    flat code structures, and promoting techniques that reduce cognitive load when reading and
    maintaining code.
Dependencies: Framework interfaces, AST analysis utilities
Exports: Nesting depth analysis rules
Interfaces: All rules implement ASTLintRule interface
Implementation: Rule-based architecture with depth tracking
"""

import ast

from tools.design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity

# Default configuration constants
DEFAULT_MAX_NESTING_DEPTH = 4
DEFAULT_MAX_FUNCTION_LINES = 50  # Default limit expected by tests
DEFAULT_MAX_DEEP_FUNCTION_NESTING = 4  # More realistic for real-world code


class ExcessiveNestingRule(ASTLintRule):
    """Rule to detect excessive nesting depth in functions."""

    @property
    def rule_id(self) -> str:
        return "style.excessive-nesting"

    @property
    def rule_name(self) -> str:
        return "Excessive Nesting"

    @property
    def description(self) -> str:
        return "Functions should not have excessive nesting depth for better readability"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"style", "complexity", "readability"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("ExcessiveNestingRule should only receive function nodes")
        config = self.get_configuration(context.metadata or {})
        max_depth = config.get("max_nesting_depth", DEFAULT_MAX_NESTING_DEPTH)

        max_found_depth = self._calculate_max_nesting_depth(node)

        if max_found_depth > max_depth:
            return [
                self.create_violation_from_node(
                    context,
                    node,
                    message=f"Function '{node.name}' has excessive nesting depth ({max_found_depth})",
                    description=f"Maximum nesting depth of {max_found_depth} exceeds limit of {max_depth}",
                    suggestion="Consider extracting nested logic into separate functions or using early returns",
                    violation_context={
                        "function_name": node.name,
                        "depth": max_found_depth,
                        "max_allowed": max_depth,
                    },
                )
            ]

        return []

    def _calculate_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate the maximum nesting depth in a function."""
        max_depth = 0

        def visit_node(n: ast.AST, current_depth: int = 0) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            # Nodes that increase nesting depth
            if isinstance(
                n,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                    ast.ExceptHandler,
                    ast.Match,
                    ast.match_case,
                ),
            ):
                current_depth += 1

            # Visit children
            for child in ast.iter_child_nodes(n):
                visit_node(child, current_depth)

        # Start visiting from function body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("Expected function node")
        for stmt in node.body:
            visit_node(stmt, 1)  # Start at depth 1 for function body

        return max_depth


class DeepFunctionRule(ASTLintRule):
    """Rule to detect functions that are too complex based on nesting and length."""

    @property
    def rule_id(self) -> str:
        return "style.deep-function"

    @property
    def rule_name(self) -> str:
        return "Complex Function"

    @property
    def description(self) -> str:
        return "Functions should not be overly complex with deep nesting and many lines"

    @property
    def severity(self) -> Severity:
        return Severity.INFO

    @property
    def categories(self) -> set[str]:
        return {"style", "complexity", "maintainability"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("DeepFunctionRule should only receive function nodes")
        config = self.get_configuration(context.metadata or {})
        max_lines = config.get("max_function_lines", DEFAULT_MAX_FUNCTION_LINES)
        max_depth = config.get("max_nesting_depth", DEFAULT_MAX_DEEP_FUNCTION_NESTING)

        violations = []

        # Check function length
        if node.end_lineno and node.lineno:
            line_count = node.end_lineno - node.lineno

            if line_count > max_lines:
                violations.append(
                    self.create_violation_from_node(
                        context,
                        node,
                        message=f"Function '{node.name}' is too long ({line_count} lines)",
                        description=(f"Function length of {line_count} lines exceeds recommended limit of {max_lines}"),
                        suggestion="Consider breaking this function into smaller, focused functions",
                        violation_context={
                            "function_name": node.name,
                            "length": line_count,
                            "issue": "length",
                        },
                    )
                )

        # Check nesting depth
        nesting_depth = self._calculate_max_nesting_depth(node)
        if nesting_depth > max_depth:
            violations.append(
                self.create_violation_from_node(
                    context,
                    node,
                    message=f"Function '{node.name}' has deep nesting ({nesting_depth} levels)",
                    description=(f"Nesting depth of {nesting_depth} exceeds recommended limit of {max_depth}"),
                    suggestion="Consider using early returns or extracting nested logic into helper functions",
                    violation_context={
                        "function_name": node.name,
                        "depth": nesting_depth,
                        "issue": "nesting",
                    },
                )
            )

        return violations

    def _calculate_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate the maximum nesting depth in a function."""
        max_depth = 0

        def visit_node(n: ast.AST, current_depth: int = 0) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)

            # Nodes that increase nesting depth
            if isinstance(
                n,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                    ast.ExceptHandler,
                ),
            ):
                current_depth += 1

            # Visit children
            for child in ast.iter_child_nodes(n):
                visit_node(child, current_depth)

        # Start visiting from function body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise TypeError("Expected function node")
        for stmt in node.body:
            visit_node(stmt, 1)

        return max_depth
