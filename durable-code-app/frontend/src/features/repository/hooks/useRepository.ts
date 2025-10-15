/**
 * Purpose: Custom hook for managing repository feature data and state
 * Scope: Repository tab data provider with error handling and loading states
 * Overview: React hook that provides all repository-related data including
 *     repository items, folder structure, make targets, stats, and action links.
 *     Handles loading states and error management for the repository feature.
 * Dependencies: React (useState, useEffect, useMemo), repository types
 * Exports: useRepository hook function
 * Props/Interfaces: No parameters, returns UseRepositoryReturn interface
 * State/Behavior: Manages loading state, error state, and static data provision
 */

import { useEffect, useMemo, useState } from 'react';
import type {
  ActionLink,
  FolderItem,
  MakeTarget,
  RepositoryItem,
  RepositoryStats,
  UseRepositoryReturn,
} from '../types/repository.types';

export function useRepository(): UseRepositoryReturn {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  // Repository items data
  const repositoryItems = useMemo(
    (): RepositoryItem[] => [
      {
        id: 'project-layout',
        icon: '📐',
        title: 'Tell AI Where to Put Things',
        badge: 'Foundation',
        category: 'structure',
        popup: {
          problem: {
            title: 'AI Creates Files Anywhere',
            points: [
              'AI puts test files in source directories',
              'Creates temporary files that pollute the codebase',
              'Mixes frontend and backend technologies',
              'Ignores project structure conventions',
              'Creates duplicate functionality in wrong places',
            ],
          },
          solution: {
            title: 'Enforced Layout Rules',
            points: [
              'Define allowed file patterns per directory',
              'Specify forbidden patterns explicitly',
              'Automated validation catches violations',
              'AI gets immediate feedback on wrong placement',
              'Consistent structure across entire codebase',
            ],
          },
          example: {
            title: 'layout.yaml - Backend Structure Rules',
            language: 'yaml',
            code: `backend:
  allowed_patterns:
    - "app/**/*.py"          # Python modules only in app/
    - "tests/**/*_test.py"   # Tests follow naming convention
    - "alembic/versions/*.py" # Database migrations
  forbidden_patterns:
    - "**/*.js"              # No JavaScript in backend
    - "**/temp_*.py"         # No temporary files
    - "app/**/test_*.py"     # Tests go in tests/, not app/`,
            file: '.ai/layout.yaml',
          },
          links: [
            {
              text: 'View Full Layout Config',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.ai/layout.yaml',
            },
          ],
        },
      },
      {
        id: 'custom-linters',
        icon: '🔧',
        title: 'Gate Everything You Care About',
        badge: 'Critical',
        category: 'quality',
        popup: {
          problem: {
            title: 'Standard Linters Miss Your Issues',
            points: [
              "ESLint/Pylint don't know YOUR business logic",
              "Can't enforce architectural decisions",
              'Miss project-specific antipatterns',
              'No way to enforce team conventions',
              'AI repeats the same mistakes',
            ],
          },
          solution: {
            title: 'Custom Rules for Your Project',
            points: [
              'Build linters for YOUR specific needs',
              'Enforce SOLID principles automatically',
              'Block project-specific bad patterns',
              'Gate security vulnerabilities you care about',
              'Extensible framework for new rules',
            ],
          },
          example: {
            title: 'Custom Rule: Block Print Statements',
            language: 'python',
            code: `class NoPrintStatementsRule(LinterRule):
    """Prevents print() statements in production code"""

    def check(self, context: LintContext) -> List[LintViolation]:
        violations = []
        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                if getattr(node.func, 'id', None) == 'print':
                    violations.append(LintViolation(
                        line=node.lineno,
                        message="print() not allowed - use logger",
                        severity="error"
                    ))
        return violations`,
            file: 'tools/design_linters/rules/no_print.py',
          },
          links: [
            {
              text: 'Explore Linting Framework',
              url: 'https://github.com/steve-e-jackson/durable-code-test/tree/main/tools/design_linters',
            },
          ],
        },
      },
      {
        id: 'make-targets',
        icon: '⚙️',
        title: 'Make It Work The Same Everywhere',
        badge: 'Critical',
        category: 'automation',
        popup: {
          problem: {
            title: 'AI is Non-Deterministic by Nature',
            points: [
              'AI suggests different commands each time',
              'One day: "npm test", next day: "yarn test:unit"',
              'Invents creative new ways to run same task',
              'Each approach might work... or might not',
              'Compounds environment differences with variation',
            ],
          },
          solution: {
            title: 'Deterministic Targets for AI to Call',
            points: [
              'Tell AI: "Always use make test" - nothing else',
              'Single command that works identically everywhere',
              'Docker ensures same environment every time',
              "AI can't introduce variation when target is fixed",
              'Predictable commands = predictable results',
            ],
          },
          example: {
            title: 'Deterministic Test Target',
            language: 'makefile',
            code: `test-backend: docker-check
	@echo "Running backend tests in Docker..."
	docker-compose -f docker-compose.test.yml run \\
		--rm \\
		-e PYTHONPATH=/app \\
		-e PYTEST_ARGS="-xvs" \\
		backend-test \\
		pytest $$PYTEST_ARGS --cov=app --cov-report=term
	@echo "✅ Backend tests passed"`,
            file: 'Makefile.test',
          },
          links: [
            {
              text: 'View All Make Targets',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/Makefile',
            },
          ],
        },
      },
      {
        id: 'docker-everything',
        icon: '🐳',
        title: 'Lock Down Every Version',
        badge: 'Foundation',
        category: 'infrastructure',
        popup: {
          problem: {
            title: 'AI Always Reaches for "Latest"',
            points: [
              'AI suggests "pip install package" without versions',
              'Uses latest syntax that breaks older systems',
              'Mixes modern and legacy API patterns',
              "Assumes features that don't exist in your versions",
              'Generated code works today, breaks tomorrow when packages update',
            ],
          },
          solution: {
            title: 'Force AI Into Your Exact Environment',
            points: [
              'AI reads your lock files and respects them',
              "Can't suggest packages outside your dependencies",
              "Generated code matches YOUR version's syntax",
              'Test AI changes in identical environment immediately',
              'When AI code works once, it works forever',
            ],
          },
          example: {
            title: 'Pinned Versions in Docker',
            language: 'yaml',
            code: `services:
  backend:
    image: python:3.11.7-slim  # Exact Python version
    environment:
      - POETRY_VERSION=1.7.0   # Exact Poetry version
    volumes:
      - ./poetry.lock:/app/poetry.lock:ro  # Lock file
    command: |
      sh -c "pip install poetry==1.7.0 &&
             poetry install --no-root --only main"`,
            file: 'docker-compose.yml',
          },
          links: [
            {
              text: 'View Docker Configuration',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/docker-compose.yml',
            },
          ],
        },
      },
      {
        id: 'quality-gates',
        icon: '🔒',
        title: 'Stop Bad Code at Every Stage',
        badge: 'Critical',
        category: 'quality',
        popup: {
          problem: {
            title: 'Single Checkpoints Always Fail',
            points: [
              'Developer forgets to run tests locally',
              'CI/CD catches issues too late',
              'Bad code gets merged during review',
              'Production breaks from accumulated debt',
              'AI bypasses human review processes',
            ],
          },
          solution: {
            title: 'Defense in Depth Strategy',
            points: [
              'Pre-commit hooks catch issues before commit',
              'CI/CD validates every push automatically',
              'Branch protection enforces all checks pass',
              'Multiple layers mean multiple chances to catch bugs',
              'AI code goes through same rigorous pipeline',
            ],
          },
          example: {
            title: 'Multi-Layer Defense Configuration',
            language: 'yaml',
            code: `# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: no-print-statements
        name: Block print/console.log
        entry: 'print(|console.'
        language: pygrep
        types: [python, javascript, typescript]

      - id: design-linters
        name: Custom Design Linters
        entry: make lint-custom
        language: system
        always_run: true`,
            file: '.pre-commit-config.yaml',
          },
          links: [
            {
              text: 'View Pre-commit Config',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.pre-commit-config.yaml',
            },
          ],
        },
      },
      {
        id: 'step-by-step',
        icon: '📚',
        title: 'Step-by-Step How-To Guides',
        badge: 'Essential',
        category: 'documentation',
        popup: {
          problem: {
            title: 'AI Invents Its Own Workflows',
            points: [
              'Different approach every time for same task',
              'Skips critical steps in processes',
              'Uses deprecated or dangerous commands',
              'No consistency across team members',
              'Reinvents the wheel repeatedly',
            ],
          },
          solution: {
            title: 'Documented Step-by-Step Procedures',
            points: [
              'Exact commands for every common task',
              'Consistent workflow across all users',
              'AI follows proven procedures',
              'New team members onboard quickly',
              'Reduces cognitive load and mistakes',
            ],
          },
          example: {
            title: 'How-To: Debug Failing Tests',
            language: 'markdown',
            code: `## Debug Failing Tests

1. **Identify the failing test:**
   \`\`\`bash
   make test 2>&1 | grep FAILED
   \`\`\`

2. **Run single test with verbose output:**
   \`\`\`bash
   make test PYTEST_ARGS="-xvs -k test_name"
   \`\`\`

3. **Check test logs:**
   \`\`\`bash
   docker logs durable-code-backend-test
   \`\`\``,
            file: '.ai/howto/debug-tests.md',
          },
          links: [
            {
              text: 'Browse How-To Guides',
              url: 'https://github.com/steve-e-jackson/durable-code-test/tree/main/.ai/howto',
            },
          ],
        },
      },
      {
        id: 'file-headers',
        icon: '📋',
        title: 'Make Every File Self-Documenting',
        badge: 'Foundation',
        category: 'documentation',
        popup: {
          problem: {
            title: 'AI Needs Context But Gets Overwhelmed',
            points: [
              'Loading entire codebases wastes tokens and slows decisions',
              'Without context, AI makes wrong assumptions about dependencies',
              'No quick way to understand file purpose and exports',
              'Scope and responsibility remain unclear',
              'Too much information is as bad as too little',
            ],
          },
          solution: {
            title: 'Optimal Context Through Structured Headers',
            points: [
              'Contractor-level understanding without the noise',
              'Purpose and scope stated upfront',
              'Dependencies and exports explicitly documented',
              'Comprehensive detail in minimal tokens',
              "AI gets depth it needs, not data it doesn't",
            ],
          },
          example: {
            title: 'Required File Header Format',
            language: 'typescript',
            code: `/**
 * Purpose: Custom hook for managing infrastructure data
 * Scope: Infrastructure tab data provider with error handling
 * Overview: React hook providing infrastructure items,
 *     folder structure, make targets, and stats.
 *     Handles loading states and error management.
 * Dependencies: React (useState, useEffect), types
 * Exports: useInfrastructure hook function
 * Props/Interfaces: Returns UseInfrastructureReturn
 * State/Behavior: Manages loading, error, and data states
 */`,
            file: 'Every TypeScript/JavaScript file',
          },
          links: [
            {
              text: 'File Header Standards',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.ai/docs/FILE_HEADER_STANDARDS.md',
            },
          ],
        },
      },
      {
        id: 'ai-index',
        icon: '🤖',
        title: 'Give AI a Map of Your Code',
        badge: 'Critical',
        category: 'ai',
        popup: {
          problem: {
            title: 'AI Gets Lost in Large Codebases',
            points: [
              'Wastes tokens reading irrelevant files',
              "Can't find the right module quickly",
              "Doesn't know where features live",
              'Misses important configuration files',
              'Makes changes in wrong locations',
            ],
          },
          solution: {
            title: 'Structured Navigation Index',
            points: [
              'Single file maps entire project structure',
              'Lists all key commands and their purposes',
              'Points to feature documentation',
              'Provides optimal context - comprehensive yet efficient',
              'AI navigates like experienced developer',
            ],
          },
          example: {
            title: 'AI Navigation Index',
            language: 'yaml',
            code: `project:
  name: durable-code-test
  structure:
    backend:
      location: durable-code-app/backend
      entry: app/main.py
      tests: tests/
    frontend:
      location: durable-code-app/frontend
      entry: src/main.tsx

commands:
  test: "make test-all"
  lint: "make lint-all"
  dev: "make dev"`,
            file: '.ai/index.yaml',
          },
          links: [
            {
              text: 'View Full Index',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.ai/index.yaml',
            },
          ],
        },
      },
      {
        id: 'test-infrastructure',
        icon: '🧪',
        title: 'Test Everything, Trust Nothing',
        badge: 'Critical',
        category: 'testing',
        popup: {
          problem: {
            title: 'AI Writes Happy Path Code',
            points: [
              'Only tests the success case',
              'Forgets edge cases and error conditions',
              'No validation for malicious input',
              "Doesn't test integration between components",
              'Changes break unrelated features silently',
            ],
          },
          solution: {
            title: 'Comprehensive Test Coverage',
            points: [
              'Parameterized tests for all edge cases',
              'Test the unhappy paths - errors, timeouts, bad data',
              'Integration tests verify components work together',
              'Regression tests catch breaking changes',
              'All tests run in Docker for consistency',
            ],
          },
          example: {
            title: 'Parameterized Edge Case Testing',
            language: 'python',
            code: `@pytest.mark.parametrize("input,expected", [
    (None, ValidationError),
    ("", ValidationError),
    ("valid_input", Success),
    ("x" * 1001, ValidationError),  # Max length
    ("<script>", ValidationError),   # XSS attempt
    ("'; DROP TABLE;", Success),    # SQL injection
])
def test_input_validation(input, expected):
    """Test all edge cases AI might miss"""
    if expected == ValidationError:
        with pytest.raises(ValidationError):
            validate_user_input(input)
    else:
        assert validate_user_input(input) is not None`,
            file: 'tests/test_validation.py',
          },
          links: [
            {
              text: 'Testing Infrastructure',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/Makefile.test',
            },
          ],
        },
      },
      {
        id: 'code-templates',
        icon: '📝',
        title: 'Start from Proven Patterns',
        badge: 'Important',
        category: 'ai',
        popup: {
          problem: {
            title: 'AI Reinvents Patterns Incorrectly',
            points: [
              'Creates components missing error handling',
              'Forgets loading states and edge cases',
              'Inconsistent patterns across codebase',
              'Violates established conventions',
              'Generates boilerplate with subtle bugs',
            ],
          },
          solution: {
            title: 'Production-Ready Templates',
            points: [
              'Battle-tested code patterns',
              'All edge cases handled by default',
              'Consistent structure across components',
              'Best practices baked in',
              'AI fills in specifics, not structure',
            ],
          },
          example: {
            title: 'React Component Template',
            language: 'typescript',
            code: `export function \${COMPONENT}({\n  className = '',\n  onError,\n}: \${COMPONENT}Props): ReactElement {\n  const [loading, setLoading] = useState(false);\n  const [error, setError] = useState<Error | null>(null);\n  \n  // Error propagation\n  if (error) onError?.(error);\n  \n  if (loading) return <LoadingSpinner />;\n  if (error) return <ErrorMessage message={error.message} />;\n  \n  return (\n    <div className={className}>\n      {/* Component content */}\n    </div>\n  );\n}`,
            file: '.ai/templates/react-component.tsx.template',
          },
          links: [
            {
              text: 'Browse Templates',
              url: 'https://github.com/steve-e-jackson/durable-code-test/tree/main/.ai/templates',
            },
          ],
        },
      },
      {
        id: 'error-resilience',
        icon: '🛡️',
        title: 'Handle Errors Like Production',
        badge: 'Critical',
        category: 'resilience',
        popup: {
          problem: {
            title: 'AI Writes Happy Path Code',
            points: [
              'Generated code assumes everything will work',
              'No handling for network failures, timeouts, or API errors',
              'Catches broad exceptions that hide real problems',
              'No retry logic for transient failures',
              'Silent failures that corrupt data or lose user work',
            ],
          },
          solution: {
            title: 'Production-Grade Error Resilience',
            points: [
              'Structured exception hierarchy with specific error types',
              'Automatic retry with exponential backoff for transient errors',
              'Circuit breakers prevent cascading failures',
              'Proper logging at every error boundary',
              'Graceful degradation instead of complete failure',
            ],
          },
          example: {
            title: 'Retry with Exponential Backoff',
            language: 'python',
            code: `@with_retry(\n    max_attempts=3,\n    backoff_factor=2.0,\n    exceptions=(TimeoutError, ConnectionError)\n)\nasync def call_external_api(url: str):\n    """Auto-retry on transient failures"""\n    try:\n        response = await http_client.get(url, timeout=5)\n        return response.json()\n    except (TimeoutError, ConnectionError) as e:\n        logger.warning(f"Transient error: {e}")\n        raise  # Retry decorator handles this\n    except Exception as e:\n        logger.error(f"Permanent failure: {e}")\n        raise AppException(\n            message="External API unavailable",\n            code="API_ERROR",\n            status_code=503\n        )`,
            file: 'app/core/retry.py',
          },
          links: [
            {
              text: 'Exception Hierarchy',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/durable-code-app/backend/app/core/exceptions.py',
            },
            {
              text: 'Retry Implementation',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/durable-code-app/backend/app/core/retry.py',
            },
          ],
        },
      },
      {
        id: 'resource-naming',
        icon: '🏷️',
        title: 'Name Resources So AI Can Find Them',
        badge: 'Important',
        category: 'infrastructure',
        popup: {
          problem: {
            title: 'AI Creates Inconsistently Named Resources',
            points: [
              'Each conversation creates different naming patterns',
              'Cannot identify which resources belong to which service',
              'Impossible to calculate costs per product or environment',
              'AI searches for wrong names when looking for existing resources',
              'Manual cleanup required to identify orphaned resources',
            ],
          },
          solution: {
            title: 'Enforced Naming Conventions',
            points: [
              'Standard pattern: {product}-{env}-{type}-{name}',
              'Required tags on all resources for identification',
              'AI always follows same naming pattern',
              'Cost tracking by product domain or environment',
              'Easy search and cleanup of related resources',
            ],
          },
          example: {
            title: 'Terraform Resource Naming Standard',
            language: 'hcl',
            code: `# Pattern: {product-domain}-{environment}-{resource-type}
resource "aws_s3_bucket" "main" {
  bucket = "durableai-\${var.environment}-assets"

  tags = {
    ProductDomain = "durableai"
    Environment   = var.environment
    ManagedBy     = "terraform"
    CostCenter    = "engineering"
  }
}`,
            file: '.ai/docs/TERRAFORM_STANDARDS.md',
          },
          links: [
            {
              text: 'View Terraform Standards',
              url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.ai/docs/TERRAFORM_STANDARDS.md',
            },
          ],
        },
      },
    ],
    [],
  );

  // Folder structure data
  const folderStructure = useMemo(
    (): FolderItem[] => [
      {
        id: 'ai-root',
        type: 'folder',
        name: '.ai/',
        icon: '📦',
        depth: 0,
      },
      {
        id: 'index-json',
        type: 'file',
        name: 'index.json',
        icon: '📋',
        description: 'Quick navigation for AI agents',
        depth: 1,
      },
      {
        id: 'index-expanded',
        type: 'file',
        name: 'index_expanded.md',
        icon: '📄',
        description: 'Comprehensive AI documentation',
        depth: 1,
      },
      {
        id: 'docs-folder',
        type: 'folder',
        name: 'docs/',
        icon: '📁',
        description: 'Development standards',
        depth: 1,
      },
      {
        id: 'standards-md',
        type: 'file',
        name: 'STANDARDS.md',
        icon: '📝',
        depth: 2,
      },
      {
        id: 'file-header-standards',
        type: 'file',
        name: 'FILE_HEADER_STANDARDS.md',
        icon: '📝',
        depth: 2,
      },
      {
        id: 'css-layout',
        type: 'file',
        name: 'CSS_LAYOUT_STABILITY.md',
        icon: '📝',
        depth: 2,
      },
      {
        id: 'branch-protection',
        type: 'file',
        name: 'BRANCH_PROTECTION.md',
        icon: '📝',
        depth: 2,
        isLast: true,
      },
      {
        id: 'features-folder',
        type: 'folder',
        name: 'features/',
        icon: '📁',
        description: 'Feature documentation',
        depth: 1,
      },
      {
        id: 'design-linters-md',
        type: 'file',
        name: 'design-linters.md',
        icon: '🔧',
        depth: 2,
      },
      {
        id: 'web-application-md',
        type: 'file',
        name: 'web-application.md',
        icon: '🌐',
        depth: 2,
      },
      {
        id: 'development-tooling-md',
        type: 'file',
        name: 'development-tooling.md',
        icon: '⚙️',
        depth: 2,
      },
      {
        id: 'claude-integration-md',
        type: 'file',
        name: 'claude-integration.md',
        icon: '🤖',
        depth: 2,
      },
      {
        id: 'testing-framework-md',
        type: 'file',
        name: 'testing-framework.md',
        icon: '🧪',
        depth: 2,
        isLast: true,
      },
      {
        id: 'howto-folder',
        type: 'folder',
        name: 'howto/',
        icon: '📚',
        description: 'Exact steps for every task',
        depth: 1,
      },
      {
        id: 'run-tests-md',
        type: 'file',
        name: 'run-tests.md',
        icon: '🧪',
        description: 'Step-by-step testing guide',
        depth: 2,
      },
      {
        id: 'run-linting-md',
        type: 'file',
        name: 'run-linting.md',
        icon: '🔍',
        description: 'How to run all linters',
        depth: 2,
      },
      {
        id: 'setup-development-md',
        type: 'file',
        name: 'setup-development.md',
        icon: '🛠️',
        description: 'Environment setup walkthrough',
        depth: 2,
      },
      {
        id: 'deploy-application-md',
        type: 'file',
        name: 'deploy-application.md',
        icon: '🚀',
        description: 'Production deployment steps',
        depth: 2,
      },
      {
        id: 'debug-issues-md',
        type: 'file',
        name: 'debug-issues.md',
        icon: '🐛',
        description: 'Troubleshooting guide',
        depth: 2,
      },
      {
        id: 'add-new-feature-md',
        type: 'file',
        name: 'add-new-feature.md',
        icon: '✨',
        description: 'Feature implementation process',
        depth: 2,
      },
      {
        id: 'fix-failing-tests-md',
        type: 'file',
        name: 'fix-failing-tests.md',
        icon: '🔧',
        description: 'Test debugging walkthrough',
        depth: 2,
        isLast: true,
      },
      {
        id: 'templates-folder',
        type: 'folder',
        name: 'templates/',
        icon: '📁',
        description: 'Production-ready templates',
        depth: 1,
        isLast: true,
      },
      {
        id: 'linting-rule-template',
        type: 'file',
        name: 'linting-rule.py.template',
        icon: '🔧',
        depth: 2,
        parentIsLast: true,
      },
      {
        id: 'react-component-template',
        type: 'file',
        name: 'react-component.tsx.template',
        icon: '⚛️',
        depth: 2,
        parentIsLast: true,
      },
      {
        id: 'web-tab-template',
        type: 'file',
        name: 'web-tab.tsx.template',
        icon: '📑',
        depth: 2,
        parentIsLast: true,
      },
      {
        id: 'fastapi-endpoint-template',
        type: 'file',
        name: 'fastapi-endpoint.py.template',
        icon: '🌐',
        depth: 2,
        parentIsLast: true,
      },
      {
        id: 'test-suite-template',
        type: 'file',
        name: 'test-suite.py.template',
        icon: '🧪',
        depth: 2,
        parentIsLast: true,
      },
      {
        id: 'workflow-template',
        type: 'file',
        name: 'workflow.html.template',
        icon: '📊',
        depth: 2,
        isLast: true,
        parentIsLast: true,
      },
    ],
    [],
  );

  // Make targets data
  const makeTargets = useMemo(
    (): MakeTarget[] => [
      {
        name: 'test',
        icon: '🧪',
        description: 'Same tests, same environment, every time',
        category: 'testing',
        importance: 'critical',
      },
      {
        name: 'lint-all',
        icon: '🔍',
        description: 'Consistent quality checks across machines',
        category: 'linting',
        importance: 'critical',
      },
      {
        name: 'build',
        icon: '🏗️',
        description: 'Identical builds from identical inputs',
        category: 'building',
        importance: 'critical',
      },
      {
        name: 'deploy',
        icon: '🚀',
        description: 'Predictable deployment every time',
        category: 'deployment',
        importance: 'important',
      },
      {
        name: 'setup',
        icon: '🔧',
        description: 'Environment setup: deterministic',
        category: 'deployment',
        importance: 'important',
      },
      {
        name: 'validate',
        icon: '📊',
        description: 'Quality gates with known outcomes',
        category: 'testing',
        importance: 'important',
      },
      {
        name: 'clean',
        icon: '🧹',
        description: 'Reset to known clean state',
        category: 'maintenance',
        importance: 'utility',
      },
      {
        name: 'format',
        icon: '📋',
        description: 'Code formatting: same result always',
        category: 'linting',
        importance: 'utility',
      },
      {
        name: 'security-scan',
        icon: '🔒',
        description: 'Reproducible security analysis',
        category: 'testing',
        importance: 'important',
      },
      {
        name: 'benchmark',
        icon: '📈',
        description: 'Performance metrics: consistent baseline',
        category: 'testing',
        importance: 'utility',
      },
    ],
    [],
  );

  // Stats data
  const stats = useMemo(
    (): RepositoryStats => ({
      makeTargets: 40,
      linterCategories: 5,
      codeTemplates: 6,
      dockerCoverage: '100%',
    }),
    [],
  );

  // Action links data
  const actionLinks = useMemo(
    (): ActionLink[] => [
      {
        id: 'ai-repository',
        url: 'https://github.com/steve-e-jackson/durable-code-test/tree/main/.ai',
        text: 'Explore .ai Repository',
        icon: '📂',
        type: 'primary',
        description: 'Browse the AI documentation structure',
      },
      {
        id: 'make-targets',
        url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/Makefile.lint',
        text: 'View Make Targets',
        icon: '🔧',
        type: 'secondary',
        description: 'See automation targets in action',
      },
      {
        id: 'custom-linters',
        url: 'https://github.com/steve-e-jackson/durable-code-test/tree/main/tools/design_linters',
        text: 'Custom Linters',
        icon: '🎯',
        type: 'secondary',
        description: 'Explore the linting framework',
      },
      {
        id: 'precommit-config',
        url: 'https://github.com/steve-e-jackson/durable-code-test/blob/main/.pre-commit-config.yaml',
        text: 'Pre-commit Config',
        icon: '🔒',
        type: 'secondary',
        description: 'See quality gates configuration',
      },
    ],
    [],
  );

  // Simulate loading effect
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Simulate brief loading for realistic UX
        await new Promise((resolve) => setTimeout(resolve, 100));

        setLoading(false);
      } catch (err) {
        const error =
          err instanceof Error ? err : new Error('Failed to load infrastructure data');
        setError(error);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return {
    repositoryItems,
    folderStructure,
    makeTargets,
    stats,
    actionLinks,
    loading,
    error,
  };
}
