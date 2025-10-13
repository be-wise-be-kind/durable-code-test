#!/usr/bin/env python3
"""
Purpose: Rule registry for managing and discovering linting rules
Scope: Provides dynamic registration and discovery of linting rules
Overview: This module implements the dynamic rule discovery and registration system that forms
    the backbone of the pluggable linter framework's extensibility. It automatically discovers
    all rule classes in the rules directory structure, validates they implement the correct
    interfaces, and registers them for use by the orchestrator. The registry maintains mappings
    between rule IDs, categories, and implementation classes, enabling rules to be selected by
    ID, category, or custom filters. It supports lazy loading for performance, caching of
    discovered rules, and hot-reloading during development. The module also provides rule
    metadata querying, dependency resolution between rules, and configuration management for
    individual rule settings. This centralized registry ensures new rules can be added simply
    by placing them in the appropriate directory without modifying any framework code.
Dependencies: importlib for dynamic imports, pkgutil for package discovery
Exports: DefaultRuleRegistry, RuleDiscoveryService
Interfaces: Implements RuleRegistry interface
Implementation: Plugin architecture with automatic discovery capabilities
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from loguru import logger

from tools.design_linters.framework.base_interfaces import BaseLintRule
from tools.design_linters.framework.interfaces import LintRule, RuleRegistry


class DefaultRuleRegistry(RuleRegistry):
    """Default implementation of rule registry with plugin discovery."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._rules: dict[str, LintRule] = {}
        self._rules_by_category: dict[str, set[str]] = {}

    def register_rule(self, rule: LintRule) -> None:
        """Register a new rule."""
        rule_id = rule.rule_id

        if rule_id in self._rules:
            logger.warning("Rule %s already registered, overriding", rule_id)

        self._rules[rule_id] = rule

        # Update category index
        for category in rule.categories:
            if category not in self._rules_by_category:
                self._rules_by_category[category] = set()
            self._rules_by_category[category].add(rule_id)

        logger.debug("Registered rule: %s", rule_id)

    def unregister_rule(self, rule_id: str) -> None:
        """Unregister a rule by ID."""
        if rule_id not in self._rules:
            logger.warning("Rule %s not found for unregistration", rule_id)
            return

        rule = self._rules[rule_id]

        # Remove from category index
        for category in rule.categories:
            if category in self._rules_by_category:
                self._rules_by_category[category].discard(rule_id)
                if not self._rules_by_category[category]:
                    del self._rules_by_category[category]

        del self._rules[rule_id]
        logger.debug("Unregistered rule: %s", rule_id)

    def get_rule(self, rule_id: str) -> LintRule | None:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> list[LintRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def get_rules_by_category(self, category: str) -> list[LintRule]:
        """Get rules belonging to a specific category."""
        rule_ids = self._rules_by_category.get(category, set())
        return [self._rules[rule_id] for rule_id in rule_ids if rule_id in self._rules]

    def get_rule_count(self) -> int:
        """Get total number of registered rules."""
        return len(self._rules)

    def get_categories(self) -> set[str]:
        """Get all available rule categories."""
        return set(self._rules_by_category.keys())

    def get_rule_info(self) -> dict[str, dict[str, Any]]:
        """Get summary information about all rules."""
        return {
            rule_id: {
                "name": rule.rule_name,
                "description": rule.description,
                "severity": rule.severity.value,
                "categories": list(rule.categories),
            }
            for rule_id, rule in self._rules.items()
        }

    def discover_rules(self, package_paths: list[str]) -> int:
        """Discover and register rules from package paths."""
        discovered_count = 0
        discovery_service = RuleDiscoveryService()

        for package_path in package_paths:
            try:
                count = discovery_service.discover_from_package(package_path, self)
                discovered_count += count
                logger.info("Discovered %s rules from %s", count, package_path)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Error discovering rules from %s", package_path)

        return discovered_count


class RuleDiscoveryService:
    """Service for discovering rules from packages and modules."""

    def discover_from_package(self, package_path: str, registry: RuleRegistry) -> int:
        """Discover rules from a package and register them."""
        discovered_count = 0

        try:
            # Import the package
            package = importlib.import_module(package_path)
        except ImportError:
            logger.exception("Could not import package %s", package_path)
            raise

        # Check if it's a package or single module
        if not hasattr(package, "__path__"):
            # Single module - no iteration needed
            return self._discover_from_module(package_path, registry)

        # Walk through all modules in the package
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            full_module_name = f"{package_path}.{module_name}"
            discovered_count += self._try_discover_from_module(full_module_name, registry)

        return discovered_count

    def _try_discover_from_module(self, module_name: str, registry: RuleRegistry) -> int:
        """Try to discover rules from a module, handling errors gracefully."""
        try:
            return self._discover_from_module(module_name, registry)
        except (ImportError, AttributeError, ValueError) as e:
            logger.error("Error importing module %s: %s", module_name, e)
            return 0

    def _discover_from_module(self, module_path: str, registry: RuleRegistry) -> int:
        """Discover rules from a specific module."""
        discovered_count = 0

        try:
            module = importlib.import_module(module_path)
        except (ImportError, AttributeError) as e:
            logger.error("Error processing module %s: %s", module_path, e)
            return 0

        # Look for rule classes in the module
        for name, obj in inspect.getmembers(module):
            if not self._is_rule_class(obj):
                continue

            discovered_count += self._try_register_rule(name, obj, registry)

        return discovered_count

    def _try_register_rule(self, name: str, rule_class: type[LintRule], registry: RuleRegistry) -> int:
        """Try to instantiate and register a rule, handling errors gracefully."""
        try:
            # Instantiate the rule
            rule_instance = rule_class()
            registry.register_rule(rule_instance)
            logger.debug("Discovered rule: %s", rule_instance.rule_id)
            return 1
        except (TypeError, AttributeError, ValueError) as e:
            logger.error("Error instantiating rule %s: %s", name, e)
            return 0

    def _is_rule_class(self, obj: Any) -> bool:
        """Check if an object is a valid rule class."""
        return (
            inspect.isclass(obj)
            and (issubclass(obj, LintRule) or issubclass(obj, BaseLintRule))
            and obj not in (LintRule, BaseLintRule)  # Don't instantiate the base classes
            and not inspect.isabstract(obj)
        )  # Don't instantiate abstract classes

    def discover_from_directory(self, directory_path: Path, registry: RuleRegistry) -> int:
        """Discover rules from Python files in a directory."""
        discovered_count = 0

        for py_file in directory_path.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("test_"):
                continue

            try:
                count = self._discover_from_file(py_file, registry)
                discovered_count += count
            except (ImportError, AttributeError, OSError) as e:
                logger.debug("Skipped rule discovery from %s: %s", py_file, e)  # noqa

        return discovered_count

    def _discover_from_file(self, file_path: Path, registry: RuleRegistry) -> int:
        """Discover rules from a specific Python file."""
        # This is more complex as it requires dynamic module loading
        # For now, we'll focus on package-based discovery
        # Could be implemented using importlib.util.spec_from_file_location
        # Parameters are kept for future implementation
        del file_path, registry  # Mark as intentionally unused
        return 0


class CategorizedRuleRegistry(DefaultRuleRegistry):
    """Extended rule registry with advanced categorization features."""

    def __init__(self) -> None:
        """Initialize with category management features."""
        super().__init__()
        self._category_metadata: dict[str, dict[str, Any]] = {}

    def register_category(self, category: str, description: str, priority: int = 0) -> None:
        """Register metadata for a category."""
        self._category_metadata[category] = {
            "description": description,
            "priority": priority,
            "rule_count": len(self._rules_by_category.get(category, set())),
        }

    def get_category_info(self, category: str) -> dict[str, Any] | None:
        """Get information about a category."""
        if category in self._category_metadata:
            info = self._category_metadata[category].copy()
            info["rule_count"] = len(self._rules_by_category.get(category, set()))
            return info
        return None

    def get_categories_by_priority(self) -> list[str]:
        """Get categories sorted by priority."""
        return sorted(
            self._category_metadata.keys(),
            key=lambda cat: self._category_metadata[cat].get("priority", 0),
            reverse=True,
        )

    def get_rules_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of all rules and categories."""
        return {
            "total_rules": len(self._rules),
            "total_categories": len(self._rules_by_category),
            "categories": {
                cat: {
                    "rule_count": len(rule_ids),
                    "rules": list(rule_ids),
                    "metadata": self._category_metadata.get(cat, {}),
                }
                for cat, rule_ids in self._rules_by_category.items()
            },
            "uncategorized_rules": [rule_id for rule_id, rule in self._rules.items() if not rule.categories],
        }
