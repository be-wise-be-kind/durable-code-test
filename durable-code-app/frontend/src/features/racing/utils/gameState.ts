/**
 * Purpose: Game State Management utility for racing game state transitions
 * Scope: State machine for game state transitions and validation
 * Overview: Manages valid game state transitions following a defined state machine pattern.
 *     Ensures that state changes follow allowed transitions (e.g., MENU -> RACING,
 *     RACING -> PAUSED, etc.) and prevents invalid state changes. Provides utility
 *     functions for state validation and event handling.
 * Dependencies: racing types (GameState)
 * Exports: GameStateManager class, state transition validation functions
 * Implementation: State machine pattern with transition validation
 */

import { GameState } from '../types/racing.types';
import { logger } from '../../../utils/logger';

/**
 * Valid state transitions mapping
 * Key: current state, Value: array of allowed next states
 */
const VALID_TRANSITIONS: Record<GameState, GameState[]> = {
  [GameState.MENU]: [GameState.LOADING, GameState.RACING],
  [GameState.LOADING]: [GameState.RACING, GameState.MENU],
  [GameState.RACING]: [GameState.PAUSED, GameState.FINISHED, GameState.MENU],
  [GameState.PAUSED]: [GameState.RACING, GameState.MENU],
  [GameState.FINISHED]: [GameState.MENU, GameState.RACING],
};

/**
 * State transition event types
 */
export type StateTransitionEvent = {
  from: GameState;
  to: GameState;
  timestamp: number;
  reason?: string;
};

/**
 * State change listener callback type
 */
export type StateChangeListener = (event: StateTransitionEvent) => void;

/**
 * Game State Manager for handling state transitions
 */
export class GameStateManager {
  private currentState: GameState;
  private listeners: Set<StateChangeListener> = new Set();
  private transitionHistory: StateTransitionEvent[] = [];
  private readonly maxHistorySize: number = 50;

  /**
   * Create a new GameStateManager
   * @param initialState - Starting state (default: MENU)
   */
  constructor(initialState: GameState = GameState.MENU) {
    this.currentState = initialState;
  }

  /**
   * Get the current game state
   * @returns Current state
   */
  getState(): GameState {
    return this.currentState;
  }

  /**
   * Check if a state transition is valid
   * @param fromState - Current state
   * @param toState - Target state
   * @returns True if transition is valid
   */
  static isValidTransition(fromState: GameState, toState: GameState): boolean {
    const allowedStates = VALID_TRANSITIONS[fromState];
    return allowedStates.includes(toState);
  }

  /**
   * Transition to a new state
   * @param newState - Target state
   * @param reason - Optional reason for transition
   * @returns True if transition succeeded
   * @throws Error if transition is invalid
   */
  transition(newState: GameState, reason?: string): boolean {
    if (this.currentState === newState) {
      return false; // No change needed
    }

    if (!GameStateManager.isValidTransition(this.currentState, newState)) {
      throw new Error(
        `Invalid state transition from ${this.currentState} to ${newState}`,
      );
    }

    const event: StateTransitionEvent = {
      from: this.currentState,
      to: newState,
      timestamp: Date.now(),
      reason,
    };

    this.currentState = newState;
    this.addToHistory(event);
    this.notifyListeners(event);

    return true;
  }

  /**
   * Attempt to transition to a new state without throwing on failure
   * @param newState - Target state
   * @param reason - Optional reason for transition
   * @returns True if transition succeeded, false if invalid
   */
  tryTransition(newState: GameState, reason?: string): boolean {
    try {
      return this.transition(newState, reason);
    } catch {
      return false;
    }
  }

  /**
   * Get all valid transitions from current state
   * @returns Array of valid next states
   */
  getValidTransitions(): GameState[] {
    return VALID_TRANSITIONS[this.currentState];
  }

  /**
   * Check if a specific transition is valid from current state
   * @param targetState - State to check
   * @returns True if transition is valid
   */
  canTransitionTo(targetState: GameState): boolean {
    return GameStateManager.isValidTransition(this.currentState, targetState);
  }

  /**
   * Register a listener for state changes
   * @param listener - Callback function
   * @returns Unsubscribe function
   */
  subscribe(listener: StateChangeListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Get transition history
   * @returns Array of past state transitions
   */
  getHistory(): StateTransitionEvent[] {
    return [...this.transitionHistory];
  }

  /**
   * Clear transition history
   */
  clearHistory(): void {
    this.transitionHistory = [];
  }

  /**
   * Reset to initial state
   * @param initialState - State to reset to (default: MENU)
   */
  reset(initialState: GameState = GameState.MENU): void {
    const event: StateTransitionEvent = {
      from: this.currentState,
      to: initialState,
      timestamp: Date.now(),
      reason: 'reset',
    };

    this.currentState = initialState;
    this.clearHistory();
    this.notifyListeners(event);
  }

  /**
   * Add event to transition history
   * @param event - State transition event
   */
  private addToHistory(event: StateTransitionEvent): void {
    this.transitionHistory.push(event);

    // Limit history size
    if (this.transitionHistory.length > this.maxHistorySize) {
      this.transitionHistory.shift();
    }
  }

  /**
   * Notify all listeners of state change
   * @param event - State transition event
   */
  private notifyListeners(event: StateTransitionEvent): void {
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (error) {
        logger.error('Error in state change listener:', error);
      }
    });
  }
}

/**
 * Utility function to check if a state is a playing state
 * @param state - Game state to check
 * @returns True if state is RACING or PAUSED
 */
export function isPlayingState(state: GameState): boolean {
  return state === GameState.RACING || state === GameState.PAUSED;
}

/**
 * Utility function to check if a state is active (not menu or finished)
 * @param state - Game state to check
 * @returns True if state is LOADING, RACING, or PAUSED
 */
export function isActiveState(state: GameState): boolean {
  return (
    state === GameState.LOADING ||
    state === GameState.RACING ||
    state === GameState.PAUSED
  );
}

/**
 * Get human-readable state name
 * @param state - Game state
 * @returns Formatted state name
 */
export function getStateName(state: GameState): string {
  const names: Record<GameState, string> = {
    [GameState.MENU]: 'Menu',
    [GameState.LOADING]: 'Loading',
    [GameState.RACING]: 'Racing',
    [GameState.PAUSED]: 'Paused',
    [GameState.FINISHED]: 'Finished',
  };
  return names[state];
}
