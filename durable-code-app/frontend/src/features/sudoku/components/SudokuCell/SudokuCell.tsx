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

import { memo, useCallback } from 'react';
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
  onClick,
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

  return (
    <div
      className={cellClasses}
      onClick={onClick}
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
    </div>
  );
}

export const SudokuCell = memo(SudokuCellComponent, areEqual);
