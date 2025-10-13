/**
 * Purpose: Repository tab component showcasing AI-ready project setup and architecture
 * Scope: Feature-based React component for displaying repository best practices
 * Overview: Standardized component using FeatureCard grid layout with popup functionality
 * Dependencies: React, FeatureCard component, useRepository hook, CSS modules
 * Exports: RepositoryTab component (default export)
 * Props/Interfaces: No props - self-contained feature component
 * Implementation: Feature-based architecture with FeatureCard grid layout and modal popups
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { FeatureCard } from '../../../../components/common/FeatureCard/FeatureCard';
import { ErrorMessage, LoadingSpinner } from '../../../../components/common';
import { useRepository } from '../../hooks/useRepository';
import type { RepositoryItem } from '../../types/repository.types';
import styles from './RepositoryTab.module.css';
import {
  FaCheckCircle,
  FaCogs,
  FaDocker,
  FaFileAlt,
  FaFileCode,
  FaFlask,
  FaFolder,
  FaGavel,
  FaListOl,
  FaMap,
  FaShieldAlt,
} from 'react-icons/fa';

export function RepositoryTab(): ReactElement {
  const { repositoryItems, loading, error } = useRepository();
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  // Icon mapping function
  const getIconForItem = useCallback((itemId: string): ReactElement | null => {
    switch (itemId) {
      case 'project-layout':
        return <FaFolder />;
      case 'custom-linters':
        return <FaGavel />;
      case 'make-targets':
        return <FaCogs />;
      case 'docker-everything':
        return <FaDocker />;
      case 'quality-gates':
        return <FaCheckCircle />;
      case 'step-by-step':
        return <FaListOl />;
      case 'file-headers':
        return <FaFileAlt />;
      case 'ai-index':
        return <FaMap />;
      case 'test-infrastructure':
        return <FaFlask />;
      case 'code-templates':
        return <FaFileCode />;
      case 'error-resilience':
        return <FaShieldAlt />;
      case 'resource-naming':
        return <span>🏷️</span>;
      default:
        return null;
    }
  }, []);

  // Event handler for card clicks
  const handleItemClick = useCallback((item: RepositoryItem) => {
    if (item.popup) {
      setSelectedItem(item.id);
    }
  }, []);

  // Convert repository items to FeatureCard format
  const repositoryFeatures = useMemo(() => {
    return repositoryItems.map((item) => ({
      icon: getIconForItem(item.id) || <FaFolder />,
      title: item.title,
      description: item.popup?.solution.title || 'Repository feature information',
      linkText: 'Click to explore',
      onClick: () => handleItemClick(item),
    }));
  }, [repositoryItems, getIconForItem, handleItemClick]);

  // Find selected item for popup
  const selectedRepoItem = useMemo(() => {
    if (!selectedItem) return null;
    return repositoryItems.find((item) => item.id === selectedItem);
  }, [selectedItem, repositoryItems]);

  // Prevent body scroll when popup is open
  useEffect(() => {
    if (selectedRepoItem) {
      // Store current scroll position
      const scrollY = window.scrollY;

      // Store original body styles
      const originalOverflow = document.body.style.overflow;
      const originalPosition = document.body.style.position;
      const originalTop = document.body.style.top;
      const originalWidth = document.body.style.width;

      // Prevent scrolling
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.width = '100%';

      return () => {
        // Restore original styles
        document.body.style.overflow = originalOverflow;
        document.body.style.position = originalPosition;
        document.body.style.top = originalTop;
        document.body.style.width = originalWidth;

        // Restore scroll position
        window.scrollTo(0, scrollY);
      };
    }
    return undefined;
  }, [selectedRepoItem]);

  // Loading state
  if (loading) {
    return (
      <div className={styles.container}>
        <LoadingSpinner />
        <p>Loading repository data...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.container}>
        <ErrorMessage
          message={error.message}
          title="Error loading repository"
          variant="error"
          onDismiss={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h3 className="hero-title">
          Why Rigid Repository Structure Matters for AI Development
        </h3>
        <p className="subtitle">
          AI coding assistants are powerful but unpredictable. Without strict repository
          controls, they create inconsistent code, violate conventions, and introduce
          subtle bugs that compound over time. The solution is to establish{' '}
          <strong>rigid boundaries inside which AI can be free to create</strong>. When
          every file has a defined location, every operation runs identically, and every
          violation gets caught automatically, AI becomes a reliable engineering partner
          instead of a source of technical debt. The patterns below show how to build
          this foundation.
        </p>
      </div>

      <div className={styles.grid}>
        {repositoryFeatures.map((feature) => (
          <FeatureCard key={feature.title} {...feature} />
        ))}
      </div>

      {/* Popup rendered at component level */}
      {selectedRepoItem && selectedRepoItem.popup && (
        <>
          <div className={styles.popupBackdrop} onClick={() => setSelectedItem(null)} />
          <div className={styles.structuredPopup}>
            {/* Document Header */}
            <div className={styles.documentHeader}>
              <h2 className={styles.documentTitle}>
                {getIconForItem(selectedRepoItem.id) && (
                  <span className={styles.documentIcon}>
                    {getIconForItem(selectedRepoItem.id)}
                  </span>
                )}
                {selectedRepoItem.title}
              </h2>
              <button
                className={styles.closeButton}
                onClick={() => setSelectedItem(null)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <div className={styles.popupContainer}>
              {/* Problem Section */}
              <div className={styles.popupSection}>
                <h3 className={styles.sectionTitle}>
                  <span className={styles.sectionIcon}>🔴</span>
                  The Problem
                </h3>
                <div className={styles.sectionContent}>
                  <h4>{selectedRepoItem.popup.problem.title}</h4>
                  <ul className={styles.pointsList}>
                    {selectedRepoItem.popup.problem.points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Solution Section */}
              <div className={styles.popupSection}>
                <h3 className={styles.sectionTitle}>
                  <span className={styles.sectionIcon}>✅</span>
                  Our Solution
                </h3>
                <div className={styles.sectionContent}>
                  <h4>{selectedRepoItem.popup.solution.title}</h4>
                  <ul className={styles.pointsList}>
                    {selectedRepoItem.popup.solution.points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Example Section */}
              <div className={styles.popupSection}>
                <h3 className={styles.sectionTitle}>
                  <span className={styles.sectionIcon}>💻</span>
                  Example from Our Code
                </h3>
                <div className={styles.exampleHeader}>
                  <span className={styles.exampleTitle}>
                    {selectedRepoItem.popup.example.title}
                  </span>
                  {selectedRepoItem.popup.example.file && (
                    <span className={styles.exampleFile}>
                      {selectedRepoItem.popup.example.file}
                    </span>
                  )}
                </div>
                <pre className={styles.codeBlock}>
                  <code
                    className={`language-${selectedRepoItem.popup.example.language}`}
                  >
                    {selectedRepoItem.popup.example.code}
                  </code>
                </pre>
              </div>
            </div>

            {/* Links Section - Outside scrollable area */}
            {selectedRepoItem.popup.links && (
              <div className={styles.popupLinks}>
                {selectedRepoItem.popup.links.map((link, index) => (
                  <a
                    key={index}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.popupLink}
                  >
                    {link.text} →
                  </a>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default RepositoryTab;
