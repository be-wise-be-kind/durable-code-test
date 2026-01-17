/**
 * Purpose: Sudoku puzzle validation utilities
 * Scope: Row, column, and box validation for Sudoku grids
 * Overview: Provides comprehensive validation functions for Sudoku puzzles.
 *     Validates individual placements against row, column, and box constraints.
 *     Supports both 6x6 and 9x9 grid sizes with appropriate box dimensions.
 *     Checks for conflicts and determines puzzle completion status.
 * Dependencies: sudoku.types for type definitions, sudoku.constants for box dimensions
 * Exports: validatePlacement, getRowValues, getColValues, getBoxValues, findConflicts
 * Implementation: Constraint-based validation using set operations for efficiency
 */

import type { CellState, GridSize } from '../types/sudoku.types';
import { BOX_DIMENSIONS, getBoxPosition } from '../config/sudoku.constants';

/**
 * Get all values in a row (excluding nulls)
 */
export function getRowValues(grid: CellState[][], row: number): number[] {
  return grid[row]
    .filter((cell) => cell.value !== null)
    .map((cell) => cell.value as number);
}

/**
 * Get all values in a column (excluding nulls)
 */
export function getColValues(grid: CellState[][], col: number): number[] {
  return grid
    .map((row) => row[col])
    .filter((cell) => cell.value !== null)
    .map((cell) => cell.value as number);
}

/**
 * Get all values in a box (excluding nulls)
 */
export function getBoxValues(
  grid: CellState[][],
  row: number,
  col: number,
  gridSize: GridSize,
): number[] {
  const { rows: boxRows, cols: boxCols } = BOX_DIMENSIONS[gridSize];
  const { boxRow, boxCol } = getBoxPosition(row, col, gridSize);

  const startRow = boxRow * boxRows;
  const startCol = boxCol * boxCols;

  const values: number[] = [];

  for (let r = startRow; r < startRow + boxRows; r++) {
    for (let c = startCol; c < startCol + boxCols; c++) {
      const cell = grid[r][c];
      if (cell.value !== null) {
        values.push(cell.value);
      }
    }
  }

  return values;
}

/**
 * Validate if a number can be placed at a specific position
 * Returns true if the placement is valid (no conflicts)
 */
export function validatePlacement(
  grid: CellState[][],
  row: number,
  col: number,
  value: number,
  gridSize: GridSize,
): boolean {
  // Check row (excluding the cell itself)
  const rowValues = getRowValues(grid, row);
  if (rowValues.includes(value) && grid[row][col].value !== value) {
    return false;
  }

  // Check column (excluding the cell itself)
  const colValues = getColValues(grid, col);
  if (colValues.includes(value) && grid[row][col].value !== value) {
    return false;
  }

  // Check box (excluding the cell itself)
  const boxValues = getBoxValues(grid, row, col, gridSize);
  if (boxValues.includes(value) && grid[row][col].value !== value) {
    return false;
  }

  return true;
}

/**
 * Find all cells that conflict with a given cell's value
 * Returns a set of cell keys in "row,col" format
 */
export function findConflicts(
  grid: CellState[][],
  row: number,
  col: number,
  gridSize: GridSize,
): Set<string> {
  const conflicts = new Set<string>();
  const cell = grid[row][col];

  if (cell.value === null) {
    return conflicts;
  }

  const value = cell.value;
  const cellKey = `${row},${col}`;

  // Check row
  for (let c = 0; c < gridSize; c++) {
    if (c !== col && grid[row][c].value === value) {
      conflicts.add(`${row},${c}`);
      conflicts.add(cellKey);
    }
  }

  // Check column
  for (let r = 0; r < gridSize; r++) {
    if (r !== row && grid[r][col].value === value) {
      conflicts.add(`${r},${col}`);
      conflicts.add(cellKey);
    }
  }

  // Check box
  const { rows: boxRows, cols: boxCols } = BOX_DIMENSIONS[gridSize];
  const { boxRow, boxCol } = getBoxPosition(row, col, gridSize);
  const startRow = boxRow * boxRows;
  const startCol = boxCol * boxCols;

  for (let r = startRow; r < startRow + boxRows; r++) {
    for (let c = startCol; c < startCol + boxCols; c++) {
      if ((r !== row || c !== col) && grid[r][c].value === value) {
        conflicts.add(`${r},${c}`);
        conflicts.add(cellKey);
      }
    }
  }

  return conflicts;
}

/**
 * Validate entire grid and mark invalid cells
 * Returns a new grid with updated isValid flags
 */
export function validateGrid(grid: CellState[][], gridSize: GridSize): CellState[][] {
  const allConflicts = new Set<string>();

  // Find all conflicts in the grid
  for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      const conflicts = findConflicts(grid, row, col, gridSize);
      conflicts.forEach((c) => allConflicts.add(c));
    }
  }

  // Create new grid with updated validity
  return grid.map((row, rowIdx) =>
    row.map((cell, colIdx) => ({
      ...cell,
      isValid: !allConflicts.has(`${rowIdx},${colIdx}`),
    })),
  );
}

/**
 * Check if the grid is completely filled (no empty cells)
 */
export function isGridComplete(grid: CellState[][]): boolean {
  return grid.every((row) => row.every((cell) => cell.value !== null));
}

/**
 * Check if the grid is valid (no conflicts)
 */
export function isGridValid(grid: CellState[][]): boolean {
  return grid.every((row) => row.every((cell) => cell.isValid));
}

/**
 * Check if the puzzle is solved (complete and valid)
 */
export function isPuzzleSolved(grid: CellState[][]): boolean {
  return isGridComplete(grid) && isGridValid(grid);
}

/**
 * Get candidates for a cell (numbers that could potentially go there)
 */
export function getCandidates(
  grid: CellState[][],
  row: number,
  col: number,
  gridSize: GridSize,
): Set<number> {
  if (grid[row][col].value !== null) {
    return new Set();
  }

  const rowValues = new Set(getRowValues(grid, row));
  const colValues = new Set(getColValues(grid, col));
  const boxValues = new Set(getBoxValues(grid, row, col, gridSize));

  const candidates = new Set<number>();

  for (let num = 1; num <= gridSize; num++) {
    if (!rowValues.has(num) && !colValues.has(num) && !boxValues.has(num)) {
      candidates.add(num);
    }
  }

  return candidates;
}
