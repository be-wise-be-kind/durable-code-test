/**
 * Purpose: Performance monitoring utilities for React components
 * Scope: Development-only performance tracking and measurement
 * Overview: Provides utilities for measuring component render times and performance
 * Dependencies: Web Performance API
 * Exports: Performance measurement functions
 * Interfaces: Performance monitoring utilities
 * Implementation: Uses Performance API for accurate timing measurements
 */

import { logger } from './logger';

interface PerformanceMetrics {
  componentName: string;
  duration: number;
  timestamp: number;
}

// Store for performance metrics (development only)
const performanceMetrics: PerformanceMetrics[] = [];

/**
 * Measures component performance during render
 * @param componentName - Name of the component being measured
 * @returns Cleanup function to call after render
 */
export function measureComponentPerf(componentName: string): () => void {
  if (process.env.NODE_ENV !== 'development') {
    // No-op in production
    return () => {};
  }

  const startMark = `${componentName}-start`;
  const endMark = `${componentName}-end`;

  // Mark the start of the render
  performance.mark(startMark);

  // Return cleanup function
  return () => {
    // Mark the end of the render
    performance.mark(endMark);

    try {
      // Measure the duration
      performance.measure(componentName, startMark, endMark);

      // Get the measurement
      const measures = performance.getEntriesByName(componentName, 'measure');
      const latestMeasure = measures[measures.length - 1];

      if (latestMeasure) {
        const metrics: PerformanceMetrics = {
          componentName,
          duration: latestMeasure.duration,
          timestamp: latestMeasure.startTime,
        };

        // Store metrics
        performanceMetrics.push(metrics);

        // Log if duration exceeds threshold (16ms = 60fps)
        if (latestMeasure.duration > 16) {
          logger.warn(
            `⚠️ Slow render detected: ${componentName} took ${latestMeasure.duration.toFixed(
              2,
            )}ms`,
          );
        }
      }
    } catch (error) {
      logger.error(`Failed to measure performance for ${componentName}:`, error);
    } finally {
      // Clean up marks to prevent memory leaks
      try {
        performance.clearMarks(startMark);
        performance.clearMarks(endMark);
        performance.clearMeasures(componentName);
      } catch {
        // Ignore cleanup errors
      }
    }
  };
}

/**
 * Hook for measuring component render performance
 * @param componentName - Name of the component
 */
export function useRenderPerformance(componentName: string): void {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  // Measure on each render
  const cleanup = measureComponentPerf(componentName);
  // Cleanup immediately after render
  requestAnimationFrame(cleanup);
}

/**
 * Get performance metrics summary
 * @returns Array of performance metrics
 */
export function getPerformanceMetrics(): PerformanceMetrics[] {
  return [...performanceMetrics];
}

/**
 * Clear all stored performance metrics
 */
export function clearPerformanceMetrics(): void {
  performanceMetrics.length = 0;
}

/**
 * Log performance summary to console
 */
export function logPerformanceSummary(): void {
  if (process.env.NODE_ENV !== 'development' || performanceMetrics.length === 0) {
    return;
  }

  // Group metrics by component
  const summary = performanceMetrics.reduce(
    (acc, metric) => {
      if (!acc[metric.componentName]) {
        acc[metric.componentName] = {
          count: 0,
          totalDuration: 0,
          maxDuration: 0,
          minDuration: Infinity,
        };
      }

      const stats = acc[metric.componentName];
      stats.count++;
      stats.totalDuration += metric.duration;
      stats.maxDuration = Math.max(stats.maxDuration, metric.duration);
      stats.minDuration = Math.min(stats.minDuration, metric.duration);

      return acc;
    },
    {} as Record<
      string,
      { count: number; totalDuration: number; maxDuration: number; minDuration: number }
    >,
  );

  // Log summary table
  logger.error('📊 Performance Summary');
  Object.entries(summary).forEach(([componentName, stats]) => {
    const avgDuration = stats.totalDuration / stats.count;
    logger.error(
      `${componentName}:`,
      `Renders: ${stats.count},`,
      `Avg: ${avgDuration.toFixed(2)}ms,`,
      `Min: ${stats.minDuration.toFixed(2)}ms,`,
      `Max: ${stats.maxDuration.toFixed(2)}ms`,
    );
  });
}

/**
 * Performance observer for long tasks
 */
export function observeLongTasks(): void {
  if (process.env.NODE_ENV !== 'development' || !('PerformanceObserver' in window)) {
    return;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 50) {
          logger.error(
            `⚠️ Long task detected: ${entry.name || 'Unknown'} took ${entry.duration.toFixed(
              2,
            )}ms`,
          );
        }
      }
    });

    observer.observe({ entryTypes: ['longtask'] });
  } catch {
    // Long task observation not supported
  }
}

// Auto-enable performance monitoring in development
if (process.env.NODE_ENV === 'development') {
  // Log summary on page unload
  window.addEventListener('beforeunload', logPerformanceSummary);

  // Start observing long tasks
  observeLongTasks();

  // Expose utilities to window for debugging
  (window as unknown as Record<string, unknown>).__PERF__ = {
    measureComponentPerf,
    getPerformanceMetrics,
    clearPerformanceMetrics,
    logPerformanceSummary,
  };

  logger.error('🚀 Performance monitoring enabled. Use window.__PERF__ for debugging.');
}
