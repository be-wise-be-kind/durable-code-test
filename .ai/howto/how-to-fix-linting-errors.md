# How to Fix Linting Errors (Phase 1: Basic Linting)

**Purpose**: Systematic guide for fixing objective, mechanical linting violations

**Scope**: Code style, formatting, security, type checking, and import organization

**Overview**: Phase 1 of the two-phase linting approach focuses on objective violations with clear right/wrong answers. These are mechanical fixes that don't require architectural decisions. Complete Phase 1 before moving to Phase 2 (architectural refactoring).

---

## When to Use This Guide

Use this guide when:
- ✅ `make lint-all` shows violations
- ✅ Pre-commit hooks fail
- ✅ You're starting work on a feature
- ✅ PR checks are failing
- ✅ Before creating a pull request

## Phase 1 Categories

### 1. Code Style and Formatting

**Backend (Python)**:
- Indentation and spacing
- Line length violations
- Import ordering
- Trailing whitespace
- Quote style consistency

**Frontend (TypeScript/React)**:
- Prettier formatting
- Semicolons and quotes
- Indentation
- Line breaks

**Command to Check**:
```bash
make lint-all
```

**How to Fix**:
```bash
# Auto-fix most formatting issues
make lint-fix

# Then check for remaining issues
make lint-all
```

### 2. Import Organization

**Python Issues**:
- Unused imports
- Duplicate imports
- Import ordering (stdlib → third-party → local)
- Star imports (`from module import *`)

**TypeScript Issues**:
- Unused imports
- Missing imports
- Import path inconsistencies

**How to Fix**:
```bash
# Python: Let Ruff auto-organize
make lint-fix

# TypeScript: Let Prettier + ESLint fix
make lint-fix
```

**Manual Fixes Required**:
- Remove genuinely unused imports
- Replace star imports with explicit imports
- Fix circular import issues

### 3. Type Checking

**Python (MyPy)**:
Common issues:
- Missing type hints on function arguments
- Missing return type hints
- Incorrect type annotations
- Type incompatibilities

**How to Fix**:
```python
# Before: No type hints
def process_data(data):
    return data.upper()

# After: With type hints
def process_data(data: str) -> str:
    return data.upper()
```

**TypeScript**:
Common issues:
- Use of `any` type
- Missing type definitions
- Type assertion needed
- Incompatible types

**How to Fix**:
```typescript
// Before: Using any
const processData = (data: any) => data.toUpperCase();

// After: Proper typing
const processData = (data: string): string => data.toUpperCase();
```

**Check Types**:
```bash
# Python
make lint-all  # Includes MyPy

# TypeScript
make lint-all  # Includes TypeScript compiler
```

### 4. Security Issues

**Python (Bandit)**:
Common issues:
- Hardcoded passwords/secrets
- SQL injection vulnerabilities
- Insecure cryptography
- Shell injection risks
- Eval/exec usage

**How to Fix**:
```python
# Before: Hardcoded secret
API_KEY = "sk-1234567890abcdef"

# After: Environment variable
import os
API_KEY = os.getenv("API_KEY")

# Before: SQL injection risk
query = f"SELECT * FROM users WHERE id = {user_id}"

# After: Parameterized query
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

**TypeScript (ESLint security rules)**:
- XSS vulnerabilities
- Unsafe innerHTML usage
- Insecure randomness

**Check Security**:
```bash
make lint-all  # Includes security scanning
```

### 5. Code Quality Basics

**Python (Pylint basics)**:
- Unused variables
- Redefined variables
- Missing docstrings
- Invalid names (too short, wrong case)

**How to Fix**:
```python
# Before: Unused variable
def calculate(x, y):
    result = x + y
    unused = x * y  # ← Unused
    return result

# After: Remove unused
def calculate(x, y):
    result = x + y
    return result

# Before: Missing docstring
def calculate(x, y):
    return x + y

# After: With docstring
def calculate(x: int, y: int) -> int:
    """Calculate the sum of two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Sum of x and y
    """
    return x + y
```

**TypeScript (ESLint basics)**:
- Unused variables
- Console.log statements
- Missing semicolons
- Debugger statements

**How to Fix**:
```typescript
// Before: Console.log left in
const processData = (data: string) => {
  console.log('Processing:', data);  // ← Remove
  return data.toUpperCase();
};

// After: Use proper logging or remove
const processData = (data: string): string => {
  return data.toUpperCase();
};
```

### 6. React-Specific Issues

**Common Issues**:
- Missing key props in lists
- Unused hook dependencies
- Direct state mutation
- Missing dependency arrays

**How to Fix**:
```typescript
// Before: Missing key
{items.map(item => <div>{item.name}</div>)}

// After: With key
{items.map(item => <div key={item.id}>{item.name}</div>)}

// Before: Missing dependencies
useEffect(() => {
  fetchData(userId);
}, []);  // ← Missing userId

// After: Complete dependencies
useEffect(() => {
  fetchData(userId);
}, [userId, fetchData]);
```

## Systematic Fixing Process

### Step 1: Run Full Lint Check

```bash
# Run all linting
make lint-all > lint-output.txt 2>&1

# Review output
cat lint-output.txt
```

### Step 2: Auto-Fix What's Possible

```bash
# Auto-fix formatting and simple issues
make lint-fix

# Check what's left
make lint-all
```

### Step 3: Fix By Category

Work through violations in this order:

1. **Formatting** (should be auto-fixed)
2. **Imports** (mostly auto-fixed, remove genuinely unused)
3. **Security** (always fix immediately)
4. **Types** (add missing annotations)
5. **Basic quality** (docstrings, unused variables)

### Step 4: Validate Continuously

After each fix:
```bash
# Check linting
make lint-all

# Run tests to ensure nothing broke
make test
```

### Step 5: Commit When Clean

Only commit when:
- ✅ `make lint-all` exits with code 0
- ✅ `make test` exits with code 0
- ✅ All Phase 1 issues resolved

```bash
git add .
git commit -m "fix: Resolve Phase 1 linting violations"
```

## Common Patterns and Solutions

### Pattern 1: Too Many Import Violations

**Problem**: Hundreds of import-related errors

**Solution**:
```bash
# Let tooling fix it
make lint-fix

# Review what's left - likely unused imports
# Remove them manually
```

### Pattern 2: Missing Type Hints Everywhere

**Problem**: File has no type hints

**Solution**:
```python
# Start with function signatures
def process_data(data: str) -> dict[str, Any]:
    ...

# Then add complex types as needed
from typing import Optional, List, Dict

def get_users(
    active: bool = True,
    limit: Optional[int] = None
) -> List[Dict[str, str]]:
    ...
```

### Pattern 3: Broad Exception Catching

**Problem**: `except Exception:` everywhere

**Solution**:
```python
# Before: Too broad
try:
    result = risky_operation()
except Exception:
    pass

# After: Specific exceptions
try:
    result = risky_operation()
except (ValueError, KeyError) as e:
    logger.error(f"Operation failed: {e}")
    raise
```

See `.ai/docs/ERROR_HANDLING_STANDARDS.md` for complete guidance.

### Pattern 4: React Hook Dependency Warnings

**Problem**: ESLint warns about missing dependencies

**Solution**:
```typescript
// Before: Missing dependencies
useEffect(() => {
  fetchData(userId);
}, []);  // ← ESLint warning

// After: Complete dependencies
useEffect(() => {
  fetchData(userId);
}, [userId, fetchData]);

// Or: Use useCallback to stabilize functions
const fetchDataCallback = useCallback(() => {
  fetchData(userId);
}, [userId]);

useEffect(() => {
  fetchDataCallback();
}, [fetchDataCallback]);
```

## Troubleshooting

### Issue: Linting passes locally but fails in CI

**Cause**: Different tool versions or incomplete runs

**Solution**:
```bash
# Ensure you're running same checks as CI
make lint-all

# Check exit code explicitly
make lint-all && echo "PASS" || echo "FAIL"
```

### Issue: Auto-fix breaks code

**Cause**: Conflicting formatter rules or edge cases

**Solution**:
```bash
# Run tests immediately after auto-fix
make lint-fix && make test

# If tests fail, review the changes
git diff

# Revert if needed
git checkout -- .
```

### Issue: Can't fix without architectural changes

**Indication**: This is a Phase 2 issue

**Solution**:
- Complete all Phase 1 fixes first
- Move to Phase 2: Read `.ai/howto/how-to-refactor-for-quality.md`

## When to Move to Phase 2

Move to Phase 2 (architectural refactoring) when:

✅ All of these are true:
- `make lint-all` exits with code 0
- All auto-fixable issues resolved
- All type hints added
- All security issues fixed
- All unused imports removed
- All tests pass

❌ Don't move to Phase 2 if:
- Basic linting still shows errors
- Tests are failing
- Security issues remain

**Next Steps**:
Read `.ai/howto/how-to-refactor-for-quality.md` for Phase 2 guidance.

## Quick Reference

| Issue Type | Tool | Auto-Fix | Manual Fix Required |
|-----------|------|----------|---------------------|
| Formatting | Prettier/Ruff | ✅ Yes | Rarely |
| Imports | ESLint/Ruff | ✅ Mostly | Remove unused |
| Type hints | MyPy/TSC | ❌ No | Always |
| Security | Bandit/ESLint | ❌ No | Always |
| Docstrings | Pylint | ❌ No | Always |
| Unused vars | ESLint/Ruff | ⚠️ Sometimes | Often |
| React keys | ESLint | ❌ No | Always |
| Hook deps | ESLint | ❌ No | Always |

## Success Criteria

Phase 1 is complete when:

```bash
# These commands all exit with code 0
make lint-all
make test

# And you see output like:
# "All checks passed"
# "0 errors, 0 warnings"
# "All tests passed"
```

**Remember**: Phase 1 is about mechanical fixes. If you need to make architectural decisions, that's Phase 2.

---

**Related Documentation**:
- `.ai/howto/how-to-refactor-for-quality.md` - Phase 2 guidance
- `.ai/docs/LINTING_ENFORCEMENT_STANDARDS.md` - Enforcement rules
- `.ai/docs/ERROR_HANDLING_STANDARDS.md` - Error handling patterns
