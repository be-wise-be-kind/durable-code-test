/**
 * Purpose: Error logging service for structured error tracking
 * Scope: Centralized error logging and reporting
 * Overview: Provides consistent error logging with context and metrics
 * Dependencies: Error types
 * Exports: ErrorLogger class, default instance
 * Interfaces: ErrorLogger interface implementation
 * Implementation: Console and service logging with queuing for offline scenarios
 */

import type {
  ErrorInfo,
  ErrorRecoveryAction,
  ErrorLogger as IErrorLogger,
} from './ErrorBoundary.types';
import { logger } from '../../utils/logger';

/**
 * Error log entry structure
 */
interface ErrorLogEntry {
  timestamp: number;
  level: 'error' | 'warning' | 'info';
  message: string;
  error?: Error;
  errorInfo?: ErrorInfo;
  context?: Record<string, unknown>;
  action?: ErrorRecoveryAction;
  success?: boolean;
}

/**
 * ErrorLogger implementation for structured error tracking
 */
export class ErrorLogger implements IErrorLogger {
  private logQueue: ErrorLogEntry[] = [];
  private maxQueueSize = 100;
  private isOnline = navigator.onLine;
  private serviceUrl?: string;
  private logToConsole: boolean;
  private logToService: boolean;

  constructor(
    options: {
      logToConsole?: boolean;
      logToService?: boolean;
      serviceUrl?: string;
    } = {},
  ) {
    this.logToConsole = options.logToConsole ?? true;
    this.logToService = options.logToService ?? false;
    this.serviceUrl = options.serviceUrl;

    // Monitor online status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushQueue();
    });
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  /**
   * Log an error with full context
   */
  logError(error: Error, errorInfo: ErrorInfo): void {
    const entry: ErrorLogEntry = {
      timestamp: Date.now(),
      level: 'error',
      message: error.message,
      error,
      errorInfo,
      context: {
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        errorBoundary: errorInfo.errorBoundary,
        url: errorInfo.url,
        userAgent: errorInfo.userAgent,
      },
    };

    this.log(entry);
    this.reportMetrics('error_boundary_triggered', {
      errorBoundary: errorInfo.errorBoundary || 'unknown',
      errorMessage: error.message,
    });
  }

  /**
   * Log a recovery action and its outcome
   */
  logRecovery(action: ErrorRecoveryAction, success: boolean): void {
    const entry: ErrorLogEntry = {
      timestamp: Date.now(),
      level: 'info',
      message: `Error recovery ${action} ${success ? 'succeeded' : 'failed'}`,
      action,
      success,
    };

    this.log(entry);
    this.reportMetrics('error_recovery_attempted', {
      action,
      success,
    });
  }

  /**
   * Log a warning with optional context
   */
  logWarning(message: string, context?: Record<string, unknown>): void {
    const entry: ErrorLogEntry = {
      timestamp: Date.now(),
      level: 'warning',
      message,
      context,
    };

    this.log(entry);
  }

  /**
   * Internal logging method
   */
  private log(entry: ErrorLogEntry): void {
    // Console logging
    if (this.logToConsole) {
      const style = this.getConsoleStyle(entry.level);
      logger.error(
        `[${entry.level.toUpperCase()}] ${new Date(entry.timestamp).toISOString()}`,
        style,
      );
      logger.error('Message:', entry.message);

      if (entry.error) {
        logger.error('Error:', entry.error);
      }

      if (entry.errorInfo) {
        logger.error('Error Info:', entry.errorInfo);
      }

      if (entry.context) {
        logger.error('Context:', entry.context);
      }
    }

    // Service logging
    if (this.logToService && this.serviceUrl) {
      if (this.isOnline) {
        this.sendToService(entry);
      } else {
        this.queueEntry(entry);
      }
    }
  }

  /**
   * Get console style based on log level
   */
  private getConsoleStyle(level: string): string {
    const styles: Record<string, string> = {
      error: 'color: red; font-weight: bold;',
      warning: 'color: orange; font-weight: bold;',
      info: 'color: blue;',
    };
    return styles[level] || '';
  }

  /**
   * Queue entry for later sending
   */
  private queueEntry(entry: ErrorLogEntry): void {
    this.logQueue.push(entry);

    // Maintain max queue size
    if (this.logQueue.length > this.maxQueueSize) {
      this.logQueue.shift();
    }
  }

  /**
   * Send log entry to service
   */
  private async sendToService(entry: ErrorLogEntry): Promise<void> {
    if (!this.serviceUrl) return;

    try {
      await fetch(this.serviceUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...entry,
          sessionId: this.getSessionId(),
          environment: process.env.NODE_ENV,
        }),
      });
    } catch {
      // Silently fail but queue for retry
      this.queueEntry(entry);
    }
  }

  /**
   * Flush queued log entries
   */
  private async flushQueue(): Promise<void> {
    if (!this.isOnline || this.logQueue.length === 0) return;

    const queue = [...this.logQueue];
    this.logQueue = [];

    for (const entry of queue) {
      await this.sendToService(entry);
    }
  }

  /**
   * Get or create session ID
   */
  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('errorLoggerSessionId');

    if (!sessionId) {
      sessionId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('errorLoggerSessionId', sessionId);
    }

    return sessionId;
  }

  /**
   * Report metrics for monitoring
   */
  private reportMetrics(eventName: string, metadata: Record<string, unknown>): void {
    // Integration point for analytics services
    if (
      typeof window !== 'undefined' &&
      (window as unknown as Record<string, unknown>).analytics
    ) {
      (
        (window as unknown as Record<string, unknown>).analytics as {
          track: (event: string, data: Record<string, unknown>) => void;
        }
      ).track(eventName, metadata);
    }
  }
}

// Default singleton instance
export const errorLogger = new ErrorLogger({
  logToConsole: process.env.NODE_ENV === 'development',
  logToService: process.env.NODE_ENV === 'production',
  serviceUrl: process.env.REACT_APP_ERROR_SERVICE_URL,
});

export default errorLogger;
