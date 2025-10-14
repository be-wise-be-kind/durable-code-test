#!/usr/bin/env python3
"""
Purpose: Multi-language orchestrator for the pluggable design linter framework
Scope: Extends the existing orchestrator to support multiple programming languages
Overview: This module provides a multi-language orchestrator that extends the existing
    Python-focused DefaultLintCoordinator to support multiple programming languages.
    It inherits from BaseCoordinator and manages a registry of language-specific
    analyzers, automatically selecting the appropriate analyzer based on file extensions.
    The orchestrator maintains backward compatibility with existing Python rules while
    enabling new multi-language rules to work across different programming languages.
    It handles rule filtering based on language support, context conversion between
    language-specific and generic contexts, and provides unified reporting across
    all supported languages.
Dependencies: pathlib for file operations, typing for type hints
Exports: MultiLanguageCoordinator, LanguageRegistry
Interfaces: Implements BaseCoordinator for multi-language support
Implementation: Extends existing orchestrator with language-agnostic capabilities
"""

from pathlib import Path
from typing import Any

from loguru import logger

from .analyzer import DefaultLintCoordinator, PythonAnalyzer
from .base_interfaces import BaseCoordinator, BaseLintAnalyzer, BaseLintContext, BaseLintRule
from .interfaces import LintViolation, RuleRegistry


class DefaultLanguageRegistry:
    """Default implementation of language registry."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._analyzers: dict[str, BaseLintAnalyzer] = {}
        self._extension_map: dict[str, str] = {}

        # Register Python analyzer by default
        python_analyzer = PythonAnalyzer()
        self.register_analyzer(python_analyzer)

    def register_analyzer(self, analyzer: BaseLintAnalyzer) -> None:
        """Register a language analyzer."""
        language = analyzer.language_name
        self._analyzers[language] = analyzer

        # Map extensions to language
        for ext in analyzer.get_supported_extensions():
            self._extension_map[ext] = language

        logger.info("Registered %s analyzer for extensions: %s", language, analyzer.get_supported_extensions())

    def get_analyzer(self, language_name: str) -> BaseLintAnalyzer | None:
        """Get analyzer by language name."""
        return self._analyzers.get(language_name)

    def get_analyzer_for_file(self, file_path: Path) -> BaseLintAnalyzer | None:
        """Get appropriate analyzer for a file based on extension."""
        extension = file_path.suffix.lower()
        language = self._extension_map.get(extension)
        if language:
            return self._analyzers.get(language)
        return None

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language names."""
        return list(self._analyzers.keys())

    def get_supported_extensions(self) -> set[str]:
        """Get all supported file extensions."""
        return set(self._extension_map.keys())


class MultiLanguageCoordinator(BaseCoordinator):
    """Multi-language orchestrator that extends the existing Python orchestrator."""

    def __init__(
        self,
        rule_registry: RuleRegistry,
        language_registry: DefaultLanguageRegistry | None = None,
        python_orchestrator: DefaultLintCoordinator | None = None,
    ):
        """Initialize with rule registry and optional language registry."""
        self.rule_registry = rule_registry
        self.language_registry = language_registry or DefaultLanguageRegistry()

        # Use existing Python orchestrator or create a new one
        self.python_orchestrator = python_orchestrator or DefaultLintCoordinator(
            rule_registry=rule_registry,
            analyzers={"python": PythonAnalyzer()},
            reporters={},
        )

    def lint_file(self, file_path: Path, config: dict[str, Any] | None = None) -> list[LintViolation]:
        """Lint a single file using appropriate language analyzer."""
        analyzer = self.language_registry.get_analyzer_for_file(file_path)
        if not analyzer:
            logger.warning("No analyzer available for %s", file_path)
            return []

        # For Python files, use the existing orchestrator for full compatibility
        if analyzer.language_name == "python":
            return self.python_orchestrator.lint_file(file_path, config)

        # For other languages, use the generic approach
        context = analyzer.analyze_file(file_path)
        return self._lint_with_context(context, config or {})

    def _lint_with_context(self, context: BaseLintContext, config: dict[str, Any]) -> list[LintViolation]:
        """Lint using a generic context."""
        violations = []
        enabled_rules = self._get_enabled_rules_for_language(context.language, config)

        for rule in enabled_rules:
            try:
                rule_violations = rule.check(context)
                violations.extend(rule_violations)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Error executing rule %s on %s", rule.rule_id, context.file_path)

        return violations

    def _get_enabled_rules_for_language(self, language: str, config: dict[str, Any]) -> list[BaseLintRule]:
        """Get enabled rules that support the given language."""
        all_rules = self.rule_registry.get_all_rules()
        language_rules = []

        for rule in all_rules:
            # Check if rule is enabled
            if not rule.is_enabled(config):
                continue

            # Check if rule supports this language
            if hasattr(rule, "supports_language") and not rule.supports_language(language):
                continue

            language_rules.append(rule)

        return language_rules

    def lint_directory(
        self,
        directory_path: Path,
        config: dict[str, Any] | None = None,
        recursive: bool = True,
    ) -> list[LintViolation]:
        """Lint all supported files in a directory."""
        config = config or {}
        all_violations = []

        # Get supported extensions from all registered analyzers
        supported_extensions = self.language_registry.get_supported_extensions()

        # Find files to analyze
        pattern = "**/*" if recursive else "*"
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                violations = self.lint_file(file_path, config)
                all_violations.extend(violations)

        return all_violations

    def get_available_rules(self) -> list[str]:
        """Get list of available rule IDs."""
        return [rule.rule_id for rule in self.rule_registry.get_all_rules()]

    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages."""
        return self.language_registry.get_supported_languages()

    def register_analyzer(self, analyzer: BaseLintAnalyzer) -> None:
        """Register a language analyzer."""
        self.language_registry.register_analyzer(analyzer)

    def generate_report(self, violations: list[LintViolation], output_format: str = "text") -> str:
        """Generate a report in the specified format (delegates to Python orchestrator)."""
        return self.python_orchestrator.generate_report(violations, output_format)

    def get_rule_registry(self) -> RuleRegistry:
        """Get the rule registry."""
        return self.rule_registry
