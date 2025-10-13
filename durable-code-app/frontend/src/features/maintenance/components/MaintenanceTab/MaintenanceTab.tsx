/**
 * Purpose: Maintenance tab for AI documentation and knowledge management
 * Scope: React component for AI documentation with FeatureCard integration
 * Overview: Modularized maintenance tab using FeatureCard components for consistency
 * Dependencies: React, FeatureCard component, CSS modules
 * Exports: MaintenanceTab component
 * Props/Interfaces: No props - self-contained feature component
 * Implementation: Feature module with FeatureCard grid layout
 */

import type { ReactElement } from 'react';
import { FeatureCard } from '../../../../components/common/FeatureCard/FeatureCard';
import styles from './MaintenanceTab.module.css';
import { FaBook, FaCode, FaCog, FaFileAlt, FaRobot, FaSync } from 'react-icons/fa';

export function MaintenanceTab(): ReactElement {
  const maintenanceFeatures = [
    {
      icon: <FaRobot />,
      title: 'AI Agent Index',
      description:
        'Comprehensive .ai/index.md designed for AI agents with 12 templates, 5 features, 8 guides, and 4 standards',
      linkText: 'View AI Index',
      linkHref: '/.ai/index.md',
    },
    {
      icon: <FaBook />,
      title: 'Feature Documentation',
      description:
        'Complete .ai/features/ documentation including design linters, web application, development tooling, and Claude integration',
      linkText: 'Browse Features',
      linkHref: '/.ai/features/',
    },
    {
      icon: <FaCode />,
      title: 'Code Templates',
      description:
        'AI-ready templates in .ai/templates/ for React components, FastAPI endpoints, linting rules, and test suites',
      linkText: 'View Templates',
      linkHref: '/.ai/templates/',
    },
    {
      icon: <FaFileAlt />,
      title: 'Standards & Best Practices',
      description:
        'Comprehensive standards documentation including file headers, CSS layout stability, and branch protection',
      linkText: 'Read Standards',
      linkHref: '/.ai/docs/STANDARDS.md',
    },
    {
      icon: <FaCog />,
      title: 'How-To Guides',
      description:
        'Step-by-step guides for running tests, linting, setup, deployment, and debugging in .ai/howto/',
      linkText: 'View Guides',
      linkHref: '/.ai/howto/',
    },
    {
      icon: <FaSync />,
      title: 'Auto-Generated Content',
      description:
        'AI-powered generation of README files, changelogs, API docs, and code indexes with make commands',
      linkText: 'Generate Docs',
    },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h3 className="hero-title">AI-Powered Documentation</h3>
        <p className="subtitle">
          Self-maintaining documentation that evolves with your codebase, powered by
          AI-driven content generation and automatic synchronization
        </p>
      </div>

      <div className={styles.grid}>
        {maintenanceFeatures.map((feature) => (
          <FeatureCard key={feature.title} {...feature} />
        ))}
      </div>
    </div>
  );
}
