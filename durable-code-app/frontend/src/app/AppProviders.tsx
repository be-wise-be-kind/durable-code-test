/**
 * Purpose: Application-wide provider wrapper for React Query and development tools
 *
 * Scope: Global state management setup for the entire React application
 *
 * Overview: Configures and provides React Query client with optimized default settings for
 *     caching, stale time management, and retry logic. Includes development tools integration
 *     for enhanced debugging capabilities during development. Centralizes all provider setup
 *     to ensure consistent data fetching behavior across the application with proper error
 *     handling and performance optimizations.
 *
 * Dependencies: React, @tanstack/react-query for data fetching, development tools for debugging
 *
 * Exports: AppProviders component as the main provider wrapper
 *
 * Props/Interfaces: AppProvidersProps with children prop for component composition
 *
 * Implementation: Provider pattern with React Query configuration and conditional dev tools
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes (replaces cacheTime)
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
