/**
 * Purpose: Custom React hook for canvas rendering and animation management
 * Scope: Hook for managing HTML5 canvas rendering, animation loops, and drawing operations
 * Overview: Provides a reusable hook for canvas-based rendering with automatic animation
 *     frame management, resize handling, and drawing function integration. Optimized for
 *     high-performance real-time graphics rendering.
 * Dependencies: React hooks, HTML5 Canvas API
 * Exports: useCanvas hook
 * Interfaces: Hook return type with canvas ref and control methods
 * Implementation: Animation frame loop management with cleanup and resize handling
 */

import { useCallback, useEffect, useRef } from 'react';
import { logger } from '../../../utils/logger';

interface UseCanvasOptions {
  width?: number;
  height?: number;
  autoResize?: boolean;
}

interface UseCanvasReturn {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  startAnimation: () => void;
  stopAnimation: () => void;
  isAnimating: boolean;
}

export function useCanvas(
  drawFunction: (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => void,
  options: UseCanvasOptions = {},
): UseCanvasReturn {
  const { width, height, autoResize = true } = options;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationIdRef = useRef<number | undefined>(undefined);
  const isAnimatingRef = useRef(false);
  const drawFunctionRef = useRef(drawFunction);

  // Update draw function reference
  useEffect(() => {
    drawFunctionRef.current = drawFunction;
  }, [drawFunction]);

  // Animation loop
  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !isAnimatingRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    try {
      drawFunctionRef.current(ctx, canvas);
    } catch (error) {
      logger.error('Error in canvas draw function:', error);
    }

    animationIdRef.current = requestAnimationFrame(animate);
  }, []);

  // Start animation
  const startAnimation = useCallback(() => {
    if (isAnimatingRef.current) return;

    isAnimatingRef.current = true;
    animate();
  }, [animate]);

  // Stop animation
  const stopAnimation = useCallback(() => {
    isAnimatingRef.current = false;

    if (animationIdRef.current !== undefined) {
      cancelAnimationFrame(animationIdRef.current);
      animationIdRef.current = undefined;
    }
  }, []);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas size
    if (width !== undefined && height !== undefined) {
      canvas.width = width;
      canvas.height = height;
    } else if (autoResize) {
      canvas.width = canvas.offsetWidth || canvas.clientWidth;
      canvas.height = canvas.offsetHeight || canvas.clientHeight;
    }

    // Draw once on initialization
    const ctx = canvas.getContext('2d');
    if (ctx) {
      try {
        drawFunctionRef.current(ctx, canvas);
      } catch (error) {
        logger.error('Error in canvas draw function:', error);
      }
    }

    // Cleanup on unmount
    return () => {
      stopAnimation();
    };
  }, [width, height, autoResize, stopAnimation]);

  // Redraw when draw function changes (i.e., when data changes)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    try {
      drawFunctionRef.current(ctx, canvas);
    } catch (error) {
      logger.error('Error in canvas draw function:', error);
    }
  }, [drawFunction]);

  // Handle resize
  useEffect(() => {
    if (!autoResize) return;

    const handleResize = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      canvas.width = canvas.offsetWidth || canvas.clientWidth;
      canvas.height = canvas.offsetHeight || canvas.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Also handle when canvas element itself is resized
    let resizeObserver: ResizeObserver | undefined;

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(handleResize);
      const canvas = canvasRef.current;
      if (canvas) {
        resizeObserver.observe(canvas);
      }
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, [autoResize]);

  return {
    canvasRef,
    startAnimation,
    stopAnimation,
    isAnimating: isAnimatingRef.current,
  };
}
