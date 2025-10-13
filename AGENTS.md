# AI Agent Guide for Durable Code Test

**Purpose**: Primary entry point for AI agents working on this project

**Quick Start**: Read `.ai/index.yaml` for full context, then check available resources for your task.

---

## MANDATORY: First Action for Every Task

**BEFORE working on ANY task, you MUST:**

1. ✅ **READ** `.ai/index.yaml` to understand available resources
2. ✅ **IDENTIFY** relevant documentation, howtos, and templates for your task
3. ✅ **READ** all applicable documents completely before proceeding
4. ✅ **INFORM** the user which documents you are using to solve the problem

**Process:**
```
1. Scan .ai/index.yaml sections:
   - documentation: (docs for understanding)
   - howto: (step-by-step guides)
   - templates: (file templates and boilerplate)
   - standards: (requirements and best practices)
   - features: (existing feature documentation)

2. Read applicable documents in this order:
   - Standards/requirements first
   - How-to guides second
   - Templates third

3. Tell the user:
   "I will use these resources to solve this problem:
    - [document 1]: [why it's relevant]
    - [document 2]: [why it's relevant]"

4. Then proceed with the task following the guidance
```

**Examples:**

- **Task: Fix linting errors** → Read `how-to-fix-linting-errors.md` and `how-to-refactor-for-quality.md`
- **Task: Write new file** → Read `FILE_HEADER_STANDARDS.md` and `how-to-write-file-headers.md`
- **Task: Add tests** → Read `run-tests.md` and `testing-framework.md`
- **Task: Create roadmap** → Read `create-roadmap-item.md` and roadmap templates
- **Task: Add API endpoint** → Read `add-api-endpoint.md` and `fastapi-endpoint.py.template`
- **Task: Add React component** → Read `react-component.tsx.template` and `PERFORMANCE_OPTIMIZATION_STANDARDS.md`

**This is NOT optional.** Skipping this step leads to incomplete work and quality issues.

---

## Project Overview

Durable Code Test - A demonstration project showcasing AI-ready development practices with full-stack web application, custom design linters, and infrastructure automation.

**Type**: full-stack-application (React/TypeScript frontend, FastAPI backend, Terraform infrastructure)
**Status**: active-development

## Navigation

### Critical Documents
- **Project Context**: `.ai/docs/REPOSITORY_FOR_AI.md` - Repository patterns and AI development principles
- **Index**: `.ai/index.yaml` - Repository structure and navigation
- **Layout**: `.ai/layout.yaml` - Directory organization rules

### How-To Guides
See `.ai/howto/` for step-by-step guides on common tasks.

### Templates
See `.ai/templates/` for reusable file templates and boilerplate.

### Features
See `.ai/features/` for documentation on implemented features.

## Roadmap-Driven Development

### When User Requests Planning

If the user says any of the following:
- "I want to plan out..."
- "I want to roadmap..."
- "Create a roadmap for..."
- "Plan the implementation of..."
- "Break down the feature..."

**Your Actions**:
1. **Read** `.ai/howto/create-roadmap-item.md` for roadmap workflow guidance
2. **Use templates** from `.ai/templates/roadmap-*.md.template`
3. **Create roadmap** in `roadmap/planning/[feature-name]/`
4. **Follow** the three-document structure:
   - PROGRESS_TRACKER.md (required - primary handoff document with % tracking)
   - PR_BREAKDOWN.md (required for multi-PR features)
   - AI_CONTEXT.md (optional - architectural context)

### When User Requests Continuation

If the user says any of the following:
- "I want to continue with..."
- "Continue the roadmap for..."
- "What's next in..."
- "Resume work on..."

**Your Actions**:
1. **Check** `roadmap/in-progress/` for active roadmaps
2. **Read** the roadmap's `PROGRESS_TRACKER.md` FIRST
3. **READ** `.ai/docs/FILE_HEADER_STANDARDS.md` for header templates
4. **Follow** the "Next PR to Implement" section
5. **Update** PROGRESS_TRACKER.md after completing each PR:
   - Mark PR as complete
   - **Calculate and update completion percentage**
   - Add commit hash to Notes column
   - Update "Next PR to Implement"
   - **Check if directory move needed**:
     - 0% → >0%: Move from `planning/` to `in_progress/`
     - 100%: Move from `in_progress/` to `complete/`

**BEFORE Writing Any Files**:
- ✅ Check `.ai/docs/FILE_HEADER_STANDARDS.md` for correct header template
- ✅ Use template matching file type (Python, TypeScript, YAML, Markdown, etc.)
- ✅ Include ALL mandatory fields: Purpose, Scope, Overview, Dependencies, Exports, Interfaces, Implementation
- ✅ Use atemporal language (no "currently", "now", "new", "old", dates, or temporal references)

### Roadmap Lifecycle

```
planning/ → in_progress/ → complete/
   ↓             ↓              ↓
Created      Implementing    Archived
  (0%)        (1-99%)         (100%)
```

See `.ai/howto/create-roadmap-item.md` for detailed workflow instructions.

## Development Guidelines

### Project-Specific Rules (CRITICAL)

**Docker and Testing**:
- ⚠️ **NEVER run tests locally** - Always use Docker or Make targets
- ⚠️ **NEVER run npm install locally** - Always update package.json and rebuild Docker containers
- ⚠️ All package installations must be done within Docker containers, not on the host system
- ⚠️ All linting should be run through Docker or Make targets (not `npm run lint`, not direct linting commands)

**Make Targets**:
- ⚠️ Always use Make targets for operations (testing, linting, building)
- ⚠️ Always prefer Makefile targets for Terraform operations
- Run all linting via Make targets, don't call linting directly

**Branch Protection**:
- ⚠️ **NEVER create anything on the main branch** - Not a single file, not a single commit
- Always create a feature branch first

**Git Workflow**:
- ⚠️ **NEVER bypass or skip pre-commit hooks** - They must be made to pass
- When creating a PR, always check for uncommitted code - don't leave anything behind

**Terraform State**:
- ⚠️ **NEVER force unlock Terraform state without explicit user permission**
- State locks protect against corruption and concurrent modifications

**File Creation Philosophy**:
- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested

**Linting Rule Enforcement - CRITICAL**:
- ⚠️ **NEVER skip linting rules** using noqa, pylint: disable, type: ignore, or eslint-disable without explicit approval
- ⚠️ **ALWAYS fix the underlying issue** instead of skipping the rule
- ⚠️ **CRITICAL RULES that must NEVER be skipped**:
  - Python: C901 (complexity), W0718 (broad exceptions), E501 (line length), S### (security), F401 (unused imports except __init__.py)
  - TypeScript: no-explicit-any, react-hooks/exhaustive-deps, react-hooks/rules-of-hooks, no-console
  - Infrastructure: terraform validate errors, shellcheck warnings
- If a linting rule is firing, FIX the code - don't skip the rule
- The enforcement.no-skip linting rule will automatically catch and block attempts to skip critical rules
- See `.ai/docs/LINTING_ENFORCEMENT_STANDARDS.md` for complete guidance on fixing vs skipping

### Code Style

**Backend (Python)**:
- Follow PEP 8 style guide
- Use type hints (checked by MyPy)
- Docstrings required for all public functions
- No broad exception catching (W0718 enforced)

**Frontend (TypeScript/React)**:
- Strict TypeScript mode enabled
- No `any` types without justification
- React hooks rules enforced (exhaustive-deps, rules-of-hooks)
- CSS Modules + CSS Variables for styling

**Infrastructure (Terraform)**:
- All resources must have tags
- Use locals for repeated values
- Follow naming conventions (env-project-resource)
- Conditional deployment patterns for cost optimization

### File Organization
See `.ai/layout.yaml` for the canonical directory structure.

**Key Directories**:
- Backend: `durable-code-app/backend/`
- Frontend: `durable-code-app/frontend/`
- Infrastructure: `infra/terraform/`
- Design Linters: `tools/design_linters/`
- Tests: `test/`
- Documentation: `.ai/`
- Roadmaps: `roadmap/`

### Documentation Standards

**MANDATORY: File Headers Before Writing Any Code**

All code files MUST have comprehensive headers following `.ai/docs/FILE_HEADER_STANDARDS.md`:

**Required Process**:
1. ✅ **READ** `.ai/docs/FILE_HEADER_STANDARDS.md` BEFORE writing any files
2. ✅ **SELECT** correct template for file type:
   - Python (.py): Docstring format
   - TypeScript/JavaScript (.ts, .tsx, .js, .jsx): JSDoc format
   - YAML/Config (.yml, .yaml): Comment format
   - Markdown (.md): Structured metadata
3. ✅ **INCLUDE** all mandatory fields:
   - Purpose: Brief description (1-2 lines)
   - Scope: What areas/components this file covers
   - Overview: Comprehensive summary (3-5 sentences minimum)
   - Dependencies: Key dependencies or related files
   - Exports: Main classes, functions, or constants provided
   - Interfaces: Key APIs or methods exposed
   - Implementation: Notable patterns or architectural decisions
4. ✅ **USE** atemporal language (no "currently", "now", "new", "old", dates)

**Validation**: Header linter runs in CI/CD and will block PRs with missing/incorrect headers.

See `.ai/docs/FILE_HEADER_STANDARDS.md` for complete templates and examples.

## Build and Test Commands

### Development
```bash
# Start development environment
make dev

# Check status
make status

# View logs
make logs
```

### Testing
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with coverage
make test-coverage
```

### Linting
```bash
# Run all linting (backend + frontend + custom)
make lint-all

# Fix auto-fixable issues
make lint-fix

# Run custom design linters
make lint-custom
```

### Building
```bash
# Build Docker containers
make build

# Build for production
make build-prod
```

### Infrastructure
```bash
# Check AWS credentials
make infra-check-aws

# Plan infrastructure changes
make infra-plan

# Apply infrastructure changes
make infra-apply

# Destroy infrastructure
make infra-destroy
```

## Git Workflow

### Commit Messages
Follow conventional commits format:
```
type(scope): Brief description

Detailed description if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `infra`

### Branch Strategy
- `main` - Production-ready code (NEVER commit directly)
- `develop` - Integration branch (NEVER push directly)
- `feat/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code refactoring
- `infra/*` - Infrastructure changes

### Before Committing
- [ ] All tests pass (`make test` exits with code 0)
- [ ] Code is linted (`make lint-all` exits with code 0)
- [ ] **All files have proper headers per `.ai/docs/FILE_HEADER_STANDARDS.md`**
- [ ] Documentation updated
- [ ] No secrets committed (pre-commit hooks check this)
- [ ] Pre-commit hooks pass (NEVER skip with --no-verify)

### Quality Gates - CRITICAL

**YOU ARE ALWAYS RESPONSIBLE FOR CODE QUALITY - NO EXCEPTIONS**

**Core Principle**: When you commit code (whether you wrote it, modified it, or just touched the same file), you are responsible for ensuring it meets ALL quality standards. There is no "not my problem" - if you're committing it, it's your responsibility.

**NEVER claim linting is clean unless ALL of these are true:**

1. ✅ `make lint-all` exits with **code 0** - not 1, not 2, exactly 0
2. ✅ **ZERO test failures** - failing tests mean the feature is broken
3. ✅ **No pre-commit hook failures** - if hooks fail, you must fix before committing
4. ✅ **All TypeScript checks pass** - no `any` types, no missing dependencies in hooks
5. ✅ **All Python linting passes** - Ruff, MyPy, Pylint all clean

**Dangerous False Assumptions to AVOID:**

1. ❌ **"This was pre-existing code"**
   - If you're modifying a file, you own the quality of that file
   - If you add code to a file with issues, you must fix those issues
   - Don't rationalize "someone else wrote this" - you're committing it now

2. ❌ **"It's just a linter warning, not an error"**
   - ALL linter output must be addressed
   - Warnings are not "optional suggestions" - they must be fixed or explicitly suppressed with justification
   - Don't dismiss warnings as unimportant

3. ❌ **"The exit code is non-zero but the output looks okay"**
   - Exit code 0 is the ONLY acceptable result
   - Visual inspection of output is NOT a substitute for checking exit codes
   - Use `make lint-all && echo "SUCCESS" || echo "FAILED"` to verify

**Correct Validation Process:**
```bash
# Step 1: Run full linting (must exit with code 0)
make lint-all
if [ $? -ne 0 ]; then
    echo "FAILED - must fix all issues"
    exit 1
fi

# Step 2: Run tests (must exit with code 0)
make test
if [ $? -ne 0 ]; then
    echo "FAILED - must fix all tests"
    exit 1
fi

# Step 3: Only if ALL checks pass with code 0, then quality is acceptable
```

**When Standards Seem Difficult:**
- ✅ DO refactor code to meet standards (extract functions, simplify logic)
- ✅ DO ask the user for permission BEFORE adding any ignore/disable comments
- ✅ DO ask the user if standards should be adjusted (but don't assume they should)
- ❌ DON'T add `# type: ignore`, `# pylint: disable`, `# noqa`, or similar without explicit user permission
- ❌ DON'T lower standards on your own
- ❌ DON'T skip checks or claim "close enough"
- ❌ DON'T rationalize why violations are "acceptable"

**CRITICAL: Suppression Comments Require User Permission**

**NEVER add linter suppression comments without explicit user permission:**
- `# type: ignore` (MyPy)
- `# pylint: disable=rule` (Pylint)
- `# noqa` (Ruff)
- `# nosec` (Bandit)
- `/* eslint-disable */` (ESLint)
- `// @ts-ignore` (TypeScript)
- Any similar suppression directive

**Required Process for Suppressions:**
1. ✅ **STOP** - Don't add the suppression yet
2. ✅ **EXPLAIN** the problem clearly to the user
3. ✅ **PROPOSE** why suppression might be needed
4. ✅ **ASK** for explicit permission from the user
5. ✅ **WAIT** for user approval before adding suppression
6. ✅ **ADD** detailed justification comment if approved

**CRITICAL: Suppression Permission is Issue-Specific and Never Transfers**

Permission to suppress one type of linting issue does NOT grant permission for other issues:

❌ **NEVER Transfer Permission Across:**
- **Issue types**: MyPy permission ≠ Pylint permission ≠ ESLint permission
- **Files**: Permission for file A ≠ permission for file B
- **Phases**: Permission in Phase 1 (basic linting) ≠ permission in Phase 2 (refactoring)
- **Sessions**: Permission expires when context changes to a new issue category

✅ **When Context Changes, Always Ask Again:**
```
Correct: "I've completed the MyPy fixes you approved. Now I found an ESLint
rule firing in the frontend. The component uses a ref that TypeScript
flags. May I suppress this with justification?"

Wrong: "You said I could suppress things, so I'm suppressing this ESLint
violation too."
```

**The Permission Boundary Rule:**

Every time you encounter a NEW:
- Linter tool (MyPy vs Pylint vs ESLint vs Ruff)
- File being modified
- Phase of work (Phase 1 vs Phase 2)
- Category of violation

You MUST:
1. Stop
2. Explain the new issue
3. Justify why suppression might be needed
4. Ask explicitly: "May I add suppression for THIS issue?"
5. Wait for approval

**The Bottom Line:**
If `make lint-all` exits with non-zero code or if tests fail - **your code is not ready to commit**. Period. No excuses, no rationalizations, no "but this was pre-existing" - fix it before committing.

---

## Fixing Linting and Quality Issues

### When to Enter Systematic Linting Mode

Enter systematic linting mode when:

1. **`make lint-all` shows violations** - Any non-zero exit code requires fixing
2. **Pre-commit hooks fail** - Hooks are your first quality gate
3. **PR checks fail** - CI/CD caught issues you missed locally
4. **Working on existing code with issues** - You touched it, you own it
5. **After major refactoring** - Verify quality hasn't degraded
6. **Before creating a PR** - Always validate quality first

### The Two-Phase Approach

**CRITICAL**: Fix linting issues in TWO distinct phases. DO NOT mix them.

#### Phase 1: Basic Linting (Objective Fixes)

**Goal**: Fix mechanical, objective violations with clear right/wrong answers

**Reference**: `.ai/howto/how-to-fix-linting-errors.md`

**Covers**:
- Code style and formatting (Ruff, Prettier, ESLint)
- Security issues (Bandit, ESLint security rules)
- Type checking (MyPy, TypeScript)
- Import organization
- Unused imports/variables

**Success Criteria**:
- `make lint-all` exits with code 0
- All tests pass
- No security violations

**Process**:
```bash
# Run basic linting
make lint-all

# Fix violations following the howto guide
# Validate after each fix
make test  # Ensure nothing broke
```

#### Phase 2: Architectural Refactoring (Design Decisions)

**Goal**: Fix complexity and architectural violations through thoughtful refactoring

**Reference**: `.ai/howto/how-to-refactor-for-quality.md`

**Covers**:
- Component complexity
- React hook dependency arrays
- Performance optimizations
- Code organization improvements

**Success Criteria**:
- All custom design linter rules pass
- Code follows architectural patterns
- All tests pass

**Process**:
```bash
# Run architectural linting
make lint-custom

# Analyze violations together (don't fix sequentially)
# Follow decision tree in howto guide
# Refactor with architectural goals in mind
make test  # Ensure nothing broke
```

### Critical Rule: Never Commit Until BOTH Phases Pass

```bash
# Final validation before commit
make lint-all   # Must exit with code 0
make test       # Must exit with code 0

# Only then:
git commit -m "fix: Resolve all quality issues"
```

---

## Security Considerations

- Never commit secrets or credentials
- Secrets should be in `.env` (gitignored)
- Validate user input
- Use parameterized queries (no SQL injection)
- Implement proper error boundaries in React
- Follow principle of least privilege for AWS resources

## Common Tasks

### Adding a New Feature
1. Check `.ai/features/` for existing feature documentation
2. Create feature branch: `git checkout -b feat/your-feature`
3. If complex, create roadmap in `roadmap/planning/`
4. Implement feature following code style guidelines
5. Add tests
6. Update documentation
7. Run quality checks: `make lint-all && make test`
8. Submit PR

### Adding a Web Tab
See `.ai/howto/` and use `.ai/templates/web-tab.tsx.template`

### Adding an API Endpoint
See `.ai/howto/add-api-endpoint.md` and use `.ai/templates/fastapi-endpoint.py.template`

### Adding a Custom Linter Rule
See `.ai/howto/create-custom-linter.md` and use `.ai/templates/linting-rule.py.template`

### Debugging
1. Check logs: `make logs`
2. Run tests with verbose output: `make test`
3. Use browser DevTools for frontend issues
4. Check `.ai/howto/complete-debugging-guide.md` for systematic approach

## Resources

### Documentation
- Project patterns: `.ai/docs/REPOSITORY_FOR_AI.md`
- Infrastructure: `.ai/docs/INFRASTRUCTURE_PRINCIPLES.md`
- Performance: `.ai/docs/PERFORMANCE_OPTIMIZATION_STANDARDS.md`
- Error handling: `.ai/docs/ERROR_HANDLING_STANDARDS.md`

### External Dependencies
See `durable-code-app/backend/pyproject.toml` and `durable-code-app/frontend/package.json`

## Getting Help

### When Stuck
1. Check `.ai/docs/` for context and architecture
2. Review `.ai/howto/` for guides
3. Check existing code for patterns
4. Review git history for similar changes
5. Check roadmaps in `roadmap/` for related work

### Active Roadmaps
Check `roadmap/in_progress/` for ongoing work and context

---

**Remember**: This repository is designed for AI-assisted development. Following these guidelines ensures consistent, high-quality contributions.
