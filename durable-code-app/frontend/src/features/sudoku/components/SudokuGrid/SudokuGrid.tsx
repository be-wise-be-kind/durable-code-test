/**
 * Purpose: Sudoku grid container component using CSS Grid
 * Scope: Grid layout for 6x6 and 9x9 Sudoku puzzles
 * Overview: Renders the complete Sudoku grid using CSS Grid layout.
 *     Manages cell highlighting for related cells (same row/col/box) and
 *     same-value highlighting. Supports both 6x6 and 9x9 grid sizes with
 *     appropriate box boundaries.
 * Dependencies: React, SudokuCell component, sudoku.types
 * Exports: SudokuGrid component
 * Props/Interfaces: SudokuGridProps
 * State/Behavior: Controlled component with selection passed from parent
 */

import { memo, useCallback, useMemo } from 'react';
import type { ReactElement } from 'react';
import type { CellPosition, SudokuGridProps } from '../../types/sudoku.types';
import { SudokuCell } from '../SudokuCell';
import { hasSameValue, isRelatedCell, positionsEqual } from '../../utils/sudokuHelpers';
import styles from './SudokuGrid.module.css';

/**
 * SudokuGrid component
 * Renders the complete Sudoku grid with cells
 */
function SudokuGridComponent({
  grid,
  gridSize,
  selectedCell,
  highlightedValue,
  keypadHighlightValue,
  inputMode,
  isUnsureMode,
  showCellPopup,
  onCellClick,
  onNumberPlace,
  onToggleInputMode,
  onToggleUnsureMode,
  className = '',
}: SudokuGridProps): ReactElement {
  // Memoize cell click handlers
  const handleCellClick = useCallback(
    (position: CellPosition) => {
      onCellClick(position);
    },
    [onCellClick],
  );

  // Grid classes
  const gridClasses = useMemo(() => {
    return [styles.grid, styles[`grid${gridSize}`], className]
      .filter(Boolean)
      .join(' ');
  }, [gridSize, className]);

  return (
    <div
      className={gridClasses}
      role="grid"
      aria-label={`${gridSize}x${gridSize} Sudoku grid`}
    >
      {grid.map((row, rowIdx) =>
        row.map((cell, colIdx) => {
          const position: CellPosition = { row: rowIdx, col: colIdx };
          const isSelected = positionsEqual(position, selectedCell);
          const isRelated = isRelatedCell(position, selectedCell, gridSize);
          const isSameValueCell =
            highlightedValue !== null && hasSameValue(grid, position, highlightedValue);

          return (
            <SudokuCell
              key={`${rowIdx}-${colIdx}`}
              cell={cell}
              position={position}
              gridSize={gridSize}
              isSelected={isSelected}
              isHighlighted={false}
              isRelated={isRelated}
              isSameValue={isSameValueCell}
              keypadHighlightValue={keypadHighlightValue}
              inputMode={inputMode}
              isUnsureMode={isUnsureMode}
              showCellPopup={showCellPopup}
              onClick={() => handleCellClick(position)}
              onNumberPlace={onNumberPlace}
              onToggleInputMode={onToggleInputMode}
              onToggleUnsureMode={onToggleUnsureMode}
            />
          );
        }),
      )}
    </div>
  );
}

export const SudokuGrid = memo(SudokuGridComponent);
