/**
 * Purpose: Status bar component showing game statistics
 * Scope: Timer, mistakes, completion percentage, and pause control
 * Overview: Displays real-time game statistics including elapsed time,
 *     mistake count, and completion percentage. Provides pause/resume
 *     functionality and shows completion message when puzzle is solved.
 * Dependencies: React, sudoku.types, sudokuHelpers
 * Exports: StatusBar component
 * Props/Interfaces: StatusBarProps
 * State/Behavior: Controlled component, stats passed from parent
 */

import { memo, useMemo } from 'react';
import type { ReactElement } from 'react';
import type { StatusBarProps } from '../../types/sudoku.types';
import { GameState } from '../../types/sudoku.types';
import { formatTime } from '../../utils/sudokuHelpers';
import styles from './StatusBar.module.css';

/**
 * StatusBar component
 * Displays game statistics and controls
 */
function StatusBarComponent({
  stats,
  gameState,
  onPauseToggle,
  className = '',
}: StatusBarProps): ReactElement {
  // Format elapsed time
  const formattedTime = useMemo(
    () => formatTime(stats.elapsedTime),
    [stats.elapsedTime],
  );

  // Container classes
  const containerClasses = useMemo(() => {
    return [
      styles.container,
      gameState === GameState.COMPLETED ? styles.completed : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');
  }, [gameState, className]);

  // Show completion message
  if (gameState === GameState.COMPLETED) {
    return (
      <div className={containerClasses}>
        <div className={styles.completionMessage}>
          <span className={styles.completionIcon}>*</span>
          <span className={styles.completionText}>Puzzle Complete!</span>
        </div>
        <div className={styles.finalStats}>
          <span>Time: {formattedTime}</span>
          <span>Mistakes: {stats.mistakes}</span>
        </div>
      </div>
    );
  }

  // Show paused overlay
  if (gameState === GameState.PAUSED) {
    return (
      <div className={containerClasses}>
        <div className={styles.pausedMessage}>
          <span>Game Paused</span>
          <button type="button" className={styles.resumeButton} onClick={onPauseToggle}>
            Resume
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={containerClasses}>
      {/* Timer */}
      <div className={styles.stat}>
        <span className={styles.statIcon}>T</span>
        <span className={styles.statValue}>{formattedTime}</span>
      </div>

      {/* Mistakes */}
      <div className={styles.stat}>
        <span className={styles.statIcon}>X</span>
        <span className={styles.statValue}>{stats.mistakes}</span>
        <span className={styles.statLabel}>mistakes</span>
      </div>

      {/* Completion */}
      <div className={styles.stat}>
        <span className={styles.statValue}>{stats.completionPercentage}%</span>
        <span className={styles.statLabel}>complete</span>
      </div>

      {/* Progress bar */}
      <div className={styles.progressContainer}>
        <div
          className={styles.progressBar}
          style={{ width: `${stats.completionPercentage}%` }}
          role="progressbar"
          aria-valuenow={stats.completionPercentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Pause button */}
      <button
        type="button"
        className={styles.pauseButton}
        onClick={onPauseToggle}
        aria-label="Pause game"
      >
        ||
      </button>
    </div>
  );
}

export const StatusBar = memo(StatusBarComponent);
