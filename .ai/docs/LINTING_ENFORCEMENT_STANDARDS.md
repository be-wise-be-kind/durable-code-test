# Linting Rule Enforcement Standards

**Purpose**: Define strict enforcement policies for linting rules to prevent agents from skipping issues

**Scope**: All code across backend, frontend, infrastructure, tools, and tests

**Overview**: This document establishes the philosophy and enforcement mechanisms for ensuring code quality
    through linting. It explicitly prohibits skipping critical linting rules and provides guidance on how to
    properly fix issues rather than bypassing them. The enforcement is automated through the design linting
    framework and integrated into pre-commit hooks to prevent violations from entering the codebase.

**Dependencies**: Design linting framework, pre-commit hooks, Just targets

**Related**: STANDARDS.md, ERROR_HANDLING_STANDARDS.md, CLAUDE.md

**Implementation**: Automated enforcement via `enforcement.no-skip` rule in design linter framework

---

## Philosophy: Fix, Don't Skip

### Core Principle
**ALWAYS fix the underlying issue, NEVER skip the linting rule.**

Linting rules exist to maintain code quality, prevent bugs, and ensure consistency. When a linting rule fires, it's identifying a real problem that needs to be addressed. Skipping the rule hides the problem without solving it.

### The Problem with Skipping
- **Technical Debt**: Skipped rules accumulate as technical debt
- **Security Risks**: Skipping security rules can introduce vulnerabilities
- **Maintenance Burden**: Future developers must work around skipped rules
- **Slippery Slope**: One skip encourages more skips
- **False Confidence**: Tests and metrics become unreliable

### The Right Approach
1. **Understand the Rule**: Why is it firing? What is it trying to prevent?
2. **Fix the Root Cause**: Refactor the code to comply with the rule
3. **Seek Guidance**: If unsure, ask for help or consult documentation
4. **Only Skip as Last Resort**: And only with explicit approval and documentation

---

## Critical Rules That Must NEVER Be Skipped

### Python Backend

#### Complexity (C901)
```python
# ❌ WRONG - Skipping complexity rule
def complex_function():  # noqa: C901
    # 50 lines of nested if statements
    pass

# ✅ CORRECT - Refactor to reduce complexity
def process_data(data):
    validated_data = validate(data)
    processed_data = transform(validated_data)
    return save(processed_data)

def validate(data):
    # Validation logic extracted
    pass

def transform(data):
    # Transformation logic extracted
    pass

def save(data):
    # Save logic extracted
    pass
```

**Why**: Complex functions are hard to test, maintain, and debug. Break them into smaller, focused functions.

#### Broad Exception Catching (W0718)
```python
# ❌ WRONG - Skipping broad exception rule
try:
    risky_operation()
except Exception:  # pylint: disable=W0718
    pass

# ✅ CORRECT - Catch specific exceptions
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except KeyError as e:
    logger.error(f"Missing key: {e}")
    return default_value
```

**Why**: Broad exception handling masks bugs and makes debugging impossible. Always catch specific exceptions.

#### Line Length (E501)
```python
# ❌ WRONG - Skipping line length rule
some_very_long_variable_name = some_very_long_function_name(arg1, arg2, arg3, arg4, arg5)  # noqa: E501

# ✅ CORRECT - Break into multiple lines
some_very_long_variable_name = some_very_long_function_name(
    arg1=arg1,
    arg2=arg2,
    arg3=arg3,
    arg4=arg4,
    arg5=arg5,
)
```

**Why**: Long lines are hard to read and cause horizontal scrolling. Break them up for readability.

#### Security Rules (S###)
```python
# ❌ WRONG - Skipping security rule
password = "hardcoded_password"  # noqa: S105

# ✅ CORRECT - Use environment variables
import os
password = os.getenv("DATABASE_PASSWORD")
if not password:
    raise ValueError("DATABASE_PASSWORD environment variable not set")
```

**Why**: Security rules prevent vulnerabilities. Never skip them - fix the security issue.

#### Unused Imports (F401)
```python
# ❌ WRONG - Keeping unused imports
import unused_module  # noqa: F401

# ✅ CORRECT - Remove unused imports
# (Simply delete the import)

# ✅ EXCEPTION - Allowed in __init__.py for public API
# file: package/__init__.py
from .module import PublicClass  # noqa: F401 - Re-exported for public API
```

**Why**: Unused imports clutter the code and slow down imports. Remove them unless re-exporting.

### TypeScript/React Frontend

#### No Explicit Any (no-explicit-any)
```typescript
// ❌ WRONG - Skipping type safety
// eslint-disable-next-line no-explicit-any
const data: any = fetchData();

// ✅ CORRECT - Use specific types
interface UserData {
  id: string;
  name: string;
  email: string;
}

const data: UserData = fetchData();

// ✅ ALTERNATIVE - Use unknown for truly dynamic data
const data: unknown = fetchData();
if (isUserData(data)) {
  // Type guard ensures safety
  console.log(data.name);
}
```

**Why**: `any` defeats TypeScript's purpose. Use specific types or `unknown` with type guards.

#### React Hooks Dependencies (react-hooks/exhaustive-deps)
```typescript
// ❌ WRONG - Skipping dependency rule
useEffect(() => {
  fetchData(userId);
// eslint-disable-next-line react-hooks/exhaustive-deps
}, []);

// ✅ CORRECT - Include all dependencies
useEffect(() => {
  fetchData(userId);
}, [userId, fetchData]);

// ✅ ALTERNATIVE - Use useCallback for stable references
const fetchDataCallback = useCallback(() => {
  fetchData(userId);
}, [userId]);

useEffect(() => {
  fetchDataCallback();
}, [fetchDataCallback]);
```

**Why**: Missing dependencies cause stale closures and bugs. Always include all dependencies.

#### React Hooks Rules (react-hooks/rules-of-hooks)
```typescript
// ❌ WRONG - Skipping hooks rules
// eslint-disable-next-line react-hooks/rules-of-hooks
if (condition) {
  const [state, setState] = useState(0);
}

// ✅ CORRECT - Hooks at top level only
const [state, setState] = useState(0);

if (condition) {
  // Use the state here
}
```

**Why**: Hooks must be called in the same order every render. Conditional hooks break React.

#### No Console (no-console)
```typescript
// ❌ WRONG - Skipping console rule
// eslint-disable-next-line no-console
console.log('debug info');

// ✅ CORRECT - Use proper logging
import { logger } from '@/utils/logger';
logger.debug('debug info');
```

**Why**: Console statements leak into production and aren't controllable. Use a logging service.

### Infrastructure (Terraform & Shell)

#### Terraform Validation
```hcl
# ❌ WRONG - Skipping terraform validation
# tflint-ignore: terraform_unused_declarations
resource "aws_s3_bucket" "unused" {
  bucket = "my-bucket"
}

# ✅ CORRECT - Remove unused resources
# (Simply delete the unused resource)
```

**Why**: Unused infrastructure costs money and creates security risks. Remove what you don't need.

#### Shellcheck Rules
```bash
# ❌ WRONG - Skipping shellcheck
# shellcheck disable=SC2086
echo $variable

# ✅ CORRECT - Quote variables
echo "$variable"
```

**Why**: Unquoted variables cause word splitting and globbing bugs. Always quote.

---

## Enforcement Mechanism

### Automated Detection

The `enforcement.no-skip` rule automatically detects and blocks:

- **Python**: `noqa`, `pylint: disable`, `type: ignore`
- **TypeScript**: `eslint-disable`, `@ts-ignore`, `@ts-nocheck`
- **Terraform**: `tflint-ignore`
- **Shell**: `shellcheck disable`

### Integration Points

1. **Pre-commit Hooks**: Runs before every commit
2. **Make Targets**: `just lint-all` includes enforcement checks
3. **CI/CD Pipeline**: Blocks PRs with skip violations
4. **Design Linter**: Part of custom linting framework

### Violation Example

```
ERROR: enforcement.no-skip
File: backend/app/complex.py:42
Message: Skipping rule 'C901' is not allowed - fix the code instead
Suggestion: Refactor the function to reduce complexity (extract helper functions, simplify logic)
```

---

## Whitelisted Exceptions

### Allowed Skips (With Restrictions)

#### 1. Unused Imports in `__init__.py`
```python
# file: package/__init__.py
from .module import PublicClass  # noqa: F401 - Re-exported for public API
```
**Reason**: Common pattern for package public APIs.

#### 2. Test Files (With Caution)
```typescript
// file: component.test.tsx
// eslint-disable-next-line no-explicit-any
const mockData: any = {};  // Test mock data can use any
```
**Reason**: Test mocks sometimes need flexibility. Use sparingly.

### Requesting Exception Approval

If you believe a skip is absolutely necessary:

1. **Document Why**: Explain why the code can't be fixed
2. **Propose Alternative**: What mitigations are in place?
3. **Get Review**: Require team lead or senior developer approval
4. **Add Comment**: Explain the skip with `# Approved by [Name] - [Reason]`
5. **Track as Tech Debt**: Add to technical debt backlog

---

## Common Scenarios and Solutions

### Scenario 1: Legacy Code with High Complexity

**Problem**: Inherited function with C901 complexity violation

**Wrong Approach**:
```python
def legacy_function():  # noqa: C901
    # 100 lines of complex logic
    pass
```

**Right Approach**:
1. Create tests for current behavior
2. Extract helper functions incrementally
3. Reduce complexity step by step
4. Commit after each successful reduction

### Scenario 2: Type Errors in Migration

**Problem**: Converting JavaScript to TypeScript, many type errors

**Wrong Approach**:
```typescript
// @ts-nocheck  // Disable checking for whole file
```

**Right Approach**:
1. Fix types incrementally, file by file
2. Use `unknown` and type guards for dynamic data
3. Create proper interfaces for data structures
4. Use `@ts-expect-error` with explanation for unavoidable cases (rare)

### Scenario 3: External Library Has No Types

**Problem**: Third-party library missing TypeScript definitions

**Wrong Approach**:
```typescript
// eslint-disable-next-line no-explicit-any
const lib: any = require('legacy-lib');
```

**Right Approach**:
1. Check for `@types/legacy-lib` package
2. Create local `.d.ts` type definition file
3. Use `unknown` and create type guards
4. Consider contributing types to DefinitelyTyped

### Scenario 4: Complex Algorithm Needs High Cyclomatic Complexity

**Problem**: Sorting algorithm with many branches

**Wrong Approach**:
```python
def sort_algorithm(data):  # noqa: C901
    # Complex sorting logic with many branches
    pass
```

**Right Approach**:
1. Break into smaller functions (compare, swap, partition)
2. Use helper functions for edge cases
3. Consider using standard library (often better tested)
4. If truly unavoidable, get team approval and document

---

## Developer Responsibilities

### Before Skipping a Rule
1. ✅ Have I read the rule documentation?
2. ✅ Have I tried to fix the underlying issue?
3. ✅ Have I consulted team members or documentation?
4. ✅ Is there truly no way to fix this?
5. ✅ Have I documented why this skip is necessary?
6. ✅ Have I received approval from a team lead?

### When Reviewing Code
- ❌ **REJECT** PRs with unapproved skip directives
- ❌ **REJECT** PRs that skip critical rules (C901, W0718, security)
- ✅ **REQUIRE** explanation comments for any skips
- ✅ **VERIFY** that legitimate fixes were attempted
- ✅ **SUGGEST** alternative approaches to fix the issue

---

## Enforcement Configuration

### Critical Rules List

Maintained in `tools/design_linters/rules/enforcement/no_skip_rules.py`:

```python
CRITICAL_PYTHON_RULES = {
    "C901",   # Complexity
    "W0718",  # Broad exceptions
    "E501",   # Line length
    "S",      # Security (all Bandit rules)
    "F401",   # Unused imports (except __init__.py)
}

CRITICAL_TYPESCRIPT_RULES = {
    "no-explicit-any",
    "react-hooks/exhaustive-deps",
    "react-hooks/rules-of-hooks",
    "no-console",
}
```

### Running Enforcement

```bash
# Check all files for skip violations
just lint-all

# Check specific category
just lint-custom

# Pre-commit hook (automatic)
git commit -m "feat: add feature"  # Enforcement runs automatically
```

---

## Questions and Answers

**Q: What if the linting rule is wrong?**
A: Open an issue to discuss changing the project's linting rules. Don't skip individual occurrences.

**Q: What if I'm in a hurry and need to commit quickly?**
A: The time you save now will be lost debugging later. Fix it properly.

**Q: What if the fix is too complex for my current task?**
A: Create a TODO/FIXME comment and a tracking issue. Don't skip the rule.

**Q: What if a third-party library forces the violation?**
A: Wrap the library in your own interface with proper types. Isolate the violation.

**Q: Can I skip rules in prototype/experimental code?**
A: Create a separate experimental branch. Don't merge to main with skips.

---

## Conclusion

Linting rules are not obstacles - they're guardrails that keep code maintainable and bug-free. When a rule fires, it's providing valuable feedback. Listen to it, fix the issue, and move forward with better code.

**Remember**: Future you (and your teammates) will thank you for fixing issues properly instead of skipping them.