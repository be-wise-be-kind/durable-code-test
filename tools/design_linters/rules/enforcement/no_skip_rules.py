#!/usr/bin/env python3
"""
Purpose: Linting rule skip detection and enforcement for design linter framework
Scope: Multi-language enforcement preventing improper linting rule skips
Overview: This module implements rules that detect and prevent developers from skipping
    critical linting rules across Python, TypeScript, Terraform, and shell scripts. It
    identifies skip patterns like noqa, pylint: disable, type: ignore, and eslint-disable,
    and enforces that certain critical rules (complexity, broad exceptions, security issues)
    are never bypassed. The rule maintains configurable whitelists for legitimate exceptions
    while ensuring code quality standards are upheld. It supports different enforcement
    levels for different project areas (strict for tools, lenient for tests) and provides
    clear violation messages explaining why the skip is not allowed and how to fix the issue.
Dependencies: Framework interfaces, multi-language file analysis, regex matching
Exports: NoSkipRule for multi-language skip pattern detection
Interfaces: Implements FileBasedLintRule from framework for all file types
Implementation: Regex-based pattern matching with configurable critical rule lists
"""

import re
from pathlib import Path

from tools.design_linters.framework.base_interfaces import BaseLintContext, BaseLintRule
from tools.design_linters.framework.types import LintViolation, Severity


class NoSkipRule(BaseLintRule):
    """Detect and prevent skipping of critical linting rules across all languages."""

    # Critical rules that should NEVER be skipped
    CRITICAL_PYTHON_RULES = {
        "C901",  # Complexity too high
        "W0718",  # Broad exception catching
        "E501",  # Line too long (should be fixed)
        "S",  # Bandit security rules (all S### codes)
        "F401",  # Unused imports (except __init__.py)
    }

    CRITICAL_TYPESCRIPT_RULES = {
        "no-explicit-any",
        "react-hooks/exhaustive-deps",
        "react-hooks/rules-of-hooks",
        "no-console",
    }

    CRITICAL_INFRASTRUCTURE_RULES = {
        "terraform-validate",
        "shellcheck",
    }

    # Skip patterns to detect
    SKIP_PATTERNS = {
        "python": [
            r"#\s*noqa(?::\s*([A-Z]\d+(?:,\s*[A-Z]\d+)*))?",  # noqa or noqa: E501
            r"#\s*pylint:\s*disable=([a-zA-Z0-9_,-]+)",  # pylint: disable=rule-name
            r"#\s*type:\s*ignore(?:\[([a-z0-9_,-]+)\])?",  # type: ignore or type: ignore[rule]
        ],
        "typescript": [
            r"//\s*eslint-disable(?:-next-line)?(?:\s+([a-zA-Z0-9/@_,-]+))?",  # eslint-disable rule-name
            r"//\s*@ts-ignore",  # @ts-ignore
            r"//\s*@ts-nocheck",  # @ts-nocheck
        ],
        "terraform": [
            r"#\s*tflint-ignore:\s*([a-zA-Z0-9_-]+)",  # tflint-ignore: rule-name
        ],
        "shell": [
            r"#\s*shellcheck\s+disable=([A-Z0-9,]+)",  # shellcheck disable=SC2086
        ],
    }

    # Whitelist: Patterns that are allowed to be skipped
    WHITELIST_PATTERNS = {
        "python": [
            r"__init__.py:F401",  # Allow unused imports in __init__.py
        ],
        "typescript": [
            r"\.test\.tsx?:no-explicit-any",  # Allow any in test files
        ],
    }

    @property
    def rule_id(self) -> str:
        """Return the unique identifier for this rule."""
        return "enforcement.no-skip"

    @property
    def rule_name(self) -> str:
        """Return the human-readable name for this rule."""
        return "No Skipping Critical Linting Rules"

    @property
    def description(self) -> str:
        """Return the description of what this rule checks."""
        return "Prevent skipping of critical linting rules - fix the code instead"

    @property
    def severity(self) -> Severity:
        """Return the severity level of violations from this rule."""
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        """Return the categories this rule belongs to."""
        return {"enforcement", "quality", "standards"}

    def check(self, context: BaseLintContext) -> list[LintViolation]:
        """Check file for improper linting rule skips."""
        if not context.file_path or not context.file_content:
            return []

        file_path = Path(context.file_path) if isinstance(context.file_path, str) else context.file_path

        # Determine language from file extension
        language = self._get_language(file_path)
        if not language:
            return []

        violations: list[LintViolation] = []
        lines = context.file_content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            for pattern in self.SKIP_PATTERNS.get(language, []):
                match = re.search(pattern, line)
                if match:
                    skipped_rule = self._extract_skipped_rule(match)
                    if self._is_critical_skip(language, skipped_rule, file_path, line):
                        violations.append(
                            self._create_skip_violation(context, file_path, line_num, line, language, skipped_rule)
                        )

        return violations

    def _get_language(self, file_path: Path) -> str | None:
        """Determine language from file extension."""
        suffix = file_path.suffix
        if suffix == ".py":
            return "python"
        if suffix in {".ts", ".tsx", ".js", ".jsx"}:
            return "typescript"
        if suffix == ".tf":
            return "terraform"
        if suffix == ".sh":
            return "shell"
        return None

    def _extract_skipped_rule(self, match: re.Match[str]) -> str:
        """Extract the specific rule being skipped from the match."""
        # Try to get the captured group (the rule name)
        if match.groups():
            rule = match.group(1)
            return rule if rule else "all"
        return "all"

    def _is_critical_skip(self, language: str, skipped_rule: str, file_path: Path, line: str) -> bool:
        """Check if the skip involves a critical rule."""
        # Check whitelist first
        if self._is_whitelisted(language, file_path, skipped_rule):
            return False

        # For "all" skips (no specific rule), always flag as potential issue
        if skipped_rule == "all":
            return True

        # Check if skipped rule is in critical list
        if language == "python":
            # Handle multiple rules (noqa: E501,W503)
            rules = [r.strip() for r in skipped_rule.split(",")]
            for rule in rules:
                if any(rule.startswith(critical) for critical in self.CRITICAL_PYTHON_RULES):
                    return True
                if rule in self.CRITICAL_PYTHON_RULES:
                    return True
        elif language == "typescript":
            rules = [r.strip() for r in skipped_rule.split(",")]
            if any(rule in self.CRITICAL_TYPESCRIPT_RULES for rule in rules):
                return True
        elif language in {"terraform", "shell"}:
            # All infrastructure skips are critical
            return True

        return False

    def _is_whitelisted(self, language: str, file_path: Path, skipped_rule: str) -> bool:
        """Check if this skip is whitelisted."""
        whitelist = self.WHITELIST_PATTERNS.get(language, [])
        file_path_str = str(file_path)

        for pattern in whitelist:
            if re.search(pattern, file_path_str) or re.search(pattern, f"{file_path_str}:{skipped_rule}"):
                return True

        return False

    def _create_skip_violation(
        self,
        context: BaseLintContext,
        file_path: Path,
        line_num: int,
        line: str,
        language: str,
        skipped_rule: str,
    ) -> LintViolation:
        """Create a violation for an improper skip."""
        rule_display = f"rule '{skipped_rule}'" if skipped_rule != "all" else "rules"

        suggestion = self._generate_suggestion(language, skipped_rule)

        message = f"Skipping {rule_display} is not allowed - fix the code instead"
        description = (
            f"Found skip directive for {rule_display} in {language} code. "
            f"Critical linting rules must not be skipped - the underlying issue should be fixed. "
            f"{suggestion}"
        )

        return self.create_violation(
            context=context,
            message=message,
            description=description,
            line=line_num,
            column=line.index("#") if "#" in line else line.index("//") if "//" in line else 0,
            suggestion=suggestion,
        )

    def _generate_suggestion(self, language: str, skipped_rule: str) -> str:
        """Generate a helpful suggestion for fixing the issue."""
        suggestions = {
            "python": {
                "C901": "Refactor the function to reduce complexity (extract helper functions, simplify logic)",
                "W0718": "Catch specific exception types instead of bare except or Exception",
                "E501": "Break the line into multiple lines or refactor to reduce length",
                "F401": "Remove the unused import or use it in the code",
            },
            "typescript": {
                "no-explicit-any": "Use a specific type instead of 'any' (e.g., unknown, or define an interface)",
                "react-hooks/exhaustive-deps": "Add missing dependencies to the useEffect/useCallback dependency array",
                "react-hooks/rules-of-hooks": "Move hooks to the top level of the function component",
                "no-console": "Use a proper logging service instead of console.log",
            },
        }

        lang_suggestions = suggestions.get(language, {})
        if skipped_rule in lang_suggestions:
            return lang_suggestions[skipped_rule]

        return f"Review the {language} linting rule '{skipped_rule}' and fix the underlying issue"
