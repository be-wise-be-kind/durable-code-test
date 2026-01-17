/**
 * Purpose: Barrel exports for Sudoku feature
 * Scope: All public Sudoku feature exports
 * Overview: Provides centralized exports for the Sudoku game feature
 *     including components, hooks, types, and utilities for use by
 *     other parts of the application.
 * Dependencies: All Sudoku feature modules
 * Exports: SudokuTab, useSudoku, types, and utilities
 * Implementation: Re-export pattern for clean module boundaries
 */

// Components
export { SudokuTab } from './components/SudokuTab';
export { SudokuGrid } from './components/SudokuGrid';
export { SudokuCell } from './components/SudokuCell';
export { NumberPad } from './components/NumberPad';
export { GameControls } from './components/GameControls';
export { StatusBar } from './components/StatusBar';

// Hooks
export { useSudoku } from './hooks/useSudoku';
export { useSudokuValidation } from './hooks/useSudokuValidation';

// Types
export type {
  GridSize,
  Difficulty,
  InputMode,
  CellPosition,
  CellState,
  BoxDimensions,
  GameStats,
  GameStateType,
  PuzzleConfig,
  SudokuTabProps,
  SudokuGridProps,
  SudokuCellProps,
  NumberPadProps,
  GameControlsProps,
  StatusBarProps,
  UseSudokuReturn,
  UseSudokuValidationReturn,
} from './types/sudoku.types';
export { GameState } from './types/sudoku.types';

// Utilities
export {
  generatePuzzle,
  generateSolution,
  createEmptyGrid,
} from './utils/puzzleGenerator';
export {
  validatePlacement,
  validateGrid,
  isGridComplete,
  isGridValid,
  isPuzzleSolved,
  getCandidates,
} from './utils/puzzleValidator';
export {
  formatTime,
  cloneGrid,
  calculateStats,
  getCompletedNumbers,
} from './utils/sudokuHelpers';

// Constants
export {
  BOX_DIMENSIONS,
  DIFFICULTY_CONFIG,
  GAME_CONSTANTS,
  CELL_CONSTANTS,
} from './config/sudoku.constants';
