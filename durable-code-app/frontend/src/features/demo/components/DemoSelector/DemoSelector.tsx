/**
 * Purpose: Demo selector landing page
 * Scope: Selection interface for available demos
 * Overview: Card-based interface for choosing between available demos
 * Dependencies: React, navigation store
 * Exports: DemoSelector component
 * Implementation: Grid layout with demo cards for selection
 */

import type { ReactElement } from 'react';
import { useCallback } from 'react';
import { useNavigationStore } from '../../../../store/navigationStore';
import styles from './DemoSelector.module.css';

interface DemoInfo {
  id: string;
  title: string;
  icon: string;
  description: string;
  features: string[];
  status: 'available' | 'coming-soon';
}

const demos: DemoInfo[] = [
  {
    id: 'oscilloscope',
    title: 'Oscilloscope',
    icon: '📊',
    description:
      'Real-time waveform visualization with WebSocket streaming. Experience smooth, hardware-accelerated canvas rendering with multiple waveform types.',
    features: [
      'Real-time WebSocket streaming',
      'Multiple waveform types',
      'Adjustable parameters',
      'Performance monitoring',
    ],
    status: 'available',
  },
  {
    id: 'racing',
    title: 'Racing Game',
    icon: '🏎️',
    description:
      'Physics-based racing game with procedural track generation. Control your car with mouse movements in this exciting demo.',
    features: [
      'Mouse-following controls',
      'Physics simulation',
      'Procedural tracks',
      'Scoring system',
    ],
    status: 'available',
  },
  {
    id: 'sudoku',
    title: 'Sudoku',
    icon: '🔢',
    description:
      'Classic number puzzle with 6x6 and 9x9 grids. Place numbers, use pencil marks, and track your progress.',
    features: [
      '6x6 and 9x9 grids',
      'Notes mode',
      'Unsure color mode',
      'Shareable puzzle seeds',
    ],
    status: 'available',
  },
];

export function DemoSelector(): ReactElement {
  const { setActiveSubTab } = useNavigationStore();

  const handleDemoSelect = useCallback(
    (demoId: string) => {
      setActiveSubTab(demoId);
    },
    [setActiveSubTab],
  );

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Interactive Demos</h2>
      <p className={styles.subtitle}>
        Explore our collection of AI-authored interactive demonstrations
      </p>

      <div className={styles.demoGrid}>
        {demos.map((demo) => (
          <div
            key={demo.id}
            className={styles.demoCard}
            onClick={() => demo.status === 'available' && handleDemoSelect(demo.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if ((e.key === 'Enter' || e.key === ' ') && demo.status === 'available') {
                e.preventDefault();
                handleDemoSelect(demo.id);
              }
            }}
          >
            <div className={styles.demoHeader}>
              <span className={styles.demoIcon}>{demo.icon}</span>
              <h3 className={styles.demoTitle}>{demo.title}</h3>
            </div>

            <p className={styles.demoDescription}>{demo.description}</p>

            <ul className={styles.demoFeatures}>
              {demo.features.map((feature, index) => (
                <li key={index} className={styles.demoFeature}>
                  <span className={styles.featureIcon}>✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            <div
              className={`${styles.demoStatus} ${
                demo.status === 'available'
                  ? styles.statusAvailable
                  : styles.statusComingSoon
              }`}
            >
              {demo.status === 'available' ? (
                <>
                  <span>●</span> Available Now
                </>
              ) : (
                <>
                  <span>○</span> Coming Soon
                </>
              )}
            </div>

            <button
              className={styles.launchButton}
              disabled={demo.status !== 'available'}
              onClick={(e) => {
                e.stopPropagation();
                if (demo.status === 'available') {
                  handleDemoSelect(demo.id);
                }
              }}
            >
              {demo.status === 'available' ? 'Launch Demo' : 'In Development'}
              <span>→</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
