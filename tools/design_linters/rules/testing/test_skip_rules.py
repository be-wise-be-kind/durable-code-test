#!/usr/bin/env python3
"""
Purpose: Test skip detection linting rule for the design linter framework
Scope: Testing category rule implementation for preventing skipped tests
Overview: This module implements a rule that detects and reports skipped tests in the codebase,
    ensuring all tests are actively running and providing value. It identifies various forms of
    test skipping including unittest.skip decorators, pytest.mark.skip, xfail markers, and
    programmatic skip calls. The rule helps maintain test suite integrity by preventing tests
    from being accidentally left in a skipped state after debugging or temporary disabling.
    It supports configuration for allowing skips with valid reasons and can be disabled via
    inline comments for legitimate cases. This ensures the test suite remains comprehensive
    and all test coverage metrics accurately reflect the actual testing being performed.
Dependencies: ast module for AST analysis, framework interfaces
Exports: NoSkippedTestsRule implementation
Interfaces: Implements ASTLintRule interface from framework
Implementation: AST-based detection of skip patterns with configurable strictness
"""

import ast
from typing import Any

from loguru import logger
from tools.design_linters.framework.interfaces import (
    ASTLintRule,
    LintContext,
    LintViolation,
    Severity,
)


class SkipPatternDetector:
    """Detects various test skip patterns in code."""

    def has_skip_decorator(self, node: ast.FunctionDef | ast.ClassDef) -> bool:
        """Check if a function or class has a skip decorator."""
        return any(self._is_skip_decorator(decorator) for decorator in node.decorator_list)

    def is_skip_call(self, node: ast.Call) -> bool:
        """Check if a call is a skip-related function."""
        # Check for unittest.skip() or pytest.skip()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["skip", "skipTest", "skipIf", "skipUnless", "xfail"]:
                return True
        # Check for standalone skip() calls
        elif isinstance(node.func, ast.Name) and node.func.id in ["skip", "skipTest"]:
            return True
        return False

    def _is_skip_decorator(self, decorator: ast.AST) -> bool:
        """Check if decorator is a skip-related decorator."""
        # Handle @skip, @skipIf, @skipUnless
        if isinstance(decorator, ast.Name):
            return decorator.id in ["skip", "skipIf", "skipUnless", "xfail"]

        # Handle @unittest.skip, @pytest.mark.skip, etc.
        if isinstance(decorator, ast.Attribute):
            return decorator.attr in ["skip", "skipIf", "skipUnless", "xfail"]

        # Handle @pytest.mark.skip(...) or @unittest.skip(...)
        if isinstance(decorator, ast.Call):
            return self._is_skip_decorator_call(decorator)

        return False

    def _is_skip_decorator_call(self, call: ast.Call) -> bool:
        """Check if a call is a skip decorator with arguments."""
        if isinstance(call.func, ast.Attribute):
            # Check for pytest.mark.skip, pytest.mark.xfail, etc.
            if call.func.attr in ["skip", "skipif", "xfail"]:
                return True
            # Check for unittest.skip variations
            if (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "unittest"
                and call.func.attr in ["skip", "skipIf", "skipUnless"]
            ):
                return True
            # Check for mark.skip pattern
            if (
                isinstance(call.func.value, ast.Attribute)
                and call.func.value.attr == "mark"
                and call.func.attr in ["skip", "skipif", "xfail"]
            ):
                return True
        elif isinstance(call.func, ast.Name):
            return call.func.id in ["skip", "skipIf", "skipUnless", "xfail"]
        return False


class DisableCommentChecker:
    """Checks for disable comments that allow skipping tests."""

    DISABLE_PATTERNS = [
        "design-lint: ignore",
        "noqa",
        "type: ignore",
        "pragma: no cover",
        "skip-ok",
        "skip-allowed",
    ]

    def has_disable_comment(self, node: ast.AST, context: LintContext) -> bool:
        """Check if node has a comment that disables the check."""
        try:
            lines = context.source.splitlines() if hasattr(context, "source") and context.source else []
            if not lines:
                return False

            # Check decorators for functions/classes
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and self._has_decorator_disable_comment(node, lines):
                return True

            # Check the node's own line
            return self._has_node_disable_comment(node, lines)
        except Exception as e:
            logger.error("Error checking disable comment", error=str(e), exc_info=True)
            return False

    def _has_decorator_disable_comment(self, node: ast.AST, lines: list[str]) -> bool:
        """Check if any decorator line has a disable comment."""
        if not hasattr(node, "decorator_list") or not node.decorator_list:
            return False

        for decorator in node.decorator_list:
            if hasattr(decorator, "lineno") and self._check_line_for_disable_comment(decorator.lineno - 1, lines):
                return True
        return False

    def _has_node_disable_comment(self, node: ast.AST, lines: list[str]) -> bool:
        """Check if the node's line has a disable comment."""
        if hasattr(node, "lineno"):
            return self._check_line_for_disable_comment(node.lineno - 1, lines)
        return False

    def _check_line_for_disable_comment(self, line_idx: int, lines: list[str]) -> bool:
        """Check if a specific line contains a disable comment."""
        if 0 <= line_idx < len(lines):
            line = lines[line_idx]
            for pattern in self.DISABLE_PATTERNS:
                if pattern in line:
                    return True
        return False


class TestFileDetector:
    """Detects if a file is a test file."""

    TEST_PATTERNS = [
        "test_",
        "_test.py",
        "/tests/",
        "/test/",
        "spec.py",
        "_spec.py",
    ]

    def is_test_file(self, context: LintContext) -> bool:
        """Check if the current file is a test file."""
        file_path = str(context.file_path).lower() if hasattr(context, "file_path") else ""

        for pattern in self.TEST_PATTERNS:
            if pattern in file_path:
                return True

        # Also check if file name starts with test_
        import os

        filename = os.path.basename(file_path)
        return filename.startswith("test_") or filename.endswith("_test.py")


class ViolationFactory:
    """Creates violation objects for skipped tests."""

    def create_violation(
        self,
        node: ast.AST,
        context: LintContext,
        rule_id: str,
        message: str,
        suggestion: str,
        severity: Severity = Severity.WARNING,
    ) -> LintViolation:
        """Create a violation for a skipped test."""
        return LintViolation(
            rule_id=rule_id,
            message=message,
            description="Test is skipped and may indicate test quality issues",
            severity=severity,
            line=node.lineno if hasattr(node, "lineno") else 0,
            column=node.col_offset if hasattr(node, "col_offset") else 0,
            file_path=context.file_path if hasattr(context, "file_path") else "",
            suggestion=suggestion,
        )


class NoSkippedTestsRule(ASTLintRule):
    """Detect and report skipped tests."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the rule with configuration."""
        super().__init__()
        self.config = config or {}

        # Initialize helper classes
        self._skip_detector = SkipPatternDetector()
        self._comment_checker = DisableCommentChecker()
        self._test_detector = TestFileDetector()
        self._violation_factory = ViolationFactory()

    @property
    def rule_id(self) -> str:
        """Return the unique identifier for this rule."""
        return "testing.no-skip"

    @property
    def rule_name(self) -> str:
        """Return the human-readable name for this rule."""
        return "No Skipped Tests"

    @property
    def description(self) -> str:
        """Return the description of what this rule checks."""
        return "Ensure tests are not skipped without valid reason"

    @property
    def severity(self) -> Severity:
        """Return the severity level of violations from this rule."""
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        """Return the categories this rule belongs to."""
        return {"testing", "quality"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        """Check if node should be validated."""
        # Only check test files
        if not self._test_detector.is_test_file(context):
            return False

        # Check function/class definitions with decorators
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return True

        # Check function calls that might be skip-related
        return bool(isinstance(node, ast.Call))

    def get_configuration(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Get configuration for this specific check."""
        # Could be extended to read from metadata or config files
        return {"allow_skip_with_reason": True, "min_reason_length": 10}

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        """Check for skipped tests."""
        violations = []

        # Skip if there's a disable comment
        if self._comment_checker.has_disable_comment(node, context):
            return violations

        config = self.get_configuration({})

        # Check for skip decorators on functions/classes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            violations.extend(self._check_decorators(node, context, config))

        # Check for skip calls within code
        elif isinstance(node, ast.Call) and self._skip_detector.is_skip_call(node):
            violations.extend(self._check_skip_call(node, context, config))

        return violations

    def _check_decorators(
        self,
        node: ast.FunctionDef | ast.ClassDef,
        context: LintContext,
        config: dict[str, Any],
    ) -> list[LintViolation]:
        """Check decorators for skip patterns."""
        violations = []

        if self._skip_detector.has_skip_decorator(node):
            test_name = node.name
            node_type = "class" if isinstance(node, ast.ClassDef) else "function"

            # Check if skip has a valid reason
            has_reason = self._has_skip_reason(node, config)

            if not has_reason or not config.get("allow_skip_with_reason", True):
                message = f"Test {node_type} '{test_name}' is skipped"
                if not has_reason:
                    message += " without a reason"

                suggestion = (
                    f"Remove skip decorator from '{test_name}' or provide a valid reason "
                    f"(minimum {config.get('min_reason_length', 10)} characters)"
                )

                violations.append(
                    self._violation_factory.create_violation(
                        node=node,
                        context=context,
                        rule_id=self.rule_id,
                        message=message,
                        suggestion=suggestion,
                        severity=self.severity,
                    )
                )

        return violations

    def _check_skip_call(self, node: ast.Call, context: LintContext, config: dict[str, Any]) -> list[LintViolation]:
        """Check skip function calls."""
        violations = []

        # Get the skip reason if provided
        has_reason = len(node.args) > 0 or len(node.keywords) > 0

        if not has_reason or not config.get("allow_skip_with_reason", True):
            message = "Test execution skipped with skip() call"
            if not has_reason:
                message += " without a reason"

            suggestion = "Remove skip() call or provide a valid reason explaining why the test is skipped"

            violations.append(
                self._violation_factory.create_violation(
                    node=node,
                    context=context,
                    rule_id=self.rule_id,
                    message=message,
                    suggestion=suggestion,
                    severity=self.severity,
                )
            )

        return violations

    def _has_skip_reason(self, node: ast.FunctionDef | ast.ClassDef, config: dict[str, Any]) -> bool:
        """Check if skip decorator has a valid reason."""
        min_length = config.get("min_reason_length", 10)

        return any(self._is_skip_decorator_with_reason(decorator, min_length) for decorator in node.decorator_list)

    def _is_skip_decorator_with_reason(self, decorator: ast.AST, min_length: int) -> bool:
        """Check if decorator is a skip with a reason."""
        if not isinstance(decorator, ast.Call):
            return False

        # Check for arguments (the reason)
        if decorator.args and self._check_arg_is_valid_reason(decorator.args[0], min_length):
            return True

        # Check for reason keyword argument
        return self._check_keyword_reason(decorator.keywords, min_length)

    def _check_arg_is_valid_reason(self, arg: ast.AST, min_length: int) -> bool:
        """Check if argument is a valid reason string."""
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return len(arg.value) >= min_length
        if isinstance(arg, ast.Str):  # Python 3.7 compatibility
            return len(arg.s) >= min_length
        return False

    def _check_keyword_reason(self, keywords: list[ast.keyword], min_length: int) -> bool:
        """Check keywords for a valid reason argument."""
        for keyword in keywords:
            if keyword.arg != "reason":
                continue
            if self._check_arg_is_valid_reason(keyword.value, min_length):
                return True
        return False
