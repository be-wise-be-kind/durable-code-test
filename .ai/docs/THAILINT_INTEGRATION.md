# Purpose: Thailint integration documentation for code quality enforcement
# Scope: Explanation of thailint usage, configuration, and integration with existing linters
# Overview: Documents the replacement of custom design linters with thailint for magic numbers,
#     nesting depth, SRP violations, file placement, and duplicate code detection. Provides
#     migration guide, configuration reference, ignore statement syntax, and troubleshooting.
#     Explains how thailint complements remaining custom linters for a comprehensive quality
#     enforcement strategy across Python, TypeScript, and JavaScript codebases.
# Dependencies: thailint package, .thailint.yaml configuration, Make targets, pre-commit hooks
# Exports: Documentation for developers using thailint in the project
# Interfaces: README reference, AGENTS.md integration, Make target documentation
# Implementation: Markdown documentation with examples and configuration reference

# Thailint Integration

## Overview

This project uses [thailint](https://pypi.org/project/thailint/) for multi-language code quality enforcement. Thailint replaces several custom design linters to provide better multi-language support and reduce maintenance burden.

## What Thailint Provides

Thailint enforces 5 key code quality rules:

1. **Magic Numbers**: Detects numeric literals that should be named constants
2. **Nesting Depth**: Prevents excessive code nesting for better readability
3. **SRP (Single Responsibility Principle)**: Detects classes with too many methods or responsibilities
4. **File Placement**: Enforces proper project structure and file organization
5. **DRY (Don't Repeat Yourself)**: Detects duplicate code blocks

### What Thailint Replaces

The following custom design linters are **replaced** by thailint:

- `tools/design_linters/rules/literals/magic_number_rules.py` → **thailint magic-numbers**
- `tools/design_linters/rules/style/nesting_rules.py` → **thailint nesting**
- `tools/design_linters/rules/solid/srp_rules.py` → **thailint srp**
- `tools/design_linters/rules/organization/file_placement_rules.py` → **thailint file-placement**
- No equivalent → **thailint dry** (new functionality)

### Custom Linters that Complement Thailint

These custom design linters remain active and complement thailint:

- **File Headers**: `style.file-header` - Enforces comprehensive file documentation headers
- **Print Statements**: `style.print-statement` - Detects debug print statements
- **Logging**: `logging.*` - Enforces Loguru usage and logging best practices
- **Security**: `security.*` - Detects security vulnerabilities in code
- **Error Handling**: `error_handling.*` - Enforces proper exception handling
- **Enforcement**: `enforcement.no-skip` - Prevents improper use of linter suppressions
- **Testing**: `testing.*` - Enforces testing best practices

## Configuration

Thailint is configured via `.thailint.yaml` in the project root.

### Current Configuration

```yaml
# Magic Numbers
magic-numbers:
  enabled: true
  allowed_numbers: [-1, 0, 1, 2, 10, 100, 1000, 1024]
  max_small_integer: 10
  ignore:
    - "test/**"
    - "**/test_*.py"
    - "**/*constants.py"

# Nesting Depth
nesting:
  enabled: true
  max_nesting_depth: 4
  ignore:
    - "test/**"

# Single Responsibility Principle
srp:
  enabled: true
  max_methods: 15
  max_loc: 200
  check_keywords: true
  keywords:
    - Manager
    - Handler
    - Processor
  ignore:
    - "test/**"
    - "**/*Rule.py"  # Framework pattern classes

# File Placement
file-placement:
  enabled: true
  layout_file: ".ai/layout.yaml"
  ignore:
    - ".git/**"
    - "**/node_modules/**"

# DRY (Don't Repeat Yourself)
dry:
  enabled: true
  min_duplicate_lines: 4
  min_occurrences: 2
  ignore:
    - "test/**"
    - "**/__init__.py"
```

## Usage

### Via Make Targets

```bash
# Run all thailint checks
make lint-thailint

# Run all linting (including thailint)
make lint-all

# Run custom linters (now includes thailint)
make lint-custom
```

### Via Command Line

```bash
# Check magic numbers
thailint magic-numbers backend/ tools/

# Check nesting depth
thailint nesting backend/ tools/

# Check SRP violations
thailint srp backend/ tools/

# Check file placement
thailint file-placement .

# Check for duplicate code
thailint dry backend/ tools/
```

### Via Pre-Commit Hooks

Thailint runs automatically on changed files during `git commit`:

```bash
git add .
git commit -m "Your commit message"
# Thailint runs automatically on Python, TypeScript, and JavaScript files
```

## Ignoring Violations

### Line-Level Ignores

Ignore specific violations on a single line:

```python
value = 3600  # thailint: ignore[magic-numbers]

class LegacyController:  # thailint: ignore[srp]
    pass
```

### Method-Level Ignores

Ignore violations for an entire function:

```python
def complex_function():  # thailint: ignore[nesting,srp]
    # Complex nested logic here
    pass
```

### File-Level Ignores

Ignore all violations of a type in a file (place near top of file):

```python
# thailint: ignore-file[magic-numbers]
```

### Repository-Level Ignores

Configure ignore patterns in `.thailint.yaml`:

```yaml
magic-numbers:
  ignore:
    - "test/**"
    - "**/*_constants.py"
```

## Migration from Custom Linters

### Old vs New Ignore Syntax

| Old Custom Linter | New Thailint |
|-------------------|--------------|
| `# design-lint: ignore[literals.magic-number]` | `# thailint: ignore[magic-numbers]` |
| `# design-lint: ignore[style.excessive-nesting]` | `# thailint: ignore[nesting]` |
| `# design-lint: ignore[solid.srp.*]` | `# thailint: ignore[srp]` |
| `# design-lint: ignore[organization.file-placement]` | `# thailint: ignore[file-placement]` |

**Note**: Ignore statements use thailint syntax for rules managed by thailint.

### Behavior Characteristics

1. **Magic Numbers**: Thailint magic number detection flags numeric literals that lack context
2. **Nesting**: Depth calculation uses AST-based analysis to measure code complexity
3. **SRP**: Uses method count and LOC thresholds (configurable in `.thailint.yaml`)
4. **File Placement**: References `.ai/layout.yaml` for project structure rules
5. **DRY**: Detects duplicate code blocks across the codebase

## Troubleshooting

### Thailint Not Found

```bash
# Install thailint
poetry add --dev thailint

# Rebuild Docker containers
docker-compose -f .docker/compose/lint.yml build
```

### Configuration Not Loading

```bash
# Verify configuration exists
ls -la .thailint.yaml

# Test configuration
thailint magic-numbers --help
```

### False Positives

1. **Add to ignore patterns** in `.thailint.yaml` (repository-level)
2. **Use inline ignores** for specific cases (line-level)
3. **Adjust thresholds** in `.thailint.yaml` (configuration)

### Pre-Commit Hook Failures

```bash
# Run linting manually to see full output
make lint-thailint

# Skip pre-commit hooks temporarily (not recommended)
git commit --no-verify

# Fix issues and recommit
make lint-fix
git add -u
git commit
```

## Integration with CI/CD

Thailint runs automatically in GitHub Actions via the `make lint-all` target:

```yaml
# .github/workflows/ci.yml
- name: Run linting
  run: make lint-all  # Includes thailint
```

## Best Practices

1. **Fix violations instead of ignoring**: Thailint violations indicate real code quality issues
2. **Use repository-level ignores sparingly**: Only for legitimate exceptions (tests, generated code)
3. **Document why when ignoring**: Add comments explaining why a violation is acceptable
4. **Keep configuration in sync**: If you adjust thresholds, document the reasoning
5. **Review DRY violations carefully**: Duplicate code detection may reveal refactoring opportunities

## Further Reading

- [Thailint Documentation](https://github.com/be-wise-be-kind/thai-lint/tree/main/docs)
- [Thailint PyPI Page](https://pypi.org/project/thailint/)
- [Project Layout Standards](.ai/docs/STANDARDS.md)
- [Linting Workflow](.ai/howto/run-linting.md)
