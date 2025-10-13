# How to Create a Custom Linter Rule

**Purpose**: Comprehensive guide for creating custom linting rules for the pluggable design linter framework
**Scope**: Rule implementation, testing, configuration, and integration
**Created**: 2025-01-17
**Author**: Development Team
**Version**: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Rule Categories](#rule-categories)
5. [Testing Your Rule](#testing-your-rule)
6. [Configuration](#configuration)
7. [Integration](#integration)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

## Overview

Custom linters in this framework are Python classes that implement the `ASTLintRule` or `FileBasedLintRule` interfaces. Rules are automatically discovered and registered when placed in the correct directory structure.

### Framework Architecture

```
tools/design_linters/
├── framework/              # Core framework (DO NOT MODIFY)
│   ├── interfaces.py       # Base classes and interfaces
│   ├── analyzer.py         # Analysis engine
│   └── rule_registry.py    # Rule discovery system
├── rules/                  # YOUR CUSTOM RULES GO HERE
│   ├── literals/           # Literal-related rules
│   ├── logging/            # Logging rules
│   ├── solid/              # SOLID principle rules
│   └── style/              # Code style rules
└── cli.py                  # Command-line interface
```

## Quick Start

### 1. Create Your Rule File

```bash
# Choose appropriate category directory
touch tools/design_linters/rules/{category}/{rule_name}_rules.py
```

### 2. Use the Template

Copy from `.ai/templates/linting-rule.py.template` and replace placeholders:

```python
#!/usr/bin/env python3
"""
Purpose: Your rule's purpose
Scope: Rule scope description
Overview: Detailed overview
"""

import ast
from typing import Any
from pathlib import Path

from design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity


class YourRuleNameRule(ASTLintRule):
    """Your rule description."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize rule with configuration."""
        super().__init__()
        self.config = config or {}

    @property
    def rule_id(self) -> str:
        return "category.rule-name"

    @property
    def rule_name(self) -> str:
        return "Human Readable Name"

    @property
    def description(self) -> str:
        return "What this rule checks for"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"category", "subcategory"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        """Determine if this node should be checked."""
        # Return True for nodes you want to analyze
        return isinstance(node, ast.YourTargetNodeType)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        """Check node for violations."""
        violations = []

        # Your rule logic here
        if self._violates_rule(node):
            violations.append(self._create_violation(node, context))

        return violations

    def _violates_rule(self, node: ast.AST) -> bool:
        """Check if node violates the rule."""
        # Implement your violation logic
        return False

    def _create_violation(self, node: ast.AST, context: LintContext) -> LintViolation:
        """Create violation object."""
        return self.create_violation(
            context=context,
            node=node,
            message=f"Specific violation message",
            description=self.description,
            suggestion="How to fix this issue"
        )
```

### 3. Create Unit Tests

```bash
touch test/unit_test/tools/design_linters/test_{rule_name}_rules.py
```

### 4. Run Your Rule

```bash
# Run via make
make lint-custom

# Run directly
python tools/design_linters/cli.py --rules category.rule-name src/
```

## Step-by-Step Guide

### Step 1: Choose the Right Base Class

The framework provides two main base classes:

#### ASTLintRule
For rules that analyze Abstract Syntax Tree nodes:
- Use when checking code structure, patterns, or specific Python constructs
- Examples: detecting magic numbers, checking function complexity, finding print statements

#### FileBasedLintRule
For rules that analyze entire files:
- Use when checking file-level patterns, line counts, or text patterns
- Examples: file naming conventions, license headers, encoding checks

### Step 2: Define Rule Properties

All rules must implement these properties:

```python
@property
def rule_id(self) -> str:
    """Unique identifier in format 'category.rule-name'."""
    return "literals.magic-number"

@property
def rule_name(self) -> str:
    """Human-readable name for display."""
    return "Magic Number Detection"

@property
def description(self) -> str:
    """Detailed description of what the rule checks."""
    return "Detects hardcoded numeric literals that should be constants"

@property
def severity(self) -> Severity:
    """Default severity level: ERROR, WARNING, or INFO."""
    return Severity.WARNING

@property
def categories(self) -> set[str]:
    """Categories for filtering and organization."""
    return {"literals", "maintainability", "constants"}
```

### Step 3: Implement Core Logic

For AST-based rules:

```python
def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
    """Pre-filter nodes to check - improves performance."""
    # Only check specific node types
    return isinstance(node, (ast.Constant, ast.Num))

def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
    """Analyze node and return violations."""
    violations = []

    # Access context information
    if context.current_function == "__init__":
        # Special handling in constructors
        pass

    # Check parent nodes
    parent = context.get_parent_node()
    if isinstance(parent, ast.Assign):
        # Node is in an assignment
        pass

    # Your validation logic
    if self._is_violation(node):
        violations.append(self.create_violation(
            context=context,
            node=node,
            message=f"Found issue at line {node.lineno}",
            description=self.description,
            suggestion="Extract to named constant"
        ))

    return violations
```

### Step 4: Use Context Information

The `LintContext` provides rich information about the code being analyzed:

```python
def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
    # File information
    file_path = context.file_path  # Path object
    file_content = context.file_content  # Full file content

    # Current scope
    current_class = context.current_class  # Class name if inside class
    current_function = context.current_function  # Function name if inside function

    # AST navigation
    parent = context.get_parent_node()  # Get parent node
    grandparent = context.get_parent_node(2)  # Get grandparent
    node_stack = context.node_stack  # Full stack of parent nodes

    # Check if in test file
    is_test = "test" in str(file_path) or "spec" in str(file_path)

    return []
```

### Step 5: Configuration Support

Make rules configurable:

```python
def __init__(self, config: dict[str, Any] | None = None):
    """Initialize with configuration."""
    super().__init__()
    self.config = config or {}

    # Extract configuration with defaults
    self.max_complexity = self.config.get("max_complexity", 10)
    self.allowed_values = set(self.config.get("allowed_values", [0, 1, -1]))
    self.exclude_patterns = self.config.get("exclude_patterns", [])
```

Configuration in `.design-lint.yml`:
```yaml
rules:
  your-category.your-rule:
    enabled: true
    config:
      max_complexity: 15
      allowed_values: [0, 1, 2, 10]
      exclude_patterns: ["test_*", "*_config.py"]
```

## Rule Categories

Place your rule in the appropriate category:

### literals/
Rules for literal values and constants:
- Magic numbers
- Magic strings
- Hardcoded values

### logging/
Rules for logging practices:
- Print statement detection
- Logging format consistency
- Log level appropriateness

### solid/
Rules enforcing SOLID principles:
- Single Responsibility Principle
- Open/Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle

### style/
Code style and formatting rules:
- Naming conventions
- Code complexity
- Nesting depth

### Custom Categories
Create new directories for domain-specific rules:
```bash
mkdir tools/design_linters/rules/security
mkdir tools/design_linters/rules/performance
```

## Testing Your Rule

### Unit Test Structure

Create comprehensive tests in `test/unit_test/tools/design_linters/`:

```python
#!/usr/bin/env python3
"""
Purpose: Unit tests for your custom rule
Scope: Test all aspects of rule behavior
"""

import ast
import unittest
from pathlib import Path

import sys
sys.path.insert(0, '/home/stevejackson/Projects/durable-code-test/tools')

from design_linters.framework.interfaces import LintContext, Severity
from design_linters.rules.category.your_rule import YourRule


class TestYourRule(unittest.TestCase):
    """Test cases for YourRule."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = YourRule()
        self.context = LintContext(
            file_path=Path('/test.py'),
            node_stack=[]
        )

    def test_rule_properties(self):
        """Test rule metadata."""
        self.assertEqual(self.rule.rule_id, 'category.rule-name')
        self.assertEqual(self.rule.severity, Severity.WARNING)
        self.assertIn('category', self.rule.categories)

    def test_detects_violation(self):
        """Test that rule detects violations."""
        # Create AST node that should trigger violation
        code = "your_problematic_code_here"
        tree = ast.parse(code)

        # Set up context
        self.context.ast_tree = tree
        self.context.file_content = code

        # Check for violations
        violations = self.rule.check(self.context)

        self.assertEqual(len(violations), 1)
        self.assertIn("expected message", violations[0].message)

    def test_ignores_valid_code(self):
        """Test that rule ignores valid code."""
        code = "valid_code_here"
        tree = ast.parse(code)

        self.context.ast_tree = tree
        self.context.file_content = code

        violations = self.rule.check(self.context)
        self.assertEqual(len(violations), 0)

    def test_configuration(self):
        """Test rule configuration."""
        config = {"threshold": 5}
        rule = YourRule(config)

        self.assertEqual(rule.threshold, 5)

    def test_context_awareness(self):
        """Test that rule uses context correctly."""
        # Test behavior in different contexts
        self.context.current_function = "__init__"
        # ... test special behavior in __init__

        self.context.current_class = "TestClass"
        # ... test behavior in class context

    def test_ignore_directives(self):
        """Test that ignore comments work."""
        code = '''
# design-lint: ignore-file[category.rule-name]
problematic_code
        '''
        tree = ast.parse(code)

        self.context.ast_tree = tree
        self.context.file_content = code

        violations = self.rule.check(self.context)
        self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
```

### Running Tests

```bash
# Run all linter tests
make test

# Run specific test file
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest \
    test/unit_test/tools/design_linters/test_your_rule.py -v

# Run with coverage
PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools python -m pytest \
    test/unit_test/tools/design_linters/test_your_rule.py --cov=tools/design_linters
```

## Configuration

### Project Configuration

Edit `.design-lint.yml`:

```yaml
# Enable/disable rules
rules:
  category.your-rule:
    enabled: true
    config:
      threshold: 10
      ignore_patterns: ["test_*.py"]

# Set custom severities
severity_overrides:
  category.your-rule: error  # Override default severity

# Exclude files/directories
exclude:
  - "vendor/"
  - "*.generated.py"

# Filter by categories
categories:
  - literals
  - logging
  - your-category
```

### Inline Suppression

Users can suppress your rule with comments:

```python
# Suppress entire file
# design-lint: ignore-file[category.your-rule]

# Suppress specific line
problematic_code()  # design-lint: ignore[category.your-rule]

# Suppress next line
# design-lint: ignore-next-line
problematic_code()

# Suppress category
# design-lint: ignore-file[category.*]
```

## Integration

### Make Targets

Your rule is automatically included in:
- `make lint-custom`: Runs all custom linting rules
- `make lint-all`: Runs all linters including yours
- `make lint-list-rules`: Lists all available rules

### CLI Usage

```bash
# Run specific rule
python tools/design_linters/cli.py --rules category.your-rule src/

# Run category
python tools/design_linters/cli.py --categories your-category src/

# Multiple output formats
python tools/design_linters/cli.py --format json --output report.json src/
python tools/design_linters/cli.py --format sarif --output sarif.json src/
python tools/design_linters/cli.py --format github src/  # For GitHub Actions
```

### CI/CD Integration

The rule automatically runs in CI via GitHub Actions:
1. Triggered on pull requests
2. Results shown as annotations
3. Fails build on ERROR severity violations

## Best Practices

### 1. Follow Coding Standards

Adhere to `.ai/docs/STANDARDS.md`:
- Use type hints for all parameters and returns
- NO print statements - use loguru logger
- Full MyPy strict compliance
- Comprehensive docstrings

### 2. Performance Optimization

```python
def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
    """Pre-filter nodes for performance."""
    # Quick type check first
    if not isinstance(node, ast.Constant):
        return False

    # Then check value type
    if not isinstance(node.value, (int, float)):
        return False

    # Finally, expensive checks
    return not self._is_in_allowed_context(node, context)
```

### 3. Clear Messages

Provide actionable feedback:

```python
def _create_violation(self, node: ast.AST, context: LintContext) -> LintViolation:
    return self.create_violation(
        context=context,
        node=node,
        # Specific message about what's wrong
        message=f"Magic number {node.value} found in {context.get_context_description()}",
        description=self.description,
        # Clear suggestion on how to fix
        suggestion=f"Extract {node.value} to a named constant like 'MAX_RETRIES' or 'DEFAULT_TIMEOUT'"
    )
```

### 4. Context-Aware Analysis

Consider context to reduce false positives:

```python
def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
    violations = []

    # Skip test files
    if self._is_test_file(context.file_path):
        return violations

    # Skip configuration contexts
    if context.current_function in ["__init__", "setup", "configure"]:
        return violations

    # Skip if in acceptable context
    parent = context.get_parent_node()
    if isinstance(parent, ast.Assign) and self._is_constant_assignment(parent):
        return violations

    # Now check for violations
    if self._violates_rule(node):
        violations.append(self._create_violation(node, context))

    return violations
```

### 5. Comprehensive Testing

Test edge cases and different contexts:

```python
def test_edge_cases(self):
    """Test edge cases and boundary conditions."""
    test_cases = [
        ("edge_case_1", expected_violations_1),
        ("edge_case_2", expected_violations_2),
        # ... more cases
    ]

    for code, expected in test_cases:
        with self.subTest(code=code):
            tree = ast.parse(code)
            self.context.ast_tree = tree
            violations = self.rule.check(self.context)
            self.assertEqual(len(violations), expected)
```

## Examples

### Example 1: Detecting TODO Comments

```python
#!/usr/bin/env python3
"""
Purpose: Detect TODO comments in code
Scope: Style category rule for tracking technical debt
"""

import re
from pathlib import Path
from typing import Any

from design_linters.framework.interfaces import FileBasedLintRule, LintContext, LintViolation, Severity


class TodoCommentRule(FileBasedLintRule):
    """Detects TODO comments that should be tracked."""

    @property
    def rule_id(self) -> str:
        return "style.todo-comment"

    @property
    def rule_name(self) -> str:
        return "TODO Comment Detection"

    @property
    def description(self) -> str:
        return "TODO comments should be tracked in issue tracker"

    @property
    def severity(self) -> Severity:
        return Severity.INFO

    @property
    def categories(self) -> set[str]:
        return {"style", "technical-debt"}

    def check_file(self, file_path: Path, content: str, context: LintContext) -> list[LintViolation]:
        violations = []

        # Find TODO patterns
        todo_pattern = re.compile(r'#\s*(TODO|FIXME|HACK|XXX):?\s*(.*)', re.IGNORECASE)

        for line_num, line in enumerate(content.splitlines(), 1):
            match = todo_pattern.search(line)
            if match:
                todo_type = match.group(1).upper()
                todo_text = match.group(2).strip()

                violations.append(LintViolation(
                    rule_id=self.rule_id,
                    file_path=str(file_path),
                    line=line_num,
                    column=match.start(),
                    severity=self.severity,
                    message=f"{todo_type}: {todo_text or 'No description provided'}",
                    description=self.description,
                    suggestion="Create an issue ticket and reference it in the comment"
                ))

        return violations
```

### Example 2: Class Complexity Rule

```python
#!/usr/bin/env python3
"""
Purpose: Detect overly complex classes
Scope: SOLID principles enforcement
"""

import ast
from typing import Any

from design_linters.framework.interfaces import ASTLintRule, LintContext, LintViolation, Severity


class ClassComplexityRule(ASTLintRule):
    """Detects classes with too many methods or attributes."""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__()
        self.config = config or {}
        self.max_methods = self.config.get("max_methods", 10)
        self.max_attributes = self.config.get("max_attributes", 7)

    @property
    def rule_id(self) -> str:
        return "solid.class-complexity"

    @property
    def rule_name(self) -> str:
        return "Class Complexity"

    @property
    def description(self) -> str:
        return "Classes should have a single responsibility"

    @property
    def severity(self) -> Severity:
        return Severity.WARNING

    @property
    def categories(self) -> set[str]:
        return {"solid", "complexity", "srp"}

    def should_check_node(self, node: ast.AST, context: LintContext) -> bool:
        return isinstance(node, ast.ClassDef)

    def check_node(self, node: ast.AST, context: LintContext) -> list[LintViolation]:
        violations = []

        if not isinstance(node, ast.ClassDef):
            return violations

        # Count methods and attributes
        methods = []
        attributes = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith("_"):
                    methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Check violations
        if len(methods) > self.max_methods:
            violations.append(self.create_violation(
                context=context,
                node=node,
                message=f"Class '{node.name}' has {len(methods)} public methods (max: {self.max_methods})",
                description=self.description,
                suggestion="Consider splitting this class into smaller, focused classes"
            ))

        if len(attributes) > self.max_attributes:
            violations.append(self.create_violation(
                context=context,
                node=node,
                message=f"Class '{node.name}' has {len(attributes)} attributes (max: {self.max_attributes})",
                description=self.description,
                suggestion="Consider extracting related attributes into separate classes"
            ))

        return violations
```

## Troubleshooting

### Rule Not Detected

1. Check file location: `tools/design_linters/rules/{category}/`
2. Verify class inherits from `ASTLintRule` or `FileBasedLintRule`
3. Ensure all required properties are implemented
4. Check for import errors: `python -c "from tools.design_linters.rules.category.your_rule import YourRule"`

### Tests Failing

1. Add tools to PYTHONPATH: `export PYTHONPATH=/home/stevejackson/Projects/durable-code-test/tools:$PYTHONPATH`
2. Use absolute imports: `from design_linters.framework.interfaces import ...`
3. Check test file naming: must start with `test_`

### Performance Issues

1. Implement `should_check_node()` to pre-filter nodes
2. Cache expensive computations
3. Avoid repeated file I/O
4. Use early returns in validation logic

## Additional Resources

- **Framework Documentation**: `.ai/features/design-linters.md`
- **Development Standards**: `.ai/docs/STANDARDS.md`
- **Template File**: `.ai/templates/linting-rule.py.template`
- **Example Rules**: `tools/design_linters/rules/` - study existing implementations
- **Test Examples**: `test/unit_test/tools/design_linters/` - review test patterns

## Final Verification

### Step 6: Validate Your Implementation

After implementing your custom linter rule, you must verify that it integrates properly with the entire system:

```bash
# Run comprehensive linting
make lint-all

# Run all tests
make test-all
```

**IMPORTANT**: Both commands must pass successfully. Since linting can modify code and tests can affect linting results, you must run both commands repeatedly until both pass in succession without errors:

```bash
# Verification loop
while true; do
    make lint-all
    if [ $? -ne 0 ]; then
        echo "Linting failed - fix issues and try again"
        break
    fi

    make test-all
    if [ $? -ne 0 ]; then
        echo "Tests failed - fix issues and try again"
        break
    fi

    # Run once more to ensure stability
    make lint-all && make test-all
    if [ $? -eq 0 ]; then
        echo "Success! Both linting and tests pass consistently"
        break
    fi
done
```

This iterative process ensures:
- Your rule doesn't conflict with existing linters
- Tests pass with all linting rules active
- No circular dependencies between linting and testing
- Code remains stable after all automated fixes

## Support

For questions or issues:
1. Check existing rules for patterns
2. Review test files for examples
3. Consult framework documentation
4. Create an issue in the project repository
