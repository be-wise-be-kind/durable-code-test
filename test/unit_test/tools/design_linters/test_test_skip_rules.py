#!/usr/bin/env python3
"""
Purpose: Unit tests for the NoSkippedTestsRule linter
Scope: Tests all skip detection patterns and configuration options
Overview: This module provides comprehensive test coverage for the NoSkippedTestsRule,
    verifying that it correctly identifies various test skip patterns including decorators,
    function calls, and different testing frameworks while respecting configuration options
    and disable comments.
Dependencies: pytest, design_linters testing utilities
Exports: Test classes for skip detection validation
Interfaces: Standard pytest test interface
Implementation: Test cases covering all skip patterns and edge cases
"""

import ast
from pathlib import Path
# Removed unused imports: typing.Any, pytest

from tools.design_linters.framework.interfaces import LintContext, Severity
from tools.design_linters.rules.testing.test_skip_rules import \
    NoSkippedTestsRule


class TestNoSkippedTestsRule:  # thailint: ignore[srp]
    """Test suite for the NoSkippedTestsRule."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.rule = NoSkippedTestsRule()

    def create_context(
        self, file_path: str = "test_example.py", source_lines: list[str] | None = None
    ) -> LintContext:
        """Create a test context."""
        context = LintContext()
        context.file_path = Path(file_path)
        context.current_module = "test_module"
        context.file_content = "\n".join(source_lines) if source_lines else ""
        context.metadata = {}
        return context

    def test_detects_pytest_mark_skip_decorator(self) -> None:
        """Test detection of @pytest.mark.skip decorator."""
        code = """
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_something():
    assert True
"""
        tree = ast.parse(code)
        context = self.create_context("test_file.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 1
        assert "Skipped test found: test_something" in violations[0].message
        assert violations[0].severity == Severity.ERROR

    def test_detects_unittest_skip_decorator(self) -> None:
        """Test detection of unittest.skip decorator."""
        code = """
import unittest

class TestCase(unittest.TestCase):
    @unittest.skip("Temporarily disabled")
    def test_method(self):
        self.assertTrue(True)
"""
        tree = ast.parse(code)
        context = self.create_context("test_case.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 1
        assert "Skipped test found: test_method" in violations[0].message

    def test_detects_pytest_skip_function_call(self) -> None:
        """Test detection of pytest.skip() function call."""
        code = """
import pytest

def test_conditional():
    if some_condition:
        pytest.skip("Not supported on this platform")
    assert True
"""
        tree = ast.parse(code)
        context = self.create_context("test_conditional.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 1
        assert "Test skip call found" in violations[0].message

    def test_allows_skipif_decorator_by_default(self) -> None:
        """Test that skipif decorators are allowed by default."""
        code = """
import pytest
import sys

@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_python39_feature():
    assert True
"""
        tree = ast.parse(code)
        context = self.create_context("test_skipif.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 0  # skipif is allowed by default

    def test_detects_class_level_skip(self) -> None:
        """Test detection of skip decorator on test class."""
        code = """
import pytest

@pytest.mark.skip(reason="Entire test class is broken")
class TestBrokenFeature:
    def test_one(self):
        assert True

    def test_two(self):
        assert False
"""
        tree = ast.parse(code)
        context = self.create_context("test_class_skip.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 1
        assert "Skipped test found: TestBrokenFeature" in violations[0].message

    def test_ignores_non_test_files(self) -> None:
        """Test that non-test files are ignored."""
        code = """
import pytest

@pytest.mark.skip
def some_function():
    return True
"""
        tree = ast.parse(code)
        context = self.create_context(
            "regular_file.py", code.splitlines()
        )  # Not a test file

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 0  # Should ignore non-test files

    def test_respects_disable_comment(self) -> None:
        """Test that disable comments are respected."""
        code = """
import pytest

@pytest.mark.skip(reason="WIP")  # design-lint: ignore[testing.no-skipped-tests]
def test_work_in_progress():
    assert False
"""
        tree = ast.parse(code)
        context = self.create_context("test_disable.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 0  # Should be ignored due to disable comment

    def test_configuration_disable_skipif(self) -> None:
        """Test configuration to also flag skipif decorators."""
        code = """
import pytest
import sys

@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_python39_feature():
    assert True
"""
        tree = ast.parse(code)
        context = self.create_context("test_skipif.py", code.splitlines())
        context.metadata = {
            "rules": {"testing.no-skipped-tests": {"allow_skipif": False}}
        }

        rule = NoSkippedTestsRule()
        violations = []
        for node in ast.walk(tree):
            if rule.should_check_node(node, context):
                violations.extend(rule.check_node(node, context))

        assert len(violations) == 1
        assert "Conditional skip (skipif) found" in violations[0].message

    def test_multiple_skip_patterns_in_file(self) -> None:
        """Test detection of multiple skip patterns in a single file."""
        code = """
import pytest
import unittest

@pytest.mark.skip
def test_one():
    pass

class TestCase(unittest.TestCase):
    @unittest.skip("reason")
    def test_two(self):
        pass

    def test_three(self):
        if condition:
            pytest.skip("conditional")
        pass
"""
        tree = ast.parse(code)
        context = self.create_context("test_multiple.py", code.splitlines())

        violations = []
        for node in ast.walk(tree):
            if self.rule.should_check_node(node, context):
                violations.extend(self.rule.check_node(node, context))

        assert len(violations) == 3  # Should detect all three skip patterns
