/**
 * Purpose: Main Sudoku game container component
 * Scope: Complete Sudoku game interface with grid, controls, and status
 * Overview: Integrates all Sudoku components into a cohesive game interface.
 *     Manages game state through useSudoku hook and orchestrates the grid,
 *     number pad, game controls, and status bar. Provides responsive layout
 *     for desktop and mobile play.
 * Dependencies: React, useSudoku hook, all Sudoku components
 * Exports: SudokuTab component
 * Props/Interfaces: SudokuTabProps
 * State/Behavior: Uses useSudoku hook for all game state management
 */

import { useCallback, useMemo } from 'react';
import type { ReactElement } from 'react';
import type { SudokuTabProps } from '../../types/sudoku.types';
import { GameState } from '../../types/sudoku.types';
import { useSudoku } from '../../hooks/useSudoku';
import { SudokuGrid } from '../SudokuGrid';
import { NumberPad } from '../NumberPad';
import { GameControls } from '../GameControls';
import { StatusBar } from '../StatusBar';
import styles from './SudokuTab.module.css';

/**
 * SudokuTab component
 * Main container for the Sudoku game
 */
export function SudokuTab({ className = '' }: SudokuTabProps): ReactElement {
  const {
    grid,
    gridSize,
    difficulty,
    gameState,
    selectedCell,
    highlightedValue,
    keypadHighlightValue,
    inputMode,
    isUnsureMode,
    stats,
    currentSeed,
    selectCell,
    placeNumber,
    eraseCell,
    undoGame,
    canUndo,
    showCellPopup,
    toggleCellPopup,
    toggleInputMode,
    toggleUnsureMode,
    setGridSize,
    setDifficulty,
    startNewGame,
    startNewGameWithSeed,
    resetGame,
    pauseGame,
    resumeGame,
    getDisabledNumbers,
  } = useSudoku();

  // Get disabled numbers for number pad
  const disabledNumbers = useMemo(() => getDisabledNumbers(), [getDisabledNumbers]);

  // Handle pause toggle
  const handlePauseToggle = useCallback(() => {
    if (gameState === GameState.PAUSED) {
      resumeGame();
    } else {
      pauseGame();
    }
  }, [gameState, pauseGame, resumeGame]);

  // Container classes
  const containerClasses = useMemo(() => {
    return [styles.container, 'tab-content', 'sudoku-content', className]
      .filter(Boolean)
      .join(' ');
  }, [className]);

  return (
    <div className={containerClasses}>
      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.title}>Sudoku</h2>
        <p className={styles.subtitle}>
          Classic number puzzle - fill the grid so each row, column, and box contains
          all numbers exactly once.
        </p>
      </div>

      {/* Status bar */}
      <StatusBar
        stats={stats}
        gameState={gameState}
        onPauseToggle={handlePauseToggle}
        className={styles.statusBar}
      />

      {/* Main game area */}
      <div className={styles.gameArea}>
        {/* Grid section */}
        <div
          className={`${styles.gridSection} ${gameState === GameState.PAUSED ? styles.gridPaused : ''}`}
        >
          <SudokuGrid
            grid={grid}
            gridSize={gridSize}
            selectedCell={selectedCell}
            highlightedValue={highlightedValue}
            keypadHighlightValue={keypadHighlightValue}
            inputMode={inputMode}
            isUnsureMode={isUnsureMode}
            showCellPopup={showCellPopup}
            onCellClick={selectCell}
            onNumberPlace={placeNumber}
            onToggleInputMode={toggleInputMode}
            onToggleUnsureMode={toggleUnsureMode}
            className={styles.grid}
          />
        </div>

        {/* Controls section */}
        <div className={styles.controlsSection}>
          {/* Number pad */}
          <NumberPad
            gridSize={gridSize}
            activeNumber={keypadHighlightValue}
            onNumberClick={placeNumber}
            onEraseClick={eraseCell}
            onUndoClick={undoGame}
            canUndo={canUndo}
            inputMode={inputMode}
            isUnsureMode={isUnsureMode}
            showCellPopup={showCellPopup}
            onToggleInputMode={toggleInputMode}
            onToggleUnsureMode={toggleUnsureMode}
            onToggleCellPopup={toggleCellPopup}
            disabledNumbers={disabledNumbers}
            className={styles.numberPad}
          />

          {/* Game controls */}
          <GameControls
            gridSize={gridSize}
            difficulty={difficulty}
            gameState={gameState}
            currentSeed={currentSeed}
            onGridSizeChange={setGridSize}
            onDifficultyChange={setDifficulty}
            onNewGame={startNewGame}
            onNewGameWithSeed={startNewGameWithSeed}
            onResetGame={resetGame}
            className={styles.gameControls}
          />
        </div>
      </div>

      {/* Instructions */}
      <div className={styles.instructions}>
        <h3>How to Play</h3>
        <ul>
          <li>
            Click a cell to select it, then click a number or use keyboard (1-{gridSize}
            )
          </li>
          <li>
            Use <strong>Notes</strong> mode (N key) to add pencil marks for candidates
          </li>
          <li>
            Use <strong>Unsure</strong> mode (U key) to mark tentative placements in
            orange
          </li>
          <li>
            Share the <strong>Seed</strong> number with others to play the same puzzle
          </li>
          <li>Arrow keys to navigate, Delete/Backspace to erase, Ctrl+Z to undo</li>
        </ul>
      </div>
    </div>
  );
}
