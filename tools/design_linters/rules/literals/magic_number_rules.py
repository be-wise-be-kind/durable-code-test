#!/usr/bin/env python3
# design-lint: ignore-file[literals.*]
"""
Purpose: Magic number detection rules for the pluggable framework
Scope: Framework-based implementation for numeric literal detection
Overview: This module detects and reports magic numbers and magic strings in code, encouraging
    the use of named constants for better code maintainability and self-documentation. It identifies
    numeric literals used in comparisons, calculations, and configurations that should be extracted
    to constants with meaningful names. The rule intelligently filters out acceptable literals like
    0, 1, -1 for basic operations while flagging domain-specific values that carry business meaning.
    It also detects magic strings used repeatedly or containing configuration values that should
    be centralized. The module provides suggestions for appropriate constant names based on context
    and usage patterns, helping developers create more readable, maintainable code where the intent
    of each value is clear from its name rather than requiring comments or domain knowledge.
Dependencies: Framework interfaces, AST analysis utilities
Exports: Numeric literal linting rules
Interfaces: All rules implement ASTLintRule interface
Implementation: Rule-based architecture with numeric pattern detection
"""

import ast
from typing import Any

from tools.design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity


class MagicNumberContextAnalyzer:
    """Helper class for analyzing magic number contexts."""

    def is_acceptable_context(self, node: ast.Constant, context: LintContext, config: dict[str, Any]) -> bool:
        """Check if a magic number is in an acceptable context."""
        if self._is_test_file(context):
            return True

        if self._is_configuration_context(context):
            return True

        if self._is_small_integer_in_range(node, context, config):
            return True

        if self._is_constant_definition(node, context):
            return True

        return bool(self._is_in_math_operation_context(context)) or bool(self._is_in_math_context(context))

    def _is_test_file(self, context: LintContext) -> bool:
        return context.file_path and ("test" in str(context.file_path) or "spec" in str(context.file_path))

    def _is_configuration_context(self, context: LintContext) -> bool:
        # Check file path
        if context.file_path and any(
            config_indicator in str(context.file_path) for config_indicator in ["config", "settings", "constants"]
        ):
            return True

        # Check function name
        if context.current_function:
            func_name = context.current_function.lower()
            return any(keyword in func_name for keyword in ["config", "setup", "init", "__init__"])

        return False

    def _is_small_integer_in_range(self, node: ast.Constant, context: LintContext, config: dict[str, Any]) -> bool:
        max_small_int = config.get("max_small_integer", 10)
        return (
            isinstance(node.value, int)
            and 0 <= node.value <= max_small_int
            and self._is_in_range_context(context)
            and self._has_sufficient_context(context)
        )

    def _is_in_range_context(self, context: LintContext) -> bool:
        if not context.node_stack or len(context.node_stack) < 3:
            return False

        # Look for range or enumerate calls at index -2 (second from the end)
        # This matches the test setup where they put range/enumerate at that position
        parent_node = context.node_stack[-2]
        if isinstance(parent_node, ast.Call) and isinstance(parent_node.func, ast.Name):
            return parent_node.func.id in ["range", "enumerate"]

        return False

    def _has_sufficient_context(self, context: LintContext) -> bool:
        return bool(context.node_stack and len(context.node_stack) > 2)

    def _check_range_functions_in_stack(self, context: LintContext) -> bool:
        if not context.node_stack:
            return False

        return any(isinstance(node, ast.Call) and self._is_range_like_call(node) for node in context.node_stack)

    def _is_range_like_call(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ["range", "enumerate"]

    def _is_constant_definition(self, _node: ast.Constant, context: LintContext) -> bool:
        if not context.node_stack or len(context.node_stack) < 2:
            return False

        # The immediate parent of a constant should be checked
        # The constant is the last item in the stack, its parent is at -2
        parent = context.node_stack[-2]
        if isinstance(parent, ast.Assign):
            for target in parent.targets:
                if isinstance(target, ast.Name) and self._is_constant_name(target.id, context):
                    return True
        return False

    def _is_constant_name(self, name: str, context: LintContext) -> bool:
        return name.isupper() and len(name) > 1

    def _is_in_math_context(self, context: LintContext) -> bool:
        if not context.file_path:
            return False

        return any(
            math_indicator in str(context.file_path).lower()
            for math_indicator in [
                "math",
                "geometry",
                "physics",
                "calculation",
                "formula",
            ]
        )

    def _is_in_math_operation_context(self, context: LintContext) -> bool:
        """Check if the current context is within a mathematical operation in the node stack."""
        if not context.node_stack or len(context.node_stack) < 2:
            return False

        # Look for math operations as direct parent
        parent_node = context.node_stack[-2]
        return isinstance(parent_node, (ast.BinOp, ast.UnaryOp, ast.Compare))


class MagicNumberSuggestionGenerator:
    """Helper class for generating magic number constant suggestions."""

    def __init__(self):
        """Initialize with common patterns and caching for suggestions."""
        self._time_constants = {
            60: "SECONDS_PER_MINUTE",
            3600: "SECONDS_PER_HOUR",
            24: "HOURS_PER_DAY",
            365: "DAYS_PER_YEAR",
            1000: "MILLISECONDS_PER_SECOND",
        }
        self._suggestion_cache = {}
        self._pattern_matchers = [
            self._check_specific_patterns,
            self._check_size_patterns,
        ]

    def generate_constant_suggestion(self, value: Any, context: LintContext) -> str:
        """Generate a suggestion for naming a magic number constant."""
        if not self._is_numeric_value(value):
            return self._get_generic_suggestion(value)

        cache_key = self._create_cache_key(value, context)
        cached_result = self._get_cached_suggestion(cache_key)
        if cached_result:
            return cached_result

        suggestion = self._generate_new_suggestion(value, context)
        self._cache_suggestion(cache_key, suggestion)
        return suggestion

    def _is_numeric_value(self, value: Any) -> bool:
        """Check if value is numeric."""
        return hasattr(value, "__int__") or hasattr(value, "__float__")

    def _create_cache_key(self, value: Any, context: LintContext) -> tuple:
        """Create cache key for suggestion lookup."""
        return (value, str(context.file_path or ""))

    def _get_cached_suggestion(self, cache_key: tuple) -> str | None:
        """Get cached suggestion if available."""
        return self._suggestion_cache.get(cache_key)

    def _cache_suggestion(self, cache_key: tuple, suggestion: str) -> None:
        """Cache the suggestion for future use."""
        self._suggestion_cache[cache_key] = suggestion

    def _generate_new_suggestion(self, value: Any, context: LintContext) -> str:
        """Generate a new suggestion based on patterns and context."""
        common_suggestion = self._get_common_pattern_suggestion(value)
        if common_suggestion:
            return common_suggestion

        context_suggestion = self._get_context_based_suggestion(value, context.current_function or "")
        if context_suggestion:
            return context_suggestion

        return f"Consider extracting to a named constant: CONSTANT_NAME = {value}"

    def _try_context_based_suggestion(self, value: Any, context: LintContext) -> str:
        """Try to generate suggestion based on context."""
        if not context.node_stack or len(context.node_stack) <= 1:
            return f"VALUE_{value}"

        parent = context.node_stack[-2]
        if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name):
            function_name = parent.func.id
            return self._get_context_based_suggestion(value, function_name)

        return f"VALUE_{value}"

    def _get_generic_suggestion(self, value: Any) -> str:
        return f"CONSTANT_{str(value).replace('.', '_').replace('-', 'NEGATIVE_')}"

    def _get_common_pattern_suggestion(self, value: Any) -> str:
        if value in self._time_constants:
            return f"{self._time_constants[value]} = {value}"

        # Check for common threshold values
        if value == 0.5:
            return "THRESHOLD_VALUE = 0.5"
        elif value == 0.1:
            return "THRESHOLD_VALUE = 0.1"

        return ""

    def _get_context_based_suggestion(self, value: Any, function_name: str) -> str:
        if not function_name:
            return ""

        lower_func_name = function_name.lower()

        # Timeout/delay patterns
        if "timeout" in lower_func_name:
            return f"DEFAULT_TIMEOUT = {value}"
        elif "delay" in lower_func_name:
            return f"DEFAULT_DELAY = {value}"

        # Retry patterns
        if "retry" in lower_func_name:
            return f"MAX_RETRIES = {value}"

        # Port patterns
        if "port" in lower_func_name:
            return f"DEFAULT_PORT = {value}"

        # Size/buffer patterns
        if any(keyword in lower_func_name for keyword in ["size", "buffer", "memory", "limit"]):
            return f"MAX_SIZE = {value}"

        return ""

    def _check_specific_patterns(self, value: Any, lower_func_name: str) -> str:
        if "timeout" in lower_func_name or "delay" in lower_func_name:
            return f"TIMEOUT_SECONDS_{value}" if value < 3600 else f"TIMEOUT_MINUTES_{value // 60}"

        if "retry" in lower_func_name or "attempt" in lower_func_name:
            return f"MAX_RETRIES_{value}"

        if "port" in lower_func_name:
            return f"DEFAULT_PORT_{value}"

        return f"VALUE_{value}"

    def _check_size_patterns(self, value: Any, lower_func_name: str) -> str:
        if "size" in lower_func_name or "length" in lower_func_name or "count" in lower_func_name:
            if value < 100:
                return f"DEFAULT_SIZE_{value}"
            elif value < 10000:
                return f"BUFFER_SIZE_{value}"
            else:
                return f"MAX_SIZE_{value}"

        return f"VALUE_{value}"


class MagicNumberRule(ASTLintRule):
    """Rule to detect magic numbers that should be replaced with named constants."""

    # Common time constants
    SECONDS_PER_MINUTE = 60  # design-lint: ignore[literals.magic-number]
    SECONDS_PER_HOUR = 3600  # design-lint: ignore[literals.magic-number]
    HOURS_PER_DAY = 24  # design-lint: ignore[literals.magic-number]
    DAYS_PER_YEAR = 365  # design-lint: ignore[literals.magic-number]
    MILLISECONDS_PER_SECOND = 1000  # design-lint: ignore[literals.magic-number]

    def __init__(self):
        super().__init__()
        self._context_analyzer = MagicNumberContextAnalyzer()
        self._suggestion_generator = MagicNumberSuggestionGenerator()

    @property
    def rule_id(self) -> str:
        return "literals.magic-number"

    @property
    def rule_name(self) -> str:
        return "Magic Number"

    @property
    def description(self) -> str:
        return "Numeric literals should be replaced with named constants for better maintainability"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"literals", "constants", "maintainability"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.Constant):
            raise TypeError("MagicNumberRule should only receive ast.Constant nodes")
        # Ensure we have a numeric value
        if not isinstance(node.value, (int, float)):
            return []
        config = self.get_configuration(context.metadata or {})

        # Get allowed numbers from configuration
        allowed_numbers = config.get("allowed_numbers", {-1, 0, 1, 2, 10, 100, 1000, 1024})

        if node.value in allowed_numbers:
            return []

        # Check for specific contexts where numbers are acceptable
        if self._context_analyzer.is_acceptable_context(node, context, config):
            return []

        # Generate appropriate suggestion
        suggestion = self._suggestion_generator.generate_constant_suggestion(node.value, context)

        return [
            self.create_violation_from_node(
                context=context,
                node=node,
                message=f"Magic number {node.value} found",
                description=f"Replace magic number {node.value} with a named constant for better maintainability",
                suggestion=suggestion,
                violation_context={
                    "value": node.value,
                    "type": type(node.value).__name__,
                    "function": context.current_function,
                    "class": context.current_class,
                },
            )
        ]

    def _is_acceptable_context(self, node: ast.Constant, context: LintContext, config: dict[str, Any]) -> bool:
        """Check if a magic number is in an acceptable context."""
        return self._context_analyzer.is_acceptable_context(node, context, config)

    def _is_in_range_context(self, context: LintContext) -> bool:
        """Check if the current context is within a range function call."""
        return self._context_analyzer._is_in_range_context(context)

    def _is_in_math_context(self, context: LintContext) -> bool:
        """Check if the current context is within a mathematical operation."""
        if not context.node_stack or len(context.node_stack) < 2:
            return False

        # Look for math operations as direct parent
        parent_node = context.node_stack[-2]
        return isinstance(parent_node, (ast.BinOp, ast.UnaryOp, ast.Compare))

    def _generate_constant_suggestion(self, value: Any, context: LintContext) -> str:
        """Generate a suggestion for naming a magic number constant."""
        return self._suggestion_generator.generate_constant_suggestion(value, context)

    def _get_common_pattern_suggestion(self, value: Any) -> str:
        """Get suggestion for common pattern values."""
        return self._suggestion_generator._get_common_pattern_suggestion(value)

    def _get_context_based_suggestion(self, value: Any, function_name: str) -> str:
        """Get suggestion based on function context."""
        return self._suggestion_generator._get_context_based_suggestion(value, function_name)


class MagicComplexRule(ASTLintRule):
    """Rule to detect magic complex numbers that should be replaced with named constants."""

    # Mathematical constants
    IMAGINARY_UNIT = 1j  # design-lint: ignore[literals.magic-complex]

    @property
    def rule_id(self) -> str:
        return "literals.magic-complex"

    @property
    def rule_name(self) -> str:
        return "Magic Complex Number"

    @property
    def description(self) -> str:
        return "Complex number literals should be replaced with named constants"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"literals", "constants", "complex", "maintainability"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, complex)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.Constant):
            raise TypeError("MagicComplexRule should only receive ast.Constant nodes")
        # Ensure we have a complex value
        if not isinstance(node.value, complex):
            return []

        # Skip test files
        if self._is_test_file(context):
            return []

        # Check if this is a constant definition
        if self._is_constant_definition(node, context):
            return []

        # Always flag complex numbers as they're usually domain-specific
        suggestion = self._generate_complex_constant_suggestion(node.value, context)

        # Format the message based on the complex number format
        if node.value.real == 0:
            # Format pure imaginary numbers nicely (5j instead of 5.0j)
            imag_part = int(node.value.imag) if node.value.imag.is_integer() else node.value.imag
            message = f"Magic complex number {imag_part}j found"
        else:
            message = f"Magic complex number {node.value} found"

        return [
            self.create_violation_from_node(
                context=context,
                node=node,
                message=message,
                description=f"Replace complex number {node.value} with a named constant for better readability",
                suggestion=suggestion,
                violation_context={
                    "value": str(node.value),
                    "real": node.value.real,
                    "imag": node.value.imag,
                    "function": context.current_function,
                    "class": context.current_class,
                },
            )
        ]

    def _generate_complex_constant_suggestion(self, value: complex, context: LintContext) -> str:
        """Generate an appropriate constant name suggestion for complex numbers."""
        function_name = context.current_function or ""

        suggestion = (
            self._get_complex_math_suggestion(value)
            or self._get_complex_context_suggestion(value, function_name)
            or self._get_generic_complex_suggestion(value)
        )

        return suggestion

    def _get_generic_complex_suggestion(self, value: complex) -> str:
        """Get generic suggestion for complex constants."""
        return f"COMPLEX_CONSTANT = {value}  # Consider a more descriptive name"

    def _get_complex_math_suggestion(self, value: complex) -> str:
        """Get suggestion for common complex mathematical constants."""
        if abs(value - self.IMAGINARY_UNIT) < 1e-10:
            return "IMAGINARY_UNIT = 1j"
        if abs(value.real) < 1e-10 and abs(value.imag) > 0:
            return f"IMAGINARY_CONSTANT = {value}"
        if abs(value.imag) < 1e-10 and abs(value.real) > 0:
            return f"REAL_CONSTANT = {value}"
        return ""

    def _get_complex_context_suggestion(self, value: complex, function_name: str) -> str:
        """Get suggestion based on function context for complex numbers."""
        if not function_name:
            return ""

        lower_func_name = function_name.lower()
        if any(word in lower_func_name for word in ["fourier", "fft", "frequency"]):
            return f"FREQUENCY_COMPONENT = {value}"
        if any(word in lower_func_name for word in ["signal", "wave"]):
            return f"SIGNAL_CONSTANT = {value}"
        if any(word in lower_func_name for word in ["impedance", "electrical"]):
            return f"IMPEDANCE_VALUE = {value}"
        return ""

    def _is_complex_constant_name(self, name: str, context: LintContext) -> bool:
        """Check if a name follows complex constant naming conventions."""
        if name.isupper():
            return True
        if "_" in name and name.replace("_", "").isupper():
            return True
        return bool(context.current_class and name and name[0].isupper())

    def _is_constant_definition(self, _node: ast.Constant, context: LintContext) -> bool:
        """Check if this complex number is part of a constant definition."""
        if not context.node_stack or len(context.node_stack) < 2:
            return False

        parent = context.node_stack[-2]
        if not isinstance(parent, ast.Assign) or context.current_function:
            return False

        return any(
            isinstance(target, ast.Name) and self._is_complex_constant_name(target.id, context)
            for target in parent.targets
        )

    def _is_test_file(self, context: LintContext) -> bool:
        """Check if current file is a test file."""
        if not context.file_path:
            return False
        path_str = str(context.file_path).lower()
        return "test" in path_str or "spec" in path_str
