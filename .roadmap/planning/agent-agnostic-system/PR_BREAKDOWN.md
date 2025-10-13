# Agent-Agnostic System - PR Breakdown

## PR1: AGENTS.md with Navigation Core and Dual-Format Layout System

### Overview
Create AGENTS.md with human-readable file placement rules alongside a new layout.json with machine-readable regex patterns for linters. This dual approach ensures both AI understanding and automated enforcement.

### Files to Create/Modify
- `AGENTS.md` (create at root)
- `.ai/layout.json` (create new - machine-readable patterns)
- `Makefile` (add validate-layout target)

### Implementation Steps

1. **Create AGENTS.md header with purpose**
```markdown
# AGENTS.md

Universal AI agent instructions for the Durable Code Test project. This file provides entry points for any AI tool (Claude, GPT-4, Copilot, Cursor, etc.) to understand and work with this codebase.

**Navigation Philosophy**: This file contains essential information. For detailed documentation, templates, and guides, see the `.ai/` directory structure described below.
```

2. **Add Project Overview**
```markdown
## Project Overview

AI-ready development demonstration with:
- **Frontend**: React 18, TypeScript, Vite
- **Backend**: FastAPI, Python 3.11
- **Infrastructure**: Docker, Terraform, AWS
- **Quality**: Custom linters, comprehensive testing
- **Documentation**: Sophisticated `.ai/` system
```

3. **Embed Navigation from index.yaml**
```markdown
## Project Navigation

### Quick References
- **Project Index**: `.ai/index.yaml` - Complete navigation map
- **Layout Rules**: `.ai/layout.yaml` - File placement enforcement
- **Detailed Docs**: `.ai/index_expanded.md` - Comprehensive guide

### Documentation Structure
```
.ai/
├── templates/        # Code generation patterns (15+ templates)
├── howto/           # Step-by-step guides (20+ guides)
├── docs/            # Standards and principles
├── features/        # Feature documentation
├── runbooks/        # Operational procedures
└── troubleshooting/ # Problem resolution
```

### Key Templates
- React Components: `.ai/templates/react-component.tsx.template`
- API Endpoints: `.ai/templates/fastapi-endpoint.py.template`
- Test Suites: `.ai/templates/test-suite.py.template`
- See `.ai/index.yaml` for complete list
```

4. **Add Human-Readable File Placement Rules in AGENTS.md**
```markdown
## File Placement Rules

**CRITICAL**: Files must be placed in specific locations. Violations will be caught by linters.

### Absolute Rules
- **Frontend Code**: ONLY in `durable-code-app/frontend/src/`
- **Backend Code**: ONLY in `durable-code-app/backend/app/`
- **Tests**: Adjacent to code or in `test/`
- **Infrastructure**: ONLY in `infrastructure/`
- **Linting Rules**: ONLY in `tools/design_linters/rules/`

### Never Allow
- JavaScript in backend directories
- Python in frontend directories
- Temporary files (`temp_*.py`, `*.tmp`)
- Test files not ending in `_test.py` or `.test.ts`

⚠️ **For Linter Enforcement**: These rules are enforced via regex patterns in `.ai/layout.json`

### Maintaining File Placement Rules
When file placement rules change:
1. Update human-readable rules in this section
2. Update regex patterns in `.ai/layout.json`
3. Run `make validate-layout` to ensure consistency
4. Test with linters to verify enforcement
```

5. **Create layout.json with Machine-Readable Patterns**
```json
// File: .ai/layout.json
{
  "_description": "Machine-readable file placement patterns for linters",
  "_note": "Keep synchronized with AGENTS.md file placement rules section",
  "_validation": "Run 'make validate-layout' to check consistency",

  "rules": {
    "frontend": {
      "description": "Frontend TypeScript/React code",
      "allowed_patterns": [
        "durable-code-app/frontend/src/**/*.ts",
        "durable-code-app/frontend/src/**/*.tsx",
        "durable-code-app/frontend/src/**/*.js",
        "durable-code-app/frontend/src/**/*.jsx"
      ],
      "forbidden_patterns": [
        "**/*.py",
        "**/temp_*",
        "**/*.tmp"
      ]
    },
    "backend": {
      "description": "Backend Python/FastAPI code",
      "allowed_patterns": [
        "durable-code-app/backend/app/**/*.py",
        "durable-code-app/backend/tests/**/*_test.py"
      ],
      "forbidden_patterns": [
        "**/*.js",
        "**/*.jsx",
        "**/*.ts",
        "**/*.tsx",
        "**/temp_*.py"
      ]
    },
    "tests": {
      "description": "Test files",
      "allowed_patterns": [
        "test/**/*_test.py",
        "test/**/*.test.ts",
        "test/**/*.test.tsx",
        "*/tests/**/*_test.py",
        "*/tests/**/*.test.ts"
      ],
      "forbidden_patterns": [
        "**/test_*.py",
        "**/*test.py"
      ]
    },
    "infrastructure": {
      "description": "Terraform and infrastructure code",
      "allowed_patterns": [
        "infrastructure/**/*.tf",
        "infrastructure/**/*.tfvars"
      ],
      "forbidden_patterns": [
        "infrastructure/**/*.py",
        "infrastructure/**/*.js"
      ]
    }
  }
}
```

6. **Add Makefile Target to Validate Consistency**
```makefile
# In Makefile
.PHONY: validate-layout
validate-layout:
	@echo "Validating AGENTS.md ↔ layout.json consistency..."
	@echo ""
	@echo "Checking that both files exist..."
	@test -f AGENTS.md || (echo "❌ AGENTS.md not found" && exit 1)
	@test -f .ai/layout.json || (echo "❌ .ai/layout.json not found" && exit 1)
	@echo "✅ Both files exist"
	@echo ""
	@echo "Checking rule categories match..."
	@grep -q "Frontend Code: ONLY" AGENTS.md || echo "⚠️ Frontend rules missing in AGENTS.md"
	@grep -q "Backend Code: ONLY" AGENTS.md || echo "⚠️ Backend rules missing in AGENTS.md"
	@grep -q '"frontend"' .ai/layout.json || echo "⚠️ Frontend patterns missing in layout.json"
	@grep -q '"backend"' .ai/layout.json || echo "⚠️ Backend patterns missing in layout.json"
	@echo ""
	@echo "✅ Layout validation complete"
	@echo "Note: Manual review recommended to ensure rules match semantically"
```

7. **Add Quick Start section**
```markdown
## Quick Start

```bash
# Start development environment
make dev              # All services in Docker

# Run quality checks
make lint-all         # All linters
make test            # All tests
make typecheck       # Type checking

# Fix issues
make fix             # Auto-fix formatting
make fix-intelligent # AI-guided fixing (see below)
```
```

6. **Add AI Permissions (replacing settings.json)**
```markdown
## AI Permissions

### ✅ Auto-Allowed Operations
These operations are safe and don't require permission:
- All `make` commands
- Git operations: `add`, `commit`, `diff`, `status`, `log`
- Docker commands: `ps`, `logs`, `exec`, `build`
- Read operations: `cat`, `ls`, `grep`, `find`
- Project navigation and file reading

### ⚠️ Requires Explicit Permission
Always ask before:
- `git push` - Pushing to remote
- `gh pr create` - Creating pull requests
- `--no-verify` - Skipping any hooks
- `rm -rf` - Deleting files/directories
- `sudo` - Any privileged operations

### ❌ Never Allowed
These operations should be avoided:
- Installing Python packages globally (use Docker)
- Running Python directly (use Docker containers)
- Modifying system configuration
- Disabling security features
```

7. **Add Agentic Commands section**
```markdown
## Agentic AI Commands

These make commands trigger AI agent workflows. They work with ANY AI tool by outputting structured instructions.

### Available Commands
```bash
make help-ai              # List all AI commands
make ask-ai QUESTION="..."  # Get project information
make review-ai            # Comprehensive code review
make fix-intelligent      # Iterative test fixing
make analyze-performance  # Performance analysis
make security-audit       # Security review
```

### How Agentic Commands Work
When you run an agentic command, it:
1. Gathers context (test output, lint results, etc.)
2. Outputs structured instructions for the AI
3. The AI reads instructions and performs the task
4. Results are verified through standard commands

Example: `make fix-intelligent` will show test failures and instruct the AI to fix them iteratively.
```

8. **Add Common Workflows**
```markdown
## Common Workflows

### Adding New API Endpoint
1. Check layout rules: Backend code goes in `backend/app/`
2. Use template: `.ai/templates/fastapi-endpoint.py.template`
3. Add Pydantic models for validation
4. Write tests in `backend/tests/`
5. Run `make test-backend` to verify

### Creating React Component
1. Check layout rules: Frontend code in `frontend/src/`
2. Use template: `.ai/templates/react-component.tsx.template`
3. Add TypeScript interfaces
4. Include tests alongside component
5. Run `make test-frontend` to verify

### Infrastructure Changes
1. Modify Terraform in `infrastructure/`
2. Run `make terraform-plan` to preview
3. Get approval for production changes
4. Apply with `make terraform-apply`
```

9. **Add Standards Reference**
```markdown
## Code Standards

### Mandatory Requirements
1. **Linting**: Must pass `make lint-all`
2. **Tests**: Required for new features (80% coverage)
3. **Types**: Full type hints (Python) and strict mode (TypeScript)
4. **Hooks**: Pre-commit hooks MUST pass (no --no-verify)
5. **Documentation**: File headers required (see `.ai/docs/FILE_HEADER_STANDARDS.md`)

### Quality Gates
- No PR without passing tests
- No merge without code review
- No deployment without CI passing
```

10. **Add footer with references**
```markdown
## Advanced Documentation

For detailed information beyond this entry point:

- **Complete Index**: `.ai/index.yaml` - Full navigation
- **Detailed Guides**: `.ai/howto/` - Step-by-step procedures
- **Templates**: `.ai/templates/` - Code generation patterns
- **Standards**: `.ai/docs/` - Comprehensive standards
- **Features**: `.ai/features/` - Feature documentation

## Migration Note

This project is transitioning from Claude-specific commands to universal AI compatibility. During transition:
- Claude users: Can still use `/` commands
- Other AI users: Use make commands documented above
- All users: AGENTS.md is the primary reference

---
*This file enables any AI tool to work with the project. For tool-specific optimizations, check your AI's documentation.*
```

8. **Update Linter to Use layout.json**
```python
# Update tools/design_linters/rules/organization/file_placement.py
import json
from pathlib import Path

def load_layout_rules():
    """Load file placement rules from layout.json"""
    layout_path = Path('.ai/layout.json')
    with open(layout_path, 'r') as f:
        return json.load(f)

def check_file_placement(filepath: Path) -> List[LintViolation]:
    """Validate files against layout.json patterns"""
    rules = load_layout_rules()
    violations = []

    for category, config in rules['rules'].items():
        allowed = config.get('allowed_patterns', [])
        forbidden = config.get('forbidden_patterns', [])

        # Check against patterns...
    return violations
```

### Testing Instructions
1. Create AGENTS.md and layout.json
2. Run `make validate-layout` to check consistency
3. Test linter with various file placements
4. Load ONLY AGENTS.md in Claude
5. Ask: "How do I add a new API endpoint?"
6. Verify AI understands to keep both files in sync
7. Test with another AI tool (GPT-4, etc.)
8. Measure context usage difference

### Success Criteria
- [ ] AI can understand rules from AGENTS.md
- [ ] Linter enforces rules from layout.json
- [ ] Both files are consistent
- [ ] AI knows to update both when rules change
- [ ] make validate-layout works correctly
- [ ] Any AI tool can use the file

---

## PR2: Agent-Triggering Make Commands

### Overview
Create Makefile.agents with commands that output structured instructions for AI agents, replacing Claude-specific slash commands.

### Files to Create/Modify
- `Makefile.agents` (create new)
- `Makefile` (modify to include Makefile.agents)
- `AGENTS.md` (update with command documentation)

### Implementation Steps

1. **Create Makefile.agents with header**
```makefile
# Makefile.agents - AI Agent Commands
# These commands output instructions that any AI can follow

.PHONY: help-ai
help-ai:
	@echo "🤖 AI Agent Commands:"
	@echo ""
	@echo "  make ask-ai QUESTION='...'  - Get project information"
	@echo "  make review-ai              - Comprehensive code review"
	@echo "  make fix-intelligent        - Fix test/lint failures"
	@echo "  make reconcile-ai           - Reconcile documentation"
	@echo "  make solid-ai               - SOLID principles analysis"
	@echo "  make analyze-performance    - Performance analysis"
	@echo "  make security-audit         - Security review"
	@echo "  make optimize-code          - Optimization suggestions"
	@echo "  make document-code          - Generate documentation"
	@echo ""
	@echo "These commands work with ANY AI tool (Claude, GPT-4, Copilot, etc.)"
```

2. **Implement ask-ai command**
```makefile
.PHONY: ask-ai
ask-ai:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║                   AI AGENT TASK: Answer Question           ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "QUESTION: $(QUESTION)"
	@echo ""
	@echo "INSTRUCTIONS FOR AI:"
	@echo "1. First, check .ai/index.yaml for navigation"
	@echo "2. Then check .ai/layout.yaml for file placement rules"
	@echo "3. Reference relevant documentation in .ai/"
	@echo "4. Check actual implementation files if needed"
	@echo "5. Provide comprehensive answer with examples"
	@echo ""
	@echo "AVAILABLE RESOURCES:"
	@echo "- Project Index: .ai/index.yaml"
	@echo "- Layout Rules: .ai/layout.yaml"
	@echo "- Templates: .ai/templates/"
	@echo "- How-to Guides: .ai/howto/"
	@echo "- Standards: .ai/docs/"
	@echo ""
	@echo "Please provide a complete answer based on project documentation."
```

3. **Implement review-ai command**
```makefile
.PHONY: review-ai
review-ai:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║              AI AGENT TASK: Code Review                    ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Performing comprehensive code review..."
	@echo ""
	@echo "=== STEP 1: Linting Check ==="
	@make lint-all 2>&1 || true
	@echo ""
	@echo "=== STEP 2: Test Coverage ==="
	@make test-coverage 2>&1 || true
	@echo ""
	@echo "=== STEP 3: Type Checking ==="
	@make typecheck 2>&1 || true
	@echo ""
	@echo "REVIEW INSTRUCTIONS FOR AI:"
	@echo "Based on the output above, please review:"
	@echo ""
	@echo "1. CODE QUALITY:"
	@echo "   □ Are linting issues critical or minor?"
	@echo "   □ Is the code following project standards?"
	@echo "   □ Are there code smells or anti-patterns?"
	@echo ""
	@echo "2. TESTING:"
	@echo "   □ Is test coverage adequate (>80%)?"
	@echo "   □ Are edge cases covered?"
	@echo "   □ Are tests meaningful?"
	@echo ""
	@echo "3. ARCHITECTURE:"
	@echo "   □ Does code follow SOLID principles?"
	@echo "   □ Is there proper separation of concerns?"
	@echo "   □ Are dependencies well-managed?"
	@echo ""
	@echo "4. PERFORMANCE:"
	@echo "   □ Are there obvious bottlenecks?"
	@echo "   □ Is caching used appropriately?"
	@echo "   □ Are database queries optimized?"
	@echo ""
	@echo "5. SECURITY:"
	@echo "   □ Is input validation present?"
	@echo "   □ Are secrets handled properly?"
	@echo "   □ Are there SQL injection risks?"
	@echo ""
	@echo "Please provide a summary with:"
	@echo "- Critical issues (must fix)"
	@echo "- Recommendations (should fix)"
	@echo "- Suggestions (nice to have)"
```

4. **Implement fix-intelligent command**
```makefile
.PHONY: fix-intelligent
fix-intelligent:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║           AI AGENT TASK: Intelligent Fix                   ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Gathering all issues..."
	@echo ""
	@echo "=== TEST FAILURES ==="
	@make test 2>&1 || true
	@echo ""
	@echo "=== LINT ISSUES ==="
	@make lint-all 2>&1 || true
	@echo ""
	@echo "=== TYPE ERRORS ==="
	@make typecheck 2>&1 || true
	@echo ""
	@echo "FIXING INSTRUCTIONS FOR AI:"
	@echo ""
	@echo "Please fix issues in this priority order:"
	@echo ""
	@echo "1. CRITICAL (Fix First):"
	@echo "   - Test failures (functional breaks)"
	@echo "   - Type errors (contract violations)"
	@echo "   - Security issues"
	@echo ""
	@echo "2. IMPORTANT (Fix Second):"
	@echo "   - Linting errors"
	@echo "   - Missing imports"
	@echo "   - Undefined variables"
	@echo ""
	@echo "3. MINOR (Fix Last):"
	@echo "   - Formatting issues (can use 'make fix')"
	@echo "   - Style violations"
	@echo ""
	@echo "ITERATIVE PROCESS:"
	@echo "1. Read the error messages above"
	@echo "2. Understand root cause"
	@echo "3. Fix the issue in the source code"
	@echo "4. Run the specific test: make test-specific TEST=..."
	@echo "5. Once fixed, verify with full test: make test"
	@echo "6. Repeat for each issue"
	@echo ""
	@echo "For formatting issues, you can use: make fix"
```

5. **Implement reconcile-ai command**
```makefile
.PHONY: reconcile-ai
reconcile-ai:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║         AI AGENT TASK: Reconcile Documentation            ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Checking documentation consistency..."
	@echo ""
	@echo "FILES TO CHECK:"
	@ls -la .ai/ 2>/dev/null || echo "No .ai directory"
	@ls -la roadmap/ 2>/dev/null || echo "No roadmap directory"
	@echo ""
	@echo "RECONCILIATION INSTRUCTIONS FOR AI:"
	@echo ""
	@echo "1. CHECK FOR INCONSISTENCIES:"
	@echo "   □ Do .ai/index.yaml entries match actual files?"
	@echo "   □ Are roadmap percentages accurate?"
	@echo "   □ Do templates match current code patterns?"
	@echo "   □ Are how-to guides still valid?"
	@echo ""
	@echo "2. CHECK FOR DUPLICATES:"
	@echo "   □ Multiple files covering same topic?"
	@echo "   □ Conflicting instructions?"
	@echo "   □ Outdated vs current versions?"
	@echo ""
	@echo "3. CHECK FOR GAPS:"
	@echo "   □ Missing documentation for features?"
	@echo "   □ Incomplete how-to guides?"
	@echo "   □ Undocumented commands?"
	@echo ""
	@echo "4. UPDATE AS NEEDED:"
	@echo "   □ Fix inconsistencies"
	@echo "   □ Remove duplicates"
	@echo "   □ Fill gaps"
	@echo "   □ Update cross-references"
```

6. **Add utility functions**
```makefile
# Utility functions for consistent output
define agent_header
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║$(1)║"
	@echo "╚════════════════════════════════════════════════════════════╝"
endef

define agent_section
	@echo ""
	@echo "=== $(1) ==="
	@echo ""
endef
```

7. **Include in main Makefile**
```makefile
# In Makefile
include Makefile.agents

# Add to help target
help::
	@echo "  make help-ai         Show AI agent commands"
```

### Testing Instructions
1. Run `make help-ai` to see all commands
2. Test `make ask-ai QUESTION="How to add API endpoint?"`
3. Test `make review-ai` and verify output structure
4. Test `make fix-intelligent` with actual failures
5. Verify ANY AI can understand instructions

### Success Criteria
- [ ] All slash commands have make equivalents
- [ ] Instructions are clear and structured
- [ ] Commands work with any AI tool
- [ ] Output is actionable

---

## PR3: Migrate Claude Settings to AGENTS.md

### Overview
Convert .claude/settings.json permissions to human-readable markdown in AGENTS.md.

### Files to Modify
- `AGENTS.md` (expand permissions section)
- `.claude/settings.json` (mark as deprecated)

### Implementation Steps

1. **Analyze current settings.json**
```bash
# Extract and categorize all permissions
cat .claude/settings.json | jq '.permissions'
```

2. **Expand AI Permissions in AGENTS.md**
```markdown
## AI Permissions

### ✅ Auto-Allowed Operations

#### Make Commands (Safe)
- `make *` - All make targets are safe
- `make dev` - Start development
- `make test` - Run tests
- `make lint-all` - Check code quality
- `make fix` - Auto-fix formatting

#### Git Operations (Read/Local)
- `git status`, `git diff`, `git log` - Read operations
- `git add`, `git commit` - Local changes
- `git checkout`, `git branch` - Branch management
- `git stash` - Temporary storage

#### Docker Commands
- `docker ps`, `docker logs` - Monitoring
- `docker exec` - Container access
- `docker build` - Image creation
- `docker-compose *` - Service management

#### File Operations
- `cat`, `ls`, `tree` - Reading files
- `grep`, `find` - Searching
- `mkdir` - Creating directories
- `echo` - Output text

### ⚠️ Requires Permission

#### Remote Operations
- `git push` - Pushing to remote (ask: "May I push to remote?")
- `gh pr create` - Creating PRs (ask: "May I create a PR?")
- `gh pr merge` - Merging PRs (ask: "May I merge this PR?")

#### Destructive Operations
- `rm -rf` - Deleting directories (ask: "May I delete [path]?")
- `git reset --hard` - Resetting changes (ask: "May I reset?")
- `git force-push` - Force pushing (ask: "May I force push?")

#### System Operations
- `sudo *` - Privileged operations (ask: "May I run with sudo?")
- `npm install -g` - Global installs (ask: "May I install globally?")

### ❌ Never Allowed

#### Python Execution
- Direct Python execution outside Docker
- `pip install` outside containers
- `python setup.py` operations
- Global Python package installation

#### Security Risks
- Disabling security features
- Skipping tests in CI
- Committing secrets
- Modifying .git/hooks

### 📝 Permission Examples

```bash
# ✅ Allowed
make test
git commit -m "Fix: Update component"
docker exec app-container npm test

# ⚠️ Ask First
git push origin main  # "May I push to main?"
rm -rf node_modules   # "May I delete node_modules?"

# ❌ Never
python script.py      # Use: docker exec app python script.py
pip install pandas    # Use: Docker container with pandas
```
```

3. **Add deprecation notice to settings.json**
```json
{
  "_deprecated": "This file is deprecated. See AGENTS.md for permissions.",
  "_migration": "All permissions have been moved to human-readable format in AGENTS.md",
  "permissions": {
    // ... existing permissions remain for backward compatibility
  }
}
```

### Success Criteria
- [ ] All permissions documented in markdown
- [ ] Examples provided for each category
- [ ] Clear rationale for restrictions
- [ ] Works with any AI tool

---

## PR4: Create Agentic Workflows

### Overview
Build sophisticated make targets that guide AI through complex, multi-step tasks.

### Files to Modify
- `Makefile.agents` (add complex workflows)

### Implementation Steps

1. **Add performance analysis workflow**
```makefile
.PHONY: analyze-performance
analyze-performance:
	$(call agent_header, "     AI AGENT TASK: Performance Analysis    ")
	@echo ""
	@echo "Gathering performance data..."
	@echo ""
	$(call agent_section, "BUNDLE SIZE ANALYSIS")
	@cd durable-code-app/frontend && npm run build 2>&1 | grep -E "(chunk|size)" || true
	@echo ""
	$(call agent_section, "BACKEND PROFILE")
	@echo "Key metrics to analyze:"
	@echo "- API response times"
	@echo "- Database query performance"
	@echo "- Memory usage patterns"
	@echo ""
	@echo "ANALYSIS INSTRUCTIONS:"
	@echo ""
	@echo "Please analyze and report on:"
	@echo ""
	@echo "1. FRONTEND PERFORMANCE:"
	@echo "   Component          | Issue | Impact | Solution"
	@echo "   ------------------|-------|--------|----------"
	@echo "   [Identify slow components and rendering issues]"
	@echo ""
	@echo "2. BACKEND PERFORMANCE:"
	@echo "   Endpoint          | Time  | Queries | Optimization"
	@echo "   ------------------|-------|---------|-------------"
	@echo "   [Identify slow endpoints and database issues]"
	@echo ""
	@echo "3. RECOMMENDATIONS:"
	@echo "   Priority | Area | Current | Proposed | Impact"
	@echo "   ---------|------|---------|----------|--------"
	@echo "   P0       | ...  | ...     | ...      | ..."
	@echo ""
	@echo "Use profiling tools:"
	@echo "- Frontend: React DevTools Profiler"
	@echo "- Backend: cProfile, memory_profiler"
```

2. **Add multi-stage deployment check**
```makefile
.PHONY: deploy-check
deploy-check:
	$(call agent_header, "     AI AGENT TASK: Deployment Readiness    ")
	@echo ""
	@echo "Running deployment checks..."
	@echo ""
	@echo "STAGE 1: Code Quality"
	@make lint-all > /tmp/lint.log 2>&1 && echo "✅ Linting passed" || echo "❌ Linting failed (see /tmp/lint.log)"
	@echo ""
	@echo "STAGE 2: Tests"
	@make test > /tmp/test.log 2>&1 && echo "✅ Tests passed" || echo "❌ Tests failed (see /tmp/test.log)"
	@echo ""
	@echo "STAGE 3: Security"
	@echo "⏳ Security checks needed"
	@echo ""
	@echo "STAGE 4: Documentation"
	@test -f CHANGELOG.md && echo "✅ Changelog exists" || echo "❌ Changelog missing"
	@echo ""
	@echo "DEPLOYMENT CHECKLIST FOR AI:"
	@echo ""
	@echo "□ All tests passing"
	@echo "□ No critical lint issues"
	@echo "□ Security vulnerabilities addressed"
	@echo "□ Documentation updated"
	@echo "□ CHANGELOG.md updated"
	@echo "□ Version bumped appropriately"
	@echo "□ Migration scripts ready (if needed)"
	@echo "□ Rollback plan documented"
	@echo ""
	@echo "If any checks failed, fix before deployment."
```

### Success Criteria
- [ ] Complex workflows broken into stages
- [ ] Clear progress indicators
- [ ] Structured output for AI parsing
- [ ] Actionable instructions

---

## PR5: Multi-Tool Validation

### Overview
Test the entire system with multiple AI tools to ensure universal compatibility.

### Testing Framework
```python
# test/ai-validation/test_compatibility.py
import subprocess
import json

test_scenarios = [
    {
        "name": "Basic Navigation",
        "command": "make ask-ai QUESTION='How to add API endpoint?'",
        "expected_elements": ["backend/app", "Pydantic", "template"]
    },
    {
        "name": "Code Review",
        "command": "make review-ai",
        "expected_elements": ["CODE QUALITY", "TESTING", "SECURITY"]
    },
    {
        "name": "Intelligent Fix",
        "command": "make fix-intelligent",
        "expected_elements": ["TEST FAILURES", "ITERATIVE PROCESS"]
    }
]

def test_ai_compatibility(ai_tool):
    results = []
    for scenario in test_scenarios:
        output = subprocess.check_output(scenario["command"], shell=True)
        success = all(elem in output for elem in scenario["expected_elements"])
        results.append({
            "tool": ai_tool,
            "scenario": scenario["name"],
            "success": success
        })
    return results
```

### Tools to Test
1. Claude (baseline)
2. GPT-4
3. GitHub Copilot
4. Cursor
5. Gemini (if available)

### Success Criteria
- [ ] 90%+ scenarios pass with all tools
- [ ] No tool-specific failures
- [ ] Clear compatibility matrix created

---

## PR6: Documentation & Training

### Overview
Finalize the migration with comprehensive documentation and team training.

### Documentation to Create

1. **Developer Guide** (`docs/AI_AGENT_GUIDE.md`)
```markdown
# AI Agent Development Guide

## Using the Agent-Agnostic System

### For Developers
1. All AI commands start with `make`
2. Run `make help-ai` to see available commands
3. Permissions are documented in AGENTS.md

### For AI Tools
- Claude: Full compatibility with make commands
- GPT-4: Use make commands as documented
- Copilot: Reference AGENTS.md for context
- Others: Follow AGENTS.md instructions

### Adding New Commands
To add a new agentic command:
1. Edit Makefile.agents
2. Follow the pattern of existing commands
3. Test with multiple AI tools
4. Document in AGENTS.md
```

2. **Migration Guide** (`docs/MIGRATION_FROM_CLAUDE.md`)
```markdown
# Migration from Claude-Specific System

## What's Changed
- `/ask` → `make ask-ai`
- `/review` → `make review-ai`
- `/fix` → `make fix-intelligent`
- Settings.json → AGENTS.md permissions

## Transition Period
Both systems work during migration:
- Claude users can still use slash commands
- New commands work with any AI

## Training Resources
- Video walkthrough: [link]
- Example sessions: [link]
- FAQ: [link]
```

### Team Training Plan
1. Introduction presentation (30 min)
2. Hands-on workshop (1 hour)
3. Q&A session (30 min)
4. Documentation review
5. Feedback collection

### Success Criteria
- [ ] All documentation complete
- [ ] Team trained on new system
- [ ] Feedback incorporated
- [ ] Old system deprecated gracefully

---

## Implementation Tips

### For Each PR
1. **Test Incrementally**: Verify each command works
2. **Document Changes**: Update AGENTS.md immediately
3. **Maintain Compatibility**: Both systems work during transition
4. **Gather Metrics**: Measure improvement

### Common Patterns

#### Agent Instruction Pattern
```makefile
command-name:
	@echo "=== AGENT TASK: [Task Name] ==="
	@echo "Gathering context..."
	@[gather context commands]
	@echo ""
	@echo "INSTRUCTIONS FOR AI:"
	@echo "[Structured instructions]"
	@echo ""
	@echo "EXPECTED OUTPUT:"
	@echo "[Format specification]"
```

#### Progressive Disclosure Pattern
```markdown
## Quick Command
`make fix` - Simple formatting fixes

## Intelligent Command
`make fix-intelligent` - AI-guided comprehensive fixing
- Analyzes test failures
- Understands root causes
- Fixes iteratively
```

### Testing Checklist
- [ ] Command works with Claude
- [ ] Command works with GPT-4
- [ ] Instructions are clear
- [ ] Output is structured
- [ ] No tool-specific dependencies

---

## Success Validation

After completing all PRs:

1. **Universal Compatibility**: Any AI can use the system
2. **No Lock-in**: No proprietary formats
3. **Improved DX**: Easier to discover and use
4. **Maintained Power**: Sophisticated features preserved
5. **Future-Proof**: Easy to extend and maintain