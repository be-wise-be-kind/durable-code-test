# Development Standards and Best Practices

**Purpose**: Define comprehensive development standards for Python backend and React frontend applications

**Scope**: All development practices, code quality requirements, and project structure standards

**Overview**: Establishes comprehensive development standards that ensure code quality, maintainability,
    and consistency across Python backend and React frontend applications. Covers type safety requirements,
    testing strategies, security practices, and project organization patterns that support reliable software
    development. Provides detailed guidelines for code style, API design, error handling, and performance
    optimization that enable sustainable long-term development practices.

**Dependencies**: Python development tooling, React/TypeScript ecosystem, testing frameworks, linting tools

**Exports**: Development standards, coding guidelines, quality requirements, project structure patterns

**Related**: FILE_HEADER_STANDARDS.md, linting configuration, testing documentation, security guidelines

**Implementation**: Comprehensive standards enforcement through automated tooling, testing requirements, and code review processes

---

## Python Backend Standards

### 1. Project Structure: see ../layout.yaml

### 2. Code Style and Formatting
- **Formatter**: Black with line length 120
- **Linter**: Ruff with default configuration
- **Type Checker**: MyPy with strict mode
- **Docstrings**: Google style docstrings for all public functions/classes
- **Naming Conventions**:
  - Classes: PascalCase
  - Functions/Variables: snake_case
  - Constants: UPPER_SNAKE_CASE
  - Private methods: _leading_underscore

### 3. Type Annotation Requirements (MyPy & Pylint Compliance)

#### Core Requirements
- **MANDATORY**: All code must pass `mypy --strict` without any errors or warnings
- **MANDATORY**: All code must pass `pylint` with project configuration
- **PROHIBITED**: Never use `# type: ignore` comments - fix the actual type issue
- **PROHIBITED**: Never disable W0718 (broad-exception-caught) - catch specific exceptions

#### Function and Method Signatures
All functions and methods must have complete type annotations:

```python
# ✅ CORRECT - Complete type hints
def process_data(items: list[str], threshold: int = 10) -> dict[str, Any]:
    """Process data items with optional threshold."""
    return {"processed": len(items), "threshold": threshold}

# ❌ INCORRECT - Missing type hints
def process_data(items, threshold=10):  # MyPy error: Missing type annotations
    return {"processed": len(items), "threshold": threshold}
```

#### Modern Python 3.11+ Type Syntax
Use built-in generics instead of typing module imports:

```python
# ✅ CORRECT - Python 3.11+ built-in generics
def get_items() -> list[str]:
    return ["item1", "item2"]

def get_mapping() -> dict[str, int]:
    return {"key": 1}

# ❌ INCORRECT - Old typing module syntax
from typing import List, Dict
def get_items() -> List[str]:  # Use list[str] instead
    return ["item1", "item2"]
```

#### Class Type Annotations
All class attributes must be explicitly typed:

```python
# ✅ CORRECT - All attributes typed
class DataProcessor:
    items: list[str]
    threshold: int
    results: dict[str, Any] | None = None
    _cache: dict[str, Any]  # Private attributes also need types

    def __init__(self) -> None:
        self.items = []
        self.threshold = 10
        self.results = None
        self._cache = {}

# ❌ INCORRECT - Missing attribute types
class DataProcessor:
    def __init__(self):  # Missing return type
        self.items = []  # Type not declared in class body
```

#### Optional and Union Types
Use modern `|` syntax for unions and optional types:

```python
# ✅ CORRECT - Modern union syntax
def process(value: str | int | None = None) -> bool:
    return value is not None

# Alternative for Optional (both are acceptable)
from typing import Optional
def process(value: Optional[str] = None) -> bool:
    return value is not None

# ❌ INCORRECT - Missing None in union when default is None
def process(value: str = None) -> bool:  # MyPy error: incompatible default
    return value is not None
```

#### Avoiding Common MyPy/Pylint Errors

**1. Mutable Default Arguments**
```python
# ❌ INCORRECT - Mutable default argument (pylint: W0102)
def process(items: list[str] = []) -> None:
    items.append("new")

# ✅ CORRECT - Use None and create inside function
def process(items: list[str] | None = None) -> None:
    if items is None:
        items = []
    items.append("new")
```

**2. TypeVar Usage**
```python
# ✅ CORRECT - Properly bound TypeVar
from typing import TypeVar

T = TypeVar('T')
NumberT = TypeVar('NumberT', bound=float)

def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

**3. Self Type in Methods**
```python
from typing import Self  # Python 3.11+

class Node:
    def add_child(self, child: Self) -> Self:
        # Returns same type as the class
        return self
```

**4. Callable Types**
```python
from collections.abc import Callable

# ✅ CORRECT - Fully typed callable
def register_callback(
    func: Callable[[str, int], bool]
) -> None:
    pass

# ❌ INCORRECT - Untyped callable
def register_callback(func: Callable) -> None:  # Missing argument and return types
    pass
```

#### Import Requirements
Use absolute imports for better type checking:

```python
# ✅ CORRECT - Absolute imports
from design_linters.framework.interfaces import ASTLintRule, LintContext
from app.models.user import UserModel

# ❌ INCORRECT - Relative imports can confuse type checkers
from ...framework.interfaces import ASTLintRule
from ..models.user import UserModel
```

#### Logging Requirements
Always use loguru for logging:

```python
# ✅ CORRECT - Loguru
from loguru import logger

logger.info("Processing started")

# ❌ INCORRECT - Never use built-in logging module
import logging
logger = logging.getLogger(__name__)  # Don't use this
```

#### Protocol and ABC Usage
Use Protocol for structural typing, ABC for inheritance:

```python
from typing import Protocol
from abc import ABC, abstractmethod

# Protocol - for structural typing (duck typing)
class Drawable(Protocol):
    def draw(self, canvas: Canvas) -> None: ...

# ABC - for inheritance hierarchies
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...
```

#### Async Function Types
Properly type async functions:

```python
from collections.abc import Coroutine
from typing import Any

# Direct async function
async def fetch_data(url: str) -> dict[str, Any]:
    ...

# Function returning coroutine
def create_task(url: str) -> Coroutine[Any, Any, dict[str, Any]]:
    return fetch_data(url)
```

#### Context Managers
Type context managers properly:

```python
from types import TracebackType
from typing import Self

class DatabaseConnection:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        self.close()
```

#### Dataclass Integration
Use proper typing with dataclasses:

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    name: str
    enabled: bool = True
    timeout: float | None = None
    tags: list[str] = field(default_factory=list)  # Correct mutable default
```

#### Type Checking Configuration
Ensure mypy.ini or pyproject.toml has strict settings:

```toml
[tool.mypy]
python_version = "3.11"
strict = true  # Enables all strict flags
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true
```

#### Common Error Solutions

| Error | Solution |
|-------|----------|
| `Missing type annotations` | Add complete type hints to all functions |
| `Incompatible default for argument` | Include `None` in union type when default is None |
| `Need type annotation for variable` | Explicitly type class attributes |
| `Cannot determine type` | Add explicit type annotation: `items: list[str] = []` |
| `Broad exception caught (W0718)` | Catch specific exceptions, never use bare `except:` |
| `Mutable default argument (W0102)` | Use `None` default with initialization in function |

### 3.5 Linting Rule Enforcement - NO SKIPPING CRITICAL RULES

#### Core Principle: Fix, Don't Skip
**PROHIBITED**: Skipping linting rules without fixing the underlying issue
**REQUIRED**: All code must pass linting without skip directives for critical rules

When a linting rule fires, it's identifying a real problem. The solution is to **fix the code**, not skip the rule.

#### Critical Rules That Must NEVER Be Skipped

**Python Backend:**
- **C901** - Complexity too high: Refactor into smaller functions
- **W0718** - Broad exception catching: Catch specific exceptions
- **E501** - Line too long: Break into multiple lines
- **S###** - Security violations (Bandit): Fix the security issue
- **F401** - Unused imports: Remove them (except __init__.py re-exports)

**TypeScript/React Frontend:**
- **no-explicit-any**: Use specific types or `unknown` with type guards
- **react-hooks/exhaustive-deps**: Add all dependencies to dependency array
- **react-hooks/rules-of-hooks**: Move hooks to top level of component
- **no-console**: Use proper logging service

**Infrastructure:**
- **terraform validate**: Fix Terraform configuration errors
- **shellcheck warnings**: Fix shell script issues

#### Enforcement Mechanism

The `enforcement.no-skip` rule automatically detects and blocks skip attempts:
```python
# ❌ BLOCKED - Will fail pre-commit hook
def complex():  # noqa: C901
    pass

# ✅ CORRECT - Refactor to fix
def complex():
    step_one()
    step_two()
```

**Integration Points:**
- Pre-commit hooks: Runs automatically before commits
- `just lint-all`: Includes enforcement checks
- CI/CD: Blocks PRs with violations
- Design linter: `--categories enforcement`

#### Whitelisted Exceptions

Only these patterns are allowed:
```python
# ✅ Allowed: F401 in __init__.py for public API
from .module import PublicClass  # noqa: F401

# ✅ Allowed: Test files can use 'any' sparingly
const mockData: any = {};  # Test mock only
```

#### What To Do Instead

1. **Understand the Rule**: Read documentation for why it exists
2. **Fix the Root Cause**: Refactor code to comply
3. **Seek Help**: Ask teammates or consult docs if unsure
4. **Get Approval**: If truly unavoidable, document and get team lead approval

**See .ai/docs/LINTING_ENFORCEMENT_STANDARDS.md for complete guidance**

### 4. API Design Principles
- RESTful conventions with proper HTTP methods
- Version API endpoints (/api/v1/)
- Use Pydantic models for request/response validation
- Implement proper error handling with meaningful status codes
- Document all endpoints with OpenAPI/Swagger

### 5. Testing Requirements
- Minimum 80% code coverage
- Use pytest for all tests
- Test file naming: test_*.py
- Use fixtures for common test data
- Mock external dependencies

### 6. Security Best Practices
- Never hardcode secrets
- Use environment variables for configuration
- Implement proper authentication/authorization
- Validate all inputs with Pydantic
- Use parameterized queries for database operations
- Enable CORS with specific origins only

### 7. Error Handling
- Use custom exception classes
- Implement global exception handlers
- Return consistent error response format:
  ```python
  {
      "error": {
          "code": "ERROR_CODE",
          "message": "Human readable message",
          "details": {}
      }
  }
  ```

### 8. Logging Standards - LOGURU ONLY, NO PRINT STATEMENTS
- **PROHIBITED**: `print()` statements are strictly forbidden in production code
- **PROHIBITED**: Built-in `logging` module is forbidden - use `loguru` instead
- **REQUIRED**: Use `loguru` for ALL logging needs throughout the codebase
- **Installation**: `poetry add loguru` or `pip install loguru`
- **Import**: `from loguru import logger`
- **Consistent Usage**: All modules, classes, and functions must use loguru logger
- **Usage Examples**:
  ```python
  from loguru import logger

  # Instead of print("Debug info")
  logger.debug("Debug information")

  # Instead of print(f"Processing {item}")
  logger.info(f"Processing {item}")

  # Instead of print(f"Warning: {message}")
  logger.warning(f"Warning: {message}")

  # Instead of print(f"Error: {error}")
  logger.error(f"Error occurred: {error}")

  # NEVER use built-in logging module
  # WRONG: import logging; logging.getLogger(__name__).info("message")
  # CORRECT: from loguru import logger; logger.info("message")
  ```
- **Log Levels**:
  - `logger.trace()`: Detailed diagnostic info
  - `logger.debug()`: Debug information
  - `logger.info()`: General informational messages
  - `logger.success()`: Success messages
  - `logger.warning()`: Warning messages
  - `logger.error()`: Error messages
  - `logger.critical()`: Critical failure messages
- **Configuration**:
  ```python
  # Configure in main.py or config.py
  from loguru import logger

  logger.add(
      "logs/app_{time}.log",
      rotation="500 MB",
      retention="10 days",
      level="INFO"
  )
  ```
- **Benefits of Loguru over Built-in Logging**:
  - Structured logging with automatic formatting
  - Built-in rotation and retention
  - Better performance than print statements
  - Thread-safe and async-safe
  - Contextual information (file, function, line)
  - Easy filtering and formatting
  - Simpler API than Python's logging module
  - No need for logger configuration or getLogger() calls
  - Automatic serialization of complex objects
- **Migration from Built-in Logging**:
  ```python
  # OLD (built-in logging) - DO NOT USE
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Message")

  # NEW (loguru) - REQUIRED
  from loguru import logger
  logger.info("Message")
  ```
- **Enforcement**:
  - The `print_statement_linter.py` tool automatically detects and reports any print statements
  - Custom linting rules detect usage of built-in logging module

### 9. Dependency Management
- Use Poetry for dependency management
- Pin exact versions in pyproject.toml
- Separate dev dependencies
- Regular security updates

## React Frontend Standards

### 1. Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable components
│   │   └── features/        # Feature-specific components
│   ├── core/
│   │   └── errors/          # Error boundary repository
│   │       ├── MinimalErrorBoundary.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── ErrorBoundary.types.ts
│   │       └── index.ts
│   ├── pages/               # Page components (must have error boundaries)
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API services
│   ├── store/               # State management
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── styles/              # Global styles
│   ├── App.tsx
│   └── main.tsx             # Must include root error boundary
├── scripts/                 # Page content verification tools
│   ├── simple-check.js
│   └── check-page-content.js
├── public/
├── tests/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

### 2. Code Style and Formatting
- **Formatter**: Prettier with 2 space indentation
- **Linter**: ESLint with recommended rules
- **TypeScript**: Strict mode enabled
- **Import Order**:
  1. React imports
  2. Third-party libraries
  3. Internal absolute imports
  4. Relative imports
  5. Style imports

### 3. Component Guidelines
- **Functional Components Only**: Use hooks instead of class components (Exception: Error boundaries require class components)
- **Error Boundary Requirements**:
  - ✅ **MANDATORY**: All route components must be wrapped with error boundaries
  - ✅ **MANDATORY**: Root level error boundary in main.tsx
  - ✅ **RECOMMENDED**: Component-level error boundaries for complex features
  - ✅ **STANDARD**: Use MinimalErrorBoundary for stability unless advanced features needed
  - ✅ **TESTING**: Verify with `scripts/check-page-content.js` after adding error boundaries
- **Component Structure**:
  ```typescript
  // 1. Imports
  // 2. Type definitions
  // 3. Error boundary wrapper (if applicable)
  // 4. Component definition
  // 5. Styled components (if using CSS-in-JS)
  ```
- **Naming Conventions**:
  - Components: PascalCase
  - Props interfaces: ComponentNameProps
  - Hooks: use prefix (useCustomHook)
  - Event handlers: handle prefix (handleClick)
  - Boolean props: is/has/should prefix

### 4. TypeScript Best Practices
- Define explicit types for all props
- Avoid using `any` type
- Use interfaces for object types
- Use type for unions and primitives
- Export types from their usage location

### 5. State Management
- Use React Context for global state
- Use local state for component-specific data
- Use custom hooks for reusable stateful logic
- Implement proper loading and error states

### 6. API Integration
- Centralize API calls in services directory
- Use environment variables for API URLs
- Implement proper error handling
- Add request/response interceptors
- Type all API responses

### 7. Performance Optimization
- Use React.memo for expensive components
- Implement lazy loading for routes
- Use useMemo and useCallback appropriately
- Optimize bundle size with code splitting
- Minimize re-renders

### 8. Logging Standards - NO CONSOLE STATEMENTS
- **PROHIBITED**: `console.log()`, `console.debug()`, `alert()`, and `debugger` statements are strictly forbidden in production code
- **Allowed in Development Only**: Console statements must be removed before committing
- **Recommended Loggers**:
  - **Winston**: For Node.js/backend logging
  - **Pino**: Lightweight alternative for Node.js
  - **Debug**: For development debugging (`DEBUG=app:* npm start`)
- **For Frontend React/TypeScript**:
  ```typescript
  // Use a logging service/utility
  import { logger } from '@/utils/logger';

  // Instead of console.log("User logged in")
  logger.info('User logged in', { userId: user.id });

  // Instead of console.error("API failed")
  logger.error('API request failed', { error, endpoint });
  ```
- **Example Logger Setup** (utils/logger.ts):
  ```typescript
  const isDevelopment = process.env.NODE_ENV === 'development';

  export const logger = {
    debug: (...args: any[]) => isDevelopment && console.debug(...args),
    info: (...args: any[]) => isDevelopment && console.info(...args),
    warn: (...args: any[]) => console.warn(...args), // Keep warnings
    error: (...args: any[]) => console.error(...args), // Keep errors
  };
  ```
- **Benefits**:
  - Can be toggled off in production builds
  - Prevents sensitive data leakage
  - Improves performance (no console overhead)
  - Enables proper log aggregation
- **Build-time Removal**: Configure webpack/vite to strip console statements:
  ```javascript
  // vite.config.ts
  esbuild: {
    drop: ['console', 'debugger'],
  }
  ```
- **Enforcement**: The `print_statement_linter.py` tool detects console.log, alert, and debugger statements

### 9. Testing Requirements
- Unit tests for utilities and hooks
- Component testing with React Testing Library
- Integration tests for critical user flows
- Maintain 70% code coverage minimum

### 10. Accessibility Standards
- Use semantic HTML elements
- Provide proper ARIA labels
- Ensure keyboard navigation
- Maintain proper heading hierarchy
- Test with screen readers

### 11. CSS Guidelines
- Use CSS Modules or styled-components
- Follow BEM naming for class names
- Use CSS variables for theming
- Mobile-first responsive design
- Avoid inline styles

## File Placement and Organization Standards

### 1. Root-Level Files
**Allowed files only:**
- Configuration files: `.gitignore`, `.env.example`, `docker-compose.yml`, `Makefile`, `README.md`
- Project setup files: `pyproject.toml`, `package.json` (for monorepo package managers)
- CI/CD files: `.pre-commit-config.yaml`, `.github/` directory contents
- IDE configurations: `.vscode/`, `.idea/` (optional)

**Prohibited at root:**
- Source code files (`.py`, `.js`, `.ts`, `.tsx`, `.html`, `.css`)
- Test files (`test_*.py`, `*.test.js`, `*.spec.ts`)
- Build artifacts (`dist/`, `build/`, compiled files)

### 2. Python Files Placement
```
├── durable-code-app/backend/
│   ├── app/                    # Application source code
│   │   ├── *.py               # Python modules
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Data models
│   │   ├── services/          # Business logic
│   │   └── core/              # Core functionality
│   └── docs/                  # Module-specific documentation
├── tools/                     # Development and build tools
│   └── *.py                   # Python utility scripts
└── test/                      # ALL project tests (unified location)
    ├── unit_test/             # Unit tests for all components
    │   ├── tools/             # Tests for tools/ directory
    │   ├── backend/           # Tests for backend components
    │   └── frontend/          # Tests for frontend components
    └── integration_test/      # Integration tests
```

**Important**: All test files should be in the root `test/` directory, organized by component being tested. This provides a unified testing structure across the entire project.

### 3. Frontend Files Placement
```
├── durable-code-app/frontend/
│   ├── src/                   # Source code
│   │   ├── *.tsx, *.ts        # TypeScript/React files
│   │   ├── *.css              # Stylesheets
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API services
│   │   ├── types/             # Type definitions
│   │   └── utils/             # Utility functions
│   ├── public/                # Static assets
│   │   ├── *.html             # HTML templates (index.html only)
│   │   ├── *.svg, *.png       # Static images
│   │   └── *.ico              # Favicons
│   ├── tests/                 # Test files
│   │   ├── *.test.tsx         # Component tests
│   │   ├── *.spec.ts          # Unit tests
│   │   └── __tests__/         # Test directories
│   └── dist/                  # Build output (generated)
```

### 4. HTML Files Placement Rules
- **Main Template**: `frontend/index.html` (Vite entry point - required in frontend root)
- **Static HTML**: `frontend/public/` for additional static pages
- **Documentation HTML**: `docs/` directory only
- **Build Output**: `frontend/dist/` (auto-generated)
- **Component HTML**: Should be React/JSX components in `frontend/src/components/`

**Prohibited locations:**
- Root directory
- Backend directories
- Direct in `src/` without component structure

**Note**: `index.html` must be in the frontend root directory as required by Vite.

### 5. Test Files Organization
```
├── test/                      # ALL project tests (unified structure)
│   ├── unit_test/            # Unit tests organized by component
│   │   ├── tools/            # Tests for tools/ directory
│   │   │   ├── test_magic_number_detector.py
│   │   │   └── test_srp_analyzer.py
│   │   ├── backend/          # Tests for backend components
│   │   │   ├── app/          # Tests for backend app
│   │   │   ├── api/          # API endpoint tests
│   │   │   └── models/       # Model tests
│   │   └── frontend/         # Tests for frontend components
│   │       ├── components/   # Component tests
│   │       └── utils/        # Utility function tests
│   ├── integration_test/     # Integration tests
│   │   ├── backend/          # Backend integration tests
│   │   └── frontend/         # Frontend integration tests
│   └── fixtures/             # Test data and fixtures
└── durable-code-app/frontend/tests/ # Frontend-specific tests (if needed)
    └── e2e/                  # End-to-end tests only
```

**Key Principles:**
- **Unified Structure**: All tests in root `test/` directory
- **Component Organization**: Tests organized by what they test, not where they run
- **Clear Separation**: Unit tests, integration tests, and fixtures clearly separated
- **Frontend Exception**: Only E2E tests can remain in frontend/tests/ if needed for tooling

### 6. Documentation Files
- **Project docs**: `docs/` directory
- **Component docs**: Next to source files or in module `docs/` subdirectory
- **API docs**: Auto-generated in `durable-code-app/backend/docs/`
- **README files**: Each major directory can have one README.md

### 7. Configuration Files Hierarchy
```
├── .env.example               # Global environment template
├── .pre-commit-config.yaml    # Global pre-commit
├── durable-code-app/
│   ├── backend/
│   │   ├── pyproject.toml     # Python dependencies
│   │   ├── .flake8           # Python linting config
│   │   └── .env              # Backend-specific env (gitignored)
│   └── frontend/
│       ├── package.json       # Node dependencies
│       ├── tsconfig.json      # TypeScript config
│       ├── vite.config.ts     # Build tool config
│       └── .env              # Frontend-specific env (gitignored)
```

### 8. File Placement Validation Rules
The custom file placement linter enforces these rules:
- **Python files**: Must be in `app/`, `tools/`, or root `test/` directories
- **HTML files**: Must be in `frontend/`, `frontend/public/`, `frontend/dist/`, or `docs/`
- **TypeScript/React**: Must be in `frontend/src/` or `frontend/tests/` (E2E only)
- **CSS files**: Must be in `frontend/src/` or `frontend/public/`
- **Test files**: Must be in root `test/` directory with proper organization
- **Config files**: Must be in designated locations based on scope and purpose

**Critical Rule**: All test files must be in the root `test/` directory, organized by component being tested, not by technology stack.

## General Development Practices

### 1. Version Control
- Commit messages: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
- Keep commits atomic and focused
- Write descriptive PR descriptions

### 2. Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded values
- [ ] Error handling is implemented
- [ ] **Error boundaries are implemented** (for React components)
- [ ] **Page content verification passes** (`scripts/check-page-content.js`)
- [ ] Security considerations addressed
- [ ] Performance impact considered

### 3. Documentation Requirements
- README with setup instructions
- API documentation
- Component documentation
- Architecture decision records
- Deployment guides

### 4. Development Workflow
1. Create feature branch from main
2. Write tests first (TDD approach)
3. Implement feature
4. Run linters and formatters
5. Ensure all tests pass
6. Update documentation
7. Create pull request
8. Address review feedback
9. Merge after approval

### 5. Performance Monitoring
- Implement logging for errors
- Monitor API response times
- Track frontend performance metrics
- Set up alerts for critical issues

### 6. Security Checklist
- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] Authentication required where needed
- [ ] HTTPS enforced
- [ ] Dependencies updated
- [ ] Security headers configured
- [ ] Rate limiting implemented

## Continuous Integration/Deployment

### 1. Pre-commit Hooks
- Format code automatically
- Run linters
- Check for secrets
- Verify commit message format

### 2. CI Pipeline
- Run tests on every PR
- Check code coverage
- Run security scans
- Build validation
- Deploy to staging

### 3. Production Deployment
- Require PR approval
- Run full test suite
- Deploy with rollback capability
- Monitor after deployment
- Update documentation

## Code Quality Metrics
- Code coverage: >75%
- Cyclomatic complexity: <10
- Duplication: <3%
- Technical debt ratio: <5%
- Bundle size limits enforced
