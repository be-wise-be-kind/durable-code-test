/**
 * Purpose: Application entry point that initializes and renders the React application
 *
 * Scope: Handles application bootstrapping, error handling, observability, and provider setup
 *
 * Overview: This is the main entry file that sets up the React application with all necessary
 *     providers and error boundaries. It includes global error handling for uncaught errors
 *     and promise rejections, implements error storm protection, initializes Grafana Faro
 *     browser SDK for client-side observability, and renders the app within StrictMode for
 *     development safety. The FaroErrorBoundary sits between MinimalErrorBoundary and
 *     AppProviders to report React rendering errors to the observability backend.
 *
 * Dependencies: React, React DOM, React Router, AppProviders, MinimalErrorBoundary,
 *     FaroErrorBoundary, initializeFaro, App component
 *
 * Exports: No exports - this is an entry point file
 *
 * Props/Interfaces: No props - bootstraps the application
 *
 * State/Behavior: Sets up global error handlers, initializes Faro SDK, finds root DOM element,
 *     and renders app tree
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './styles/global.css';
import './index.css';
import App from './App.tsx';
import { AppProviders } from './app/AppProviders';
import { MinimalErrorBoundary } from './core/errors/MinimalErrorBoundary';
import { FaroErrorBoundary, initializeFaro } from './core/observability';
import { logger } from './utils/logger';

// Simplified global error handling for security/performance
let errorCount = 0;
let lastErrorTime = 0;
const ERROR_THRESHOLD = 5;
const TIME_WINDOW = 60000;

window.addEventListener('error', (event) => {
  const now = Date.now();
  if (now - lastErrorTime > TIME_WINDOW) errorCount = 0;
  errorCount++;
  lastErrorTime = now;

  if (errorCount >= ERROR_THRESHOLD) {
    logger.error('Error storm detected, preventing cascade');
    return;
  }

  logger.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  const now = Date.now();
  if (now - lastErrorTime > TIME_WINDOW) errorCount = 0;
  errorCount++;
  lastErrorTime = now;

  if (errorCount >= ERROR_THRESHOLD) {
    logger.error('Promise rejection storm detected');
    return;
  }

  logger.error('Unhandled promise rejection:', event.reason);
});

logger.debug('[main.tsx] Starting app initialization');

initializeFaro();

const rootElement = document.getElementById('root');
if (!rootElement) {
  logger.error('[main.tsx] Root element not found!');
  throw new Error('Failed to find root element');
}

logger.debug('[main.tsx] Root element found, rendering app');

createRoot(rootElement).render(
  <StrictMode>
    <MinimalErrorBoundary>
      <FaroErrorBoundary>
        <AppProviders>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AppProviders>
      </FaroErrorBoundary>
    </MinimalErrorBoundary>
  </StrictMode>,
);
