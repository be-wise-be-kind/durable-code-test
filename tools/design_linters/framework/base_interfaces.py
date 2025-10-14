#!/usr/bin/env python3
"""
Purpose: Extended base interfaces for multi-language support in the design linter framework
Scope: Extends existing interfaces with language-agnostic capabilities while maintaining backward compatibility
Overview: This module extends the existing Python-specific interfaces to support multiple
    programming languages through inheritance. The base classes provide language-agnostic
    functionality while the existing Python classes inherit from them, ensuring all existing
    Python rules continue to work without modification. New language support can be added
    by implementing the base interfaces, and rules can be written to work across languages
    by inheriting from the base classes instead of the Python-specific ones. The design
    maintains complete backward compatibility while enabling future multi-language support.
Dependencies: abc for abstract base classes, typing for type hints, pathlib for paths
Exports: BaseLintRule, BaseLintAnalyzer, BaseLintContext, BaseCoordinator
Interfaces: Language-agnostic base classes that existing Python classes inherit from
Implementation: Inheritance-based multi-language support with backward compatibility
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# Import common types
from .types import LintViolation, Severity


class BaseLintContext(ABC):
    """Base class for language-agnostic lint contexts."""

    @property
    @abstractmethod
    def file_path(self) -> Path | None:
        """Get the file path being analyzed."""
        raise NotImplementedError("Subclasses must implement file_path")

    @property
    @abstractmethod
    def file_content(self) -> str | None:
        """Get the file content being analyzed."""
        raise NotImplementedError("Subclasses must implement file_content")

    @property
    @abstractmethod
    def language(self) -> str:
        """Get the programming language of the file."""
        raise NotImplementedError("Subclasses must implement language")

    @abstractmethod
    def get_context_description(self) -> str:
        """Get human-readable context description."""
        raise NotImplementedError("Subclasses must implement get_context_description")


class BaseLintRule(ABC):
    """Base class for language-agnostic linting rules."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for this rule."""
        raise NotImplementedError("Subclasses must implement rule_id")

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable name for this rule."""
        raise NotImplementedError("Subclasses must implement rule_name")

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this rule checks."""
        raise NotImplementedError("Subclasses must implement description")

    @property
    @abstractmethod
    def severity(self) -> Severity:
        """Default severity level for violations of this rule."""
        raise NotImplementedError("Subclasses must implement severity")

    @property
    def categories(self) -> set[str]:
        """Categories this rule belongs to (e.g., 'solid', 'style', 'complexity')."""
        return set()

    @property
    def supported_languages(self) -> set[str]:
        """Languages this rule supports. Empty set means all languages."""
        return set()  # Empty set means all languages by default

    @abstractmethod
    def check(self, context: BaseLintContext) -> list[LintViolation]:
        """Check for violations in the given context."""
        raise NotImplementedError("Subclasses must implement check")

    def is_enabled(self, config: dict[str, Any] | None) -> bool:
        """Check if this rule is enabled in the given configuration."""
        if config is None:
            return True
        rules_config = config.get("rules", {})
        rule_config = rules_config.get(self.rule_id, {})
        default_enabled = config.get("default_rule_enabled", True)
        return bool(rule_config.get("enabled", default_enabled))

    def get_configuration(self, config: dict[str, Any] | None) -> dict[str, Any]:
        """Get configuration for this rule."""
        if config is None:
            return {}
        rules_config = config.get("rules", {})
        rule_config = rules_config.get(self.rule_id, {})
        return dict(rule_config.get("config", {}))

    def supports_language(self, language: str) -> bool:
        """Check if this rule supports the given language."""
        # Empty set means supports all languages
        return not self.supported_languages or language in self.supported_languages

    def create_violation(
        self,
        context: BaseLintContext,
        message: str,
        description: str,
        *,
        line: int = 1,
        column: int = 0,
        suggestion: str | None = None,
        violation_context: dict[str, Any] | None = None,
    ) -> LintViolation:
        """Helper method to create a violation with consistent structure."""
        from .ignore_utils import create_violation_from_data

        return create_violation_from_data(
            self.rule_id,
            str(context.file_path) if context.file_path else "<unknown>",
            line=line,
            column=column,
            severity=self.severity,
            message=message,
            description=description,
            suggestion=suggestion,
            violation_context=violation_context,
        )


class BaseLintAnalyzer(ABC):
    """Base class for language-specific analyzers."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Get the name of the language this analyzer handles."""
        raise NotImplementedError("Subclasses must implement language_name")

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Get file extensions this analyzer supports."""
        raise NotImplementedError("Subclasses must implement get_supported_extensions")

    @abstractmethod
    def analyze_file(self, file_path: Path) -> BaseLintContext:
        """Analyze a file and return context."""
        raise NotImplementedError("Subclasses must implement analyze_file")


class BaseCoordinator(ABC):
    """Base class for multi-language orchestrators."""

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
    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages."""
        raise NotImplementedError("Subclasses must implement get_supported_languages")

    @abstractmethod
    def register_analyzer(self, analyzer: BaseLintAnalyzer) -> None:
        """Register a language analyzer."""
        raise NotImplementedError("Subclasses must implement register_analyzer")


class MultiLanguageRule(BaseLintRule):
    """Base class for rules that work across multiple languages."""

    def __init__(self, supported_languages: set[str] | None = None):
        """Initialize with optional language restrictions."""
        self._supported_languages = supported_languages or set()

    @property
    def supported_languages(self) -> set[str]:
        """Languages this rule supports."""
        return self._supported_languages


class FileBasedMultiLanguageRule(MultiLanguageRule):
    """Base class for file-based rules that work across multiple languages."""

    @abstractmethod
    def check_file(self, file_path: Path, content: str, context: BaseLintContext) -> list[LintViolation]:
        """Check an entire file for violations."""
        raise NotImplementedError("Subclasses must implement check_file")

    def check(self, context: BaseLintContext) -> list[LintViolation]:
        """Default implementation that checks entire file."""
        # Check language support
        if not self.supports_language(context.language):
            return []

        from .ignore_utils import check_file_with_ignores

        return check_file_with_ignores(self, context, self.check_file)
