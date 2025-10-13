#!/usr/bin/env python3
"""
Purpose: File organization and placement linting rule for the design linter framework
Scope: Organization category rule implementation with JSON/YAML-based layout configuration
Overview: This module implements comprehensive file organization rules that ensure proper project
    structure and prevent common placement mistakes that can lead to maintenance issues. It detects
    files placed in incorrect directories such as debug scripts in root, test files outside test
    directories, frontend code mixed with backend, and configuration files in source directories.
    The rule loads configuration from a JSON or YAML layout file that supports both AI-readable guidance
    and machine-readable regex patterns for comprehensive file organization enforcement. It helps
    maintain clean separation of concerns, prevents accidental commits of temporary files, and
    ensures consistent project organization across team members. The implementation includes
    helpful suggestions for where files should be moved and can be configured to enforce
    organization standards specific to each project's architecture.
Dependencies: Framework interfaces, pathlib for path analysis, json/yaml for config loading, re for regex
Exports: FileOrganizationRule implementation
Interfaces: Implements ASTLintRule interface from framework
Implementation: JSON-driven path validation with regex pattern matching
"""

import json
import re
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from tools.design_linters.framework.interfaces import (
    ASTLintRule,
    LintContext,
    LintViolation,
    Severity,
)


class LayoutRulesLoader:
    """Handles loading and parsing of layout rules from configuration files."""

    def __init__(self, layout_file: str):
        """Initialize with layout file path."""
        self.layout_file = layout_file
        self.rules = None
        self._load_rules()

    def _load_rules(self) -> None:
        """Load layout rules from JSON or YAML file."""
        try:
            layout_path = self._get_layout_path()
            if not layout_path.exists():
                logger.warning("Layout rules file not found, using default configuration", file_path=str(layout_path))
                self.rules = self.get_default_rules()
                return

            data = self._load_config_data(layout_path)
            self._process_config_data(data, layout_path)
        except Exception as e:
            logger.error("Error loading layout rules, using defaults", error=str(e), exc_info=True)
            self.rules = self.get_default_rules()

    def _get_layout_path(self) -> Path:
        """Get absolute path to layout file."""
        path = Path(self.layout_file)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    def _load_config_data(self, layout_path: Path) -> dict[str, Any]:
        """Load data from config file."""
        with open(layout_path) as f:
            if layout_path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            return json.load(f)

    def _process_config_data(self, data: dict[str, Any], layout_path: Path) -> None:
        """Process loaded configuration data."""
        if "$schema" in data:
            del data["$schema"]

        # Extract linter_rules if present (from layout.yaml structure)
        if "linter_rules" in data:
            data = data["linter_rules"]

        self.rules = data
        logger.info("Loaded layout rules from file", file_path=str(layout_path))

    def get_rules(self) -> dict[str, Any] | None:
        """Get loaded layout rules."""
        return self.rules

    @staticmethod
    def get_default_rules() -> dict[str, Any]:
        """Get default layout rules if no config file exists."""
        return {
            "paths": {
                ".": {
                    "allow": [
                        "^[^/]+\\.md$",
                        "^[^/]+\\.yml$",
                        "^[^/]+\\.yaml$",
                        "^[^/]+\\.json$",
                        "^[^/]+\\.toml$",
                        "^Makefile",
                        "^Dockerfile",
                        "^\\.gitignore$",
                        "^\\.env",
                        "^requirements.*\\.txt$",
                        "^setup\\.py$",
                        "^conftest\\.py$",
                        "^manage\\.py$",
                    ],
                    "deny": [
                        {"pattern": "^debug[_-].*\\.py$", "reason": "Debug files should not be in the root directory"},
                        {
                            "pattern": "^tmp[_-].*\\.py$",
                            "reason": "Temporary files should not be in the root directory",
                        },
                        {
                            "pattern": "^temp[_-].*\\.py$",
                            "reason": "Temporary files should not be in the root directory",
                        },
                        {"pattern": "^test[_-].*\\.py$", "reason": "Test files should be in test/ directory"},
                        {"pattern": "_test\\.py$", "reason": "Test files should be in test/ directory"},
                        {"pattern": "_spec\\.py$", "reason": "Test files should be in test/ directory"},
                    ],
                }
            }
        }


class PatternMatcher:
    """Handles pattern matching logic for file paths."""

    def match_deny_patterns(self, path_str: str, deny_patterns: list[dict[str, str]]) -> tuple[bool, str | None]:
        """Check if path matches any deny patterns."""
        for deny_item in deny_patterns:
            pattern = deny_item["pattern"]
            if re.search(pattern, path_str, re.IGNORECASE):
                reason = deny_item.get("reason", "File not allowed in this location")
                return True, reason
        return False, None

    def match_allow_patterns(self, path_str: str, allow_patterns: list[str]) -> bool:
        """Check if path matches any allow patterns."""
        return any(re.search(pattern, path_str, re.IGNORECASE) for pattern in allow_patterns)


class GlobalPatternChecker:
    """Checks files against global pattern rules."""

    def __init__(self, pattern_matcher: PatternMatcher):
        """Initialize with pattern matcher."""
        self.pattern_matcher = pattern_matcher

    def check_patterns(
        self, path_str: str, rel_path: Path, global_patterns: dict[str, Any], rule_id: str
    ) -> list[LintViolation]:
        """Check path against global patterns."""
        violations = []

        # Check global deny patterns
        if "deny" in global_patterns:
            is_denied, reason = self.pattern_matcher.match_deny_patterns(path_str, global_patterns["deny"])
            if is_denied:
                violations.append(
                    LintViolation(
                        rule_id=rule_id,
                        message=reason or f"File '{rel_path}' matches denied pattern",
                        description="File placement violates project organization rules",
                        severity=Severity.ERROR,
                        line=1,
                        column=0,
                        file_path=str(rel_path),
                        suggestion=FileSuggestionGenerator.get_suggestion(rel_path.name, path_str),
                    )
                )

        # Check global allow patterns
        if "allow" in global_patterns:
            allow_patterns = global_patterns["allow"]
            if not self.pattern_matcher.match_allow_patterns(path_str, allow_patterns):
                violations.append(
                    LintViolation(
                        rule_id=rule_id,
                        message=f"File '{rel_path}' does not match any allowed patterns",
                        description="File does not match allowed patterns for this location",
                        severity=Severity.WARNING,
                        line=1,
                        column=0,
                        file_path=str(rel_path),
                        suggestion="Ensure file matches project structure patterns",
                    )
                )

        return violations


class DirectoryRuleChecker:
    """Checks files against directory-specific rules."""

    def __init__(self, pattern_matcher: PatternMatcher):
        """Initialize with pattern matcher."""
        self.pattern_matcher = pattern_matcher
        self.current_path_str = ""
        self.current_rel_path = None
        self.current_rule_id = ""
        self.current_directories = {}

    def check_directory_rules(
        self, path_str: str, rel_path: Path, directories: dict[str, Any], rule_id: str
    ) -> list[LintViolation]:
        """Check if file complies with directory-specific rules."""
        # Store state for use by other methods
        self.current_path_str = path_str
        self.current_rel_path = rel_path
        self.current_rule_id = rule_id
        self.current_directories = directories

        violations = []

        # Find matching directory rule
        dir_rule, matched_path = self._find_matching_directory_rule()
        if not dir_rule:
            return violations

        # Check deny patterns first (catches debug, temp, test files with specific patterns)
        if "deny" in dir_rule:
            is_denied, reason = self.pattern_matcher.match_deny_patterns(self.current_path_str, dir_rule["deny"])
            if is_denied:
                violations.append(self._create_deny_violation(matched_path, reason))
                return violations

        # Check for test files in root (catches test files not caught by deny patterns)
        if self._is_test_file_in_root():
            violations.append(self._create_test_file_violation())
            return violations

        # Check allow patterns - if file doesn't match, create appropriate violation
        if "allow" in dir_rule and not self.pattern_matcher.match_allow_patterns(
            self.current_path_str, dir_rule["allow"]
        ):
            # Special case: Python files in root get INFO severity
            is_root_file = "/" not in self.current_path_str
            is_python_file = self.current_path_str.endswith(".py")
            if is_root_file and is_python_file:
                violations.append(self._create_python_file_info(matched_path))
            else:
                violations.append(self._create_allow_violation(matched_path))

        return violations

    def _is_test_file_in_root(self) -> bool:
        """Check if this is a test file in root directory."""
        if len(self.current_rel_path.parts) == 1:
            filename = self.current_rel_path.name.lower()
            # Exclude conftest.py which is a special pytest file that's allowed in root
            if filename == "conftest.py":
                return False
            return filename.startswith("test_") or filename.endswith("_test.py")
        return False

    def _create_test_file_violation(self) -> LintViolation:
        """Create violation for test file in root."""
        return LintViolation(
            rule_id=self.current_rule_id,
            message=f"Test file '{self.current_rel_path}' should not be in project root",
            description="Test files should be organized in dedicated test directories",
            severity=Severity.ERROR,
            line=1,
            column=0,
            file_path=str(self.current_rel_path),
            suggestion="Move test files to test/ or tests/ directory to maintain project organization",
        )

    def _find_matching_directory_rule(self) -> tuple[dict[str, Any] | None, str | None]:
        """Find the most specific directory rule that matches the path."""
        best_match = None
        best_path = None
        best_depth = -1

        for dir_path, rules in self.current_directories.items():
            # Handle root directory matching
            is_root_file = "/" not in self.current_path_str
            matches_root = (dir_path == "." or dir_path == "root") and is_root_file
            matches_prefix = (
                self.current_path_str.startswith(dir_path + "/") if dir_path not in (".", "root") else False
            )

            if matches_root or matches_prefix or self.current_path_str == dir_path:
                depth = len(dir_path.split("/")) if dir_path not in (".", "root") else 0
                if depth > best_depth or (matches_root and best_depth == -1):
                    best_match = rules
                    best_path = dir_path
                    best_depth = depth if depth > 0 else 0

        return best_match, best_path

    def _create_deny_violation(self, matched_path: str | None, reason: str | None) -> LintViolation:
        """Create violation for denied file."""
        filename = self.current_rel_path.name
        message = f"File '{self.current_rel_path}' not allowed in {matched_path or 'this location'}"
        if reason:
            message = f"{message}: {reason}"

        # Generate appropriate suggestion based on filename
        suggestion = FileSuggestionGenerator.get_suggestion(filename, self.current_path_str)

        return LintViolation(
            rule_id=self.current_rule_id,
            message=message,
            description="File violates directory-specific organization rules",
            severity=Severity.ERROR,
            line=1,
            column=0,
            file_path=str(self.current_rel_path),
            suggestion=suggestion,
        )

    def _create_allow_violation(self, matched_path: str | None) -> LintViolation:
        """Create violation for file not matching allow patterns."""
        message = (
            f"File '{self.current_rel_path}' does not match allowed patterns for {matched_path or 'this directory'}"
        )
        suggestion = f"Ensure file type is appropriate for {matched_path or 'this location'}"

        return LintViolation(
            rule_id=self.current_rule_id,
            message=message,
            description="File does not match allowed patterns for this directory",
            severity=Severity.WARNING,
            line=1,
            column=0,
            file_path=str(self.current_rel_path),
            suggestion=suggestion,
        )

    def _create_python_file_info(self, matched_path: str | None) -> LintViolation:
        """Create INFO violation for Python file in root directory."""
        return LintViolation(
            rule_id=self.current_rule_id,
            message=f"Python file '{self.current_rel_path}' is in the root directory",
            description="Consider if this file belongs in a more specific directory",
            severity=Severity.INFO,
            line=1,
            column=0,
            file_path=str(self.current_rel_path),
            suggestion="Move to src/, lib/, or appropriate module directory if this is application code",
        )


class FilePlacementChecker:
    """Handles the actual file placement validation logic."""

    def __init__(self, layout_rules: dict[str, Any]):
        """Initialize with layout rules."""
        self.layout_rules = layout_rules
        self.pattern_matcher = PatternMatcher()
        self.global_checker = GlobalPatternChecker(self.pattern_matcher)
        self.directory_checker = DirectoryRuleChecker(self.pattern_matcher)

    def check_file_placement(self, file_path: Path, rule_id: str) -> list[LintViolation]:
        """Check if file is properly placed according to layout rules."""
        violations = []

        # Get relative path from project root
        try:
            cwd = Path.cwd()
            rel_path = file_path.relative_to(cwd) if file_path.is_absolute() else file_path
        except ValueError as e:
            logger.error("File is outside project directory", file_path=str(file_path), error=str(e))
            return violations

        # Convert to string for pattern matching
        path_str = str(rel_path).replace("\\", "/")

        # Check directory-specific rules first (support both "paths" and "directories" keys)
        directories = self.layout_rules.get("directories") or self.layout_rules.get("paths")
        if directories:
            dir_violations = self.directory_checker.check_directory_rules(path_str, rel_path, directories, rule_id)
            violations.extend(dir_violations)

        # Check global patterns only if not already flagged by directory rules
        if not violations and "global_patterns" in self.layout_rules:
            global_violations = self.global_checker.check_patterns(
                path_str, rel_path, self.layout_rules["global_patterns"], rule_id
            )
            violations.extend(global_violations)

        return violations


class FileSuggestionGenerator:
    """Generates suggestions for file placement."""

    @staticmethod
    def get_suggestion(filename: str, pattern: str | None) -> str:
        """Get suggestion for where to move a file based on its type."""
        filename_lower = filename.lower()

        # Check for debug/temp files first (before test check)
        if filename_lower.startswith("debug"):
            return "Move to debug/ directory, or remove debug files if not needed"

        if filename_lower.startswith(("temp", "tmp")):
            return "Move to tmp/ directory, or remove temporary files if not needed"

        # Then check for test files
        if "test" in filename_lower:
            return "Move to test/ or tests/ directory"

        if filename.endswith((".ts", ".tsx", ".jsx")):
            return FileSuggestionGenerator._get_typescript_suggestion(filename)

        if filename.endswith(".py"):
            return FileSuggestionGenerator._get_python_suggestion(pattern)

        if filename.endswith(".log"):
            return "Move to logs/ directory or add to .gitignore"

        return "Review file organization and move to appropriate directory"

    @staticmethod
    def _get_typescript_suggestion(filename: str) -> str:
        """Get suggestion for TypeScript/React files."""
        if "component" in filename.lower():
            return "Move to frontend/components/ or src/components/"
        elif "hook" in filename.lower():
            return "Move to frontend/hooks/ or src/hooks/"
        elif "util" in filename.lower() or "helper" in filename.lower():
            return "Move to frontend/utils/ or src/utils/"
        else:
            return "Move to frontend/src/ or appropriate frontend directory"

    @staticmethod
    def _get_python_suggestion(pattern: str | None) -> str:
        """Get suggestion for Python files."""
        if pattern and "debug" in pattern:
            return "Move to debug/ directory or remove debug code"
        else:
            return "Move to src/, lib/, or appropriate module directory"


class FileOrganizationRule(ASTLintRule):
    """Check file organization and placement."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the rule with optional configuration."""
        super().__init__()
        self.config = config or {}
        layout_file = self.config.get("layout_file", ".ai/layout.yaml")

        # Load layout rules
        loader = LayoutRulesLoader(layout_file)
        layout_rules = loader.get_rules()

        # Store the layout rules on the instance
        self.layout_rules = layout_rules

        # Create placement checker
        self.placement_checker = FilePlacementChecker(layout_rules) if layout_rules else None

    @property
    def rule_id(self) -> str:
        """Return the unique identifier for this rule."""
        return "organization.file-placement"

    @property
    def rule_name(self) -> str:
        """Return the human-readable name for this rule."""
        return "File Placement Check"

    @property
    def description(self) -> str:
        """Return the description of what this rule checks."""
        return "Ensure files are placed in appropriate directories according to project structure"

    @property
    def severity(self) -> Severity:
        """Return the severity level of violations from this rule."""
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        """Return the categories this rule belongs to."""
        return {"organization", "structure"}

    def should_check_node(self, node: Any, context: LintContext) -> bool:
        """Only check Module nodes (file-level)."""
        import ast

        return isinstance(node, ast.Module)

    def check_node(self, node: Any, context: LintContext) -> list[LintViolation]:
        """Check if file is properly organized."""
        if not self.placement_checker:
            return []

        file_path = Path(context.file_path) if hasattr(context, "file_path") else None
        if not file_path:
            return []

        return self.placement_checker.check_file_placement(file_path, self.rule_id)
