#!/usr/bin/env python3
"""
Purpose: Core analyzer and orchestrator for the pluggable linter framework
Scope: Coordinates rule execution, context management, and result aggregation
Overview: This module implements the core orchestration and analysis engine for the pluggable
    linter framework, serving as the central coordinator for all linting operations. It provides
    the PythonAnalyzer class that parses Python source files into AST representations and manages
    the analysis context including file paths, source content, and node tracking. The
    DefaultLintCoordinator coordinates the execution of multiple lint rules across multiple files,
    handling rule discovery, configuration management, parallel execution, and result aggregation.
    The module implements sophisticated context tracking with node stacks for hierarchical analysis,
    ignore directive parsing for suppressing specific violations, and comprehensive error handling
    to ensure robust operation even when individual rules fail. The design follows SOLID principles
    with clear separation between analysis, orchestration, and reporting concerns.
Dependencies: ast for Python AST parsing, pathlib for file operations
Exports: PythonAnalyzer, LintCoordinator, DefaultLintCoordinator
Interfaces: Implements LintAnalyzer and LintCoordinator interfaces
Implementation: Visitor pattern with plugin architecture coordination
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from .interfaces import (
    ASTLintRule,
    ConfigurationProvider,
    LintAnalyzer,
    LintContext,
    LintCoordinator,
    LintReporter,
    LintRule,
    LintViolation,
    RuleRegistry,
    has_file_level_ignore,
    should_ignore_node,
    update_context_for_node,
)


class PythonAnalyzer(LintAnalyzer):
    """Analyzer for Python source code using AST parsing."""

    def __init__(self) -> None:
        """Initialize Python analyzer."""

    def analyze_file(self, file_path: Path) -> LintContext:
        """Analyze a Python file and return rich context."""
        try:
            return self._parse_file_successfully(file_path)
        except SyntaxError as e:
            logger.error("Syntax error in %s: %s", file_path, e)
            return self._handle_syntax_error(file_path, e)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Error analyzing %s", file_path)
            return self._handle_analysis_error(file_path)

    def _parse_file_successfully(self, file_path: Path) -> LintContext:
        """Parse a file successfully and return context."""
        with open(file_path, encoding="utf-8") as file:
            content = file.read()

        ast_tree = ast.parse(content, filename=str(file_path))

        context = LintContext(
            file_path=file_path,
            file_content=content,
            ast_tree=ast_tree,
            current_module=self._get_module_name(file_path),
            node_stack=[],
            metadata={"encoding": "utf-8", "ast_parsed": True},
        )

        # Parse ignore directives
        from .ignore_utils import parse_ignore_directives

        parse_ignore_directives(content, context)
        return context

    def _handle_syntax_error(self, file_path: Path, error: SyntaxError) -> LintContext:
        """Handle syntax errors during file analysis."""
        logger.error("Syntax error in %s: %s", file_path, error)
        return LintContext(
            file_path=file_path,
            file_content=None,
            metadata={"syntax_error": str(error), "ast_parsed": False},
        )

    def _handle_analysis_error(self, file_path: Path) -> LintContext:
        """Handle general errors during file analysis."""
        # Error already logged with exception details in the caller
        return LintContext(
            file_path=file_path,
            metadata={"error": "Analysis failed", "ast_parsed": False},
        )

    def get_supported_extensions(self) -> set[str]:
        """Get file extensions this analyzer supports."""
        return {".py", ".pyi"}

    def _get_module_name(self, file_path: Path) -> str:
        """Extract module name from file path."""
        return file_path.stem


class ContextualASTVisitor(ast.NodeVisitor):
    """AST visitor that maintains context and executes rules."""

    def __init__(self, context: LintContext, rules: list[ASTLintRule], config: dict[str, Any]):
        """Initialize visitor with context and rules."""
        self.context = context
        self.rules = rules
        self.config = config
        self.violations: list[LintViolation] = []

        # Initialize context tracking
        if self.context.node_stack is None:
            self.context.node_stack = []

    def visit(self, node: ast.AST) -> None:
        """Visit node and execute applicable rules."""
        # Push node to context stack
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")
        self.context.node_stack.append(node)

        # Update context based on node type
        self._update_context_for_node(node)

        # Execute AST-based rules
        self._execute_rules_for_node(node)

        # Continue visiting child nodes
        self.generic_visit(node)

        # Pop node from context stack
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")
        self.context.node_stack.pop()

        # Restore previous context
        self._restore_context_for_node(node)

    def _update_context_for_node(self, node: ast.AST) -> None:
        """Update context based on current node type."""
        update_context_for_node(self.context, node)

    def _restore_context_for_node(self, node: ast.AST) -> None:
        """Restore context when leaving a node."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._restore_function_context()
        elif isinstance(node, ast.ClassDef):
            self._restore_class_context()

    def _restore_function_context(self) -> None:
        """Restore function context from stack."""
        self.context.current_function = None
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")

        for stack_node in reversed(self.context.node_stack[:-1]):
            if isinstance(stack_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.context.current_function = stack_node.name
                break

    def _restore_class_context(self) -> None:
        """Restore class context from stack."""
        self.context.current_class = None
        if self.context.node_stack is None:
            raise RuntimeError("Node stack should be initialized")

        for stack_node in reversed(self.context.node_stack[:-1]):
            if isinstance(stack_node, ast.ClassDef):
                self.context.current_class = stack_node.name
                break

    def _execute_rules_for_node(self, node: ast.AST) -> None:
        """Execute all applicable rules for the current node."""
        for rule in self.rules:
            if self._should_execute_rule(rule, node):
                self._execute_single_rule(rule, node)

    def _should_execute_rule(self, rule: ASTLintRule, node: ast.AST) -> bool:
        """Check if a rule should be executed for the given node."""
        if not rule.is_enabled(self.config):
            return False

        return isinstance(rule, ASTLintRule) and rule.should_check_node(node, self.context)

    def _execute_single_rule(self, rule: ASTLintRule, node: ast.AST) -> None:
        """Execute a single rule safely and handle errors."""
        try:
            # Check file-level ignore
            if self.context.file_content and has_file_level_ignore(self.context.file_content, rule.rule_id):
                return

            # Check node-level ignore (line-level and ignore-next-line)
            if self.context.file_content and should_ignore_node(node, self.context.file_content, rule.rule_id):
                return

            violations = rule.check_node(node, self.context)
            self.violations.extend(violations)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Error executing rule %s on %s", rule.rule_id, type(node).__name__)


@dataclass
class LintResults:
    """Container for linting results and metadata."""

    violations: list[LintViolation] = field(default_factory=list)
    files_analyzed: int = 0
    files_with_violations: int = 0
    rules_executed: int = 0
    analysis_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        by_severity: dict[str, int] = {}
        by_rule: dict[str, int] = {}

        for violation in self.violations:
            # Count by severity
            sev_key = violation.severity.value
            by_severity[sev_key] = by_severity.get(sev_key, 0) + 1

            # Count by rule
            by_rule[violation.rule_id] = by_rule.get(violation.rule_id, 0) + 1

        return {
            "total_violations": len(self.violations),
            "files_analyzed": self.files_analyzed,
            "files_with_violations": self.files_with_violations,
            "rules_executed": self.rules_executed,
            "analysis_time_ms": self.analysis_time_ms,
            "by_severity": by_severity,
            "by_rule": by_rule,
        }


class _FileDiscoveryService:
    """Service for discovering files to analyze."""

    def find_files_to_analyze(
        self,
        directory: Path,
        include_patterns: list[str],
        exclude_patterns: list[str],
        recursive: bool,
    ) -> list[Path]:
        """Find files to analyze based on patterns."""
        import fnmatch  # pylint: disable=import-outside-toplevel

        files = []
        pattern = "**/*" if recursive else "*"

        for path in directory.glob(pattern):
            if self._should_analyze_path(path, directory, include_patterns, exclude_patterns, fnmatch=fnmatch):
                files.append(path)

        return files

    def _should_analyze_path(
        self, path: Path, directory: Path, include_patterns: list[str], exclude_patterns: list[str], *, fnmatch: Any
    ) -> bool:
        """Determine if a path should be analyzed based on patterns."""
        if not path.is_file():
            return False

        relative_path = path.relative_to(directory)

        if not self._matches_include_patterns(relative_path, include_patterns, fnmatch):
            return False

        return not self._matches_exclude_patterns(relative_path, exclude_patterns, fnmatch)

    def _matches_include_patterns(self, relative_path: Path, include_patterns: list[str], fnmatch: Any) -> bool:
        """Check if path matches include patterns."""
        return any(fnmatch.fnmatch(str(relative_path), pattern) for pattern in include_patterns)

    def _matches_exclude_patterns(self, relative_path: Path, exclude_patterns: list[str], fnmatch: Any) -> bool:
        """Check if path matches exclude patterns."""
        return any(fnmatch.fnmatch(str(relative_path), pattern) for pattern in exclude_patterns)


class _RuleExecutionService:
    """Service for executing linting rules."""

    def execute_all_rules(
        self, rules: list[LintRule], context: LintContext, config: dict[str, Any]
    ) -> list[LintViolation]:
        """Execute all applicable rules for the given context."""
        violations = []
        violations.extend(self.execute_file_based_rules(rules, context, config))

        if context.ast_tree:
            violations.extend(self.execute_ast_based_rules(rules, context, config))

        return violations

    def execute_file_based_rules(
        self, rules: list[LintRule], context: LintContext, config: dict[str, Any]
    ) -> list[LintViolation]:
        """Execute file-based rules."""
        del config  # Currently unused but part of interface
        from .interfaces import FileBasedLintRule  # pylint: disable=import-outside-toplevel

        violations = []
        file_based_rules = [rule for rule in rules if isinstance(rule, FileBasedLintRule)]

        for rule in file_based_rules:
            violations.extend(self._execute_single_file_rule(rule, context))

        return violations

    def execute_ast_based_rules(
        self, rules: list[LintRule], context: LintContext, config: dict[str, Any]
    ) -> list[LintViolation]:
        """Execute AST-based rules using visitor pattern."""
        from .interfaces import ASTLintRule as ASTRule  # pylint: disable=import-outside-toplevel

        ast_rules = [rule for rule in rules if isinstance(rule, ASTRule)]

        if not ast_rules or not context.ast_tree:
            return []

        visitor = ContextualASTVisitor(context, ast_rules, config)
        visitor.visit(context.ast_tree)
        return visitor.violations

    def _execute_single_file_rule(self, rule: Any, context: LintContext) -> list[LintViolation]:
        """Execute a single file-based rule with error handling."""
        try:
            return rule.check(context)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Error executing file rule %s", rule.rule_id)
            return []


class DefaultLintCoordinator(LintCoordinator):
    """Default implementation of the linting orchestrator."""

    def __init__(
        self,
        rule_registry: RuleRegistry,
        analyzers: dict[str, LintAnalyzer] | None = None,
        reporters: dict[str, LintReporter] | None = None,
        config_provider: ConfigurationProvider | None = None,
    ):
        """Initialize orchestrator with dependencies."""
        self.rule_registry = rule_registry
        self.analyzers = analyzers or {"python": PythonAnalyzer()}
        self.reporters = reporters or {}
        self.config_provider = config_provider
        self._file_discovery = _FileDiscoveryService()
        self._rule_execution = _RuleExecutionService()

    def lint_file(self, file_path: Path, config: dict[str, Any] | None = None) -> list[LintViolation]:
        """Lint a single file."""
        config = config or self._get_default_config()

        analyzer = self._get_analyzer_for_file(file_path)
        if not analyzer:
            logger.warning("No analyzer available for %s", file_path)
            return []

        context = analyzer.analyze_file(file_path)
        if not self._should_analyze_context(context):
            return []

        enabled_rules = self._get_enabled_rules(config)
        return self._rule_execution.execute_all_rules(enabled_rules, context, config)

    def _should_analyze_context(self, context: LintContext) -> bool:
        """Determine if context should be analyzed based on AST availability."""
        return bool(context.ast_tree or not (context.metadata or {}).get("ast_parsed", True))

    def lint_directory(
        self,
        directory_path: Path,
        config: dict[str, Any] | None = None,
        recursive: bool = True,
    ) -> list[LintViolation]:
        """Lint all supported files in a directory."""
        config = config or self._get_default_config()

        include_patterns = config.get("include", ["**/*.py"])
        exclude_patterns = config.get("exclude", ["__pycache__/**", ".git/**", ".venv/**"])

        files_to_analyze = self._file_discovery.find_files_to_analyze(
            directory_path, include_patterns, exclude_patterns, recursive
        )
        return self._lint_file_list(files_to_analyze, config)

    def _lint_file_list(self, files: list[Path], config: dict[str, Any]) -> list[LintViolation]:
        """Lint a list of files and aggregate violations."""
        all_violations = []
        for file_path in files:
            violations = self._lint_single_file_safely(file_path, config)
            all_violations.extend(violations)
        return all_violations

    def _lint_single_file_safely(self, file_path: Path, config: dict[str, Any]) -> list[LintViolation]:
        """Lint a single file with error handling."""
        try:
            return self.lint_file(file_path, config)
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Error linting %s", file_path)
            return []

    def get_available_rules(self) -> list[str]:
        """Get list of available rule IDs."""
        return [rule.rule_id for rule in self.rule_registry.get_all_rules()]

    def generate_report(self, violations: list[LintViolation], output_format: str = "text") -> str:
        """Generate a report in the specified format."""
        if output_format not in self.reporters:
            from .reporters import ReporterFactory  # pylint: disable=import-outside-toplevel

            reporter = ReporterFactory.create_reporter(output_format)
        else:
            reporter = self.reporters[output_format]

        metadata = {
            "timestamp": str(__import__("datetime").datetime.now()),
            "total_violations": len(violations),
            "files_with_violations": len({v.file_path for v in violations}),
        }

        return reporter.generate_report(violations, metadata)

    def get_rule_registry(self) -> RuleRegistry:
        """Get the rule registry."""
        return self.rule_registry

    def _get_analyzer_for_file(self, file_path: Path) -> LintAnalyzer | None:
        """Get appropriate analyzer for file based on extension."""
        extension = file_path.suffix.lower()

        for analyzer in self.analyzers.values():
            if extension in analyzer.get_supported_extensions():
                return analyzer

        return None

    def _get_enabled_rules(self, config: dict[str, Any]) -> list[LintRule]:
        """Get list of enabled rules based on configuration."""
        all_rules = self.rule_registry.get_all_rules()

        # Filter by categories if specified
        categories = config.get("categories")
        if categories:
            # Only include rules that have at least one of the specified categories
            filtered_rules = []
            for rule in all_rules:
                if any(cat in categories for cat in rule.categories):
                    filtered_rules.append(rule)
            all_rules = filtered_rules

        return [rule for rule in all_rules if rule.is_enabled(config)]

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        if self.config_provider:
            return self.config_provider.load_config()

        return {
            "rules": {},  # All rules enabled by default
            "include": ["**/*.py"],
            "exclude": ["__pycache__/**", ".git/**", ".venv/**", "**/.pytest_cache/**"],
        }
