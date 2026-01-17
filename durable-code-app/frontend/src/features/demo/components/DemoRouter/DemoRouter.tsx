/**
 * Purpose: Router component for demo sub-navigation
 * Scope: Handles routing between different demo applications
 * Overview: Routes to specific demo based on sub-tab selection
 * Dependencies: React, navigation store, demo components
 * Exports: DemoRouter component
 * Implementation: Renders appropriate demo based on activeSubTab
 */

import type { ReactElement } from 'react';
import { lazy, Suspense, useEffect } from 'react';
import { useNavigationStore } from '../../../../store/navigationStore';
import { OscilloscopeDemo } from '../OscilloscopeDemo';
import { DemoSelector } from '../DemoSelector';

// Lazy load racing game to prevent import-time errors
const RacingGameTab = lazy(() =>
  import('../../../racing/components/RacingGameTab').then((m) => ({
    default: m.RacingGameTab,
  })),
);

// Lazy load sudoku game
const SudokuTab = lazy(() =>
  import('../../../sudoku/components/SudokuTab').then((m) => ({
    default: m.SudokuTab,
  })),
);

export function DemoRouter(): ReactElement {
  const { activeSubTab, setActiveSubTab } = useNavigationStore();

  // Set default sub-tab if none is selected
  useEffect(() => {
    if (!activeSubTab) {
      // Parse hash to check if there's a sub-tab in the URL
      const hash =
        typeof window !== 'undefined' && window.location?.hash
          ? window.location.hash.slice(1)
          : '';
      const parts = hash.split('/');
      if (parts.length > 1 && parts[0] === 'Demo') {
        setActiveSubTab(parts[1]);
      }
    }
  }, [activeSubTab, setActiveSubTab]);

  // Render the appropriate demo based on activeSubTab
  switch (activeSubTab) {
    case 'oscilloscope':
      return <OscilloscopeDemo />;
    case 'racing':
      return (
        <Suspense fallback={<div>Loading Racing Game...</div>}>
          <RacingGameTab />
        </Suspense>
      );
    case 'sudoku':
      return (
        <Suspense fallback={<div>Loading Sudoku...</div>}>
          <SudokuTab />
        </Suspense>
      );
    default:
      return <DemoSelector />;
  }
}
