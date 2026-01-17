/**
 * Purpose: Number pad component for Sudoku input
 * Scope: Clickable number buttons, erase, and mode toggles
 * Overview: Provides a clickable interface for placing numbers in Sudoku cells.
 *     Adapts to grid size (1-6 or 1-9 buttons). Includes erase button and
 *     toggle buttons for notes mode and unsure mode. Disables completed numbers.
 * Dependencies: React, sudoku.types
 * Exports: NumberPad component
 * Props/Interfaces: NumberPadProps
 * State/Behavior: Controlled component with mode state from parent
 */

import { memo, useCallback, useMemo } from 'react';
import type { ReactElement } from 'react';
import type { NumberPadProps } from '../../types/sudoku.types';
import styles from './NumberPad.module.css';

/**
 * NumberPad component
 * Provides number buttons and mode toggles for Sudoku input
 */
function NumberPadComponent({
  gridSize,
  onNumberClick,
  onEraseClick,
  inputMode,
  isUnsureMode,
  onToggleInputMode,
  onToggleUnsureMode,
  disabledNumbers,
  className = '',
}: NumberPadProps): ReactElement {
  // Generate number buttons based on grid size
  const numbers = useMemo(
    () => Array.from({ length: gridSize }, (_, i) => i + 1),
    [gridSize],
  );

  // Handle number click
  const handleNumberClick = useCallback(
    (num: number) => {
      if (!disabledNumbers.has(num)) {
        onNumberClick(num);
      }
    },
    [onNumberClick, disabledNumbers],
  );

  // Container classes
  const containerClasses = useMemo(() => {
    return [styles.container, className].filter(Boolean).join(' ');
  }, [className]);

  return (
    <div className={containerClasses}>
      {/* Number buttons */}
      <div className={styles.numberGrid} data-grid-size={gridSize}>
        {numbers.map((num) => (
          <button
            key={num}
            type="button"
            className={`${styles.numberButton} ${
              disabledNumbers.has(num) ? styles.disabled : ''
            }`}
            onClick={() => handleNumberClick(num)}
            disabled={disabledNumbers.has(num)}
            aria-label={`Place number ${num}`}
          >
            {num}
          </button>
        ))}
      </div>

      {/* Action buttons */}
      <div className={styles.actionButtons}>
        <button
          type="button"
          className={styles.actionButton}
          onClick={onEraseClick}
          aria-label="Erase cell"
        >
          <span className={styles.actionIcon}>x</span>
          <span className={styles.actionLabel}>Erase</span>
        </button>
      </div>

      {/* Mode toggles */}
      <div className={styles.modeToggles}>
        <button
          type="button"
          className={`${styles.modeButton} ${
            inputMode === 'notes' ? styles.modeActive : ''
          }`}
          onClick={onToggleInputMode}
          aria-label={`Notes mode ${inputMode === 'notes' ? 'on' : 'off'}`}
          aria-pressed={inputMode === 'notes'}
        >
          <span className={styles.modeIcon}>N</span>
          <span className={styles.modeLabel}>Notes</span>
        </button>

        <button
          type="button"
          className={`${styles.modeButton} ${
            isUnsureMode ? styles.modeActive : ''
          } ${styles.unsureButton}`}
          onClick={onToggleUnsureMode}
          aria-label={`Unsure mode ${isUnsureMode ? 'on' : 'off'}`}
          aria-pressed={isUnsureMode}
        >
          <span className={styles.modeIcon}>?</span>
          <span className={styles.modeLabel}>Unsure</span>
        </button>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className={styles.hints}>
        <span>Keyboard: 1-{gridSize} to place, N for notes, U for unsure</span>
      </div>
    </div>
  );
}

export const NumberPad = memo(NumberPadComponent);
