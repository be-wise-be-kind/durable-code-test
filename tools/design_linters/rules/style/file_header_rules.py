#!/usr/bin/env python3
"""
Purpose: File header validation linting rule for the design linter framework
Scope: Style category rule implementation for enforcing file header standards
Overview: This module validates that all source files contain comprehensive documentation headers
    according to project standards, ensuring consistent documentation across the codebase. It checks
    for required fields including Purpose, Scope, and Overview in all files, plus additional fields
    like Dependencies, Exports, and Interfaces for code files. The rule supports multiple file types
    with format-specific header patterns for Python, TypeScript, JavaScript, HTML, YAML, and Markdown.
    It validates not just the presence of fields but also their content quality, ensuring descriptions
    are substantive rather than placeholders. The module provides file-type specific templates for
    missing headers and helpful suggestions for improving incomplete headers. This ensures every file
    in the project is self-documenting, helping developers understand file purposes without examining
    implementation details, which is especially valuable for onboarding and maintenance.
Dependencies: Framework interfaces, pathlib for file operations, re for pattern matching
Exports: FileHeaderRule implementation
Interfaces: Implements ASTLintRule interface from framework
Implementation: Pattern-based header extraction with file-type specific validation
"""

import re
from pathlib import Path
from typing import Any

from loguru import logger
from tools.design_linters.framework.interfaces import (
    ASTLintRule,
    LintContext,
    LintViolation,
    Severity,
)


class HeaderFieldValidator:
    """Handles validation of header field content and quality."""

    # Constants for validation
    DEFAULT_MIN_OVERVIEW_WORDS = 20
    DEFAULT_MIN_OVERVIEW_CHARS = 100

    PLACEHOLDER_PATTERNS = [
        r"^TODO",
        r"^TBD",
        r"^FIXME",
        r"^XXX",
        r"^\.\.\.",
        r"^<.*>$",
        r"^\[.*\]$",
        r"^your .* here",
        r"^describe .*",
        r"^brief .*",
        r"^placeholder",
        r"^undefined",
        r"^unknown",
        r"^n/a",
        r"^not applicable",
    ]

    def validate_field_content(self, fields: dict[str, str]) -> list[dict[str, str]]:
        """Validate that field content is not placeholder text."""
        issues = []
        for field_name, content in fields.items():
            content_lower = content.lower().strip()
            for pattern in self.PLACEHOLDER_PATTERNS:
                if re.match(pattern, content_lower, re.IGNORECASE):
                    issues.append(
                        {
                            "field": field_name.title(),
                            "issue": f"contains placeholder text: '{content}'",
                            "suggestion": f"Provide a meaningful {field_name.lower()} description",
                        }
                    )
                    break
        return issues

    def validate_overview_content(
        self, overview: str, min_words: int | None = None, min_chars: int | None = None
    ) -> tuple[bool, str]:
        """Validate overview field meets quality requirements."""
        # Use defaults if not provided
        if min_words is None:
            min_words = self.DEFAULT_MIN_OVERVIEW_WORDS
        if min_chars is None:
            min_chars = self.DEFAULT_MIN_OVERVIEW_CHARS

        words = overview.split()
        word_count = len(words)
        char_count = len(overview)

        if word_count < min_words or char_count < min_chars:
            return (
                False,
                f"Overview field too brief ({word_count} words, {char_count} chars). "
                f"Minimum: {min_words} words, {min_chars} chars. "
                "Provide comprehensive file documentation.",
            )
        return (True, "")


class TemporalLanguageChecker:
    """Handles detection and validation of temporal language in headers."""

    TEMPORAL_PATTERNS = {
        "date_stamps": r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
        "created_updated": r"\b(?:created|updated|modified|changed)\s*(?:on|at|:)?\s*\d",
        "replacement_reference": r"\b(?:replaces?|replacing)\s+(?:the\s+)?old\b",
        "migration_reference": r"\b(?:migrated|migration)\s+(?:from|to)\b",
        "previous_state_reference": r"\b(?:previously|was previously|formerly|used to be|changed from)\b",
        "state_changes": r"\b(?:was|were|had been|has been|have been|will be|would be)\b",
        "recent_change_qualifier": r"\b(?:recently|just)\s+(?:added|updated|changed|refactored)\b",
        "current_state_qualifier": r"\b(?:currently|now)\s+(?:supports?|handles?|provides?|includes?)\b",
        "temporal_qualifiers": r"\b(?:recently|currently|now|today|yesterday|tomorrow|soon|later|temporary|temporarily|for now|as of)\b",
        "future_references": r"\b(?:will|shall|going to|plan to|intend to|expect to|planned|upcoming|to be|will be)\b",
    }

    def check_temporal_language_patterns(self, header_content: str) -> list[dict[str, str]]:
        """Check header for temporal language patterns."""
        temporal_issues = []
        for pattern_type, pattern in self.TEMPORAL_PATTERNS.items():
            matches = re.finditer(pattern, header_content, re.IGNORECASE)
            for match in matches:
                # Use match.group(0) to get the full matched text
                temporal_issues.append({"type": pattern_type, "text": match.group(0)})
        return temporal_issues

    def get_temporal_suggestion(self, pattern_type: str, matched_text: str) -> str:
        """Get suggestion for fixing temporal language."""
        suggestions = {
            "date_stamps": (
                f"Remove date '{matched_text}' from header. Dates belong in version control history, not documentation."
            ),
            "created_updated": (
                f"Remove temporal metadata '{matched_text}'. Creation/modification info belongs in version control."
            ),
            "replacement_reference": (
                f"Remove replacement reference '{matched_text}'. "
                "Describe what the module does, not what it replaced. Historical info belongs in git."
            ),
            "migration_reference": (
                f"Remove migration reference '{matched_text}'. "
                "Describe current functionality, not migration history. Track migrations in git or issues."
            ),
            "previous_state_reference": (
                f"Remove previous state reference '{matched_text}'. "
                "Documentation should describe current behavior, not past states. Use git history for changes."
            ),
            "state_changes": (
                f"Replace past/future tense '{matched_text}' with present tense. "
                "Documentation should describe current state."
            ),
            "temporal_qualifiers": (
                f"Remove temporal qualifier '{matched_text}'. "
                "Documentation should be timeless and describe current behavior."
            ),
            "recent_change_qualifier": (
                f"Remove recent change qualifier '{matched_text}'. "
                "Describe functionality without temporal context. Track changes in git history."
            ),
            "current_state_qualifier": (
                f"Remove current state qualifier '{matched_text}'. "
                "Documentation should be timeless. If it's in the code, it's current."
            ),
            "future_references": (
                f"Remove future reference '{matched_text}'. "
                "Document what IS, not what WILL BE. Future plans belong in issues/roadmap."
            ),
        }
        return suggestions.get(pattern_type, f"Remove temporal language '{matched_text}' for timeless documentation.")


class HeaderTemplateProvider:
    """Provides header templates for different file types."""

    TEMPLATES = {
        ".py": (
            '"""\n'
            "Purpose: [Single line describing why this file exists]\n"
            "Scope: [What this file covers/handles]\n"
            "Overview: [Comprehensive 3-5 sentence description of what this file does,\n"
            "    how it fits into the larger system, and any important behaviors or patterns\n"
            "    it implements. This helps developers understand the file without reading code.]\n"
            "Dependencies: [Key imports and external dependencies]\n"
            "Exports: [Main classes/functions/constants exported]\n"
            "Interfaces: [Key interfaces this implements or provides]\n"
            "Implementation: [High-level approach or algorithm used]\n"
            '"""'
        ),
        ".ts": (
            "/**\n"
            " * Purpose: [Single line describing why this file exists]\n"
            " * Scope: [What this file covers/handles]\n"
            " * Overview: [Comprehensive 3-5 sentence description]\n"
            " * Dependencies: [Key imports and external dependencies]\n"
            " * Exports: [Main exports from this module]\n"
            " * Interfaces: [Key interfaces defined or implemented]\n"
            " * Implementation: [High-level approach]\n"
            " */"
        ),
        ".tsx": (
            "/**\n"
            " * Purpose: [React component purpose]\n"
            " * Scope: [Component responsibility/domain]\n"
            " * Overview: [Component behavior and usage]\n"
            " * Props: [Key props accepted]\n"
            " * State: [State management approach]\n"
            " * Dependencies: [Key imports]\n"
            " * Implementation: [Rendering approach]\n"
            " */"
        ),
        ".js": (
            "/**\n"
            " * Purpose: [Why this file exists]\n"
            " * Scope: [What this file handles]\n"
            " * Overview: [Detailed description]\n"
            " * Dependencies: [Key imports]\n"
            " * Exports: [Module exports]\n"
            " * Implementation: [Approach used]\n"
            " */"
        ),
        ".jsx": (
            "/**\n"
            " * Purpose: [React component purpose]\n"
            " * Scope: [Component domain]\n"
            " * Overview: [Component description]\n"
            " * Props: [Component props]\n"
            " * State: [State management]\n"
            " * Dependencies: [Key imports]\n"
            " */"
        ),
        ".css": (
            "/**\n"
            " * Purpose: [Styling purpose]\n"
            " * Scope: [What components/pages these styles apply to]\n"
            " * Overview: [Design system usage and patterns]\n"
            " * Dependencies: [CSS imports/variables used]\n"
            " */"
        ),
        ".sh": (
            "#!/usr/bin/env bash\n"
            "# Purpose: [Script purpose]\n"
            "# Scope: [What this script handles]\n"
            "# Overview: [Detailed description]\n"
            "# Dependencies: [Required tools/scripts]\n"
            "# Usage: [How to run this script]"
        ),
        ".md": (
            "<!-- Purpose: [Document purpose] -->\n"
            "<!-- Scope: [What this covers] -->\n"
            "<!-- Overview: [Detailed description] -->"
        ),
        ".html": (
            "<!-- Purpose: [Page/component purpose] -->\n"
            "<!-- Scope: [What this handles] -->\n"
            "<!-- Overview: [Detailed description] -->"
        ),
        ".yaml": ("# Purpose: [Config purpose]\n# Scope: [What this configures]\n# Overview: [Detailed description]"),
        ".yml": ("# Purpose: [Config purpose]\n# Scope: [What this configures]\n# Overview: [Detailed description]"),
    }

    def get_template(self, file_ext: str) -> str:
        """Get the appropriate header template for a file type."""
        return self.TEMPLATES.get(file_ext, self.TEMPLATES[".py"])


class HeaderParser:
    """Handles parsing of file headers from different file types."""

    def __init__(self):
        """Initialize the parser."""
        self.fields = {}
        self.current_field = None
        self.current_content = []
        self.field_pattern = None

    def parse_header_fields(self, header_content: str, field_pattern: re.Pattern) -> dict[str, str]:
        """Parse header content to extract field values."""
        # Reset state for new parse
        self.fields = {}
        self.current_field = None
        self.current_content = []
        self.field_pattern = field_pattern

        lines = header_content.split("\n")
        for line in lines:
            cleaned_line = self._clean_header_line(line)
            if not cleaned_line:
                continue

            # Process the cleaned line
            self._process_header_line(cleaned_line, line)

        # Save last field if exists
        if self.current_field:
            self.fields[self.current_field] = " ".join(self.current_content).strip()

        return self.fields

    def _process_header_line(self, cleaned_line: str, original_line: str) -> None:
        """Process a single header line and update internal state."""
        is_continuation = self._is_continuation_line(original_line)

        # If it's a continuation line for the current field, add to content
        if self._should_add_to_field(cleaned_line, original_line, is_continuation):
            if self.current_field:
                self.current_content.append(cleaned_line)
            return

        # Try to match as a new field
        match = self.field_pattern.match(cleaned_line)
        if not match:
            return

        # Save previous field if it exists
        if self.current_field:
            self.fields[self.current_field] = " ".join(self.current_content).strip()

        # Start new field
        self.current_field = match.group(1).lower()
        content = match.group(2).strip() if match.group(2) else ""
        self.current_content = [content] if content else []

    def _is_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation of previous field."""
        return line.strip() and not line.lstrip().startswith(("*", "#", "//"))

    def _clean_header_line(self, line: str) -> str:
        """Remove comment markers from header line."""
        line = line.strip()
        # Don't strip ** from markdown fields
        if line.startswith("**"):
            return line
        # Strip single comment markers
        for prefix in ["*", "#", "//"]:
            if line.startswith(prefix):
                line = line[len(prefix) :].strip()
        return line

    def _should_add_to_field(
        self,
        cleaned_line: str,
        original_line: str,
        is_continuation: bool,  # pylint: disable=unused-argument
    ) -> bool:
        """Determine if line should be added to current field."""
        # If the cleaned line matches the field pattern, it's a new field, not a continuation
        # Otherwise, it's a continuation line
        return not (self.field_pattern and self.field_pattern.match(cleaned_line))


class FileSkipChecker:
    """Handles logic for determining which files to skip."""

    SKIP_PATTERNS = [
        r"__pycache__",
        r"\.git",
        r"\.pytest_cache",
        r"node_modules",
        r"dist",
        r"build",
        r"coverage",
        r"\.egg-info",
        r"migrations",
        r"\.min\.",
        r"vendor",
        r"third_party",
    ]

    def should_skip_file(self, file_path: Path, skip_test_files: bool = False) -> bool:
        """Check if file should be skipped from header checking."""
        path_str = str(file_path).replace("\\", "/")

        # Skip __init__.py files
        if file_path.name == "__init__.py":
            return True

        # Skip test files if configured
        if skip_test_files and self._is_test_file(path_str):
            return True

        # Check skip patterns
        return self._matches_skip_patterns(path_str)

    def _matches_skip_patterns(self, path_str: str) -> bool:
        """Check if path matches any skip patterns."""
        return any(self._matches_pattern(pattern, path_str) for pattern in self.SKIP_PATTERNS)

    def _matches_pattern(self, pattern: str, path_str: str) -> bool:
        """Check if a specific pattern matches the path."""
        return bool(re.search(pattern, path_str))

    def _is_test_file(self, path_str: str) -> bool:
        """Check if file is a test file."""
        test_patterns = [r"test_.*\.py$", r".*_test\.py$", r"tests?/", r"\.test\.", r"\.spec\."]
        return any(re.search(pattern, path_str) for pattern in test_patterns)


class HeaderConfigConstants:
    """Constants for header configuration."""

    REQUIRED_FIELDS = {"purpose", "scope"}
    OVERVIEW_FIELD = "overview"
    CODE_REQUIRED_FIELDS = {"dependencies", "exports"}
    CODE_RECOMMENDED_FIELDS = {"interfaces", "implementation"}
    CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cpp", ".c", ".cs", ".go", ".rs"}
    SUPPORTED_EXTENSIONS = CODE_EXTENSIONS | {".html", ".css", ".scss", ".yaml", ".yml", ".sh", ".md"}


class HeaderExtractor:
    """Extracts header content from files."""

    HEADER_PATTERNS = {
        ".py": (r'^"""', r'"""'),
        ".ts": (r"^/\*\*", r"\*/"),
        ".tsx": (r"^/\*\*", r"\*/"),
        ".js": (r"^/\*\*", r"\*/"),
        ".jsx": (r"^/\*\*", r"\*/"),
        ".md": (r"^<!--", r"-->"),
        ".html": (r"^<!--", r"-->"),
        ".yaml": (r"^#", None),
        ".yml": (r"^#", None),
        ".sh": (r"^#", None),
        ".css": (r"^/\*\*", r"\*/"),
    }

    def extract_header_content(self, file_content: str, file_ext: str) -> str | None:
        """Extract header content from file."""
        header_pattern = self.HEADER_PATTERNS.get(file_ext)
        if not header_pattern:
            return None

        # For markdown files, extract metadata section before first ---
        if file_ext == ".md":
            lines = file_content.split("\n")
            header_lines = []
            in_header = False
            for line in lines:
                # Start collecting after first line (title)
                if line.startswith("#"):
                    in_header = True
                    continue
                # Stop at separator
                if line.strip() == "---":
                    break
                if in_header:
                    header_lines.append(line)
            return "\n".join(header_lines)

        start_pattern, end_pattern = header_pattern
        header_match = re.search(start_pattern, file_content, re.MULTILINE)
        if not header_match:
            return None

        header_start = header_match.end()
        if end_pattern:
            end_match = re.search(end_pattern, file_content[header_start:], re.MULTILINE)
            return file_content[header_start : header_start + end_match.start()] if end_match else ""
        else:
            # For single-line comment styles, extract until first non-comment line
            lines = file_content[header_start:].split("\n")
            header_lines = []
            for line in lines:
                if line.strip() and not line.strip().startswith("#"):
                    break
                header_lines.append(line)
            return "\n".join(header_lines)


class HeaderViolationChecker:
    """Helper class that handles violation checking for file headers."""

    def __init__(self, field_validator, temporal_checker, config, field_pattern):
        """Initialize with dependencies."""
        self.field_validator = field_validator
        self.temporal_checker = temporal_checker
        self.config = config
        self.field_pattern = field_pattern

    def check_required_fields(
        self, context: LintContext, node: Any, fields: dict[str, str], rule_id: str, severity: Severity
    ) -> list[LintViolation]:
        """Check for missing required fields."""
        violations = []
        missing_fields = self.config.REQUIRED_FIELDS - fields.keys()
        if self.config.OVERVIEW_FIELD not in fields:
            missing_fields.add(self.config.OVERVIEW_FIELD)

        if missing_fields:
            violations.append(
                LintViolation(
                    rule_id=rule_id,
                    file_path=context.file_path,
                    line=1,
                    column=0,
                    severity=severity,
                    message=(f"Missing required header fields: {self._format_missing_fields(missing_fields)}"),
                    description="File headers should include all required documentation fields",
                    suggestion="Add missing fields to the header documentation",
                )
            )
        return violations

    def check_overview_field(
        self, context: LintContext, node: Any, fields: dict[str, str], rule_id: str, min_words: int
    ) -> list[LintViolation]:
        """Check overview field quality."""
        violations = []
        if self.config.OVERVIEW_FIELD in fields:
            overview = fields[self.config.OVERVIEW_FIELD]
            is_valid, message = self.field_validator.validate_overview_content(overview, min_words)
            if not is_valid:
                violations.append(
                    LintViolation(
                        rule_id=rule_id,
                        file_path=context.file_path,
                        line=1,
                        column=0,
                        severity=Severity.WARNING,
                        message=message,
                        description="Overview field should provide comprehensive documentation",
                        suggestion="Expand the Overview field with comprehensive documentation",
                    )
                )
        return violations

    def check_code_specific_fields(
        self,
        context: LintContext,
        node: Any,
        fields: dict[str, str],
        file_ext: str,
        rule_id: str,
        severity: Severity,
        strict_mode: bool,
    ) -> list[LintViolation]:
        """Check code-specific required and recommended fields."""
        violations = []

        # Check required code fields
        missing_required = self.config.CODE_REQUIRED_FIELDS - fields.keys()
        if missing_required:
            violations.append(
                LintViolation(
                    rule_id=rule_id,
                    file_path=context.file_path,
                    line=1,
                    column=0,
                    severity=severity,
                    message=f"Code file missing required fields: {self._format_missing_fields(missing_required)}",
                    description="Code files require specific documentation fields",
                    suggestion="Add missing code documentation fields",
                )
            )

        # Check recommended fields (as warnings)
        missing_recommended = self.config.CODE_RECOMMENDED_FIELDS - fields.keys()
        if missing_recommended and strict_mode:
            violations.append(
                LintViolation(
                    rule_id=rule_id,
                    file_path=context.file_path,
                    line=1,
                    column=0,
                    severity=Severity.WARNING,
                    message=f"Missing recommended header field: {self._format_missing_fields(missing_recommended)}",
                    description="Recommended documentation fields improve code maintainability",
                    suggestion="Consider adding recommended documentation fields",
                )
            )

        return violations

    def check_field_content_quality(
        self, context: LintContext, node: Any, fields: dict[str, str], rule_id: str
    ) -> list[LintViolation]:
        """Check quality of field content."""
        violations = []
        issues = self.field_validator.validate_field_content(fields)

        for issue in issues:
            violations.append(
                LintViolation(
                    rule_id=rule_id,
                    file_path=context.file_path,
                    line=1,
                    column=0,
                    severity=Severity.WARNING,
                    message=f"Header field '{issue['field']}' {issue['issue']}",
                    description="Header field content should meet quality standards",
                    suggestion=issue["suggestion"],
                )
            )

        return violations

    def check_temporal_language(
        self, context: LintContext, node: Any, header_content: str, rule_id: str
    ) -> list[LintViolation]:
        """Check for temporal language in headers."""
        violations = []
        temporal_issues = self.temporal_checker.check_temporal_language_patterns(header_content)

        for issue in temporal_issues:
            suggestion = self.temporal_checker.get_temporal_suggestion(issue["type"], issue["text"])

            # Determine pattern description based on type and matched text
            pattern_desc = self._get_pattern_description(issue["type"], issue["text"])

            violations.append(
                LintViolation(
                    rule_id=rule_id,
                    file_path=context.file_path,
                    line=1,
                    column=0,
                    severity=Severity.WARNING,
                    message=f"Header contains temporal language ({pattern_desc}): '{issue['text']}'",
                    description="Temporal language makes documentation time-dependent",
                    suggestion=suggestion,
                )
            )

        return violations

    def _get_pattern_description(self, pattern_type: str, matched_text: str) -> str:
        """Get descriptive name for pattern type based on matched text."""
        if pattern_type == "created_updated":
            return self._get_created_updated_description(matched_text)

        # Map other pattern types to descriptive names
        pattern_descriptions = {
            "date_stamps": "date stamp",
            "replacement_reference": "replacement reference",
            "migration_reference": "migration reference",
            "previous_state_reference": "previous state reference",
            "state_changes": "state change language",
            "temporal_qualifiers": "temporal qualifier",
            "recent_change_qualifier": "recent change qualifier",
            "current_state_qualifier": "current state qualifier",
            "future_references": "future reference",
        }
        return pattern_descriptions.get(pattern_type, "temporal language")

    def _get_created_updated_description(self, matched_text: str) -> str:
        """Get specific description for created/updated pattern types.

        Args:
            matched_text: The matched text to analyze

        Returns:
            Specific timestamp description
        """
        text_lower = matched_text.lower()
        if "created" in text_lower or "creation" in text_lower:
            return "creation timestamp"
        if "updated" in text_lower or "modified" in text_lower:
            return "update timestamp"
        if "changed" in text_lower:
            return "change timestamp"
        return "creation/update timestamp"

    def _format_missing_fields(self, fields: set[str]) -> str:
        """Format missing fields for display."""
        return ", ".join(sorted(f.title() for f in fields))


class FileHeaderRule(ASTLintRule):
    """Validate file headers according to project standards."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the rule with configuration."""
        super().__init__()
        self.config = config or {}
        self.strict_mode = self.config.get("strict_mode", True)
        self.min_overview_words = self.config.get("min_overview_words", HeaderFieldValidator.DEFAULT_MIN_OVERVIEW_WORDS)
        self.check_all_files = self.config.get("check_all_files", True)
        self.skip_test_files = self.config.get("skip_test_files", False)
        self.check_temporal = self.config.get("check_temporal_language", True)

        # Pre-compile regex patterns for different file types
        self._field_pattern = re.compile(r"^(\w+):\s*(.*)$")
        self._markdown_field_pattern = re.compile(r"^\*\*(\w+)\*\*:\s*(.*)$")

        # File-specific configurations
        self.FILE_CONFIGS = {
            ".py": {"field_pattern": self._field_pattern},
            ".ts": {"field_pattern": self._field_pattern},
            ".tsx": {"field_pattern": self._field_pattern},
            ".js": {"field_pattern": self._field_pattern},
            ".jsx": {"field_pattern": self._field_pattern},
            ".md": {"field_pattern": self._markdown_field_pattern},
            ".html": {"field_pattern": self._field_pattern},
            ".yaml": {"field_pattern": self._field_pattern},
            ".yml": {"field_pattern": self._field_pattern},
        }

        # Initialize helper classes
        self._field_validator = HeaderFieldValidator()
        self._temporal_checker = TemporalLanguageChecker()
        self._template_provider = HeaderTemplateProvider()
        self._header_parser = HeaderParser()
        self._skip_checker = FileSkipChecker()
        self._header_extractor = HeaderExtractor()
        self._config = HeaderConfigConstants()
        self._violation_checker = HeaderViolationChecker(
            self._field_validator, self._temporal_checker, self._config, self._field_pattern
        )

    @property
    def rule_id(self) -> str:
        """Return the unique identifier for this rule."""
        return "style.file-header"

    @property
    def rule_name(self) -> str:
        """Return the human-readable name for this rule."""
        return "File Header Documentation"

    @property
    def description(self) -> str:
        """Return the description of what this rule checks."""
        return "Ensure all files have comprehensive documentation headers"

    @property
    def severity(self) -> Severity:
        """Return the severity level of violations from this rule."""
        return Severity.ERROR if self.strict_mode else Severity.WARNING

    @property
    def categories(self) -> set[str]:
        """Return the categories this rule belongs to."""
        return {"style", "documentation"}

    def should_check_node(self, node: Any, context: LintContext) -> bool:
        """Check if node should be validated (Module nodes only)."""
        import ast

        return isinstance(node, ast.Module)

    def check_node(self, node: Any, context: LintContext) -> list[LintViolation]:
        """Check if file has proper header documentation."""
        file_path = Path(context.file_path)

        # Skip files that should not be checked
        if self._skip_checker.should_skip_file(file_path, self.skip_test_files):
            return []

        # Check if file type is supported
        file_ext = file_path.suffix.lower()
        if not self._is_supported_file_type(file_ext):
            return []

        # Get and validate header content
        header_content, file_content = self._extract_and_validate_header(file_path, context, file_ext)
        if header_content is None:
            return [self._create_missing_header_violation(context, node, file_ext)]

        # Get the appropriate field pattern for this file type
        field_pattern = self.FILE_CONFIGS.get(file_ext, {}).get("field_pattern", self._field_pattern)

        # Parse header fields and check violations
        fields = self._header_parser.parse_header_fields(header_content, field_pattern)
        return self._collect_header_violations(context, node, fields, file_ext, header_content)

    def _extract_and_validate_header(
        self, file_path: Path, context: LintContext, file_ext: str
    ) -> tuple[str | None, str | None]:
        """Extract header content from file."""
        file_content = self._get_file_content(file_path, context)
        if file_content is None:
            return None, None

        header_content = self._header_extractor.extract_header_content(file_content, file_ext)
        return header_content, file_content

    def _collect_header_violations(
        self, context: LintContext, node: Any, fields: dict[str, str], file_ext: str, header_content: str
    ) -> list[LintViolation]:
        """Collect all header-related violations."""
        violations = []

        # Check required fields
        violations.extend(
            self._violation_checker.check_required_fields(context, node, fields, self.rule_id, self.severity)
        )

        # Check overview field
        violations.extend(
            self._violation_checker.check_overview_field(context, node, fields, self.rule_id, self.min_overview_words)
        )

        # Check code-specific fields
        if file_ext in self._config.CODE_EXTENSIONS:
            violations.extend(
                self._violation_checker.check_code_specific_fields(
                    context, node, fields, file_ext, self.rule_id, self.severity, self.strict_mode
                )
            )

        # Check field content quality
        violations.extend(self._violation_checker.check_field_content_quality(context, node, fields, self.rule_id))

        # Check for temporal language if enabled
        if self.check_temporal:
            violations.extend(
                self._violation_checker.check_temporal_language(context, node, header_content, self.rule_id)
            )

        return violations

    def _is_supported_file_type(self, file_ext: str) -> bool:
        """Check if file extension is supported."""
        return file_ext in self._config.SUPPORTED_EXTENSIONS

    def _get_file_content(self, file_path: Path, context: LintContext) -> str | None:
        """Get file content from context or read from disk."""
        if hasattr(context, "file_content") and context.file_content:
            return context.file_content
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug("Could not read file", file_path=str(file_path), error=str(e))
            return None

    def _parse_header_fields(self, header_content: str, field_pattern: re.Pattern) -> dict[str, str]:
        """Parse header content to extract field values.

        This is a public method exposed for testing purposes.
        """
        return self._header_parser.parse_header_fields(header_content, field_pattern)

    def _create_missing_header_violation(self, context: LintContext, node: Any, file_ext: str) -> LintViolation:
        """Create violation for missing header."""
        template = self._template_provider.get_template(file_ext)
        return LintViolation(
            rule_id=self.rule_id,
            file_path=context.file_path,
            line=1,
            column=0,
            severity=self.severity,
            message="Missing file header",
            description="All files should have proper documentation headers with required fields",
            suggestion=f"Add header at the beginning of the file:\n{template}",
        )
