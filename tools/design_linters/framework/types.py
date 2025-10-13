#!/usr/bin/env python3
"""
Purpose: Common types and data structures for the design linter framework
Scope: Shared data structures used across the framework components
Overview: This module contains common types, enums, and data structures that are
    used throughout the design linter framework. By placing these in a separate
    module, we avoid circular import issues between the base interfaces and
    the specific implementations. The module includes the core LintViolation
    class, severity levels, and other shared data structures that need to be
    accessible from both language-specific and language-agnostic components.
Dependencies: abc for abstract base classes, typing for type hints, enum for enums
Exports: LintViolation, Severity
Interfaces: Core data structures used throughout the framework
Implementation: Framework-wide shared types
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):  # thailint: ignore[srp]
    """Enumeration of violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def level(self) -> int:
        """Return numeric severity level for comparison (higher = more severe)."""
        levels = {"info": 0, "warning": 1, "error": 2}
        return levels.get(self.value, 0)

    def __ge__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.level >= other.level

    def __gt__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.level > other.level

    def __le__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.level <= other.level

    def __lt__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.level < other.level

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Create severity from string value."""
        for severity in cls:
            if severity.value == value:
                return severity
        raise ValueError(f"Invalid severity value: {value}")


@dataclass
class LintViolation:  # pylint: disable=too-many-instance-attributes
    """Represents a detected linting violation."""

    rule_id: str
    file_path: str
    line: int
    column: int
    severity: Severity
    message: str
    description: str
    suggestion: str | None = None
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            "rule_id": self.rule_id,
            "file": self.file_path,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "message": self.message,
            "description": self.description,
            "suggestion": self.suggestion,
            "context": self.context or {},
        }
