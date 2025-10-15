/**
 * Purpose: Home page component with tabbed interface for durable code framework
 * Scope: Main page component displaying different aspects of AI-ready development
 * Overview: Comprehensive dashboard for the Durable Code framework with tabbed navigation
 * Dependencies: React, navigation feature, tab configurations
 * Exports: HomePage component
 * Props/Interfaces: No props - page component
 * Implementation: Uses navigation feature and tab configuration
 */

import { Suspense } from 'react';
import type { ReactElement } from 'react';
import ParticleBackground from '../../components/ParticleBackground';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { TabNavigation, useNavigation } from '../../features/navigation';
import { tabs } from '../../config/tabs.config';
import styles from './HomePage.module.css';
import { MinimalErrorBoundary } from '../../core/errors/MinimalErrorBoundary';
import { PrinciplesBanner } from '../../components/PrinciplesBanner/PrinciplesBanner';
import { logger } from '../../utils/logger';

export default function HomePage(): ReactElement {
  const { activeTab, handleTabChange } = useNavigation();
  const tabConfig = tabs[activeTab];

  if (!tabConfig) {
    logger.error(`Tab configuration not found for: ${activeTab}`);
    logger.error('Available tabs:', Object.keys(tabs));
    throw new Error(`Tab configuration not found for: ${activeTab}`);
  }

  const ActiveTabComponent = tabConfig.component;

  if (!ActiveTabComponent) {
    return (
      <div className={styles.container}>
        <ParticleBackground />
        <div className={styles.errorMessage}>
          Tab component not found for: {activeTab}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.app}>
      <ParticleBackground />
      <header className={styles.hero}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>
            <span className={styles.gradientText}>AI-Authored Excellence</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Proving that AI can create production-quality, scalable, and maintainable
            code through intelligent architecture and automated quality assurance
          </p>
          <div className={styles.heroInfoGrid}>
            <div className={styles.projectInfo}>
              <h3>Project Purpose</h3>
              <p>
                This project serves a dual purpose: documenting best practices for
                AI-assisted development while simultaneously demonstrating through its
                own implementation that these practices enable AI to create
                production-quality, maintainable software at enterprise scale.
              </p>
            </div>
            <div className={styles.projectScope}>
              <h3>Design Goals</h3>
              <ul>
                <li>AI writes quality code on first attempt with minimal iteration</li>
                <li>100% AI-authored codebase proving the methodology works</li>
                <li>Self-documenting architecture that guides future AI development</li>
              </ul>
            </div>
          </div>

          <PrinciplesBanner />
        </div>
      </header>

      <main className={styles.mainContent}>
        <TabNavigation
          activeTab={activeTab}
          onTabChange={handleTabChange}
          tabs={tabs}
        />

        <section className={styles.tabContainer}>
          <MinimalErrorBoundary>
            <Suspense fallback={<LoadingSpinner />}>
              <ActiveTabComponent />
            </Suspense>
          </MinimalErrorBoundary>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerSection}>
            <h4>Resources</h4>
            <ul>
              <li>
                <a
                  href="https://github.com/be-wise-be-kind/durable-code-test"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/be-wise-be-kind/durable-code-test/blob/main/README.md"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  API Reference
                </a>
              </li>
            </ul>
          </div>
          <div className={styles.footerSection}>
            <h4>Deployed</h4>
            <p className={styles.versionInfo}>
              {import.meta.env.VITE_BUILD_TIMESTAMP || 'development'}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
