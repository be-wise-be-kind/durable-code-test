/**
 * Purpose: WebSocket service for oscilloscope data streaming and communication
 * Scope: WebSocket connection management, message handling, and event distribution
 * Overview: Provides a robust WebSocket service with connection management, event
 *     handling, reconnection logic, and type-safe message parsing for oscilloscope data.
 * Dependencies: WebSocket API, oscilloscope types and constants
 * Exports: WebSocketService class
 * Interfaces: Event-driven WebSocket communication with reconnection support
 * Implementation: Event emitter pattern with automatic reconnection and error handling
 */

import type { OscilloscopeData, WebSocketCommand } from '../types/oscilloscope.types';
import { WEBSOCKET_CONFIG } from '../constants/oscilloscope.constants';
import { logger } from '../../../utils/logger';

type EventCallback<T = unknown> = (data: T) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private componentListeners: Map<string, Map<string, Set<EventCallback>>> = new Map(); // componentId -> event -> callbacks
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private url = '';
  private isConnecting = false;

  constructor() {
    this.listeners.set('open', new Set());
    this.listeners.set('close', new Set());
    this.listeners.set('error', new Set());
    this.listeners.set('data', new Set());
    this.listeners.set('reconnecting', new Set());
    this.listeners.set('reconnected', new Set());
    this.listeners.set('maxReconnectAttemptsReached', new Set());
  }

  /**
   * Connect to WebSocket server
   */
  connect(url?: string): Promise<void> {
    // If already connected, resolve immediately
    if (this.isConnected) {
      return Promise.resolve();
    }

    if (this.isConnecting) {
      return Promise.reject(new Error('Connection already in progress'));
    }

    if (!url) {
      // Auto-generate URL if not provided
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;

      // In development, try to detect the backend port dynamically
      // The port offset is the same for both frontend and backend
      const currentPort = parseInt(window.location.port);
      let backendPort = WEBSOCKET_CONFIG.BACKEND_PORT;

      if (currentPort >= 5173 && currentPort <= 6172) {
        // We're in dev mode with a frontend dev server
        // Frontend base port is 5173, backend base is 8000
        // Both use the same offset from their base
        const portOffset = currentPort - 5173;
        backendPort = 8000 + portOffset;
        url = `${protocol}//${host}:${backendPort}${WEBSOCKET_CONFIG.ENDPOINT}`;
      } else if (!currentPort || currentPort === 80 || currentPort === 443) {
        // Production mode - no port or standard HTTP/HTTPS ports
        // Don't specify a port (ALB handles routing)
        url = `${protocol}//${host}${WEBSOCKET_CONFIG.ENDPOINT}`;
      } else {
        // Use the same port as the page (likely proxied in production)
        backendPort = currentPort as 8000;
        url = `${protocol}//${host}:${backendPort}${WEBSOCKET_CONFIG.ENDPOINT}`;
      }
    }

    this.url = url;
    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('open', null);

          if (this.reconnectAttempts > 0) {
            this.emit('reconnected', null);
          }

          resolve();
        };

        this.ws.onclose = () => {
          this.isConnecting = false;
          this.emit('close', null);
          this.handleReconnection();
        };

        this.ws.onerror = (error) => {
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

        this.ws.onmessage = this.handleMessage.bind(this);
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearReconnectTimer();
    this.reconnectAttempts = WEBSOCKET_CONFIG.MAX_RECONNECT_ATTEMPTS; // Prevent reconnection

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send command to WebSocket server
   */
  send(data: WebSocketCommand): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        return true;
      } catch (error) {
        this.emit('error', error);
        return false;
      }
    }
    return false;
  }

  /**
   * Add event listener
   */
  on<T = unknown>(event: string, callback: EventCallback<T>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback as EventCallback);
  }

  /**
   * Add event listener for a specific component
   */
  onForComponent<T = unknown>(
    componentId: string,
    event: string,
    callback: EventCallback<T>,
  ): void {
    // Add to global listeners
    this.on(event, callback);

    // Track component-specific listeners
    if (!this.componentListeners.has(componentId)) {
      this.componentListeners.set(componentId, new Map());
    }
    const componentEvents = this.componentListeners.get(componentId);
    if (!componentEvents) return;

    if (!componentEvents.has(event)) {
      componentEvents.set(event, new Set());
    }
    componentEvents.get(event)?.add(callback as EventCallback);
  }

  /**
   * Remove event listener
   */
  off<T = unknown>(event: string, callback: EventCallback<T>): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(callback as EventCallback);
    }
  }

  /**
   * Remove all event listeners for a specific component
   */
  removeAllListenersForComponent(componentId: string): void {
    const componentEvents = this.componentListeners.get(componentId);
    if (componentEvents) {
      // Remove each listener from global listeners
      componentEvents.forEach((callbacks, event) => {
        const globalListeners = this.listeners.get(event);
        if (globalListeners) {
          callbacks.forEach((callback) => {
            globalListeners.delete(callback);
          });
        }
      });

      // Clear component's listener tracking
      this.componentListeners.delete(componentId);
    }
  }

  /**
   * Get the total number of listeners (for testing)
   */
  getListenerCount(): number {
    let count = 0;
    this.listeners.forEach((eventListeners) => {
      count += eventListeners.size;
    });
    return count;
  }

  /**
   * Get the number of components with active listeners (for testing)
   */
  getComponentCount(): number {
    return this.componentListeners.size;
  }

  /**
   * Get connection status
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  get readyState(): number | null {
    return this.ws?.readyState ?? null;
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const data: OscilloscopeData = JSON.parse(event.data);
      this.emit('data', data);
    } catch (error) {
      this.emit('error', new Error(`Failed to parse WebSocket message: ${error}`));
    }
  }

  /**
   * Emit event to all listeners
   */
  private emit<T>(event: string, data: T): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach((callback) => {
        try {
          callback(data);
        } catch (error) {
          logger.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnection(): void {
    if (this.reconnectAttempts >= WEBSOCKET_CONFIG.MAX_RECONNECT_ATTEMPTS) {
      this.emit('maxReconnectAttemptsReached', null);
      return;
    }

    this.clearReconnectTimer();
    this.reconnectAttempts++;

    this.emit('reconnecting', { attempt: this.reconnectAttempts });

    this.reconnectTimer = setTimeout(() => {
      if (this.url) {
        this.connect(this.url).catch(() => {
          // Reconnection failed, handleReconnection will be called again via onclose
        });
      }
    }, WEBSOCKET_CONFIG.RECONNECT_DELAY);
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
