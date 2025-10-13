#!/usr/bin/env python3
"""
Purpose: Unit tests for the file header validation linting rule
Scope: Testing header field detection, validation, and quality checks across file types
Overview: This comprehensive test suite validates the FileHeaderRule implementation, ensuring
    it correctly identifies missing headers, validates required fields, checks content quality,
    and supports multiple file types. Tests cover Python, TypeScript, JavaScript, HTML, YAML,
    and Markdown files with various header formats. The suite verifies field parsing logic,
    multi-line field handling, Overview word count validation, and proper error reporting.
    It also tests edge cases like files without headers, headers with placeholder text, and
    files that should be skipped. The tests ensure the rule provides helpful suggestions and
    maintains consistent behavior across all supported file types.
Dependencies: pytest, ast, pathlib, design_linters framework
Exports: Test classes and fixtures for FileHeaderRule validation
Interfaces: pytest test cases following standard test patterns
Implementation: Uses pytest fixtures and parameterized tests for comprehensive coverage
"""

import ast
import tempfile
from pathlib import Path

import pytest
from tools.design_linters.framework.interfaces import LintContext, Severity
from tools.design_linters.rules.style.file_header_rules import FileHeaderRule


class TestFileHeaderRule:  # thailint: ignore[srp]
    """Test suite for FileHeaderRule."""

    @pytest.fixture
    def rule(self):
        """Create a FileHeaderRule instance."""
        return FileHeaderRule()

    @pytest.fixture
    def context(self):
        """Create a basic lint context."""
        ctx = LintContext()
        ctx.file_path = "test_file.py"  # Test files should have headers too
        ctx.file_content = ""
        ctx.ast_tree = ast.parse("")
        return ctx

    def test_python_file_with_complete_header(self, rule, context):
        """Test Python file with all required fields."""
        content = '''"""
Purpose: Test module for validating header compliance in Python files
Scope: Unit testing of header validation logic for Python modules
Overview: This test module provides comprehensive validation of the header checking
    logic for Python files. It ensures that all required fields are present and properly
    formatted, validates content quality requirements, and checks that multi-line fields
    are correctly parsed. The module tests both positive cases with complete headers
    and negative cases with missing or inadequate fields.
Dependencies: pytest framework, ast module for parsing, design_linters for rule implementation
Exports: TestFileHeaderRule class with comprehensive test cases
Interfaces: Standard pytest test methods for validation scenarios
Implementation: Uses fixtures and parameterized tests for thorough coverage
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have no violations for a complete header
        assert len(violations) == 0

    def test_python_file_missing_header(self, rule, context):
        """Test Python file with no header."""
        content = """def test_function():
    pass
"""
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have violations for missing header
        assert len(violations) > 0
        assert any("Missing file header" in v.message for v in violations)

    def test_python_file_missing_required_fields(self, rule, context):
        """Test Python file with incomplete header."""
        content = '''"""
This is a simple module description without proper fields.
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have violations for missing required fields
        assert len(violations) > 0
        assert any("Missing required header fields" in v.message for v in violations)

    def test_overview_word_count_validation(self, rule, context):
        """Test Overview field word count requirement."""
        content = '''"""
Purpose: Test module for validation
Scope: Testing header validation
Overview: Short overview text
Dependencies: pytest
Exports: Test class
Interfaces: Test methods
Implementation: Test patterns
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have violation for brief Overview
        assert any("Overview field too brief" in v.message for v in violations)

    def test_multiline_overview_parsing(self, rule, context):
        """Test that multi-line Overview fields are correctly parsed."""
        content = '''"""
Purpose: Test module for validating multi-line overview field parsing capability
Scope: Testing multi-line field parsing in Python docstring headers
Overview: This is a comprehensive overview that spans multiple lines to ensure
    the parser correctly handles continuation lines in header fields. It contains
    enough words to satisfy the minimum word count requirement. The parser should
    collect all these lines and count the total words correctly, not just the first
    line of the overview field.
Dependencies: pytest, ast module, design_linters framework
Exports: Test functions for validation
Interfaces: Standard test interfaces
Implementation: Comprehensive test coverage patterns
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have no Overview word count violation
        assert not any("Overview field too brief" in v.message for v in violations)

    def test_typescript_file_header(self, rule, context):
        """Test TypeScript file header validation."""
        content = """/**
 * Purpose: React component for displaying user profile information
 * Scope: User interface components for profile management
 * Overview: This component renders user profile data including avatar, name, bio,
 *     and social links. It handles loading states, error conditions, and provides
 *     edit functionality for authenticated users. The component uses React hooks for
 *     state management and integrates with the user API service for data fetching.
 * Dependencies: React, user API service, styling utilities
 * Exports: UserProfile component as default export
 * Interfaces: UserProfileProps interface with user data
 * Implementation: State management with React hooks
 */

export default function UserProfile() {
    return null;
}
"""
        context.file_path = "test_file.tsx"
        context.file_content = content
        # For TypeScript files, we still need an AST (even if minimal)
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should have no violations for complete TypeScript header
        assert len(violations) == 0

    def test_markdown_file_header(self, rule, context):
        """Test Markdown file header validation."""
        content = """# Documentation Title

**Purpose**: Comprehensive guide for using the application features
**Scope**: End-user documentation for all application modules

---

## Overview
Content starts here...
"""
        context.file_path = "test_file.md"
        context.file_content = content
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should have violation for missing Overview in header section
        assert any("Missing required Overview field" in v.message for v in violations)

    def test_skip_test_files(self):
        """Test that test files can be skipped when configured."""
        rule = FileHeaderRule(config={"skip_test_files": True})  # Changed from check_test_files
        context = LintContext()
        context.file_path = "test_something.py"
        context.file_content = "# No header needed for test files"
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should have no violations for test files when check_test_files is False
        assert len(violations) == 0

    def test_skip_init_files(self, rule, context):
        """Test that __init__.py files are skipped."""
        context.file_path = "__init__.py"
        context.file_content = "# Empty init file"

        violations = rule.check(context)

        # Should have no violations for __init__.py files
        assert len(violations) == 0

    def test_html_file_header(self, rule, context):
        """Test HTML file header validation."""
        content = """<!DOCTYPE html>
<!--
Purpose: Main application template for the web interface
Scope: HTML structure for single-page application
Dependencies: Bootstrap CSS, Vue.js framework
-->
<html lang="en">
<head>
    <title>Test</title>
</head>
<body>
</body>
</html>
"""
        context.file_path = "test_file.html"
        context.file_content = content
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should have violations for missing Overview and other fields
        assert len(violations) > 0

    def test_yaml_file_header(self, rule, context):
        """Test YAML file header validation."""
        content = """# Purpose: Configuration for CI/CD pipeline
# Scope: GitHub Actions workflow configuration
# Dependencies: Node.js, Python, Docker

name: CI Pipeline
on: [push, pull_request]
"""
        context.file_path = "test_file.yml"
        context.file_content = content
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should have violation for missing Overview
        assert any("Missing required Overview field" in v.message for v in violations)

    def test_placeholder_text_detection(self, rule, context):
        """Test detection of placeholder text in fields."""
        content = '''"""
Purpose: TODO
Scope: TBD
Overview: This is a placeholder overview that needs to be filled in later
Dependencies: TODO
Exports: TODO
Interfaces: TODO
Implementation: TODO
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have violations for placeholder text
        assert any("placeholder text" in v.message for v in violations)

    def test_field_parsing_with_colons(self, rule, context):
        """Test that fields with colons in values are parsed correctly."""
        content = '''"""
Purpose: Module for parsing URLs like http://example.com
Scope: URL validation and parsing utilities
Overview: This module provides comprehensive URL parsing functionality including
    validation of protocols like http:// and https://, extraction of components,
    and normalization of URLs. It handles various URL formats and edge cases to
    ensure reliable URL processing throughout the application.
Dependencies: urllib.parse, validators library
Exports: parse_url(), validate_url(), normalize_url() functions
Interfaces: URL parsing and validation functions
Implementation: Uses urllib.parse with custom validation logic
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should handle colons in field values correctly
        assert len(violations) == 0

    def test_recommended_field_warnings(self, rule, context):
        """Test that missing recommended fields generate warnings."""
        content = '''"""
Purpose: Basic module for testing recommended field warnings
Scope: Testing the detection of missing recommended fields
Overview: This module has all required fields but is missing the recommended
    Implementation field. The linter should generate a warning for this missing
    field when running in strict mode to encourage comprehensive documentation.
Dependencies: Standard library only
Exports: Basic test functions
Interfaces: Simple function interfaces
"""

def test_function():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)

        # Should have warning for missing Implementation field
        assert any("Missing recommended header field" in v.message for v in violations)
        assert any(v.severity == Severity.WARNING for v in violations)

    @pytest.mark.parametrize(
        "file_ext,header_start",
        [
            (".py", '"""'),
            (".ts", "/**"),
            (".tsx", "/**"),
            (".js", "/**"),
            (".jsx", "/**"),
        ],
    )
    def test_file_type_detection(self, rule, file_ext, header_start):
        """Test that different file types are detected correctly."""
        context = LintContext()
        context.file_path = f"test_file{file_ext}"
        context.file_content = f"{header_start}\nPurpose: Test\n"
        context.ast_tree = ast.parse("")

        violations = rule.check(context)

        # Should detect the file type and check for violations
        assert len(violations) > 0  # Missing required fields


class TestFileHeaderFieldParsing:  # thailint: ignore[srp]
    """Test the field parsing logic specifically."""

    @pytest.fixture
    def rule(self):
        """Create a FileHeaderRule instance."""
        return FileHeaderRule()

    def test_parse_python_header_fields(self, rule):
        """Test parsing of Python docstring header fields."""
        header_content = '''"""
Purpose: Test module for validation
Scope: Unit testing
Overview: This is a comprehensive overview spanning
    multiple lines with continuation
    and more text here.
Dependencies: pytest, unittest
Exports: TestClass, test_function
"""'''

        pattern = rule.FILE_CONFIGS[".py"]["field_pattern"]
        fields = rule._parse_header_fields(header_content, pattern)

        assert "purpose" in fields
        assert fields["purpose"] == "Test module for validation"
        assert "scope" in fields
        assert fields["scope"] == "Unit testing"
        assert "overview" in fields
        # Check that multi-line Overview is fully captured
        assert "multiple lines" in fields["overview"]
        assert "more text here" in fields["overview"]

    def test_parse_typescript_header_fields(self, rule):
        """Test parsing of TypeScript comment header fields."""
        header_content = """/**
 * Purpose: Component for user interface
 * Scope: UI components
 * Overview: A detailed overview that
 *     continues on multiple lines
 *     with proper indentation.
 * Dependencies: React, Redux
 */"""

        pattern = rule.FILE_CONFIGS[".ts"]["field_pattern"]
        fields = rule._parse_header_fields(header_content, pattern)

        assert "purpose" in fields
        assert "overview" in fields
        assert "multiple lines" in fields["overview"]
        assert "proper indentation" in fields["overview"]

    def test_parse_markdown_header_fields(self, rule):
        """Test parsing of Markdown header fields."""
        header_content = """# Title

**Purpose**: Documentation for the system
**Scope**: All system components

---"""

        pattern = rule.FILE_CONFIGS[".md"]["field_pattern"]
        fields = rule._parse_header_fields(header_content, pattern)

        assert "purpose" in fields
        assert fields["purpose"] == "Documentation for the system"
        assert "scope" in fields


class TestFileHeaderTemporalLanguage:  # thailint: ignore[srp]
    """Test suite for temporal language detection in file headers."""

    @pytest.fixture
    def rule(self):
        """Create a FileHeaderRule instance with temporal checking enabled."""
        return FileHeaderRule(config={"check_temporal_language": True})

    @pytest.fixture
    def context(self):
        """Create a basic lint context."""
        ctx = LintContext()
        ctx.file_path = "test_file.py"
        ctx.file_content = ""
        ctx.ast_tree = ast.parse("")
        return ctx

    def test_detects_date_stamps(self, rule, context):
        """Test detection of date stamps in headers."""
        content = '''"""
Purpose: Test module for date detection
Scope: Testing temporal patterns
Overview: This module was created on 2025-09-12 and provides validation logic
    for checking temporal patterns. It was last updated on 2025-09-16 to include
    new features for comprehensive temporal language detection.
Dependencies: pytest, ast
Exports: Test functions
Interfaces: Test interface
Implementation: Pattern matching
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        assert any("date stamp" in v.message for v in temporal_violations)

    def test_detects_creation_updated_fields(self, rule, context):
        """Test detection of Created/Updated fields."""
        content = '''"""
Purpose: Test module for temporal fields
Scope: Testing header fields
Created: 2025-09-12
Updated: 2025-09-16
Overview: This module provides comprehensive testing functionality for validating
    temporal language patterns in file headers across the codebase.
Dependencies: pytest, ast
Exports: Test functions
Interfaces: Standard test interface
Implementation: Uses regex patterns
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        assert any("creation timestamp" in v.message for v in temporal_violations)
        assert any("update timestamp" in v.message for v in temporal_violations)

    def test_detects_state_change_language(self, rule, context):
        """Test detection of state change references."""
        content = '''"""
Purpose: Test module that replaces the old implementation
Scope: Testing state changes
Overview: This module was migrated from the legacy system and now provides enhanced
    functionality. It was previously part of the old framework but has been refactored
    to work with the new architecture. Originally designed for a different purpose,
    it has been changed from a simple validator to a comprehensive checker.
Dependencies: pytest, ast
Exports: Test functions
Interfaces: New interface replacing old one
Implementation: Refactored from previous version
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        assert any("replacement reference" in v.message for v in temporal_violations)
        assert any("migration reference" in v.message for v in temporal_violations)
        assert any("previous state reference" in v.message for v in temporal_violations)

    def test_detects_temporal_qualifiers(self, rule, context):
        """Test detection of temporal qualifiers."""
        content = '''"""
Purpose: Module that currently handles validation
Scope: Testing temporal qualifiers
Overview: This module currently supports JSON validation and will soon add XML support.
    It temporarily uses a simplified algorithm for now, but the implementation is
    planned to be enhanced. Recently added features include better error messages.
    As of version 2.0, it now includes comprehensive validation logic.
Dependencies: pytest, ast
Exports: Test functions
Interfaces: Current interface
Implementation: Temporary simplified approach
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        assert any("current state qualifier" in v.message for v in temporal_violations)
        assert any("temporary" in v.message for v in temporal_violations)
        assert any("recent change qualifier" in v.message for v in temporal_violations)

    def test_detects_future_references(self, rule, context):
        """Test detection of future plan references."""
        content = '''"""
Purpose: Module for validation with upcoming features
Scope: Testing future references
Overview: This module provides basic validation that will be enhanced with additional
    features. Support for XML is planned for the next release. The API will be
    redesigned to be more intuitive. Future improvements include better performance
    and more comprehensive error messages that are to be implemented.
Dependencies: pytest, ast
Exports: Test functions
Interfaces: Interface to be redesigned
Implementation: Basic implementation, enhancements planned
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        assert any("future" in v.message.lower() for v in temporal_violations)
        assert any("planned" in v.message for v in temporal_violations)

    def test_clean_header_no_temporal_violations(self, rule, context):
        """Test that clean headers without temporal language pass."""
        content = '''"""
Purpose: Validates file headers according to project standards
Scope: All source code files in the project
Overview: This module provides comprehensive validation of file headers to ensure
    they meet project documentation standards. It checks for required fields,
    validates content quality, and ensures headers provide sufficient information
    for developers to understand file purposes without reading implementation details.
Dependencies: pytest framework, ast module, design_linters framework
Exports: FileHeaderRule class implementing validation logic
Interfaces: ASTLintRule interface for integration with linting framework
Implementation: Pattern-based field extraction with file-type specific validation
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        # Should have no temporal language violations
        assert len(temporal_violations) == 0

    def test_typescript_file_with_temporal_language(self, rule, context):
        """Test TypeScript file with temporal language."""
        content = '''/**
 * Purpose: Component that replaces the old UI element
 * Scope: UI components
 * Created: 2025-09-12
 * Updated: 2025-09-16
 * Overview: This new implementation provides enhanced functionality compared to
 *     the previous version. It was recently refactored to improve performance.
 * Dependencies: React, Redux
 * Exports: NewComponent
 * Props: Enhanced props interface
 * State: Improved state management
 */
export const Component = () => {};
'''
        context.file_path = "test_file.tsx"
        context.file_content = content
        # For non-Python files, we still use ast.parse("") as placeholder
        context.ast_tree = ast.parse("")

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0
        # Should detect multiple temporal patterns
        assert any("creation timestamp" in v.message for v in temporal_violations)
        assert any("update timestamp" in v.message for v in temporal_violations)
        assert any("replacement reference" in v.message for v in temporal_violations)

    def test_temporal_checking_can_be_disabled(self):
        """Test that temporal checking can be disabled via config."""
        rule_disabled = FileHeaderRule(config={"check_temporal_language": False})

        content = '''"""
Purpose: Test module
Scope: Testing
Created: 2025-09-12
Updated: 2025-09-16
Overview: This module was recently updated to provide better functionality than
    the previous version. It replaces the old implementation completely.
Dependencies: pytest
Exports: Functions
Interfaces: Test interface
Implementation: New approach replacing old one
"""
def test():
    pass
'''
        ctx = LintContext()
        ctx.file_path = "test_file.py"
        ctx.file_content = content
        ctx.ast_tree = ast.parse(content)

        violations = rule_disabled.check(ctx)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        # Should have no temporal violations when disabled
        assert len(temporal_violations) == 0

    def test_temporal_suggestions_are_helpful(self, rule, context):
        """Test that temporal language violations provide helpful suggestions."""
        content = '''"""
Purpose: Module created on 2025-09-12
Scope: Testing suggestions
Overview: This module currently provides validation and will be enhanced with
    additional features in the future. It was previously part of another system.
Dependencies: pytest
Exports: Functions
Interfaces: Current interface
Implementation: Temporary approach for now
"""
def test():
    pass
'''
        context.file_content = content
        context.ast_tree = ast.parse(content)

        violations = rule.check(context)
        temporal_violations = [v for v in violations if "Temporal language" in v.message]

        assert len(temporal_violations) > 0

        # Check that suggestions are provided
        for violation in temporal_violations:
            assert violation.suggestion is not None
            assert len(violation.suggestion) > 0
            # Suggestions should mention git or issue tracking
            assert any(keyword in violation.suggestion.lower()
                      for keyword in ["git", "remove", "describe", "track", "issue"])
