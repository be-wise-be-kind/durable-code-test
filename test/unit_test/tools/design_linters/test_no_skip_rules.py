#!/usr/bin/env python3
"""
Purpose: Test suite for no-skip linting enforcement rules
Scope: Comprehensive testing of skip pattern detection across all languages
Overview: Tests the NoSkipRule implementation to ensure it correctly detects attempts
    to skip critical linting rules across Python, TypeScript, Terraform, and shell scripts.
    Verifies that critical rules are properly enforced, whitelisted patterns are allowed,
    and violation messages provide helpful guidance. Includes tests for multi-language
    support, edge cases, and configuration options.
Dependencies: pytest, design_linters framework, no_skip_rules module
Exports: Test cases for NoSkipRule
Interfaces: pytest test discovery
Implementation: Fixture-based testing with parametrized test cases
"""

from dataclasses import dataclass
from pathlib import Path

import pytest
from tools.design_linters.framework.base_interfaces import BaseLintContext
from tools.design_linters.rules.enforcement.no_skip_rules import NoSkipRule


@dataclass
class MockContext(BaseLintContext):
    """Mock context for testing."""

    file_path: Path | str | None = None
    file_content: str | None = None

    @property
    def language(self) -> str:
        """Get the language of the file."""
        if isinstance(self.file_path, Path):
            suffix = self.file_path.suffix
        elif isinstance(self.file_path, str):
            suffix = Path(self.file_path).suffix
        else:
            return "unknown"

        if suffix == ".py":
            return "python"
        if suffix in {".ts", ".tsx"}:
            return "typescript"
        if suffix == ".tf":
            return "terraform"
        if suffix == ".sh":
            return "shell"
        return "unknown"

    def get_context_description(self) -> str:
        """Get human-readable context description."""
        if self.file_path:
            return f"file {self.file_path}"
        return "unknown context"


class TestNoSkipRulePython:
    """Test NoSkipRule for Python files."""

    def test_detects_noqa_with_c901(self):
        """Test that noqa: C901 is detected and flagged."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("test_module.py"),
            file_content="def complex_function():  # noqa: C901\n    pass\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "C901" in violations[0].message
        assert "complexity" in violations[0].suggestion.lower()

    def test_detects_pylint_disable_w0718(self):
        """Test that pylint: disable=W0718 is detected."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("error_handler.py"),
            file_content="try:\n    pass\nexcept Exception:  # pylint: disable=W0718\n    pass\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "W0718" in violations[0].message
        assert "specific exception" in violations[0].suggestion.lower()

    def test_detects_type_ignore(self):
        """Test that type: ignore is detected for critical rules."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("typed_module.py"),
            file_content="value: int = 'string'  # type: ignore\n",
        )

        violations = rule.check(context)

        # type: ignore without specific code skips all rules
        assert len(violations) == 1
        assert "all" in violations[0].message.lower() or "type: ignore" in violations[0].description

    def test_allows_f401_in_init_py(self):
        """Test that F401 (unused import) is allowed in __init__.py files."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("package/__init__.py"),
            file_content="from .module import Something  # noqa: F401\n",
        )

        violations = rule.check(context)

        # Should be whitelisted
        assert len(violations) == 0

    def test_detects_security_rule_skip(self):
        """Test that Bandit security rules (S###) cannot be skipped."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("security.py"),
            file_content="password = 'hardcoded'  # noqa: S105\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "S105" in violations[0].message

    def test_detects_line_length_skip(self):
        """Test that E501 (line too long) skip is flagged."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("long_lines.py"),
            file_content=(
                "some_very_long_variable_name = 'this is a very long string that exceeds"
                " the line length limit'  # noqa: E501\n"
            ),
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "E501" in violations[0].message
        assert "break the line" in violations[0].suggestion.lower()

    def test_detects_multiple_rules_in_noqa(self):
        """Test detection of multiple rules in single noqa comment."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("multiple.py"),
            file_content="code = 'test'  # noqa: C901,W0718\n",
        )

        violations = rule.check(context)

        # Should detect both critical rules
        assert len(violations) == 1
        assert any(rule_code in violations[0].message for rule_code in ["C901", "W0718"])


class TestNoSkipRuleTypeScript:
    """Test NoSkipRule for TypeScript/JavaScript files."""

    def test_detects_eslint_disable_no_explicit_any(self):
        """Test that eslint-disable for no-explicit-any is detected."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("component.tsx"),
            file_content="// eslint-disable-next-line no-explicit-any\nconst data: any = {};\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "no-explicit-any" in violations[0].message
        assert "specific type" in violations[0].suggestion.lower()

    def test_detects_eslint_disable_react_hooks(self):
        """Test that eslint-disable for react-hooks rules is detected."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("hooks.ts"),
            file_content="// eslint-disable-next-line react-hooks/exhaustive-deps\nuseEffect(() => {}, []);\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "react-hooks/exhaustive-deps" in violations[0].message
        assert "dependencies" in violations[0].suggestion.lower()

    def test_detects_ts_ignore(self):
        """Test that @ts-ignore is detected."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("typescript.ts"),
            file_content="// @ts-ignore\nconst value: string = 123;\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert violations[0].message

    def test_detects_no_console_skip(self):
        """Test that no-console skip is detected."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("debug.ts"),
            file_content="// eslint-disable-next-line no-console\nconsole.log('debug');\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "no-console" in violations[0].message
        assert "logging service" in violations[0].suggestion.lower()

    def test_allows_any_in_test_files(self):
        """Test that no-explicit-any is allowed in test files."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("component.test.tsx"),
            file_content="// eslint-disable-next-line no-explicit-any\nconst mockData: any = {};\n",
        )

        violations = rule.check(context)

        # Should be whitelisted for test files
        assert len(violations) == 0


class TestNoSkipRuleInfrastructure:
    """Test NoSkipRule for infrastructure files."""

    def test_detects_tflint_ignore(self):
        """Test that tflint-ignore is detected in Terraform files."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("main.tf"),
            file_content='# tflint-ignore: terraform_unused_declarations\nresource "aws_s3_bucket" "test" {}\n',
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "terraform_unused_declarations" in violations[0].message

    def test_detects_shellcheck_disable(self):
        """Test that shellcheck disable is detected in shell scripts."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("script.sh"),
            file_content="# shellcheck disable=SC2086\necho $variable\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "SC2086" in violations[0].message


class TestNoSkipRuleEdgeCases:
    """Test edge cases and special scenarios."""

    def test_ignores_non_linting_files(self):
        """Test that non-code files are ignored."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("README.md"),
            file_content="# README\n# noqa: C901\n",
        )

        violations = rule.check(context)

        assert len(violations) == 0

    def test_handles_empty_file(self):
        """Test that empty files don't cause errors."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("empty.py"),
            file_content="",
        )

        violations = rule.check(context)

        assert len(violations) == 0

    def test_handles_file_without_skips(self):
        """Test that files without skip directives return no violations."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("clean.py"),
            file_content="def good_function():\n    return True\n",
        )

        violations = rule.check(context)

        assert len(violations) == 0

    def test_rule_metadata(self):
        """Test that rule metadata is correct."""
        rule = NoSkipRule()

        assert rule.rule_id == "enforcement.no-skip"
        assert "no skip" in rule.rule_name.lower()
        assert "enforcement" in rule.categories
        assert "quality" in rule.categories


class TestNoSkipRuleViolationMessages:
    """Test that violation messages are helpful and actionable."""

    def test_violation_includes_suggestion(self):
        """Test that violations include helpful suggestions."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("test.py"),
            file_content="def complex():  # noqa: C901\n    pass\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert violations[0].suggestion
        assert len(violations[0].suggestion) > 0

    def test_violation_describes_problem(self):
        """Test that violations clearly describe the problem."""
        rule = NoSkipRule()
        context = MockContext(
            file_path=Path("test.py"),
            file_content="x = 1  # noqa: E501\n",
        )

        violations = rule.check(context)

        assert len(violations) == 1
        assert "E501" in violations[0].message
        assert violations[0].description
        assert "fix" in violations[0].description.lower()