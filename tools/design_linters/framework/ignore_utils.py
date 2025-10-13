#!/usr/bin/env python3
# design-lint: ignore-file[literals.*]
"""
Purpose: Utilities for handling ignore/suppress directives in code
Scope: Framework utilities for skipping specific linting violations
Overview: This module provides comprehensive ignore directive handling for the design linter
    framework, allowing developers to suppress specific violations when necessary while
    maintaining code quality standards. It supports multiple ignore patterns including file-level
    ignores for entire files, line-level ignores for specific lines, next-line ignores for the
    following line, and rule-specific patterns using wildcards. The module parses special comments
    in source code to identify ignore directives, validates their syntax, and efficiently matches
    violations against ignore patterns. It maintains ignore state throughout the analysis process,
    integrates with the context tracking system, and provides detailed reporting of which
    violations were suppressed. The implementation ensures ignored violations are tracked for
    audit purposes while preventing them from appearing in final reports.
Dependencies: AST, re for pattern matching
Exports: Functions for checking and processing ignore directives
Interfaces: Used by linting rules to determine if violations should be skipped
Implementation: Pattern-based detection of ignore comments
"""

import ast
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import LintContext
    from .types import LintViolation

# Common ignore directive patterns
IGNORE_PATTERNS = [
    r"#\s*design-lint:\s*ignore",  # Our custom ignore directive
    r"#\s*design-lint:\s*disable",  # Alternative disable directive
    r"#\s*noqa",  # Standard Python linting ignore
    r"#\s*type:\s*ignore",  # Type checking ignore
]

# Specific rule ignore patterns (e.g., # thailint: ignore[magic-numbers])
SPECIFIC_RULE_PATTERN = r"#\s*design-lint:\s*(?:ignore|disable)\[([^\]]+)\]"


def _has_general_ignore(line: str) -> bool:
    """Check if line has general ignore patterns."""
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in IGNORE_PATTERNS)


def _rule_matches_ignore(rule_id: str, ignored_rule: str) -> bool:
    """Check if a rule ID matches an ignored rule pattern."""
    if ignored_rule.endswith("*"):
        prefix = ignored_rule[:-1]
        return rule_id.startswith(prefix)
    return ignored_rule == rule_id


def _has_specific_rule_ignore(line: str, rule_id: str) -> bool:
    """Check if line has specific rule ignore for given rule_id."""
    match = re.search(SPECIFIC_RULE_PATTERN, line, re.IGNORECASE)
    if not match:
        return False

    ignored_rules = [r.strip() for r in match.group(1).split(",")]
    return any(_rule_matches_ignore(rule_id, ignored_rule) for ignored_rule in ignored_rules)


def should_ignore_line(file_content: str, line_number: int, rule_id: str | None = None) -> bool:
    """
    Check if a specific line should be ignored based on inline comments.

    Args:
        file_content: The full file content
        line_number: The line number to check (1-indexed)
        rule_id: Optional specific rule ID to check for

    Returns:
        True if the line should be ignored, False otherwise
    """
    if not file_content:
        return False

    lines = file_content.splitlines()
    if line_number < 1 or line_number > len(lines):
        return False

    line = lines[line_number - 1]

    # Check for general ignore patterns
    if _has_general_ignore(line):
        return True

    # Check for specific rule ignores
    return bool(rule_id and _has_specific_rule_ignore(line, rule_id))


def should_ignore_node(node: ast.AST, file_content: str, rule_id: str) -> bool:
    """Check if an AST node should be ignored for a specific rule."""
    if not hasattr(node, "lineno"):
        return False

    line_num = node.lineno
    lines = file_content.split("\n")

    # Check if line is in ignore_next_line set (previous line had ignore-next-line)
    if line_num in {
        line_num
        for line_num in range(1, len(lines) + 1)
        if line_num > 1 and "# design-lint: ignore-next-line" in lines[line_num - 2]
    }:
        return True

    # Check line-level ignore on same line
    if line_num <= len(lines):
        line_content = lines[line_num - 1]  # lines are 1-indexed
        if "# design-lint: ignore[" in line_content:
            pattern = _extract_ignore_pattern(line_content, "ignore")
            if pattern and _matches_rule_pattern(rule_id, pattern):
                return True

    return False


def should_ignore_violation(violation: "LintViolation", file_content: str) -> bool:
    """
    Check if a violation should be ignored based on its location.

    Args:
        violation: The violation object (must have line and rule_id attributes)
        file_content: The full file content

    Returns:
        True if the violation should be ignored, False otherwise
    """
    lines = file_content.split("\n")

    # Check line-level ignore on same line
    if violation.line <= len(lines):
        line_content = lines[violation.line - 1]  # lines are 1-indexed
        if "# design-lint: ignore[" in line_content:
            pattern = _extract_ignore_pattern(line_content, "ignore")
            if pattern and _matches_rule_pattern(violation.rule_id, pattern):
                return True

    # Check ignore-next-line directive on previous line
    if violation.line > 1:
        prev_line = lines[violation.line - 2]  # previous line
        if "# design-lint: ignore-next-line" in prev_line:
            return True

    return False


def extract_ignore_next_line_directives(file_content: str) -> set[int]:
    """
    Extract line numbers that should be ignored based on "ignore next line" directives.

    Args:
        file_content: The full file content

    Returns:
        Set of line numbers (1-indexed) that should be ignored
    """
    ignored_lines = set()
    lines = file_content.splitlines()

    for i, line in enumerate(lines):
        # Check for "ignore next line" pattern
        if not re.search(r"#\s*design-lint:\s*ignore-next-line", line, re.IGNORECASE):
            continue

        # Find the next non-empty line to ignore
        next_line_num = _find_next_non_empty_line(lines, i + 1)
        if next_line_num is not None:
            ignored_lines.add(next_line_num)  # Already 1-indexed

    return ignored_lines


def _find_next_non_empty_line(lines: list[str], start_index: int) -> int | None:
    """Find the next non-empty line starting from the given index.

    Args:
        lines: List of lines to search
        start_index: Index to start searching from (0-indexed)

    Returns:
        1-indexed line number of the next non-empty line, or None if not found
    """
    for j in range(start_index, len(lines)):
        if lines[j].strip():
            return j + 1  # Convert to 1-indexed
    return None


def has_file_level_ignore(file_content: str, rule_id: str) -> bool:
    """
    Check if the entire file should be ignored based on file-level directives.

    Args:
        file_content: The full file content
        rule_id: Optional specific rule ID to check for

    Returns:
        True if the entire file should be ignored, False otherwise
    """
    if not file_content:
        return False

    # Check first few lines for file-level ignore directives
    lines = file_content.splitlines()[:10]  # Check first 10 lines

    for line in lines:
        # Check for general file-level ignore pattern (ignore all rules)
        if re.search(r"#\s*design-lint:\s*ignore-file\s*$", line, re.IGNORECASE):
            return True

        # Check for specific rule file-level ignore
        match = re.search(r"#\s*design-lint:\s*ignore-file\[([^\]]+)\]", line, re.IGNORECASE)
        if match and rule_id:
            ignored_rules = [r.strip() for r in match.group(1).split(",")]
            if any(_rule_matches_ignore(rule_id, ignored_rule) for ignored_rule in ignored_rules):
                return True

    return False


def _extract_ignore_pattern(line: str, directive_type: str) -> str | None:
    """Extract ignore pattern from directive line."""
    if directive_type == "ignore-file":
        match = re.search(r"# design-lint: ignore-file\[([^\]]+)\]", line)
    elif directive_type == "ignore":
        match = re.search(r"# design-lint: ignore\[([^\]]+)\]", line)
    else:
        return None

    return match.group(1) if match else None


def _matches_rule_pattern(rule_id: str, pattern: str) -> bool:
    """Check if rule ID matches ignore pattern."""
    # Handle comma-separated patterns
    patterns = [p.strip() for p in pattern.split(",")]

    for p in patterns:
        if p == rule_id:
            return True

        # Handle wildcard patterns like "literals.*"
        if p.endswith(".*"):
            prefix = p[:-2]
            if rule_id.startswith(prefix + "."):
                return True

    return False


# Function removed - using the original version above


def parse_ignore_directives(file_content: str, context: "LintContext") -> None:
    """Parse ignore directives from file content and populate context."""
    lines = file_content.split("\n")

    for line_num, line in enumerate(lines, 1):
        _process_file_level_ignore(line_num, line, context)
        _process_line_level_ignore(line_num, line, context)
        _process_ignore_next_line(line_num, line, context)


def _process_file_level_ignore(line_num: int, line: str, context: "LintContext") -> None:
    """Process file-level ignore directives."""
    if line_num > 10 or "# design-lint: ignore-file[" not in line:
        return
    pattern = _extract_ignore_pattern(line, "ignore-file")
    if pattern:
        context.file_ignores.append(pattern)


def _process_line_level_ignore(line_num: int, line: str, context: "LintContext") -> None:
    """Process line-level ignore directives."""
    if "# design-lint: ignore[" not in line:
        return
    pattern = _extract_ignore_pattern(line, "ignore")
    if not pattern:
        return
    if line_num not in context.line_ignores:
        context.line_ignores[line_num] = []
    context.line_ignores[line_num].append(pattern)


def _process_ignore_next_line(line_num: int, line: str, context: "LintContext") -> None:
    """Process ignore-next-line directives."""
    if "# design-lint: ignore-next-line" in line:
        context.ignore_next_line.add(line_num + 1)  # Next line


def check_file_with_ignores(rule_instance, context, check_file_method):
    """
    Common implementation for file-based rule checking with ignore handling.

    Args:
        rule_instance: The rule instance (must have rule_id attribute)
        context: The lint context (must have file_content, file_path attributes)
        check_file_method: The method to call for file checking

    Returns:
        List of violations after filtering ignored ones
    """
    # Check for file-level ignore directives
    if context.file_content and has_file_level_ignore(context.file_content, rule_instance.rule_id):
        return []

    if context.file_path and context.file_content:
        violations = check_file_method(context.file_path, context.file_content, context)
        # Filter out violations on ignored lines
        if context.file_content:
            violations = [v for v in violations if not should_ignore_violation(v, context.file_content)]
        return violations

    return []


def create_violation_from_data(
    rule_id: str,
    file_path: str,
    *,
    line: int,
    column: int,
    severity,
    message: str,
    description: str,
    suggestion: str | None = None,
    violation_context: dict | None = None,
):
    """Helper function to create a LintViolation with consistent structure."""
    from .types import LintViolation

    return LintViolation(
        rule_id=rule_id,
        file_path=file_path,
        line=line,
        column=column,
        severity=severity,
        message=message,
        description=description,
        suggestion=suggestion,
        context=violation_context,
    )
