/**
 * Purpose: Runtime validation schemas for track API responses using Zod
 * Scope: Validates track data received from the backend to prevent security issues
 * Overview: Zod schemas for type-safe runtime validation of racing track data structures
 * Dependencies: zod library
 * Exports: TrackSchema, Track type
 * Implementation: Comprehensive validation with bounds checking for all numeric values
 */

import { z } from 'zod';

/**
 * Schema for 2D point coordinates
 */
const Point2DSchema = z.object({
  x: z.number().finite(),
  y: z.number().finite(),
});

/**
 * Schema for track boundary definitions (inner and outer boundaries)
 */
const TrackBoundarySchema = z.object({
  outer: z.array(Point2DSchema).min(3),
  inner: z.array(Point2DSchema).min(3),
});

/**
 * Complete track schema with validation rules
 * Validates all track data received from the backend API
 */
export const TrackSchema = z.object({
  start_position: Point2DSchema,
  boundaries: TrackBoundarySchema,
  track_width: z.number().min(40).max(200).finite(),
  width: z.number().min(400).max(2000).finite(),
  height: z.number().min(300).max(1500).finite(),
});

/**
 * TypeScript type inferred from the Zod schema
 */
export type Track = z.infer<typeof TrackSchema>;

/**
 * Validates track data and returns typed result
 * @throws {z.ZodError} If validation fails
 */
export function validateTrack(data: unknown): Track {
  return TrackSchema.parse(data);
}

/**
 * Safely validates track data without throwing
 * @returns {success: true, data: Track} or {success: false, error: ZodError}
 */
export function safeValidateTrack(
  data: unknown,
): z.SafeParseReturnType<unknown, Track> {
  return TrackSchema.safeParse(data);
}
