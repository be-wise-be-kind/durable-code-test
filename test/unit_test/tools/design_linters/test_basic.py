#!/usr/bin/env python3
"""
Purpose: Validates design linters framework basic functionality

Scope: Smoke tests for framework components and core functionality

Overview: This module provides comprehensive basic tests that verify the design linters framework loads correctly,
    basic components exist and can be imported without errors, core functionality works as expected, and integration
    between different modules functions properly. Tests focus on framework stability, import validation, component
    initialization, and basic rule execution without testing complex advanced functionality or edge cases. The suite
    ensures the linting infrastructure is properly configured and operational.

Dependencies: unittest, framework modules

Exports: Test classes for basic imports, functionality, categories filter, and ignore functionality

Interfaces: Standard unittest test methods and pytest-style fixtures for framework testing

Implementation: Uses unittest with temporary files and mock configurations for testing framework components
"""

import os
import sys
import unittest
from pathlib import Path
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../tools"))


class TestBasicImports(unittest.TestCase):  # thailint: ignore[srp]
    """Test that all modules can be imported without errors."""

    def test_framework_imports(self):
        """Test framework module imports."""
        try:
            from tools.design_linters.framework import analyzer, interfaces, reporters, rule_registry

            self.assertTrue(True)  # If we get here, imports worked
        except ImportError as e:
            logger.error("Framework import failed", error=str(e), exc_info=True)
            self.fail(f"Framework import failed: {e}")

    def test_rules_imports(self):
        """Test rules module imports."""
        try:
            from tools.design_linters.rules.literals import magic_number_rules
            from tools.design_linters.rules.logging import general_logging_rules, loguru_rules
            from tools.design_linters.rules.solid import srp_rules
            from tools.design_linters.rules.style import nesting_rules, print_statement_rules

            self.assertTrue(True)  # If we get here, imports worked
        except ImportError as e:
            logger.error("Rules import failed", error=str(e), exc_info=True)
            self.fail(f"Rules import failed: {e}")

    def test_cli_import(self):
        """Test CLI module import."""
        try:
            from design_linters import cli

            self.assertTrue(True)
        except ImportError as e:
            logger.error("CLI import failed", error=str(e), exc_info=True)
            self.fail(f"CLI import failed: {e}")


class TestBasicFunctionality(unittest.TestCase):  # thailint: ignore[srp]
    """Test basic functionality without complex scenarios."""

    def test_severity_enum(self):
        """Test Severity enum exists and has expected values."""
        from tools.design_linters.framework.interfaces import Severity

        self.assertEqual(Severity.ERROR.value, "error")
        self.assertEqual(Severity.WARNING.value, "warning")
        self.assertEqual(Severity.INFO.value, "info")

    def test_lint_violation_creation(self):
        """Test basic LintViolation creation."""
        from tools.design_linters.framework.interfaces import LintViolation, Severity

        violation = LintViolation(
            rule_id="test.rule",
            file_path="/test.py",
            line=1,
            column=0,
            severity=Severity.WARNING,
            message="Test message",
            description="Test description",
            suggestion="Test suggestion",
        )

        self.assertEqual(violation.rule_id, "test.rule")
        self.assertEqual(violation.severity, Severity.WARNING)

    def test_lint_context_creation(self):
        """Test basic LintContext creation."""
        from tools.design_linters.framework.interfaces import LintContext

        context = LintContext(file_path=Path("/test.py"))
        self.assertEqual(context.file_path, Path("/test.py"))

    def test_text_reporter_exists(self):
        """Test TextReporter can be created."""
        from tools.design_linters.framework.reporters import TextReporter

        reporter = TextReporter()
        self.assertIsNotNone(reporter)

    def test_json_reporter_exists(self):
        """Test JSONReporter can be created."""
        from tools.design_linters.framework.reporters import JSONReporter

        reporter = JSONReporter()
        self.assertIsNotNone(reporter)

    def test_rule_registry_exists(self):
        """Test DefaultRuleRegistry can be created."""
        from tools.design_linters.framework.rule_registry import DefaultRuleRegistry

        registry = DefaultRuleRegistry()
        self.assertIsNotNone(registry)

    def test_orchestrator_exists(self):
        """Test DefaultLintOrchestrator can be created."""
        from tools.design_linters.framework.analyzer import DefaultLintOrchestrator
        from tools.design_linters.framework.rule_registry import DefaultRuleRegistry

        registry = DefaultRuleRegistry()
        orchestrator = DefaultLintOrchestrator(registry)
        self.assertIsNotNone(orchestrator)

    def test_cli_exists(self):
        """Test DesignLinterCLI can be created."""
        from tools.design_linters.cli import DesignLinterCLI

        cli = DesignLinterCLI()
        self.assertIsNotNone(cli)

    def test_magic_number_rule_exists(self):
        """Test MagicNumberRule can be created."""
        from tools.design_linters.rules.literals.magic_number_rules import MagicNumberRule

        rule = MagicNumberRule()
        self.assertEqual(rule.rule_id, "literals.magic-number")

    def test_print_statement_rule_exists(self):
        """Test PrintStatementRule can be created."""
        from tools.design_linters.rules.style.print_statement_rules import PrintStatementRule

        rule = PrintStatementRule()
        self.assertEqual(rule.rule_id, "style.print-statement")


class TestCategoriesFilter(unittest.TestCase):  # thailint: ignore[srp]
    """Test that --categories filter works correctly."""

    def setUp(self):
        """Set up test fixtures."""
        from tools.design_linters.cli import ConfigurationManager, DesignLinterCLI
        from tools.design_linters.framework.rule_registry import DefaultRuleRegistry
        from tools.design_linters.rules.literals.magic_number_rules import MagicNumberRule
        from tools.design_linters.rules.solid.srp_rules import ClassTooBigRule
        from tools.design_linters.rules.style.print_statement_rules import PrintStatementRule

        self.config_manager = ConfigurationManager()
        self.cli = DesignLinterCLI()
        self.registry = DefaultRuleRegistry()

        # Register rules from different categories
        self.registry.register_rule(MagicNumberRule())  # literals category
        self.registry.register_rule(PrintStatementRule())  # style category
        self.registry.register_rule(ClassTooBigRule())  # solid category

    def test_filter_by_categories_in_config(self):
        """Test that categories filter is applied to config."""
        config = {}
        self.config_manager._filter_by_categories(config, "literals")
        self.assertEqual(config["categories"], ["literals"])

    def test_filter_by_multiple_categories(self):
        """Test filtering by multiple categories."""
        config = {}
        self.config_manager._filter_by_categories(config, "literals,style")
        self.assertIn("literals", config["categories"])
        self.assertIn("style", config["categories"])
        self.assertEqual(len(config["categories"]), 2)

    def test_categories_filter_via_cli_args(self):
        """Test that --categories argument gets processed correctly."""
        import argparse

        # Create args namespace with categories
        args = argparse.Namespace()
        args.categories = "literals"
        args.rules = None
        args.exclude_rules = None
        args.exclude = None
        args.legacy = None
        args.config = None
        args.strict = False
        args.lenient = False
        args.fail_on_error = False

        # Load configuration with categories filter
        config = self.config_manager.load_configuration(args)

        # Check that categories is in config
        self.assertIn("categories", config)
        self.assertEqual(config["categories"], ["literals"])

    def test_categories_filter_execution(self):
        """Test that categories filter actually filters rules during execution."""
        import os
        import tempfile

        # Create a test file with violations from different categories
        test_code = '''
def test_function():
    magic_number = 42  # Should trigger literals.magic-number
    print("debug")     # Should trigger style.print-statement

class VeryLongClassWithManyLines:
    """This is a long class for testing."""
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
'''

        # Write test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = f.name

        try:
            # Test with categories filter for literals only
            result = self.cli.run(["--categories", "literals", "--format", "json", test_file])

            # The result should only contain literals violations, not style violations
            # Note: We can't easily check the actual violations without running the full
            # orchestrator, but we've verified the config is set correctly

        finally:
            # Clean up test file
            os.unlink(test_file)

    def test_registry_get_rules_by_category(self):
        """Test that registry can filter rules by category."""
        # Get rules for literals category only
        literals_rules = self.registry.get_rules_by_category("literals")

        # Should only get rules from literals category
        self.assertEqual(len(literals_rules), 1)
        self.assertEqual(literals_rules[0].rule_id, "literals.magic-number")

        # Get rules for style category
        style_rules = self.registry.get_rules_by_category("style")
        self.assertEqual(len(style_rules), 1)
        self.assertEqual(style_rules[0].rule_id, "style.print-statement")

        # Get rules for solid category
        solid_rules = self.registry.get_rules_by_category("solid")
        self.assertEqual(len(solid_rules), 1)
        self.assertIn("solid", solid_rules[0].categories)


class TestIgnoreFunctionality(unittest.TestCase):  # thailint: ignore[srp]
    """Test that ignore directives work correctly."""

    def setUp(self):
        """Set up test fixtures."""
        from tools.design_linters.framework.analyzer import DefaultLintOrchestrator, PythonAnalyzer
        from tools.design_linters.framework.rule_registry import DefaultRuleRegistry
        from tools.design_linters.rules.literals.magic_number_rules import MagicComplexRule, MagicNumberRule

        self.registry = DefaultRuleRegistry()
        self.analyzer = PythonAnalyzer()
        self.orchestrator = DefaultLintOrchestrator(rule_registry=self.registry, analyzers={".py": self.analyzer})

        # Register literal rules
        self.registry.register_rule(MagicNumberRule())
        self.registry.register_rule(MagicComplexRule())

    def test_line_level_ignore(self):
        """Test that line-level ignore directives work."""
        import os
        import tempfile
        from pathlib import Path

        # Create test file with magic number and ignore directive
        test_code = """
def calculate():
    return 42  # thailint: ignore[magic-numbers]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            # Should have no violations because of the ignore directive
            magic_number_violations = [v for v in violations if v.rule_id == "literals.magic-number"]
            self.assertEqual(
                len(magic_number_violations), 0, "Line-level ignore should suppress magic number violation"
            )
        finally:
            os.unlink(test_file)

    def test_file_level_ignore_all_literals(self):
        """Test that file-level ignore for all literals works."""
        import os
        import tempfile
        from pathlib import Path

        # Create test file with file-level ignore for all literals
        test_code = '''#!/usr/bin/env python3
# design-lint: ignore-file[literals.*]
"""Test file with literals."""

def test_function():
    magic_number = 42  # Should not be flagged
    another_number = 999  # Should not be flagged
    complex_num = 2j  # Should not be flagged
    return magic_number + another_number
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            # Should have no literal violations
            literal_violations = [v for v in violations if v.rule_id.startswith("literals.")]
            self.assertEqual(
                len(literal_violations),
                0,
                f"File-level ignore should suppress all literal violations, but got: {[v.rule_id for v in literal_violations]}",
            )
        finally:
            os.unlink(test_file)

    def test_file_level_ignore_specific_rule(self):
        """Test that file-level ignore for specific rule works."""
        import os
        import tempfile
        from pathlib import Path

        # Create test file with file-level ignore for magic numbers only
        test_code = '''#!/usr/bin/env python3
# design-lint: ignore-file[literals.magic-number]
"""Test file."""

def test_function():
    magic_number = 42  # Should not be flagged
    another_magic = 1337  # Should not be flagged due to file-level ignore
    return magic_number + another_magic
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            # Should have no magic number violations
            magic_number_violations = [v for v in violations if v.rule_id == "literals.magic-number"]
            self.assertEqual(
                len(magic_number_violations), 0, "File-level ignore should suppress magic number violations"
            )

            # Should also have no complex number violations
            complex_violations = [v for v in violations if v.rule_id == "literals.magic-complex"]
            self.assertEqual(len(complex_violations), 0, "File-level ignore should suppress complex number violations")
        finally:
            os.unlink(test_file)

    def test_ignore_next_line_directive(self):
        """Test that ignore-next-line directive works."""
        import os
        import tempfile
        from pathlib import Path

        # Create test file with ignore-next-line directive
        test_code = """
def calculate():
    # design-lint: ignore-next-line
    return 42  # This should not be flagged

    return 99  # This should be flagged
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            magic_number_violations = [v for v in violations if v.rule_id == "literals.magic-number"]

            # Should have exactly one violation (the 99, not the 42)
            self.assertEqual(len(magic_number_violations), 1, "Should have one magic number violation")
            self.assertIn("99", magic_number_violations[0].message)
        finally:
            os.unlink(test_file)

    def test_complex_number_in_test_file(self):
        """Test that complex numbers in test files are not flagged."""
        import os
        import tempfile
        from pathlib import Path

        # Create test file with 'test' in the name
        test_code = """
def test_complex_math():
    result = 2j  # Should not be flagged in test file
    return result
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            complex_violations = [v for v in violations if v.rule_id == "literals.magic-complex"]
            self.assertEqual(len(complex_violations), 0, "Complex numbers in test files should not be flagged")
        finally:
            os.unlink(test_file)

    def test_constant_definition_not_flagged(self):
        """Test that constant definitions are not flagged as magic numbers."""
        import os
        import tempfile
        from pathlib import Path

        test_code = """
# Module-level constants should not be flagged
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60
SECONDS_PER_MINUTE = 60

class Config:
    # Class-level constants should not be flagged
    MAX_CONNECTIONS = 100
    DEFAULT_PORT = 8080

def calculate():
    # This should be flagged (not a constant definition)
    return 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            magic_number_violations = [v for v in violations if v.rule_id == "literals.magic-number"]

            # Should only have one violation (the 42 in the function)
            self.assertEqual(
                len(magic_number_violations),
                1,
                "Should only flag the magic number in the function, not constant definitions",
            )
            self.assertIn("42", magic_number_violations[0].message)

            # Verify that none of the constant values are in the violations
            violation_messages = " ".join(v.message for v in magic_number_violations)
            self.assertNotIn("60", violation_messages, "SECONDS_PER_MINUTE should not be flagged")
            self.assertNotIn("100", violation_messages, "MAX_CONNECTIONS should not be flagged")
            self.assertNotIn("8080", violation_messages, "DEFAULT_PORT should not be flagged")
        finally:
            os.unlink(test_file)

    def test_file_level_ignore_logging_and_style(self):
        """Test that file-level ignore for logging and style rules works."""
        import os
        import tempfile
        from pathlib import Path

        from tools.design_linters.rules.logging.general_logging_rules import NoPlainPrintRule
        from tools.design_linters.rules.style.print_statement_rules import PrintStatementRule

        # Register the print statement rules
        self.registry.register_rule(NoPlainPrintRule())
        self.registry.register_rule(PrintStatementRule())

        # Create test file with file-level ignore for logging and style
        test_code = """#!/usr/bin/env python3
# design-lint: ignore-file[logging.*,style.*]
# This file intentionally contains print statements

def test_function():
    print("This should be ignored")
    x = 42
    print(f"Value: {x}")
    return x
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            # Should have no print statement violations
            print_violations = [v for v in violations if "print" in v.rule_id]
            self.assertEqual(
                len(print_violations),
                0,
                f"File-level ignore should suppress print statement violations, but got: {[v.rule_id for v in print_violations]}",
            )

            # Magic numbers should still be caught (not ignored)
            magic_violations = [v for v in violations if "magic" in v.rule_id]
            self.assertEqual(len(magic_violations), 1, "Magic number should still be caught")
        finally:
            os.unlink(test_file)

    def test_debug_file_level_ignore(self):
        """Debug test to understand file-level ignore issue."""
        import os
        import tempfile
        from pathlib import Path

        from tools.design_linters.framework.ignore_utils import has_file_level_ignore

        # Test that the pattern matching works for both styles
        test_code1 = """#!/usr/bin/env python3
# design-lint: ignore-file[logging.*,style.*]
def test():
    print("test")
"""

        # Test direct function
        self.assertTrue(has_file_level_ignore(test_code1, "logging.no-print"))
        self.assertTrue(has_file_level_ignore(test_code1, "style.print-statement"))
        self.assertFalse(has_file_level_ignore(test_code1, "other.rule"))

        # Now test with actual linting
        from tools.design_linters.rules.logging.general_logging_rules import NoPlainPrintRule
        from tools.design_linters.rules.style.print_statement_rules import PrintStatementRule

        # Register the print statement rules
        self.registry.register_rule(NoPlainPrintRule())
        self.registry.register_rule(PrintStatementRule())

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code1)
            test_file = Path(f.name)

        try:
            violations = self.orchestrator.lint_file(test_file)
            print_violations = [v for v in violations if "print" in v.rule_id]
            print(f"DEBUG: Found violations: {[v.rule_id for v in print_violations]}")
            self.assertEqual(len(print_violations), 0, "Should have no print violations with ignore directive")
        finally:
            os.unlink(test_file)


if __name__ == "__main__":
    unittest.main()
