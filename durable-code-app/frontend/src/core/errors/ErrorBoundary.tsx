/**
 * Purpose: Main error boundary component for catching React errors
 * Scope: Error isolation and recovery at any component tree level
 * Overview: Implements React error boundary with recovery mechanisms
 * Dependencies: React, error types, fallback component, logger
 * Exports: ErrorBoundary component
 * Props/Interfaces: ErrorBoundaryProps
 * Implementation: Class component with error lifecycle methods and recovery logic
 */

import { Component } from 'react';
import type { ErrorInfo as ReactErrorInfo, ReactNode } from 'react';
import type {
  ErrorBoundaryProps,
  ErrorBoundaryState,
  ErrorInfo,
} from './ErrorBoundary.types';
import { ErrorFallback } from './ErrorFallback';
import { errorLogger } from './ErrorLogger';
import { logger } from '../../utils/logger';

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: NodeJS.Timeout | null = null;
  private retryCount = 0;
  private previousResetKeys: Array<string | number> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      lastErrorTime: null,
    };

    this.previousResetKeys = props.resetKeys || [];
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    logger.error('[ErrorBoundary] Caught error:', error);
    // Update state so the next render shows the fallback UI
    return {
      hasError: true,
      error,
      errorCount: 1,
      lastErrorTime: Date.now(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ReactErrorInfo): void {
    // Create enhanced error info
    const enhancedErrorInfo: ErrorInfo = {
      ...errorInfo,
      digest: errorInfo.digest || undefined,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      errorBoundary: this.props.name || 'Unknown',
      errorBoundaryProps: {
        level: this.props.level,
        isolate: this.props.isolate,
      },
    };

    // Update state with error info
    this.setState((prevState) => ({
      errorInfo: enhancedErrorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Log the error
    errorLogger.logError(error, enhancedErrorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, enhancedErrorInfo);
    }

    // Auto-recovery if enabled
    if (this.props.recoveryOptions?.enableAutoRecovery) {
      this.scheduleAutoRecovery();
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    const { resetKeys, resetOnPropsChange } = this.props;

    // Check if reset keys have changed
    if (resetKeys && prevProps.resetKeys) {
      const hasResetKeyChanged = resetKeys.some(
        (key, index) => key !== this.previousResetKeys[index],
      );

      if (hasResetKeyChanged) {
        this.handleReset();
        this.previousResetKeys = resetKeys;
      }
    }

    // Reset on any prop change if configured
    if (resetOnPropsChange && this.state.hasError) {
      const propsChanged = Object.keys(prevProps).some(
        (key) =>
          key !== 'children' &&
          (prevProps as unknown as Record<string, unknown>)[key] !==
            (this.props as unknown as Record<string, unknown>)[key],
      );

      if (propsChanged) {
        this.handleReset();
      }
    }
  }

  componentWillUnmount(): void {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  /**
   * Schedule automatic recovery attempt
   */
  private scheduleAutoRecovery = (): void => {
    const delay = this.props.recoveryOptions?.autoRecoveryDelay || 5000;

    this.resetTimeoutId = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };

  /**
   * Handle error reset
   */
  private handleReset = (): void => {
    this.retryCount = 0;

    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }

    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      lastErrorTime: null,
    });

    errorLogger.logRecovery('reset', true);

    if (this.props.recoveryOptions?.onReset) {
      this.props.recoveryOptions.onReset();
    }
  };

  /**
   * Handle retry attempt
   */
  private handleRetry = (): void => {
    const maxRetries = this.props.recoveryOptions?.maxRetries || 3;

    if (this.retryCount >= maxRetries) {
      errorLogger.logRecovery('retry', false);
      return;
    }

    this.retryCount++;

    // Add delay before retry
    const retryDelay = this.props.recoveryOptions?.retryDelay || 1000;

    setTimeout(() => {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
      });

      errorLogger.logRecovery('retry', true);

      if (this.props.recoveryOptions?.onRetry) {
        this.props.recoveryOptions.onRetry();
      }
    }, retryDelay);
  };

  /**
   * Handle navigation to home
   */
  private handleHome = (): void => {
    errorLogger.logRecovery('home', true);
    window.location.href = '/';
  };

  render(): ReactNode {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || ErrorFallback;
      const error = this.state.error;
      if (!error) {
        return <div>Unknown error occurred</div>;
      }

      return (
        <FallbackComponent
          error={error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
          onRetry={this.props.recoveryOptions?.onRetry ? this.handleRetry : undefined}
          onHome={this.handleHome}
          level={this.props.level}
          name={this.props.name}
          retryCount={this.retryCount}
          maxRetries={this.props.recoveryOptions?.maxRetries || 3}
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
