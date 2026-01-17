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

import { memo, useCallback, useMemo } from 'react';
import type { ReactElement } from 'react';
import type { SudokuCellProps } from '../../types/sudoku.types';
import { isBoxBoundary } from '../../config/sudoku.constants';
import styles from './SudokuCell.module.css';

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
  const boundaries = useMemo(
    () => isBoxBoundary(position.row, position.col, gridSize),
    [position.row, position.col, gridSize],
  );

  // Build class list
  const cellClasses = useMemo(() => {
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

    return classes.join(' ');
  }, [
    isSelected,
    isHighlighted,
    isRelated,
    isSameValue,
    cell.isOriginal,
    cell.isUnsure,
    cell.isValid,
    boundaries,
  ]);

  // Handle click
  const handleClick = useCallback(() => {
    onClick();
  }, [onClick]);

  // Handle keyboard
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onClick();
      }
    },
    [onClick],
  );

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
      onClick={handleClick}
      onKeyDown={handleKeyDown}
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

export const SudokuCell = memo(SudokuCellComponent);
