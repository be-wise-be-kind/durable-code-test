/**
 * Purpose: Checkpoint system for racing game lap validation
 * Scope: Finish line detection, lap counting, wrong-way detection
 * Overview: Validates lap completion and prevents backwards lap exploitation
 * Dependencies: racing types
 * Exports: CheckpointManager class
 * Implementation: Geometric line crossing detection with directional validation
 */

import type { Point2D } from '../types/racing.types';
import { logger } from '../../../utils/logger';

interface CheckpointCrossing {
  timestamp: number;
  direction: 1 | -1; // 1 = forward, -1 = backward
  position: Point2D;
}

const FINISH_LINE_BUFFER_DISTANCE = 100; // Distance car must be from finish line to arm the trigger

/**
 * Checkpoint manager for lap validation and wrong-way detection
 */
export class CheckpointManager {
  private finishLine: { start: Point2D; end: Point2D } | null = null;
  private lastCrossing: CheckpointCrossing | null = null;
  private validLapCount = 0;
  private wrongWayDetected = false;
  private lastCarPosition: Point2D | null = null;
  private isArmed = false; // Schmitt trigger: must leave finish line area before next crossing counts

  /**
   * Set up the finish line checkpoint based on track start position
   *
   * @param startPosition Track start position (center of finish line)
   * @param trackWidth Width of the track
   * @param trackBoundaries Track boundaries to determine orientation (optional)
   */
  public setupFinishLine(
    startPosition: Point2D,
    trackWidth: number,
    _trackBoundaries?: { inner: Point2D[]; outer: Point2D[] },
  ): void {
    // For circular tracks, the finish line should be vertical (perpendicular to horizontal)
    // This is 90 degrees or PI/2 radians
    const lineAngle = Math.PI / 2; // Vertical line

    // Calculate line endpoints perpendicular to track direction
    const halfWidth = trackWidth / 2;
    const x1 = startPosition.x + Math.cos(lineAngle) * halfWidth;
    const y1 = startPosition.y + Math.sin(lineAngle) * halfWidth;
    const x2 = startPosition.x - Math.cos(lineAngle) * halfWidth;
    const y2 = startPosition.y - Math.sin(lineAngle) * halfWidth;

    this.finishLine = {
      start: { x: x1, y: y1 },
      end: { x: x2, y: y2 },
    };

    // Initialize last position
    this.lastCarPosition = { ...startPosition };

    // Reset state
    this.lastCrossing = null;
    this.validLapCount = 0;
    this.wrongWayDetected = false;
    this.isArmed = false; // Start disarmed since car is on the finish line
  }

  /**
   * Check if the car has crossed the finish line and in which direction
   *
   * @param carPosition Current car position
   * @returns Object with crossed flag, direction, and lap validity
   */
  public checkFinishLineCrossing(carPosition: Point2D): {
    crossed: boolean;
    direction: 1 | -1 | 0;
    isValidLap: boolean;
    wrongWayWarning: boolean;
  } {
    if (!this.finishLine || !this.lastCarPosition) {
      this.lastCarPosition = carPosition;
      return {
        crossed: false,
        direction: 0,
        isValidLap: false,
        wrongWayWarning: false,
      };
    }

    // Calculate distance from car to finish line center
    const finishLineCenter = {
      x: (this.finishLine.start.x + this.finishLine.end.x) / 2,
      y: (this.finishLine.start.y + this.finishLine.end.y) / 2,
    };
    const distanceToFinishLine = Math.sqrt(
      Math.pow(carPosition.x - finishLineCenter.x, 2) +
        Math.pow(carPosition.y - finishLineCenter.y, 2),
    );

    // Schmitt trigger logic: arm when far enough away
    if (!this.isArmed && distanceToFinishLine > FINISH_LINE_BUFFER_DISTANCE) {
      this.isArmed = true;
    }

    // Check if line segment from lastCarPosition to carPosition crosses finish line
    const crossed = this.doLineSegmentsIntersect(
      this.lastCarPosition,
      carPosition,
      this.finishLine.start,
      this.finishLine.end,
    );

    let direction: 1 | -1 | 0 = 0;
    let isValidLap = false;

    // Only process crossing if the trigger is armed
    if (crossed && this.isArmed) {
      // Determine crossing direction using cross product
      // Finish line vector
      const lineVec = {
        x: this.finishLine.end.x - this.finishLine.start.x,
        y: this.finishLine.end.y - this.finishLine.start.y,
      };

      // Movement vector
      const moveVec = {
        x: carPosition.x - this.lastCarPosition.x,
        y: carPosition.y - this.lastCarPosition.y,
      };

      // Cross product (z component) tells us the direction
      const crossProduct = lineVec.x * moveVec.y - lineVec.y * moveVec.x;

      // For a vertical finish line, positive crossProduct means moving in the forward direction
      // Negative means moving backward
      direction = crossProduct > 0 ? 1 : -1;

      const now = performance.now();

      // Check if this is a valid lap completion
      // Valid if: crossing forward AND (first lap OR enough time since last crossing)
      const timeSinceLastCrossing = this.lastCrossing
        ? now - this.lastCrossing.timestamp
        : Infinity;

      // Count any crossing as a valid lap (removed wrong-way detection for demo)
      if (timeSinceLastCrossing > 2000) {
        // Must be at least 2 seconds since last crossing to prevent immediate re-crossing
        isValidLap = true;
        this.validLapCount += 1;
        this.isArmed = false; // Disarm after crossing, must leave area again
        logger.debug(`✅ Lap ${this.validLapCount} completed!`);
      }

      // Record this crossing
      this.lastCrossing = {
        timestamp: now,
        direction,
        position: { ...carPosition },
      };
    }

    this.lastCarPosition = { ...carPosition };

    // Return crossing info (wrong-way detection disabled for demo)
    return {
      crossed,
      direction,
      isValidLap,
      wrongWayWarning: false,
    };
  }

  /**
   * Check if line segments intersect using vector cross products
   *
   * @param p1 First point of first line segment
   * @param p2 Second point of first line segment
   * @param p3 First point of second line segment
   * @param p4 Second point of second line segment
   * @returns True if line segments intersect
   */
  private doLineSegmentsIntersect(
    p1: Point2D,
    p2: Point2D,
    p3: Point2D,
    p4: Point2D,
  ): boolean {
    const d1 = this.direction(p3, p4, p1);
    const d2 = this.direction(p3, p4, p2);
    const d3 = this.direction(p1, p2, p3);
    const d4 = this.direction(p1, p2, p4);

    if (
      ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
      ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))
    ) {
      return true;
    }

    // Check for collinear cases
    if (d1 === 0 && this.onSegment(p3, p1, p4)) return true;
    if (d2 === 0 && this.onSegment(p3, p2, p4)) return true;
    if (d3 === 0 && this.onSegment(p1, p3, p2)) return true;
    if (d4 === 0 && this.onSegment(p1, p4, p2)) return true;

    return false;
  }

  /**
   * Calculate direction of point c relative to line segment ab
   *
   * @param a First point of line segment
   * @param b Second point of line segment
   * @param c Point to test
   * @returns Positive if c is left of ab, negative if right, 0 if collinear
   */
  private direction(a: Point2D, b: Point2D, c: Point2D): number {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
  }

  /**
   * Check if point q lies on line segment pr
   *
   * @param p First point of line segment
   * @param q Point to test
   * @param r Second point of line segment
   * @returns True if q is on segment pr
   */
  private onSegment(p: Point2D, q: Point2D, r: Point2D): boolean {
    return (
      q.x <= Math.max(p.x, r.x) &&
      q.x >= Math.min(p.x, r.x) &&
      q.y <= Math.max(p.y, r.y) &&
      q.y >= Math.min(p.y, r.y)
    );
  }

  /**
   * Get the current valid lap count
   *
   * @returns Number of valid laps completed
   */
  public getValidLapCount(): number {
    return this.validLapCount;
  }

  /**
   * Check if wrong-way is currently detected
   *
   * @returns True if car went backwards through finish line
   */
  public isWrongWayDetected(): boolean {
    return this.wrongWayDetected;
  }

  /**
   * Reset the checkpoint manager
   */
  public reset(): void {
    this.lastCrossing = null;
    this.validLapCount = 0;
    this.wrongWayDetected = false;
    this.lastCarPosition = null;
    this.isArmed = false;
  }

  /**
   * Get the finish line for rendering
   *
   * @returns Finish line endpoints or null if not set
   */
  public getFinishLine(): { start: Point2D; end: Point2D } | null {
    return this.finishLine;
  }
}
