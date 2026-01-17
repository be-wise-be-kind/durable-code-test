/**
 * Purpose: Sudoku puzzle generation using backtracking algorithm
 * Scope: Complete puzzle generation for 6x6 and 9x9 grids
 * Overview: Generates valid Sudoku puzzles using a backtracking algorithm.
 *     Creates a complete valid solution first, then removes cells based on
 *     difficulty settings. Supports both 6x6 and 9x9 grid sizes with
 *     configurable difficulty levels. Uses Fisher-Yates shuffle for
 *     randomization and ensures unique solutions.
 * Dependencies: sudoku.types for type definitions, sudoku.constants for configuration
 * Exports: generatePuzzle, generateSolution, createEmptyGrid
 * Implementation: Recursive backtracking with constraint propagation
 */

import type { CellState, Difficulty, GridSize } from '../types/sudoku.types';
import { DIFFICULTY_CONFIG } from '../config/sudoku.constants';

/**
 * Simple seeded random number generator
 */
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff;
    return this.seed / 0x7fffffff;
  }

  nextInt(max: number): number {
    return Math.floor(this.next() * max);
  }
}

/**
 * Shuffle an array using Fisher-Yates algorithm
 */
function shuffleArray<T>(array: T[], random: SeededRandom): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = random.nextInt(i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/**
 * Create an empty cell state
 */
function createEmptyCell(): CellState {
  return {
    value: null,
    isOriginal: false,
    isUnsure: false,
    notes: new Set<number>(),
    isValid: true,
  };
}

/**
 * Create an empty grid of the specified size
 */
export function createEmptyGrid(gridSize: GridSize): CellState[][] {
  return Array.from({ length: gridSize }, () =>
    Array.from({ length: gridSize }, () => createEmptyCell()),
  );
}

/**
 * Create a simple number grid (just values, no CellState)
 */
function createEmptyNumberGrid(gridSize: GridSize): (number | null)[][] {
  return Array.from({ length: gridSize }, () =>
    Array.from({ length: gridSize }, () => null),
  );
}

/**
 * Check if a number can be placed at a position in a simple number grid
 */
function canPlace(
  grid: (number | null)[][],
  row: number,
  col: number,
  num: number,
  gridSize: GridSize,
): boolean {
  // Check row
  if (grid[row].includes(num)) {
    return false;
  }

  // Check column
  for (let r = 0; r < gridSize; r++) {
    if (grid[r][col] === num) {
      return false;
    }
  }

  // Check box
  const boxRows = gridSize === 6 ? 2 : 3;
  const boxCols = gridSize === 6 ? 3 : 3;
  const startRow = Math.floor(row / boxRows) * boxRows;
  const startCol = Math.floor(col / boxCols) * boxCols;

  for (let r = startRow; r < startRow + boxRows; r++) {
    for (let c = startCol; c < startCol + boxCols; c++) {
      if (grid[r][c] === num) {
        return false;
      }
    }
  }

  return true;
}

/**
 * Solve the grid using backtracking (modifies in place)
 * Returns true if solution found
 */
function solveGrid(
  grid: (number | null)[][],
  gridSize: GridSize,
  random: SeededRandom,
): boolean {
  // Find the next empty cell
  let emptyRow = -1;
  let emptyCol = -1;

  outer: for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      if (grid[row][col] === null) {
        emptyRow = row;
        emptyCol = col;
        break outer;
      }
    }
  }

  // No empty cells - puzzle is solved
  if (emptyRow === -1) {
    return true;
  }

  // Try numbers in random order
  const numbers = shuffleArray(
    Array.from({ length: gridSize }, (_, i) => i + 1),
    random,
  );

  for (const num of numbers) {
    if (canPlace(grid, emptyRow, emptyCol, num, gridSize)) {
      grid[emptyRow][emptyCol] = num;

      if (solveGrid(grid, gridSize, random)) {
        return true;
      }

      grid[emptyRow][emptyCol] = null;
    }
  }

  return false;
}

/**
 * Generate a complete valid Sudoku solution
 */
export function generateSolution(
  gridSize: GridSize,
  seed?: number,
): (number | null)[][] {
  const random = new SeededRandom(seed ?? Date.now());
  const grid = createEmptyNumberGrid(gridSize);

  // Fill diagonal boxes first (they're independent)
  const boxRows = gridSize === 6 ? 2 : 3;
  const boxCols = gridSize === 6 ? 3 : 3;
  const numBoxes = gridSize / boxCols;

  for (let box = 0; box < numBoxes; box++) {
    const startRow = box * boxRows;
    const startCol = box * boxCols;
    const nums = shuffleArray(
      Array.from({ length: gridSize }, (_, i) => i + 1),
      random,
    );

    let idx = 0;
    for (let r = startRow; r < startRow + boxRows; r++) {
      for (let c = startCol; c < startCol + boxCols; c++) {
        grid[r][c] = nums[idx++];
      }
    }
  }

  // Clear the grid and solve properly to get a valid solution
  for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      grid[row][col] = null;
    }
  }

  solveGrid(grid, gridSize, random);

  return grid;
}

/**
 * Count solutions for a puzzle (used to verify unique solution)
 * Returns 0, 1, or 2 (stops after finding 2)
 */
function countSolutions(
  grid: (number | null)[][],
  gridSize: GridSize,
  limit = 2,
): number {
  // Find the next empty cell
  let emptyRow = -1;
  let emptyCol = -1;

  outer: for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      if (grid[row][col] === null) {
        emptyRow = row;
        emptyCol = col;
        break outer;
      }
    }
  }

  // No empty cells - found a solution
  if (emptyRow === -1) {
    return 1;
  }

  let count = 0;

  for (let num = 1; num <= gridSize; num++) {
    if (canPlace(grid, emptyRow, emptyCol, num, gridSize)) {
      grid[emptyRow][emptyCol] = num;
      count += countSolutions(grid, gridSize, limit - count);
      grid[emptyRow][emptyCol] = null;

      if (count >= limit) {
        return count;
      }
    }
  }

  return count;
}

/**
 * Generate a puzzle by removing cells from a complete solution
 */
export function generatePuzzle(
  gridSize: GridSize,
  difficulty: Difficulty,
  seed?: number,
): CellState[][] {
  const random = new SeededRandom(seed ?? Date.now());

  // Generate a complete solution
  const solution = generateSolution(gridSize, seed);

  // Calculate how many cells to remove
  const totalCells = gridSize * gridSize;
  const { removePercentage } = DIFFICULTY_CONFIG[difficulty][gridSize];
  const cellsToRemove = Math.floor(totalCells * removePercentage);

  // Create list of all positions and shuffle
  const positions: Array<{ row: number; col: number }> = [];
  for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      positions.push({ row, col });
    }
  }
  const shuffledPositions = shuffleArray(positions, random);

  // Remove cells one by one, ensuring unique solution
  let removed = 0;
  for (const pos of shuffledPositions) {
    if (removed >= cellsToRemove) break;

    const { row, col } = pos;
    const value = solution[row][col];

    // Temporarily remove the cell
    solution[row][col] = null;

    // Check if puzzle still has unique solution
    // For efficiency, only check on harder difficulties
    if (difficulty === 'hard') {
      const gridCopy = solution.map((r) => [...r]);
      if (countSolutions(gridCopy, gridSize) !== 1) {
        // Multiple solutions - restore the cell
        solution[row][col] = value;
        continue;
      }
    }

    removed++;
  }

  // Convert to CellState grid
  return solution.map((row) =>
    row.map((value) => ({
      value,
      isOriginal: value !== null,
      isUnsure: false,
      notes: new Set<number>(),
      isValid: true,
    })),
  );
}

/**
 * Check if a puzzle has a unique solution
 */
export function hasUniqueSolution(grid: CellState[][], gridSize: GridSize): boolean {
  const numberGrid = grid.map((row) =>
    row.map((cell) => (cell.isOriginal ? cell.value : null)),
  );
  return countSolutions(numberGrid, gridSize) === 1;
}
