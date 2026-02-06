/**
 * Purpose: Initializes Grafana Faro browser SDK for client-side observability
 *
 * Scope: Frontend telemetry collection including errors, web vitals, sessions, and distributed tracing
 *
 * Overview: Configures and initializes the Grafana Faro browser SDK to capture client-side telemetry
 *     data including console logs, uncaught errors, web vitals, and session tracking. Integrates
 *     OpenTelemetry-based distributed tracing with W3C TraceContext propagation for API requests.
 *     The entire module is feature-gated behind the VITE_FARO_ENABLED environment variable,
 *     returning null when disabled for zero runtime overhead. Collector URL defaults to '/collect'
 *     for same-origin ALB routing to the Alloy Faro receiver.
 *
 * Dependencies: @grafana/faro-web-sdk for core SDK, @grafana/faro-web-tracing for OTel integration
 *
 * Exports: initializeFaro (SDK bootstrap), getFaroInstance (singleton accessor)
 *
 * Interfaces: initializeFaro() returns Faro | null, getFaroInstance() returns Faro | null
 *
 * Implementation: Decomposed helper functions keep complexity low. Module-level singleton pattern
 *     mirrors the backend telemetry.py approach. TracingInstrumentation propagates W3C trace
 *     headers on /api/* requests for distributed tracing correlation.
 */

import {
  initializeFaro as faroInit,
  getWebInstrumentations,
} from '@grafana/faro-web-sdk';
import type { Faro } from '@grafana/faro-web-sdk';
import { TracingInstrumentation } from '@grafana/faro-web-tracing';

let faroInstance: Faro | null = null;

/** Checks whether Faro is enabled via the VITE_FARO_ENABLED build-time variable. */
function isFaroEnabled(): boolean {
  return import.meta.env.VITE_FARO_ENABLED === 'true';
}

/** Resolves the Faro collector URL from env or falls back to '/collect'. */
function getCollectorUrl(): string {
  const envUrl = import.meta.env.VITE_FARO_COLLECTOR_URL;
  if (typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  return '/collect';
}

/** Builds app metadata for Faro from Vite environment variables. */
function buildAppMeta(): { name: string; version: string; environment: string } {
  return {
    name: 'durable-code-frontend',
    version: String(import.meta.env.VITE_BUILD_TIMESTAMP ?? 'dev'),
    environment: import.meta.env.MODE,
  };
}

/** Creates a TracingInstrumentation configured for W3C propagation on /api/* requests. */
function buildTracingInstrumentation(): TracingInstrumentation {
  return new TracingInstrumentation({
    instrumentationOptions: {
      propagateTraceHeaderCorsUrls: [/\/api\/.*/],
    },
  });
}

/**
 * Initializes the Grafana Faro browser SDK.
 *
 * Returns the Faro instance when VITE_FARO_ENABLED is 'true', or null when disabled.
 * Safe to call multiple times; subsequent calls return the existing instance.
 */
export function initializeFaro(): Faro | null {
  if (faroInstance) {
    return faroInstance;
  }

  if (!isFaroEnabled()) {
    return null;
  }

  faroInstance = faroInit({
    url: getCollectorUrl(),
    app: buildAppMeta(),
    instrumentations: [...getWebInstrumentations(), buildTracingInstrumentation()],
  });

  return faroInstance;
}

/** Returns the Faro singleton, or null if not initialized or disabled. */
export function getFaroInstance(): Faro | null {
  return faroInstance;
}
