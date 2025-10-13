#!/usr/bin/env python3
"""
Purpose: Single Responsibility Principle rules for pluggable framework
Scope: Implements SRP violation detection as individual, focused rules
Overview: This module enforces the Single Responsibility Principle (SRP) from SOLID design
    principles, ensuring classes and functions maintain focused, cohesive responsibilities. It
    detects violations such as classes handling multiple unrelated concerns, functions performing
    too many distinct operations, mixed business logic with infrastructure code, and coupled
    responsibilities that should be separated. The rules analyze method names, class structure,
    dependency patterns, and code complexity to identify SRP violations. Each violation provides
    refactoring suggestions showing how to extract responsibilities into separate classes or
    methods. The module helps maintain maintainable, testable code by ensuring each component
    has a single, well-defined reason to change, reducing coupling and improving code organization
    across the entire codebase.
Dependencies: Framework interfaces, AST analysis utilities
Exports: Individual SRP-focused rules
Interfaces: All rules implement ASTLintRule interface
Implementation: Rule-based architecture with single responsibility per rule
"""

import ast
from collections import defaultdict
from typing import cast

from tools.design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity

# Configuration constants
MIN_METHODS_FOR_COHESION_CHECK = 5


class TooManyMethodsRule(ASTLintRule):
    """Rule to detect classes with too many methods."""

    DEFAULT_MAX_METHODS = 15

    @property
    def rule_id(self) -> str:
        return "solid.srp.too-many-methods"

    @property
    def rule_name(self) -> str:
        return "Too Many Methods"

    @property
    def description(self) -> str:
        return "Classes should not have too many methods as it may indicate multiple responsibilities"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        return {"solid", "srp", "complexity"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.ClassDef)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.ClassDef):
            raise TypeError("TooManyMethodsRule should only receive ast.ClassDef nodes")
        config = self.get_configuration(context.metadata or {})
        max_methods = config.get("max_methods", self.DEFAULT_MAX_METHODS)

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        method_count = len(methods)

        if method_count > max_methods:
            return [
                self.create_violation_from_node(
                    context=context,
                    node=node,
                    message=f"Class '{node.name}' has {method_count} methods (max: {max_methods})",
                    description="Classes with many methods often violate SRP by handling multiple responsibilities",
                    suggestion=f"Consider splitting '{node.name}' into smaller, focused classes",
                )
            ]

        return []


class TooManyResponsibilitiesRule(ASTLintRule):
    """Rule to detect classes with multiple responsibility groups."""

    @property
    def rule_id(self) -> str:
        return "solid.srp.multiple-responsibilities"

    @property
    def rule_name(self) -> str:
        return "Multiple Responsibilities"

    @property
    def description(self) -> str:
        return "Classes should have a single responsibility based on method naming patterns"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        return {"solid", "srp"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.ClassDef)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.ClassDef):
            raise TypeError("TooManyResponsibilitiesRule should only receive ast.ClassDef nodes")

        # Skip framework pattern classes that are expected to have multiple responsibility groups
        if self._is_framework_pattern_class(node):
            return []

        config = self.get_configuration(context.metadata or {})
        responsibility_analysis = self._analyze_class_responsibilities(node, config)

        return self._create_violation_if_too_many_groups(
            node,
            context,
            responsibility_analysis["groups"],
            responsibility_analysis["max_groups"],
        )

    def _analyze_class_responsibilities(self, node: ast.ClassDef, config: dict) -> dict:
        """Analyze class responsibilities and return analysis results."""
        max_groups = config.get("max_responsibility_groups", 2)
        responsibility_prefixes = self._get_responsibility_prefixes(config)
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        responsibility_groups = self._group_methods_by_responsibility(methods, responsibility_prefixes)

        return {"groups": responsibility_groups, "max_groups": max_groups}

    def _get_responsibility_prefixes(self, config: dict) -> dict[str, list[str]]:
        """Get responsibility prefixes from configuration."""
        default_prefixes: dict[str, list[str]] = {
            "data": ["get", "set", "fetch", "load", "save", "store"],
            "validation": ["validate", "check", "verify", "confirm"],
            "formatting": ["format", "render", "display", "print"],
            "calculation": ["calculate", "compute", "sum", "count"],
            "communication": ["send", "receive", "notify", "broadcast"],
            "file_io": ["read", "write", "open", "close", "export", "import"],
            "network": ["connect", "disconnect", "upload", "download", "sync"],
            "ui": ["show", "hide", "update", "refresh", "draw"],
        }
        result = config.get("responsibility_prefixes", default_prefixes)
        return cast(dict[str, list[str]], result)

    def _create_violation_if_too_many_groups(
        self,
        node: ast.ClassDef,
        context: LintContext,
        responsibility_groups: dict,
        max_groups: int,
    ) -> list[LintViolation]:
        """Create violation if class has too many responsibility groups."""
        if len(responsibility_groups) <= max_groups:
            return []

        groups_list = ", ".join(responsibility_groups.keys())
        return [
            self.create_violation_from_node(
                context=context,
                node=node,
                message=f"Class '{node.name}' has {len(responsibility_groups)} responsibility groups",
                description=f"Multiple responsibility groups detected: {groups_list}",
                suggestion=f"Split '{node.name}' by responsibility: {groups_list}",
                violation_context={"responsibility_groups": responsibility_groups},
            )
        ]

    def _group_methods_by_responsibility(
        self,
        methods: list[ast.FunctionDef],
        responsibility_prefixes: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        """Group methods by their likely responsibility based on naming."""
        groups = defaultdict(list)

        for method in methods:
            if method.name.startswith("_"):
                continue  # Skip private methods

            category = self._find_method_category(method.name, responsibility_prefixes)
            groups[category].append(method.name)

        return dict(groups)

    def _find_method_category(self, method_name: str, responsibility_prefixes: dict[str, list[str]]) -> str:
        """Find the category for a method based on its name."""
        for category, prefixes in responsibility_prefixes.items():
            for prefix in prefixes:
                if method_name.lower().startswith(prefix):
                    return category
        return "other"

    def _is_framework_pattern_class(self, node: ast.ClassDef) -> bool:
        """Check if this is a framework pattern class that's expected to have multiple responsibilities."""
        class_name = node.name

        # Rule implementation classes - these implement interfaces and have expected patterns
        if class_name.endswith("Rule"):
            return True

        # Interface/abstract base classes - these define contracts, not implementations
        interface_patterns = [
            "Reporter",
            "Analyzer",
            "Registry",
            "Context",
            "Interface",
        ]
        return any(pattern in class_name for pattern in interface_patterns)


class CohesionAnalyzer:
    """Helper class for analyzing class cohesion."""

    def extract_instance_variables(self, node: ast.ClassDef) -> set[str]:
        """Extract instance variables from a class."""
        instance_vars = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name) and item.value.id == "self":
                instance_vars.add(item.attr)
        return instance_vars

    def calculate_cohesion(self, methods: list[ast.FunctionDef], instance_vars: set[str]) -> float:
        """Calculate cohesion score using LCOM metric."""
        # Filter out __init__ and other special methods for cohesion calculation
        business_methods = [m for m in methods if not m.name.startswith("__")]

        method_var_usage = self._build_method_var_usage_map(business_methods, instance_vars)
        method_names = list(method_var_usage.keys())

        if len(method_names) < 2:
            return 1.0

        return self._calculate_shared_variable_ratio(method_names, method_var_usage)

    def _build_method_var_usage_map(self, methods: list[ast.FunctionDef], instance_vars: set[str]) -> dict:
        """Build mapping of methods to their used instance variables."""
        method_var_usage = {}
        for method in methods:
            used_vars = self._find_used_instance_vars(method, instance_vars)
            method_var_usage[method.name] = used_vars
        return method_var_usage

    def _calculate_shared_variable_ratio(self, method_names: list[str], method_var_usage: dict) -> float:
        """Calculate ratio of method pairs that share variables."""
        total_pairs = 0
        shared_pairs = 0

        for i, method_i in enumerate(method_names):
            for method_j in method_names[i + 1 :]:
                total_pairs += 1
                if method_var_usage[method_i] & method_var_usage[method_j]:
                    shared_pairs += 1

        return shared_pairs / total_pairs if total_pairs > 0 else 1.0

    def _find_used_instance_vars(self, method: ast.FunctionDef, instance_vars: set[str]) -> set[str]:
        """Find instance variables used by a method."""
        used_vars = set()
        for node in ast.walk(method):
            if self._is_instance_variable_access(node, instance_vars):
                used_vars.add(node.attr)  # type: ignore
        return used_vars

    def _is_instance_variable_access(self, node: ast.AST, instance_vars: set[str]) -> bool:
        """Check if node is an instance variable access."""
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and node.attr in instance_vars
        )


class LowCohesionRule(ASTLintRule):
    """Rule to detect classes with low cohesion."""

    DEFAULT_MIN_COHESION = 0.02  # Very lenient - only catch egregious violations

    def __init__(self):
        super().__init__()
        self._cohesion_analyzer = CohesionAnalyzer()

    @property
    def rule_id(self) -> str:
        return "solid.srp.low-cohesion"

    @property
    def rule_name(self) -> str:
        return "Low Cohesion"

    @property
    def description(self) -> str:
        return "Classes should have high cohesion with methods using shared instance variables"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        return {"solid", "srp", "cohesion"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.ClassDef)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.ClassDef):
            raise TypeError("LowCohesionRule should only receive ast.ClassDef nodes")

        cohesion_analysis = self._perform_cohesion_analysis(node, context)

        # Skip utility classes with no instance variables or classes where cohesion can't be calculated
        if not cohesion_analysis["can_calculate"]:
            return []

        # Skip small utility classes (less than MIN_METHODS_FOR_COHESION_CHECK methods)
        # These are often legitimate service classes
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) < MIN_METHODS_FOR_COHESION_CHECK:
            return []

        # Skip framework pattern classes that are expected to have low cohesion
        if self._is_framework_pattern_class(node):
            return []

        return self._create_violation_if_low_cohesion(
            node, context, cohesion_analysis["score"], cohesion_analysis["min_cohesion"]
        )

    def _perform_cohesion_analysis(self, node: ast.ClassDef, context: LintContext) -> dict:
        """Perform complete cohesion analysis for a class."""
        config = self.get_configuration(context.metadata or {})
        min_cohesion = config.get("min_cohesion_score", self.DEFAULT_MIN_COHESION)

        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        instance_vars = self._cohesion_analyzer.extract_instance_variables(node)
        can_calculate = self._can_calculate_cohesion(methods, instance_vars)

        cohesion_score = self._cohesion_analyzer.calculate_cohesion(methods, instance_vars) if can_calculate else 0.0

        return {
            "can_calculate": can_calculate,
            "score": cohesion_score,
            "min_cohesion": min_cohesion,
        }

    def _can_calculate_cohesion(self, methods: list, instance_vars: set) -> bool:
        """Check if cohesion can be calculated."""
        return bool(methods and instance_vars)

    def _create_violation_if_low_cohesion(
        self,
        node: ast.ClassDef,
        context: LintContext,
        cohesion_score: float,
        min_cohesion: float,
    ) -> list[LintViolation]:
        """Create violation if cohesion is below threshold."""
        if cohesion_score >= min_cohesion:
            return []

        return [
            self.create_violation_from_node(
                context,
                node,
                message=f"Class '{node.name}' has low cohesion ({cohesion_score:.2f})",
                description=(
                    f"Methods in the class share few instance variables "
                    f"(cohesion: {cohesion_score:.2f}, min: {min_cohesion})"
                ),
                suggestion="Consider splitting the class into more cohesive units",
            )
        ]

    def _is_framework_pattern_class(self, node: ast.ClassDef) -> bool:
        """Check if this is a framework pattern class that's expected to have low cohesion."""
        class_name = node.name

        # Rule implementation classes - these implement interfaces and have expected patterns
        if class_name.endswith("Rule"):
            return True

        # Interface/abstract base classes - these define contracts, not implementations
        interface_patterns = [
            "Reporter",
            "Analyzer",
            "Registry",
            "Context",
            "Interface",
        ]
        return any(pattern in class_name for pattern in interface_patterns)

    # Expose methods expected by tests
    def _extract_instance_variables(self, node: ast.ClassDef) -> set[str]:
        """Extract instance variables from a class."""
        return self._cohesion_analyzer.extract_instance_variables(node)

    def _find_used_instance_vars(self, method: ast.FunctionDef, instance_vars: set[str]) -> set[str]:
        """Find instance variables used by a method."""
        return self._cohesion_analyzer._find_used_instance_vars(method, instance_vars)

    def _calculate_cohesion(self, methods: list[ast.FunctionDef], instance_vars: set[str]) -> float:
        """Calculate cohesion score using LCOM metric."""
        return self._cohesion_analyzer.calculate_cohesion(methods, instance_vars)


class ClassTooBigRule(ASTLintRule):
    """Rule to detect classes that are too large."""

    DEFAULT_MAX_LINES = 200

    def __init__(self):
        super().__init__()
        from loguru import logger

        logger.info("ClassTooBigRule initialized", max_lines=self.DEFAULT_MAX_LINES)

    @property
    def rule_id(self) -> str:
        return "solid.srp.class-too-big"

    @property
    def rule_name(self) -> str:
        return "Class Too Big"

    @property
    def description(self) -> str:
        return "Classes should not be excessively large as it may indicate multiple responsibilities"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        return {"solid", "srp", "size"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        result = isinstance(node, ast.ClassDef)
        if result:
            from loguru import logger

            logger.debug("ClassTooBigRule.should_check_node: Will check class", class_name=node.name)
        return result

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.ClassDef):
            raise TypeError("ClassTooBigRule should only receive ast.ClassDef nodes")
        config = self.get_configuration(context.metadata or {})
        max_lines = config.get("max_class_lines", self.DEFAULT_MAX_LINES)

        from loguru import logger

        logger.debug("ClassTooBigRule checking class", class_name=node.name, file_path=str(context.file_path))

        if node.end_lineno and node.lineno:
            line_count = node.end_lineno - node.lineno
            logger.debug("Class line count analysis", class_name=node.name, line_count=line_count, max_lines=max_lines)

            if line_count > max_lines:
                return [
                    self.create_violation_from_node(
                        context,
                        node,
                        message=f"Class '{node.name}' is large ({line_count} lines)",
                        description="Large classes may violate SRP by handling multiple concerns",
                        suggestion=f"Consider breaking down '{node.name}' into smaller classes",
                    )
                ]

        return []


class TooManyDependenciesRule(ASTLintRule):
    """Rule to detect classes with too many dependencies."""

    @property
    def rule_id(self) -> str:
        return "solid.srp.too-many-dependencies"

    @property
    def rule_name(self) -> str:
        return "Too Many Dependencies"

    @property
    def description(self) -> str:
        return "Classes should not have excessive dependencies as it may indicate multiple responsibilities"

    @property
    def severity(self) -> Severity:
        return Severity.ERROR

    @property
    def categories(self) -> set[str]:
        return {"solid", "srp", "dependencies"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.ClassDef)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.ClassDef):
            raise TypeError("TooManyDependenciesRule should only receive ast.ClassDef nodes")

        dependency_analysis = self._analyze_class_dependencies(node, context)

        if dependency_analysis["exceeds_limit"]:
            return [self._create_dependency_violation(node, context, dependency_analysis)]

        return []

    def _analyze_class_dependencies(self, node: ast.ClassDef, context: LintContext) -> dict:
        """Analyze class dependencies and return analysis results."""
        config = self.get_configuration(context.metadata or {})
        max_dependencies = config.get("max_dependencies", 10)
        dependencies = self._extract_dependencies(node)
        dependency_count = len(dependencies)

        return {
            "count": dependency_count,
            "max_dependencies": max_dependencies,
            "exceeds_limit": dependency_count > max_dependencies,
            "dependencies": dependencies,
        }

    def _create_dependency_violation(self, node: ast.ClassDef, context: LintContext, analysis: dict) -> LintViolation:
        """Create a violation for excessive dependencies."""
        return self.create_violation_from_node(
            context,
            node,
            message=f"Class '{node.name}' has {analysis['count']} dependencies",
            description="Classes with many dependencies may be handling multiple concerns",
            suggestion=f"Consider reducing dependencies or splitting '{node.name}'",
        )

    def _extract_dependencies(self, node: ast.ClassDef) -> set[str]:
        """Extract external dependencies from a class."""
        dependencies: set[str] = set()
        for item in ast.walk(node):
            self._process_import_node(item, dependencies)
        return dependencies

    def _process_import_node(self, node: ast.AST, dependencies: set[str]) -> None:
        """Process an import node and add to dependencies set."""
        if isinstance(node, ast.Import):
            self._add_import_dependencies(node, dependencies)
        elif isinstance(node, ast.ImportFrom) and node.module:
            self._add_import_from_dependencies(node, dependencies)

    def _add_import_dependencies(self, node: ast.Import, dependencies: set[str]) -> None:
        """Add dependencies from import statement."""
        for alias in node.names:
            dependencies.add(alias.name.split(".")[0])

    def _add_import_from_dependencies(self, node: ast.ImportFrom, dependencies: set[str]) -> None:
        """Add dependencies from import from statement."""
        if node.module:
            dependencies.add(node.module.split(".")[0])
