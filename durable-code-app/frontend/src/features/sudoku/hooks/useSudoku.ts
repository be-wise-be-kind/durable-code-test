/**
 * Purpose: Main Sudoku game state management hook
 * Scope: Complete game state, user actions, and game lifecycle
 * Overview: Manages all Sudoku game state including grid, selection, input modes,
 *     timer, and game lifecycle. Handles cell selection, number placement, notes
 *     mode, unsure mode, and game controls. Provides callbacks for all user
 *     interactions and maintains game statistics. Supports seeded puzzle generation
 *     for sharing puzzles between players.
 * Dependencies: React, sudoku.types, puzzleGenerator, puzzleValidator, sudokuHelpers
 * Exports: useSudoku hook
 * Implementation: React hook with useState, useCallback, useEffect, and useRef
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  CellPosition,
  CellState,
  Difficulty,
  GameStateType,
  GameStats,
  GridSize,
  InputMode,
  UseSudokuReturn,
} from '../types/sudoku.types';
import { GameState } from '../types/sudoku.types';
import { GAME_CONSTANTS } from '../config/sudoku.constants';
import { generatePuzzle } from '../utils/puzzleGenerator';
import {
  isPuzzleSolved,
  validateGrid,
  validatePlacement,
} from '../utils/puzzleValidator';
import {
  calculateStats,
  clearRelatedNotes,
  cloneGrid,
  getCompletedNumbers,
  updateCell,
} from '../utils/sudokuHelpers';

/**
 * Generate a random seed value
 */
function generateSeed(): number {
  return Math.floor(Math.random() * 1000000);
}

/**
 * Main Sudoku game hook
 * Manages complete game state and provides action handlers
 */
export function useSudoku(): UseSudokuReturn {
  // Generate initial seed
  const initialSeed = useRef(generateSeed());

  // Core game state
  const [gridSize, setGridSizeState] = useState<GridSize>(
    GAME_CONSTANTS.DEFAULT_GRID_SIZE,
  );
  const [difficulty, setDifficultyState] = useState<Difficulty>(
    GAME_CONSTANTS.DEFAULT_DIFFICULTY,
  );
  const [currentSeed, setCurrentSeed] = useState<number>(initialSeed.current);
  const [grid, setGrid] = useState<CellState[][]>(() =>
    generatePuzzle(
      GAME_CONSTANTS.DEFAULT_GRID_SIZE,
      GAME_CONSTANTS.DEFAULT_DIFFICULTY,
      initialSeed.current,
    ),
  );
  const [gameState, setGameState] = useState<GameStateType>(GameState.PLAYING);

  // Selection state
  const [selectedCell, setSelectedCell] = useState<CellPosition | null>(null);

  // Input mode state
  const [inputMode, setInputMode] = useState<InputMode>('normal');
  const [isUnsureMode, setIsUnsureMode] = useState(false);
  const [showCellPopup, setShowCellPopup] = useState(true);

  // Stats
  const [mistakes, setMistakes] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Timer ref
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Original puzzle for reset
  const originalPuzzleRef = useRef<CellState[][]>(grid);

  // Undo stack (ref to avoid unnecessary re-renders)
  const undoStackRef = useRef<CellState[][][]>([]);
  const [undoStackLength, setUndoStackLength] = useState(0);
  const canUndo = undoStackLength > 0;

  // Keypad highlight state
  const [keypadHighlightValue, setKeypadHighlightValue] = useState<number | null>(null);

  // Get highlighted value (keypad takes precedence over selected cell)
  const cellValue =
    selectedCell !== null ? grid[selectedCell.row][selectedCell.col].value : null;
  const highlightedValue = keypadHighlightValue ?? cellValue;

  // Calculate stats
  const stats: GameStats = calculateStats(grid, elapsedTime, mistakes);

  /**
   * Start the timer
   */
  const startTimer = useCallback(() => {
    if (timerRef.current) return;
    timerRef.current = setInterval(() => {
      setElapsedTime((prev) => prev + GAME_CONSTANTS.TIMER_INTERVAL);
    }, GAME_CONSTANTS.TIMER_INTERVAL);
  }, []);

  /**
   * Stop the timer
   */
  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  /**
   * Push current grid state onto the undo stack
   */
  const pushUndo = useCallback((currentGrid: CellState[][]) => {
    const stack = undoStackRef.current;
    stack.push(cloneGrid(currentGrid));
    if (stack.length > GAME_CONSTANTS.MAX_UNDO_STACK_SIZE) {
      stack.shift();
    }
    setUndoStackLength(stack.length);
  }, []);

  /**
   * Clear the undo stack
   */
  const clearUndoStack = useCallback(() => {
    undoStackRef.current = [];
    setUndoStackLength(0);
  }, []);

  /**
   * Core placement logic: mutates the grid to place a number at a position.
   * Handles undo, notes mode, validation, and completion checks.
   */
  const performPlacement = useCallback(
    (num: number, position: CellPosition) => {
      if (gameState !== GameState.PLAYING) return;

      const cell = grid[position.row][position.col];
      if (cell.isOriginal) return;

      // Cannot overwrite a cell that already has a value — erase first
      if (cell.value !== null) return;

      pushUndo(grid);

      // In notes mode, toggle the note instead
      if (inputMode === 'notes') {
        const newNotes = new Set(cell.notes);
        if (newNotes.has(num)) {
          newNotes.delete(num);
        } else {
          newNotes.add(num);
        }
        setGrid(updateCell(grid, position, { notes: newNotes }));
        return;
      }

      // Normal mode - place the number
      const isValid = validatePlacement(
        grid,
        position.row,
        position.col,
        num,
        gridSize,
      );

      if (!isValid) {
        setMistakes((prev) => prev + 1);
      }

      let updatedGrid = updateCell(grid, position, {
        value: num,
        isUnsure: isUnsureMode,
        notes: new Set<number>(),
      });

      updatedGrid = clearRelatedNotes(updatedGrid, position, num, gridSize);
      updatedGrid = validateGrid(updatedGrid, gridSize);
      setGrid(updatedGrid);

      if (isPuzzleSolved(updatedGrid)) {
        setGameState(GameState.COMPLETED);
        stopTimer();
      }
    },
    [gameState, grid, gridSize, inputMode, isUnsureMode, pushUndo, stopTimer],
  );

  /**
   * Select a cell. Clicking the already-selected cell toggles selection off
   * (dismissing the popup). Keeps keypad highlight sticky.
   */
  const selectCell = useCallback(
    (position: CellPosition | null) => {
      if (
        position !== null &&
        selectedCell !== null &&
        position.row === selectedCell.row &&
        position.col === selectedCell.col
      ) {
        setSelectedCell(null);
        return;
      }
      setSelectedCell(position);
    },
    [selectedCell],
  );

  /**
   * Place a number in the selected cell (called from keypad/keyboard)
   */
  const placeNumber = useCallback(
    (num: number) => {
      setKeypadHighlightValue(num);

      if (!selectedCell || gameState !== GameState.PLAYING) {
        setSelectedCell(null);
        return;
      }

      if (grid[selectedCell.row][selectedCell.col].isOriginal) {
        setSelectedCell(null);
        return;
      }

      performPlacement(num, selectedCell);
    },
    [selectedCell, gameState, grid, performPlacement],
  );

  /**
   * Erase the selected cell
   */
  const eraseCell = useCallback(() => {
    if (!selectedCell || gameState !== GameState.PLAYING) return;

    const cell = grid[selectedCell.row][selectedCell.col];

    // Cannot modify original cells
    if (cell.isOriginal) return;

    // Save grid state for undo before mutation
    pushUndo(grid);

    // Clear value and notes
    let updatedGrid = updateCell(grid, selectedCell, {
      value: null,
      isUnsure: false,
      notes: new Set<number>(),
    });

    // Revalidate grid
    updatedGrid = validateGrid(updatedGrid, gridSize);

    setGrid(updatedGrid);
  }, [selectedCell, grid, gridSize, gameState, pushUndo]);

  /**
   * Toggle a note in the selected cell
   */
  const toggleNote = useCallback(
    (num: number) => {
      if (!selectedCell || gameState !== GameState.PLAYING) return;

      const cell = grid[selectedCell.row][selectedCell.col];

      // Cannot modify original cells or cells with values
      if (cell.isOriginal || cell.value !== null) return;

      const newNotes = new Set(cell.notes);
      if (newNotes.has(num)) {
        newNotes.delete(num);
      } else {
        newNotes.add(num);
      }

      const updatedGrid = updateCell(grid, selectedCell, { notes: newNotes });
      setGrid(updatedGrid);
    },
    [selectedCell, grid, gameState],
  );

  /**
   * Toggle input mode between normal and notes
   */
  const toggleInputMode = useCallback(() => {
    setInputMode((prev) => (prev === 'normal' ? 'notes' : 'normal'));
  }, []);

  /**
   * Toggle unsure mode
   */
  const toggleUnsureMode = useCallback(() => {
    setIsUnsureMode((prev) => !prev);
  }, []);

  /**
   * Toggle cell popup keypad
   */
  const toggleCellPopup = useCallback(() => {
    setShowCellPopup((prev) => !prev);
  }, []);

  /**
   * Undo the last grid mutation
   */
  const undoGame = useCallback(() => {
    if (gameState !== GameState.PLAYING) return;

    const stack = undoStackRef.current;
    const previousGrid = stack.pop();
    if (!previousGrid) return;

    setUndoStackLength(stack.length);

    // Revalidate and set the restored grid
    const revalidated = validateGrid(previousGrid, gridSize);
    setGrid(revalidated);
  }, [gameState, gridSize]);

  /**
   * Set grid size and start new game
   */
  const setGridSize = useCallback(
    (size: GridSize) => {
      if (size === gridSize) return;
      setGridSizeState(size);
      const newSeed = generateSeed();
      setCurrentSeed(newSeed);
      const newPuzzle = generatePuzzle(size, difficulty, newSeed);
      setGrid(newPuzzle);
      originalPuzzleRef.current = cloneGrid(newPuzzle);
      setSelectedCell(null);
      setMistakes(0);
      setElapsedTime(0);
      setGameState(GameState.PLAYING);
      clearUndoStack();
      setKeypadHighlightValue(null);
      stopTimer();
      startTimer();
    },
    [gridSize, difficulty, stopTimer, startTimer, clearUndoStack],
  );

  /**
   * Set difficulty and start new game
   */
  const setDifficulty = useCallback(
    (diff: Difficulty) => {
      if (diff === difficulty) return;
      setDifficultyState(diff);
      const newSeed = generateSeed();
      setCurrentSeed(newSeed);
      const newPuzzle = generatePuzzle(gridSize, diff, newSeed);
      setGrid(newPuzzle);
      originalPuzzleRef.current = cloneGrid(newPuzzle);
      setSelectedCell(null);
      setMistakes(0);
      setElapsedTime(0);
      setGameState(GameState.PLAYING);
      clearUndoStack();
      setKeypadHighlightValue(null);
      stopTimer();
      startTimer();
    },
    [gridSize, difficulty, stopTimer, startTimer, clearUndoStack],
  );

  /**
   * Start a new game with current settings and a new random seed
   */
  const startNewGame = useCallback(() => {
    const newSeed = generateSeed();
    setCurrentSeed(newSeed);
    const newPuzzle = generatePuzzle(gridSize, difficulty, newSeed);
    setGrid(newPuzzle);
    originalPuzzleRef.current = cloneGrid(newPuzzle);
    setSelectedCell(null);
    setMistakes(0);
    setElapsedTime(0);
    setInputMode('normal');
    setIsUnsureMode(false);
    setGameState(GameState.PLAYING);
    clearUndoStack();
    setKeypadHighlightValue(null);
    stopTimer();
    startTimer();
  }, [gridSize, difficulty, stopTimer, startTimer, clearUndoStack]);

  /**
   * Start a new game with a specific seed (for playing same puzzle as someone else)
   */
  const startNewGameWithSeed = useCallback(
    (seed: number) => {
      setCurrentSeed(seed);
      const newPuzzle = generatePuzzle(gridSize, difficulty, seed);
      setGrid(newPuzzle);
      originalPuzzleRef.current = cloneGrid(newPuzzle);
      setSelectedCell(null);
      setMistakes(0);
      setElapsedTime(0);
      setInputMode('normal');
      setIsUnsureMode(false);
      setGameState(GameState.PLAYING);
      clearUndoStack();
      setKeypadHighlightValue(null);
      stopTimer();
      startTimer();
    },
    [gridSize, difficulty, stopTimer, startTimer, clearUndoStack],
  );

  /**
   * Reset current game to original state
   */
  const resetGame = useCallback(() => {
    setGrid(cloneGrid(originalPuzzleRef.current));
    setSelectedCell(null);
    setMistakes(0);
    setElapsedTime(0);
    setInputMode('normal');
    setIsUnsureMode(false);
    setGameState(GameState.PLAYING);
    clearUndoStack();
    setKeypadHighlightValue(null);
    stopTimer();
    startTimer();
  }, [stopTimer, startTimer, clearUndoStack]);

  /**
   * Pause the game
   */
  const pauseGame = useCallback(() => {
    if (gameState === GameState.PLAYING) {
      setGameState(GameState.PAUSED);
      stopTimer();
    }
  }, [gameState, stopTimer]);

  /**
   * Resume the game
   */
  const resumeGame = useCallback(() => {
    if (gameState === GameState.PAUSED) {
      setGameState(GameState.PLAYING);
      startTimer();
    }
  }, [gameState, startTimer]);

  /**
   * Get disabled numbers (already complete in grid)
   */
  const getDisabledNumbers = useCallback(() => {
    return getCompletedNumbers(grid, gridSize);
  }, [grid, gridSize]);

  // Start timer on mount
  useEffect(() => {
    startTimer();
    return () => stopTimer();
  }, [startTimer, stopTimer]);

  // Handle keyboard input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (gameState !== GameState.PLAYING) return;

      // Ctrl+Z / Cmd+Z for undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        undoGame();
        return;
      }

      // Number keys 1-9
      if (e.key >= '1' && e.key <= String(gridSize)) {
        placeNumber(parseInt(e.key, 10));
        return;
      }

      // Arrow keys for navigation
      if (
        selectedCell &&
        ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)
      ) {
        e.preventDefault();
        let newRow = selectedCell.row;
        let newCol = selectedCell.col;

        switch (e.key) {
          case 'ArrowUp':
            newRow = Math.max(0, selectedCell.row - 1);
            break;
          case 'ArrowDown':
            newRow = Math.min(gridSize - 1, selectedCell.row + 1);
            break;
          case 'ArrowLeft':
            newCol = Math.max(0, selectedCell.col - 1);
            break;
          case 'ArrowRight':
            newCol = Math.min(gridSize - 1, selectedCell.col + 1);
            break;
        }

        setSelectedCell({ row: newRow, col: newCol });
        return;
      }

      // Delete/Backspace to erase
      if (e.key === 'Delete' || e.key === 'Backspace') {
        eraseCell();
        return;
      }

      // N for notes mode toggle
      if (e.key === 'n' || e.key === 'N') {
        toggleInputMode();
        return;
      }

      // U for unsure mode toggle
      if (e.key === 'u' || e.key === 'U') {
        toggleUnsureMode();
        return;
      }

      // Escape to deselect
      if (e.key === 'Escape') {
        setSelectedCell(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    selectedCell,
    gridSize,
    gameState,
    placeNumber,
    eraseCell,
    toggleInputMode,
    toggleUnsureMode,
    undoGame,
  ]);

  return {
    // Grid state
    grid,
    gridSize,
    difficulty,
    gameState,

    // Selection state
    selectedCell,
    highlightedValue,
    keypadHighlightValue,

    // Input mode state
    inputMode,
    isUnsureMode,
    showCellPopup,

    // Stats
    stats,

    // Current seed for sharing puzzles
    currentSeed,

    // Cell actions
    selectCell,
    placeNumber,
    eraseCell,
    toggleNote,

    // Undo
    undoGame,
    canUndo,

    // Mode toggles
    toggleInputMode,
    toggleUnsureMode,
    toggleCellPopup,

    // Game actions
    setGridSize,
    setDifficulty,
    startNewGame,
    startNewGameWithSeed,
    resetGame,
    pauseGame,
    resumeGame,

    // Utility
    getDisabledNumbers,
  };
}
