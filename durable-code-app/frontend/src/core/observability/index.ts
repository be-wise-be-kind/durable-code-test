/**
 * Purpose: Barrel exports for the frontend observability module
 *
 * Scope: Re-exports Grafana Faro initialization and error boundary components
 *
 * Overview: Provides a single import path for all frontend observability functionality.
 *     Consumers import initializeFaro for SDK bootstrap, getFaroInstance for runtime
 *     access to the Faro API, and FaroErrorBoundary for React error reporting.
 *
 * Dependencies: ./faro (SDK init), ./FaroErrorBoundary (error boundary component)
 *
 * Exports: initializeFaro, getFaroInstance, FaroErrorBoundary
 */

export { initializeFaro, getFaroInstance } from './faro';
export { FaroErrorBoundary } from './FaroErrorBoundary';
