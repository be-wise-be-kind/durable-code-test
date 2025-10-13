# React Frontend Upgrade - AI Agent Context

**Purpose**: AI agent context document for React frontend upgrade transforming poorly structured code into professional, maintainable application

**Scope**: Complete frontend architecture transformation from functional demo code to production-quality React application following industry best practices

**Overview**: Comprehensive context document for AI agents working on React frontend upgrade project. Addresses
    critical code quality issues including monolithic components, missing error boundaries, performance problems,
    and architectural deficiencies. Provides target architecture with feature-based organization, proper state
    management, comprehensive testing strategies, and performance optimization. Includes specific implementation
    guidance, technical decisions, success criteria, and development workflow for systematic transformation
    to production-ready application.

**Dependencies**: React 19, TypeScript 5.8, Vite 7.1, Vitest 3.2, Zustand, TanStack Query, CSS Modules, testing frameworks

**Exports**: Frontend architecture patterns, implementation strategies, testing approaches, and development workflow guidance

**Related**: PR breakdown documents for implementation phases, testing strategies, performance optimization guidelines

**Implementation**: Phased upgrade approach with atomic PRs, comprehensive testing, and systematic architecture improvement

---

## Project Overview
**Repository**: durable-code-test
**Location**: `/home/stevejackson/Projects/durable-code-test/durable-code-app/frontend`
**Current Stack**: React 19.1.1, TypeScript 5.8.3, Vite 7.1.2, Vitest 3.2.4
**Objective**: Transform the frontend from functional but poorly structured code into a professional, maintainable React application following industry best practices.

## Current State Analysis

### File Structure (Current - Problematic)
```
durable-code-app/frontend/src/
├── App.tsx (409 lines - monolithic)
├── App.css (1000+ lines)
├── App.test.tsx
├── main.tsx
├── components/
│   ├── ParticleBackground.tsx
│   └── tabs/
│       ├── InfrastructureTab.tsx
│       ├── PlanningTab.tsx
│       ├── BuildingTab.tsx
│       ├── QualityAssuranceTab.tsx
│       ├── MaintenanceTab.tsx
│       └── DemoTab.tsx (707 lines - monolithic)
├── pages/
│   ├── Standards.tsx
│   └── CustomLinters.tsx
└── utils/
    ├── HttpRequestService.ts
    ├── LinkExtractionService.ts
    ├── LinkCategorizationService.ts
    ├── LinkValidationService.ts
    ├── LinkReportService.ts
    ├── LinkRegistryInterfaces.ts
    ├── ParticleSystem.ts
    └── link-validator.ts
```

### Critical Issues Identified

1. **Architecture Problems**
   - No clear separation of concerns
   - Business logic mixed with presentation
   - No state management solution
   - Flat component structure
   - Missing abstraction layers

2. **Code Quality Issues**
   - Monolithic components (App.tsx: 409 lines, DemoTab: 707 lines)
   - Inline styles mixed with CSS files
   - No consistent patterns
   - Missing TypeScript strict mode
   - No error boundaries or loading states

3. **Performance Issues**
   - No memoization
   - No lazy loading
   - No code splitting
   - Unnecessary re-renders
   - Large bundle size

4. **Testing Gaps**
   - Only 3 test files
   - No integration tests
   - No E2E tests
   - No visual regression testing
   - Low coverage

5. **Developer Experience**
   - No component documentation
   - No Storybook
   - Inconsistent code style
   - No component generators
   - Poor folder structure

## Target Architecture

### Desired File Structure
```
src/
├── app/                    # App-level components and config
│   ├── App.tsx            # Main app component (thin)
│   ├── AppProviders.tsx   # All context providers
│   └── AppRouter.tsx      # Route configuration
├── components/            # Shared UI components
│   ├── common/           # Button, Card, Modal, etc.
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.module.css
│   │   │   ├── Button.test.tsx
│   │   │   └── Button.stories.tsx
│   │   └── [other components...]
│   ├── layout/           # Header, Footer, Navigation
│   └── particles/        # ParticleBackground
├── features/             # Feature-based modules
│   ├── infrastructure/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── planning/
│   ├── building/
│   ├── quality/
│   ├── maintenance/
│   └── demo/
│       ├── components/
│       │   ├── Oscilloscope/
│       │   ├── ControlPanel/
│       │   └── WaveformControls/
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   └── useOscilloscope.ts
│       └── services/
├── hooks/                # Global custom hooks
├── services/            # API clients and utilities
├── store/              # State management (Zustand)
├── styles/             # Global styles and theme
├── types/              # Global TypeScript types
└── utils/              # Helper functions
```

## Technical Decisions

### Core Libraries
- **State Management**: Zustand (lightweight, TypeScript-friendly)
- **Data Fetching**: TanStack Query (React Query)
- **Styling**: CSS Modules + CSS Variables for theming
- **Testing**: Vitest + React Testing Library + Playwright
- **Documentation**: Storybook 8
- **Forms**: React Hook Form + Zod
- **Routing**: React Router v7 (already in use)

### Coding Standards
- **Component Size**: Max 200 lines
- **File Organization**: Co-located tests and stories
- **Naming**: PascalCase for components, camelCase for utilities
- **Exports**: Named exports for components
- **Props**: Interface definitions with JSDoc
- **State**: Prefer hooks and composition
- **Performance**: Memo by default for pure components

### TypeScript Configuration
```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@features/*": ["./src/features/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@services/*": ["./src/services/*"],
      "@store/*": ["./src/store/*"],
      "@utils/*": ["./src/utils/*"],
      "@types/*": ["./src/types/*"]
    }
  }
}
```

## Success Criteria

### Must Have
- ✅ Clean architecture with feature-based organization
- ✅ All components < 200 lines
- ✅ TypeScript strict mode enabled
- ✅ 80%+ test coverage
- ✅ All critical paths have E2E tests
- ✅ Storybook with all components documented
- ✅ Zero console errors/warnings
- ✅ Lighthouse score > 95
- ✅ WCAG 2.1 AA compliant

### Nice to Have
- ✅ Component generator CLI
- ✅ Visual regression testing
- ✅ Bundle size < 200KB gzipped
- ✅ Perfect TypeScript coverage
- ✅ Automated dependency updates

## Development Workflow

### For Each PR
1. Create feature branch from main
2. Implement changes following the plan
3. Write/update tests (maintain coverage)
4. Update Storybook stories
5. Run linting and type checking
6. Ensure app still builds and runs
7. Create PR with detailed description
8. Merge only after all checks pass

### Commands to Know
```bash
# Development
make dev                # Start development server
npm run dev            # Alternative: direct npm command

# Testing
make test              # Run all tests
npm run test:coverage  # Check coverage
npm run test:watch    # Watch mode

# Linting
make lint-all         # Run all linters
npm run lint:fix      # Fix linting issues
npm run typecheck     # TypeScript checking

# Building
make build            # Production build
npm run build         # Alternative: direct npm command
```

## Important Context for AI

### Project Constraints
- Must maintain compatibility with existing backend
- Must preserve all current functionality
- Cannot break existing Make targets
- Must follow project's CLAUDE.md guidelines:
  - Don't run tests locally, use docker or make
  - Run linting via make targets, not directly
  - Never push to develop branch

### Existing Patterns to Preserve
- Tab-based navigation with URL hash sync
- Return parameter for navigation
- Particle background animation
- WebSocket connection for demo oscilloscope
- External and internal link handling

### Files to Reference
- `/home/stevejackson/Projects/durable-code-test/.ai/index.json` - AI navigation
- `/home/stevejackson/Projects/durable-code-test/.ai/templates/react-component.tsx.template` - Component template
- `/home/stevejackson/Projects/durable-code-test/.ai/docs/STANDARDS.md` - Coding standards
- `/home/stevejackson/Projects/durable-code-test/CLAUDE.md` - AI-specific rules

## Risk Mitigation

### Potential Issues
1. **Breaking Changes**: Each PR must leave app functional
2. **State Management Migration**: Gradual adoption, not big bang
3. **CSS Conflicts**: Namespace all new styles
4. **Testing Coverage**: Never let it drop below current level
5. **Bundle Size**: Monitor with each PR

### Rollback Strategy
- Each PR is atomic and revertible
- Feature flags for major changes
- Maintain backwards compatibility
- Keep old components until new ones proven

## Communication

### PR Description Template
```markdown
## PR Title: [PR#X] Feature: Description

### Context
[Link to this document and specific PR section]

### Changes
- List of specific changes
- File moves/renames
- New dependencies

### Testing
- [ ] Unit tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed
- [ ] Coverage maintained/improved

### Screenshots
[Before/After if UI changes]

### Breaking Changes
[None expected, or list them]

### Next Steps
[What PR comes next]
```

This document should be referenced at the start of each PR implementation to ensure consistency and alignment with the overall upgrade strategy.
