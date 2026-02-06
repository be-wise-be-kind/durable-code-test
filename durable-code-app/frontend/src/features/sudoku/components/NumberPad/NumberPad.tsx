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
  activeNumber,
  onNumberClick,
  onEraseClick,
  onUndoClick,
  canUndo,
  inputMode,
  isUnsureMode,
  showCellPopup,
  onToggleInputMode,
  onToggleUnsureMode,
  onToggleCellPopup,
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
        {numbers.map((num) => {
          const isDisabled = disabledNumbers.has(num);
          const isActive = activeNumber === num && !isDisabled;
          const buttonClass = [
            styles.numberButton,
            isDisabled ? styles.disabled : '',
            isActive ? styles.active : '',
          ]
            .filter(Boolean)
            .join(' ');

          return (
            <button
              key={num}
              type="button"
              className={buttonClass}
              onClick={() => handleNumberClick(num)}
              disabled={isDisabled}
              aria-label={`Place number ${num}`}
              aria-pressed={isActive}
            >
              {num}
            </button>
          );
        })}
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
        <button
          type="button"
          className={`${styles.actionButton} ${!canUndo ? styles.actionDisabled : ''}`}
          onClick={onUndoClick}
          disabled={!canUndo}
          aria-label="Undo last action"
        >
          <span className={styles.actionIcon}>&#8617;</span>
          <span className={styles.actionLabel}>Undo</span>
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

        <button
          type="button"
          className={`${styles.modeButton} ${showCellPopup ? styles.modeActive : ''}`}
          onClick={onToggleCellPopup}
          aria-label={`Cell popup ${showCellPopup ? 'on' : 'off'}`}
          aria-pressed={showCellPopup}
        >
          <span className={styles.modeIcon}>#</span>
          <span className={styles.modeLabel}>Popup</span>
        </button>
      </div>

      {/* Keyboard shortcuts hint */}
      <div className={styles.hints}>
        <span>
          Keyboard: 1-{gridSize} to place, N for notes, U for unsure, Ctrl+Z to undo
        </span>
      </div>
    </div>
  );
}

export const NumberPad = memo(NumberPadComponent);
