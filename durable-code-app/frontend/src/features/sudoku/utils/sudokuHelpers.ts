/**
 * Purpose: Utility functions for Sudoku grid operations
 * Scope: Grid manipulation, cell operations, and game state calculations
 * Overview: Provides helper functions for common Sudoku operations including
 *     cell position calculations, grid state management, game statistics,
 *     and time formatting. Supports both 6x6 and 9x9 grid sizes.
 *     Ensures immutable operations on grid state.
 * Dependencies: sudoku.types for type definitions
 * Exports: Grid manipulation and utility functions
 * Implementation: Pure functions with immutable data patterns
 */

import type {
  CellPosition,
  CellState,
  GameStats,
  GridSize,
} from '../types/sudoku.types';
import { getBoxPosition } from '../config/sudoku.constants';

/**
 * Create a deep copy of the grid
 */
export function cloneGrid(grid: CellState[][]): CellState[][] {
  return grid.map((row) =>
    row.map((cell) => ({
      ...cell,
      notes: new Set(cell.notes),
    })),
  );
}

/**
 * Check if two cell positions are equal
 */
export function positionsEqual(
  a: CellPosition | null,
  b: CellPosition | null,
): boolean {
  if (a === null || b === null) return a === b;
  return a.row === b.row && a.col === b.col;
}

/**
 * Check if a cell is in the same row, column, or box as the selected cell
 */
export function isRelatedCell(
  position: CellPosition,
  selected: CellPosition | null,
  gridSize: GridSize,
): boolean {
  if (!selected) return false;

  // Same row or column
  if (position.row === selected.row || position.col === selected.col) {
    return true;
  }

  // Same box
  const posBox = getBoxPosition(position.row, position.col, gridSize);
  const selBox = getBoxPosition(selected.row, selected.col, gridSize);

  return posBox.boxRow === selBox.boxRow && posBox.boxCol === selBox.boxCol;
}

/**
 * Check if a cell has the same value as another cell
 */
export function hasSameValue(
  grid: CellState[][],
  position: CellPosition,
  value: number | null,
): boolean {
  if (value === null) return false;
  return grid[position.row][position.col].value === value;
}

/**
 * Calculate game statistics from the current grid state
 */
export function calculateStats(
  grid: CellState[][],
  elapsedTime: number,
  mistakes: number,
): GameStats {
  let filledCells = 0;
  let totalEmptyCells = 0;

  for (const row of grid) {
    for (const cell of row) {
      if (!cell.isOriginal) {
        totalEmptyCells++;
        if (cell.value !== null) {
          filledCells++;
        }
      }
    }
  }

  const completionPercentage =
    totalEmptyCells > 0 ? Math.round((filledCells / totalEmptyCells) * 100) : 0;

  return {
    mistakes,
    elapsedTime,
    filledCells,
    totalEmptyCells,
    completionPercentage,
  };
}

/**
 * Format elapsed time as MM:SS
 */
export function formatTime(milliseconds: number): string {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Get all numbers that are complete (9 instances in a 9x9 grid)
 * These numbers should be disabled in the number pad
 */
export function getCompletedNumbers(
  grid: CellState[][],
  gridSize: GridSize,
): Set<number> {
  const counts = new Map<number, number>();

  for (const row of grid) {
    for (const cell of row) {
      if (cell.value !== null) {
        counts.set(cell.value, (counts.get(cell.value) ?? 0) + 1);
      }
    }
  }

  const completed = new Set<number>();
  for (let num = 1; num <= gridSize; num++) {
    if ((counts.get(num) ?? 0) >= gridSize) {
      completed.add(num);
    }
  }

  return completed;
}

/**
 * Convert a cell position to a string key
 */
export function positionToKey(position: CellPosition): string {
  return `${position.row},${position.col}`;
}

/**
 * Parse a string key to a cell position
 */
export function keyToPosition(key: string): CellPosition {
  const [row, col] = key.split(',').map(Number);
  return { row, col };
}

/**
 * Get all empty cells in the grid
 */
export function getEmptyCells(grid: CellState[][]): CellPosition[] {
  const emptyCells: CellPosition[] = [];

  for (let row = 0; row < grid.length; row++) {
    for (let col = 0; col < grid[row].length; col++) {
      if (grid[row][col].value === null) {
        emptyCells.push({ row, col });
      }
    }
  }

  return emptyCells;
}

/**
 * Count filled cells (non-original)
 */
export function countFilledCells(grid: CellState[][]): number {
  let count = 0;

  for (const row of grid) {
    for (const cell of row) {
      if (!cell.isOriginal && cell.value !== null) {
        count++;
      }
    }
  }

  return count;
}

/**
 * Update a single cell in the grid (immutable)
 */
export function updateCell(
  grid: CellState[][],
  position: CellPosition,
  updates: Partial<CellState>,
): CellState[][] {
  return grid.map((row, rowIdx) =>
    row.map((cell, colIdx) => {
      if (rowIdx === position.row && colIdx === position.col) {
        return {
          ...cell,
          ...updates,
          notes: updates.notes ?? cell.notes,
        };
      }
      return cell;
    }),
  );
}

/**
 * Clear notes from related cells when a number is placed
 * (Cells in the same row, column, or box)
 */
export function clearRelatedNotes(
  grid: CellState[][],
  position: CellPosition,
  value: number,
  gridSize: GridSize,
): CellState[][] {
  return grid.map((row, rowIdx) =>
    row.map((cell, colIdx) => {
      const cellPos = { row: rowIdx, col: colIdx };
      if (
        isRelatedCell(cellPos, position, gridSize) &&
        !positionsEqual(cellPos, position)
      ) {
        const newNotes = new Set(cell.notes);
        newNotes.delete(value);
        return { ...cell, notes: newNotes };
      }
      return cell;
    }),
  );
}
