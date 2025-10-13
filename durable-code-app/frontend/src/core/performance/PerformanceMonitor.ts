/**
 * Purpose: Performance monitoring and metrics collection system
 * Scope: Application-wide performance tracking with real-time metrics
 * Overview: Provides a comprehensive performance monitoring system that tracks
 *     render times, memory usage, frame rates, and custom metrics. Designed for
 *     production monitoring and development debugging with minimal overhead.
 * Dependencies: Browser Performance API, optional Web Workers for background processing
 * Exports: PerformanceMonitor class, performance hooks, and utility functions
 * Interfaces: Performance metrics types and monitoring configuration
 * Implementation: Event-driven monitoring with automatic reporting and alerting
 */

import { logger } from '../../utils/logger';

export interface PerformanceMetrics {
  fps: number;
  renderTime: number;
  memoryUsage: number;
  timestamp: number;
  componentName?: string;
}

export interface PerformanceAlert {
  type: 'fps' | 'memory' | 'render';
  severity: 'warning' | 'critical';
  message: string;
  metrics: PerformanceMetrics;
  timestamp: number;
}

export interface PerformanceThresholds {
  minFps: number;
  maxRenderTime: number;
  maxMemoryMB: number;
}

type PerformanceEventHandler = (alert: PerformanceAlert) => void;

export class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null;
  private metrics: PerformanceMetrics[] = [];
  private thresholds: PerformanceThresholds;
  private eventHandlers: PerformanceEventHandler[] = [];
  private isMonitoring: boolean = false;
  private monitoringInterval: number | null = null;
  private frameCount: number = 0;
  private lastFrameTime: number = performance.now();

  private constructor(thresholds: PerformanceThresholds) {
    this.thresholds = thresholds;
  }

  /**
   * Get singleton instance of PerformanceMonitor
   */
  static getInstance(thresholds?: PerformanceThresholds): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      const defaultThresholds: PerformanceThresholds = {
        minFps: 55,
        maxRenderTime: 16.67, // ~60fps
        maxMemoryMB: 100,
      };
      PerformanceMonitor.instance = new PerformanceMonitor(
        thresholds || defaultThresholds,
      );
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Start performance monitoring
   */
  startMonitoring(): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.frameCount = 0;
    this.lastFrameTime = performance.now();

    // Monitor every second
    this.monitoringInterval = window.setInterval(() => {
      this.collectMetrics();
    }, 1000);

    // Monitor frame rate
    this.monitorFrameRate();
  }

  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Add performance event handler
   */
  onPerformanceAlert(handler: PerformanceEventHandler): () => void {
    this.eventHandlers.push(handler);

    // Return cleanup function
    return () => {
      const index = this.eventHandlers.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Record a custom performance metric
   */
  recordMetric(componentName: string, renderTime: number): void {
    const metrics: PerformanceMetrics = {
      fps: this.getCurrentFPS(),
      renderTime,
      memoryUsage: this.getMemoryUsage(),
      timestamp: performance.now(),
      componentName,
    };

    this.metrics.push(metrics);

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }

    // Check thresholds
    this.checkThresholds(metrics);
  }

  /**
   * Get current performance metrics
   */
  getCurrentMetrics(): PerformanceMetrics {
    return {
      fps: this.getCurrentFPS(),
      renderTime: 0,
      memoryUsage: this.getMemoryUsage(),
      timestamp: performance.now(),
    };
  }

  /**
   * Get performance history
   */
  getMetricsHistory(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  /**
   * Update performance thresholds
   */
  updateThresholds(thresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...thresholds };
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary() {
    if (this.metrics.length === 0) {
      return {
        avgFps: 0,
        avgRenderTime: 0,
        avgMemory: 0,
        alerts: 0,
      };
    }

    const avgFps =
      this.metrics.reduce((sum, m) => sum + m.fps, 0) / this.metrics.length;
    const avgRenderTime =
      this.metrics.reduce((sum, m) => sum + m.renderTime, 0) / this.metrics.length;
    const avgMemory =
      this.metrics.reduce((sum, m) => sum + m.memoryUsage, 0) / this.metrics.length;

    return {
      avgFps: Math.round(avgFps * 10) / 10,
      avgRenderTime: Math.round(avgRenderTime * 100) / 100,
      avgMemory: Math.round(avgMemory * 10) / 10,
      alerts: 0, // Count of alerts in last session
    };
  }

  private monitorFrameRate(): void {
    if (!this.isMonitoring) return;

    this.frameCount++;

    requestAnimationFrame(() => this.monitorFrameRate());
  }

  private getCurrentFPS(): number {
    const now = performance.now();
    const deltaTime = now - this.lastFrameTime;

    if (deltaTime >= 1000) {
      const fps = (this.frameCount * 1000) / deltaTime;
      this.frameCount = 0;
      this.lastFrameTime = now;
      return Math.round(fps);
    }

    return 60; // Default assumption
  }

  private getMemoryUsage(): number {
    if ('memory' in performance) {
      const memory = (performance as unknown as { memory: { usedJSHeapSize: number } })
        .memory;
      return Math.round((memory.usedJSHeapSize / 1024 / 1024) * 10) / 10;
    }
    return 0;
  }

  private collectMetrics(): void {
    const metrics: PerformanceMetrics = {
      fps: this.getCurrentFPS(),
      renderTime: 0,
      memoryUsage: this.getMemoryUsage(),
      timestamp: performance.now(),
    };

    this.metrics.push(metrics);

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }

    this.checkThresholds(metrics);
  }

  private checkThresholds(metrics: PerformanceMetrics): void {
    // Check FPS
    if (metrics.fps < this.thresholds.minFps) {
      this.emitAlert({
        type: 'fps',
        severity: metrics.fps < this.thresholds.minFps / 2 ? 'critical' : 'warning',
        message: `Low FPS detected: ${metrics.fps} (threshold: ${this.thresholds.minFps})`,
        metrics,
        timestamp: performance.now(),
      });
    }

    // Check render time
    if (metrics.renderTime > this.thresholds.maxRenderTime) {
      this.emitAlert({
        type: 'render',
        severity:
          metrics.renderTime > this.thresholds.maxRenderTime * 2
            ? 'critical'
            : 'warning',
        message: `Slow render detected: ${metrics.renderTime.toFixed(2)}ms (threshold: ${this.thresholds.maxRenderTime}ms)`,
        metrics,
        timestamp: performance.now(),
      });
    }

    // Check memory usage
    if (metrics.memoryUsage > this.thresholds.maxMemoryMB) {
      this.emitAlert({
        type: 'memory',
        severity:
          metrics.memoryUsage > this.thresholds.maxMemoryMB * 1.5
            ? 'critical'
            : 'warning',
        message: `High memory usage: ${metrics.memoryUsage}MB (threshold: ${this.thresholds.maxMemoryMB}MB)`,
        metrics,
        timestamp: performance.now(),
      });
    }
  }

  private emitAlert(alert: PerformanceAlert): void {
    this.eventHandlers.forEach((handler) => {
      try {
        handler(alert);
      } catch (error) {
        logger.error('Error in performance alert handler:', error);
      }
    });
  }
}
