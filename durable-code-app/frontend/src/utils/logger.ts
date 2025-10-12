/**
 * Purpose: Environment-aware logging utility to prevent information disclosure in production
 * Scope: Secure logging that only outputs to console in development mode
 * Overview: Provides logger methods (debug, info, warn, error) that respect environment settings
 * Dependencies: None (uses import.meta.env for environment detection)
 * Exports: logger singleton with secure logging methods
 * Implementation: Logging utility with production-safe behavior and optional service integration
 */

/* eslint-disable no-console */
// This file is the logger utility itself and needs to use console methods internally

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Secure logger that prevents information disclosure in production
 * In development: logs to console
 * In production: suppresses debug/info, sends warn/error to logging service
 */
class SecureLogger {
  private isDevelopment = import.meta.env.DEV;

  /**
   * Debug logging - only in development
   */
  debug(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.debug(...args);
    }
  }

  /**
   * Info logging - only in development
   */
  info(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.info(...args);
    }
  }

  /**
   * Warning logging - development: console, production: logging service
   */
  warn(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.warn(...args);
    } else {
      this.sendToLoggingService('warn', args);
    }
  }

  /**
   * Error logging - development: console, production: logging service
   */
  error(...args: unknown[]): void {
    if (this.isDevelopment) {
      console.error(...args);
    } else {
      this.sendToLoggingService('error', args);
    }
  }

  /**
   * Send logs to external logging service (Sentry, DataDog, etc.)
   * TODO: Implement integration with chosen logging service
   */
  private sendToLoggingService(level: LogLevel, args: unknown[]): void {
    // Future integration point for Sentry/DataDog/CloudWatch
    // For now, suppress in production to prevent information disclosure
    void level;
    void args;
  }
}

/**
 * Singleton logger instance
 */
export const logger = new SecureLogger();
