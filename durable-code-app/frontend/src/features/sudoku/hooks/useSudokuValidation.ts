/**
 * Purpose: React hook for Sudoku grid validation
 * Scope: Grid validation, conflict detection, and completion checking
 * Overview: Provides memoized validation functions for Sudoku grids.
 *     Validates entire grids, detects conflicts between cells, and checks
 *     for puzzle completion. Optimized with useCallback for performance
 *     in React components.
 * Dependencies: React, sudoku.types, puzzleValidator utilities
 * Exports: useSudokuValidation hook
 * Implementation: React hook with memoized validation callbacks
 */

import { useCallback } from 'react';
import type {
  CellState,
  GridSize,
  UseSudokuValidationReturn,
} from '../types/sudoku.types';
import {
  isGridComplete as checkGridComplete,
  isGridValid as checkGridValid,
  findConflicts,
  validateGrid as performValidation,
} from '../utils/puzzleValidator';

/**
 * Hook for Sudoku grid validation
 * Provides memoized validation functions for grid state management
 */
export function useSudokuValidation(): UseSudokuValidationReturn {
  /**
   * Validate entire grid and update cell validity flags
   */
  const validateGrid = useCallback(
    (grid: CellState[][], gridSize: GridSize): CellState[][] => {
      return performValidation(grid, gridSize);
    },
    [],
  );

  /**
   * Check if the grid is completely filled
   */
  const isGridComplete = useCallback((grid: CellState[][]): boolean => {
    return checkGridComplete(grid);
  }, []);

  /**
   * Check if the grid has no conflicts
   */
  const isGridValid = useCallback((grid: CellState[][]): boolean => {
    return checkGridValid(grid);
  }, []);

  /**
   * Get all cells that have conflicts
   * Returns a Set of cell keys in "row,col" format
   */
  const getConflictingCells = useCallback(
    (grid: CellState[][], gridSize: GridSize): Set<string> => {
      const allConflicts = new Set<string>();

      for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
          if (grid[row][col].value !== null) {
            const conflicts = findConflicts(grid, row, col, gridSize);
            conflicts.forEach((c) => allConflicts.add(c));
          }
        }
      }

      return allConflicts;
    },
    [],
  );

  return {
    validateGrid,
    isGridComplete,
    isGridValid,
    getConflictingCells,
  };
}
