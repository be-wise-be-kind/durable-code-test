/**
 * Purpose: Global error handler for unhandled errors and promise rejections
 * Scope: Catch errors that escape React error boundaries
 * Overview: Window-level error handling with logging and recovery
 * Dependencies: Error types, logger
 * Exports: GlobalErrorHandler class, setup function
 * Implementation: Event listeners for global error events with recovery UI
 */

import type { ErrorInfo, GlobalErrorHandlerOptions } from './ErrorBoundary.types';
import { errorLogger } from './ErrorLogger';
import { logger } from '../../utils/logger';

/**
 * GlobalErrorHandler class for handling unhandled errors
 */
export class GlobalErrorHandler {
  private options: GlobalErrorHandlerOptions;
  private errorCount = 0;
  private lastErrorTime = 0;
  private readonly ERROR_THRESHOLD = 5; // Max errors per minute
  private readonly TIME_WINDOW = 60000; // 1 minute

  constructor(options: GlobalErrorHandlerOptions = {}) {
    this.options = {
      logToConsole: true,
      logToService: false,
      ...options,
    };
  }

  /**
   * Setup global error handlers
   */
  setup(): void {
    // Handle unhandled errors
    window.addEventListener('error', this.handleError);

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', this.handleUnhandledRejection);

    // Setup performance monitoring
    this.setupPerformanceMonitoring();

    // Log setup completion
    if (this.options.logToConsole) {
      logger.error('🛡️ Global error handlers initialized');
    }
  }

  /**
   * Teardown global error handlers
   */
  teardown(): void {
    window.removeEventListener('error', this.handleError);
    window.removeEventListener('unhandledrejection', this.handleUnhandledRejection);
  }

  /**
   * Handle global errors
   */
  private handleError = (event: ErrorEvent): void => {
    // Check for error storm
    if (this.isErrorStorm()) {
      this.handleErrorStorm();
      return;
    }

    this.errorCount++;
    this.lastErrorTime = Date.now();

    const error = event.error || new Error(event.message);
    const errorInfo = {
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      type: 'global-error',
    };

    // Log the error
    errorLogger.logError(error, errorInfo as ErrorInfo);

    // Call custom handler if provided
    if (this.options.onError) {
      this.options.onError(event);
    }

    // Show error notification for critical errors
    if (this.isCriticalError(error)) {
      this.showErrorNotification(error);
    }

    // Prevent default error handling in production
    if (process.env.NODE_ENV === 'production') {
      event.preventDefault();
    }
  };

  /**
   * Handle unhandled promise rejections
   */
  private handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
    // Check for error storm
    if (this.isErrorStorm()) {
      this.handleErrorStorm();
      return;
    }

    this.errorCount++;
    this.lastErrorTime = Date.now();

    const error = new Error(
      event.reason?.message || event.reason || 'Unhandled Promise Rejection',
    );

    const errorInfo = {
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      type: 'unhandled-rejection',
      promise: event.promise,
      reason: event.reason,
    };

    // Log the error
    errorLogger.logError(error, errorInfo as ErrorInfo);

    // Call custom handler if provided
    if (this.options.onUnhandledRejection) {
      this.options.onUnhandledRejection(event);
    }

    // Show error notification for critical errors
    if (this.isCriticalError(error)) {
      this.showErrorNotification(error);
    }

    // Prevent default handling in production
    if (process.env.NODE_ENV === 'production') {
      event.preventDefault();
    }
  };

  /**
   * Check if we're experiencing an error storm
   */
  private isErrorStorm(): boolean {
    const now = Date.now();

    // Reset counter if outside time window
    if (now - this.lastErrorTime > this.TIME_WINDOW) {
      this.errorCount = 0;
    }

    return this.errorCount >= this.ERROR_THRESHOLD;
  }

  /**
   * Handle error storm situation
   */
  private handleErrorStorm(): void {
    errorLogger.logWarning('Error storm detected', {
      errorCount: this.errorCount,
      timeWindow: this.TIME_WINDOW,
    });

    // Show critical error UI
    this.showCriticalErrorUI();

    // Reset counter to prevent infinite loop
    this.errorCount = 0;
  }

  /**
   * Check if error is critical
   */
  private isCriticalError(error: Error): boolean {
    const criticalPatterns = [
      /out of memory/i,
      /maximum call stack/i,
      /network error/i,
      /failed to fetch/i,
    ];

    return criticalPatterns.some((pattern) => pattern.test(error.message));
  }

  /**
   * Show error notification to user
   */
  private showErrorNotification(error: Error): void {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('global-error-notification');

    if (!notification) {
      notification = document.createElement('div');
      notification.id = 'global-error-notification';
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #dc2626;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 12px;
      `;

      // Add animation
      const style = document.createElement('style');
      style.textContent = `
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `;
      document.head.appendChild(style);
    }

    // Create icon
    const icon = document.createElement('span');
    icon.textContent = '⚠️';
    icon.style.fontSize = '24px';

    // Create message container
    const messageContainer = document.createElement('div');

    const titleDiv = document.createElement('div');
    titleDiv.textContent = 'An error occurred';
    titleDiv.style.fontWeight = '600';
    titleDiv.style.marginBottom = '4px';

    const errorText = document.createElement('div');
    errorText.textContent = this.sanitizeErrorMessage(error.message);
    errorText.style.fontSize = '14px';
    errorText.style.opacity = '0.9';

    messageContainer.appendChild(titleDiv);
    messageContainer.appendChild(errorText);

    // Create close button
    const closeButton = document.createElement('button');
    closeButton.textContent = '×';
    closeButton.style.cssText = `
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 20px;
      padding: 0;
      margin-left: auto;
    `;
    closeButton.onclick = () => notification?.remove();

    // Append all elements
    notification.appendChild(icon);
    notification.appendChild(messageContainer);
    notification.appendChild(closeButton);

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification?.remove();
    }, 5000);
  }

  /**
   * Show critical error UI (error storm or fatal error)
   */
  private showCriticalErrorUI(): void {
    const criticalUI = document.createElement('div');
    criticalUI.id = 'critical-error-ui';
    criticalUI.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.9);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99999;
    `;

    // Create container
    const container = document.createElement('div');
    container.style.cssText = 'text-align: center; max-width: 500px; padding: 32px;';

    // Create emoji icon
    const emojiIcon = document.createElement('div');
    emojiIcon.textContent = '🚨';
    emojiIcon.style.cssText = 'font-size: 64px; margin-bottom: 24px;';

    // Create title
    const title = document.createElement('h1');
    title.textContent = 'Application Error';
    title.style.cssText = 'font-size: 28px; margin-bottom: 16px;';

    // Create description
    const description = document.createElement('p');
    description.textContent =
      'The application has encountered multiple errors and may not be functioning correctly. Please refresh the page to continue.';
    description.style.cssText = 'font-size: 16px; margin-bottom: 32px; opacity: 0.9;';

    // Create refresh button
    const refreshButton = document.createElement('button');
    refreshButton.textContent = 'Refresh Page';
    refreshButton.style.cssText = `
      background: #dc2626;
      color: white;
      border: none;
      padding: 12px 32px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
    `;
    refreshButton.onclick = () => window.location.reload();

    // Append all elements
    container.appendChild(emojiIcon);
    container.appendChild(title);
    container.appendChild(description);
    container.appendChild(refreshButton);

    criticalUI.appendChild(container);

    document.body.appendChild(criticalUI);
  }

  /**
   * Sanitize error message for display
   */
  private sanitizeErrorMessage(message: string): string {
    // Remove sensitive information from error messages
    const sanitized = message
      .replace(/https?:\/\/[^\s]+/g, '[URL]')
      .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]')
      .replace(/\b\d{4,}\b/g, '[NUMBER]');

    // Truncate long messages
    return sanitized.length > 100 ? `${sanitized.substring(0, 100)}...` : sanitized;
  }

  /**
   * Setup performance monitoring
   */
  private setupPerformanceMonitoring(): void {
    // Monitor long tasks
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              errorLogger.logWarning('Long task detected', {
                duration: entry.duration,
                name: entry.name,
                startTime: entry.startTime,
              });
            }
          }
        });

        observer.observe({ entryTypes: ['longtask'] });
      } catch {
        // Silently fail if not supported
      }
    }
  }
}

/**
 * Singleton instance
 */
let globalErrorHandler: GlobalErrorHandler | null = null;

/**
 * Setup global error handling
 */
export function setupGlobalErrorHandling(options?: GlobalErrorHandlerOptions): void {
  if (!globalErrorHandler) {
    globalErrorHandler = new GlobalErrorHandler(options);
    globalErrorHandler.setup();
  }
}

/**
 * Teardown global error handling
 */
export function teardownGlobalErrorHandling(): void {
  if (globalErrorHandler) {
    globalErrorHandler.teardown();
    globalErrorHandler = null;
  }
}

export default GlobalErrorHandler;
