/**
 * Purpose: Tab configuration for the application with error boundaries
 * Scope: Centralized tab definitions and lazy loading with error isolation
 * Overview: Defines all application tabs and their components with error handling
 * Dependencies: React lazy loading, feature components, error boundaries
 * Exports: Tab configuration object
 * Implementation: Lazy-loaded feature tab configuration with error boundary wrapping
 */

import { lazy } from 'react';
import type { TabContent, TabName } from '../features/navigation';

// Lazy load components normally - error boundaries will be applied at render time
const RepositoryTab = lazy(() =>
  import('../features/repository/components/RepositoryTab').then((m) => ({
    default: m.RepositoryTab,
  })),
);
const PlanningTab = lazy(() =>
  import('../features/planning/components/PlanningTab').then((m) => ({
    default: m.PlanningTab,
  })),
);
const BuildingTab = lazy(() =>
  import('../features/building/components/BuildingTab').then((m) => ({
    default: m.BuildingTab,
  })),
);
const QualityAssuranceTab = lazy(() =>
  import('../features/quality/components/QualityAssuranceTab').then((m) => ({
    default: m.QualityAssuranceTab,
  })),
);
const MaintenanceTab = lazy(() =>
  import('../features/maintenance/components/MaintenanceTab').then((m) => ({
    default: m.MaintenanceTab,
  })),
);
const DemoTab = lazy(() =>
  import('../features/demo/components/DemoTab').then((m) => ({ default: m.DemoTab })),
);
const JourneyTab = lazy(() =>
  import('../features/journey/components/JourneyTab/JourneyTab').then((m) => ({
    default: m.JourneyTab,
  })),
);

export const tabs: Record<TabName, TabContent> = {
  Repository: {
    title: 'Repository',
    icon: '',
    description:
      'Building AI-ready projects with proper repository structure and context',
    component: RepositoryTab,
  },
  Planning: {
    title: 'Planning',
    icon: '',
    description: 'Strategic planning and documentation for AI-assisted development',
    component: PlanningTab,
  },
  Building: {
    title: 'Building',
    icon: '',
    description: 'Tools and commands for AI-assisted code generation',
    component: BuildingTab,
  },
  'Quality Assurance': {
    title: 'Quality Assurance',
    icon: '',
    description: 'Automated testing, linting, and CI/CD for code quality',
    component: QualityAssuranceTab,
  },
  Maintenance: {
    title: 'Maintenance',
    icon: '',
    description: 'Ongoing maintenance and evolution strategies',
    component: MaintenanceTab,
  },
  Demo: {
    title: 'Demo',
    icon: '',
    description: 'Interactive demonstrations showcasing AI-authored capabilities',
    component: DemoTab,
  },
  Journey: {
    title: 'Journey',
    icon: '',
    description: 'The evolution of an AI-authored codebase from concept to production',
    component: JourneyTab,
  },
};
