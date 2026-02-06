/**
 * Purpose: Type definitions for Sudoku game feature
 * Scope: All Sudoku game related types and interfaces
 * Overview: Central type definitions for grid state, cell state, game configuration,
 *     and user interactions. Defines types for 6x6 and 9x9 grid variants, cell values
 *     with notes and uncertainty modes, validation states, and hook return types.
 *     Provides comprehensive type safety for all Sudoku game operations.
 * Dependencies: None (pure TypeScript types)
 * Exports: GridSize, Difficulty, CellState, CellPosition, UseSudokuReturn, and related types
 * Implementation: TypeScript interfaces and type aliases for Sudoku game state management
 */

/**
 * Grid size variants supported by the game
 * - 6: 6x6 grid with 2x3 boxes
 * - 9: 9x9 grid with 3x3 boxes
 */
export type GridSize = 6 | 9;

/**
 * Difficulty levels affecting number of pre-filled cells
 */
export type Difficulty = 'easy' | 'medium' | 'hard';

/**
 * Input mode for number placement
 */
export type InputMode = 'normal' | 'notes';

/**
 * Position of a cell in the grid
 */
export interface CellPosition {
  row: number;
  col: number;
}

/**
 * State of an individual cell in the Sudoku grid
 */
export interface CellState {
  /** The value in the cell (1-6 for 6x6, 1-9 for 9x9, null if empty) */
  value: number | null;
  /** Whether this cell is part of the original puzzle (read-only) */
  isOriginal: boolean;
  /** Whether the user marked this as an unsure/tentative placement */
  isUnsure: boolean;
  /** Pencil marks (candidate numbers) for this cell */
  notes: Set<number>;
  /** Whether the value conflicts with row/col/box rules */
  isValid: boolean;
}

/**
 * Box dimensions for different grid sizes
 */
export interface BoxDimensions {
  rows: number;
  cols: number;
}

/**
 * Game statistics and progress tracking
 */
export interface GameStats {
  /** Number of mistakes made */
  mistakes: number;
  /** Time elapsed in milliseconds */
  elapsedTime: number;
  /** Number of cells filled (excluding original cells) */
  filledCells: number;
  /** Total cells that need to be filled */
  totalEmptyCells: number;
  /** Percentage of puzzle completed */
  completionPercentage: number;
}

/**
 * Game state enumeration
 */
export const GameState = {
  IDLE: 'idle',
  PLAYING: 'playing',
  PAUSED: 'paused',
  COMPLETED: 'completed',
} as const;

export type GameStateType = (typeof GameState)[keyof typeof GameState];

/**
 * Configuration for generating puzzles
 */
export interface PuzzleConfig {
  gridSize: GridSize;
  difficulty: Difficulty;
  seed?: number;
}

/**
 * Props for SudokuTab component
 */
export interface SudokuTabProps {
  className?: string;
  onError?: (error: Error) => void;
}

/**
 * Props for SudokuGrid component
 */
export interface SudokuGridProps {
  grid: CellState[][];
  gridSize: GridSize;
  selectedCell: CellPosition | null;
  highlightedValue: number | null;
  keypadHighlightValue: number | null;
  inputMode: InputMode;
  isUnsureMode: boolean;
  showCellPopup: boolean;
  onCellClick: (position: CellPosition) => void;
  onNumberPlace: (num: number) => void;
  onToggleInputMode: () => void;
  onToggleUnsureMode: () => void;
  className?: string;
}

/**
 * Props for SudokuCell component
 */
export interface SudokuCellProps {
  cell: CellState;
  position: CellPosition;
  gridSize: GridSize;
  isSelected: boolean;
  isHighlighted: boolean;
  isRelated: boolean;
  isSameValue: boolean;
  keypadHighlightValue: number | null;
  popupSuggestedNumber: number | null;
  inputMode: InputMode;
  isUnsureMode: boolean;
  showCellPopup: boolean;
  onClick: () => void;
  onNumberPlace: (num: number) => void;
  onToggleInputMode: () => void;
  onToggleUnsureMode: () => void;
}

/**
 * Props for NumberPad component
 */
export interface NumberPadProps {
  gridSize: GridSize;
  activeNumber: number | null;
  onNumberClick: (num: number) => void;
  onEraseClick: () => void;
  onUndoClick: () => void;
  canUndo: boolean;
  inputMode: InputMode;
  isUnsureMode: boolean;
  showCellPopup: boolean;
  onToggleInputMode: () => void;
  onToggleUnsureMode: () => void;
  onToggleCellPopup: () => void;
  disabledNumbers: Set<number>;
  className?: string;
}

/**
 * Props for GameControls component
 */
export interface GameControlsProps {
  gridSize: GridSize;
  difficulty: Difficulty;
  gameState: GameStateType;
  currentSeed: number;
  onGridSizeChange: (size: GridSize) => void;
  onDifficultyChange: (difficulty: Difficulty) => void;
  onNewGame: () => void;
  onNewGameWithSeed: (seed: number) => void;
  onResetGame: () => void;
  className?: string;
}

/**
 * Props for StatusBar component
 */
export interface StatusBarProps {
  stats: GameStats;
  gameState: GameStateType;
  onPauseToggle: () => void;
  className?: string;
}

/**
 * Return type for useSudoku hook
 */
export interface UseSudokuReturn {
  // Grid state
  grid: CellState[][];
  gridSize: GridSize;
  difficulty: Difficulty;
  gameState: GameStateType;

  // Selection state
  selectedCell: CellPosition | null;
  highlightedValue: number | null;
  keypadHighlightValue: number | null;

  // Input mode state
  inputMode: InputMode;
  isUnsureMode: boolean;

  // Stats
  stats: GameStats;

  // Current seed for sharing puzzles
  currentSeed: number;

  // Cell actions
  selectCell: (position: CellPosition | null) => void;
  placeNumber: (num: number) => void;
  eraseCell: () => void;
  toggleNote: (num: number) => void;

  // Undo
  undoGame: () => void;
  canUndo: boolean;

  // Mode toggles
  toggleInputMode: () => void;
  toggleUnsureMode: () => void;

  // Game actions
  setGridSize: (size: GridSize) => void;
  setDifficulty: (difficulty: Difficulty) => void;
  startNewGame: () => void;
  startNewGameWithSeed: (seed: number) => void;
  resetGame: () => void;
  pauseGame: () => void;
  resumeGame: () => void;

  // Cell popup toggle
  showCellPopup: boolean;
  toggleCellPopup: () => void;

  // Utility
  getDisabledNumbers: () => Set<number>;
}

/**
 * Return type for useSudokuValidation hook
 */
export interface UseSudokuValidationReturn {
  validateGrid: (grid: CellState[][], gridSize: GridSize) => CellState[][];
  isGridComplete: (grid: CellState[][]) => boolean;
  isGridValid: (grid: CellState[][]) => boolean;
  getConflictingCells: (grid: CellState[][], gridSize: GridSize) => Set<string>;
}
