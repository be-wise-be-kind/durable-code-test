#!/usr/bin/env python3
"""
Purpose: Print statement detection rules for the pluggable framework
Scope: Converts print statement linter functionality to framework rules
Overview: Overview: This module enforces proper logging practices by detecting and discouraging the use of
    print statements and console output methods in production code. It identifies various forms of
    console output including print() calls, sys.stdout writes, console.log in JavaScript within
    Python strings, and other debugging output that should be replaced with proper logging. The
    rules check for print statements in all contexts except legitimate uses like CLI output handling,
    and suggest appropriate logging alternatives using the configured logging framework. Each
    violation provides the correct logging method to use based on the output's purpose (debug, info,
    warning, error). The module helps maintain clean production code, ensures consistent log
    formatting, enables proper log level control, and prevents sensitive information from being
    accidentally printed to console in production environments.
Dependencies: Framework interfaces, AST analysis utilities
Exports: Print statement detection rules
Interfaces: All rules implement ASTLintRule interface
Implementation: Rule-based architecture with language-specific detection
"""

import ast
from typing import Any

from tools.design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity


class PrintStatementRule(ASTLintRule):  # thailint: ignore[srp]
    """Rule to detect print statements that should use logging instead.

    AST visitor pattern requires multiple visit methods for different node types.
    """

    @property
    def rule_id(self) -> str:
        return "style.print-statement"

    @property
    def rule_name(self) -> str:
        return "Print Statement Usage"

    @property
    def description(self) -> str:
        return "Print statements should be replaced with proper logging for production code"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"style", "logging", "production"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        # Check for print() function calls
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.Call):
            raise TypeError("PrintStatementRule should only receive ast.Call nodes")
        config = self.get_configuration(context.metadata or {})

        # Check if print statements are allowed in certain contexts
        if self._is_allowed_context(context, config):
            return []

        # Check for disable comments
        if self._has_disable_comment(node, context):
            return []

        suggestion = self._generate_logging_suggestion(node, context)

        return [
            self.create_violation_from_node(
                context=context,
                node=node,
                message="Print statement found - use logging instead",
                description=(
                    "Print statements should be replaced with proper logging "
                    "for better control and production readiness"
                ),
                suggestion=suggestion,
                violation_context={
                    "function": context.current_function,
                    "class": context.current_class,
                },
            )
        ]

    def _is_allowed_context(self, context: LintContext, config: dict[str, Any]) -> bool:
        """Check if print statements are allowed in this context."""
        rule_config = config.get("rules", {}).get(self.rule_id, {})

        if self._is_test_context(context):
            return True

        if self._is_custom_pattern_allowed(context, rule_config):
            return True

        return rule_config.get("allow_in_cli", True) and self._is_cli_output_context(context)

    def _is_test_context(self, context: LintContext) -> bool:
        """Check if context is in test environment."""
        file_path = str(context.file_path)
        test_patterns = ["test_", "/test", "example", "/examples/", "demo"]
        if any(pattern in file_path for pattern in test_patterns):
            return True

        function_name = context.current_function or ""
        return function_name.startswith("test_") or "debug" in function_name.lower() or function_name == "__main__"

    def _is_custom_pattern_allowed(self, context: LintContext, rule_config: dict[str, Any]) -> bool:
        """Check if custom patterns allow this context."""
        allowed_patterns = rule_config.get("allowed_patterns", [])
        function_name = context.current_function or ""
        return allowed_patterns and any(pattern in function_name for pattern in allowed_patterns)

    def _has_disable_comment(self, _node: ast.Call, _context: LintContext) -> bool:
        """Check if there's a disable comment for this print statement."""
        # This would require parsing comments from the source code
        # For now, we'll implement a basic check
        return False

    def _generate_logging_suggestion(self, node: ast.Call, _context: LintContext) -> str:
        """Generate a suggestion for replacing print with logging."""
        if not self._has_single_string_arg(node):
            return "logger.info('...')  # Use appropriate logging level"

        message = node.args[0].value  # type: ignore
        log_level = self._determine_log_level(message)
        return f"logger.{log_level}('{message}')"

    def _is_cli_output_context(self, context: LintContext) -> bool:
        """Check if this is a CLI output context where print statements might be acceptable."""
        # Only allow in CLI scripts with specific user-facing output functions
        file_content = context.file_content or ""
        if "argparse" not in file_content:
            return False

        # Only allow in specific CLI output functions, not general code
        function_name = context.current_function or ""
        cli_output_functions = [
            "print_",
            "display_",
            "show_",
            "output_",
            "list_",
            "_print_",
        ]
        return any(pattern in function_name.lower() for pattern in cli_output_functions)

    def _is_test_function_context(self, context: LintContext) -> bool:
        """Check if this is within a test function (not just any file in test directory)."""
        function_name = context.current_function or ""
        return function_name.startswith("test_") or function_name.startswith("debug_")

    def _has_single_string_arg(self, node: ast.Call) -> bool:
        """Check if node has a single string argument."""
        return len(node.args) == 1 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)

    def _determine_log_level(self, message: str) -> str:
        """Determine appropriate log level based on message content."""
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ["error", "fail", "exception"]):
            return "error"
        if any(keyword in message_lower for keyword in ["warn", "warning"]):
            return "warning"
        if any(keyword in message_lower for keyword in ["info", "start", "finish"]):
            return "info"
        return "debug"


class ConsoleOutputRule(ASTLintRule):  # thailint: ignore[srp]
    """Rule to detect other console output methods that should use logging.

    AST visitor pattern requires multiple visit methods for different node types.
    """

    @property
    def rule_id(self) -> str:
        return "style.console-output"

    @property
    def rule_name(self) -> str:
        return "Console Output Usage"

    @property
    def description(self) -> str:
        return "Console output methods should be replaced with proper logging"

    @property
    def severity(self) -> Severity:
        return Severity.INFO

    @property
    def categories(self) -> set[str]:
        return {"style", "logging", "console"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        if not isinstance(node, ast.Call):
            return False

        return self._is_console_output_call(node)

    def _is_console_output_call(self, node: ast.Call) -> bool:
        """Check if this is a console output call."""
        if not isinstance(node.func, ast.Attribute):
            return False

        return self._is_sys_output_call(node) or self._is_console_log_call(node)

    def _is_sys_output_call(self, node: ast.Call) -> bool:
        """Check for sys.stdout.write, sys.stderr.write calls."""
        func = node.func
        if not isinstance(func, ast.Attribute):
            return False

        return (
            isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "sys"
            and func.value.attr in ["stdout", "stderr"]
            and func.attr == "write"
        )

    def _is_console_log_call(self, node: ast.Call) -> bool:
        """Check for console.log calls."""
        func = node.func
        if not isinstance(func, ast.Attribute):
            return False

        return isinstance(func.value, ast.Name) and func.value.id == "console" and func.attr == "log"

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        if not isinstance(node, ast.Call):
            raise TypeError("ConsoleOutputRule should only receive ast.Call nodes")
        config = self.get_configuration(context.metadata or {})

        # Skip if in allowed contexts
        if self._is_allowed_context(context, config):
            return []

        output_method = self._get_output_method(node)
        suggestion = self._generate_suggestion(output_method)

        return [
            self.create_violation_from_node(
                context,
                node,
                message=(f"Console output method '{output_method}' found - use logging instead"),
                description=f"Replace {output_method} with appropriate logging calls",
                suggestion=suggestion,
                violation_context={"output_method": output_method},
            )
        ]

    def _is_allowed_context(self, context: LintContext, config: dict[str, Any]) -> bool:
        """Check if console output is allowed in this context."""
        if self._is_test_or_script_context(context):
            return True

        if self._is_special_function_context(context):
            return True

        rule_config = config.get("rules", {}).get(self.rule_id, {})
        return self._is_cli_context_allowed(context, rule_config)

    def _is_test_or_script_context(self, context: LintContext) -> bool:
        """Check if context is in test or script environment."""
        file_path = str(context.file_path)
        allowed_patterns = [
            "test_",
            "/test",
            "example",
            "/examples/",
            "demo",
            "script",
            "/scripts/",
        ]
        return any(pattern in file_path for pattern in allowed_patterns)

    def _is_special_function_context(self, context: LintContext) -> bool:
        """Check if function is test, debug, or main function."""
        function_name = context.current_function or ""
        return (
            function_name.startswith("test_")
            or "debug" in function_name.lower()
            or function_name in ["__main__", "main"]
        )

    def _is_cli_context_allowed(self, context: LintContext, rule_config: dict[str, Any]) -> bool:
        """Check if CLI output context is allowed."""
        if not rule_config.get("allow_in_cli", True):
            return False

        file_content = context.file_content or ""
        if "argparse" not in file_content:
            return False

        function_name = context.current_function or ""
        cli_output_functions = [
            "print_",
            "display_",
            "show_",
            "output_",
            "list_",
            "_print_",
        ]
        return any(pattern in function_name.lower() for pattern in cli_output_functions)

    def _get_output_method(self, node: ast.Call) -> str:
        """Get the name of the output method being used."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Attribute):
                # sys.stdout.write
                if isinstance(node.func.value.value, ast.Name):
                    return f"{node.func.value.value.id}.{node.func.value.attr}.{node.func.attr}"
            else:
                # console.log
                if isinstance(node.func.value, ast.Name):
                    return f"{node.func.value.id}.{node.func.attr}"
        return "unknown"

    def _generate_suggestion(self, output_method: str) -> str:
        """Generate appropriate logging suggestion based on output method."""
        if "stderr" in output_method:
            return "logger.error('...')  # For error output"
        if "stdout" in output_method:
            return "logger.info('...')   # For standard output"
        return "logger.debug('...')  # Use appropriate logging level"
