/**
 * Purpose: Individual Sudoku cell component with value and notes display
 * Scope: Single cell rendering with selection, highlighting, and validation states
 * Overview: Renders a single Sudoku cell with support for values, notes (pencil marks),
 *     and various visual states. Handles original cells, user-placed values, unsure mode,
 *     and validation errors. Displays notes in a 3x3 grid layout within the cell.
 *     Supports keyboard and mouse interaction.
 * Dependencies: React, sudoku.types, sudoku.constants
 * Exports: SudokuCell component
 * Props/Interfaces: SudokuCellProps
 * State/Behavior: Stateless component, controlled by parent via props
 */

import { memo, useCallback, useMemo, useRef } from 'react';
import type { ReactElement } from 'react';
import type { SudokuCellProps } from '../../types/sudoku.types';
import { isBoxBoundary } from '../../config/sudoku.constants';
import styles from './SudokuCell.module.css';

/**
 * Compare two Sets for shallow equality
 */
function setsEqual(a: Set<number>, b: Set<number>): boolean {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
}

/**
 * Custom comparator for memo() that compares props by value
 * rather than by reference, so memoization actually prevents re-renders.
 */
function areEqual(
  prev: Readonly<SudokuCellProps>,
  next: Readonly<SudokuCellProps>,
): boolean {
  return (
    prev.position.row === next.position.row &&
    prev.position.col === next.position.col &&
    prev.gridSize === next.gridSize &&
    prev.isSelected === next.isSelected &&
    prev.isHighlighted === next.isHighlighted &&
    prev.isRelated === next.isRelated &&
    prev.isSameValue === next.isSameValue &&
    prev.cell.value === next.cell.value &&
    prev.cell.isOriginal === next.cell.isOriginal &&
    prev.cell.isUnsure === next.cell.isUnsure &&
    prev.cell.isValid === next.cell.isValid &&
    prev.showCellPopup === next.showCellPopup &&
    prev.keypadHighlightValue === next.keypadHighlightValue &&
    prev.popupSuggestedNumber === next.popupSuggestedNumber &&
    prev.inputMode === next.inputMode &&
    prev.isUnsureMode === next.isUnsureMode &&
    setsEqual(prev.cell.notes, next.cell.notes)
  );
}

/**
 * SudokuCell component
 * Renders an individual cell in the Sudoku grid
 */
function SudokuCellComponent({
  cell,
  position,
  gridSize,
  isSelected,
  isHighlighted,
  isRelated,
  isSameValue,
  keypadHighlightValue,
  popupSuggestedNumber,
  inputMode,
  isUnsureMode,
  showCellPopup,
  onClick,
  onNumberPlace,
  onToggleInputMode,
  onAutoFillNotes,
  onToggleUnsureMode,
}: SudokuCellProps): ReactElement {
  // Determine box boundaries for thick borders
  const boundaries = isBoxBoundary(position.row, position.col, gridSize);

  // Build class list
  const classes = [styles.cell];

  if (isSelected) classes.push(styles.selected);
  if (isHighlighted) classes.push(styles.highlighted);
  if (isRelated && !isSelected) classes.push(styles.related);
  if (isSameValue && !isSelected) classes.push(styles.sameValue);
  if (cell.isOriginal) classes.push(styles.original);
  if (cell.isUnsure) classes.push(styles.unsure);
  if (!cell.isValid) classes.push(styles.invalid);
  if (boundaries.isRowBoundary) classes.push(styles.topBorder);
  if (boundaries.isColBoundary) classes.push(styles.leftBorder);

  const cellClasses = classes.join(' ');

  // Render notes in a 3x3 grid
  const renderNotes = useCallback(() => {
    if (cell.value !== null || cell.notes.size === 0) return null;

    const maxNum = gridSize;

    return (
      <div className={styles.notesGrid} data-grid-size={gridSize}>
        {Array.from({ length: maxNum }, (_, i) => i + 1).map((num) => (
          <span
            key={num}
            className={`${styles.note} ${cell.notes.has(num) ? styles.noteActive : ''}`}
          >
            {cell.notes.has(num) ? num : ''}
          </span>
        ))}
      </div>
    );
  }, [cell.value, cell.notes, gridSize]);

  // Show popup when cell is selected, empty, not original, and popup is enabled
  const showPopup =
    showCellPopup && isSelected && cell.value === null && !cell.isOriginal;

  // Popup position: show below by default, above if in bottom rows
  const popupPositionClass =
    position.row >= gridSize - 2 ? styles.popupAbove : styles.popupBelow;

  // Numbers for the popup
  const popupNumbers = useMemo(
    () => Array.from({ length: gridSize }, (_, i) => i + 1),
    [gridSize],
  );

  // Long-press detection for auto-filling notes on the cell itself
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressFiredRef = useRef(false);

  const clearLongPress = useCallback(() => {
    if (longPressTimerRef.current !== null) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, []);

  const handleCellPointerDown = useCallback(() => {
    longPressFiredRef.current = false;
    clearLongPress();
    longPressTimerRef.current = setTimeout(() => {
      longPressFiredRef.current = true;
      onAutoFillNotes(position);
    }, 500);
  }, [clearLongPress, onAutoFillNotes, position]);

  const handleCellPointerUp = useCallback(() => {
    clearLongPress();
    if (!longPressFiredRef.current) {
      onClick();
    }
  }, [clearLongPress, onClick]);

  const handleCellPointerLeave = useCallback(() => {
    clearLongPress();
  }, [clearLongPress]);

  return (
    <div
      className={cellClasses}
      onPointerDown={handleCellPointerDown}
      onPointerUp={handleCellPointerUp}
      onPointerLeave={handleCellPointerLeave}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`Cell row ${position.row + 1}, column ${position.col + 1}${
        cell.value ? `, value ${cell.value}` : ', empty'
      }`}
      aria-selected={isSelected}
    >
      {cell.value !== null ? (
        <span className={styles.value}>{cell.value}</span>
      ) : (
        renderNotes()
      )}
      {showPopup && (
        <div
          className={`${styles.popup} ${popupPositionClass}`}
          data-grid-size={gridSize}
          onClick={(e) => e.stopPropagation()}
          onPointerDown={(e) => e.stopPropagation()}
          onPointerUp={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
          role="group"
          aria-label="Quick number entry"
        >
          {popupNumbers.map((num) => {
            const highlightNum = popupSuggestedNumber ?? keypadHighlightValue;
            return (
              <button
                key={num}
                type="button"
                className={`${styles.popupButton} ${num === highlightNum ? styles.popupButtonActive : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onNumberPlace(num);
                }}
                aria-label={`Place ${num}`}
              >
                {num}
              </button>
            );
          })}
          <div className={styles.popupModeRow}>
            <button
              type="button"
              className={`${styles.popupModeButton} ${inputMode === 'notes' ? styles.popupModeActive : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggleInputMode();
              }}
              aria-label={`Notes mode ${inputMode === 'notes' ? 'on' : 'off'}`}
              aria-pressed={inputMode === 'notes'}
            >
              N
            </button>
            <button
              type="button"
              className={`${styles.popupModeButton} ${isUnsureMode ? styles.popupModeUnsureActive : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                onToggleUnsureMode();
              }}
              aria-label={`Unsure mode ${isUnsureMode ? 'on' : 'off'}`}
              aria-pressed={isUnsureMode}
            >
              ?
            </button>
            <button
              type="button"
              className={styles.popupDismiss}
              onClick={(e) => {
                e.stopPropagation();
                onClick();
              }}
              aria-label="Dismiss popup keypad"
            >
              Hide
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export const SudokuCell = memo(SudokuCellComponent, areEqual);
