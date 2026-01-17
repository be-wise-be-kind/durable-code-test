/**
 * Purpose: Game controls component for Sudoku settings and actions
 * Scope: Grid size, difficulty, new game, reset, and seed input
 * Overview: Provides controls for configuring and managing Sudoku games.
 *     Includes grid size toggle, difficulty selector, new game and reset buttons,
 *     and seed input for playing the same puzzle on different devices.
 * Dependencies: React, sudoku.types
 * Exports: GameControls component
 * Props/Interfaces: GameControlsProps
 * State/Behavior: Controlled component with local state for seed input
 */

import { memo, useCallback, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import type { Difficulty, GameControlsProps, GridSize } from '../../types/sudoku.types';
import styles from './GameControls.module.css';

/**
 * GameControls component
 * Provides game configuration and control buttons
 */
function GameControlsComponent({
  gridSize,
  difficulty,
  currentSeed,
  onGridSizeChange,
  onDifficultyChange,
  onNewGame,
  onNewGameWithSeed,
  onResetGame,
  className = '',
}: GameControlsProps): ReactElement {
  // Local state for seed input
  const [seedInput, setSeedInput] = useState('');
  const [showSeedInput, setShowSeedInput] = useState(false);

  // Handle grid size change
  const handleGridSizeChange = useCallback(
    (size: GridSize) => {
      onGridSizeChange(size);
    },
    [onGridSizeChange],
  );

  // Handle difficulty change
  const handleDifficultyChange = useCallback(
    (diff: Difficulty) => {
      onDifficultyChange(diff);
    },
    [onDifficultyChange],
  );

  // Handle seed submission
  const handleSeedSubmit = useCallback(() => {
    const seed = parseInt(seedInput, 10);
    if (!isNaN(seed) && seed > 0) {
      onNewGameWithSeed(seed);
      setSeedInput('');
      setShowSeedInput(false);
    }
  }, [seedInput, onNewGameWithSeed]);

  // Copy current seed to clipboard
  const handleCopySeed = useCallback(() => {
    navigator.clipboard.writeText(currentSeed.toString());
  }, [currentSeed]);

  // Container classes
  const containerClasses = useMemo(() => {
    return [styles.container, className].filter(Boolean).join(' ');
  }, [className]);

  return (
    <div className={containerClasses}>
      {/* Grid size toggle */}
      <div className={styles.controlGroup}>
        <label className={styles.label}>Grid Size</label>
        <div className={styles.buttonGroup}>
          <button
            type="button"
            className={`${styles.toggleButton} ${gridSize === 6 ? styles.active : ''}`}
            onClick={() => handleGridSizeChange(6)}
          >
            6x6
          </button>
          <button
            type="button"
            className={`${styles.toggleButton} ${gridSize === 9 ? styles.active : ''}`}
            onClick={() => handleGridSizeChange(9)}
          >
            9x9
          </button>
        </div>
      </div>

      {/* Difficulty selector */}
      <div className={styles.controlGroup}>
        <label className={styles.label}>Difficulty</label>
        <div className={styles.buttonGroup}>
          <button
            type="button"
            className={`${styles.toggleButton} ${
              difficulty === 'easy' ? styles.active : ''
            }`}
            onClick={() => handleDifficultyChange('easy')}
          >
            Easy
          </button>
          <button
            type="button"
            className={`${styles.toggleButton} ${
              difficulty === 'medium' ? styles.active : ''
            }`}
            onClick={() => handleDifficultyChange('medium')}
          >
            Medium
          </button>
          <button
            type="button"
            className={`${styles.toggleButton} ${
              difficulty === 'hard' ? styles.active : ''
            }`}
            onClick={() => handleDifficultyChange('hard')}
          >
            Hard
          </button>
        </div>
      </div>

      {/* Seed display and input */}
      <div className={styles.controlGroup}>
        <label className={styles.label}>Puzzle Seed</label>
        <div className={styles.seedDisplay}>
          <span className={styles.seedValue}>{currentSeed}</span>
          <button
            type="button"
            className={styles.smallButton}
            onClick={handleCopySeed}
            title="Copy seed to clipboard"
          >
            Copy
          </button>
        </div>

        {showSeedInput ? (
          <div className={styles.seedInputRow}>
            <input
              type="number"
              className={styles.seedInput}
              value={seedInput}
              onChange={(e) => setSeedInput(e.target.value)}
              placeholder="Enter seed..."
              min="1"
            />
            <button
              type="button"
              className={styles.smallButton}
              onClick={handleSeedSubmit}
            >
              Go
            </button>
            <button
              type="button"
              className={styles.smallButton}
              onClick={() => setShowSeedInput(false)}
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            className={styles.linkButton}
            onClick={() => setShowSeedInput(true)}
          >
            Enter seed to play same puzzle
          </button>
        )}
      </div>

      {/* Game actions */}
      <div className={styles.controlGroup}>
        <div className={styles.actionButtons}>
          <button type="button" className={styles.primaryButton} onClick={onNewGame}>
            New Game
          </button>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={onResetGame}
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}

export const GameControls = memo(GameControlsComponent);
