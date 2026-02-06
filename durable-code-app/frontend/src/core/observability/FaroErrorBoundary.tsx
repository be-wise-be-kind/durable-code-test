/**
 * Purpose: React error boundary that reports uncaught component errors to Grafana Faro
 *
 * Scope: Wraps the application component tree to capture and report React rendering errors
 *
 * Overview: Implements a React class component error boundary positioned between MinimalErrorBoundary
 *     (outermost, zero-dependency fallback) and AppProviders in the render tree. When a descendant
 *     component throws during rendering, componentDidCatch pushes the error to Faro with the
 *     component stack trace for observability. If Faro is not initialized (disabled or not yet
 *     loaded), the push is silently skipped. Renders a minimal fallback UI with a refresh button
 *     that has no application dependencies.
 *
 * Dependencies: React (Component, ErrorInfo, ReactNode), getFaroInstance from ./faro
 *
 * Exports: FaroErrorBoundary class component
 *
 * Props/Interfaces: { children: ReactNode }
 *
 * State/Behavior: Tracks hasError boolean via getDerivedStateFromError; reports errors via
 *     Faro API pushError in componentDidCatch
 */

import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

import { getFaroInstance } from './faro';

interface FaroErrorBoundaryProps {
  children: ReactNode;
}

interface FaroErrorBoundaryState {
  hasError: boolean;
}

export class FaroErrorBoundary extends Component<
  FaroErrorBoundaryProps,
  FaroErrorBoundaryState
> {
  constructor(props: FaroErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): FaroErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    const faro = getFaroInstance();
    if (faro) {
      faro.api.pushError(error, {
        context: { componentStack: errorInfo.componentStack ?? '' },
      });
    }
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Something went wrong</h1>
          <p>An unexpected error occurred. Please try refreshing the page.</p>
          <button
            type="button"
            onClick={() => {
              window.location.reload();
            }}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
            }}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
