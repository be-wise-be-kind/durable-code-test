#!/usr/bin/env python3
"""
Purpose: Core interfaces for the pluggable design linter framework
Scope: Defines contracts for rules, analyzers, reporters, and orchestrators
Overview: This module establishes the foundational interfaces that enable a pluggable
    architecture for the design linter framework, providing the core abstractions that all
    components must implement. It defines the contracts for lint rules (both AST-based and
    file-based), violation reporting with severity levels, analysis contexts with comprehensive
    file information, and output reporters for various formats. The interfaces support dynamic
    rule discovery and registration, supporting dynamic rule integration without modifying the
    framework core. The design follows SOLID principles with clear separation of concerns,
    dependency injection, and extensibility points. The module also includes ignore directive
    handling for suppressing specific violations, node stack tracking for context-aware analysis,
    and helper functions for creating consistent violation messages across all rules.
Dependencies: abc for abstract base classes, typing for type hints, ast for AST nodes
Exports: LintRule, LintViolation, LintReporter, LintAnalyzer, LintCoordinator
Interfaces: All classes are abstract interfaces requiring implementation
Implementation: Enables plugin architecture with dynamic rule loading
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base_interfaces import BaseLintAnalyzer, BaseLintContext, BaseLintRule
from .ignore_utils import has_file_level_ignore, should_ignore_node
from .types import LintViolation, Severity

# All ignore utility functions are now imported from ignore_utils module


class LintRule(BaseLintRule):
    """Abstract base class for all linting rules (Python-specific, inherits from BaseLintRule)."""

    @abstractmethod
    def check(self, context: "LintContext") -> list[LintViolation]:
        """Check for violations in the given context."""
        raise NotImplementedError("Subclasses must implement check")

    def create_violation_from_node(
        self,
        context: "LintContext",
        node: ast.AST,
        message: str,
        description: str,
        *,
        suggestion: str | None = None,
        violation_context: dict[str, Any] | None = None,
    ) -> LintViolation:
        """Helper method to create a violation from an AST node."""
        # Delegate to the base class method with extracted node info
        return super().create_violation(
            context,
            message=message,
            description=description,
            line=getattr(node, "lineno", 1),
            column=getattr(node, "col_offset", 0),
            suggestion=suggestion,
            violation_context=violation_context,
        )


class _ASTRuleNodeVisitor(ast.NodeVisitor):
    """Helper visitor class to reduce nesting in ASTLintRule.check()."""

    def __init__(self, rule: "ASTLintRule", context: "LintContext") -> None:
        """Initialize visitor with rule and context."""
        self.rule = rule
        self.context = context
        self.violations: list[LintViolation] = []

    def visit(self, node: ast.AST) -> None:
        """Visit node and execute rule checks."""
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")
        self.context.node_stack.append(node)

        # Track current context
        old_function = self.context.current_function
        old_class = self.context.current_class

        update_context_for_node(self.context, node)

        try:
            self._check_node_if_applicable(node)
            self.generic_visit(node)
        finally:
            self._restore_context_and_stack(node, old_function, old_class)

    def _check_node_if_applicable(self, node: ast.AST) -> None:
        """Check node if rule conditions are met."""
        if not self.rule.should_check_node(node, self.context):
            return
        if not self.context.file_content:
            return
        if should_ignore_node(node, self.context.file_content, self.rule.rule_id):
            return
        self.violations.extend(self.rule.check_node(node, self.context))

    def _restore_context_and_stack(self, node: ast.AST, old_function: str | None, old_class: str | None) -> None:
        """Restore context stack and function/class tracking."""
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")
        self.context.node_stack.pop()
        # Only restore if we changed them
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.context.current_function = old_function
        elif isinstance(node, ast.ClassDef):
            self.context.current_class = old_class


class ASTLintRule(LintRule):
    """Base class for rules that analyze AST nodes."""

    @abstractmethod
    def check_node(self, node: ast.AST, context: "LintContext") -> list[LintViolation]:
        """Check a specific AST node for violations."""
        raise NotImplementedError("Subclasses must implement check_node")

    def check(self, context: "LintContext") -> list[LintViolation]:
        """Default implementation that traverses AST and checks each node."""
        violations: list[LintViolation] = []

        # Check for file-level ignore directives
        if context.file_content and has_file_level_ignore(context.file_content, self.rule_id):
            return violations

        if not context.ast_tree:
            return violations

        # Initialize node stack if not already set
        if context.node_stack is None:
            context.node_stack = []

        # Use a visitor to maintain node stack
        visitor = _ASTRuleNodeVisitor(self, context)
        visitor.visit(context.ast_tree)
        return visitor.violations

    def should_check_node(self, node: ast.AST, context: "LintContext") -> bool:  # pylint: disable=unused-argument
        """Determine if this node should be checked by this rule."""
        return True


class FileBasedLintRule(LintRule):
    """Base class for rules that analyze entire files."""

    @abstractmethod
    def check_file(self, file_path: Path, content: str, context: "LintContext") -> list[LintViolation]:
        """Check an entire file for violations."""
        raise NotImplementedError("Subclasses must implement check_file")

    def check(self, context: "LintContext") -> list[LintViolation]:
        """Default implementation that checks entire file."""
        from .ignore_utils import check_file_with_ignores

        return check_file_with_ignores(self, context, self.check_file)


@dataclass
class LintContext(BaseLintContext):  # pylint: disable=too-many-instance-attributes
    """Context information for rule checking (Python-specific, inherits from BaseLintContext)."""

    file_path: Path | None = None
    file_content: str | None = None
    ast_tree: ast.AST | None = None
    current_function: str | None = None
    current_class: str | None = None
    current_module: str | None = None
    node_stack: list[ast.AST] | None = None
    metadata: dict[str, Any] | None = None
    file_ignores: list[str] = field(default_factory=list)  # File-level ignore patterns
    line_ignores: dict[int, list[str]] = field(default_factory=dict)  # Line number -> ignore patterns
    ignore_next_line: set[int] = field(default_factory=set)  # Line numbers to ignore next line

    @property
    def language(self) -> str:
        """Get the programming language of the file."""
        return "python"

    def get_parent_node(self, offset: int = 1) -> ast.AST | None:
        """Get parent node at specified offset in the stack."""
        if self.node_stack and len(self.node_stack) > offset:
            return self.node_stack[-(offset + 1)]
        return None

    def get_context_description(self) -> str:
        """Get human-readable context description."""
        parts = []
        if self.current_module:
            parts.append(f"module {self.current_module}")
        if self.current_class:
            parts.append(f"class {self.current_class}")
        if self.current_function:
            parts.append(f"function {self.current_function}")

        return " -> ".join(parts) if parts else "global scope"


def update_context_for_node(context: "LintContext", node: ast.AST) -> None:
    """Update context based on current node type."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        context.current_function = node.name
    elif isinstance(node, ast.ClassDef):
        context.current_class = node.name


class LintReporter(ABC):
    """Abstract base class for violation reporters."""

    @abstractmethod
    def generate_report(self, violations: list[LintViolation], metadata: dict[str, Any] | None = None) -> str:
        """Generate a report from the list of violations."""
        raise NotImplementedError("Subclasses must implement generate_report")

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """Get list of output formats this reporter supports."""
        raise NotImplementedError("Subclasses must implement get_supported_formats")

    def filter_violations(self, violations: list[LintViolation], filters: dict[str, Any]) -> list[LintViolation]:
        """Filter violations based on criteria."""
        filtered = violations

        filtered = self._filter_by_severity(filtered, filters)
        filtered = self._filter_by_rules(filtered, filters)
        filtered = self._filter_by_files(filtered, filters)

        return filtered

    def _filter_by_severity(self, violations: list[LintViolation], filters: dict[str, Any]) -> list[LintViolation]:
        """Filter violations by minimum severity level."""
        if "min_severity" not in filters:
            return violations

        min_sev = filters["min_severity"]
        severity_order = [Severity.INFO, Severity.WARNING, Severity.ERROR]
        min_index = severity_order.index(min_sev)
        return [v for v in violations if severity_order.index(v.severity) >= min_index]

    def _filter_by_rules(self, violations: list[LintViolation], filters: dict[str, Any]) -> list[LintViolation]:
        """Filter violations by rule IDs."""
        if "rules" not in filters:
            return violations

        rule_ids = set(filters["rules"])
        return [v for v in violations if v.rule_id in rule_ids]

    def _filter_by_files(self, violations: list[LintViolation], filters: dict[str, Any]) -> list[LintViolation]:
        """Filter violations by file patterns."""
        if "files" not in filters:
            return violations

        patterns = filters["files"]
        return [v for v in violations if any(pattern in str(v.file_path) for pattern in patterns)]


class LintAnalyzer(BaseLintAnalyzer):
    """Abstract base class for code analyzers (Python-specific, inherits from BaseLintAnalyzer)."""

    @property
    def language_name(self) -> str:
        """Get the name of the language this analyzer handles."""
        return "python"

    @abstractmethod
    def analyze_file(self, file_path: Path) -> LintContext:
        """Analyze a single file and return context."""
        raise NotImplementedError("Subclasses must implement analyze_file")

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Get file extensions this analyzer supports."""
        raise NotImplementedError("Subclasses must implement get_supported_extensions")


class RuleRegistry(ABC):
    """Abstract interface for rule management."""

    @abstractmethod
    def register_rule(self, rule: LintRule) -> None:
        """Register a new rule."""
        raise NotImplementedError("Subclasses must implement register_rule")

    @abstractmethod
    def unregister_rule(self, rule_id: str) -> None:
        """Unregister a rule by ID."""
        raise NotImplementedError("Subclasses must implement unregister_rule")

    @abstractmethod
    def get_rule(self, rule_id: str) -> LintRule | None:
        """Get a rule by ID."""
        raise NotImplementedError("Subclasses must implement get_rule")

    @abstractmethod
    def get_all_rules(self) -> list[LintRule]:
        """Get all registered rules."""
        raise NotImplementedError("Subclasses must implement get_all_rules")

    @abstractmethod
    def get_rules_by_category(self, category: str) -> list[LintRule]:
        """Get rules belonging to a specific category."""
        raise NotImplementedError("Subclasses must implement get_rules_by_category")

    @abstractmethod
    def discover_rules(self, package_paths: list[str]) -> int:
        """Discover and register rules from package paths."""
        raise NotImplementedError("Subclasses must implement discover_rules")


class LintCoordinator(ABC):
    """Abstract interface for coordinating the linting process (Python-focused)."""

    @abstractmethod
    def lint_file(self, file_path: Path, config: dict[str, Any] | None = None) -> list[LintViolation]:
        """Lint a single file."""
        raise NotImplementedError("Subclasses must implement lint_file")

    @abstractmethod
    def lint_directory(
        self,
        directory_path: Path,
        config: dict[str, Any] | None = None,
        recursive: bool = True,
    ) -> list[LintViolation]:
        """Lint all files in a directory."""
        raise NotImplementedError("Subclasses must implement lint_directory")

    @abstractmethod
    def get_available_rules(self) -> list[str]:
        """Get list of available rule IDs."""
        raise NotImplementedError("Subclasses must implement get_available_rules")

    @abstractmethod
    def generate_report(self, violations: list[LintViolation], output_format: str = "text") -> str:
        """Generate a report in the specified format."""
        raise NotImplementedError("Subclasses must implement generate_report")

    @abstractmethod
    def get_rule_registry(self) -> "RuleRegistry":
        """Get the rule registry."""
        raise NotImplementedError("Subclasses must implement get_rule_registry")


class ConfigurationProvider(ABC):
    """Abstract interface for configuration management."""

    @abstractmethod
    def load_config(self, config_path: Path | None = None) -> dict[str, Any]:
        """Load configuration from file or use defaults."""
        raise NotImplementedError("Subclasses must implement load_config")

    @abstractmethod
    def get_rule_config(self, rule_id: str) -> dict[str, Any]:
        """Get configuration for a specific rule."""
        raise NotImplementedError("Subclasses must implement get_rule_config")

    @abstractmethod
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        raise NotImplementedError("Subclasses must implement is_rule_enabled")

    @abstractmethod
    def get_output_config(self) -> dict[str, Any]:
        """Get output/reporting configuration."""
        raise NotImplementedError("Subclasses must implement get_output_config")
