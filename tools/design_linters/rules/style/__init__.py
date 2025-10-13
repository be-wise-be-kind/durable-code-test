#!/usr/bin/env python3
"""
Purpose: Code style and formatting rules for the framework
Scope: Style-related linters (nesting moved to thailint)
Overview: This package contains rules for code style violations including
    print statements and file headers. Nesting depth detection has been
    moved to thailint for better multi-language support.
Dependencies: Framework interfaces and style analysis utilities
Exports: Individual style-related rules (nesting now in thailint)
Interfaces: All rules implement LintRule interface
Implementation: Rule-based architecture with proper separation of concerns
"""

from .file_header_rules import FileHeaderRule
from .print_statement_rules import ConsoleOutputRule, PrintStatementRule

__all__ = [
    # File header rules
    "FileHeaderRule",
    # Print statement rules
    "PrintStatementRule",
    "ConsoleOutputRule",
]
