#!/usr/bin/env python3
"""
Purpose: Pluggable design linter framework package initialization
Scope: Exports main framework classes and provides unified API
Overview: This module provides the public API for the pluggable design linter
    framework. It enables a rule-based architecture where different design
    principles can be implemented as pluggable rules with unified reporting,
    configuration management, and execution orchestration.
Dependencies: All framework submodules
Exports: Core framework classes and factory functions
Interfaces: Unified API for framework consumers
Implementation: Plugin architecture with dependency injection support
"""

import contextlib
import pkgutil
from pathlib import Path

from .analyzer import ContextualASTVisitor, DefaultLintCoordinator, LintResults, PythonAnalyzer
from .base_interfaces import (
    BaseCoordinator,
    BaseLintAnalyzer,
    BaseLintContext,
    BaseLintRule,
    FileBasedMultiLanguageRule,
    MultiLanguageRule,
)
from .interfaces import (
    ASTLintRule,
    ConfigurationProvider,
    FileBasedLintRule,
    LintAnalyzer,
    LintContext,
    LintCoordinator,
    LintReporter,
    LintRule,
    RuleRegistry,
)
from .multi_language_orchestrator import DefaultLanguageRegistry, MultiLanguageCoordinator
from .reporters import GitHubActionsReporter, JSONReporter, ReporterFactory, SARIFReporter, TextReporter

# Rule management
from .rule_registry import CategorizedRuleRegistry, DefaultRuleRegistry, RuleDiscoveryService
from .types import LintViolation, Severity

# Core interfaces


# Main public API
__all__ = [
    # Core interfaces (Python-specific, backward compatible)
    "LintRule",
    "ASTLintRule",
    "FileBasedLintRule",
    "LintViolation",
    "LintContext",
    "LintReporter",
    "LintAnalyzer",
    "LintCoordinator",
    "RuleRegistry",
    "Severity",
    "ConfigurationProvider",
    # Multi-language base interfaces
    "BaseLintRule",
    "BaseLintContext",
    "BaseLintAnalyzer",
    "BaseCoordinator",
    "MultiLanguageRule",
    "FileBasedMultiLanguageRule",
    # Multi-language orchestration
    "MultiLanguageCoordinator",
    "DefaultLanguageRegistry",
    # Rule management
    "DefaultRuleRegistry",
    "CategorizedRuleRegistry",
    "RuleDiscoveryService",
    # Reporting
    "TextReporter",
    "JSONReporter",
    "SARIFReporter",
    "GitHubActionsReporter",
    "ReporterFactory",
    # Analysis
    "ContextualASTVisitor",
    "PythonAnalyzer",
    "DefaultLintCoordinator",
    "LintResults",
    # Factory functions
    "create_orchestrator",
    "create_multi_language_orchestrator",
    "create_rule_registry",
    "discover_rules",
]


def _discover_rule_packages() -> list[str]:
    """Dynamically discover all rule packages in the rules directory."""
    import tools.design_linters.rules as rules_module  # pylint: disable=import-outside-toplevel

    rule_packages = []

    # Walk through all subdirectories in the rules package
    if hasattr(rules_module, "__path__"):
        for _, package_name, is_pkg in pkgutil.iter_modules(rules_module.__path__):
            if is_pkg:  # Only include packages, not individual modules
                rule_packages.append(f"tools.design_linters.rules.{package_name}")

    return rule_packages


def create_orchestrator(rule_packages: list[str] | None = None) -> LintCoordinator:
    """Create a fully configured linter orchestrator.

    Args:
        rule_packages: List of package names to discover rules from.
                      If None, will auto-discover from known rule packages.

    Returns:
        Configured LintCoordinator instance
    """
    # Create rule registry and discover rules
    registry = DefaultRuleRegistry()

    # Auto-discover from all rule packages if no specific packages provided
    if rule_packages is None:
        rule_packages = _discover_rule_packages()

    discovery = RuleDiscoveryService()
    for package in rule_packages:
        with contextlib.suppress(ImportError):
            discovery.discover_from_package(package, registry)

    # Create analyzers
    analyzers: dict[str, LintAnalyzer] = {"python": PythonAnalyzer()}

    # Create reporters
    from .reporters import ReporterFactory as Factory  # pylint: disable=import-outside-toplevel

    reporters = Factory.get_standard_reporters()

    return DefaultLintCoordinator(rule_registry=registry, analyzers=analyzers, reporters=reporters)


def create_multi_language_orchestrator(rule_packages: list[str] | None = None) -> MultiLanguageCoordinator:
    """Create a fully configured multi-language linter orchestrator.

    Args:
        rule_packages: List of package names to discover rules from.
                      If None, will auto-discover from known rule packages.

    Returns:
        Configured MultiLanguageOrchestrator instance
    """
    # Create rule registry and discover rules
    registry = DefaultRuleRegistry()

    # Auto-discover from all rule packages if no specific packages provided
    if rule_packages is None:
        rule_packages = _discover_rule_packages()

    discovery = RuleDiscoveryService()
    for package in rule_packages:
        with contextlib.suppress(ImportError):
            discovery.discover_from_package(package, registry)

    # Create language registry with Python support
    language_registry = DefaultLanguageRegistry()

    # Create the multi-language orchestrator
    return MultiLanguageCoordinator(
        rule_registry=registry,
        language_registry=language_registry,
    )


def create_rule_registry(auto_discover: bool = True) -> RuleRegistry:
    """Create and optionally populate a rule registry.

    Args:
        auto_discover: Whether to automatically discover rules from known packages

    Returns:
        Configured RuleRegistry instance
    """
    registry = CategorizedRuleRegistry()

    if auto_discover:
        # Try to discover rules from known rule packages
        known_packages = [
            "tools.design_linters.rules.solid",  # design-lint: ignore[literals.magic-string]
            "tools.design_linters.rules.complexity",  # design-lint: ignore[literals.magic-string]
            "tools.design_linters.rules.style",  # design-lint: ignore[literals.magic-string]
        ]

        discovery = RuleDiscoveryService()
        for package in known_packages:
            with contextlib.suppress(ImportError):
                discovery.discover_from_package(package, registry)

    return registry


def discover_rules(*package_paths: str) -> int:
    """Discover rules from specified packages.

    Args:
        package_paths: Package paths to discover rules from

    Returns:
        Number of rules discovered
    """
    registry = DefaultRuleRegistry()
    discovery = RuleDiscoveryService()

    total_discovered = 0
    for package_path in package_paths:
        with contextlib.suppress(ImportError):
            count = discovery.discover_from_package(package_path, registry)
            total_discovered += count

    return total_discovered


# Convenience function for quick linting
def lint_files(
    file_paths: list[str],
    rule_packages: list[str] | None = None,
    output_format: str = "text",
    config: dict[str, str] | None = None,
) -> str:
    """Convenience function to lint files and get formatted output.

    Args:
        file_paths: List of file paths to lint
        rule_packages: List of rule packages to use
        output_format: Output format ('text', 'json', 'sarif', 'github')
        config: Configuration for rules and analysis

    Returns:
        Formatted linting report
    """
    orchestrator = create_orchestrator(rule_packages)
    all_violations = []

    for file_path in file_paths:
        path = Path(file_path)
        if path.is_file():
            violations = orchestrator.lint_file(path, config)
            all_violations.extend(violations)
        elif path.is_dir():
            violations = orchestrator.lint_directory(path, config)
            all_violations.extend(violations)

    return orchestrator.generate_report(all_violations, output_format)
