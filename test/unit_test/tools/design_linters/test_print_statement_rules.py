#!/usr/bin/env python3
"""
Purpose: Comprehensive unit tests for print statement rules
Scope: Test all rule classes and methods in print_statement_rules.py
Overview: This module provides comprehensive tests for PrintStatementRule and
    ConsoleOutputRule classes, including property tests, node checking, violation
    detection, and configuration handling.
Dependencies: unittest, ast, framework interfaces
Exports: TestPrintStatementRule, TestConsoleOutputRule, TestRuleIntegration
Interfaces: Standard unittest.TestCase interface for test execution
Implementation: Comprehensive test coverage using unittest framework with AST parsing
"""

import ast
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, "/home/stevejackson/Projects/durable-code-test-2")

from tools.design_linters.framework.interfaces import LintContext, LintViolation, Severity
from tools.design_linters.rules.style.print_statement_rules import ConsoleOutputRule, PrintStatementRule


class TestPrintStatementRule(unittest.TestCase):  # thailint: ignore[srp]
    """Test PrintStatementRule class."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = PrintStatementRule()
        self.context = LintContext(file_path=Path("/src/module.py"), file_content="", ast_tree=None, node_stack=[])

    def test_rule_properties(self):
        """Test rule property getters."""
        self.assertEqual(self.rule.rule_id, "style.print-statement")
        self.assertEqual(self.rule.rule_name, "Print Statement Usage")
        self.assertEqual(
            self.rule.description, "Print statements should be replaced with proper logging for production code"
        )
        self.assertEqual(self.rule.severity, Severity.WARNING)
        self.assertEqual(self.rule.categories, {"style", "logging", "production"})

    def test_should_check_node_with_print_call(self):
        """Test should_check_node returns True for print() calls."""
        # Create a print() function call AST node
        code = "print('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # Extract the Call node

        result = self.rule.should_check_node(call_node, self.context)
        self.assertTrue(result)

    def test_should_check_node_with_other_function_call(self):
        """Test should_check_node returns False for non-print function calls."""
        # Create a different function call AST node
        code = "len([1, 2, 3])"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # Extract the Call node

        result = self.rule.should_check_node(call_node, self.context)
        self.assertFalse(result)

    def test_should_check_node_with_method_call(self):
        """Test should_check_node returns False for method calls."""
        # Create a method call AST node
        code = "obj.print('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # Extract the Call node

        result = self.rule.should_check_node(call_node, self.context)
        self.assertFalse(result)

    def test_should_check_node_with_non_call_node(self):
        """Test should_check_node returns False for non-Call nodes."""
        # Create a Name node
        code = "print"
        tree = ast.parse(code, mode="eval")
        name_node = tree.body  # Extract the Name node

        result = self.rule.should_check_node(name_node, self.context)
        self.assertFalse(result)

    def test_check_node_with_print_call(self):
        """Test check_node detects print statement violation."""
        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)

        self.assertEqual(len(violations), 1)
        violation = violations[0]
        self.assertEqual(violation.rule_id, "style.print-statement")
        self.assertEqual(violation.severity, Severity.WARNING)
        self.assertEqual(violation.message, "Print statement found - use logging instead")
        self.assertIn("Print statements should be replaced", violation.description)
        self.assertIn("logger.", violation.suggestion)

    def test_check_node_with_invalid_node_type(self):
        """Test check_node raises TypeError for non-Call nodes."""
        code = "print"
        tree = ast.parse(code, mode="eval")
        name_node = tree.body  # Extract the Name node

        with self.assertRaises(TypeError) as cm:
            self.rule.check_node(name_node, self.context)

        self.assertIn("PrintStatementRule should only receive ast.Call nodes", str(cm.exception))

    def test_check_node_in_allowed_context_test_file(self):
        """Test check_node returns no violations in test files."""
        # Set context to a test file
        self.context.file_path = Path("/test_module.py")

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_test_function(self):
        """Test check_node returns no violations in test functions."""
        # Set context to a test function
        self.context.current_function = "test_something"

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_main_function(self):
        """Test check_node returns no violations in __main__ context."""
        # Set context to __main__
        self.context.current_function = "__main__"

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_debug_function(self):
        """Test check_node returns no violations in debug functions."""
        # Set context to a debug function
        self.context.current_function = "debug_output"

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_example_file(self):
        """Test check_node returns no violations in example files."""
        # Set context to an example file
        self.context.file_path = Path("/examples/demo.py")

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_is_allowed_context_with_test_file(self):
        """Test _is_allowed_context returns True for test files."""
        self.context.file_path = Path("/test_something.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_regular_file(self):
        """Test _is_allowed_context returns False for regular files."""
        self.context.file_path = Path("/regular_module.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertFalse(result)

    def test_has_disable_comment(self):
        """Test _has_disable_comment method."""
        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        # Current implementation always returns False
        result = self.rule._has_disable_comment(call_node, self.context)
        self.assertFalse(result)

    def test_generate_logging_suggestion_error_message(self):
        """Test _generate_logging_suggestion for error messages."""
        code = "print('Error occurred')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.error('Error occurred')")

    def test_generate_logging_suggestion_warning_message(self):
        """Test _generate_logging_suggestion for warning messages."""
        code = "print('Warning: this is deprecated')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.warning('Warning: this is deprecated')")

    def test_generate_logging_suggestion_info_message(self):
        """Test _generate_logging_suggestion for info messages."""
        code = "print('Starting process')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.info('Starting process')")

    def test_generate_logging_suggestion_debug_message(self):
        """Test _generate_logging_suggestion for regular messages."""
        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.debug('hello world')")

    def test_generate_logging_suggestion_complex_call(self):
        """Test _generate_logging_suggestion for complex print calls."""
        code = "print(variable, 'text', 123)"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.info('...')  # Use appropriate logging level")

    def test_generate_logging_suggestion_no_args(self):
        """Test _generate_logging_suggestion for print with no args."""
        code = "print()"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.info('...')  # Use appropriate logging level")

    def test_generate_logging_suggestion_non_string_arg(self):
        """Test _generate_logging_suggestion for non-string arguments."""
        code = "print(42)"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        suggestion = self.rule._generate_logging_suggestion(call_node, self.context)
        self.assertEqual(suggestion, "logger.info('...')  # Use appropriate logging level")

    def test_violation_context_includes_function_and_class(self):
        """Test that violations include function and class context."""
        self.context.current_function = "my_function"
        self.context.current_class = "MyClass"

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)

        self.assertEqual(len(violations), 1)
        violation = violations[0]
        self.assertEqual(violation.context["function"], "my_function")
        self.assertEqual(violation.context["class"], "MyClass")

    def test_get_configuration_method(self):
        """Test get_configuration method."""
        config = {}
        result = self.rule.get_configuration(config)
        self.assertEqual(result, {})

    def test_check_node_with_custom_config(self):
        """Test check_node with custom configuration."""
        # Set metadata with custom config
        self.context.metadata = {
            "rules": {"style.print-statement": {"config": {"allowed_patterns": ["custom_debug_"]}}}
        }
        self.context.current_function = "custom_debug_function"

        code = "print('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)


class TestConsoleOutputRule(unittest.TestCase):  # thailint: ignore[srp]
    """Test ConsoleOutputRule class."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = ConsoleOutputRule()
        self.context = LintContext(file_path=Path("/src/module.py"), file_content="", ast_tree=None, node_stack=[])

    def test_rule_properties(self):
        """Test rule property getters."""
        self.assertEqual(self.rule.rule_id, "style.console-output")
        self.assertEqual(self.rule.rule_name, "Console Output Usage")
        self.assertEqual(self.rule.description, "Console output methods should be replaced with proper logging")
        self.assertEqual(self.rule.severity, Severity.INFO)
        self.assertEqual(self.rule.categories, {"style", "logging", "console"})

    def test_should_check_node_with_sys_stdout_write(self):
        """Test should_check_node returns True for sys.stdout.write calls."""
        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        result = self.rule.should_check_node(call_node, self.context)
        self.assertTrue(result)

    def test_should_check_node_with_sys_stderr_write(self):
        """Test should_check_node returns True for sys.stderr.write calls."""
        code = "sys.stderr.write('error')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        result = self.rule.should_check_node(call_node, self.context)
        self.assertTrue(result)

    def test_should_check_node_with_console_log(self):
        """Test should_check_node returns True for console.log calls."""
        code = "console.log('message')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        result = self.rule.should_check_node(call_node, self.context)
        self.assertTrue(result)

    def test_should_check_node_with_regular_function_call(self):
        """Test should_check_node returns False for regular function calls."""
        code = "print('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        result = self.rule.should_check_node(call_node, self.context)
        self.assertFalse(result)

    def test_should_check_node_with_other_sys_call(self):
        """Test should_check_node returns False for other sys calls."""
        code = "sys.exit(0)"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        result = self.rule.should_check_node(call_node, self.context)
        self.assertFalse(result)

    def test_should_check_node_with_non_call_node(self):
        """Test should_check_node returns False for non-Call nodes."""
        code = "sys.stdout"
        tree = ast.parse(code, mode="eval")
        attr_node = tree.body

        result = self.rule.should_check_node(attr_node, self.context)
        self.assertFalse(result)

    def test_check_node_with_sys_stdout_write(self):
        """Test check_node detects sys.stdout.write violation."""
        code = "sys.stdout.write('hello world')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)

        self.assertEqual(len(violations), 1)
        violation = violations[0]
        self.assertEqual(violation.rule_id, "style.console-output")
        self.assertEqual(violation.severity, Severity.INFO)
        self.assertIn("Console output method", violation.message)
        self.assertIn("sys.stdout.write", violation.message)
        self.assertEqual(violation.context["output_method"], "sys.stdout.write")

    def test_check_node_with_sys_stderr_write(self):
        """Test check_node detects sys.stderr.write violation."""
        code = "sys.stderr.write('error message')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)

        self.assertEqual(len(violations), 1)
        violation = violations[0]
        self.assertIn("sys.stderr.write", violation.message)
        self.assertEqual(violation.context["output_method"], "sys.stderr.write")

    def test_check_node_with_console_log(self):
        """Test check_node detects console.log violation."""
        code = "console.log('message')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)

        self.assertEqual(len(violations), 1)
        violation = violations[0]
        self.assertIn("console.log", violation.message)
        self.assertEqual(violation.context["output_method"], "console.log")

    def test_check_node_with_invalid_node_type(self):
        """Test check_node raises TypeError for non-Call nodes."""
        code = "sys.stdout"
        tree = ast.parse(code, mode="eval")
        attr_node = tree.body

        with self.assertRaises(TypeError) as cm:
            self.rule.check_node(attr_node, self.context)

        self.assertIn("ConsoleOutputRule should only receive ast.Call nodes", str(cm.exception))

    def test_check_node_in_allowed_context_test_file(self):
        """Test check_node returns no violations in test files."""
        self.context.file_path = Path("/test_module.py")

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_example_file(self):
        """Test check_node returns no violations in example files."""
        self.context.file_path = Path("/examples/demo.py")

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_script_file(self):
        """Test check_node returns no violations in script files."""
        self.context.file_path = Path("/scripts/utility.py")

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_test_function(self):
        """Test check_node returns no violations in test functions."""
        self.context.current_function = "test_something"

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_debug_function(self):
        """Test check_node returns no violations in debug functions."""
        self.context.current_function = "debug_something"

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_check_node_in_allowed_context_main_function(self):
        """Test check_node returns no violations in main context."""
        self.context.current_function = "main"

        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violations = self.rule.check_node(call_node, self.context)
        self.assertEqual(len(violations), 0)

    def test_is_allowed_context_with_test_file(self):
        """Test _is_allowed_context returns True for test files."""
        self.context.file_path = Path("/test_something.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_example_file(self):
        """Test _is_allowed_context returns True for example files."""
        self.context.file_path = Path("/example_something.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_demo_file(self):
        """Test _is_allowed_context returns True for demo files."""
        self.context.file_path = Path("/demo_something.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_script_file(self):
        """Test _is_allowed_context returns True for script files."""
        self.context.file_path = Path("/scripts/utility.py")
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_test_function(self):
        """Test _is_allowed_context returns True for test functions."""
        self.context.file_path = Path("/regular.py")
        self.context.current_function = "test_something"
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_debug_function(self):
        """Test _is_allowed_context returns True for debug functions."""
        self.context.file_path = Path("/regular.py")
        self.context.current_function = "debug_something"
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_main_function(self):
        """Test _is_allowed_context returns True for main function."""
        self.context.file_path = Path("/regular.py")
        self.context.current_function = "main"
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertTrue(result)

    def test_is_allowed_context_with_regular_context(self):
        """Test _is_allowed_context returns False for regular context."""
        self.context.file_path = Path("/regular.py")
        self.context.current_function = "regular_function"
        config = {}

        result = self.rule._is_allowed_context(self.context, config)
        self.assertFalse(result)

    def test_get_output_method_sys_stdout_write(self):
        """Test _get_output_method for sys.stdout.write."""
        code = "sys.stdout.write('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        method = self.rule._get_output_method(call_node)
        self.assertEqual(method, "sys.stdout.write")

    def test_get_output_method_sys_stderr_write(self):
        """Test _get_output_method for sys.stderr.write."""
        code = "sys.stderr.write('error')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        method = self.rule._get_output_method(call_node)
        self.assertEqual(method, "sys.stderr.write")

    def test_get_output_method_console_log(self):
        """Test _get_output_method for console.log."""
        code = "console.log('message')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        method = self.rule._get_output_method(call_node)
        self.assertEqual(method, "console.log")

    def test_get_output_method_unknown(self):
        """Test _get_output_method for unknown method."""
        # Create a function call that doesn't match expected patterns
        code = "unknown_func()"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        method = self.rule._get_output_method(call_node)
        self.assertEqual(method, "unknown")

    def test_generate_suggestion_for_stderr(self):
        """Test _generate_suggestion for stderr output."""
        suggestion = self.rule._generate_suggestion("sys.stderr.write")
        self.assertEqual(suggestion, "logger.error('...')  # For error output")

    def test_generate_suggestion_for_stdout(self):
        """Test _generate_suggestion for stdout output."""
        suggestion = self.rule._generate_suggestion("sys.stdout.write")
        self.assertEqual(suggestion, "logger.info('...')   # For standard output")

    def test_generate_suggestion_for_console(self):
        """Test _generate_suggestion for console output."""
        suggestion = self.rule._generate_suggestion("console.log")
        self.assertEqual(suggestion, "logger.debug('...')  # Use appropriate logging level")

    def test_generate_suggestion_for_unknown(self):
        """Test _generate_suggestion for unknown output method."""
        suggestion = self.rule._generate_suggestion("unknown.method")
        self.assertEqual(suggestion, "logger.debug('...')  # Use appropriate logging level")

    def test_get_configuration_method(self):
        """Test get_configuration method."""
        config = {}
        result = self.rule.get_configuration(config)
        self.assertEqual(result, {})


class TestRuleIntegration(unittest.TestCase):  # thailint: ignore[srp]
    """Test integration between rules and framework."""

    def test_both_rules_implement_astlintrule(self):
        """Test that both rules properly implement ASTLintRule interface."""
        from tools.design_linters.framework.interfaces import ASTLintRule

        print_rule = PrintStatementRule()
        console_rule = ConsoleOutputRule()

        self.assertIsInstance(print_rule, ASTLintRule)
        self.assertIsInstance(console_rule, ASTLintRule)

    def test_both_rules_have_unique_ids(self):
        """Test that both rules have unique rule IDs."""
        print_rule = PrintStatementRule()
        console_rule = ConsoleOutputRule()

        self.assertNotEqual(print_rule.rule_id, console_rule.rule_id)

    def test_create_violation_helper_method(self):
        """Test create_violation helper method works correctly."""
        rule = PrintStatementRule()
        context = LintContext(file_path=Path("/src/module.py"))

        code = "print('hello')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        violation = rule.create_violation_from_node(
            context=context,
            node=call_node,
            message="Test message",
            description="Test description",
            suggestion="Test suggestion",
            violation_context={"test": "value"},
        )

        self.assertEqual(violation.rule_id, "style.print-statement")
        self.assertEqual(violation.file_path, "/src/module.py")
        self.assertEqual(violation.message, "Test message")
        self.assertEqual(violation.description, "Test description")
        self.assertEqual(violation.suggestion, "Test suggestion")
        self.assertEqual(violation.context["test"], "value")
        self.assertEqual(violation.severity, Severity.WARNING)

    def test_is_enabled_method(self):
        """Test is_enabled method works correctly."""
        rule = PrintStatementRule()

        # Test with None config
        self.assertTrue(rule.is_enabled(None))

        # Test with empty config
        self.assertTrue(rule.is_enabled({}))

        # Test with rule enabled
        config = {"rules": {"style.print-statement": {"enabled": True}}}
        self.assertTrue(rule.is_enabled(config))

        # Test with rule disabled
        config = {"rules": {"style.print-statement": {"enabled": False}}}
        self.assertFalse(rule.is_enabled(config))

    def test_rules_work_with_ast_traversal(self):
        """Test that rules work properly with AST traversal."""
        print_rule = PrintStatementRule()
        console_rule = ConsoleOutputRule()

        # Create a context with AST
        code = """
import sys
print('hello')
sys.stdout.write('world')
console.log('debug')
"""
        tree = ast.parse(code)
        context = LintContext(file_path=Path("/src/module.py"), file_content=code, ast_tree=tree)

        # Test print rule
        print_violations = print_rule.check(context)
        self.assertEqual(len(print_violations), 1)
        self.assertEqual(print_violations[0].rule_id, "style.print-statement")

        # Test console rule
        console_violations = console_rule.check(context)
        self.assertEqual(len(console_violations), 2)  # sys.stdout.write and console.log
        self.assertEqual(console_violations[0].rule_id, "style.console-output")
        self.assertEqual(console_violations[1].rule_id, "style.console-output")


if __name__ == "__main__":
    unittest.main()
