/**
 * Purpose: Configuration for Fundamental AI Principles
 * Scope: Centralized data structure for all AI principles
 * Overview: Defines principles with title, description, and example tags
 * Dependencies: None
 * Exports: principles array
 * Implementation: Simple data structure for extensibility
 */

export interface Principle {
  number: number;
  title: string;
  description: string;
  examples: string[];
}

export const principles: Principle[] = [
  {
    number: 1,
    title: 'Immediate Feedback Loops',
    description:
      'AI needs instant visibility into success or failure through logs, terminal output, test results, and error messages. Without immediate feedback, AI cannot self-correct or validate its actions.',
    examples: ['Terminal', 'Logs', 'Tests', 'Errors'],
  },
  {
    number: 2,
    title: 'Optimal Context',
    description:
      'AI needs contractor-level context to work effectively: database schemas, API docs, infrastructure setup, and architectural decisions. Provide comprehensive understanding without overwhelming with unnecessary details. The right context equals better output.',
    examples: ['Database Schema', 'API Docs', 'Infra Setup', 'Architecture'],
  },
  {
    number: 3,
    title: 'Clear Success Criteria',
    description:
      'Define explicit, measurable success conditions. AI performs best when it knows exactly what "done" looks like - passing tests, meeting performance benchmarks, or matching specifications.',
    examples: ['Tests Pass', 'No Lint Errors', 'Builds Clean', 'Meets Specs'],
  },
  {
    number: 4,
    title: 'Modular Task Decomposition',
    description:
      'Break complex problems into small, verifiable steps. AI excels at focused, well-defined tasks but struggles with ambiguous, open-ended requests. Think functions, not monoliths.',
    examples: ['Small PRs', 'Single Purpose', 'Testable Units', 'Clear Scope'],
  },
  {
    number: 5,
    title: 'Explicit Over Implicit',
    description:
      "State requirements explicitly. Don't assume AI will infer conventions, patterns, or constraints. Document your preferences, standards, and anti-patterns clearly.",
    examples: ['No Magic', 'Clear Rules', 'Examples', 'Constraints'],
  },
  {
    number: 6,
    title: 'Defensive Validation',
    description:
      'Always verify AI output through automated tests, linting, type checking, and builds. Never trust, always verify - use CI/CD pipelines to catch issues before they reach production.',
    examples: ['CI/CD', 'Type Safety', 'Linting', 'Reviews'],
  },
  {
    number: 7,
    title: 'Version Control Everything',
    description:
      'Track all changes in git with clear commit messages. This provides rollback capability, audit trails, and allows AI to understand project evolution and patterns.',
    examples: ['Git History', 'Commits', 'Branches', 'Tags'],
  },
  {
    number: 8,
    title: 'Living Documentation',
    description:
      'Treat documentation as code - keep it in the repo, version it, and update it with every change. AI relies on current, accurate docs to understand system behavior and constraints.',
    examples: ['README', 'API Docs', 'Comments', 'Examples'],
  },
  {
    number: 9,
    title: 'Lightweight Look-ups',
    description:
      'Provide quick-access indices and metadata that AI can rapidly parse. Tables of contents, file headers, and structured navigation enable efficient codebase understanding without excessive context consumption.',
    examples: ['.ai/index.json', 'File Headers', 'TOC', 'Metadata'],
  },
];
