#!/usr/bin/env python3
"""
Purpose: Error handling and resilience pattern linting rules for code quality enforcement
Scope: Linting rules for exception handling, retry logic, circuit breakers, and structured error patterns
Overview: Comprehensive collection of AST-based linting rules that enforce proper error handling
    patterns including prevention of broad exception catching, requirement of retry logic for
    external operations, structured exception class validation, mandatory error logging, and
    circuit breaker usage recommendations for resilient system design and robust error management.
    The rules analyze AST nodes to detect error handling anti-patterns, validate exception
    structure, and recommend resilience patterns for external service interactions. Each rule
    provides specific guidance for improving error handling practices and building more robust
    applications that gracefully handle failures and provide appropriate logging and recovery.
Dependencies: ast module for AST traversal, design_linters framework interfaces for rule
    implementation
Exports: NoBroadExceptionsRule, RequireRetryLogicRule, StructuredExceptionsRule,
    RequireErrorLoggingRule, CircuitBreakerUsageRule
Interfaces: ASTLintRule interface implementations with check methods for AST node
    analysis
Implementation: AST-based rule implementations using node traversal and pattern matching
    for error handling validation
"""

import ast

from tools.design_linters.framework.interfaces import ASTLintRule, LintViolation, Severity


class NoBroadExceptionsRule(ASTLintRule):
    """Detect and prevent broad exception catching."""

    name = "error_handling.exceptions.no-broad"
    category = "error_handling"
    description = "Prohibits catching broad exception types"

    def check(self, tree: ast.AST, filepath: str, source: str) -> list[LintViolation]:
        """Check for broad exception catching in Python code."""
        violations = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            violation = self._check_exception_handler(node, filepath)
            if violation:
                violations.append(violation)
                continue

            violations.extend(self._check_exception_tuple(node, filepath))

        return violations

    def _check_exception_handler(self, node: ast.ExceptHandler, filepath: str) -> LintViolation | None:
        """Check if exception handler is too broad."""
        if node.type is None:
            # Bare except: clause
            return LintViolation(
                rule_id=self.name,
                file_path=filepath,
                line=node.lineno,
                column=node.col_offset,
                message="Bare except clause found - catch specific exceptions",
                severity=Severity.ERROR,
                description=self.description,
            )

        if isinstance(node.type, ast.Name) and node.type.id in ["Exception", "BaseException"]:
            return LintViolation(
                rule_id=self.name,
                file_path=filepath,
                line=node.lineno,
                column=node.col_offset,
                message=f"Broad exception type '{node.type.id}' - use specific exceptions",
                severity=Severity.ERROR,
                description=self.description,
            )

        return None

    def _check_exception_tuple(self, node: ast.ExceptHandler, filepath: str) -> list[LintViolation]:
        """Check tuple of exceptions for broad types."""
        violations = []

        if not isinstance(node.type, ast.Tuple):
            return violations

        for exc in node.type.elts:
            if not isinstance(exc, ast.Name):
                continue
            if exc.id not in ["Exception", "BaseException"]:
                continue

            violations.append(
                LintViolation(
                    rule_id=self.name,
                    file_path=filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Broad exception type '{exc.id}' in tuple - use specific exceptions",
                    severity=Severity.ERROR,
                    description=self.description,
                )
            )

        return violations


class RequireRetryLogicRule(ASTLintRule):
    """Ensure external operations have retry logic."""

    name = "error_handling.resilience.require-retry"
    category = "error_handling"
    description = "External operations must have retry logic"

    def check(self, tree: ast.AST, filepath: str, source: str) -> list[LintViolation]:
        """Check that external operations have retry decorators."""
        # Skip if this is a test file
        if "test" in filepath:
            return []

        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            violation = self._check_function_for_retry(node, filepath)
            if violation:
                violations.append(violation)

        return violations

    def _check_function_for_retry(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, filepath: str
    ) -> LintViolation | None:
        """Check if function needs retry logic."""
        if not self._is_external_operation(node):
            return None

        if self._has_retry_decorator(node):
            return None

        return LintViolation(
            rule_id=self.name,
            file_path=filepath,
            line=node.lineno,
            column=node.col_offset,
            message=f"External operation '{node.name}' should have retry logic",
            severity=Severity.WARNING,
            description=self.description,
        )

    def _is_external_operation(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function name suggests external operation."""
        external_keywords = [
            "fetch",
            "call",
            "request",
            "api",
            "external",
            "remote",
            "database",
            "db",
            "query",
            "http",
            "webhook",
        ]
        return any(keyword in node.name.lower() for keyword in external_keywords)

    def _has_retry_decorator(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function has retry decorator."""
        return any(self._is_retry_decorator(dec) for dec in node.decorator_list)

    def _is_retry_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is retry-related."""
        if isinstance(decorator, ast.Name):
            return "retry" in decorator.id.lower()

        if not isinstance(decorator, ast.Call):
            return False

        if isinstance(decorator.func, ast.Name):
            return "retry" in decorator.func.id.lower()

        if isinstance(decorator.func, ast.Attribute):
            return "retry" in decorator.func.attr.lower()

        return False


class StructuredExceptionsRule(ASTLintRule):
    """Ensure custom exceptions follow structured pattern."""

    name = "error_handling.exceptions.structured"
    category = "error_handling"
    description = "Custom exceptions must have proper structure"

    def check(self, tree: ast.AST, filepath: str, source: str) -> list[LintViolation]:
        """Check that exception classes are properly structured."""
        # Only check exception files
        if "exception" not in filepath.lower() and "error" not in filepath.lower():
            return []

        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            if not self._is_exception_class(node):
                continue

            violations.extend(self._check_exception_structure(node, filepath))

        return violations

    def _is_exception_class(self, node: ast.ClassDef) -> bool:
        """Check if class is an exception class."""
        for base in node.bases:
            if not isinstance(base, ast.Name):
                continue
            if "Exception" in base.id or "Error" in base.id:
                return True
        return False

    def _check_exception_structure(self, node: ast.ClassDef, filepath: str) -> list[LintViolation]:
        """Check exception class structure for required attributes."""
        violations = []

        # Skip base exception classes
        if node.name in ["AppException", "AppExceptionError"]:
            return violations

        init_attrs = self._get_init_attributes(node)
        if not init_attrs["has_init"]:
            return violations

        if not init_attrs["has_status_code"]:
            violations.append(
                LintViolation(
                    rule_id=self.name,
                    file_path=filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Exception '{node.name}' should define status_code",
                    severity=Severity.WARNING,
                    description=self.description,
                )
            )

        if not init_attrs["has_error_code"]:
            violations.append(
                LintViolation(
                    rule_id=self.name,
                    file_path=filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Exception '{node.name}' should define error_code",
                    severity=Severity.WARNING,
                    description=self.description,
                )
            )

        return violations

    def _get_init_attributes(self, node: ast.ClassDef) -> dict:
        """Get attributes defined in __init__ method."""
        result = {"has_init": False, "has_status_code": False, "has_error_code": False}

        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            if item.name != "__init__":
                continue

            result["has_init"] = True
            init_source = ast.unparse(item)
            result["has_status_code"] = "status_code" in init_source
            result["has_error_code"] = "error_code" in init_source
            break

        return result


class RequireErrorLoggingRule(ASTLintRule):
    """Ensure errors are properly logged."""

    name = "error_handling.logging.required"
    category = "error_handling"
    description = "Caught exceptions must be logged"

    def check(self, tree: ast.AST, filepath: str, source: str) -> list[LintViolation]:
        """Check that caught exceptions are logged."""
        violations = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            if self._has_logging_or_reraise(node):
                continue

            if not node.type:
                continue

            exc_type = self._get_exception_type_name(node)
            violations.append(
                LintViolation(
                    rule_id=self.name,
                    file_path=filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Caught {exc_type} should be logged or re-raised",
                    severity=Severity.WARNING,
                    description=self.description,
                )
            )

        return violations

    def _has_logging_or_reraise(self, node: ast.ExceptHandler) -> bool:
        """Check if except block has logging or re-raise."""
        for stmt in node.body:
            if self._contains_logging(stmt):
                return True
            if isinstance(stmt, ast.Raise):
                return True
        return False

    def _get_exception_type_name(self, node: ast.ExceptHandler) -> str:
        """Get exception type name for error message."""
        if isinstance(node.type, ast.Name):
            return node.type.id
        return "exception"

    def _contains_logging(self, node: ast.AST) -> bool:
        """Check if node contains logging call."""
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
        ):
            return node.value.func.attr in [
                "debug",
                "info",
                "warning",
                "error",
                "exception",
                "critical",
            ]

        # Recursively check in nested structures
        return any(self._contains_logging(child) for child in ast.iter_child_nodes(node))


class CircuitBreakerUsageRule(ASTLintRule):
    """Encourage circuit breaker pattern for external services."""

    name = "error_handling.resilience.circuit-breaker"
    category = "error_handling"
    description = "External service calls should use circuit breakers"

    def check(self, tree: ast.AST, filepath: str, source: str) -> list[LintViolation]:
        """Check for circuit breaker usage on external calls."""
        # Skip test files
        if "test" in filepath:
            return []

        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            if not self._is_service_call(node):
                continue

            if self._has_circuit_breaker_protection(node):
                continue

            violations.append(
                LintViolation(
                    rule_id=self.name,
                    file_path=filepath,
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Service call '{node.name}' could benefit from circuit breaker",
                    severity=Severity.INFO,
                    description=self.description,
                )
            )

        return violations

    def _is_service_call(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function is an external service call."""
        service_keywords = ["service", "api", "external", "remote", "database", "cache"]
        return any(keyword in node.name.lower() for keyword in service_keywords)

    def _has_circuit_breaker_protection(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function has circuit breaker protection."""
        # Check decorators
        if any(self._is_circuit_breaker(dec) for dec in node.decorator_list):
            return True
        # Check internal usage
        return self._contains_circuit_breaker(node)

    def _is_circuit_breaker(self, decorator: ast.AST) -> bool:
        """Check if decorator is circuit breaker related."""
        if isinstance(decorator, ast.Name):
            return "circuit" in decorator.id.lower() or "breaker" in decorator.id.lower()

        if not isinstance(decorator, ast.Call):
            return False

        if isinstance(decorator.func, ast.Name):
            return "circuit" in decorator.func.id.lower() or "breaker" in decorator.func.id.lower()

        if isinstance(decorator.func, ast.Attribute):
            return "circuit" in decorator.func.attr.lower() or "breaker" in decorator.func.attr.lower()

        return False

    def _contains_circuit_breaker(self, node: ast.AST) -> bool:
        """Check if function body contains circuit breaker usage."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and "circuit" in child.id.lower():
                return True
            if isinstance(child, ast.Attribute) and "circuit" in child.attr.lower():
                return True
        return False


# Export all rules
__all__ = [
    "NoBroadExceptionsRule",
    "RequireRetryLogicRule",
    "StructuredExceptionsRule",
    "RequireErrorLoggingRule",
    "CircuitBreakerUsageRule",
]
