/**
 * Purpose: Constants and configuration values for Sudoku game
 * Scope: Game configuration, box dimensions, difficulty settings, and UI constants
 * Overview: Centralized configuration for Sudoku game behavior and appearance.
 *     Defines box dimensions for different grid sizes, difficulty-based cell removal
 *     percentages, and timing/display constants. Ensures consistent behavior across
 *     all game components and simplifies configuration changes.
 * Dependencies: sudoku.types for type definitions
 * Exports: BOX_DIMENSIONS, DIFFICULTY_CONFIG, GAME_CONSTANTS
 * Implementation: Readonly constant objects for immutable game configuration
 */

import type { BoxDimensions, Difficulty, GridSize } from '../types/sudoku.types';

/**
 * Box dimensions for each grid size
 * - 6x6 grid: 2 rows x 3 columns per box
 * - 9x9 grid: 3 rows x 3 columns per box
 */
export const BOX_DIMENSIONS: Record<GridSize, BoxDimensions> = {
  6: { rows: 2, cols: 3 },
  9: { rows: 3, cols: 3 },
} as const;

/**
 * Difficulty configuration
 * Percentage of cells to remove from a complete solution
 */
export const DIFFICULTY_CONFIG: Record<
  Difficulty,
  Record<GridSize, { removePercentage: number }>
> = {
  easy: {
    6: { removePercentage: 0.35 },
    9: { removePercentage: 0.4 },
  },
  medium: {
    6: { removePercentage: 0.45 },
    9: { removePercentage: 0.5 },
  },
  hard: {
    6: { removePercentage: 0.55 },
    9: { removePercentage: 0.6 },
  },
} as const;

/**
 * General game constants
 */
export const GAME_CONSTANTS = {
  /** Maximum mistakes before game ends (0 = unlimited) */
  MAX_MISTAKES: 0,
  /** Timer update interval in milliseconds */
  TIMER_INTERVAL: 1000,
  /** Default grid size */
  DEFAULT_GRID_SIZE: 9 as GridSize,
  /** Default difficulty */
  DEFAULT_DIFFICULTY: 'medium' as Difficulty,
  /** Animation duration in milliseconds */
  ANIMATION_DURATION: 200,
  /** Maximum undo stack depth to prevent memory bloat */
  MAX_UNDO_STACK_SIZE: 10,
  /** Enable long-press on cell to auto-fill notes with valid candidates */
  LONG_PRESS_AUTO_FILL: false,
} as const;

/**
 * Cell styling constants
 */
export const CELL_CONSTANTS = {
  /** Minimum cell size in pixels */
  MIN_CELL_SIZE: 40,
  /** Maximum cell size in pixels */
  MAX_CELL_SIZE: 64,
  /** Border width for regular cells */
  BORDER_WIDTH: 1,
  /** Border width for box separators */
  BOX_BORDER_WIDTH: 2,
} as const;

/**
 * Get the maximum value for a grid size
 */
export function getMaxValue(gridSize: GridSize): number {
  return gridSize;
}

/**
 * Get the total number of cells for a grid size
 */
export function getTotalCells(gridSize: GridSize): number {
  return gridSize * gridSize;
}

/**
 * Get box position for a cell
 */
export function getBoxPosition(
  row: number,
  col: number,
  gridSize: GridSize,
): { boxRow: number; boxCol: number } {
  const { rows, cols } = BOX_DIMENSIONS[gridSize];
  return {
    boxRow: Math.floor(row / rows),
    boxCol: Math.floor(col / cols),
  };
}

/**
 * Check if a cell is at a box boundary
 */
export function isBoxBoundary(
  row: number,
  col: number,
  gridSize: GridSize,
): { isRowBoundary: boolean; isColBoundary: boolean } {
  const { rows, cols } = BOX_DIMENSIONS[gridSize];
  return {
    isRowBoundary: row > 0 && row % rows === 0,
    isColBoundary: col > 0 && col % cols === 0,
  };
}
