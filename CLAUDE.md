- The very first response you should have to any prompt is to read AGENTS.md

- Don't run tests locally, always used docker or make
- Run all linting via make targets don't call linting directly.
- Always prefer makefile targets for terraform operations.
# Trigger CI rebuild - logging fixes applied
- Never create anything, not one single thing, on the main branch.
- Nevery bypass or skip pre commit hooks. They must be made to pass.
- When creating a PR always check for un-commited code, don't leave anything behind.
- Always use make targets for terraform operation when available.
- NEVER force unlock Terraform state without explicit user permission. State locks protect against corruption and concurrent modifications.
- NEVER run npm install locally. Always update package.json and rebuild Docker containers.
- All package installations must be done within Docker containers, not on the host system.
- All linting should be run through docker

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

# Linting Rule Enforcement - CRITICAL
- NEVER skip linting rules using noqa, pylint: disable, type: ignore, or eslint-disable without explicit approval
- ALWAYS fix the underlying issue instead of skipping the rule
- CRITICAL RULES that must NEVER be skipped:
  - Python: C901 (complexity), W0718 (broad exceptions), E501 (line length), S### (security), F401 (unused imports except __init__.py)
  - TypeScript: no-explicit-any, react-hooks/exhaustive-deps, react-hooks/rules-of-hooks, no-console
  - Infrastructure: terraform validate errors, shellcheck warnings
- If a linting rule is firing, FIX the code - don't skip the rule
- The enforcement.no-skip linting rule will automatically catch and block attempts to skip critical rules
- See .ai/docs/LINTING_ENFORCEMENT_STANDARDS.md for complete guidance on fixing vs skipping
- run formatting and linting through docker or make targets, do not use nmp run format or npm run lint.