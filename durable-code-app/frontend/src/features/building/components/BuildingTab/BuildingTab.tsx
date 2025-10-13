/**
 * Purpose: Building tab feature component for AI-powered development tools
 * Scope: React component for displaying development methodologies and tool integrations
 * Overview: Modularized building tab with FeatureCard components for consistency
 * Dependencies: React, FeatureCard component, CSS modules
 * Exports: BuildingTab component
 * Props/Interfaces: No props - self-contained feature component
 * Implementation: Feature-based architecture with FeatureCard grid layout
 */

import type { ReactElement } from 'react';
import { FeatureCard } from '../../../../components/common/FeatureCard/FeatureCard';
import styles from './BuildingTab.module.css';
import {
  FaBolt,
  FaClipboardCheck,
  FaCogs,
  FaFileCode,
  FaRobot,
  FaRocket,
} from 'react-icons/fa';

export function BuildingTab(): ReactElement {
  const buildingFeatures = [
    {
      icon: <FaBolt />,
      title: 'Code Generation Commands',
      description:
        'AI-powered slash commands for instant code creation including /new-code, /solid, /fix, and /ask',
      linkText: 'View Commands',
      linkHref: '/commands?return=Building',
    },
    {
      icon: <FaCogs />,
      title: '/new-code Capabilities',
      description:
        'Smart generation system that creates React components, FastAPI endpoints, tests, and more with proper architecture',
      linkText: 'View Capabilities',
      linkHref: '/new-code?return=Building',
    },
    {
      icon: <FaRobot />,
      title: 'AI-Powered Commands',
      description:
        'Advanced AI slash commands with context awareness, template generation, and intelligent code analysis',
      linkText: 'View AI Commands',
      linkHref: '/ai-commands?return=Building',
    },
    {
      icon: <FaFileCode />,
      title: 'AI Templates',
      description:
        'Pre-built templates in .ai/templates for React components, API endpoints, tests, and documentation',
      linkText: 'View Templates',
      linkHref: '/templates?return=Building',
    },
    {
      icon: <FaRocket />,
      title: 'How-To Guides',
      description:
        'Step-by-step guides in .ai/howto for development workflows, debugging, and best practices',
      linkText: 'View Guides',
      linkHref: '/howto?return=Building',
    },
    {
      icon: <FaClipboardCheck />,
      title: 'Development Standards',
      description:
        'Comprehensive standards guide for code quality, architecture patterns, and AI development workflows',
      linkText: 'Standards Guide',
      linkHref: '/standards?return=Building',
    },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h3 className="hero-title">AI-Powered Code Generation</h3>
        <p className="subtitle">
          Build complete applications without writing a single line of code - powered by
          AI-driven development and intelligent automation
        </p>
      </div>

      <div className={styles.grid}>
        {buildingFeatures.map((feature) => (
          <FeatureCard key={feature.title} {...feature} />
        ))}
      </div>
    </div>
  );
}
